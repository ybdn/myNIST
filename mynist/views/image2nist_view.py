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

from mynist.utils.design_tokens import Typography, Spacing, Radius, load_svg_icon


class Image2NISTView(QWidget):
    """Placeholder view for Image-2-NIST feature (coming soon)."""

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _get_icon_path(self, name: str) -> Path:
        """Return path to hub icon."""
        return Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"

    def _load_icon(self, name: str, size: int = 64):
        """Load colored icon with OS color."""
        path = self._get_icon_path(name)
        return load_svg_icon(path, size=size)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.XXXL, Spacing.XXL, Spacing.XXXL, Spacing.XXL)
        layout.setSpacing(Spacing.XL)

        # Header with back button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        back_btn = QPushButton("Retour au Hub")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                border-radius: {Radius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-weight: {Typography.WEIGHT_MEDIUM};
            }}
        """)
        back_btn.clicked.connect(self.back_requested.emit)
        back_icon = self._load_icon("home", 20)
        if not back_icon.isNull():
            back_btn.setIcon(back_icon)
        header.addWidget(back_btn)

        header.addStretch()

        page_title = QLabel("Image-2-NIST")
        page_title.setStyleSheet(f"""
            font-size: {Typography.SIZE_XL}px;
            font-weight: {Typography.WEIGHT_SEMIBOLD};
        """)
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
        frame.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed palette(mid);
                border-radius: {Radius.XL}px;
            }}
        """)
        frame.setFixedSize(500, 320)

        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(Spacing.XXXL, Spacing.XXXL, Spacing.XXXL, Spacing.XXXL)
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
        title.setStyleSheet(f"""
            font-size: {Typography.SIZE_XL}px;
            font-weight: {Typography.WEIGHT_SEMIBOLD};
        """)
        title.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Cette fonctionnalite permettra de convertir\n"
            "des images (JPG, PNG, WSQ, JP2) en fichiers NIST\n"
            "avec metadonnees personnalisables."
        )
        desc.setStyleSheet(f"font-size: {Typography.SIZE_MD}px;")
        desc.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(desc)

        # Coming soon label
        soon = QLabel("Disponible prochainement")
        soon.setStyleSheet(f"""
            font-style: italic;
            font-size: {Typography.SIZE_SM}px;
        """)
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
