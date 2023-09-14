from __future__ import annotations

import asyncio

import discord
import youtube_dl
from discord import Interaction, app_commands

from bot import tree

youtube_dl.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(
        self: YTDLSource,
        source: discord.AudioSource,
        *,
        data: dict,
        volume: float = 0.5,
    ) -> None:
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = ""

    @classmethod
    async def from_url(
        cls: type,
        url: str,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        stream: bool = False,
    ) -> str:
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(url, download=not stream),
        )
        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]
        return data["title"] if stream else ytdl.prepare_filename(data)


@tree.command(description="Plays a song")
@app_commands.describe(name="The name of the song.")
async def play(interaction: Interaction, name: str) -> None:
    """
    Plays a song from YouTube.
    """
    if isinstance(interaction.user, discord.Member) and interaction.user.voice is None:
        await interaction.response.send_message(
            "You are not connected to a voice channel.",
        )
        return

    channel = interaction.user.voice.channel
    if channel is None:
        await interaction.response.send_message(
            "Error: Unable to find a voice channel.",
        )
        return

    await channel.connect()

    async with interaction.channel.typing():
        filename = await YTDLSource.from_url(name, loop=client.loop)
        player = discord.FFmpegPCMAudio(
            filename,
            **ffmpeg_options,
        )
        interaction.guild.voice_client.play(
            player,
            after=lambda e: print(f"Player error: {e}") if e else None,
        )

    await interaction.response.send_message(f"Now playing: {filename}")
