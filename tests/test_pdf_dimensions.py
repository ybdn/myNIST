"""Tests dimensionnels sur les PDFs générés (gabarit A4, 1 page)."""

import tempfile
from pathlib import Path

import PyPDF2

from mynist.controllers.pdf_controller import PDFController
from mynist.models.nist_file import NISTFile


FIXTURES = [
    Path("tests/fixtures/palm15/109018515_export_test.nist"),
    Path("tests/fixtures/signa/102556281_export_test.nist"),
]


def test_generated_pdf_has_one_page_and_a4_size():
    controller = PDFController()
    for fixture in FIXTURES:
        nist = NISTFile(str(fixture))
        assert nist.parse() is True

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / f"{fixture.stem}.pdf"
            ok, msg = controller.export_dacty_pdf(nist, str(out))
            assert ok, msg
            assert out.exists() and out.stat().st_size > 0

            reader = PyPDF2.PdfReader(str(out))
            assert len(reader.pages) == 1
            page = reader.pages[0]
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            # A4 PDF standard ~ 595x842 points ; tolérance :
            assert 500 < width < 700
            assert 750 < height < 900
