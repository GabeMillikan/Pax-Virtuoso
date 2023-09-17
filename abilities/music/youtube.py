import subprocess
from typing import IO

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


def to_audio_source(song: str) -> discord.AudioSource:
    """
    Assumes that `yt-dlp` and `ffmpeg` are installed on your PATH.
    """

    download_process = subprocess.Popen(
        [
            "yt-dlp",
            "--quiet",
            "--default-search",
            "ytsearch",
            "--format",
            "bestaudio/best",
            song,
            "-o",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    assert download_process.stdout

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
        stdin=download_process.stdout,
        stdout=subprocess.PIPE,
    )
    assert encoding_process.stdout

    return OpusAudioSource(encoding_process.stdout)
