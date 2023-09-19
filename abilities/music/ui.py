import discord

from .youtube import Song

GREEN = 0x8EC356
BLUE = 0x51A8DB


def embed_song(song: Song, title_prefix: str = "Now Playing: ") -> discord.Embed:
    e = discord.Embed(title=f"{title_prefix}{song.title}", url=song.url, color=GREEN)
    e.set_thumbnail(url=song.thumbnail_url)

    e.add_field(
        name="Channel",
        value=f"[{song.uploader.nickname}]({song.uploader.url})\n{song.uploader.subscribers:,} Subscribers",
    )

    e.add_field(
        name="Duration",
        value=(
            f"{song.duration // 60:d}:{song.duration % 60:02d}"
            if song.duration < 3600
            else f"{song.duration // 3600:d}:{song.duration // 60 % 60:02d}:{song.duration % 60:02d}"
        ),
    )

    e.add_field(name="Views", value=f"{song.view_count:,}")

    e.add_field(
        name="Upload Date",
        value=f"<t:{song.timestamp}:D> (<t:{song.timestamp}:R>)",
    )
    return e
