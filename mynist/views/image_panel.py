"""Image panel - displays fingerprint and biometric images."""

from typing import Optional
from io import BytesIO

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image

from mynist.models.nist_file import NISTFile
from mynist.utils.constants import IMAGE_TYPES
from mynist.utils.image_tools import locate_image_payload, exif_transpose
from mynist.utils.image_codecs import decode_wsq, decode_jpeg2000


class ImagePanel(QWidget):
    """Panel displaying biometric images from NIST records."""

    def __init__(self, parent=None):
        """Initialize ImagePanel."""
        super().__init__(parent)
        self.nist_file: Optional[NISTFile] = None
        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title label
        self.title_label = QLabel("Image biométrique")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)

        # Scroll area for image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #000000; border: 1px solid #333; color: #888;")
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setText("Aucune image à afficher")

        scroll_area.setWidget(self.image_label)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def load_nist_file(self, nist_file: NISTFile):
        """
        Load NIST file.

        Args:
            nist_file: Parsed NISTFile instance
        """
        self.nist_file = nist_file

    def display_record(self, record_type: int, idc: int):
        """
        Display image from a specific record.

        Args:
            record_type: NIST record type
            idc: IDC of the record
        """
        # Update title
        self.title_label.setText(f"Type-{record_type} Image (IDC {idc})")

        # Check if this is an image type
        if record_type not in IMAGE_TYPES:
            self.image_label.setText(f"Type-{record_type} ne contient pas d'image")
            self.image_label.setPixmap(QPixmap())
            return

        if not self.nist_file:
            self.image_label.setText("Aucun fichier NIST chargé")
            self.image_label.setPixmap(QPixmap())
            return

        # Get the record
        key = (record_type, idc)
        if key not in self.nist_file.records:
            self.image_label.setText("Enregistrement introuvable")
            self.image_label.setPixmap(QPixmap())
            return

        record = self.nist_file.records[key]

        # Try to extract and display image
        try:
            image_data = self._extract_image_data(record)

            if image_data:
                self._display_image(image_data)
            else:
                self.image_label.setText("Impossible d'extraire l'image")
                self.image_label.setPixmap(QPixmap())

        except Exception as e:
            self.image_label.setText(f"Erreur d'affichage de l'image: {str(e)}")
            self.image_label.setPixmap(QPixmap())

    def _extract_image_data(self, record) -> Optional[bytes]:
        """
        Extract image data from a NIST record.

        Args:
            record: NIST record object

        Returns:
            Image data as bytes or None
        """
        # Try different attributes that might contain image data
        # For Type-14 and Type-15, image data is in field 999
        image_attrs = ['_999', '_009', 'DATA', 'data', 'image', 'Image', 'BDB']

        for attr in image_attrs:
            try:
                data = getattr(record, attr, None)
                if data and isinstance(data, (bytes, bytearray)):
                    return bytes(data)
            except:
                continue

        # BinaryRecord fallback: value may contain the raster data
        try:
            raw_value = getattr(record, "value", None)
            if raw_value and isinstance(raw_value, (bytes, bytearray)):
                return bytes(raw_value)
        except Exception:
            pass

        return None

    def _display_image(self, image_data: bytes):
        """
        Display image data in the label.

        Args:
            image_data: Raw image bytes
        """
        if len(image_data) < 10:
            self.image_label.setText("Données image trop courtes pour être affichées.")
            return

        # Try to locate an image payload, even if nested in a binary record
        image_data, format_name = locate_image_payload(image_data)

        try:
            # Handle WSQ via imagecodecs
            if format_name == "WSQ":
                pil_image, err = decode_wsq(image_data)
                if pil_image is None:
                    self.image_label.setText(
                        "Format détecté : WSQ (empreinte digitale)\n\n"
                        f"Impossible de décoder l'image.\n{err}\n\n"
                        f"Taille des données : {len(image_data)} octets"
                    )
                    self.image_label.setPixmap(QPixmap())
                    return

            # Handle JPEG2000 via imagecodecs
            elif format_name == "JPEG2000":
                pil_image, err = decode_jpeg2000(image_data)
                if pil_image is None:
                    self.image_label.setText(
                        "Format détecté : JPEG2000\n\n"
                        f"Impossible de décoder l'image.\n{err}\n\n"
                        f"Taille des données : {len(image_data)} octets"
                    )
                    self.image_label.setPixmap(QPixmap())
                    return
            else:
                pil_image = Image.open(BytesIO(image_data))

            pil_image = exif_transpose(pil_image)
            self._set_pixmap_from_pil(pil_image)
            self.image_label.setToolTip(f"{format_name} — {pil_image.width}x{pil_image.height}px")

        except Exception as e:
            self.image_label.setText(
                f"Erreur lors du chargement ({format_name})\n"
                f"Taille des données : {len(image_data)} octets\n"
                f"Détails : {str(e)}"
            )
            self.image_label.setPixmap(QPixmap())

    def _set_pixmap_from_pil(self, pil_image: Image.Image):
        """Convert a PIL image to QPixmap and display it."""
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        image_bytes = pil_image.tobytes()
        qimage = QImage(
            image_bytes,
            pil_image.width,
            pil_image.height,
            pil_image.width * 3,
            QImage.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(qimage)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setText("")

    def clear(self):
        """Clear the image panel."""
        self.image_label.setText("Aucune image à afficher")
        self.image_label.setPixmap(QPixmap())
        self.title_label.setText("Image biométrique")
        self.nist_file = None
