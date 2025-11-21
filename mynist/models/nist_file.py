"""NIST file model for parsing and manipulating ANSI/NIST-ITL files."""

import nistitl
from typing import Dict, List, Optional, Tuple, Any


class NISTFile:
    """Represents a parsed NIST file with methods to access and modify records."""

    def __init__(self, filepath: Optional[str] = None):
        """
        Initialize NISTFile.

        Args:
            filepath: Path to NIST file to parse (optional)
        """
        self.filepath = filepath
        self.message: Optional[nistitl.Message] = None
        self.records: Dict[Tuple[int, int], Any] = {}
        self.is_parsed = False

    def parse(self, filepath: Optional[str] = None) -> bool:
        """
        Parse NIST file.

        Args:
            filepath: Path to NIST file (uses self.filepath if not provided)

        Returns:
            True if parsing succeeded, False otherwise
        """
        if filepath:
            self.filepath = filepath

        if not self.filepath:
            raise ValueError("No filepath provided")

        try:
            self.message = nistitl.Message()
            with open(self.filepath, 'rb') as f:
                self.message.parse(f.read())

            # Extract all records
            self._extract_records()
            self.is_parsed = True
            return True

        except Exception as e:
            print(f"Error parsing NIST file: {e}")
            self.is_parsed = False
            return False

    def _extract_records(self):
        """Extract all records from parsed message."""
        self.records.clear()

        # Iterate through all possible record types (1-99)
        for record_type in range(1, 100):
            try:
                for idx, record in enumerate(self.message.iter(record_type)):
                    # Use IDC if available, otherwise use index
                    idc = getattr(record, 'IDC', idx)
                    key = (record_type, idc)
                    self.records[key] = record
            except:
                continue

    def get_record_types(self) -> List[int]:
        """
        Get list of record types present in the file.

        Returns:
            List of record type numbers
        """
        types = set()
        for record_type, _ in self.records.keys():
            types.add(record_type)
        return sorted(list(types))

    def get_records_by_type(self, record_type: int) -> List[Tuple[int, Any]]:
        """
        Get all records of a specific type.

        Args:
            record_type: NIST record type number

        Returns:
            List of tuples (IDC, record)
        """
        records = []
        for (rtype, idc), record in self.records.items():
            if rtype == record_type:
                records.append((idc, record))
        return sorted(records, key=lambda x: x[0])

    def get_type2_fields(self) -> Dict[str, Any]:
        """
        Extract all fields from Type-2 record.

        Returns:
            Dictionary mapping field numbers to values (e.g., '2.001': 'value')
        """
        type2_records = self.get_records_by_type(2)
        if not type2_records:
            return {}

        # Use first Type-2 record
        _, record = type2_records[0]
        fields = {}

        # Try to extract fields 1-999
        for field_num in range(1, 1000):
            try:
                # nistitl uses underscore notation: _001, _002, etc.
                attr_name = f'_{field_num:03d}'
                value = getattr(record, attr_name, None)

                if value is not None and value != '':
                    field_key = f'2.{field_num:03d}'
                    fields[field_key] = value
            except:
                continue

        return fields

    def get_fingerprint_records(self) -> List[Tuple[int, int, Any]]:
        """
        Get all fingerprint-related records.

        Fingerprint types in ANSI/NIST-ITL:
        - Type 4: High-resolution grayscale fingerprint
        - Type 13: Variable-resolution latent
        - Type 14: Variable-resolution fingerprint
        - Type 15: Variable-resolution palmprint

        Returns:
            List of tuples (record_type, IDC, record)
        """
        fingerprint_types = [4, 13, 14, 15]
        fingerprint_records = []

        for fp_type in fingerprint_types:
            records = self.get_records_by_type(fp_type)
            for idc, record in records:
                fingerprint_records.append((fp_type, idc, record))

        return fingerprint_records

    def export(self, output_path: str) -> bool:
        """
        Export current NIST message to file.

        Args:
            output_path: Path to save the NIST file

        Returns:
            True if export succeeded, False otherwise
        """
        if not self.message:
            print("No NIST message to export")
            return False

        try:
            nist_data = self.message.NIST
            with open(output_path, 'wb') as f:
                f.write(nist_data)
            return True
        except Exception as e:
            print(f"Error exporting NIST file: {e}")
            return False

    def modify_field(self, record_type: int, field_num: int, value: Any, idc: int = 0) -> bool:
        """
        Modify a field in a specific record.

        Args:
            record_type: Type of record to modify
            field_num: Field number to modify
            value: New value for the field
            idc: IDC of the record (default 0)

        Returns:
            True if modification succeeded, False otherwise
        """
        key = (record_type, idc)
        if key not in self.records:
            print(f"Record ({record_type}, {idc}) not found")
            return False

        try:
            record = self.records[key]
            attr_name = f'_{field_num:03d}'
            setattr(record, attr_name, value)
            return True
        except Exception as e:
            print(f"Error modifying field {record_type}.{field_num:03d}: {e}")
            return False

    def delete_field(self, record_type: int, field_num: int, idc: int = 0) -> bool:
        """
        Delete a field from a specific record.

        Args:
            record_type: Type of record
            field_num: Field number to delete
            idc: IDC of the record (default 0)

        Returns:
            True if deletion succeeded, False otherwise
        """
        key = (record_type, idc)
        if key not in self.records:
            print(f"Record ({record_type}, {idc}) not found")
            return False

        try:
            record = self.records[key]
            attr_name = f'_{field_num:03d}'

            # Remove matching fields directly from the internal list to avoid getattr/hasattr
            try:
                original_len = len(record._fields)  # _fields is part of __slots__
                record._fields = [f for f in record._fields if getattr(f, "tag", None) != field_num]
                if len(record._fields) < original_len:
                    return True  # Field removed
            except Exception as inner_e:
                print(f"Error pruning field list for {record_type}.{field_num:03d}: {inner_e}")
                return False

            # If nothing was removed, the field was likely already absent; ensure no stray attr
            try:
                delattr(record, attr_name)
            except Exception:
                pass
            return True

        except Exception as e:
            print(f"Error deleting field {record_type}.{field_num:03d}: {e}")
            return False

    def get_summary(self) -> str:
        """
        Get a text summary of the NIST file.

        Returns:
            Human-readable summary string
        """
        if not self.is_parsed:
            return "NIST file not parsed"

        summary_lines = [
            f"NIST File: {self.filepath}",
            f"Total Records: {len(self.records)}",
            "Record Types Present:"
        ]

        for record_type in self.get_record_types():
            count = len(self.get_records_by_type(record_type))
            summary_lines.append(f"  - Type {record_type}: {count} record(s)")

        return "\n".join(summary_lines)
