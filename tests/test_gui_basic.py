"""Smoke tests for MainWindow using pytest-qt and fixtures."""

import os
from pathlib import Path

import pytest

from mynist.views.main_window import MainWindow


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def offscreen(monkeypatch):
    """Force Qt to use offscreen platform to avoid GUI requirements."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")


def test_load_type10_png_displays_pixmap(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    src = FIXTURES / "type10" / "Interpol_FRA_24000000448327A_FI.nist"
    window.load_nist_file(str(src))

    # Select Type-10 record IDC 0
    window.on_record_selected(10, 0)
    pix = window.image_panel.image_label.pixmap()
    assert pix is not None and not pix.isNull()


def test_tree_contains_expected_types_for_palm(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    src = FIXTURES / "palm15" / "109018515_export_test.nist"
    window.load_nist_file(str(src))

    tree = window.file_panel.tree_widget
    top_labels = [tree.topLevelItem(i).text(0) for i in range(tree.topLevelItemCount())]
    assert any("Type-14" in label for label in top_labels)
    assert any("Type-15" in label for label in top_labels)


def test_selects_record_updates_data_panel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    src = FIXTURES / "type4" / "HR_12883247_3190184.nist"
    window.load_nist_file(str(src))

    # Select Type-4, IDC first
    window.on_record_selected(4, 0)
    assert "Type-4" in window.data_panel.title_label.text()
    assert window.data_panel.table_widget.rowCount() > 0
