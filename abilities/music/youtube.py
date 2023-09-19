from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from datetime import datetime
from math import ceil
from typing import IO, Any, Callable, TypeVar

import discord
from discord.oggparse import OggStream


class OpusAudioSource(discord.AudioSource):
    def __init__(self, stream: IO[bytes]) -> None:
        self.stream = OggStream(stream)
        self.packets_iterator = self.stream.iter_packets()

    def read(self) -> bytes:
        return next(self.packets_iterator, b"")

    def is_opus(self) -> bool:
        return True


class BufferedAudioSource(discord.AudioSource):
    """
    Wraps an existing AudioSource, with an additional "peek" method.
    This allows the source to be buffered for up to one packet.
    """

    def __init__(self, source: discord.AudioSource) -> None:
        self.source = source
        self.peeked_packet: bytes | None = None

    def peek(self) -> bytes:
        """
        Waits for and returns the next packet from the AudioSource
        without actually removing that packet from the AudioSource.
        """
        self.peeked_packet = self.read()
        return self.peeked_packet

    def read(self) -> bytes:
        if self.peeked_packet is not None:
            pp, self.peeked_packet = self.peeked_packet, None
            return pp

        return self.source.read()

    def is_opus(self) -> bool:
        return self.source.is_opus()


@dataclass
class Uploader:
    id: str
    nickname: str
    url: str
    subscribers: int


@dataclass
class Song:
    id: str
    title: str
    thumbnail_url: str
    duration: int
    view_count: int
    timestamp: int
    uploader: Uploader
    stream: BufferedAudioSource

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.id}"

    async def preload(self):
        """
        Simply waits until first packet of the song is available.
        """
        await asyncio.to_thread(self.stream.peek)


T = TypeVar("T")
D = TypeVar("D")


def convert(data: D, converter: Callable[[D], T], default: T) -> T:
    try:
        return converter(data)
    except:
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
            "before_dl:uploader_id",
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
    binary_youtube_data_stream = download_process.stdout

    encoding_process = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-f",
            "opus",
            "pipe:1",
        ],
        stdin=binary_youtube_data_stream,
        stdout=subprocess.PIPE,
    )
    assert encoding_process.stdout
    encoded_audio_stream = encoding_process.stdout

    (
        id,
        title,
        thumbnail,
        upload_date,
        duration,
        view_count,
        uploader_id,
        uploader,
        channel_url,
        channel_follower_count,
    ) = (printed_info_stream.readline().decode().strip() for _ in range(10))

    return Song(
        id=id,
        title=title,
        thumbnail_url=thumbnail,
        duration=ceil(convert(duration, float, 0.0)),
        view_count=convert(view_count, int, 0),
        timestamp=convert(
            upload_date,
            lambda d: int(datetime.strptime(d, "%Y%m%d").timestamp()),
            0,
        ),
        uploader=Uploader(
            id=uploader_id,
            nickname=uploader,
            url=channel_url,
            subscribers=convert(channel_follower_count, int, 0),
        ),
        stream=BufferedAudioSource(OpusAudioSource(encoded_audio_stream)),
    )


async def fetch(song: str) -> Song:
    return await asyncio.to_thread(fetch_synchronously, song)
