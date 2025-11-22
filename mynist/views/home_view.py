"""Home view (hub) for mode selection."""

from pathlib import Path
from typing import Optional, Dict

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QPalette, QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QGridLayout,
)

from mynist.utils.constants import APP_NAME, APP_VERSION


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
        """Load SVG icon with current palette color."""
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

    def _apply_theme(self):
        """Compute palette-aware stylesheet for light/dark compatibility."""
        palette = self.palette()
        window = palette.color(QPalette.Window)
        base = palette.color(QPalette.Base)
        text = palette.color(QPalette.Text)
        border = palette.color(QPalette.Mid)
        highlight = palette.color(QPalette.Highlight)

        is_dark = window.value() < 96 or base.value() < 96

        def tweak(color: QColor, factor: int) -> QColor:
            return color.lighter(factor) if is_dark else color.darker(factor)

        card_bg = tweak(base, 115)
        card_hover = tweak(base, 130)
        hover_border = highlight if highlight.alpha() > 0 else border
        disabled_bg = tweak(base, 95)

        self.setStyleSheet(
            f"""
            #HomeRoot {{
                background-color: {window.name()};
                color: {text.name()};
            }}
            #HomeRoot QLabel {{
                color: {text.name()};
            }}
            #titleLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {text.name()};
            }}
            #subtitleLabel {{
                font-size: 13px;
                color: {border.name()};
            }}
            #currentFileLabel {{
                font-size: 12px;
                padding: 10px 16px;
                background: {tweak(base, 105).name()};
                border: 1px solid {border.name()};
                border-radius: 8px;
            }}
            QPushButton#modeCard {{
                text-align: center;
                padding: 20px;
                border: 1px solid {border.name()};
                border-radius: 12px;
                background: {card_bg.name()};
                color: {text.name()};
                font-size: 13px;
            }}
            QPushButton#modeCard:hover {{
                border-color: {hover_border.name()};
                background: {card_hover.name()};
            }}
            QPushButton#modeCard:disabled {{
                background: {disabled_bg.name()};
                color: {border.name()};
            }}
            """
        )

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(24)

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

        layout.addSpacing(8)

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
        layout.setSpacing(6)
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
        grid.setSpacing(16)

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
        button.setFixedHeight(140)
        button.setMinimumWidth(280)
        button.setEnabled(enabled)

        icon = self._load_icon(icon_name, 48)
        button.setIcon(icon)
        button.setIconSize(QSize(48, 48))

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
