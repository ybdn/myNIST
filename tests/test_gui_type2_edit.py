"""Tests for Type-2 editing workflow (pytest-qt)."""

import os
from pathlib import Path
import tempfile

import pytest

from mynist.views.main_window import MainWindow


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def offscreen(monkeypatch):
    """Force Qt to offscreen to run headless."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")


def _find_row_for_field(table, field_key: str) -> int:
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        if item and item.text() == field_key:
            return row
    return -1


def test_edit_type2_value_and_undo(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    src = FIXTURES / "type4" / "HR_12883247_3190184.nist"
    window.load_nist_file(str(src))

    # Select Type-2 (IDC 0)
    window.on_record_selected(2, 0)
    table = window.data_panel.table_widget
    row = _find_row_for_field(table, "2.030")
    assert row >= 0

    old_value = table.item(row, 1).text()
    new_value = old_value + "_EDIT"

    # Edit cell
    table.item(row, 1).setText(new_value)

    assert window.is_modified is True
    nist_file = window.file_controller.get_current_file()
    assert nist_file is not None
    type2_fields = nist_file.get_type2_fields()
    assert type2_fields.get("2.030") == new_value

    # Export to a temp file and verify persisted
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / "edited.nist"
        assert nist_file.export(str(export_path)) is True
        from mynist.models.nist_file import NISTFile  # local import to avoid circular at top
        reread = NISTFile(str(export_path))
        assert reread.parse() is True
        assert reread.get_type2_fields().get("2.030") == new_value

    # Undo last change
    window.undo_last_change()
    assert window.is_modified is False
    assert window.data_panel.table_widget.item(row, 1).text() == old_value
