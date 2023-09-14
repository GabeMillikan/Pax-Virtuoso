from __future__ import annotations

import asyncio

import discord
import yt_dlp
from discord import Interaction, app_commands

from bot import client, tree

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
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


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
    guild = interaction.guild
    member = interaction.user
    if not isinstance(member, discord.Member) or not guild:
        if guild:
            member = await guild.fetch_member(member.id)
        else:
            await interaction.response.send_message(
                "I cannot play music in DMs.",
            )
            return

    if member.voice is None:
        await interaction.response.send_message(
            "You are not connected to a voice channel.",
        )
        return

    channel = member.voice.channel
    if channel is None:
        await interaction.response.send_message(
            "Error: Unable to find a voice channel.",
        )
        return

    await interaction.response.defer()

    if isinstance(interaction.channel, discord.abc.Messageable):
        async with interaction.channel.typing():
            filename = await YTDLSource.from_url(name, loop=client.loop)
    else:
        filename = await YTDLSource.from_url(name, loop=client.loop)

    if isinstance(guild.voice_client, discord.VoiceClient):
        voice_client = guild.voice_client
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    player = discord.FFmpegPCMAudio(
        filename,
        options="-vn",  # no video
    )
    voice_client.play(
        player,
        after=lambda e: print(f"Player error: {e}") if e else None,
    )

    await interaction.followup.send(f"Now playing: {filename}")
