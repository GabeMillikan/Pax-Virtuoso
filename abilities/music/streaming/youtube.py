from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from math import ceil
from typing import Callable, TypeVar

from .common import BufferedOpusAudioSource, transmux_to_ogg_opus
from .common import Song as BaseSong


@dataclass
class Song(BaseSong):
    video_id: str
    view_count: int
    uploaded_at: int  # unix timestamp
    subscribers: int


T = TypeVar("T")
D = TypeVar("D")


def convert(data: D, converter: Callable[[D], T], default: T) -> T:
    try:
        return converter(data)
    except Exception:
        return default


def fetch_synchronously(song: str) -> Song:
    """
    Assumes that `yt-dlp` and `ffmpeg` are installed on your PATH.
    """
    download_process = subprocess.Popen(
        [
            "yt-dlp",
            # Video information
            "--print",
            "before_dl:id",
            "--print",
            "before_dl:title",
            "--print",
            "before_dl:thumbnail",
            "--print",
            "before_dl:upload_date",
            "--print",
            "before_dl:duration",
            "--print",
            "before_dl:view_count",
            # Uploader information
            "--print",
            "before_dl:uploader",
            "--print",
            "before_dl:channel_url",
            "--print",
            "before_dl:channel_follower_count",
            # Download options
            "--no-simulate",
            "--default-search",
            "ytsearch",
            "--format",
            "bestaudio/best",
            song,
            "-o",
            "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=-1,
    )
    assert download_process.stdout
    assert download_process.stderr
    printed_info_stream = download_process.stderr

    encoded_audio_stream = transmux_to_ogg_opus(download_process.stdout)

    (
        video_id,
        title,
        thumbnail,
        upload_date,
        duration,
        view_count,
        uploader,
        channel_url,
        channel_follower_count,
    ) = (printed_info_stream.readline().decode().strip() for _ in range(9))

    return Song(
        artist=uploader,
        artist_url=channel_url,
        video_id=video_id,
        url=f"https://www.youtube.com/watch?v={video_id}",
        title=title,
        image_url=thumbnail,
        duration=ceil(convert(duration, float, 0.0)),
        view_count=convert(view_count, int, 0),
        uploaded_at=convert(
            upload_date,
            lambda d: int(
                datetime.strptime(d, "%Y%m%d").replace(tzinfo=timezone.utc).timestamp(),
            ),
            0,
        ),
        subscribers=convert(channel_follower_count, int, 0),
        stream=BufferedOpusAudioSource(encoded_audio_stream),
    )


async def fetch(song: str) -> Song:
    x = await asyncio.to_thread(fetch_synchronously, song)
    return x
