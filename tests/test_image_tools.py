"""Tests for image format detection and EXIF helper."""

from PIL import Image

from mynist.utils.image_tools import (
    detect_image_format,
    exif_transpose,
    locate_image_payload,
    load_jpeg2000_image,
)


def test_detect_image_format_basic_signatures():
    assert detect_image_format(b"\xff\xd8\xff") == "JPEG"
    assert detect_image_format(b"\x89PNG\r\n\x1a\nrest") == "PNG"
    assert detect_image_format(b"BMxxxx") == "BMP"
    assert detect_image_format(b"\xff\xa0\xff\xa8rest") == "WSQ"
    assert detect_image_format(b"\x00\x00\x00\x0cjP  \r\n\x87\nmore") == "JPEG2000"
    assert detect_image_format(b"") == "Unknown"


def test_exif_transpose_no_exif_roundtrip():
    img = Image.new("RGB", (10, 20), color="red")
    result = exif_transpose(img)
    assert result.size == (10, 20)


def test_locate_image_payload_with_leading_header():
    payload = b"\x00\x11\x22" + b"\xff\xa0\xff\xa8rest"
    data, fmt = locate_image_payload(payload)
    assert fmt == "WSQ"
    assert data.startswith(b"\xff\xa0\xff\xa8")


def test_load_jpeg2000_image_missing_plugin(tmp_path):
    payload = (tmp_path / "fake.jp2")
    payload.write_bytes(b"\x00\x00\x00\x0cjP  \r\n\x87\n" + b"\x00" * 10)
    data = payload.read_bytes()
    img, err = load_jpeg2000_image(data)
    assert img is None
    assert err  # should mention plugin missing or parse error


def test_detect_wsq_variant_signature():
    data = b"\xff\xa0\xff\xa2" + b"\x00" * 10
    assert detect_image_format(data) == "WSQ"
