"""Design System Tokens for NIST Studio.

Tech Modern Clean style - Professional biometric analysis application.
"""

# =============================================================================
# COLOR PALETTE
# =============================================================================

class Colors:
    """Official NIST Studio color palette."""

    # Primary colors
    PRIMARY = "#0D1B2A"          # Bleu nuit - Brand identity
    ACCENT = "#3AAFA9"           # Cyan tech - Interactive elements
    ACCENT_SECONDARY = "#4FC3F7" # Bleu clair - Highlights

    # Backgrounds
    BG_LIGHT = "#F5F7FA"         # Gris froid - Light mode background
    BG_DARK = "#1A1F25"          # Anthracite - Dark mode background

    # Surfaces (panels, cards)
    SURFACE_LIGHT = "#FFFFFF"
    SURFACE_DARK = "#2A3038"

    # Text
    TEXT_PRIMARY_LIGHT = "#0D1B2A"
    TEXT_PRIMARY_DARK = "#FFFFFF"
    TEXT_SECONDARY = "#5C6975"

    # Borders
    BORDER_SUBTLE = "#D0D7DF"
    BORDER_DARK = "#3A424D"

    # States
    HOVER_ACCENT = "#45C4BE"     # Accent +10%
    DISABLED = "#8A9199"
    ERROR = "#E53935"
    SUCCESS = "#43A047"
    WARNING = "#FB8C00"


class ColorsLight:
    """Light theme colors."""
    WINDOW = Colors.BG_LIGHT
    BASE = Colors.SURFACE_LIGHT
    TEXT = Colors.TEXT_PRIMARY_LIGHT
    TEXT_SECONDARY = Colors.TEXT_SECONDARY
    BORDER = Colors.BORDER_SUBTLE
    ACCENT = Colors.ACCENT
    SURFACE = Colors.SURFACE_LIGHT


class ColorsDark:
    """Dark theme colors."""
    WINDOW = Colors.BG_DARK
    BASE = Colors.SURFACE_DARK
    TEXT = Colors.TEXT_PRIMARY_DARK
    TEXT_SECONDARY = Colors.TEXT_SECONDARY
    BORDER = Colors.BORDER_DARK
    ACCENT = Colors.ACCENT
    SURFACE = Colors.SURFACE_DARK


# =============================================================================
# TYPOGRAPHY
# =============================================================================

class Typography:
    """Font sizes and weights."""

    # Font family (fallbacks for system availability)
    FONT_FAMILY = "Inter, Source Sans Pro, Segoe UI, sans-serif"

    # Sizes in points
    SIZE_SMALL = 12
    SIZE_NORMAL = 14
    SIZE_MEDIUM = 16
    SIZE_LARGE = 20
    SIZE_XLARGE = 24
    SIZE_TITLE = 28

    # Weights
    WEIGHT_LIGHT = 300
    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700


# =============================================================================
# SPACING
# =============================================================================

class Spacing:
    """Spacing values in pixels."""

    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    XXXL = 32

    # Component-specific
    CARD_PADDING = 20
    PANEL_PADDING = 16
    HEADER_PADDING_H = 16
    HEADER_PADDING_V = 8


# =============================================================================
# BORDER RADIUS
# =============================================================================

class Radius:
    """Border radius values in pixels."""

    NONE = 0
    SM = 4
    MD = 6
    LG = 10
    XL = 12
    ROUND = 9999


# =============================================================================
# SHADOWS (minimal for flat UI)
# =============================================================================

class Shadows:
    """Box shadows - subtle for flat design."""

    NONE = "none"
    SUBTLE = "0 1px 3px rgba(0, 0, 0, 0.08)"
    CARD = "0 2px 8px rgba(0, 0, 0, 0.06)"
    ELEVATED = "0 4px 12px rgba(0, 0, 0, 0.1)"


# =============================================================================
# ICON CONFIGURATION
# =============================================================================

class Icons:
    """Icon configuration - Tabler Icons style."""

    STROKE_WIDTH = 1.5  # px
    SIZE_SM = 16
    SIZE_MD = 20
    SIZE_LG = 24
    SIZE_XL = 32
    SIZE_CARD = 48


# =============================================================================
# COMPONENT DIMENSIONS
# =============================================================================

class Dimensions:
    """Standard component dimensions."""

    # Cards
    CARD_HEIGHT = 140
    CARD_MIN_WIDTH = 280
    CARD_MAX_WIDTH = 400

    # Buttons
    BUTTON_HEIGHT = 36
    BUTTON_HEIGHT_SM = 28
    BUTTON_HEIGHT_LG = 44

    # Panels
    PANEL_ADJUSTMENTS_WIDTH = 850

    # Header
    HEADER_HEIGHT = 48


# =============================================================================
# QSS HELPER FUNCTIONS
# =============================================================================

def get_button_style(
    bg_color: str = Colors.ACCENT,
    text_color: str = "#FFFFFF",
    hover_color: str = Colors.HOVER_ACCENT,
    radius: int = Radius.MD
) -> str:
    """Generate QPushButton stylesheet."""
    return f"""
        QPushButton {{
            background-color: {bg_color};
            color: {text_color};
            border: none;
            border-radius: {radius}px;
            padding: 8px 16px;
            font-size: {Typography.SIZE_NORMAL}px;
            font-weight: {Typography.WEIGHT_MEDIUM};
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {bg_color};
        }}
        QPushButton:disabled {{
            background-color: {Colors.DISABLED};
            color: {Colors.TEXT_SECONDARY};
        }}
    """


def get_card_style(
    bg_color: str,
    border_color: str,
    text_color: str,
    hover_border: str = Colors.ACCENT,
    radius: int = Radius.LG
) -> str:
    """Generate card button stylesheet."""
    return f"""
        QPushButton#modeCard {{
            text-align: center;
            padding: {Spacing.CARD_PADDING}px;
            border: 1px solid {border_color};
            border-radius: {radius}px;
            background: {bg_color};
            color: {text_color};
            font-size: {Typography.SIZE_NORMAL}px;
        }}
        QPushButton#modeCard:hover {{
            border-color: {hover_border};
            border-width: 2px;
        }}
        QPushButton#modeCard:disabled {{
            background: {Colors.DISABLED};
            color: {Colors.TEXT_SECONDARY};
        }}
    """


def get_header_style(
    bg_color: str,
    text_color: str,
    border_color: str
) -> str:
    """Generate header frame stylesheet."""
    return f"""
        #viewerHeader, #moduleHeader {{
            background: {bg_color};
            border-bottom: 1px solid {border_color};
        }}
        #viewerHeader QLabel, #moduleHeader QLabel {{
            color: {text_color};
        }}
        #titleLabel {{
            font-size: {Typography.SIZE_MEDIUM}px;
            font-weight: {Typography.WEIGHT_SEMIBOLD};
            color: {Colors.PRIMARY};
        }}
        #subtitleLabel {{
            font-size: {Typography.SIZE_SMALL}px;
            color: {Colors.TEXT_SECONDARY};
        }}
    """
