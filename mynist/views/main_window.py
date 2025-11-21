"""Main application window."""

from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QSplitter, QFileDialog, QMessageBox,
                              QAction, QStatusBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from mynist.views.file_panel import FilePanel
from mynist.views.data_panel import DataPanel
from mynist.views.image_panel import ImagePanel
from mynist.controllers.file_controller import FileController
from mynist.controllers.export_controller import ExportController
from mynist.utils.constants import (APP_NAME, APP_VERSION, DEFAULT_WINDOW_WIDTH,
                                     DEFAULT_WINDOW_HEIGHT, PANEL_SIZES, NIST_FILE_FILTER)
from mynist.utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with 3-panel layout."""

    def __init__(self):
        """Initialize MainWindow."""
        super().__init__()
        self.file_controller = FileController()
        self.export_controller = ExportController()
        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle(f"{APP_NAME} - NIST File Viewer")
        self.setGeometry(100, 100, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        # Set application icon
        icon_path = Path(__file__).parent.parent / 'resources' / 'icons' / 'mynist.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Create 3-panel splitter
        splitter = QSplitter(Qt.Horizontal)

        # Create panels
        self.file_panel = FilePanel(self)
        self.data_panel = DataPanel(self)
        self.image_panel = ImagePanel(self)

        # Add panels to splitter
        splitter.addWidget(self.file_panel)
        splitter.addWidget(self.data_panel)
        splitter.addWidget(self.image_panel)

        # Set initial panel sizes
        splitter.setSizes(PANEL_SIZES)

        # Set central widget
        self.setCentralWidget(splitter)

        # Connect signals
        self.file_panel.record_selected.connect(self.on_record_selected)

        # Create menu bar
        self.create_menus()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        # Open action
        open_action = QAction('&Open NIST File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open a NIST file')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Export Signa Multiple action
        export_signa_action = QAction('Export &Signa Multiple...', self)
        export_signa_action.setShortcut('Ctrl+E')
        export_signa_action.setStatusTip('Export with Signa Multiple modifications')
        export_signa_action.triggered.connect(self.export_signa_multiple)
        file_menu.addAction(export_signa_action)

        file_menu.addSeparator()

        # Quit action
        quit_action = QAction('&Quit', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.setStatusTip('Quit application')
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        # About action
        about_action = QAction('&About', self)
        about_action.setStatusTip('About myNIST')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Export Signa Info action
        info_action = QAction('Export Signa Multiple &Info', self)
        info_action.setStatusTip('Information about Export Signa Multiple')
        info_action.triggered.connect(self.show_export_info)
        help_menu.addAction(info_action)

    def open_file(self):
        """Open NIST file dialog and load file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open NIST File",
            "",
            NIST_FILE_FILTER
        )

        if file_path:
            logger.info(f"User selected file: {file_path}")
            self.load_nist_file(file_path)

    def load_nist_file(self, file_path: str):
        """
        Load and display NIST file.

        Args:
            file_path: Path to NIST file
        """
        self.status_bar.showMessage(f"Loading {file_path}...")

        # Open file with controller
        nist_file = self.file_controller.open_file(file_path)

        if nist_file:
            # Load into panels
            self.file_panel.load_nist_file(nist_file)
            self.data_panel.load_nist_file(nist_file)
            self.image_panel.load_nist_file(nist_file)

            # Update window title
            self.setWindowTitle(f"{APP_NAME} - {file_path}")

            # Update status
            self.status_bar.showMessage(f"Loaded: {file_path}", 5000)

            logger.info(f"Successfully loaded: {file_path}")
        else:
            # Show error
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load NIST file:\n{file_path}\n\nPlease check the file format."
            )
            self.status_bar.showMessage("Failed to load file", 5000)
            logger.error(f"Failed to load: {file_path}")

    def on_record_selected(self, record_type: int, idc: int):
        """
        Handle record selection from file panel.

        Args:
            record_type: Selected record type
            idc: Selected record IDC
        """
        logger.info(f"Record selected: Type-{record_type}, IDC {idc}")

        # Update data panel
        self.data_panel.display_record(record_type, idc)

        # Update image panel
        self.image_panel.display_record(record_type, idc)

        # Update status
        self.status_bar.showMessage(f"Displaying Type-{record_type} record (IDC {idc})")

    def export_signa_multiple(self):
        """Export NIST file with Signa Multiple modifications."""
        # Check if file is loaded
        if not self.file_controller.is_file_open():
            QMessageBox.warning(
                self,
                "No File",
                "Please open a NIST file first."
            )
            return

        # Get output path
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Signa Multiple",
            "",
            NIST_FILE_FILTER
        )

        if output_path:
            self.status_bar.showMessage(f"Exporting to {output_path}...")

            # Get current NIST file
            nist_file = self.file_controller.get_current_file()

            # Export with modifications
            success = self.export_controller.export_signa_multiple(nist_file, output_path)

            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully exported to:\n{output_path}\n\n"
                    "Modifications applied:\n"
                    "- Deleted field 2.215\n"
                    "- Set field 2.217 = '11707'"
                )
                self.status_bar.showMessage(f"Exported: {output_path}", 5000)
                logger.info(f"Export Signa Multiple successful: {output_path}")
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to export to:\n{output_path}\n\n"
                    "Please check the logs for details."
                )
                self.status_bar.showMessage("Export failed", 5000)
                logger.error(f"Export Signa Multiple failed: {output_path}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h2>{APP_NAME} {APP_VERSION}</h2>"
            "<p>A NIST File Viewer and Editor for Ubuntu</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>View ANSI/NIST-ITL files</li>"
            "<li>Display Type-2 alphanumeric data</li>"
            "<li>Display fingerprint images</li>"
            "<li>Export Signa Multiple with fixed modifications</li>"
            "</ul>"
            "<p>Powered by nistitl (Idemia) and PyQt5</p>"
        )

    def show_export_info(self):
        """Show Export Signa Multiple information."""
        info_text = self.export_controller.get_export_info()

        QMessageBox.information(
            self,
            "Export Signa Multiple Info",
            info_text
        )

    def closeEvent(self, event):
        """
        Handle window close event.

        Args:
            event: Close event
        """
        logger.info("Application closing")
        event.accept()
