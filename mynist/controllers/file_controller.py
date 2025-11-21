"""File operations controller for NIST files."""

from pathlib import Path
from typing import Optional
from mynist.models.nist_file import NISTFile
from mynist.utils.logger import get_logger

logger = get_logger(__name__)


class FileController:
    """Handles file operations for NIST files."""

    def __init__(self):
        """Initialize FileController."""
        self.current_file: Optional[NISTFile] = None
        self.current_filepath: Optional[str] = None
        self.last_error: Optional[str] = None

    def open_file(self, filepath: str) -> Optional[NISTFile]:
        """
        Open and parse a NIST file.

        Args:
            filepath: Path to NIST file

        Returns:
            NISTFile instance if successful, None otherwise
        """
        try:
            logger.info(f"Opening NIST file: {filepath}")

            # Check if file exists
            if not Path(filepath).exists():
                logger.error(f"File not found: {filepath}")
                return None

            # Create and parse NIST file
            nist_file = NISTFile(filepath)
            if nist_file.parse():
                self.current_file = nist_file
                self.current_filepath = filepath
                self.last_error = None
                logger.info(f"Successfully opened: {filepath}")
                logger.info(f"Records found: {len(nist_file.records)}")
                return nist_file
            else:
                self.last_error = nist_file.last_error
                logger.error(f"Failed to parse NIST file: {filepath} "
                             f"({self.last_error})")
                return None

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error opening file: {e}")
            return None

    def get_current_file(self) -> Optional[NISTFile]:
        """
        Get currently open NIST file.

        Returns:
            Current NISTFile instance or None
        """
        return self.current_file

    def close_file(self):
        """Close current file."""
        if self.current_file:
            logger.info(f"Closing file: {self.current_filepath}")
            self.current_file = None
            self.current_filepath = None
            self.last_error = None

    def is_file_open(self) -> bool:
        """
        Check if a file is currently open.

        Returns:
            True if file is open, False otherwise
        """
        return self.current_file is not None

    def get_file_summary(self) -> str:
        """
        Get summary of current file.

        Returns:
            Summary string or empty string if no file open
        """
        if not self.current_file:
            return "No file open"

        return self.current_file.get_summary()

    def format_last_error(self) -> str:
        """Return a user-friendly error message based on the last parsing error."""
        if not self.last_error:
            return "Please check the file format."

        low = self.last_error.lower()
        if "nist_too_short" in low:
            return (
                "Fichier tronqué ou incomplet (NIST_TOO_SHORT). "
                "Le fichier semble coupé et ne peut pas être ouvert."
            )

        return self.last_error

    def export_file(self, output_path: str) -> bool:
        """
        Export current NIST file to a new location.

        Args:
            output_path: Path to save the file

        Returns:
            True if export succeeded, False otherwise
        """
        if not self.current_file:
            logger.error("No file to export")
            return False

        try:
            logger.info(f"Exporting NIST file to: {output_path}")
            success = self.current_file.export(output_path)

            if success:
                logger.info(f"Successfully exported to: {output_path}")
            else:
                logger.error(f"Failed to export to: {output_path}")

            return success

        except Exception as e:
            logger.error(f"Error exporting file: {e}")
            return False
