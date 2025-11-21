"""Tests pour l'export PDF décadactylaire."""

from pathlib import Path
import tempfile

from mynist.controllers.pdf_controller import PDFController
from mynist.models.nist_file import NISTFile


FIXTURE = Path(__file__).parent / "fixtures" / "palm15" / "109018515_export_test.nist"


def test_pdf_export_creates_file():
    controller = PDFController()
    nist = NISTFile(str(FIXTURE))
    assert nist.parse() is True

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "export.pdf"
        ok, message = controller.export_dacty_pdf(nist, str(out))
        assert ok, message
        assert out.exists()
        assert out.stat().st_size > 0
