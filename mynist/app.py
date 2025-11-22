"""Main application module for NIST Studio."""

import sys
from PyQt5.QtWidgets import QApplication
from mynist.views.main_window import MainWindow
from mynist.utils.logger import setup_logger
from mynist.utils.constants import APP_NAME

logger = setup_logger(APP_NAME)


class NISTStudioApp:
    """NIST Studio main application class."""

    def __init__(self):
        """Initialize application."""
        self.qapp = QApplication(sys.argv)
        self.qapp.setApplicationName(APP_NAME)

        # Set application style (optional - for better Ubuntu look)
        self.qapp.setStyle('Fusion')

        # Create main window
        self.main_window = MainWindow()

    def run(self):
        """Run the application."""
        logger.info(f"Starting {APP_NAME}...")

        # Show main window
        self.main_window.show()

        # Start event loop
        exit_code = self.qapp.exec_()

        logger.info(f"{APP_NAME} exiting with code {exit_code}")
        return exit_code
