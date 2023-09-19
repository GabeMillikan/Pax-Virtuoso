from __future__ import annotations

import asyncio

import discord
from discord import Interaction, app_commands

from bot import tree

from . import ui, youtube


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

    audio = await youtube.fetch(song)

    embed = ui.embed_song(audio)
    embed.add_field(name="Requested By", value=interaction.user.mention)
    embed.add_field(name="Voice Channel", value=channel.mention)

    canceled = False

    async def cancel(cancel_interaction: discord.Interaction) -> None:
        nonlocal canceled

        canceled = True
        # TODO: account for the song queue
        if cancel_interaction.guild and cancel_interaction.guild.voice_client:
            await cancel_interaction.guild.voice_client.disconnect(force=True)

        await cancel_interaction.response.send_message(
            "Canceled!",
            ephemeral=True,
            delete_after=5,
        )
        await interaction.delete_original_response()

    view = ui.CancelView(on_cancel=cancel)
    await interaction.followup.send(embed=embed, view=view)

    async def remove_view_after_delay():
        await asyncio.sleep(10)

        if canceled:
            return

        await interaction.edit_original_response(view=None)

    asyncio.create_task(remove_view_after_delay())

    await audio.preload()
    if isinstance(guild.voice_client, discord.VoiceClient):
        voice_client = guild.voice_client
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    if not voice_client.is_playing():
        voice_client.play(
            audio.stream,
            after=lambda e: print(f"Player error: {e}") if e else None,
        )
        await interaction.followup.send(f"Now playing: {song}")
    else:
        await interaction.followup.send(f"Added {song} to the queue.")
        await queue.put((audio, song))

    while voice_client.is_playing() or not queue.empty():
        await asyncio.sleep(1)

        if not voice_client.is_playing() and not queue.empty():
            audio, song = await queue.get()
            voice_client.play(
                audio.stream,
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
    await interaction.followup.send(
        embed=discord.Embed(title="Stopped Playing Music", color=ui.BLUE),
    )
