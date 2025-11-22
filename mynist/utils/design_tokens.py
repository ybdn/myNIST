"""Design System Tokens for NIST Studio.

Tech Modern Clean style - Professional biometric analysis application.
"""

from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPalette
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication


# =============================================================================
# COLOR PALETTE
# =============================================================================

class Colors:
    """Official NIST Studio color palette."""

    # Primary colors
    PRIMARY = "#0D1B2A"
    ACCENT = "#3AAFA9"
    ACCENT_HOVER = "#2D9A94"

    # Light theme
    LIGHT_BG = "#F5F7FA"
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_TEXT = "#1A1A2E"
    LIGHT_TEXT_SECONDARY = "#64748B"
    LIGHT_BORDER = "#D1D5DB"
    LIGHT_ICON = "#374151"

    # Dark theme
    DARK_BG = "#111827"
    DARK_SURFACE = "#1F2937"
    DARK_TEXT = "#F9FAFB"
    DARK_TEXT_SECONDARY = "#9CA3AF"
    DARK_BORDER = "#4B5563"
    DARK_ICON = "#E5E7EB"

    # Special
    WHITE = "#FFFFFF"
    DISABLED = "#9CA3AF"
    ICON_ON_ACCENT = "#FFFFFF"  # White icons on accent-colored buttons


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


# =============================================================================
# THEME DETECTION
# =============================================================================

def is_dark_theme() -> bool:
    """Detect if the application is in dark mode.

    Uses multiple methods for reliable detection.
    """
    app = QApplication.instance()
    if app is None:
        return False

    palette = app.palette()

    # Check window background color
    window_color = palette.color(QPalette.Window)

    # Also check text color as a secondary signal
    text_color = palette.color(QPalette.WindowText)

    # If background is dark (low brightness) -> dark mode
    # Use HSL lightness for more accurate detection
    bg_lightness = window_color.lightnessF()

    return bg_lightness < 0.5


# =============================================================================
# THEME CLASS
# =============================================================================

class Theme:
    """Theme configuration based on light/dark mode."""

    def __init__(self, dark: bool = None):
        """Initialize theme.

        Args:
            dark: Force dark mode (True) or light mode (False).
                  If None, auto-detect.
        """
        if dark is None:
            self.is_dark = is_dark_theme()
        else:
            self.is_dark = dark

        if self.is_dark:
            self.bg = Colors.DARK_BG
            self.surface = Colors.DARK_SURFACE
            self.text = Colors.DARK_TEXT
            self.text_secondary = Colors.DARK_TEXT_SECONDARY
            self.border = Colors.DARK_BORDER
            self.icon_color = Colors.DARK_ICON
        else:
            self.bg = Colors.LIGHT_BG
            self.surface = Colors.LIGHT_SURFACE
            self.text = Colors.LIGHT_TEXT
            self.text_secondary = Colors.LIGHT_TEXT_SECONDARY
            self.border = Colors.LIGHT_BORDER
            self.icon_color = Colors.LIGHT_ICON

        # Aliases for compatibility
        self.icon = self.icon_color

        self.accent = Colors.ACCENT
        self.accent_hover = Colors.ACCENT_HOVER


# =============================================================================
# ICON LOADING
# =============================================================================

def load_svg_icon(svg_path: Path, color: str, size: int = 24) -> QIcon:
    """Load an SVG icon and apply a color.

    Args:
        svg_path: Path to SVG file
        color: Hex color string (e.g., "#FFFFFF")
        size: Icon size in pixels

    Returns:
        QIcon with the colored icon
    """
    if not svg_path.exists():
        return QIcon()

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


# =============================================================================
# STYLESHEET GENERATORS
# =============================================================================

def get_root_stylesheet(theme: Theme) -> str:
    """Get stylesheet for root widgets."""
    return f"""
        background-color: {theme.bg};
        color: {theme.text};
    """


def get_hub_button_stylesheet(theme: Theme) -> str:
    """Get stylesheet for accent-colored Hub buttons."""
    return f"""
        QPushButton#hubButton {{
            background-color: {theme.accent};
            color: {Colors.WHITE};
            border: none;
            border-radius: {Radius.MD}px;
            padding: {Spacing.SM}px {Spacing.LG}px;
            font-size: {Typography.SIZE_MD}px;
            font-weight: {Typography.WEIGHT_MEDIUM};
        }}
        QPushButton#hubButton:hover {{
            background-color: {theme.accent_hover};
        }}
        QPushButton#hubButton:pressed {{
            background-color: {theme.accent};
        }}
    """


def get_card_stylesheet(theme: Theme) -> str:
    """Get stylesheet for mode cards on the Hub."""
    hover_bg = "#374151" if theme.is_dark else "#E5E7EB"
    return f"""
        QPushButton#modeCard {{
            background-color: {theme.surface};
            color: {theme.text};
            border: 1px solid {theme.border};
            border-radius: {Radius.XL}px;
            padding: {Spacing.XL}px;
            font-size: {Typography.SIZE_MD}px;
            text-align: center;
        }}
        QPushButton#modeCard:hover {{
            border: 2px solid {theme.accent};
            background-color: {hover_bg};
        }}
        QPushButton#modeCard:disabled {{
            color: {theme.text_secondary};
            background-color: {theme.surface};
        }}
    """


def get_groupbox_stylesheet(theme: Theme) -> str:
    """Get stylesheet for QGroupBox."""
    return f"""
        QGroupBox {{
            background-color: {theme.surface};
            color: {theme.text};
            border: 1px solid {theme.border};
            border-radius: {Radius.LG}px;
            margin-top: 16px;
            padding: {Spacing.LG}px;
            padding-top: {Spacing.XXL}px;
            font-weight: {Typography.WEIGHT_SEMIBOLD};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: {Spacing.MD}px;
            padding: 0 {Spacing.SM}px;
            background-color: {theme.bg};
            color: {theme.text};
        }}
    """


def get_input_stylesheet(theme: Theme) -> str:
    """Get stylesheet for QLineEdit."""
    return f"""
        QLineEdit {{
            background-color: {theme.surface};
            color: {theme.text};
            border: 1px solid {theme.border};
            border-radius: {Radius.MD}px;
            padding: {Spacing.SM}px {Spacing.MD}px;
            font-size: {Typography.SIZE_MD}px;
        }}
        QLineEdit:focus {{
            border-color: {theme.accent};
        }}
        QLineEdit::placeholder {{
            color: {theme.text_secondary};
        }}
    """


def get_button_stylesheet(theme: Theme) -> str:
    """Get stylesheet for regular QPushButton."""
    return f"""
        QPushButton {{
            background-color: {theme.surface};
            color: {theme.text};
            border: 1px solid {theme.border};
            border-radius: {Radius.MD}px;
            padding: {Spacing.SM}px {Spacing.MD}px;
            font-size: {Typography.SIZE_MD}px;
        }}
        QPushButton:hover {{
            background-color: {theme.border};
        }}
        QPushButton:pressed {{
            background-color: {theme.surface};
        }}
    """


# Backward compatibility aliases
def detect_dark_mode(widget) -> bool:
    """Deprecated: Use is_dark_theme() instead."""
    return is_dark_theme()


def load_colored_icon(path: Path, color: str, size: int = 24) -> QIcon:
    """Deprecated: Use load_svg_icon() instead."""
    return load_svg_icon(path, color, size)
