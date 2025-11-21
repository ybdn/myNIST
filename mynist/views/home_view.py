"""Home view (hub) for mode selection and recent files."""

from pathlib import Path
from typing import List, Dict, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
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
)


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
        self.setObjectName("HomeRoot")
        self._apply_theme()
        self._build_ui()

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

        self.setStyleSheet(
            f"""
            #HomeRoot {{
                background-color: {window.name()};
                color: {text.name()};
            }}
            #HomeRoot QLabel {{
                color: {text.name()};
            }}
            QPushButton#modeCard {{
                text-align: left;
                padding: 12px;
                border: 1px solid {border.name()};
                border-radius: 10px;
                background: {card_bg.name()};
                color: {text.name()};
            }}
            QPushButton#modeCard:hover {{
                border-color: {hover_border.name()};
                background: {card_hover.name()};
            }}
            QFrame#dropFrame {{
                background: {drop_bg.name()};
                color: {text.name()};
                border: 1px dashed {border.name()};
                border-radius: 8px;
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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.current_file_label = QLabel("Aucun fichier en cours.")
        self.current_file_label.setObjectName("currentFileLabel")
        layout.addWidget(self.current_file_label)

        cards = self._build_cards()
        layout.addWidget(cards)

        drop = self._build_drop_hint()
        layout.addWidget(drop)

        recents = self._build_recents()
        layout.addWidget(recents)

        layout.addStretch()
        self.setLayout(layout)

    def _build_cards(self) -> QWidget:
        container = QWidget()
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(12)

        cards_data = [
            ("Visualiser / Éditer", "Parcours 3 panneaux, inspection et édition Type-2", "viewer"),
            ("Comparer", "Côte à côte, points, recalage DPI", "comparison"),
            ("Exporter relevé PDF", "Décadactylaire A4, métadonnées Type-1/2", "pdf"),
        ]

        for title, subtitle, mode in cards_data:
            button = self._make_card_button(title, subtitle, mode)
            hlayout.addWidget(button)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout.addItem(spacer)

        container.setLayout(hlayout)
        return container

    def _make_card_button(self, title: str, subtitle: str, mode: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName("modeCard")
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setFixedSize(220, 120)
        button.setText(f"{title}\n{subtitle}")
        button.clicked.connect(lambda: self.mode_requested.emit(mode))
        return button

    def _build_drop_hint(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("dropFrame")
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)

        hint = QLabel("Glissez un fichier .nist/.eft/.an2 ici pour ouvrir\nou utilisez « Parcourir… »")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        frame.setLayout(layout)
        return frame

    def _build_recents(self) -> QWidget:
        container = QWidget()
        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("<b>Derniers fichiers</b>")
        header.addWidget(title)
        header.addStretch()

        browse_button = QPushButton("Parcourir…")
        browse_button.clicked.connect(self.open_file_requested.emit)
        header.addWidget(browse_button)

        clear_button = QPushButton("Vider la liste")
        clear_button.clicked.connect(self.clear_recents_requested.emit)
        header.addWidget(clear_button)

        vlayout.addLayout(header)

        self.recents_list = QListWidget()
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
            self.current_file_label.setText(f"Fichier en cours : {name} ({path}) — mode {mode}")
        else:
            self.current_file_label.setText("Aucun fichier en cours.")

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
