import discord

from .streaming.spotify import Song as SpotifySong
from .streaming.youtube import Song as YoutubeSong

BLUE = 0x51A8DB


def embed_song(
    song: YoutubeSong | SpotifySong,
    title_prefix: str = "Now Playing: ",
) -> discord.Embed:
    e = discord.Embed(
        title=f"{title_prefix}{song.title}",
        url=song.url,
        color=song.platform_color,
    )
    e.set_thumbnail(url=song.image_url)

    e.add_field(
        name="Duration",
        value=(
            f"{song.duration // 60:d}:{song.duration % 60:02d}"
            if song.duration < 3600
            else f"{song.duration // 3600:d}:{song.duration // 60 % 60:02d}:{song.duration % 60:02d}"
        ),
    )

    if isinstance(song, YoutubeSong):
        e.insert_field_at(
            index=0,
            name="Channel",
            value=f"[{song.artist}]({song.artist_url})\n{song.subscribers:,} Subscribers",
        )

        e.add_field(name="Views", value=f"{song.view_count:,}")

        e.add_field(
            name="Upload Date",
            value=f"<t:{song.uploaded_at}:D> (<t:{song.uploaded_at}:R>)",
        )
    else:
        e.insert_field_at(
            index=0,
            name="Artist",
            value=f"[{song.artist}]({song.artist_url})",
        )

        e.add_field(name="Youtube", value=f"[link]({song.youtube_song.url})")

        e.add_field(
            name="Release Date",
            value=f"<t:{song.released_at}:D> (<t:{song.released_at}:R>)",
        )

    return e
