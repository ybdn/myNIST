"""Test suite for NIST file model."""

import pytest
from mynist.models.nist_file import NISTFile


class TestNISTFile:
    """Tests for NISTFile class."""

    def test_nist_file_creation(self):
        """Test NISTFile object creation."""
        nist_file = NISTFile()
        assert nist_file is not None
        assert nist_file.filepath is None
        assert nist_file.is_parsed is False

    def test_nist_file_with_filepath(self):
        """Test NISTFile creation with filepath."""
        filepath = "/path/to/test.nist"
        nist_file = NISTFile(filepath)
        assert nist_file.filepath == filepath
        assert nist_file.is_parsed is False

    def test_get_record_types_empty(self):
        """Test get_record_types with no records."""
        nist_file = NISTFile()
        types = nist_file.get_record_types()
        assert types == []

    def test_get_records_by_type_empty(self):
        """Test get_records_by_type with no records."""
        nist_file = NISTFile()
        records = nist_file.get_records_by_type(2)
        assert records == []

    def test_is_parsed_initial_state(self):
        """Test is_parsed flag initial state."""
        nist_file = NISTFile()
        assert nist_file.is_parsed is False

    def test_get_summary_not_parsed(self):
        """Test get_summary when file not parsed."""
        nist_file = NISTFile()
        summary = nist_file.get_summary()
        assert summary == "NIST file not parsed"


class TestNISTFileExport:
    """Tests for NIST file export functionality."""

    def test_export_no_message(self):
        """Test export with no message loaded."""
        nist_file = NISTFile()
        result = nist_file.export("/tmp/test.nist")
        assert result is False

    def test_modify_field_no_record(self):
        """Test modify_field with non-existent record."""
        nist_file = NISTFile()
        result = nist_file.modify_field(2, 215, "test")
        assert result is False

    def test_delete_field_no_record(self):
        """Test delete_field with non-existent record."""
        nist_file = NISTFile()
        result = nist_file.delete_field(2, 215)
        assert result is False


# Note: Integration tests with actual NIST files would require sample files
# and should be placed in a separate test_integration.py file
