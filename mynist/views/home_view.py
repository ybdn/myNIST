"""Home view (hub) for mode selection."""

from pathlib import Path
from typing import Optional, Dict

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QGridLayout,
)

from mynist.utils.constants import APP_NAME, APP_VERSION
from mynist.utils.design_tokens import (
    Colors, Typography, Spacing, Radius,
    Theme, is_dark_theme, load_svg_icon,
    get_card_stylesheet
)


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

        # Setup theme
        self._theme = Theme()
        self.setObjectName("HomeRoot")
        self._apply_styles()
        self._build_ui()

    def _get_icon_path(self, name: str) -> Path:
        """Return path to hub icon."""
        return Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"

    def _load_icon(self, name: str, size: int = 48) -> QIcon:
        """Load SVG icon with theme-appropriate color."""
        cache_key = f"{name}_{size}_{self._theme.is_dark}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        path = self._get_icon_path(name)
        icon = load_svg_icon(path, self._theme.icon_color, size)
        self._icon_cache[cache_key] = icon
        return icon

    def _apply_styles(self):
        """Apply stylesheet."""
        t = self._theme

        stylesheet = f"""
            QWidget#HomeRoot {{
                background-color: {t.bg};
            }}

            QWidget#HomeRoot QLabel {{
                color: {t.text};
                background: transparent;
            }}

            QLabel#titleLabel {{
                font-size: {Typography.SIZE_3XL}px;
                font-weight: {Typography.WEIGHT_BOLD};
                color: {t.text};
            }}

            QLabel#subtitleLabel {{
                font-size: {Typography.SIZE_MD}px;
                color: {t.text_secondary};
            }}

            QLabel#currentFileLabel {{
                font-size: {Typography.SIZE_SM}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                background-color: {t.surface};
                border: 1px solid {t.border};
                border-radius: {Radius.MD}px;
                color: {t.text};
            }}

            {get_card_stylesheet(t)}
        """

        self.setStyleSheet(stylesheet)

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
        self.current_file_label.setObjectName("currentFileLabel")
        self.current_file_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_file_label)

        layout.addSpacing(Spacing.MD)

        # Mode cards
        cards = self._build_cards()
        layout.addWidget(cards)

        layout.addStretch(2)
        self.setLayout(layout)

    def _build_header(self) -> QWidget:
        """Build header with app title."""
        container = QWidget()
        container.setObjectName("headerContainer")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(f"v{APP_VERSION} - Suite d'outils biometriques")
        subtitle.setObjectName("subtitleLabel")
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
        """Create a card button."""
        button = QPushButton()
        button.setObjectName("modeCard")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedHeight(140)
        button.setMinimumWidth(280)
        button.setEnabled(enabled)
        button.setCursor(Qt.PointingHandCursor if enabled else Qt.ForbiddenCursor)

        # Load icon
        icon = self._load_icon(icon_name, 48)
        button.setIcon(icon)
        button.setIconSize(QSize(48, 48))

        # Set text
        text = f"{title}\n\n{subtitle}"
        if not enabled:
            text += "\n\n(Bientot disponible)"
        button.setText(text)

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
