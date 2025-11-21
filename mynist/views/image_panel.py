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
        # For Type-14 and Type-15, image data is in field 999
        image_attrs = ['_999', '_009', 'DATA', 'data', 'image', 'Image', 'BDB']

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
        # Check image format
        if len(image_data) < 10:
            self.image_label.setText("Image data too short")
            return

        # Detect format
        format_name = "Unknown"
        if image_data[:2] == b'\xff\xd8':
            format_name = "JPEG"
        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
            format_name = "PNG"
        elif image_data[:2] in [b'BM', b'BA']:
            format_name = "BMP"
        elif image_data[:4] == b'\xff\xa0\xff\xa8':
            format_name = "WSQ"

        try:
            # Handle WSQ format (fingerprint compression)
            if format_name == "WSQ":
                self._display_wsq_image(image_data)
                return

            # Try to load with PIL (handles JPEG, PNG, BMP, etc.)
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
            self.image_label.setText(
                f"Error loading {format_name} image\n\n"
                f"Format detected: {format_name}\n"
                f"Data size: {len(image_data)} bytes\n"
                f"Error: {str(e)}\n\n"
                f"First bytes: {image_data[:20].hex()}"
            )
            self.image_label.setPixmap(QPixmap())

    def _display_wsq_image(self, wsq_data: bytes):
        """
        Display WSQ format image (fingerprint compression).

        Args:
            wsq_data: WSQ encoded image bytes
        """
        # Import WSQ plugin (registers decoder with Pillow)
        try:
            import wsq
        except ImportError:
            self.image_label.setText(
                "Warning: WSQ format detected.\n\n"
                "This is a WSQ-compressed fingerprint image.\n\n"
                "Install the wsq library to view it:\n"
                "   pip install wsq\n\n"
                f"Image size: {len(wsq_data)} bytes\n"
                "Format: WSQ (Wavelet Scalar Quantization)."
            )
            self.image_label.setPixmap(QPixmap())
            return

        try:
            # Pillow will use the wsq plugin registered on import
            pil_image = Image.open(BytesIO(wsq_data))
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

        except Exception as e:
            self.image_label.setText(
                "Warning: WSQ decoding failed.\n\n"
                f"Error: {str(e)}\n"
                f"Image size: {len(wsq_data)} bytes"
            )
            self.image_label.setPixmap(QPixmap())

    def clear(self):
        """Clear the image panel."""
        self.image_label.setText("No image to display")
        self.image_label.setPixmap(QPixmap())
        self.title_label.setText("Biometric Image")
        self.nist_file = None
