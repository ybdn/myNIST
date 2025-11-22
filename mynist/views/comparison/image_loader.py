"""Chargement d'images depuis différentes sources (NIST, PDF, images standard)."""

import io
from typing import Optional, Tuple, List

from PIL import Image

from mynist.models.nist_file import NISTFile
from mynist.utils.image_tools import locate_image_payload, detect_image_format, exif_transpose
from mynist.utils.image_codecs import decode_wsq, decode_jpeg2000
from mynist.utils.biometric_labels import get_short_label_fr


class ImageLoader:
    """Classe utilitaire pour charger des images depuis différents formats de fichiers."""

    # Types de records prioritaires pour l'extraction d'images
    PRIORITY_RECORD_TYPES = (14, 4, 10, 7, 15, 13, 17)

    @staticmethod
    def load_from_path(path: str) -> Optional[Image.Image]:
        """Charge une image depuis un chemin (NIST, PDF ou image standard)."""
        lower = path.lower()
        try:
            if lower.endswith((".nist", ".nst", ".eft", ".an2", ".int")):
                return ImageLoader.load_nist_first_image(path)
            if lower.endswith(".pdf"):
                return ImageLoader.load_pdf(path)
            return ImageLoader.load_standard_image(path)
        except Exception:
            return None

    @staticmethod
    def load_standard_image(path: str) -> Optional[Image.Image]:
        """Charge une image standard (PNG, JPG, BMP, TIFF, etc.)."""
        try:
            img = Image.open(path)
            return exif_transpose(img).convert("RGB")
        except Exception:
            return None

    @staticmethod
    def load_pdf(path: str) -> Optional[Image.Image]:
        """Charge la première page d'un PDF comme image."""
        try:
            img = Image.open(path)
            return img.convert("RGB")
        except Exception:
            return None

    @staticmethod
    def load_nist_first_image(path: str) -> Optional[Image.Image]:
        """Charge la première image trouvée dans un fichier NIST."""
        nist = NISTFile(path)
        if not nist.parse():
            return None
        for rtype in ImageLoader.PRIORITY_RECORD_TYPES:
            recs = nist.get_records_by_type(rtype)
            for idc, rec in recs:
                pil_img, _ = ImageLoader.record_to_image(rec)
                if pil_img:
                    return pil_img
        return None

    @staticmethod
    def load_nist_with_navigation(path: str) -> Tuple[Optional['NISTFile'], List[Tuple[int, int, object, str]]]:
        """
        Charge un fichier NIST et retourne la liste des images disponibles pour navigation.

        Returns:
            Tuple (nist_file, images_list) où images_list contient des tuples
            (record_type, idc, record, label).
        """
        nist = NISTFile(path)
        if not nist.parse():
            return None, []

        images = []
        for rtype in ImageLoader.PRIORITY_RECORD_TYPES:
            recs = nist.get_records_by_type(rtype)
            for idc, rec in recs:
                pil_img, _ = ImageLoader.record_to_image(rec)
                if pil_img:
                    label = get_short_label_fr(rtype, rec)
                    images.append((rtype, idc, rec, label))

        return nist, images

    @staticmethod
    def record_to_image(record) -> Tuple[Optional[Image.Image], str]:
        """
        Extrait une image PIL depuis un record NIST.

        Returns:
            Tuple (image, format) où format indique le type détecté (WSQ, JPEG2000, etc.)
        """
        data = None
        for attr in ("_999", "_009", "DATA", "data", "image", "Image", "BDB", "value"):
            try:
                val = getattr(record, attr, None)
                if val and isinstance(val, (bytes, bytearray)):
                    data = bytes(val)
                    break
            except Exception:
                continue

        if not data:
            return None, ""

        payload, fmt = locate_image_payload(data)

        if fmt == "WSQ":
            img, _ = decode_wsq(payload)
            if img:
                return img, fmt
            return None, fmt

        if fmt == "JPEG2000":
            img, _ = decode_jpeg2000(payload)
            if img:
                return exif_transpose(img), fmt
            return None, fmt

        try:
            img = Image.open(io.BytesIO(payload))
            img = exif_transpose(img).convert("RGB")
            return img, detect_image_format(payload)
        except Exception:
            return None, fmt

    @staticmethod
    def get_image_from_nist_index(
        nist_images: List[Tuple[int, int, object, str]],
        index: int
    ) -> Optional[Image.Image]:
        """Extrait l'image à l'index donné depuis la liste des images NIST."""
        if not nist_images or index < 0 or index >= len(nist_images):
            return None
        _, _, record, _ = nist_images[index]
        img, _ = ImageLoader.record_to_image(record)
        return img
