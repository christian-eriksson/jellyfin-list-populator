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


def get_collections():
    response = requests.get(
        f"{base_url}/Users/{user_id}/Views",
        headers=headers,
    )
    if response.status_code != 200:
        print("Could not fetch views, check your api key and/or jellyfin url!")
        exit(1)

    views = response.json()["Items"]
    collection_folder = None

    for view in views:
        if view["Name"] == "Collections":
            collection_folder = view
            break

    if not collection_folder:
        print(
            "Could not find the Collection view, check that it is present for the user on the Jellyfin server!"
        )
        exit(1)

    response = requests.get(
        f"{base_url}/Users/{user_id}/Items?ParentId={collection_folder['Id']}&SortBy=SortName&SortOrder=Ascending&Recursive=true&StartIndex=0",
        headers=headers,
    )

    if response.status_code != 200:
        print("Could not fetch collections, check your api key and/or jellyfin url!")
        exit(1)

    return response.json()["Items"]


def get_collection_by_name(name):
    collection = get_collections()
    for playlist in collection:
        if playlist["Name"] == name:
            return playlist

    return None


def create_collection(name) -> str:
    request_headers = headers.copy()
    request_headers["Content-Type"] = "application/json"
    response = requests.post(
        f"{base_url}/Collections",
        headers=request_headers,
        params={"Name": name, "IsLocked": False},
    )
    if response.status_code != 200:
        print("Could not create playlist, check your api key and/or jellyfin url!")
        exit(1)
    response = response.json()
    return response["Id"]


def add_ids_to_collection(ids: List[str], collection_id: str):
    add_ids_to_parent_url(ids, f"{base_url}/Collections/{collection_id}/Items", headers)


def populate_collection(collection_name, items_for_collection):
    collection = get_collection_by_name(collection_name)

    if collection is None:
        create_collection(collection_name)
        collection = get_collection_by_name(collection_name)

    server_content = None
    if server_content_path:
        with open(server_content_path) as file:
            server_content = json.load(file)
    else:
        server_content = get_server_content(
            base_url, user_id, headers, tvdb_key, tvdb_pin
        )

    ids_to_add_to_collection = get_ids_in_both_list_and_server(
        items_for_collection, server_content
    )

    add_ids_to_collection(ids_to_add_to_collection, collection["Id"])


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
        collection_name = sys.argv[1]
    except:
        print("please provide a collection name, in arg 1!")
        exit(1)

    user_id = get_user_id(user_name, base_url=base_url, headers=headers)

    populate_collection(collection_name, list_items)
