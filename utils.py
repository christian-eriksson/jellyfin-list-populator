import csv
import os
import sys
from typing import Union

import requests


def extract_option(flag: str, optional=False) -> Union[str, None]:
    value = None
    try:
        flag_index = sys.argv.index(flag)
        value_index = flag_index + 1
        value = sys.argv[value_index]
        sys.argv.pop(value_index)
        sys.argv.pop(flag_index)
    except Exception as ex:
        if not optional:
            raise ex

    return value


def get_user_id(name: str, base_url: str, headers: dict):
    response = requests.get(
        f"{base_url}/Users",
        headers=headers,
    )
    if response.status_code != 200:
        print("Could not fetch user id, check your api key and/or jellyfin url!")
        exit(1)
    user_list = response.json()
    correct_users = [user["Id"] for user in user_list if user["Name"] == name]
    if len(correct_users) < 1:
        print(f"Name: '{name}' not present on server!")
        exit(1)
    user = correct_users[0]
    return user


def get_ids_in_both_list_and_server(list_items, server_content):
    ids_to_add_to_collection = []
    for list_item in list_items:
        if list_item["imdb_id"] in server_content["features"]:
            server_item = server_content["features"][list_item["imdb_id"]]
            if not list_item["seasons"]:
                ids_to_add_to_collection.append(server_item["Id"])
            else:
                series_id = server_item["Id"]
                if series_id in server_content["series_content"]:
                    for season_number in list_item["seasons"]:
                        seasons_info = server_content["series_content"][series_id]
                        if season_number in seasons_info:
                            if not list_item["episodes"]:
                                ids_to_add_to_collection.append(
                                    seasons_info[season_number]["season_id"]
                                )
                            else:
                                for episode_number in list_item["episodes"]:
                                    episodes_info = seasons_info[season_number][
                                        "episodes"
                                    ]
                                    if episode_number in episodes_info:
                                        ids_to_add_to_collection.append(
                                            episodes_info[episode_number]["Id"]
                                        )
    return ids_to_add_to_collection


def extract_input_options():
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
    return (
        base_url,
        headers,
        user_name,
        list_path,
        server_content_path,
        tvdb_key,
        tvdb_pin,
    )


def parse_input_list(list_path):
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
    except:
        print(
            "please provide a valid content file (csv's should be semi-colon delimited), in '--content'!"
        )
        exit(1)
    return list_items


def add_ids_to_parent_url(ids, url, headers):
    chunk_size = 50
    chunk_start = 0
    chunk = ids[chunk_start : chunk_start + chunk_size]
    while len(chunk) > 0:
        request_headers = headers.copy()
        request_headers["Content-Type"] = "application/json"
        response = requests.post(
            url,
            headers=request_headers,
            params={"Ids": ",".join(chunk)},
        )
        if response.status_code != 204:
            print(
                "Could not add items to playlist, check your api key and/or jellyfin url!"
            )
            exit(1)
        chunk_start = chunk_start + chunk_size
        chunk = ids[chunk_start : chunk_start + chunk_size]
