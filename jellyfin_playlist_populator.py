#!/usr/bin/env python3

import csv
import json
import os
import sys
from typing import List
import requests
from get_server_content import get_server_content

from utils import extract_option, get_user_id


def get_playlists():
    response = requests.get(
        f"{base_url}/Users/{user_id}/Items?SortBy=SortName&SortOrder=Ascending&IncludeItemTypes=Playlist&Recursive=true&StartIndex=0",
        headers=headers,
    )
    if response.status_code != 200:
        print("Could not fetch playlists, check your api key and/or jellyfin url!")
        exit(1)
    return response.json()["Items"]


def get_playlist_by_name(name):
    playlists = get_playlists()
    for playlist in playlists:
        if playlist["Name"] == name:
            return playlist

    return None


def create_playlist(name) -> str:
    request_headers = headers.copy()
    request_headers["Content-Type"] = "application/json"
    response = requests.post(
        f"{base_url}/Playlists",
        headers=request_headers,
        params= {
            "userId": user_id,
            "Name": name
        }
    )
    if response.status_code != 200:
        print("Could not create playlist, check your api key and/or jellyfin url!")
        exit(1)
    response = response.json()
    return response["Id"]


def add_ids_to_playlist(ids: List[str], playlist_id: str):
    chunk_size = 50
    chunk_start = 0
    chunk = ids[chunk_start : chunk_start + chunk_size]
    while len(chunk) > 0:
        request_headers = headers.copy()
        request_headers["Content-Type"] = "application/json"
        response = requests.post(
            f"{base_url}/Playlists/{playlist_id}/Items?userId={user_id}&Ids={','.join(chunk)}",
            headers=request_headers,
        )
        if response.status_code != 204:
            print(
                "Could not add items to playlist, check your api key and/or jellyfin url!"
            )
            exit(1)
        chunk_start = chunk_start + chunk_size
        chunk = ids[chunk_start : chunk_start + chunk_size]

def populate_playlist(playlist_name, items_for_playlist):
    playlist = get_playlist_by_name(playlist_name)

    if playlist is None:
        create_playlist(list_name)
        playlist = get_playlist_by_name(list_name)

    server_content = None
    if server_content_path:
        with open(server_content_path) as file:
            server_content = json.load(file)
    else:
        server_content = get_server_content(base_url, user_id, headers, tvdb_key, tvdb_pin)

    ids_to_add_to_playlist = []
    for list_item in items_for_playlist:
        if list_item["imdb_id"] in server_content["features"]:
            server_item = server_content["features"][list_item["imdb_id"]]
            if not list_item["seasons"]:
                ids_to_add_to_playlist.append(server_item["Id"])
            else:
                series_id = server_item["Id"]
                if series_id in server_content["series_content"]:
                    for season_number in list_item["seasons"]:
                        seasons_info = server_content["series_content"][series_id]
                        if season_number in seasons_info:
                            if not list_item["episodes"]:
                                ids_to_add_to_playlist.append(seasons_info[season_number]["season_id"])
                            else:
                                for episode_number in list_item["episodes"]:
                                    episodes_info = seasons_info[season_number]["episodes"]
                                    if episode_number in episodes_info:
                                        ids_to_add_to_playlist.append(
                                            episodes_info[episode_number]["Id"]
                                        )

    add_ids_to_playlist(ids_to_add_to_playlist, playlist["Id"])

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

    try:
        list_path = extract_option("--list")
        if not os.path.isfile(list_path):
            print("the list file does not exist!")
            exit(1)
    except:
        print("please provide a path to a list of titles, in '--list'!")
        exit(1)

    tvdb_key = extract_option("--tvdb-key", optional=True)
    tvdb_pin = extract_option("--tvdb-pin", optional=True)

    server_content_path = extract_option("--server-content", optional=True)
    if server_content_path:
        if not os.path.isfile(server_content_path):
            print("the server content file does not exist!")
            exit(1)

    try:
        list_items = []
        with open(list_path, "r") as file:
            reader = csv.reader(file, delimiter=";", quotechar='"')
            for row in reader:
                id = row[0]
                seasons = None if len(row) < 3 or not row[2] else row[2].split("|")
                episodes = None if len(row) < 4 or not row[3] else row[3].split("|")
                title = {
                    "imdb_id": id,
                    "name": row[1],
                    "seasons": seasons,
                    "episodes": episodes,
                }
                list_items.append(title)
    except Exception as ex:
        print(
            "please provide a valid content file (csv's should be semi-colon delimited), in '--content'!"
        )
        exit(1)

    try:
        list_name = sys.argv[1]
    except:
        print("please provide a playlist name, in arg 1!")
        exit(1)

    user_id = get_user_id(user_name, base_url=base_url, headers=headers)

    populate_playlist(list_name, list_items)
