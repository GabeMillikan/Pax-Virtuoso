from __future__ import annotations

import asyncio
from pathlib import Path

import discord
import yt_dlp

ytdl_download_directory = Path(__file__).parent / "downloads"
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
    "outtmpl": str(ytdl_download_directory / "%(title)s.%(ext)s"),
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
