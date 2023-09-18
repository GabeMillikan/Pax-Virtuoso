from __future__ import annotations

import discord
from discord import Interaction, app_commands

from bot import tree

from . import youtube


@tree.command(description="Plays a song")
@app_commands.describe(song="The URL or name of a YouTube video.")
async def play(interaction: Interaction, song: str) -> None:
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
    audio_source = await youtube.stream(song)

    if isinstance(guild.voice_client, discord.VoiceClient):
        voice_client = guild.voice_client
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    voice_client.play(
        audio_source,
        after=lambda e: print(f"Player error: {e}") if e else None,
    )

    await interaction.followup.send(f"Now playing: {song}")
