"""Data panel - displays NIST record field data."""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                              QLabel, QHeaderView)
from PyQt5.QtCore import Qt
from typing import Optional, Dict, Any
from mynist.models.nist_file import NISTFile


class DataPanel(QWidget):
    """Panel displaying NIST record field data."""

    def __init__(self, parent=None):
        """Initialize DataPanel."""
        super().__init__(parent)
        self.nist_file: Optional[NISTFile] = None
        self.current_record_type: Optional[int] = None
        self.current_idc: Optional[int] = None
        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title label
        self.title_label = QLabel("Record Fields")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)

        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Field", "Value"])

        # Configure table
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)

        # Set column widths
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.table_widget)

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
        Display fields of a specific record.

        Args:
            record_type: NIST record type
            idc: IDC of the record
        """
        self.current_record_type = record_type
        self.current_idc = idc

        # Update title
        self.title_label.setText(f"Type-{record_type} Record (IDC {idc}) - Fields")

        # Clear table
        self.table_widget.setRowCount(0)

        if not self.nist_file:
            return

        # Get the record
        key = (record_type, idc)
        if key not in self.nist_file.records:
            self.table_widget.setRowCount(1)
            self.table_widget.setItem(0, 0, QTableWidgetItem("Error"))
            self.table_widget.setItem(0, 1, QTableWidgetItem("Record not found"))
            return

        record = self.nist_file.records[key]

        # Extract fields from record
        fields = self._extract_fields(record, record_type)

        # Populate table
        self.table_widget.setRowCount(len(fields))
        for row, (field_name, field_value) in enumerate(sorted(fields.items())):
            # Field name
            field_item = QTableWidgetItem(field_name)
            field_item.setFlags(field_item.flags() & ~Qt.ItemIsEditable)

            # Field value
            value_str = str(field_value) if field_value is not None else ""
            value_item = QTableWidgetItem(value_str)
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)

            self.table_widget.setItem(row, 0, field_item)
            self.table_widget.setItem(row, 1, value_item)

    def _extract_fields(self, record: Any, record_type: int) -> Dict[str, Any]:
        """
        Extract all fields from a record.

        Args:
            record: NIST record object
            record_type: Record type number

        Returns:
            Dictionary mapping field names to values
        """
        fields = {}

        # Try to extract fields 1-999
        for field_num in range(1, 1000):
            try:
                attr_name = f'_{field_num:03d}'
                value = getattr(record, attr_name, None)

                if value is not None and value != '':
                    field_key = f'{record_type}.{field_num:03d}'
                    fields[field_key] = value
            except:
                continue

        # If no fields found, try to get all attributes
        if not fields:
            for attr_name in dir(record):
                if not attr_name.startswith('_') and not callable(getattr(record, attr_name)):
                    try:
                        value = getattr(record, attr_name)
                        if value is not None and value != '':
                            fields[attr_name] = value
                    except:
                        continue

        return fields

    def clear(self):
        """Clear the data panel."""
        self.table_widget.setRowCount(0)
        self.title_label.setText("Record Fields")
        self.nist_file = None
        self.current_record_type = None
        self.current_idc = None
