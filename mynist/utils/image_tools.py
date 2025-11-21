"""Image helpers for format detection and EXIF handling."""

import io
from typing import Tuple, Optional, List, Iterable

from PIL import Image, ImageOps


JPEG_SIGNATURE = b"\xff\xd8"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
BMP_SIGNATURES = (b"BM", b"BA")
WSQ_SIGNATURES = (b"\xff\xa0\xff\xa8", b"\xff\xa0\xff\xa2", b"\xff\xa0")
JPEG2000_SIGNATURES = (
    b"\x00\x00\x00\x0cjP  \r\n\x87\n",
    b"\x00\x00\x00\x0c\x6a\x50\x20\x20\x0d\x0a\x87\x0a",
    b"\x00\x00\x00\x14ftypjp2",
)


def detect_image_format(data: bytes) -> str:
    """Return a lightweight guess of the image format."""
    if not data:
        return "Unknown"
    if data.startswith(JPEG_SIGNATURE):
        return "JPEG"
    if data.startswith(PNG_SIGNATURE):
        return "PNG"
    if data[:2] in BMP_SIGNATURES:
        return "BMP"
    if any(data.startswith(sig) for sig in WSQ_SIGNATURES):
        return "WSQ"
    if len(data) >= 8 and any(data.startswith(sig) for sig in JPEG2000_SIGNATURES):
        return "JPEG2000"
    return "Unknown"


def locate_image_payload(data: bytes) -> Tuple[bytes, str]:
    """
    Locate an image payload inside a larger binary blob.

    Returns:
        (payload_bytes, format_name)
    """
    format_name = detect_image_format(data)
    if format_name != "Unknown":
        return data, format_name

    signatures: List[Tuple[Iterable[bytes], str]] = [
        ([JPEG_SIGNATURE], "JPEG"),
        ([PNG_SIGNATURE], "PNG"),
        (BMP_SIGNATURES, "BMP"),
        (WSQ_SIGNATURES, "WSQ"),
        (JPEG2000_SIGNATURES, "JPEG2000"),
    ]

    for sig_group, label in signatures:
        for sig in sig_group:
            idx = data.find(sig)
            if idx >= 0:
                return data[idx:], label

    return data, "Unknown"


def exif_transpose(pil_image: Image.Image) -> Image.Image:
    """Apply EXIF orientation if present, returning a new image."""
    try:
        return ImageOps.exif_transpose(pil_image)
    except Exception:
        return pil_image


def load_jpeg2000_image(data: bytes) -> Tuple[Optional[Image.Image], str]:
    """
    Try to load JPEG2000; return (image, error_message).
    error_message is empty string on success.
    """
    try:
        img = Image.open(io.BytesIO(data))
        return img, ""
    except ModuleNotFoundError:
        return None, "Plugin manquant pour JPEG2000. Installez 'imagecodecs' ou 'glymur'."
    except Exception as exc:  # pragma: no cover - bubble message
        return None, str(exc)
