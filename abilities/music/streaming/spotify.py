from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar

from cachetools import TTLCache
from spotipy import MemoryCacheHandler, Spotify, SpotifyClientCredentials

from config import spotify_client_id, spotify_client_secret

from . import youtube
from .common import Song as BaseSong


class InvalidTrack(Exception):
    pass


@dataclass
class SpotifyTrackMetadata:
    cache: ClassVar[TTLCache] = TTLCache(100, 15 * 60)  # 100 songs for up to 15 minutes

    youtube_search_term: str
    title: str
    track_id: str
    url: str
    image_url: str | None
    artist_name: str
    artist_url: str
    released_at: int  # unix timestamp

    @classmethod
    def from_track_dict(
        cls: type[SpotifyTrackMetadata],
        track_dict: dict,
    ) -> SpotifyTrackMetadata:
        try:
            track_id = track_dict["id"]
            title = track_dict["name"]
            song_link = track_dict["external_urls"]["spotify"]
            if track_dict["album"]["images"]:
                cover_art = max(
                    track_dict["album"]["images"],
                    key=lambda img: img["height"],
                )["url"]
            else:
                cover_art = None

            artist_name = track_dict["artists"][0]["name"]
            artist_url = track_dict["artists"][0]["external_urls"]["spotify"]
            release_date = track_dict["album"]["release_date"]

            artist_names = [artist["name"] for artist in track_dict["artists"]]
        except KeyError as e:
            msg = "Track was in an unexpected format."
            raise InvalidTrack(msg) from e

        if len(artist_names) <= 2:
            # by {A}
            # by {A} and {B}
            joined_artist_names = " and ".join(artist_names)
        else:
            # by {A}, {B}, and {C}
            artist_names[-1] = f"and {artist_names[-1]}"
            joined_artist_names = ", ".join(artist_names)

        track = cls(
            youtube_search_term=f'"{title}" by {joined_artist_names}',
            title=title,
            track_id=track_id,
            url=song_link,
            image_url=cover_art,
            artist_name=artist_name,
            artist_url=artist_url,
            released_at=int(
                datetime.fromisoformat(
                    release_date if "-" in release_date else f"{release_date}-01-01",
                )
                .replace(tzinfo=timezone.utc)
                .timestamp(),
            ),
        )

        cls.cache[track_id] = track
        return track


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


async def search(query: str) -> list[SpotifyTrackMetadata]:
    """
    Returns a dictionary mapping matched track IDs to f"{track title} by {track author(s)}"
    """
    result = await asyncio.to_thread(spotify_client.search, query)
    if not result or "tracks" not in result or "items" not in result["tracks"]:
        return []

    tracks = [
        SpotifyTrackMetadata.from_track_dict(track_dict)
        for track_dict in result["tracks"]["items"]
    ]

    # Remove duplicate search results (which appear surprisingly often??)
    seen_youtube_search_terms = set()
    seen_track_ids = set()
    unique_tracks: list[SpotifyTrackMetadata] = []
    for track in tracks:
        if (
            track.youtube_search_term not in seen_youtube_search_terms
            and track.track_id not in seen_track_ids
        ):
            unique_tracks.append(track)

        seen_youtube_search_terms.add(track.youtube_search_term)
        seen_track_ids.add(track.track_id)

    return unique_tracks


async def get_metadata_by_track_id(track_id: str) -> SpotifyTrackMetadata:
    if track := SpotifyTrackMetadata.cache.get(track_id):
        return track

    try:
        track_dict = await asyncio.to_thread(spotify_client.track, track_id)
    except Exception as e:
        msg = f"Spotify raised API error. {e!r}"
        raise InvalidTrack(msg) from e

    if not track_dict:
        msg = f"Invalid track ID {track_id}"
        raise InvalidTrack(msg)

    return SpotifyTrackMetadata.from_track_dict(track_dict)


async def get_metadata(query: str) -> SpotifyTrackMetadata:
    tracks = await search(query)
    if not tracks:
        msg = "Spotify API did not return any results."
        raise InvalidTrack(msg)

    return tracks[0]


async def fetch(song: str) -> Song:
    if track_id := extract_track_id(song):
        meta = await get_metadata_by_track_id(track_id)
    else:
        meta = await get_metadata(song)

    youtube_song = await youtube.fetch(meta.youtube_search_term)
    return Song(
        youtube_song=youtube_song,
        track_id=meta.track_id,
        title=meta.title,
        artist=meta.artist_name,
        artist_url=meta.artist_url,
        url=meta.url,
        image_url=meta.image_url or youtube_song.image_url,
        duration=youtube_song.duration,
        released_at=meta.released_at,
        stream=youtube_song.stream,
    )
