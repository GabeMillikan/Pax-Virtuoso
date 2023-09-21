from __future__ import annotations

import asyncio
import re

from spotipy import MemoryCacheHandler, Spotify, SpotifyClientCredentials

from config import spotify_client_id, spotify_client_secret

sp = Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
        cache_handler=MemoryCacheHandler(),
    ),
)

TRACK_ID_REGEX = re.compile(r"spotify.com/track/(\w+)")


def extract_track_id(song: str) -> str | None:
    result = TRACK_ID_REGEX.search(song)
    return result.group(1) if result else None


async def get_song_name_from_track_id(track_id: str) -> str:
    track = await asyncio.to_thread(sp.track, track_id)
    if not track or "name" not in track or "artists" not in track:
        return "Never Gonna Give You Up by Rick Astley"

    import json

    print(json.dumps(track, indent=2))

    song_link = track["external_urls"]["spotify"]
    cover_art = max(track["album"]["images"], key=lambda img: img["height"])["url"]
    artist_name = track["artists"][0]["name"]
    artist_url = track["artists"][0]["external_urls"]["spotify"]
    release_date = track["album"]["release_date"]

    print("song_link", song_link)
    print("cover_art", cover_art)
    print("artist_name", artist_name)
    print("artist_url", artist_url)
    print("release_date", release_date)

    return f"{track['name']} by {', '.join(artist.get('name', 'Rick Astley') for artist in track['artists'])}"


async def get_song_name(song: str) -> str:
    result = sp.search(song)
    return await get_song_name_from_track_id(result["tracks"]["items"][0]["id"])


if __name__ == "__main__":
    url = "https://open.spotify.com/track/1TfqLAPs4K3s2rJMoCokcS?si=4e23cbac90054e6e"
    track_id = extract_track_id(url)

    assert track_id == "1TfqLAPs4K3s2rJMoCokcS"
    search_term = asyncio.run(get_song_name_from_track_id(track_id))

    assert (
        search_term
        == "Sweet Dreams (Are Made of This) - Remastered by Eurythmics, Annie Lennox, Dave Stewart"
    )
