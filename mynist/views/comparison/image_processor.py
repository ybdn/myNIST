"""Traitement d'images : enhancements, rotation, flip, conversion."""

from typing import Dict, Optional

from PIL import Image, ImageEnhance, ImageOps
from PyQt5.QtGui import QPixmap, QImage


# Tolérance pour la suppression d'arrière-plan
BACKGROUND_TOLERANCE = 25


class ImageProcessor:
    """Classe utilitaire pour le traitement d'images."""

    @staticmethod
    def default_enhancements() -> Dict[str, float]:
        """Retourne les valeurs par défaut des améliorations d'image."""
        return {
            "brightness": 0.0,
            "contrast": 1.0,
            "gamma": 1.0,
            "invert": False,
        }

    @staticmethod
    def apply_rotation(img: Image.Image, angle: int) -> Image.Image:
        """Applique une rotation à l'image."""
        if angle % 360 == 0:
            return img
        return img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

    @staticmethod
    def apply_enhancements(img: Image.Image, enh: Dict[str, float]) -> Image.Image:
        """Applique luminosité/contraste/gamma/inversion en conservant l'alpha éventuel."""
        had_alpha = img.mode == "RGBA"
        alpha = None
        if had_alpha:
            rgb = img.convert("RGBA").split()[:3]
            alpha = img.getchannel("A")
            result = Image.merge("RGB", rgb)
        else:
            result = img.convert("RGB")

        # Luminosité : map -100/100 vers facteur 0..2
        bright_factor = 1.0 + float(enh.get("brightness", 0.0)) / 100.0
        result = ImageEnhance.Brightness(result).enhance(max(0.0, bright_factor))

        contrast_factor = float(enh.get("contrast", 1.0))
        result = ImageEnhance.Contrast(result).enhance(max(0.1, contrast_factor))

        gamma = float(enh.get("gamma", 1.0))
        if gamma != 1.0:
            inv_gamma = 1.0 / max(gamma, 1e-6)
            lut = [pow(i / 255.0, inv_gamma) * 255 for i in range(256)]
            lut = [min(255, max(0, int(v))) for v in lut]
            result = result.point(lut * 3)

        if enh.get("invert", False):
            result = ImageOps.invert(result)

        if had_alpha and alpha is not None:
            result = result.convert("RGBA")
            result.putalpha(alpha)
        return result

    @staticmethod
    def get_processed_image(
        base_image: Optional[Image.Image],
        rotation: int = 0,
        enhancements: Optional[Dict[str, float]] = None
    ) -> Optional[Image.Image]:
        """Retourne l'image après rotation + améliorations."""
        if base_image is None:
            return None
        if enhancements is None:
            enhancements = ImageProcessor.default_enhancements()
        rotated = ImageProcessor.apply_rotation(base_image, rotation)
        return ImageProcessor.apply_enhancements(rotated, enhancements)

    @staticmethod
    def remove_background(img: Image.Image, tolerance: int = BACKGROUND_TOLERANCE) -> Image.Image:
        """Détecte un fond quasi uni (couleur dominante des coins) et le rend transparent."""
        rgba = img.convert("RGBA")
        w, h = rgba.size
        if w == 0 or h == 0:
            return rgba

        sample = min(40, w, h)
        coords = [
            (0, 0),
            (w - sample, 0),
            (0, h - sample),
            (w - sample, h - sample),
        ]
        pixels = []
        for (x, y) in coords:
            crop = rgba.crop((x, y, x + sample, y + sample))
            pixels.extend(list(crop.getdata()))

        if not pixels:
            return rgba

        avg = (
            sum(p[0] for p in pixels) // len(pixels),
            sum(p[1] for p in pixels) // len(pixels),
            sum(p[2] for p in pixels) // len(pixels),
        )

        new_data = []
        for r, g, b, a in rgba.getdata():
            if abs(r - avg[0]) <= tolerance and abs(g - avg[1]) <= tolerance and abs(b - avg[2]) <= tolerance:
                new_data.append((r, g, b, 0))
            else:
                new_data.append((r, g, b, a))
        rgba.putdata(new_data)
        return rgba

    @staticmethod
    def flip_horizontal(img: Image.Image) -> Image.Image:
        """Flip horizontal de l'image."""
        return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    @staticmethod
    def flip_vertical(img: Image.Image) -> Image.Image:
        """Flip vertical de l'image."""
        return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    @staticmethod
    def pil_to_pixmap(img: Image.Image) -> QPixmap:
        """Convertit un PIL Image en QPixmap en préservant l'alpha si présent."""
        mode = img.mode
        if mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in mode else "RGB")
            mode = img.mode

        if mode == "RGBA":
            data = img.tobytes("raw", "RGBA")
            bytes_per_line = img.width * 4
            qimg = QImage(data, img.width, img.height, bytes_per_line, QImage.Format_RGBA8888).copy()
        else:
            img = img.convert("RGB")
            data = img.tobytes("raw", "RGB")
            bytes_per_line = img.width * 3
            qimg = QImage(data, img.width, img.height, bytes_per_line, QImage.Format_RGB888).copy()

        return QPixmap.fromImage(qimg)

    @staticmethod
    def resample_to_dpi(
        img: Image.Image,
        current_dpi: float,
        target_dpi: int
    ) -> Image.Image:
        """Rééchantillonne l'image pour atteindre le DPI cible."""
        if current_dpi <= 0:
            return img
        ratio = target_dpi / current_dpi
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        if new_width < 1 or new_height < 1:
            return img
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
