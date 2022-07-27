#!/usr/bin/env python3

import json
import os
import re
from typing import List
import requests

from multiprocessing import Pool
from tvdb_client import TvdbClient
from utils import extract_option, get_user_id


def get_media_items(base_url: str, user_id: str, headers: dict):
    response = requests.get(
        f"{base_url}/Users/{user_id}/Items?SortBy=SortName&SortOrder=Ascending&IncludeItemTypes=Movie,Episode,Season,Series,Video&Recursive=true&StartIndex=0",
        headers=headers,
    )
    if response.status_code != 200:
        print("Could not fetch media items, check your api key and/or jellyfin url!")
        exit(1)
    return response.json()["Items"]


def get_server_content(
    base_url: str, user_id: str, headers: dict, tvdb_key="", tvdb_pin=""
):
    media_items = get_media_items(base_url, user_id, headers)
    item_details_requests = [
        (media_item["Id"], base_url, user_id, headers) for media_item in media_items
    ]
    detailed_media_items = []
    with Pool(os.cpu_count()) as p:
        detailed_media_items = p.map(
            request_detailed_server_items, item_details_requests
        )

    tvdb_client = None
    if tvdb_key and tvdb_pin:
        tvdb_client = TvdbClient(api_key=tvdb_key, pin=tvdb_pin)

    tvdb_special_feature_guess_requests = []
    server_content = {"features": {}, "series_content": {}}
    for detailed_media_item in detailed_media_items:
        item, special_features = detailed_media_item
        if "ProviderIds" in item:
            if "Imdb" in item["ProviderIds"]:
                if item["Type"] == "Episode":
                    add_episode_to_content(server_content, item)
                else:
                    add_feature_to_content(server_content, item)

                if len(special_features) > 0 and tvdb_client:
                    for special_feature in special_features:
                        tvdb_special_feature_guess_requests.append(
                            (
                                item["ProviderIds"]["Imdb"],
                                special_feature,
                                tvdb_client,
                            )
                        )

    if tvdb_client and len(tvdb_special_feature_guess_requests) > 0:
        add_special_feature_titles(tvdb_special_feature_guess_requests, server_content)

    return server_content


def add_special_feature_titles(tvdb_special_feature_guess_requests, server_content):
    tvdb_special_feature_guesses = []
    with Pool(os.cpu_count()) as p:
        tvdb_special_feature_guesses = p.map(
            request_tvdb_item_guess, tvdb_special_feature_guess_requests
        )

    for tvdb_special_feature_guess in tvdb_special_feature_guesses:
        imdb_id, special_feature, tvdb_guess = tvdb_special_feature_guess
        special_feature["ParentImdbId"] = imdb_id
        if tvdb_guess:
            tvdb_imdb_id = get_imdb_id(tvdb_guess)
            if tvdb_guess["type"] == "series":
                special_feature["Type"] = "Series"
                season_number = get_season(special_feature["Name"])
                if season_number:
                    season_id = special_feature["Id"]
                    new_id = tvdb_guess["id"]
                    special_feature["Id"] = new_id
                    special_feature["OldId"] = season_id

                    special_feature["SeriesId"] = new_id
                    special_feature["ParentIndexNumber"] = season_number
                    special_feature["SeasonId"] = season_id
                    special_feature["IndexNumber"] = None

                    add_episode_to_content(server_content, special_feature)

            if tvdb_imdb_id not in server_content["features"]:
                special_feature["ProviderIds"]["Imdb"] = tvdb_imdb_id
                add_feature_to_content(server_content, special_feature)


def request_detailed_server_items(decoration_request):
    id, base_url, user_id, headers = decoration_request
    item_response = requests.get(
        f"{base_url}/Users/{user_id}/Items/{id}",
        headers=headers,
    )
    if item_response.status_code != 200:
        print(
            "WARNING: Could not fetch media item to decorate, check your api key and/or jellyfin url!"
        )

    item = item_response.json()

    features_response = requests.get(
        f"{base_url}/Users/{user_id}/Items/{id}/SpecialFeatures",
        headers=headers,
    )
    if features_response.status_code != 200:
        print(
            "WARNING: Could not fetch media item to decorate, check your api key and/or jellyfin url!"
        )

    special_features = features_response.json()

    return (item, special_features)


def request_tvdb_item_guess(tvdb_item_guess_request):
    imdb_id, special_feature, tvdb_client = tvdb_item_guess_request
    name: str = special_feature["Name"]
    special_feature_candidates: List = tvdb_client.search_titles(
        re.sub(r"season \d+$", "", name, flags=re.IGNORECASE)
    )
    tvdb_guess = None
    if len(special_feature_candidates) > 0:
        tvdb_guess = special_feature_candidates[0]

    return (imdb_id, special_feature, tvdb_guess)


def add_feature_to_content(server_content, server_item):
    server_content["features"][server_item["ProviderIds"]["Imdb"]] = server_item


def add_episode_to_content(server_content, server_item):
    series_id = server_item["SeriesId"]
    season_number = str(server_item["ParentIndexNumber"])
    season_id = server_item["SeasonId"]
    episode_number = server_item["IndexNumber"]
    if episode_number:
        episode_number = str(server_item["IndexNumber"])

    if series_id not in server_content["series_content"]:
        server_content["series_content"][series_id] = {}
    if season_number not in server_content["series_content"][series_id]:
        server_content["series_content"][series_id][season_number] = {
            "season_id": season_id,
            "episodes": {},
        }
    if episode_number:
        server_content["series_content"][series_id][season_number]["episodes"][
            episode_number
        ] = server_item


def get_imdb_id(tvdb_item):
    result = None
    if "remote_ids" in tvdb_item:
        for remote_id in tvdb_item["remote_ids"]:
            if remote_id["sourceName"].lower() == "imdb":
                if remote_id["id"].startswith("tt"):
                    result = remote_id["id"]
    return result


def get_season(name):
    season_match = re.match(r".*season (\d+)$", name, flags=re.IGNORECASE)
    season = None
    if season_match:
        season = int(season_match.group(1))
    return season


if __name__ == "__main__":
    try:
        base_url = extract_option("--url")
    except:
        print("please provide a url to jellyfin, in '--url'!")
        exit(1)

    try:
        api_key = extract_option("--key")
    except:
        print("please provide an api key, in '--key'!")
        exit(1)

    headers = {"X-Emby-Authorization": f"MediaBrowser Token={api_key}"}

    try:
        user_name = extract_option("--user")
    except:
        print("please provide a username, in '--user'!")
        exit(1)

    tvdb_key = extract_option("--tvdb-key", optional=True)
    tvdb_pin = extract_option("--tvdb-pin", optional=True)

    user_id = get_user_id(user_name, base_url, headers)

    server_content = get_server_content(
        base_url, user_id, headers, tvdb_key=tvdb_key, tvdb_pin=tvdb_pin
    )

    print(json.dumps(server_content))
