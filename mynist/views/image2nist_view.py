"""Image-2-NIST placeholder view (coming soon)."""

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from mynist.utils.design_tokens import (
    Colors, Typography, Spacing, Radius,
    Theme, detect_dark_mode, load_colored_icon
)


class Image2NISTView(QWidget):
    """Placeholder view for Image-2-NIST feature (coming soon)."""

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Image2NISTRoot")
        self._setup_theme()
        self._build_ui()

    def _get_icon_path(self, name: str) -> Path:
        """Return path to hub icon."""
        return Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"

    def _setup_theme(self):
        """Setup theme and apply stylesheet."""
        self._is_dark = detect_dark_mode(self)
        self._theme = Theme(self._is_dark)
        self._apply_stylesheet()

    def _load_icon(self, name: str, size: int = 64, on_accent: bool = False):
        """Load colored icon."""
        path = self._get_icon_path(name)
        color = Colors.ICON_ON_ACCENT if on_accent else self._theme.icon
        return load_colored_icon(path, color, size)

    def _apply_stylesheet(self):
        """Apply theme stylesheet."""
        t = self._theme

        self.setStyleSheet(f"""
            #Image2NISTRoot {{
                background-color: {t.bg};
            }}

            #Image2NISTRoot QLabel {{
                color: {t.text};
            }}

            #titleLabel {{
                font-size: {Typography.SIZE_XL}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                color: {t.text};
            }}

            #subtitleLabel {{
                font-size: {Typography.SIZE_MD}px;
                color: {t.text_secondary};
            }}

            #hubButton {{
                background: {t.accent};
                color: white;
                border: none;
                border-radius: {Radius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-weight: {Typography.WEIGHT_MEDIUM};
            }}

            #hubButton:hover {{
                background: {t.accent_hover};
            }}

            QFrame#placeholderFrame {{
                background: {t.surface};
                border: 2px dashed {t.border};
                border-radius: {Radius.XL}px;
            }}

            #comingSoonLabel {{
                font-style: italic;
                color: {t.text_secondary};
            }}
        """)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.XXXL, Spacing.XXL, Spacing.XXXL, Spacing.XXL)
        layout.setSpacing(Spacing.XL)

        # Header with back button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        back_btn = QPushButton("Retour au Hub")
        back_btn.setObjectName("hubButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.back_requested.emit)
        back_icon = self._load_icon("home", 20, on_accent=True)
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
        frame_layout.setContentsMargins(Spacing.XXXL, Spacing.XXXL, Spacing.XXXL, Spacing.XXXL)
        frame_layout.setSpacing(Spacing.LG)
        frame_layout.setAlignment(Qt.AlignCenter)

        # Icon
        icon_label = QLabel()
        icon = self._load_icon("image2nist", 64, on_accent=False)
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
