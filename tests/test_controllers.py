"""Test suite for controllers."""

import pytest
from mynist.controllers.file_controller import FileController
from mynist.controllers.export_controller import ExportController

FIXTURE_TRUNC = "tests/fixtures/tronques/Interpol_FABLStemp8865791272998619994.NST-neu.nst"

class TestFileController:
    """Tests for FileController class."""

    def test_file_controller_creation(self):
        """Test FileController object creation."""
        controller = FileController()
        assert controller is not None
        assert controller.current_file is None
        assert controller.current_filepath is None

    def test_is_file_open_initial(self):
        """Test is_file_open initial state."""
        controller = FileController()
        assert controller.is_file_open() is False

    def test_get_current_file_none(self):
        """Test get_current_file when no file open."""
        controller = FileController()
        assert controller.get_current_file() is None

    def test_close_file_no_file(self):
        """Test close_file when no file is open."""
        controller = FileController()
        controller.close_file()
        assert controller.current_file is None

    def test_open_nonexistent_file(self):
        """Test opening non-existent file."""
        controller = FileController()
        result = controller.open_file("/nonexistent/file.nist")
        assert result is None
        assert controller.last_error is None

    def test_get_file_summary_no_file(self):
        """Test get_file_summary when no file open."""
        controller = FileController()
        summary = controller.get_file_summary()
        assert summary == "No file open"

    def test_open_truncated_file_sets_error(self):
        """Truncated files should fail without crashing and set an error."""
        controller = FileController()
        result = controller.open_file(FIXTURE_TRUNC)
        assert result is None
        assert controller.last_error
        assert "NIST_TOO_SHORT" in controller.last_error or "tronqué" in controller.format_last_error()


class TestExportController:
    """Tests for ExportController class."""

    def test_export_controller_creation(self):
        """Test ExportController object creation."""
        controller = ExportController()
        assert controller is not None

    def test_validate_export_path_empty(self):
        """Test validate_export_path with empty path."""
        result = ExportController.validate_export_path("")
        assert result is False

    def test_validate_export_path_valid(self):
        """Test validate_export_path with valid path."""
        result = ExportController.validate_export_path("/tmp/test.nist")
        assert result is True

    def test_get_export_info(self):
        """Test get_export_info returns string."""
        info = ExportController.get_export_info()
        assert isinstance(info, str)
        assert "2.215" in info
        assert "2.217" in info
        assert "11707" in info

    def test_export_signa_multiple_no_file(self):
        """Test export_signa_multiple with None file."""
        result = ExportController.export_signa_multiple(None, "/tmp/test.nist")
        assert result is False


# Note: Full integration tests would require actual NIST files
