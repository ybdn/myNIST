"""Fonctions d'export pour la vue de comparaison."""

from typing import TYPE_CHECKING

from PIL import Image
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QImage, QPainter

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QGraphicsScene
    from .annotatable_view import AnnotatableView


def capture_scene(scene: 'QGraphicsScene') -> Image.Image:
    """Capture le contenu d'une scène graphique en image PIL."""
    rect = scene.itemsBoundingRect()
    if rect.isEmpty():
        return Image.new("RGB", (400, 400), color=(240, 240, 240))

    width = int(rect.width())
    height = int(rect.height())
    if width <= 0 or height <= 0:
        return Image.new("RGB", (400, 400), color=(240, 240, 240))

    qimg = QImage(width, height, QImage.Format_RGB888)
    qimg.fill(Qt.white)

    painter = QPainter(qimg)
    painter.setRenderHint(QPainter.Antialiasing)
    scene.render(painter, QRectF(0, 0, width, height), rect)
    painter.end()

    ptr = qimg.bits()
    ptr.setsize(qimg.byteCount())
    return Image.frombytes("RGB", (width, height), bytes(ptr), "raw", "RGB")


def combine_images(left: Image.Image, right: Image.Image, gap: int = 10) -> Image.Image:
    """Combine deux images côte à côte avec un espace entre elles."""
    max_height = max(left.height, right.height)

    if left.height != max_height:
        ratio = max_height / left.height
        left = left.resize((int(left.width * ratio), max_height), Image.Resampling.LANCZOS)
    if right.height != max_height:
        ratio = max_height / right.height
        right = right.resize((int(right.width * ratio), max_height), Image.Resampling.LANCZOS)

    combined_width = left.width + gap + right.width
    combined = Image.new("RGB", (combined_width, max_height), color=(255, 255, 255))
    combined.paste(left, (0, 0))
    combined.paste(right, (left.width + gap, 0))
    return combined
