"""Design System Tokens for NIST Studio.

Tech Modern Clean style - Professional biometric analysis application.
"""

from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer


# =============================================================================
# COLOR PALETTE
# =============================================================================

class Colors:
    """Official NIST Studio color palette."""

    # Primary colors
    PRIMARY = "#0D1B2A"          # Bleu nuit - Brand identity
    ACCENT = "#3AAFA9"           # Cyan tech - Interactive elements
    ACCENT_HOVER = "#2D9A94"     # Cyan hover (plus fonce)
    ACCENT_LIGHT = "#5BC0BC"     # Cyan clair

    # Light theme
    LIGHT_BG = "#F5F7FA"         # Background principal
    LIGHT_SURFACE = "#FFFFFF"    # Surfaces (cards, panels)
    LIGHT_TEXT = "#1A1A2E"       # Texte principal (contraste fort)
    LIGHT_TEXT_SECONDARY = "#64748B"  # Texte secondaire
    LIGHT_BORDER = "#E2E8F0"     # Bordures subtiles
    LIGHT_ICON = "#334155"       # Couleur icones

    # Dark theme
    DARK_BG = "#0F172A"          # Background principal
    DARK_SURFACE = "#1E293B"     # Surfaces (cards, panels)
    DARK_TEXT = "#F1F5F9"        # Texte principal
    DARK_TEXT_SECONDARY = "#94A3B8"  # Texte secondaire
    DARK_BORDER = "#334155"      # Bordures
    DARK_ICON = "#E2E8F0"        # Couleur icones (clair)

    # States
    DISABLED = "#94A3B8"
    ERROR = "#EF4444"
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"

    # Special
    ICON_ON_ACCENT = "#FFFFFF"   # Icones sur fond accent


class Typography:
    """Font sizes and weights."""

    # Sizes in points
    SIZE_XS = 11
    SIZE_SM = 12
    SIZE_MD = 14
    SIZE_LG = 16
    SIZE_XL = 20
    SIZE_2XL = 24
    SIZE_3XL = 28

    # Weights
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


# =============================================================================
# ICON UTILITIES
# =============================================================================

def load_colored_icon(svg_path: Path, color: str, size: int = 24) -> QIcon:
    """Load an SVG icon and colorize it.

    Args:
        svg_path: Path to the SVG file
        color: Hex color to apply (e.g., "#FFFFFF")
        size: Icon size in pixels

    Returns:
        QIcon with the colorized icon
    """
    if not svg_path.exists():
        return QIcon()

    # Read SVG content and replace currentColor
    with open(svg_path, 'r') as f:
        svg_content = f.read()

    # Replace currentColor and any stroke/fill with our color
    svg_content = svg_content.replace('currentColor', color)
    svg_content = svg_content.replace('stroke="#000000"', f'stroke="{color}"')
    svg_content = svg_content.replace('stroke="#000"', f'stroke="{color}"')
    svg_content = svg_content.replace("stroke='#000000'", f"stroke='{color}'")
    svg_content = svg_content.replace("stroke='#000'", f"stroke='{color}'")

    # Render with QSvgRenderer
    renderer = QSvgRenderer(svg_content.encode())
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def get_icon_color(is_dark: bool, on_accent: bool = False) -> str:
    """Get the appropriate icon color based on theme.

    Args:
        is_dark: True if dark theme
        on_accent: True if icon is on accent-colored background

    Returns:
        Hex color string
    """
    if on_accent:
        return Colors.ICON_ON_ACCENT
    return Colors.DARK_ICON if is_dark else Colors.LIGHT_ICON


# =============================================================================
# THEME UTILITIES
# =============================================================================

class Theme:
    """Theme helper class."""

    def __init__(self, is_dark: bool):
        self.is_dark = is_dark

        if is_dark:
            self.bg = Colors.DARK_BG
            self.surface = Colors.DARK_SURFACE
            self.text = Colors.DARK_TEXT
            self.text_secondary = Colors.DARK_TEXT_SECONDARY
            self.border = Colors.DARK_BORDER
            self.icon = Colors.DARK_ICON
        else:
            self.bg = Colors.LIGHT_BG
            self.surface = Colors.LIGHT_SURFACE
            self.text = Colors.LIGHT_TEXT
            self.text_secondary = Colors.LIGHT_TEXT_SECONDARY
            self.border = Colors.LIGHT_BORDER
            self.icon = Colors.LIGHT_ICON

        # Common colors
        self.accent = Colors.ACCENT
        self.accent_hover = Colors.ACCENT_HOVER
        self.primary = Colors.PRIMARY

    def get_hub_button_style(self) -> str:
        """Get stylesheet for hub/accent buttons."""
        return f"""
            background: {self.accent};
            color: white;
            border: none;
            border-radius: {Radius.MD}px;
            padding: {Spacing.SM}px {Spacing.LG}px;
            font-weight: {Typography.WEIGHT_MEDIUM};
            font-size: {Typography.SIZE_MD}px;
        """

    def get_hub_button_hover_style(self) -> str:
        """Get hover style for hub buttons."""
        return f"background: {self.accent_hover};"

    def get_card_style(self) -> str:
        """Get stylesheet for mode cards."""
        hover_bg = Colors.DARK_SURFACE if self.is_dark else "#EEF2F7"
        return f"""
            QPushButton#modeCard {{
                text-align: center;
                padding: {Spacing.XL}px;
                border: 1px solid {self.border};
                border-radius: {Radius.XL}px;
                background: {self.surface};
                color: {self.text};
                font-size: {Typography.SIZE_MD}px;
            }}
            QPushButton#modeCard:hover {{
                border: 2px solid {self.accent};
                background: {hover_bg};
            }}
            QPushButton#modeCard:disabled {{
                background: {self.surface};
                color: {self.text_secondary};
                border-color: {self.border};
            }}
        """


def detect_dark_mode(widget) -> bool:
    """Detect if the system/widget is in dark mode.

    Args:
        widget: QWidget to check palette from

    Returns:
        True if dark mode
    """
    from PyQt5.QtGui import QPalette
    palette = widget.palette()
    window_color = palette.color(QPalette.Window)
    return window_color.lightness() < 128
