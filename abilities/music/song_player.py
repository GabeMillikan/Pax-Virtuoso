from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

import discord

from . import ui

if TYPE_CHECKING:
    from discord.member import VocalGuildChannel

    from .streaming.common import Song


@dataclass
class QueuedSong:
    song: Song
    requested_by: discord.User | discord.Member
    send_followups_to: discord.Webhook


class SongPlayer:
    song_player_by_guild: ClassVar[dict[int, SongPlayer]] = {}

    @classmethod
    def get(cls: type[SongPlayer], guild: discord.Guild) -> SongPlayer | None:
        return cls.song_player_by_guild.get(guild.id)

    @classmethod
    def get_or_create(cls: type[SongPlayer], guild: discord.Guild) -> SongPlayer:
        if guild.id not in cls.song_player_by_guild:
            cls.song_player_by_guild[guild.id] = cls(guild)

        return cls.song_player_by_guild[guild.id]

    def __init__(self: SongPlayer, guild: discord.Guild) -> None:
        self.guild = guild
        self.queued_songs: list[QueuedSong] = []

    @property
    def currently_playing(self: SongPlayer) -> QueuedSong | None:
        return self.queued_songs[0] if self.queued_songs else None

    @property
    def voice_client(self: SongPlayer) -> discord.VoiceClient | None:
        vc = self.guild.voice_client

        if vc is None:
            return vc

        # This player exclusively uses the standard discord.VoiceClient
        assert isinstance(vc, discord.VoiceClient)

        return vc

    def _play_recursively(self: SongPlayer, voice_client: discord.VoiceClient) -> None:
        if voice_client.is_playing():
            # The voice client _already_ has a recursive `after` callback
            # so we don't need to create another one.
            return

        if not self.currently_playing:
            # No more songs!
            # Time to disconnect.
            asyncio.ensure_future(voice_client.disconnect(), loop=voice_client.loop)
            return

        if not voice_client.is_connected():
            if not self.voice_client:
                # Can't continue playing music if disconnected
                return

            voice_client = self.voice_client

        def after(e: BaseException | None) -> None:
            print(f"Error occurred in SongPlayer: {e!r}. Advancing to the next song.")

            # Remove the current song from the queue (since it's completed)
            self.queued_songs.pop(0)

            # and begin the next one
            self._play_recursively(voice_client)

        queued_song = self.currently_playing

        embed = ui.embed_song(queued_song.song, title_prefix="Now Playing: ")
        embed.add_field(name="Requested By", value=queued_song.requested_by.mention)
        embed.add_field(name="Voice Channel", value=voice_client.channel.mention)
        asyncio.ensure_future(
            queued_song.send_followups_to.send(embed=embed),
            loop=voice_client.loop,
        )

        voice_client.play(queued_song.song.stream, after=after)

    async def play_or_queue(
        self: SongPlayer,
        song: Song,
        channel: VocalGuildChannel,
        requested_by: discord.User | discord.Member,
        send_followups_to: discord.Webhook,
    ) -> None:
        if channel.guild != self.guild:
            msg = f"You're using the wrong SongPlayer, partner. This SongPlayer is for guild {self.guild.id!r}, but that channel is in guild {channel.guild.id!r}."
            raise ValueError(msg)

        if self.currently_playing:
            embed = ui.embed_song(song, title_prefix="Added to Queue: ")
            embed.add_field(name="Requested By", value=requested_by.mention)
            embed.add_field(name="Voice Channel", value=channel.mention)
            await send_followups_to.send(embed=embed)

        self.queued_songs.append(
            QueuedSong(
                song=song,
                requested_by=requested_by,
                send_followups_to=send_followups_to,
            ),
        )
        assert self.currently_playing is not None

        if not self.voice_client:
            await channel.connect()
        elif self.voice_client.channel != channel:
            await self.voice_client.move_to(channel)
        assert self.voice_client is not None

        self._play_recursively(self.voice_client)

    def skip_current_song(self: SongPlayer) -> QueuedSong | None:
        current_song = self.currently_playing
        if not current_song:
            # there is nothing to skip...
            return None

        if self.voice_client:
            # will also call the `after` callback which pops the song
            self.voice_client.stop()
        else:
            self.queued_songs.pop(0)

        return current_song

    def stop(self: SongPlayer) -> None:
        # delete everything after the current song
        del self.queued_songs[1:]

        # and skip the current song
        self.skip_current_song()
