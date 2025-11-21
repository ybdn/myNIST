"""Image panel - displays fingerprint and biometric images."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from typing import Optional
from io import BytesIO
from PIL import Image
from mynist.models.nist_file import NISTFile
from mynist.utils.constants import IMAGE_TYPES


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
        self.title_label = QLabel("Biometric Image")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)

        # Scroll area for image
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setText("No image to display")

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
            self.image_label.setText(f"Type-{record_type} does not contain images")
            self.image_label.setPixmap(QPixmap())
            return

        if not self.nist_file:
            self.image_label.setText("No NIST file loaded")
            self.image_label.setPixmap(QPixmap())
            return

        # Get the record
        key = (record_type, idc)
        if key not in self.nist_file.records:
            self.image_label.setText("Record not found")
            self.image_label.setPixmap(QPixmap())
            return

        record = self.nist_file.records[key]

        # Try to extract and display image
        try:
            image_data = self._extract_image_data(record)

            if image_data:
                self._display_image(image_data)
            else:
                self.image_label.setText("Unable to extract image data")
                self.image_label.setPixmap(QPixmap())

        except Exception as e:
            self.image_label.setText(f"Error displaying image: {str(e)}")
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
        image_attrs = ['DATA', 'data', '_999', 'image', 'Image']

        for attr in image_attrs:
            try:
                data = getattr(record, attr, None)
                if data and isinstance(data, (bytes, bytearray)):
                    return bytes(data)
            except:
                continue

        return None

    def _display_image(self, image_data: bytes):
        """
        Display image data in the label.

        Args:
            image_data: Raw image bytes
        """
        try:
            # Try to load with PIL first (handles many formats)
            pil_image = Image.open(BytesIO(image_data))

            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convert PIL Image to QPixmap
            image_bytes = pil_image.tobytes()
            qimage = QImage(
                image_bytes,
                pil_image.width,
                pil_image.height,
                pil_image.width * 3,
                QImage.Format_RGB888
            )

            pixmap = QPixmap.fromImage(qimage)

            # Scale image to fit panel while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")  # Clear text

        except Exception as e:
            self.image_label.setText(f"Error loading image: {str(e)}")
            self.image_label.setPixmap(QPixmap())

    def clear(self):
        """Clear the image panel."""
        self.image_label.setText("No image to display")
        self.image_label.setPixmap(QPixmap())
        self.title_label.setText("Biometric Image")
        self.nist_file = None
