"""Home view (hub) for mode selection and recent files."""

from pathlib import Path
from typing import List, Dict, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QPalette, QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QSizePolicy,
    QSpacerItem,
    QGridLayout,
)

from mynist.utils.constants import APP_NAME, APP_VERSION


class HomeView(QWidget):
    """Hub screen with mode cards, drop hint and recent files."""

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

        # Create colored icon from SVG
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
        alt = palette.color(QPalette.AlternateBase)
        border = palette.color(QPalette.Mid)
        highlight = palette.color(QPalette.Highlight)

        # Detect dark-ish palette
        is_dark = window.value() < 96 or base.value() < 96  # 0-255 scale

        def tweak(color: QColor, factor: int) -> QColor:
            return color.lighter(factor) if is_dark else color.darker(factor)

        card_bg = tweak(base, 115)
        card_hover = tweak(base, 130)
        drop_bg = alt if alt != base else tweak(base, 105)
        list_bg = tweak(base, 103)
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
                font-size: 24px;
                font-weight: bold;
                color: {text.name()};
            }}
            #subtitleLabel {{
                font-size: 12px;
                color: {border.name()};
            }}
            QPushButton#modeCard {{
                text-align: center;
                padding: 16px;
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
            QFrame#dropFrame {{
                background: {drop_bg.name()};
                color: {text.name()};
                border: 2px dashed {border.name()};
                border-radius: 10px;
            }}
            QListWidget {{
                background: {list_bg.name()};
                color: {text.name()};
                border: 1px solid {border.name()};
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background: {hover_border.name()};
                color: {"#ffffff" if is_dark else text.name()};
            }}
            """
        )

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header with title
        header = self._build_header()
        layout.addWidget(header)

        # Current file status
        self.current_file_label = QLabel("Aucun fichier ouvert")
        self.current_file_label.setObjectName("currentFileLabel")
        self.current_file_label.setStyleSheet("padding: 8px; background: rgba(0,0,0,0.03); border-radius: 6px;")
        layout.addWidget(self.current_file_label)

        # Mode cards (4 cards in grid)
        cards = self._build_cards()
        layout.addWidget(cards)

        # Drop zone
        drop = self._build_drop_hint()
        layout.addWidget(drop)

        # Recent files
        recents = self._build_recents()
        layout.addWidget(recents)

        layout.addStretch()
        self.setLayout(layout)

    def _build_header(self) -> QWidget:
        """Build header with app title."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
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
                "enabled": False,  # Not yet developed
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
        return container

    def _make_card_button(
        self, title: str, subtitle: str, mode: str, icon_name: str, enabled: bool
    ) -> QPushButton:
        """Create a card button with icon."""
        button = QPushButton()
        button.setObjectName("modeCard")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedHeight(140)
        button.setEnabled(enabled)

        # Set icon
        icon = self._load_icon(icon_name, 48)
        button.setIcon(icon)
        button.setIconSize(QSize(48, 48))

        # Build text with title and subtitle
        if not enabled:
            text = f"{title}\n\n{subtitle}\n\n(Bientot disponible)"
        else:
            text = f"{title}\n\n{subtitle}"
        button.setText(text)

        if enabled:
            button.clicked.connect(lambda: self.mode_requested.emit(mode))

        return button

    def _build_drop_hint(self) -> QWidget:
        """Build drop zone for file drag & drop."""
        frame = QFrame()
        frame.setObjectName("dropFrame")
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFixedHeight(80)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)

        hint = QLabel("Glissez un fichier .nist / .eft / .an2 ici pour l'ouvrir\nou cliquez sur Parcourir...")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        frame.setLayout(layout)
        return frame

    def _build_recents(self) -> QWidget:
        """Build recent files section."""
        container = QWidget()
        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Fichiers recents")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(title)
        header.addStretch()

        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.open_file_requested.emit)
        header.addWidget(browse_button)

        clear_button = QPushButton("Vider la liste")
        clear_button.clicked.connect(self.clear_recents_requested.emit)
        header.addWidget(clear_button)

        vlayout.addLayout(header)

        self.recents_list = QListWidget()
        self.recents_list.setMaximumHeight(150)
        self.recents_list.itemDoubleClicked.connect(self._on_recent_double_clicked)
        vlayout.addWidget(self.recents_list)

        container.setLayout(vlayout)
        return container

    def _on_recent_double_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if path:
            self.open_recent_requested.emit(path)

    def _emit_resume(self):
        if self.current_file:
            self.resume_requested.emit()

    def set_current_file(self, path: Optional[str], mode: str = "viewer"):
        """Update banner and resume state."""
        self.current_file = path
        self.current_mode = mode
        has_file = path is not None
        if has_file:
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

    def set_recent_entries(self, entries: List[Dict[str, object]]):
        """Populate recent list."""
        self.recents_list.clear()
        for item in entries:
            path = str(item.get("path", ""))
            exists = bool(item.get("exists", True))
            summary_types = item.get("summary_types") or []

            name = Path(path).name
            subtext = f"Types: {', '.join(str(t) for t in summary_types)}" if summary_types else ""
            status = " (introuvable)" if not exists else ""
            display = f"{name}{status}"

            list_item = QListWidgetItem(display)
            list_item.setData(Qt.UserRole, path)
            tooltip_lines = [path]
            opened_at = item.get("opened_at")
            if opened_at:
                tooltip_lines.append(f"Ouv. : {opened_at}")
            if subtext:
                tooltip_lines.append(subtext)
            list_item.setToolTip("\n".join(tooltip_lines))

            if not exists:
                list_item.setForeground(Qt.gray)

            self.recents_list.addItem(list_item)
