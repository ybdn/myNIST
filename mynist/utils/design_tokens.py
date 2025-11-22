"""Design System Tokens for NIST Studio.

Simplified version using OS native colors.
"""

from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPalette
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication


class Typography:
    """Font sizes and weights."""

    SIZE_XS = 11
    SIZE_SM = 12
    SIZE_MD = 14
    SIZE_LG = 16
    SIZE_XL = 20
    SIZE_2XL = 24
    SIZE_3XL = 28

    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700


class Spacing:
    """Spacing values in pixels."""

    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    XXXL = 32
    XXXXL = 48


class Radius:
    """Border radius values in pixels."""

    SM = 4
    MD = 6
    LG = 8
    XL = 12


def get_icon_color() -> str:
    """Get appropriate icon color from OS palette."""
    app = QApplication.instance()
    if app is None:
        return "#000000"

    palette = app.palette()
    color = palette.color(QPalette.WindowText)
    return color.name()


def load_svg_icon(svg_path: Path, color: str = None, size: int = 24) -> QIcon:
    """Load an SVG icon and apply a color.

    Args:
        svg_path: Path to SVG file
        color: Hex color string. If None, uses OS text color.
        size: Icon size in pixels

    Returns:
        QIcon with the colored icon
    """
    if not svg_path.exists():
        return QIcon()

    if color is None:
        color = get_icon_color()

    # Read and modify SVG content
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
    except Exception:
        return QIcon()

    # Replace color references
    svg_content = svg_content.replace('currentColor', color)
    svg_content = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')

    # Create renderer from modified SVG
    renderer = QSvgRenderer(svg_content.encode('utf-8'))
    if not renderer.isValid():
        return QIcon()

    # Render to pixmap
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)
