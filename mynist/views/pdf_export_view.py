"""Vue dédiée à l'export PDF décadactylaire."""

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QColor, QPalette, QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QGroupBox,
    QSizePolicy,
)


class PdfExportView(QWidget):
    """Vue pour paramétrer et lancer l'export PDF décadactylaire."""

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

        card_bg = tweak(base, 110)
        info_bg = tweak(base, 105)

        self.setStyleSheet(
            f"""
            #PdfExportRoot {{
                background-color: {window.name()};
                color: {text.name()};
            }}
            #PdfExportRoot QLabel {{
                color: {text.name()};
            }}
            #titleLabel {{
                font-size: 20px;
                font-weight: bold;
            }}
            #subtitleLabel {{
                font-size: 12px;
                color: {border.name()};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {border.name()};
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px;
                background: {card_bg.name()};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 12px;
                background: {window.name()};
                border-radius: 4px;
            }}
            QFrame#sourceFrame {{
                background: {info_bg.name()};
                border: 1px solid {border.name()};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame#infoFrame {{
                background: {info_bg.name()};
                border: 1px solid {border.name()};
                border-radius: 8px;
            }}
            QPushButton#exportBtn {{
                background: {highlight.name()};
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 32px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton#exportBtn:hover {{
                background: {tweak(highlight, 120).name()};
            }}
            QPushButton#exportBtn:disabled {{
                background: {border.name()};
                color: {tweak(text, 150).name()};
            }}
            QLineEdit {{
                padding: 8px 12px;
                border: 1px solid {border.name()};
                border-radius: 6px;
                background: {base.name()};
            }}
            """
        )

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header with back button and title
        header = self._build_header()
        layout.addLayout(header)

        # Content area (centered)
        content = QWidget()
        content.setMaximumWidth(700)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

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
        layout.setContentsMargins(16, 20, 16, 16)

        self.source_label = QLabel("Aucun fichier NIST charge")
        self.source_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.source_label)

        group.setLayout(layout)
        return group

    def _build_destination_group(self) -> QGroupBox:
        """Build destination path input group."""
        group = QGroupBox("Destination")
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)

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
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(8)

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
        layout.addSpacing(12)
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
            self.source_label.setText(f"📄  {name}")
            # Suggest output path
            suggested = str(Path(path).with_suffix(".pdf"))
            self.output_input.setText(suggested)
        else:
            self.source_label.setText("Aucun fichier NIST charge")
            self.output_input.clear()
