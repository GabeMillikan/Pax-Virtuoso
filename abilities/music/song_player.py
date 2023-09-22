from __future__ import annotations

import asyncio
from typing import ClassVar

import discord

from .streaming.common import Song


class SongPlayer:
    song_player_by_guild: ClassVar[dict[int, SongPlayer]] = {}

    @classmethod
    def get_or_create(cls: type[SongPlayer], guild: discord.Guild) -> SongPlayer:
        if guild.id not in cls.song_player_by_guild:
            cls.song_player_by_guild[guild.id] = cls(guild)

        return cls.song_player_by_guild[guild.id]

    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.songs: list[Song] = []

    @property
    def currently_playing(self) -> Song | None:
        return self.songs[0] if self.songs else None

    @property
    def voice_client(self) -> discord.VoiceClient | None:
        vc = self.guild.voice_client

        if vc is None:
            return vc

        # This player exclusively uses the standard discord.VoiceClient
        assert isinstance(vc, discord.VoiceClient)

        return vc

    def _play_recursively(self, voice_client: discord.VoiceClient):
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

        def after(e: BaseException | None):
            print(f"Error occurred in SongPlayer: {e!r}. Advancing to the next song.")

            # Remove the current song from the queue (since it's completed)
            self.songs.pop(0)

            # and begin the next one
            self._play_recursively(voice_client)

        voice_client.play(self.currently_playing.stream, after=after)

    async def play_or_queue(self, *, song: Song, channel: discord.VoiceChannel):
        if channel.guild != self.guild:
            msg = f"You're using the wrong SongPlayer, partner. This SongPlayer is for guild {self.guild.id!r}, but that channel is in guild {channel.guild.id!r}."
            raise ValueError(msg)

        self.songs.append(song)
        assert self.currently_playing is not None

        if not self.voice_client:
            await channel.connect()
        elif self.voice_client.channel != channel:
            await self.voice_client.move_to(channel)
        assert self.voice_client is not None

        self._play_recursively(self.voice_client)

    async def skip_current_song(self):
        if not self.songs:
            # there is nothing to skip...
            return

        if self.voice_client:
            # will also call the `after` callback which pops the song
            self.voice_client.stop()
        else:
            self.songs.pop(0)

    async def stop(self):
        # delete everything after the current song
        del self.songs[1:]

        # and skip the current song
        await self.skip_current_song()
