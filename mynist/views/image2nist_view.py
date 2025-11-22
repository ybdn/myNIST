"""Image-2-NIST placeholder view (coming soon)."""

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from mynist.utils.design_tokens import (
    Colors, Typography, Spacing, Radius
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

    def _is_dark_mode(self) -> bool:
        """Detect if system is in dark mode."""
        palette = self.palette()
        window = palette.color(QPalette.Window)
        return window.value() < 128

    def _apply_theme(self):
        """Apply NIST Studio Design System theme."""
        is_dark = self._is_dark_mode()

        if is_dark:
            window_bg = Colors.BG_DARK
            surface_bg = Colors.SURFACE_DARK
            text_primary = Colors.TEXT_PRIMARY_DARK
            border = Colors.BORDER_DARK
        else:
            window_bg = Colors.BG_LIGHT
            surface_bg = Colors.SURFACE_LIGHT
            text_primary = Colors.TEXT_PRIMARY_LIGHT
            border = Colors.BORDER_SUBTLE

        self.setStyleSheet(f"""
            #Image2NISTRoot {{
                background-color: {window_bg};
            }}

            #Image2NISTRoot QLabel {{
                color: {text_primary};
            }}

            #titleLabel {{
                font-size: {Typography.SIZE_LARGE}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                color: {Colors.PRIMARY if not is_dark else text_primary};
            }}

            #subtitleLabel {{
                font-size: {Typography.SIZE_NORMAL}px;
                color: {Colors.TEXT_SECONDARY};
            }}

            #hubButton {{
                background: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: {Radius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-weight: {Typography.WEIGHT_MEDIUM};
            }}

            #hubButton:hover {{
                background: {Colors.HOVER_ACCENT};
            }}

            QFrame#placeholderFrame {{
                background: {surface_bg};
                border: 2px dashed {border};
                border-radius: {Radius.XL}px;
            }}

            #comingSoonLabel {{
                font-style: italic;
                color: {Colors.TEXT_SECONDARY};
                margin-top: {Spacing.LG}px;
            }}
        """)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(
            Spacing.XXXL, Spacing.XXL,
            Spacing.XXXL, Spacing.XXL
        )
        layout.setSpacing(Spacing.XL)

        # Header with back button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        back_btn = QPushButton("Retour au Hub")
        back_btn.setObjectName("hubButton")
        back_btn.setCursor(Qt.PointingHandCursor)
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
        spacer.setFixedWidth(120)
        header.addWidget(spacer)

        layout.addLayout(header)

        # Central placeholder
        layout.addStretch()

        frame = QFrame()
        frame.setObjectName("placeholderFrame")
        frame.setFixedSize(500, 320)

        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(
            Spacing.XXXL, Spacing.XXXL,
            Spacing.XXXL, Spacing.XXXL
        )
        frame_layout.setSpacing(Spacing.LG)
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
        soon.setObjectName("comingSoonLabel")
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
