"""Image-2-NIST placeholder view (coming soon)."""

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPalette, QColor, QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)


class Image2NISTView(QWidget):
    """Placeholder view for Image-2-NIST feature (coming soon)."""

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Image2NISTRoot")
        self._apply_theme()
        self._build_ui()

    def _get_icon_path(self, name: str) -> Path:
        """Return path to hub icon."""
        return Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"

    def _load_icon(self, name: str, size: int = 64) -> QIcon:
        """Load SVG icon."""
        path = self._get_icon_path(name)
        if not path.exists():
            return QIcon()

        renderer = QSvgRenderer(str(path))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    def _apply_theme(self):
        """Compute palette-aware stylesheet."""
        palette = self.palette()
        window = palette.color(QPalette.Window)
        base = palette.color(QPalette.Base)
        text = palette.color(QPalette.Text)
        border = palette.color(QPalette.Mid)

        is_dark = window.value() < 96 or base.value() < 96

        def tweak(color: QColor, factor: int) -> QColor:
            return color.lighter(factor) if is_dark else color.darker(factor)

        card_bg = tweak(base, 110)

        self.setStyleSheet(
            f"""
            #Image2NISTRoot {{
                background-color: {window.name()};
                color: {text.name()};
            }}
            #Image2NISTRoot QLabel {{
                color: {text.name()};
            }}
            #titleLabel {{
                font-size: 20px;
                font-weight: bold;
            }}
            #subtitleLabel {{
                font-size: 14px;
                color: {border.name()};
            }}
            QFrame#placeholderFrame {{
                background: {card_bg.name()};
                border: 2px dashed {border.name()};
                border-radius: 12px;
            }}
            """
        )

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header with back button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        back_btn = QPushButton("Retour au Hub")
        back_btn.clicked.connect(self.back_requested.emit)
        back_icon = self._load_icon("home", 20)
        if not back_icon.isNull():
            back_btn.setIcon(back_icon)
        header.addWidget(back_btn)

        header.addStretch()

        page_title = QLabel("Image-2-NIST")
        page_title.setObjectName("titleLabel")
        header.addWidget(page_title)

        header.addStretch()
        # Spacer to balance the back button
        spacer = QWidget()
        spacer.setFixedWidth(100)
        header.addWidget(spacer)

        layout.addLayout(header)

        # Central placeholder
        layout.addStretch()

        frame = QFrame()
        frame.setObjectName("placeholderFrame")
        frame.setFixedSize(500, 300)

        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(32, 32, 32, 32)
        frame_layout.setSpacing(16)
        frame_layout.setAlignment(Qt.AlignCenter)

        # Icon
        icon_label = QLabel()
        icon = self._load_icon("image2nist", 64)
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(icon_label)

        # Title
        title = QLabel("En developpement")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Cette fonctionnalite permettra de convertir\n"
            "des images (JPG, PNG, WSQ, JP2) en fichiers NIST\n"
            "avec metadonnees personnalisables."
        )
        desc.setObjectName("subtitleLabel")
        desc.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(desc)

        # Coming soon label
        soon = QLabel("Disponible prochainement")
        soon.setStyleSheet("font-style: italic; margin-top: 16px;")
        soon.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(soon)

        frame.setLayout(frame_layout)

        # Center the frame
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(frame)
        center_layout.addStretch()

        layout.addLayout(center_layout)

        layout.addStretch()

        self.setLayout(layout)
