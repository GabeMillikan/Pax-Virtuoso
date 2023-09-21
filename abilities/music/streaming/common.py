from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from typing import IO

import discord
from discord.oggparse import OggStream

OPUS_APPLICATION = "audio"
OPUS_FRAME_DURATION = 20  # milliseconds
OPUS_SAMPLE_RATE = 48000  # hertz
OPUS_CHANNELS = 2  # stereo


class BufferedOpusAudioSource(discord.AudioSource):
    def __init__(self: BufferedOpusAudioSource, stream: IO[bytes]) -> None:
        self.stream = OggStream(stream)
        self.packets_iterator = self.stream.iter_packets()
        self.peeked_packet: bytes | None = None

    def read(self: BufferedOpusAudioSource) -> bytes:
        if self.peeked_packet is not None:
            packet = self.peeked_packet
            self.peeked_packet = None
        else:
            packet = next(self.packets_iterator, b"")

        return packet

    def peek(self: BufferedOpusAudioSource) -> bytes:
        """
        Waits for and returns the next packet from the AudioSource
        without actually removing that packet from the AudioSource.
        """
        if self.peeked_packet is None:
            self.peeked_packet = self.read()

        return self.peeked_packet

    @staticmethod
    def is_opus() -> bool:
        return True


def transmux_to_ogg_opus(audio_data_stream: IO[bytes]) -> IO[bytes]:
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
            "-application",
            OPUS_APPLICATION,
            "-frame_duration",
            str(OPUS_FRAME_DURATION),
            "-ar",
            str(OPUS_SAMPLE_RATE),
            "-ac",
            str(OPUS_CHANNELS),
            "pipe:1",
        ],
        stdin=audio_data_stream,
        stdout=subprocess.PIPE,
    )
    assert encoding_process.stdout

    return encoding_process.stdout


@dataclass
class Song:
    title: str
    artist: str
    artist_url: str
    url: str
    image_url: str
    duration: int  # seconds
    stream: BufferedOpusAudioSource

    async def preload(self: Song) -> None:
        """
        Simply waits until first packet of the song is available.
        """
        await asyncio.to_thread(self.stream.peek)
