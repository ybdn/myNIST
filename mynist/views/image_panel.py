"""Image panel - displays fingerprint and biometric images."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from io import BytesIO

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
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

            self._set_pixmap_from_pil(pil_image)

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
        wsq_errors = []
        pil_image: Optional[Image.Image] = None

        # Fallback first: NBIS dwsq (safer than crashing the process)
        try:
            pil_image = self._decode_wsq_with_dwsq(wsq_data)
        except Exception as e:
            wsq_errors.append(f"dwsq fallback failed: {str(e)}")

        # Primary path when NBIS is unavailable: Pillow plugin (wsq module)
        if pil_image is None:
            try:
                import wsq  # noqa: F401  - registers the Pillow plugin
                pil_image = Image.open(BytesIO(wsq_data))
            except ImportError:
                wsq_errors.append("Python module 'wsq' not installed.")
            except Exception as e:
                wsq_errors.append(f"Pillow WSQ decode failed: {str(e)}")

        if pil_image:
            self._set_pixmap_from_pil(pil_image)
            return

        # Nothing worked: show a clear, actionable message
        extra = "\n- ".join(wsq_errors) if wsq_errors else "No decoder available."
        self.image_label.setText(
            "Warning: WSQ format detected.\n\n"
            "This is a WSQ-compressed fingerprint image.\n\n"
            "Install the wsq library (pip install wsq) or ensure the NBIS "
            "`dwsq` binary is available to view it.\n\n"
            f"Image size: {len(wsq_data)} bytes\n"
            f"Format: WSQ (Wavelet Scalar Quantization)\n\n"
            f"Details:\n- {extra}"
        )
        self.image_label.setPixmap(QPixmap())

    def _decode_wsq_with_dwsq(self, wsq_data: bytes) -> Optional[Image.Image]:
        """
        Decode WSQ data using the NBIS `dwsq` CLI when the Python plugin is unavailable.

        Args:
            wsq_data: WSQ encoded image bytes

        Returns:
            PIL Image if decoding succeeded, otherwise None.
        """
        dwsq_path = shutil.which("dwsq")
        if not dwsq_path:
            return None

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir)
            wsq_file = tmp_dir / "image.wsq"
            wsq_file.write_bytes(wsq_data)

            result = subprocess.run(
                [dwsq_path, "raw", str(wsq_file), "-raw_out"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            if result.returncode != 0:
                stderr = result.stderr.decode(errors="ignore").strip()
                raise RuntimeError(stderr or "dwsq command failed")

            raw_file = wsq_file.with_suffix(".raw")
            ncm_file = wsq_file.with_suffix(".ncm")

            if not raw_file.exists() or not ncm_file.exists():
                raise FileNotFoundError("dwsq output files not found")

            metadata = self._parse_ncm_metadata(ncm_file.read_text())
            width = int(metadata.get("PIX_WIDTH", 0))
            height = int(metadata.get("PIX_HEIGHT", 0))
            depth = int(metadata.get("PIX_DEPTH", 8))

            if not width or not height:
                raise ValueError("Invalid WSQ metadata (missing dimensions)")

            raw_bytes = raw_file.read_bytes()
            mode = "L" if depth <= 8 else "RGB"
            return Image.frombytes(mode, (width, height), raw_bytes)

    def _parse_ncm_metadata(self, content: str) -> dict:
        """Parse NBIS .ncm metadata (key value per line)."""
        metadata = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or " " not in line:
                continue
            key, value = line.split(None, 1)
            metadata[key] = value
        return metadata

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
        self.image_label.setText("No image to display")
        self.image_label.setPixmap(QPixmap())
        self.title_label.setText("Biometric Image")
        self.nist_file = None
