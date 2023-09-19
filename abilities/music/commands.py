from __future__ import annotations

import asyncio

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
    queue = asyncio.Queue()
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

    if not voice_client.is_playing():
        voice_client.play(
            audio_source,
            after=lambda e: print(f"Player error: {e}") if e else None,
        )
        await interaction.followup.send(f"Now playing: {song}")
    else:
        await interaction.followup.send(f"Added {song} to the queue.")
        await queue.put((audio_source, song))

    while voice_client.is_playing() or not queue.empty():
        await asyncio.sleep(1)

        if not voice_client.is_playing() and not queue.empty():
            audio_source, song = await queue.get()
            voice_client.play(
                audio_source,
                after=lambda e: print(f"Player error: {e}") if e else None,
            )
            await interaction.followup.send(f"Now playing: {song}")

    await voice_client.disconnect(force=False)


@tree.command(description="Skips the current song in the queue")
async def skip(interaction: Interaction) -> None:
    """
    Skips the current song in the queue.
    """
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "I cannot skip music in DMs.",
        )
        return

    if guild.voice_client is None:
        await interaction.response.send_message(
            "I am not playing music.",
        )
        return

    voice_client = None
    if isinstance(guild.voice_client, discord.VoiceClient):
        voice_client = guild.voice_client

    if voice_client is None or not voice_client.is_playing():
        await interaction.response.send_message(
            "There is no music playing to skip.",
        )
        return

    voice_client.stop()
    await interaction.response.defer()
    await interaction.followup.send("Skipped the current song.")


@tree.command(description="Stops playing music")
async def stop(interaction: Interaction) -> None:
    """
    Stops playing music.
    """
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "I cannot stop music in DMs.",
        )
        return

    if guild.voice_client is None:
        await interaction.response.send_message(
            "I am not playing music.",
        )
        return

    await interaction.response.defer()
    await guild.voice_client.disconnect(force=False)
    await interaction.followup.send("Stopped playing music.")
