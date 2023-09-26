from __future__ import annotations

import io
import sys
from math import log
from pathlib import Path

import pytest

repository_directory = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repository_directory))

from abilities.music.streaming.common import BufferedOpusAudioSource  # noqa

OPUS_HEADERS = [
    b"OpusHead\x01\x028\x01\x80\xbb\x00\x00\x00\x00\x00",
    b"OpusTags\x0c\x00\x00\x00Lavf60.3.100\x02\x00\x00\x00\x0c\x00\x00\x00language=eng\x1c\x00\x00\x00encoder=Lavc60.3.100 libopus",
]

FULL_VOLUME_PACKETS = [
    b"\xfc\xff\xfe",
    b"\xfc\xff\xfe",
    b"\xfc}\xc7\xbc\xf1\x0b\x0b\xab\x9c(\xcfk\x8e\x15\xdc\x13\xb1t\xe7S\x8a+97p\xd7\x91\xcf\xe5\xa13\x95\xb3$\xca\xfa4\xb0\xb61\xe8\xfb\x9d\xb6\x1b3\x16\xf5[\x10p}\xe2\x90In\xf4LD\xc4\xa2mq;\xcd`\x9f\xbd\xb8\xc0\x14Q\xb5\x0b\x8bT\xac\xb2!+\xf8TR\x06\xdc\xbf@\xc45\"L!\xa5a\xc2\xf5\xe3\xf2\xe0/\xbe\x87CZE\x8f=\xca\x91k>\x8b\xcdj\x9f\xda\xc5\t4{@S\x12\xf0Y\xdc\xb3K\xd6M'\xaa\xc0h#\xe4\x06{\xd9e\xbc\x95h\x1d\x08!\xf3E\xb8\x85\x86N\xeb\xf5/\xeb\xcdG'^\xfa\x1e\"\xd63\xc7f\xd6k9)V\xfdMr\xd0;\xf2\x0f\x98\xf8\x94\xc1=6FQ\xce\x99\t$},\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\xbf\xdb\xecm\x98BA\xb1yc\x1e\xe9\x8arp|\x15\xe1b`'d\x89R\xe0\x14\x96\x80\xea\xdd\xe9\x006\x9fc\xd68\x84\xd3\xcdr\xeeO\xe1~{h\xf6\x05\x93>\xae\xabK\x1d.\x9b\xad\x96\xc5\xc4\x95\x94\xb2@\x05U\n\xb7\xbe\xd9\xa7\xf8l\xc7yCZ\x8c\x03\xb5\xb29yz\xbd\x8b.\xf1\xf0\xb4\x0e%j\xf9\xc2\x92o\xc6\xf0\xb5Y\xfd]\xf7\"4[\xc7\x9d_\xb9\x0c\x04]\x9f\xd0)>\x9cO\xb7\xe1\xb1\xed\xa5l\x95oS\x89\xf9\xf2\xdce\xe3\xb3$(\xc9\\\xd5\x80e\xa0\x00\x85\xca\xb0\xd5[]rr3\xe4\x82\xfc}\xc9\xcd\xa2u\\\x1aU\xd3\x08\xab`B\x04q.\xf4\xf0\xd6\x8cd\xfd\xa4\xfe\xd3\xccl\xede\xe3~\xb2\xab\xfa\xe41X\xc0\xc9I\xdbp\x8a\xc7\x96\x9f\xdbj\xcd\x00\xc2cf\x88N\xf0\xc5|-vx\xd7\xb2\xc1\xb6\xcb",
]

HALF_VOLUME_PACKETS = [
    b"\xfc\xff\xfe",
    b"\xfc\xff\xfe",
    b"\xfc\x7f\xf9@\xe2\x15\xc8\x00\xaa\xf0\x9a\xdb6\x96\xe3{\xeb\x005\x01`au\x08\x7f\xd7\x9d\xd2yA8\x0cW.\x05}\xb3\xb7\xdd\xcb\x93\x1fp\xea%\xbbI\xbc\xa3`\xfat\x8d\x8f\x12\"vC\xbft\xdca\xd8\xe5\x91\xf2\x85\xa9\xb3\xb9i]G\x10\x0f\x8a\xbe\xca\xcb'\xde\xbf\xca\x8b\xe9\xe2\xa8\x9c\xe18Ze\x88w\rX\xf1q\xc5\x14\xeb\t\x1d\xff4H\x9bT\x7fU\xcc'\x1fA\x7f[\xd48\xcbxi3\xd0\xbfj\xa5[!n\x0b\xf3-\x80\xf6\xdb!\x8a\xdb\xa9>[\xb2\xc0\x00\x00\x00\x00\x00\x00\x0f\xf8uG\xb8\xcc\xfe]\x1f\xf1\x17\xedvT\x0c\x85\x9f\xa5\x01\xd1\xc20\xa4\x1b\xa3_Wpw[\xda\xe6\x0e\x10ko\xd9\x86w4\xe6\xa7\x8f*\xb2c\xf1\xdb\t\xd9\xa3*\xd1\xc6\x02\xa4\x13\xcc\x19\xda\xeb\x97Q\xf9\xda\x98\xe1\x7f\x06y\xa3\x96\x8b\x81\xf7X\xa8}\x8b\x81\xff\x8a\x96@\x1c\xa2\x94\x82\x92\x91\x9d*4.\xe4\xed\x97T\xad",
]


@pytest.mark.parametrize(
    ("volume", "expected"),
    [
        (
            0.005,
            (-float("inf"), "Expected negative infinity when volume is less than 0.01"),
        ),
        (
            0.02,
            (
                25 * log(0.02),
                "Expected 25 * log(volume) when volume is greater than or equal to 0.01",
            ),
        ),
    ],
)
def test_db_gain(volume: float, expected: tuple[float, str]) -> None:
    source = BufferedOpusAudioSource(io.BytesIO(b""))
    source.volume = volume
    expected_db_gain, message = expected
    assert source.db_gain == pytest.approx(expected_db_gain), message


@pytest.mark.parametrize(
    ("volume", "packets", "expected_output", "message"),
    [
        # header packets unaffected by volume
        (
            1,
            OPUS_HEADERS[:1],
            OPUS_HEADERS[0],
            "Header packets should not be postprocessed",
        ),
        (
            1,
            OPUS_HEADERS,
            OPUS_HEADERS[-1],
            "Header packets should not be postprocessed",
        ),
        (
            0.5,
            OPUS_HEADERS[:1],
            OPUS_HEADERS[0],
            "Header packets should not be postprocessed",
        ),
        (
            0.5,
            OPUS_HEADERS,
            OPUS_HEADERS[-1],
            "Header packets should not be postprocessed",
        ),
        # volume changes
        (
            0.5,
            OPUS_HEADERS + FULL_VOLUME_PACKETS,
            HALF_VOLUME_PACKETS[-1],
            "Volume halved, packet should be halved",
        ),
    ],
)
def test_postprocess_packet(
    volume: float,
    packets: list[bytes],
    expected_output: bytes,
    message: str,
) -> None:
    source = BufferedOpusAudioSource(io.BytesIO(b"".join(packets)))
    source.volume = volume

    output = None
    for packet in packets:
        output = source.postprocess_packet(packet)

    if output is None:
        msg = "You must pass more than 0 packets..."
        raise ValueError(msg)

    assert (
        output == expected_output
    ), f"{message}. Output length: {len(output)}, Expected length: {len(expected_output)}"
