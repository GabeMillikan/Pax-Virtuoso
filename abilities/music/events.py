import time

import discord

from bot import client

from .song_player import SongPlayer


@client.event
async def on_voice_state_update(
    member: discord.Member,
    _before: discord.VoiceState,
    _after: discord.VoiceState,
) -> None:
    song_player = SongPlayer.get(member.guild)
    if not song_player or not song_player.voice_client:
        return

    channel_member_ids = {
        member.id for member in song_player.voice_client.channel.members
    }
    listeners = channel_member_ids - {client.user.id if client.user else None}

    if not listeners:
        song_player.stop()
        await song_player.voice_client.disconnect()
