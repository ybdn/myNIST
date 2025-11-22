"""Home view (hub) for mode selection."""

from pathlib import Path
from typing import Optional, Dict

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QPalette, QIcon, QPixmap, QPainter, QFont
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QGridLayout,
    QGraphicsDropShadowEffect,
)

from mynist.utils.constants import APP_NAME, APP_VERSION
from mynist.utils.design_tokens import (
    Colors, Typography, Spacing, Radius, Dimensions
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
        self.setObjectName("HomeRoot")
        self._apply_theme()
        self._build_ui()

    def _get_icon_path(self, name: str) -> Path:
        """Return path to hub icon."""
        return Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"

    def _load_icon(self, name: str, size: int = 48) -> QIcon:
        """Load SVG icon."""
        if name in self._icon_cache:
            return self._icon_cache[name]

        path = self._get_icon_path(name)
        if not path.exists():
            return QIcon()

        renderer = QSvgRenderer(str(path))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        icon = QIcon(pixmap)
        self._icon_cache[name] = icon
        return icon

    def _is_dark_mode(self) -> bool:
        """Detect if system is in dark mode."""
        palette = self.palette()
        window = palette.color(QPalette.Window)
        return window.value() < 128

    def _apply_theme(self):
        """Apply NIST Studio design system theme."""
        is_dark = self._is_dark_mode()

        # Select colors based on theme
        if is_dark:
            window_bg = Colors.BG_DARK
            surface_bg = Colors.SURFACE_DARK
            text_primary = Colors.TEXT_PRIMARY_DARK
            text_secondary = Colors.TEXT_SECONDARY
            border = Colors.BORDER_DARK
            card_hover_bg = "#353D47"
        else:
            window_bg = Colors.BG_LIGHT
            surface_bg = Colors.SURFACE_LIGHT
            text_primary = Colors.TEXT_PRIMARY_LIGHT
            text_secondary = Colors.TEXT_SECONDARY
            border = Colors.BORDER_SUBTLE
            card_hover_bg = "#EEF1F5"

        self.setStyleSheet(f"""
            #HomeRoot {{
                background-color: {window_bg};
            }}

            #titleLabel {{
                font-size: {Typography.SIZE_TITLE}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                color: {Colors.PRIMARY if not is_dark else Colors.TEXT_PRIMARY_DARK};
            }}

            #subtitleLabel {{
                font-size: {Typography.SIZE_NORMAL}px;
                color: {text_secondary};
            }}

            #currentFileLabel {{
                font-size: {Typography.SIZE_SMALL}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                background: {surface_bg};
                border: 1px solid {border};
                border-radius: {Radius.MD}px;
                color: {text_primary};
            }}

            QPushButton#modeCard {{
                text-align: center;
                padding: {Spacing.CARD_PADDING}px;
                border: 1px solid {border};
                border-radius: {Radius.XL}px;
                background: {surface_bg};
                color: {text_primary};
                font-size: {Typography.SIZE_NORMAL}px;
            }}

            QPushButton#modeCard:hover {{
                border: 2px solid {Colors.ACCENT};
                background: {card_hover_bg};
            }}

            QPushButton#modeCard:disabled {{
                background: {"#2A2E35" if is_dark else "#E8EAED"};
                color: {text_secondary};
                border-color: {border};
            }}
        """)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(
            Spacing.XXXL, Spacing.XXXL,
            Spacing.XXXL, Spacing.XXXL
        )
        layout.setSpacing(Spacing.XXL)

        # Vertical centering
        layout.addStretch(1)

        # Header with title
        header = self._build_header()
        layout.addWidget(header)

        # Current file status
        self.current_file_label = QLabel("Aucun fichier ouvert")
        self.current_file_label.setObjectName("currentFileLabel")
        self.current_file_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_file_label)

        layout.addSpacing(Spacing.MD)

        # Mode cards (4 cards in grid)
        cards = self._build_cards()
        layout.addWidget(cards)

        layout.addStretch(2)

        self.setLayout(layout)

    def _build_header(self) -> QWidget:
        """Build header with app title."""
        container = QWidget()
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
            {
                "title": "NIST-Viewer",
                "subtitle": "Visualiser et editer\ndes fichiers NIST",
                "mode": "viewer",
                "icon": "viewer",
                "enabled": True,
            },
            {
                "title": "NIST-Compare",
                "subtitle": "Comparer cote a cote\ndeux images biometriques",
                "mode": "comparison",
                "icon": "compare",
                "enabled": True,
            },
            {
                "title": "NIST-2-PDF",
                "subtitle": "Exporter un releve\ndecadactylaire PDF",
                "mode": "pdf",
                "icon": "pdf",
                "enabled": True,
            },
            {
                "title": "Image-2-NIST",
                "subtitle": "Convertir une image\nen fichier NIST",
                "mode": "image2nist",
                "icon": "image2nist",
                "enabled": False,
            },
        ]

        for i, card_data in enumerate(cards_data):
            button = self._make_card_button(
                card_data["title"],
                card_data["subtitle"],
                card_data["mode"],
                card_data["icon"],
                card_data["enabled"],
            )
            row = i // 2
            col = i % 2
            grid.addWidget(button, row, col)

        container.setLayout(grid)

        # Center the grid
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(container, 0, Qt.AlignCenter)
        wrapper.setLayout(wrapper_layout)

        return wrapper

    def _make_card_button(
        self, title: str, subtitle: str, mode: str, icon_name: str, enabled: bool
    ) -> QPushButton:
        """Create a card button with icon."""
        button = QPushButton()
        button.setObjectName("modeCard")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedHeight(Dimensions.CARD_HEIGHT)
        button.setMinimumWidth(Dimensions.CARD_MIN_WIDTH)
        button.setEnabled(enabled)
        button.setCursor(Qt.PointingHandCursor if enabled else Qt.ForbiddenCursor)

        icon = self._load_icon(icon_name, Dimensions.CARD_HEIGHT // 3)
        button.setIcon(icon)
        button.setIconSize(QSize(Dimensions.CARD_HEIGHT // 3, Dimensions.CARD_HEIGHT // 3))

        if not enabled:
            text = f"{title}\n\n{subtitle}\n\n(Bientot disponible)"
        else:
            text = f"{title}\n\n{subtitle}"
        button.setText(text)

        if enabled:
            button.clicked.connect(lambda: self.mode_requested.emit(mode))

        return button

    def _emit_resume(self):
        if self.current_file:
            self.resume_requested.emit()

    def set_current_file(self, path: Optional[str], mode: str = "viewer"):
        """Update banner and resume state."""
        self.current_file = path
        self.current_mode = mode
        if path:
            name = Path(path).name
            mode_labels = {
                "viewer": "NIST-Viewer",
                "comparison": "NIST-Compare",
                "pdf": "NIST-2-PDF",
            }
            mode_label = mode_labels.get(mode, mode)
            self.current_file_label.setText(f"Fichier en cours : {name} - Mode : {mode_label}")
        else:
            self.current_file_label.setText("Aucun fichier ouvert")

    def set_recent_entries(self, entries):
        """Kept for compatibility - no longer displays recents."""
        pass
