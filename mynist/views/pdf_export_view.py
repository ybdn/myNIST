"""Vue dediee a l'export PDF decadactylaire."""

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPalette, QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QGroupBox,
)

from mynist.utils.design_tokens import (
    Colors, Typography, Spacing, Radius
)


class PdfExportView(QWidget):
    """Vue pour parametrer et lancer l'export PDF decadactylaire."""

    browse_requested = pyqtSignal()
    export_requested = pyqtSignal(str)
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: Optional[str] = None
        self.setObjectName("PdfExportRoot")
        self._apply_theme()
        self._build_ui()

    def _get_icon_path(self, name: str) -> Path:
        """Return path to hub icon."""
        return Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"

    def _load_icon(self, name: str, size: int = 24) -> QIcon:
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
            #PdfExportRoot {{
                background-color: {window_bg};
            }}

            #PdfExportRoot QLabel {{
                color: {text_primary};
            }}

            #titleLabel {{
                font-size: {Typography.SIZE_LARGE}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                color: {Colors.PRIMARY if not is_dark else text_primary};
            }}

            #subtitleLabel {{
                font-size: {Typography.SIZE_SMALL}px;
                color: {Colors.TEXT_SECONDARY};
            }}

            QGroupBox {{
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                border: 1px solid {border};
                border-radius: {Radius.LG}px;
                margin-top: 12px;
                padding: {Spacing.LG}px;
                background: {surface_bg};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 12px;
                background: {window_bg};
                border-radius: {Radius.SM}px;
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

            #exportBtn {{
                background: {Colors.ACCENT};
                color: white;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                font-size: {Typography.SIZE_NORMAL}px;
                padding: {Spacing.MD}px {Spacing.XXXL}px;
                border-radius: {Radius.LG}px;
                border: none;
            }}

            #exportBtn:hover {{
                background: {Colors.HOVER_ACCENT};
            }}

            #exportBtn:disabled {{
                background: {Colors.DISABLED};
                color: {Colors.TEXT_SECONDARY};
            }}

            QLineEdit {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border: 1px solid {border};
                border-radius: {Radius.MD}px;
                background: {surface_bg};
                color: {text_primary};
            }}

            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(
            Spacing.XXXL, Spacing.XXL,
            Spacing.XXXL, Spacing.XXL
        )
        layout.setSpacing(Spacing.XL)

        # Header with back button and title
        header = self._build_header()
        layout.addLayout(header)

        # Content area (centered)
        content = QWidget()
        content.setMaximumWidth(700)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(Spacing.XL)

        # Source file group
        source_group = self._build_source_group()
        content_layout.addWidget(source_group)

        # Destination group
        dest_group = self._build_destination_group()
        content_layout.addWidget(dest_group)

        # Export button (centered)
        export_row = QHBoxLayout()
        export_row.addStretch()

        self.export_btn = QPushButton("Exporter le PDF")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setMinimumWidth(200)
        self.export_btn.clicked.connect(self._on_export_clicked)
        export_icon = self._load_icon("pdf", 20)
        if not export_icon.isNull():
            self.export_btn.setIcon(export_icon)
        export_row.addWidget(self.export_btn)

        export_row.addStretch()
        content_layout.addLayout(export_row)

        # Info panel
        info_group = self._build_info_group()
        content_layout.addWidget(info_group)

        content.setLayout(content_layout)

        # Center the content
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(content)
        center_layout.addStretch()

        layout.addLayout(center_layout)
        layout.addStretch()

        self.setLayout(layout)

    def _build_header(self) -> QHBoxLayout:
        """Build header with back button and title."""
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        # Back button
        back_btn = QPushButton("Retour au Hub")
        back_btn.setObjectName("hubButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.back_requested.emit)
        back_icon = self._load_icon("home", 20)
        if not back_icon.isNull():
            back_btn.setIcon(back_icon)
        header.addWidget(back_btn)

        header.addStretch()

        # Title
        title = QLabel("NIST-2-PDF")
        title.setObjectName("titleLabel")
        header.addWidget(title)

        header.addStretch()

        # Spacer to balance the back button
        spacer = QWidget()
        spacer.setFixedWidth(120)
        header.addWidget(spacer)

        return header

    def _build_source_group(self) -> QGroupBox:
        """Build source file display group."""
        group = QGroupBox("Fichier source")
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.LG, Spacing.XL, Spacing.LG, Spacing.LG)

        self.source_label = QLabel("Aucun fichier NIST charge")
        self.source_label.setStyleSheet(f"font-size: {Typography.SIZE_NORMAL}px;")
        layout.addWidget(self.source_label)

        group.setLayout(layout)
        return group

    def _build_destination_group(self) -> QGroupBox:
        """Build destination path input group."""
        group = QGroupBox("Destination")
        layout = QHBoxLayout()
        layout.setContentsMargins(Spacing.LG, Spacing.XL, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Chemin du fichier PDF de sortie...")
        layout.addWidget(self.output_input, 1)

        browse_btn = QPushButton("Parcourir...")
        browse_btn.clicked.connect(self.browse_requested.emit)
        layout.addWidget(browse_btn)

        group.setLayout(layout)
        return group

    def _build_info_group(self) -> QGroupBox:
        """Build information panel group."""
        group = QGroupBox("Organisation du releve")
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.LG, Spacing.XL, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.SM)

        info_items = [
            ("Main gauche", "Pouce, Index, Majeur, Annulaire, Auriculaire"),
            ("Main droite", "Pouce, Index, Majeur, Annulaire, Auriculaire"),
            ("Simultane", "Main gauche, Pouces, Main droite"),
            ("Paumes", "Gauche, Droite"),
        ]

        for title, details in info_items:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)

            title_label = QLabel(f"<b>{title} :</b>")
            title_label.setFixedWidth(120)
            row.addWidget(title_label)

            details_label = QLabel(details)
            row.addWidget(details_label)
            row.addStretch()

            layout.addLayout(row)

        # Formats info
        layout.addSpacing(Spacing.MD)
        formats_label = QLabel(
            "<i>Formats supportes : WSQ, JPEG, PNG, JPEG2000</i>"
        )
        formats_label.setObjectName("subtitleLabel")
        layout.addWidget(formats_label)

        group.setLayout(layout)
        return group

    def _on_export_clicked(self):
        """Handle export button click."""
        output_path = self.output_input.text().strip()
        self.export_requested.emit(output_path)

    def set_current_file(self, path: Optional[str]):
        """Update the current file display."""
        self.current_file = path
        if path:
            name = Path(path).name
            self.source_label.setText(f"{name}")
            # Suggest output path
            suggested = str(Path(path).with_suffix(".pdf"))
            self.output_input.setText(suggested)
        else:
            self.source_label.setText("Aucun fichier NIST charge")
            self.output_input.clear()
