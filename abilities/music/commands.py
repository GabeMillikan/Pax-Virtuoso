from __future__ import annotations

import discord
from discord import Interaction, app_commands

from bot import client, tree

from .youtube import YTDLSource


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
