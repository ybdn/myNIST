"""Export controller for NIST file modifications."""

from typing import Optional
from mynist.models.nist_file import NISTFile
from mynist.utils.constants import SIGNA_MULTIPLE_RULES
from mynist.utils.logger import get_logger

logger = get_logger(__name__)


class ExportController:
    """Handles export operations with modifications."""

    @staticmethod
    def export_signa_multiple(nist_file: NISTFile, output_path: str) -> bool:
        """
        Export NIST file with "Signa Multiple" modifications.

        Applies fixed rules:
        - Delete field 2.215
        - Replace field 2.217 with "11707"

        Args:
            nist_file: Source NIST file
            output_path: Path to save modified file

        Returns:
            True if export succeeded, False otherwise
        """
        if not nist_file or not nist_file.is_parsed:
            logger.error("NIST file not parsed")
            return False

        try:
            logger.info("Starting Export Signa Multiple...")

            # Get Type-2 records
            type2_records = nist_file.get_records_by_type(2)
            if not type2_records:
                logger.warning("No Type-2 record found. Exporting without modifications.")
                return nist_file.export(output_path)

            # Get IDC of first Type-2 record
            idc, _ = type2_records[0]

            # Apply modifications
            modifications_applied = []

            # Delete field 2.215
            for field_num in SIGNA_MULTIPLE_RULES['delete_fields']:
                logger.info(f"Deleting field 2.{field_num:03d}")
                if nist_file.delete_field(2, field_num, idc):
                    modifications_applied.append(f"Deleted 2.{field_num:03d}")
                else:
                    logger.warning(f"Field 2.{field_num:03d} not found or already deleted")

            # Replace field 2.217
            for field_num, new_value in SIGNA_MULTIPLE_RULES['replace_fields'].items():
                logger.info(f"Setting field 2.{field_num:03d} = '{new_value}'")
                if nist_file.modify_field(2, field_num, new_value, idc):
                    modifications_applied.append(f"Set 2.{field_num:03d} = '{new_value}'")
                else:
                    logger.error(f"Failed to modify field 2.{field_num:03d}")

            # Export modified file
            logger.info(f"Exporting to: {output_path}")
            success = nist_file.export(output_path)

            if success:
                logger.info(f"Export Signa Multiple successful!")
                logger.info(f"Modifications applied: {', '.join(modifications_applied)}")
            else:
                logger.error("Export failed")

            return success

        except Exception as e:
            logger.error(f"Error during Export Signa Multiple: {e}")
            return False

    @staticmethod
    def validate_export_path(output_path: str) -> bool:
        """
        Validate export path.

        Args:
            output_path: Path to validate

        Returns:
            True if path is valid, False otherwise
        """
        if not output_path:
            return False

        # Check if path has valid extension
        valid_extensions = ['.nist', '.eft', '.an2']
        has_valid_ext = any(output_path.lower().endswith(ext) for ext in valid_extensions)

        if not has_valid_ext:
            logger.warning(f"Output path should have NIST extension (.nist, .eft, .an2)")

        return True

    @staticmethod
    def get_export_info() -> str:
        """
        Get information about Export Signa Multiple rules.

        Returns:
            Description of export rules
        """
        info_lines = [
            "Export Signa Multiple - Fixed Rules:",
            "",
            "Modifications applied to Type-2 record:",
        ]

        # Delete fields
        for field_num in SIGNA_MULTIPLE_RULES['delete_fields']:
            info_lines.append(f"  - DELETE field 2.{field_num:03d}")

        # Replace fields
        for field_num, value in SIGNA_MULTIPLE_RULES['replace_fields'].items():
            info_lines.append(f"  - SET field 2.{field_num:03d} = '{value}'")

        return "\n".join(info_lines)
