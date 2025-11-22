"""File panel - displays NIST record tree structure."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
from PyQt5.QtCore import pyqtSignal
from typing import Optional
from mynist.models.nist_file import NISTFile
from mynist.utils.constants import RECORD_TYPE_NAMES
from mynist.utils.biometric_labels import describe_biometric_record


class FilePanel(QWidget):
    """Panel displaying NIST file record tree."""

    # Signal emitted when user selects a record
    record_selected = pyqtSignal(int, int)  # (record_type, idc)

    def __init__(self, parent=None):
        """Initialize FilePanel."""
        super().__init__(parent)
        self.nist_file: Optional[NISTFile] = None
        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title label
        self.title_label = QLabel("Enregistrements NIST")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)

        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Structure des enregistrements")
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        # Improve readability with more spacing between items
        self.tree_widget.setStyleSheet("""
            QTreeWidget::item {
                padding: 6px 4px;
                margin: 2px 0;
            }
            QTreeWidget::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        self.tree_widget.setIndentation(24)
        layout.addWidget(self.tree_widget)

        self.setLayout(layout)

    def load_nist_file(self, nist_file: NISTFile):
        """
        Load NIST file and populate tree.

        Args:
            nist_file: Parsed NISTFile instance
        """
        self.nist_file = nist_file
        self.populate_tree()

    def populate_tree(self):
        """Populate tree widget with NIST records."""
        self.tree_widget.clear()

        if not self.nist_file or not self.nist_file.is_parsed:
            return

        # Get all record types
        record_types = self.nist_file.get_record_types()

        for record_type in record_types:
            # Create parent item for record type
            type_name = RECORD_TYPE_NAMES.get(record_type, f"Type-{record_type}: Unknown")
            type_item = QTreeWidgetItem([type_name])

            # Get all records of this type
            records = self.nist_file.get_records_by_type(record_type)

            # Add child items for each record
            for idc, record in records:
                descriptor = describe_biometric_record(record_type, record)
                label = f"IDC {idc}"
                if descriptor:
                    label = f"IDC {idc} — {descriptor}"
                child_item = QTreeWidgetItem([label])
                if descriptor:
                    child_item.setToolTip(0, descriptor)

                # Store record info in item data
                child_item.setData(0, 100, record_type)  # Store type
                child_item.setData(0, 101, idc)  # Store IDC

                type_item.addChild(child_item)

            # Expand Type-2 by default (most important for user)
            if record_type == 2:
                type_item.setExpanded(True)

            self.tree_widget.addTopLevelItem(type_item)

        # Expand all top-level items
        self.tree_widget.expandAll()

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Handle tree item click.

        Args:
            item: Clicked tree item
            column: Column index
        """
        # Get record type and IDC from item data
        record_type = item.data(0, 100)
        idc = item.data(0, 101)

        if record_type is not None and idc is not None:
            # Emit signal with record info
            self.record_selected.emit(record_type, idc)

    def clear(self):
        """Clear the tree widget."""
        self.tree_widget.clear()
        self.nist_file = None
