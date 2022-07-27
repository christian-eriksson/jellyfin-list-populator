# Jellyfin list populator

Scripts to create and populate jellyfin playlists and collections from a list
of imdb titles. The list should have the following fields:

```csv
imdb_id,title,[seasons],[episodes]
```

Where `seasons` and `episodes` are `|`-separated lists of the season/-s and
episode/-s we want to add for the particular title. The fields `seasons` and
`episodes` are optional (but to have the `episodes` field you should also have
the `seasons` field).

Such lists can be created by hand or by utilising scripts similar to the ones
found in [Movie Lists Parsers](https://github.com/christian-eriksson/movie-list-parsers).

## Create and populate playlist

**Usage:**

```sh
./jellyfin_playlist_populator.py --url <URL> --key <API_KEY> --user <JELLYFIN_USER> --list <LIST_PATH> [--tvdb-key <TVDB_API_KEY> --tvdb-pin <TVDB_PIN>] [--server-content <SERVER_CONTENT_JSON>] <PLAYLIST_NAME>
```

**Output:** Populates the playlist `<PLAYLIST_NAME>` with the content of the
list found at `<LIST_PATH>` if there is a title on the server that matches. The
script will create the playlist if it doesn't exist.

**Input:**

The `<PLAYLIST_NAME>` is a string, naming the playlist to be populated (and
maybe created). The `<LIST_PATH>` is a path on the file system to a list in
csv format, the fields and format of the fields in the list is described above.

For the script to know where to create the list you need to point to you
Jellyfin instance with `<URL>`, e.g. `http://media.example.com`. And you
need to create an `<API_KEY>`, login to your Jellyfin instance and go to
`Dashboard -> API Keys`, click the `+` button to generate your key. The
`<JELLYFIN_USER>` could be (I believe) any username that exists on your server.

Extracting the server content can take a long time. If you plan to run the
script multiple time you can extract the server content (see the instructions
for the `get_server_content.py` script) and store it as a cache in a json file.
You can then pass this json file in the `--server-content` option. If this
option is provided you don't need to provide any TVDB credentials.

The optional options `<TVDB_API_KEY>` and `<TVDB_PIN>` allows the script to
include special features among the titles to add to a collection or playlist.
As these doesn't have imdb ids registered on the Jellyfin servers they cannot
be matched. This is done in the same way as in the `get_server_content.py`
script described below, see that description for alternatives if you cannot
obtain TVDB API credentials.

**Example:**

```sh
./jellyfin_playlist_populator.py --url https://media.example.com --key abfhf35832b1bb200f --user john --list mcu_chronological.csv --tvdb-key d368a2c4-6f26-4d98-b7c7-082525a9761e --tvdb-pin HDFG43KL "MCU in Chronological Order"
```

or

```sh
./jellyfin_playlist_populator.py --url https://media.example.com --key abfhf35832b1bb200f --user john --list mcu_chronological.csv --server-content server_content.json "MCU in Chronological Order"
```

Will create the playlist "MCU in Chronological Order" if it doesn't exist and
populate it with the items in `mcu_chronologiacl.csv` that are also present in
`server_content.json` (or on the server if this option was omitted). It will try
to create this on the Jellyfin instance available on `https://media.example.com`.

## Save server content to file

You can use the `get_server_content.py` to extract the content from your
Jellyfin server and decorate any special features with imdb ids (if possible).
The output can then be used to pass to a populator as a cache to save time.

**Usage:**

```sh
./get_server_content.py --url <URL> --key <API_KEY> --user <JELLYFIN_USER> [--tvdb-key <TVDB_API_KEY> --tvdb-pin <TVDB_PIN>]
```

**Output:** prints a json formatted string to standard out with the server
content.

**Input:**

For the script to know where to create the list you need to point to you
Jellyfin instance with `<URL>`, e.g. `http://media.example.com`. And you need to
create an `<API_KEY>`, login to your Jellyfin instance and go to
`Dashboard -> API Keys`, click the `+` button to generate your key. The
`<JELLYFIN_USER>` could be (I believe) any username that exists on your server.

Special features don't have imdb ids in the output from the Jellyfin server. We
solve this by doing a search using the [TVDB API](https://thetvdb.github.io/v4-api/#/Search/getSearchResults)
and see if we can get a match and an IMDB ID there. You need to [get access](https://thetvdb.com/api-information)
to use it. If you cannot get access you will need to move the special features
into the main movie or series collections and let Jellyfin identify them to get
an IMDB id for them.

This is useful if there are shorts that belong to the story, for example: the
Marvel Cinematic Universe and Fast and Furious franchises have a few shorts that
ties in to the overall stories.

If you have a special feature that represents a whole season you can append
` Season X` to the name on the Jellyfin server and the script will pick that up.
For example I had the seasons of [WHIH News Front](https://www.imdb.com/title/tt5296048/?ref_=fn_al_tt_1)
as single files per season on the server. I names these special features
`WHIH News Front Season 1` and `WHIH News Front Season 2` on my server. This
assumes that the correct title (with imdb id `tt5296048` in the example) is
present in the csv list given to the script and marked with a matching season.
