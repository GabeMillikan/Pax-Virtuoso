from __future__ import annotations

import discord
from discord import Interaction, app_commands

from bot import tree

from . import ui
from .song_player import SongPlayer
from .streaming import spotify, youtube

MAXIMUM_VOLUME = 150  # percent
playback_volume = 1.0


async def song_autocomplete(
    interaction: discord.Interaction,  # noqa
    current: str,
) -> list[app_commands.Choice[str]]:
    current = current.strip()
    if not current:
        return []

    tracks = await spotify.search(current)
    return [
        app_commands.Choice(
            name=track.youtube_search_term[:100],
            value=track.url if len(track.url) < 100 else track.title[:100],
        )
        for track in tracks[:10]
    ]


@tree.command(description="Sets the volume")
@app_commands.describe(volume="The volume to play at, such as '50' for half volume.")
async def volume(interaction: Interaction, volume: float) -> None:
    global playback_volume
    if volume < 0:
        await interaction.response.send_message(
            "Volume cannot be negative.",
            ephemeral=True,
        )
        return

    if volume > MAXIMUM_VOLUME:
        await interaction.response.send_message(
            f"Maximum acceptable volume is {MAXIMUM_VOLUME}% (you entered {volume:.0f}%).",
            ephemeral=True,
        )
        return

    playback_volume = volume / 100
    await interaction.response.send_message(
        embed=discord.Embed(
            title=f"Volume Set To {volume:.4g}%",
            color=ui.BLUE,
        ),
    )


@tree.command(description="Plays a song")
@app_commands.describe(song="The URL or name of a song from YouTube or Spotify.")
@app_commands.autocomplete(
    song=song_autocomplete,
)
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
        audio = await youtube.fetch(song)
    else:
        audio = await spotify.fetch(song)

    song_player = SongPlayer.get_or_create(guild)
    await song_player.play_or_queue(
        audio,
        channel,
        interaction.user,
        interaction.followup,
    )


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

    song_player = SongPlayer.get(guild)

    if not song_player or not song_player.currently_playing:
        await interaction.response.send_message(
            "I am not playing music.",
            ephemeral=True,
            delete_after=3,
        )
        return

    skipping = song_player.currently_playing

    embed = discord.Embed(
        title=f"Skipped: {skipping.song.title}",
        color=ui.BLUE,
        url=skipping.song.url,
    )
    embed.set_thumbnail(url=skipping.song.image_url)
    if isinstance(skipping.song, youtube.Song):
        embed.add_field(
            name="Channel",
            value=f"[{skipping.song.artist}]({skipping.song.artist_url})\n{skipping.song.subscribers:,} Subscribers",
        )
    else:
        embed.add_field(
            name="Artist",
            value=f"[{skipping.song.artist}]({skipping.song.artist_url})",
        )

    await interaction.response.send_message(embed=embed)
    song_player.skip_current_song()


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

    song_player = SongPlayer.get(guild)
    skipped_song_count = len(song_player.queued_songs) if song_player else 0

    if skipped_song_count <= 0:
        await interaction.response.send_message(
            "I am not playing music.",
            ephemeral=True,
            delete_after=3,
        )
        return
    assert song_player is not None

    song_player.stop()
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Stopped Playing Music",
            description=f"{skipped_song_count} song(s) were removed from the queue.",
            color=ui.BLUE,
        ),
    )
