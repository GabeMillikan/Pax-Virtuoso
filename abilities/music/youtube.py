import asyncio
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


class BufferedAudioSource(discord.AudioSource):
    """
    Wraps an existing AudioSource, with an additional "peek" method.
    This allows the source to be buffered for up to one packet.
    """

    def __init__(self, source: discord.AudioSource):
        self.source = source
        self.peeked_packet: bytes | None = None

    async def peek(self) -> bytes:
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


async def stream(song: str) -> discord.AudioSource:
    """
    Initiates a YouTube download via yt-dlp and pipes that through
    FFMPEG to convert it to the OPUS format.

    Then, waits until the first OPUS packet to be ready for upload to Discord.

    Finally, returns a discord.AudioSource for the song.
    """
    audio_source = await asyncio.to_thread(to_audio_source, song)

    buffered_audio_source = BufferedAudioSource(audio_source)
    await buffered_audio_source.peek()

    return buffered_audio_source
