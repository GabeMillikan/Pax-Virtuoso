from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from math import ceil

from spotipy import MemoryCacheHandler, Spotify, SpotifyClientCredentials

from config import spotify_client_id, spotify_client_secret

from . import youtube
from .common import Song as BaseSong


@dataclass
class SpotifyTrackMetadata:
    youtube_search_term: str
    title: str
    track_id: str
    url: str
    image_url: str
    artist_name: str
    artist_url: str
    released_at: int  # unix timestamp


@dataclass
class Song(BaseSong):
    youtube_song: youtube.Song
    track_id: str
    released_at: int  # unix timestamp

    platform_color: int = 0x1DB954


spotify_client = Spotify(
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


async def get_song_name_from_track_id(track_id: str) -> SpotifyTrackMetadata:
    track = await asyncio.to_thread(spotify_client.track, track_id)
    if not track or "name" not in track or "artists" not in track:
        msg = "Invalid Track ID"
        raise Exception(msg)

    song_link = track["external_urls"]["spotify"]
    cover_art = max(track["album"]["images"], key=lambda img: img["height"])["url"]
    artist_name = track["artists"][0]["name"]
    artist_url = track["artists"][0]["external_urls"]["spotify"]
    release_date = track["album"]["release_date"]

    return SpotifyTrackMetadata(
        youtube_search_term=f"{track['name']} by {', '.join(artist.get('name', 'Rick Astley') for artist in track['artists'])}",
        title=track["name"],
        track_id=track_id,
        url=song_link,
        image_url=cover_art,
        artist_name=artist_name,
        artist_url=artist_url,
        released_at=int(
            datetime.fromisoformat(release_date)
            .replace(tzinfo=timezone.utc)
            .timestamp(),
        ),
    )


async def get_song_name(song: str) -> SpotifyTrackMetadata:
    result = spotify_client.search(song)
    return await get_song_name_from_track_id(result["tracks"]["items"][0]["id"])


async def fetch(song: str) -> Song:
    if track_id := extract_track_id(song):
        meta = await get_song_name_from_track_id(track_id)
    else:
        meta = await get_song_name(song)

    youtube_song = await youtube.fetch(meta.youtube_search_term)
    return Song(
        youtube_song=youtube_song,
        track_id=meta.track_id,
        title=meta.title,
        artist=meta.artist_name,
        artist_url=meta.artist_url,
        url=meta.url,
        image_url=meta.image_url,
        duration=youtube_song.duration,
        released_at=meta.released_at,
        stream=youtube_song.stream,
    )


if __name__ == "__main__":
    url = "https://open.spotify.com/track/1TfqLAPs4K3s2rJMoCokcS?si=4e23cbac90054e6e"
    track_id = extract_track_id(url)

    assert track_id == "1TfqLAPs4K3s2rJMoCokcS"
    search_term = asyncio.run(get_song_name_from_track_id(track_id))

    assert (
        search_term
        == "Sweet Dreams (Are Made of This) - Remastered by Eurythmics, Annie Lennox, Dave Stewart"
    )
