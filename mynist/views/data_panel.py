"""Data panel - displays NIST record field data."""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QMessageBox,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Optional, Dict, Any, List
from mynist.models.nist_file import NISTFile


class DataPanel(QWidget):
    """Panel displaying NIST record field data."""

    field_changed = pyqtSignal(int, int, str, str, str)

    def __init__(self, parent=None):
        """Initialize DataPanel."""
        super().__init__(parent)
        self.nist_file: Optional[NISTFile] = None
        self.current_record_type: Optional[int] = None
        self.current_idc: Optional[int] = None
        self._row_fields: List[str] = []
        self._field_cache: Dict[str, str] = {}
        self._loading = False
        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()

        # Title label
        self.title_label = QLabel("Champs de l'enregistrement")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.title_label)

        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Champ", "Valeur"])

        # Configure table
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.cellChanged.connect(self._on_cell_changed)

        # Set column widths
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.table_widget)

        # Formulaire ajout/suppression Type-2
        form = QHBoxLayout()
        form.addWidget(QLabel("Ajouter/Supprimer (Type-2) :"))

        self.field_num_input = QLineEdit()
        self.field_num_input.setPlaceholderText("Numéro (ex: 030)")
        self.field_num_input.setFixedWidth(120)
        form.addWidget(self.field_num_input)

        self.field_value_input = QLineEdit()
        self.field_value_input.setPlaceholderText("Valeur")
        form.addWidget(self.field_value_input)

        self.add_btn = QPushButton("Ajouter")
        self.add_btn.clicked.connect(self._on_add_field)
        form.addWidget(self.add_btn)

        self.del_btn = QPushButton("Supprimer")
        self.del_btn.clicked.connect(self._on_delete_field)
        form.addWidget(self.del_btn)

        form.addStretch()
        layout.addLayout(form)

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
        self.title_label.setText(f"Enregistrement Type-{record_type} (IDC {idc}) - Champs")

        # Clear table
        self.table_widget.setRowCount(0)
        self._row_fields = []
        self._field_cache = {}

        if not self.nist_file:
            return

        # Get the record
        key = (record_type, idc)
        if key not in self.nist_file.records:
            self.table_widget.setRowCount(1)
            self.table_widget.setItem(0, 0, QTableWidgetItem("Erreur"))
            self.table_widget.setItem(0, 1, QTableWidgetItem("Enregistrement introuvable"))
            return

        record = self.nist_file.records[key]

        # Extract fields from record
        fields = self._extract_fields(record, record_type)
        summary = self._extract_summary(record, record_type)
        if summary:
            self.title_label.setText(f"Type-{record_type} Record (IDC {idc}) - {summary}")

        self._field_cache = {k: str(v) for k, v in fields.items()}
        sorted_items = sorted(fields.items())
        self.table_widget.setRowCount(len(sorted_items))
        self._loading = True
        for row, (field_name, field_value) in enumerate(sorted_items):
            self._row_fields.append(field_name)
            # Field name
            field_item = QTableWidgetItem(field_name)
            field_item.setFlags(field_item.flags() & ~Qt.ItemIsEditable)

            # Field value
            value_str = str(field_value) if field_value is not None else ""
            value_item = QTableWidgetItem(value_str)
            if record_type != 2:
                value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)

            self.table_widget.setItem(row, 0, field_item)
            self.table_widget.setItem(row, 1, value_item)
        self._loading = False

        if record_type == 2:
            self.table_widget.setEditTriggers(
                QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.EditKeyPressed
            )
        else:
            self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

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

    def _safe_get_first(self, record: Any, candidates: List[str]) -> Optional[Any]:
        """Return first non-empty attribute value among candidates."""
        for name in candidates:
            try:
                value = getattr(record, name, None)
                if value not in (None, ""):
                    return value
            except Exception:
                continue
        return None

    def _extract_summary(self, record: Any, record_type: int) -> str:
        """Build a short summary for Type-1/2 to surface key metadata."""
        if record_type not in (1, 2):
            return ""

        summary_parts = []
        tcn = self._safe_get_first(record, ["TCN", "_009", "_005", "_007"])
        ori = self._safe_get_first(record, ["ORI", "_008", "_007"])
        tot = self._safe_get_first(record, ["TOT", "_004"])

        if tot:
            summary_parts.append(f"TOT: {tot}")
        if ori:
            summary_parts.append(f"ORI: {ori}")
        if tcn:
            summary_parts.append(f"TCN: {tcn}")

        return " · ".join(summary_parts)

    def clear(self):
        """Clear the data panel."""
        self.table_widget.setRowCount(0)
        self.title_label.setText("Champs de l'enregistrement")
        self.nist_file = None
        self.current_record_type = None
        self.current_idc = None
        self._row_fields = []
        self._field_cache = {}

    def _on_cell_changed(self, row: int, column: int):
        """Handle edits in value column for Type-2."""
        if self._loading:
            return
        if self.current_record_type != 2 or column != 1:
            return
        if not self.nist_file or not self._row_fields:
            return

        field_key = self._row_fields[row]
        old_value = self._field_cache.get(field_key, "")
        item = self.table_widget.item(row, column)
        if not item:
            return
        new_value = item.text()

        if new_value == old_value:
            return

        valid, error_msg = self._validate_field(field_key, new_value, old_value)
        if not valid:
            self._loading = True
            item.setText(old_value)
            self._loading = False
            QMessageBox.warning(
                self,
                "Valeur invalide",
                error_msg or "Format invalide pour ce champ."
            )
            return

        record_type = self.current_record_type or 2
        idc = self.current_idc or 0
        field_num = int(field_key.split(".")[1])

        if new_value == "":
            success = self.nist_file.delete_field(record_type, field_num, idc=idc)
        else:
            success = self.nist_file.modify_field(record_type, field_num, new_value, idc=idc)

        if not success:
            QMessageBox.critical(self, "Erreur", "Impossible d'appliquer la modification.")
            self._loading = True
            item.setText(old_value)
            self._loading = False
            return

        self._field_cache[field_key] = new_value
        self.field_changed.emit(record_type, idc, field_key, old_value, new_value)

    def _validate_field(self, field_key: str, value: str, old_value: str) -> (bool, str):
        """Basic validation based on previous value patterns."""
        if value == "":
            return True, ""

        if len(old_value) == 8 and old_value.isdigit():
            if not (value.isdigit() and len(value) == 8):
                return False, "Ce champ attend une date au format YYYYMMDD (8 chiffres)."

        if old_value.isdigit() and not value.isdigit():
            return False, "Ce champ attend uniquement des chiffres."

        return True, ""

    def _on_add_field(self):
        """Add a new field to Type-2."""
        if self.current_record_type != 2 or not self.nist_file:
            QMessageBox.information(self, "Type-2 requis", "Sélectionnez un Type-2 pour ajouter un champ.")
            return

        num_text = self.field_num_input.text().strip()
        value_text = self.field_value_input.text().strip()

        if not num_text.isdigit():
            QMessageBox.warning(self, "Numéro invalide", "Le numéro de champ doit être numérique (1-999).")
            return
        field_num = int(num_text)
        if field_num < 1 or field_num > 999:
            QMessageBox.warning(self, "Numéro invalide", "Le numéro de champ doit être compris entre 1 et 999.")
            return

        field_key = f"2.{field_num:03d}"
        old_value = self._field_cache.get(field_key, "")

        success = self.nist_file.modify_field(2, field_num, value_text, idc=self.current_idc or 0)
        if not success:
            QMessageBox.critical(self, "Erreur", "Impossible d'ajouter/modifier le champ.")
            return

        # Refresh view
        if self.current_record_type == 2 and self.current_idc is not None:
            self.display_record(2, self.current_idc)

        self.field_changed.emit(2, self.current_idc or 0, field_key, old_value, value_text)

    def _on_delete_field(self):
        """Delete selected field in Type-2."""
        if self.current_record_type != 2 or not self.nist_file:
            QMessageBox.information(self, "Type-2 requis", "Sélectionnez un Type-2 pour supprimer un champ.")
            return

        selected = self.table_widget.currentRow()
        if selected < 0 or selected >= len(self._row_fields):
            QMessageBox.information(self, "Sélection requise", "Choisissez un champ à supprimer dans la liste.")
            return

        field_key = self._row_fields[selected]
        if not field_key.startswith("2."):
            QMessageBox.warning(self, "Champ non supporté", "Seuls les champs Type-2 peuvent être supprimés ici.")
            return

        old_value = self._field_cache.get(field_key, "")
        choice = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer le champ {field_key} ?\nValeur : {old_value}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if choice != QMessageBox.Yes:
            return

        field_num = int(field_key.split(".")[1])
        success = self.nist_file.delete_field(2, field_num, idc=self.current_idc or 0)
        if not success:
            QMessageBox.critical(self, "Erreur", "Impossible de supprimer le champ.")
            return

        # Refresh view
        if self.current_record_type == 2 and self.current_idc is not None:
            self.display_record(2, self.current_idc)

        self.field_changed.emit(2, self.current_idc or 0, field_key, old_value, "")
