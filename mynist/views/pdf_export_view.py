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
    QScrollArea,
    QSplitter,
    QFrame,
)
from PyQt5.QtGui import QPixmap, QImage

from mynist.utils.design_tokens import Typography, Spacing, Radius, load_svg_icon


class PdfExportView(QWidget):
    """Vue pour parametrer et lancer l'export PDF decadactylaire."""

    browse_requested = pyqtSignal()
    export_requested = pyqtSignal(str)
    back_requested = pyqtSignal()
    import_requested = pyqtSignal()
    close_requested = pyqtSignal()
    preview_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: Optional[str] = None
        self._preview_image = None
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
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        # Header with back button and title
        header = self._build_header()
        layout.addLayout(header)

        # Main splitter: controls on left, preview on right
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        left_layout.setSpacing(Spacing.LG)

        # Source file group
        source_group = self._build_source_group()
        left_layout.addWidget(source_group)

        # Destination group
        dest_group = self._build_destination_group()
        left_layout.addWidget(dest_group)

        # Buttons row
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(Spacing.MD)

        self.export_btn = QPushButton("Exporter le PDF")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setMinimumWidth(180)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                font-size: {Typography.SIZE_MD}px;
                padding: {Spacing.MD}px {Spacing.XL}px;
                border-radius: {Radius.LG}px;
            }}
        """)
        self.export_btn.clicked.connect(self._on_export_clicked)
        export_icon = self._load_icon("pdf", 20)
        if not export_icon.isNull():
            self.export_btn.setIcon(export_icon)
        buttons_row.addWidget(self.export_btn)

        buttons_row.addStretch()
        left_layout.addLayout(buttons_row)

        # Info panel
        info_group = self._build_info_group()
        left_layout.addWidget(info_group)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)

        # Right panel: preview
        right_panel = self._build_preview_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 500])

        layout.addWidget(splitter, 1)

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

    def _build_preview_panel(self) -> QWidget:
        """Build the PDF preview panel."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a1a;
                border-radius: {Radius.LG}px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Header
        header = QHBoxLayout()
        title = QLabel("Aperçu du PDF")
        title.setStyleSheet(f"""
            font-weight: {Typography.WEIGHT_SEMIBOLD};
            font-size: {Typography.SIZE_MD}px;
            color: #ffffff;
        """)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Scroll area for preview
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #2a2a2a;
            }
        """)

        # Preview label
        self.preview_label = QLabel("Chargez un fichier NIST pour voir l'aperçu")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("color: #888888;")
        self.preview_label.setMinimumSize(300, 400)
        scroll.setWidget(self.preview_label)

        layout.addWidget(scroll, 1)

        panel.setLayout(layout)
        return panel

    def set_preview_image(self, pil_image):
        """Set the preview image from a PIL Image."""
        if pil_image is None:
            self.preview_label.setText("Impossible de générer l'aperçu")
            self.preview_label.setPixmap(QPixmap())
            return

        # Convert PIL to QPixmap
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Scale down for preview (A4 at 300 DPI is large)
        max_height = 800
        if pil_image.height > max_height:
            ratio = max_height / pil_image.height
            new_size = (int(pil_image.width * ratio), max_height)
            pil_image = pil_image.resize(new_size)

        image_bytes = pil_image.tobytes()
        qimage = QImage(
            image_bytes,
            pil_image.width,
            pil_image.height,
            pil_image.width * 3,
            QImage.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(qimage)
        self.preview_label.setPixmap(pixmap)
        self.preview_label.setText("")
        self._preview_image = pil_image

    def clear_preview(self):
        """Clear the preview."""
        self.preview_label.setText("Chargez un fichier NIST pour voir l'aperçu")
        self.preview_label.setPixmap(QPixmap())
        self._preview_image = None

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
