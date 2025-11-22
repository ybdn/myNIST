"""Home view (hub) for mode selection."""

from pathlib import Path
from typing import Optional, Dict

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPalette
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QGridLayout,
    QApplication,
)

from mynist.utils.constants import APP_NAME, APP_VERSION
from mynist.utils.design_tokens import Typography, Spacing, Radius, load_svg_icon


class HomeView(QWidget):
    """Hub screen with mode cards."""

    open_file_requested = pyqtSignal()
    open_recent_requested = pyqtSignal(str)
    mode_requested = pyqtSignal(str)
    clear_recents_requested = pyqtSignal()
    resume_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: Optional[str] = None
        self.current_mode: str = "viewer"
        self._icon_cache: Dict[str, QIcon] = {}
        self._build_ui()

    def _get_icon_path(self, name: str) -> Path:
        """Return path to hub icon."""
        return Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"

    def _is_dark_theme(self) -> bool:
        """Detect if the OS is using dark theme."""
        app = QApplication.instance()
        if app is None:
            return False
        palette = app.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightnessF() < 0.5

    def _get_logo_path(self) -> Path:
        """Return path to appropriate logo based on theme."""
        icons_dir = Path(__file__).parent.parent / "resources" / "icons"
        if self._is_dark_theme():
            return icons_dir / "logo-nist-studio-white.png"
        else:
            return icons_dir / "logo-nist-studio-black.png"

    def _load_icon(self, name: str, size: int = 48) -> QIcon:
        """Load SVG icon with OS-appropriate color."""
        cache_key = f"{name}_{size}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        path = self._get_icon_path(name)
        icon = load_svg_icon(path, size=size)
        self._icon_cache[cache_key] = icon
        return icon

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.XXXXL, Spacing.XXXL, Spacing.XXXXL, Spacing.XXXL)
        layout.setSpacing(Spacing.XXL)

        # Vertical centering
        layout.addStretch(1)

        # Header
        header = self._build_header()
        layout.addWidget(header)

        # Current file status
        self.current_file_label = QLabel("Aucun fichier ouvert")
        self.current_file_label.setAlignment(Qt.AlignCenter)
        self.current_file_label.setStyleSheet(f"""
            font-size: {Typography.SIZE_SM}px;
            padding: {Spacing.SM}px {Spacing.LG}px;
            border-radius: {Radius.MD}px;
        """)
        layout.addWidget(self.current_file_label)

        layout.addSpacing(Spacing.MD)

        # Mode cards
        cards = self._build_cards()
        layout.addWidget(cards)

        layout.addStretch(2)
        self.setLayout(layout)

    def _build_header(self) -> QWidget:
        """Build header with app logo."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)
        layout.setAlignment(Qt.AlignCenter)

        # Logo
        logo_label = QLabel()
        logo_path = self._get_logo_path()
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Scale to reasonable size (max 400px width)
            scaled = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled)
        else:
            # Fallback to text if logo not found
            logo_label.setText(APP_NAME)
            logo_label.setStyleSheet(f"""
                font-size: {Typography.SIZE_3XL}px;
                font-weight: {Typography.WEIGHT_BOLD};
            """)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Version subtitle
        subtitle = QLabel(f"v{APP_VERSION} - Suite d'outils biometriques")
        subtitle.setStyleSheet(f"font-size: {Typography.SIZE_MD}px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        container.setLayout(layout)
        return container

    def _build_cards(self) -> QWidget:
        """Build 4 mode cards in a grid layout."""
        container = QWidget()
        container.setMaximumWidth(800)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(Spacing.LG)

        cards_data = [
            ("NIST-Viewer", "Visualiser et editer\ndes fichiers NIST", "viewer", "viewer", True),
            ("NIST-Compare", "Comparer cote a cote\ndeux images biometriques", "comparison", "compare", True),
            ("NIST-2-PDF", "Exporter un releve\ndecadactylaire PDF", "pdf", "pdf", True),
            ("Image-2-NIST", "Convertir une image\nen fichier NIST", "image2nist", "image2nist", False),
        ]

        for i, (title, subtitle, mode, icon_name, enabled) in enumerate(cards_data):
            button = self._make_card_button(title, subtitle, mode, icon_name, enabled)
            grid.addWidget(button, i // 2, i % 2)

        container.setLayout(grid)

        # Center wrapper
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(container, 0, Qt.AlignCenter)
        wrapper.setLayout(wrapper_layout)

        return wrapper

    def _make_card_button(self, title: str, subtitle: str, mode: str, icon_name: str, enabled: bool) -> QPushButton:
        """Create a card button with styled title and subtitle."""
        button = QPushButton()
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedHeight(160)
        button.setMinimumWidth(300)
        button.setEnabled(enabled)
        button.setCursor(Qt.PointingHandCursor if enabled else Qt.ForbiddenCursor)

        # Style with OS colors + layout tokens
        button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {Radius.XL}px;
                padding: {Spacing.XL}px;
                text-align: left;
            }}
        """)

        # Create layout for card content
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Icon row
        icon_label = QLabel()
        icon = self._load_icon(icon_name, 40)
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(40, 40))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Title - bold and bigger
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Typography.SIZE_LG}px;
            font-weight: {Typography.WEIGHT_BOLD};
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Subtitle - normal size
        subtitle_text = subtitle.replace("\n", " ")
        if not enabled:
            subtitle_text += " (Bientot disponible)"
        subtitle_label = QLabel(subtitle_text)
        subtitle_label.setStyleSheet(f"font-size: {Typography.SIZE_SM}px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

        button.setLayout(layout)

        if enabled:
            button.clicked.connect(lambda checked, m=mode: self.mode_requested.emit(m))

        return button

    def set_current_file(self, path: Optional[str], mode: str = "viewer"):
        """Update current file display."""
        self.current_file = path
        self.current_mode = mode
        if path:
            name = Path(path).name
            mode_labels = {"viewer": "NIST-Viewer", "comparison": "NIST-Compare", "pdf": "NIST-2-PDF"}
            mode_label = mode_labels.get(mode, mode)
            self.current_file_label.setText(f"Fichier en cours : {name} - Mode : {mode_label}")
        else:
            self.current_file_label.setText("Aucun fichier ouvert")

    def set_recent_entries(self, entries):
        """Compatibility stub."""
        pass
