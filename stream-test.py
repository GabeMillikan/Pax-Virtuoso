from dataclasses import dataclass
from typing import Any

from yt_dlp import YoutubeDL

ytdl_options = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
}


@dataclass
class AudioFormat:
    id: str
    data_url: str
    extension: str
    codec: str
    bit_rate: int | float
    has_video: bool

    def rank(self) -> tuple[bool, int | float]:
        """
        Returns a comparable tuple that ranks the format.
        Lower values indicate better formats.

        So if `a.rank() > b.rank()`, then `b` is a better format than a.

        A format is 'good' if:
        1. It is not muxed with a video (in order to stream the audio
           we would need to _also_ stream the video and use ffmpeg to
           separate the streams - WASTEFUL)
        2. Has a high bitrate (for a higher quality sound)
        """
        return (self.has_video, self.bit_rate)


def api_value_truthy(youtube_api_value: Any) -> bool:
    """
    Checks whether or not a raw value coming from YouTube is 'truthy'.

    An API value is 'truthy' if it is _not_ one of the following:
        - 'none'
        - None
        - False
    """
    # Sometimes YouTube will interchange these values, seemingly at random.
    # I'm not really sure why.
    return youtube_api_value not in {"none", None, False}


def select_audio_formats(formats: list[dict]) -> list[AudioFormat]:
    """
    Selects formats which:
        - are 'valid' (have all of the required data present)
        - have an audio stream
        - are not DRM-protected
    """
    return [
        AudioFormat(
            id=fmt["format_id"],
            data_url=fmt["url"],
            extension=fmt["audio_ext"],
            codec=fmt["acodec"],
            bit_rate=(
                fmt["abr"] if isinstance(fmt["abr"], float | int) else float(fmt["abr"])
            ),
            has_video=(
                api_value_truthy(fmt.get("vcodec"))
                or api_value_truthy(fmt.get("video_ext"))
            ),
        )
        for fmt in formats
        if (
            api_value_truthy(fmt.get("format_id"))
            and api_value_truthy(fmt.get("url"))
            and api_value_truthy(fmt.get("audio_ext"))
            and api_value_truthy(fmt.get("acodec"))
            and api_value_truthy(fmt.get("abr"))
            and not api_value_truthy(fmt.get("has_drm"))
        )
    ]


class YouTubeParseFailure(Exception):
    pass


with YoutubeDL(ytdl_options) as ytdl:
    # this is a 24-hour video whose audio file is 317 MB
    # That's way too big to download all at once
    # so we'll need to stream it...
    video_info = ytdl.extract_info(
        "https://www.youtube.com/watch?v=3Lfr3BhvkQY",
        download=False,
    )

    if not isinstance(video_info, dict) or "formats" not in video_info:
        msg = "Could not find the relevant metadata."
        raise YouTubeParseFailure(msg)

    audio_formats = select_audio_formats(video_info["formats"])
    if not audio_formats:
        msg = "No audio streams found."
        raise YouTubeParseFailure(msg)

    audio_format = min(audio_formats, key=AudioFormat.rank)

    print("TODO: stream the data from", audio_format.data_url)
    if audio_format.has_video:
        print("I'll need to stream the video & audio, and separate out the audio")
