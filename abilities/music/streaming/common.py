from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from math import log
from typing import IO

import discord
from discord.oggparse import OggStream
from pydub import AudioSegment

try:
    import opuslib
except Exception:
    msg = "`opuslib` failed to load. Did you install the Opus codec? Please see ./abilities/music/streaming/opus-binary/README.md"
    raise Exception(msg)

OPUS_APPLICATION = "audio"
OPUS_FRAME_DURATION = 20  # milliseconds
OPUS_SAMPLE_RATE = 48000  # hertz
OPUS_CHANNELS = 2  # stereo
OPUS_SAMPLE_WIDTH = 2  # opus samples are 16 bits
OPUS_FRAME_SIZE = OPUS_SAMPLE_RATE // (1000 // OPUS_FRAME_DURATION)


class BufferedOpusAudioSource(discord.AudioSource):
    def __init__(self: BufferedOpusAudioSource, stream: IO[bytes]) -> None:
        self.stream = OggStream(stream)
        self.packets_iterator = self.stream.iter_packets()
        self.peeked_packet: bytes | None = None

        self.decoder = opuslib.Decoder(OPUS_SAMPLE_RATE, OPUS_CHANNELS)
        self.encoder = opuslib.Encoder(
            OPUS_SAMPLE_RATE, OPUS_CHANNELS, OPUS_APPLICATION
        )
        self.volume: float = 1.0

    @property
    def db_gain(self) -> float:
        """
        Converts self.volume into a Decibel adjustment.

        Uses the same conversion as VLC:
        https://sound.stackexchange.com/a/48502
        """
        if self.volume < 0.01:
            return -float("inf")
        else:
            return 25 * log(self.volume)

    def translate_packet(self, packet: bytes) -> bytes:
        if packet.startswith((b"OpusHead", b"OpusTags")):
            return packet

        pcm_data = self.decoder.decode(packet, OPUS_FRAME_SIZE)

        segment = AudioSegment(
            pcm_data,
            sample_width=2,
            frame_rate=OPUS_SAMPLE_RATE,
            channels=OPUS_CHANNELS,
        )

        segment += self.db_gain

        assert isinstance(segment._data, bytes)
        packet = self.encoder.encode(segment._data, OPUS_FRAME_SIZE)

        return packet

    def read(self: BufferedOpusAudioSource) -> bytes:
        if self.peeked_packet is not None:
            packet = self.peeked_packet
            self.peeked_packet = None
        else:
            try:
                packet = self.translate_packet(next(self.packets_iterator))
            except StopIteration:
                packet = b""

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
