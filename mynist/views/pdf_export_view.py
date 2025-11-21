"""Vue dédiée à l'export PDF décadactylaire."""

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QHBoxLayout,
    QTextEdit,
)


class PdfExportView(QWidget):
    """Vue simple pour paramétrer et lancer l'export PDF."""

    browse_requested = pyqtSignal()
    export_requested = pyqtSignal(str)
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: Optional[str] = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.title = QLabel("<h2>Export relevé PDF</h2>")
        layout.addWidget(self.title)

        self.current_label = QLabel("Aucun fichier NIST chargé.")
        layout.addWidget(self.current_label)

        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Chemin de sortie PDF (.pdf)")
        layout.addWidget(self.output_input)

        buttons = QHBoxLayout()
        self.browse_btn = QPushButton("Choisir…")
        self.browse_btn.clicked.connect(self.browse_requested.emit)
        buttons.addWidget(self.browse_btn)

        self.export_btn = QPushButton("Exporter le PDF")
        self.export_btn.clicked.connect(lambda: self.export_requested.emit(self.output_input.text().strip()))
        buttons.addWidget(self.export_btn)

        self.back_btn = QPushButton("Retour au hub")
        self.back_btn.clicked.connect(self.back_requested.emit)
        buttons.addWidget(self.back_btn)

        buttons.addStretch()
        layout.addLayout(buttons)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMinimumHeight(180)
        help_text.setHtml(
            "<b>Organisation :</b><br>"
            "- Main gauche : Pouce, Index, Majeur, Annulaire, Auriculaire.<br>"
            "- Main droite : Pouce, Index, Majeur, Annulaire, Auriculaire.<br>"
            "- Simultané : main gauche, pouces, main droite.<br>"
            "- Paumes : gauche, droite.<br><br>"
            "<b>Formats :</b> WSQ/JPEG/PNG/JPEG2000 pris en charge via <code>imagecodecs</code>. "
            "Installez <code>pip install imagecodecs</code> pour décoder WSQ/JPEG2000."
        )
        layout.addWidget(help_text)

        layout.addStretch()
        self.setLayout(layout)

    def set_current_file(self, path: Optional[str]):
        self.current_file = path
        if path:
            self.current_label.setText(f"Fichier en cours : {Path(path).name}")
            # suggestion output
            suggested = str(Path(path).with_suffix(".pdf"))
            self.output_input.setText(suggested)
        else:
            self.current_label.setText("Aucun fichier NIST chargé.")
            self.output_input.clear()
