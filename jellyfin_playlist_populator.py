#!/usr/bin/env python3

import json
import sys
from typing import List
import requests
from get_server_content import get_server_content

from utils import (
    add_ids_to_parent_url,
    parse_input_list,
    extract_input_options,
    get_ids_in_both_list_and_server,
    get_user_id,
)


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
        params={"userId": user_id, "Name": name},
    )
    if response.status_code != 200:
        print("Could not create playlist, check your api key and/or jellyfin url!")
        exit(1)
    response = response.json()
    return response["Id"]


def add_ids_to_playlist(ids: List[str], playlist_id: str):
    add_ids_to_parent_url(
        ids, f"{base_url}/Playlists/{playlist_id}/Items?userId={user_id}", headers
    )


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
        server_content = get_server_content(
            base_url, user_id, headers, tvdb_key, tvdb_pin
        )

    ids_to_add_to_playlist = get_ids_in_both_list_and_server(
        items_for_playlist, server_content
    )

    add_ids_to_playlist(ids_to_add_to_playlist, playlist["Id"])


if __name__ == "__main__":
    (
        base_url,
        headers,
        user_name,
        list_path,
        server_content_path,
        tvdb_key,
        tvdb_pin,
    ) = extract_input_options()

    list_items = parse_input_list(list_path)

    try:
        list_name = sys.argv[1]
    except:
        print("please provide a playlist name, in arg 1!")
        exit(1)

    user_id = get_user_id(user_name, base_url=base_url, headers=headers)

    populate_playlist(list_name, list_items)
