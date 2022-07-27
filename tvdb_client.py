import json
import re
from typing import Any, Optional, TypedDict

import requests


# def extract_tvdb_id(object_id: str) -> Optional[int]:
#     id_pattern = re.compile(r"^\w+-([\d]+)")
#     is_id = id_pattern.match(object_id)
#     tvdb_id = None
#     if is_id:
#         tvdb_id = int(is_id.group(1))
#     return tvdb_id


# def get_tvdb_ids(series) -> list[int]:
#     tvdb_ids = []
#     for serie in series:
#         tvdb_id = (
#             extract_tvdb_id(serie["objectID"])
#             if "tvdb_id" not in serie
#             else serie["tvdb_id"]
#         )
#         if tvdb_id:
#             tvdb_ids.append(tvdb_id)

#     return tvdb_ids


class TvdbClient:
    def __init__(self, api_key, pin):
        login_data = {"apikey": api_key, "pin": pin}
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        }
        self.base_url = "https://api4.thetvdb.com/v4"
        response = requests.post(
            f"{self.base_url}/login", json=login_data, headers=headers
        )

        self.token = response.json()["data"]["token"]

    def search_titles(self, title_name):
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + self.token,
        }
        search_url = f"{self.base_url}/search?q={title_name}"
        response = requests.get(search_url, headers=headers)
        resp = response.json()
        titles = resp["data"]
        return titles

    # def search_series_ids(self, title_name):
    #     headers = {
    #         "accept": "application/json",
    #         "Authorization": "Bearer " + self.token,
    #     }
    #     search_url = f"{self.base_url}/search?q={title_name}&type=series"
    #     response = requests.get(search_url, headers=headers)
    #     resp = response.json()
    #     found_series = resp["data"]
    #     tvdb_ids = get_tvdb_ids(found_series)
    #     return tvdb_ids

    # def find_series(self, imdb_id, series_ids):
    #     series = None
    #     headers = {
    #         "accept": "application/json",
    #         "Authorization": "Bearer " + self.token,
    #     }
    #     for series_id in series_ids:
    #         response = requests.get(
    #             f"{self.base_url}/series/{series_id}/extended", headers=headers
    #         )
    #         candidate = response.json()["data"]
    #         imdb_ids = []
    #         if candidate and "remoteIds" in candidate:
    #             imdb_ids = [
    #                 remoteId
    #                 for remoteId in candidate["remoteIds"]
    #                 if remoteId["type"] == 2 and remoteId["id"] == imdb_id
    #             ]
    #         if len(imdb_ids) > 0:
    #             series = candidate
    #             break

    #     return series

    # def get_season(self, season_id):
    #     headers = {
    #         "accept": "application/json",
    #         "Authorization": "Bearer " + self.token,
    #     }
    #     response = requests.get(
    #         f"{self.base_url}/seasons/{season_id}/extended", headers=headers
    #     )
    #     return response.json()["data"]

    # def get_episode(self, episode_id):
    #     headers = {
    #         "accept": "application/json",
    #         "Authorization": "Bearer " + self.token,
    #     }
    #     response = requests.get(
    #         f"{self.base_url}/episodes/{episode_id}/extended", headers=headers
    #     )
    #     return response.json()["data"]

    # def get_series(self, imdb_id, title_name) -> Tuple[Optional[Any], str]:
    #     series_ids = self.search_series_ids(title_name)
    #     series = self.find_series(imdb_id, series_ids)
    #     series_url = "https://thetvdb.com"
    #     if series:
    #         series_url = f'{series_url}/search?query={series["id"]}'
    #     return series, series_url


# class Episode(TypedDict):
#     number: int


# class Season(TypedDict):
#     number: int
#     order_type: int
#     episodes: list[Episode]


# class Series(TypedDict):
#     seasons: list[Season]
#     url: Optional[str]
#     tvdb_id: str
#     tvdb_title: Any


# def is_episode(val: Any) -> TypeGuard[Episode]:
#     result = True
#     if "number" not in val or type(val["number"]) is not int:
#         result = False
#     return result


# def collect_series_meta(
#     imdb_id, title, client: TvdbClient
# ) -> Union[Series, None]:
#     series, series_url = client.get_series(imdb_id, title)
#     result = None
#     if series:
#         dvd_and_aired_seasons = [
#             season for season in series["seasons"] if season["type"]["id"] in [1, 2]
#         ]

#         def filter_season(season_number, seasons):
#             return [season for season in seasons if season["number"] == season_number]

#         def filter_season_id_by_order_type(order_type, seasons):
#             order_type_to_id = {"aired_order": 1, "dvd_order": 2}
#             order_id = order_type_to_id[order_type]
#             season_ids = [s for s in seasons if s["type"]["id"] == order_id]
#             return season_ids[0]["id"]

#         season_number = 0
#         numbered_seasons = filter_season(season_number, dvd_and_aired_seasons)
#         seasons = []
#         while season_number == 0 or len(numbered_seasons) > 0:
#             try:
#                 season_id = filter_season_id_by_order_type(
#                     "dvd_order", numbered_seasons
#                 )
#                 season = client.get_season(season_id)

#                 if len(season["episodes"]) == 0:
#                     season_id = filter_season_id_by_order_type(
#                         "aired_order", numbered_seasons
#                     )
#                     season = client.get_season(season_id)
#             except (KeyError, requests.exceptions.RequestException, IndexError):
#                 try:
#                     season_id = filter_season_id_by_order_type(
#                         "aired_order", numbered_seasons
#                     )
#                     season = client.get_season(season_id)
#                 except (KeyError, requests.exceptions.RequestException, IndexError):
#                     season = None
#                     season_id = None

#             if season:
#                 seasons.append(season)

#             season_number += 1
#             numbered_seasons = filter_season(season_number, dvd_and_aired_seasons)

#         result = Series(
#             {
#                 "seasons": seasons,
#                 "url": series_url,
#                 "tvdb_id": series["id"],
#                 "tvdb_title": series,
#             }
#         )
#     return result
