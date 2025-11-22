"""Vue dediee a l'export PDF decadactylaire."""

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QGroupBox,
)

from mynist.utils.design_tokens import Typography, Spacing, Radius, load_svg_icon


class PdfExportView(QWidget):
    """Vue pour parametrer et lancer l'export PDF decadactylaire."""

    browse_requested = pyqtSignal()
    export_requested = pyqtSignal(str)
    back_requested = pyqtSignal()
    import_requested = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: Optional[str] = None
        self._build_ui()

    def _get_icon_path(self, name: str) -> Path:
        """Return path to hub icon."""
        return Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"

    def _load_icon(self, name: str, size: int = 24):
        """Load colored icon with OS color."""
        path = self._get_icon_path(name)
        return load_svg_icon(path, size=size)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.XXXL, Spacing.XXL, Spacing.XXXL, Spacing.XXL)
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
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setMinimumWidth(200)
        self.export_btn.setEnabled(False)  # Disabled until a file is loaded
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                font-size: {Typography.SIZE_MD}px;
                padding: {Spacing.MD}px {Spacing.XXXL}px;
                border-radius: {Radius.LG}px;
            }}
        """)
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

        # Title
        title = QLabel("NIST-2-PDF")
        title.setStyleSheet(f"""
            font-size: {Typography.SIZE_XL}px;
            font-weight: {Typography.WEIGHT_SEMIBOLD};
        """)
        header.addWidget(title)

        header.addStretch()

        # Import button
        import_btn = QPushButton("Importer")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.clicked.connect(self.import_requested.emit)
        header.addWidget(import_btn)

        # Close button
        self.close_btn = QPushButton("Fermer")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close_requested.emit)
        self.close_btn.setEnabled(False)
        header.addWidget(self.close_btn)

        return header

    def _build_source_group(self) -> QGroupBox:
        """Build source file display group."""
        group = QGroupBox("Fichier source")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                font-size: {Typography.SIZE_MD}px;
                border-radius: {Radius.LG}px;
                margin-top: 14px;
                padding: {Spacing.LG}px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.LG, Spacing.XL, Spacing.LG, Spacing.LG)

        self.source_label = QLabel("Aucun fichier NIST charge")
        self.source_label.setStyleSheet(f"font-size: {Typography.SIZE_MD}px;")
        layout.addWidget(self.source_label)

        group.setLayout(layout)
        return group

    def _build_destination_group(self) -> QGroupBox:
        """Build destination path input group."""
        group = QGroupBox("Destination")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                font-size: {Typography.SIZE_MD}px;
                border-radius: {Radius.LG}px;
                margin-top: 14px;
                padding: {Spacing.LG}px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(Spacing.LG, Spacing.XL, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Chemin du fichier PDF de sortie...")
        self.output_input.setStyleSheet(f"""
            QLineEdit {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {Radius.MD}px;
                font-size: {Typography.SIZE_MD}px;
            }}
        """)
        layout.addWidget(self.output_input, 1)

        browse_btn = QPushButton("Parcourir...")
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {Radius.MD}px;
            }}
        """)
        browse_btn.clicked.connect(self.browse_requested.emit)
        layout.addWidget(browse_btn)

        group.setLayout(layout)
        return group

    def _build_info_group(self) -> QGroupBox:
        """Build information panel group."""
        group = QGroupBox("Organisation du releve")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                font-size: {Typography.SIZE_MD}px;
                border-radius: {Radius.LG}px;
                margin-top: 14px;
                padding: {Spacing.LG}px;
            }}
        """)
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
        formats_label.setStyleSheet(f"font-size: {Typography.SIZE_SM}px;")
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
            self.close_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
        else:
            self.source_label.setText("Aucun fichier NIST charge")
            self.output_input.clear()
            self.close_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
