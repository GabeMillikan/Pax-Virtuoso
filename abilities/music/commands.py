from __future__ import annotations

import asyncio

import discord
from discord import Interaction, app_commands

from bot import tree

from . import ui
from .streaming import spotify, youtube


@tree.command(description="Plays a song")
@app_commands.describe(song="The URL or name of a song from YouTube or Spotify.")
@app_commands.choices(
    platform=[
        app_commands.Choice(name="YouTube", value="youtube"),
        app_commands.Choice(name="Spotify", value="spotify"),
    ],
)
async def play(interaction: Interaction, song: str, platform: str = "spotify") -> None:
    """
    Plays a song from YouTube or Spotify.
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

    if platform == "youtube" or ("youtube.com" in song or "youtu.be" in song):
        print("begin fetch with youtube")
        audio = await youtube.fetch(song)
    else:
        print("begin fetch with spotify")
        audio = await spotify.fetch(song)
    print("fetch completed, now preloading", audio)
    await audio.preload()
    print("preloaded")

    if isinstance(guild.voice_client, discord.VoiceClient):
        voice_client = guild.voice_client
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()
    print("joined channel")

    if not voice_client.is_playing():
        voice_client.play(
            audio.stream,
            after=lambda e: print(f"Player error: {e}") if e else None,
        )
        embed = ui.embed_song(audio, title_prefix="Now Playing: ")
    else:
        await queue.put((audio, song))
        embed = ui.embed_song(audio, title_prefix="Added to Queue: ")

    embed.add_field(name="Requested By", value=interaction.user.mention)
    embed.add_field(name="Voice Channel", value=channel.mention)
    await interaction.followup.send(embed=embed)

    while voice_client.is_playing() or not queue.empty():
        await asyncio.sleep(1)

        if not voice_client.is_playing() and not queue.empty():
            audio, song = await queue.get()
            voice_client.play(
                audio.stream,
                after=lambda e: print(f"Player error: {e}") if e else None,
            )

            embed = ui.embed_song(audio, title_prefix="Now Playing: ")
            embed.add_field(name="Requested By", value=interaction.user.mention)
            embed.add_field(name="Voice Channel", value=channel.mention)
            await interaction.followup.send(embed=embed)


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

    # TODO: maybe say what the current song is?
    # or at least reply to the relevant "Now Playing" message
    await interaction.followup.send(
        embed=discord.Embed(title="Skipped the Current Song", color=ui.BLUE),
    )


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
    await interaction.followup.send(
        embed=discord.Embed(title="Stopped Playing Music", color=ui.BLUE),
    )
