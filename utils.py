import sys

import requests


def extract_option(flag: str, optional=False) -> str:
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
