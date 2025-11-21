"""Main application window."""

from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QSplitter, QFileDialog, QMessageBox,
                              QAction, QStatusBar, QToolBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
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
        self.base_title = f"{APP_NAME} - NIST File Viewer"
        self.init_ui()

    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle(self.base_title)
        self.setGeometry(100, 100, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setAcceptDrops(True)

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

        # Quick action toolbar
        self.create_toolbar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.update_actions_state(False)

    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        # Open action
        self.open_action = QAction('&Open NIST File...', self)
        self.open_action.setShortcut('Ctrl+O')
        self.open_action.setStatusTip('Open a NIST file')
        self.open_action.triggered.connect(self.open_file)
        file_menu.addAction(self.open_action)

        # Close action
        self.close_action = QAction('&Close NIST File', self)
        self.close_action.setShortcut('Ctrl+W')
        self.close_action.setStatusTip('Close the current NIST file')
        self.close_action.triggered.connect(self.close_current_file)
        self.close_action.setEnabled(False)
        file_menu.addAction(self.close_action)

        file_menu.addSeparator()

        # Export Signa Multiple action
        self.export_signa_action = QAction('Export &Signa Multiple...', self)
        self.export_signa_action.setShortcut('Ctrl+E')
        self.export_signa_action.setStatusTip('Export with Signa Multiple modifications')
        self.export_signa_action.triggered.connect(self.export_signa_multiple)
        self.export_signa_action.setEnabled(False)
        file_menu.addAction(self.export_signa_action)

        file_menu.addSeparator()

        # Quit action
        self.quit_action = QAction('&Quit', self)
        self.quit_action.setShortcut('Ctrl+Q')
        self.quit_action.setStatusTip('Quit application')
        self.quit_action.triggered.connect(self.close)
        file_menu.addAction(self.quit_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        # About action
        self.about_action = QAction('&About', self)
        self.about_action.setStatusTip('About myNIST')
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)

        # Export Signa Info action
        self.info_action = QAction('Export Signa Multiple &Info', self)
        self.info_action.setStatusTip('Information about Export Signa Multiple')
        self.info_action.triggered.connect(self.show_export_info)
        help_menu.addAction(self.info_action)

    def create_toolbar(self):
        """Create quick action toolbar with icons."""
        toolbar = QToolBar("Quick Actions", self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(20, 20))

        # Attach icons
        self.open_action.setIcon(self._build_plus_icon())
        self.close_action.setIcon(self._build_stop_icon())
        self.export_signa_action.setIcon(self._build_magic_icon())

        toolbar.addAction(self.open_action)
        toolbar.addAction(self.close_action)
        toolbar.addAction(self.export_signa_action)

        self.addToolBar(toolbar)

    def _build_plus_icon(self) -> QIcon:
        """Create a simple green plus icon."""
        size = 28
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#2b8a3e"), 4))

        mid = size // 2
        offset = 7
        painter.drawLine(mid, offset, mid, size - offset)
        painter.drawLine(offset, mid, size - offset, mid)

        painter.end()
        return QIcon(pixmap)

    def _build_stop_icon(self) -> QIcon:
        """Create a red square stop icon."""
        size = 28
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(6, 6, size - 12, size - 12, QColor("#c92a2a"))
        painter.setPen(QPen(QColor("#7c2a2a"), 2))
        painter.drawRect(6, 6, size - 12, size - 12)
        painter.end()
        return QIcon(pixmap)

    def _build_magic_icon(self) -> QIcon:
        """Create a small magic-wand icon."""
        size = 28
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Wand handle
        painter.setPen(QPen(QColor("#364fc7"), 3))
        painter.drawLine(8, size - 8, size - 10, 10)

        # Sparkles
        painter.setPen(QPen(QColor("#f59f00"), 2))
        center = 10
        painter.drawLine(center, center - 6, center, center + 6)
        painter.drawLine(center - 6, center, center + 6, center)
        painter.drawLine(center - 4, center - 4, center + 4, center + 4)
        painter.drawLine(center - 4, center + 4, center + 4, center - 4)

        painter.end()
        return QIcon(pixmap)

    def update_actions_state(self, file_open: bool):
        """Enable or disable actions based on whether a file is loaded."""
        self.close_action.setEnabled(file_open)
        self.export_signa_action.setEnabled(file_open)

    def close_current_file(self, show_message: bool = True):
        """Close and clear the currently loaded NIST file."""
        if not self.file_controller.is_file_open():
            return

        self.file_controller.close_file()
        self.file_panel.clear()
        self.data_panel.clear()
        self.image_panel.clear()
        self.setWindowTitle(self.base_title)
        self.update_actions_state(False)

        if show_message:
            self.status_bar.showMessage("Closed current NIST file", 4000)

    def dragEnterEvent(self, event):
        """Accept drag if it contains a supported local file."""
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths and self._is_supported_file(paths[0]):
                event.acceptProposedAction()
                self.status_bar.showMessage(f"Drop to open: {paths[0]}", 3000)
                return

        event.ignore()

    def dropEvent(self, event):
        """Load a NIST file dropped onto the window."""
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths:
                file_path = paths[0]
                if self._is_supported_file(file_path):
                    event.acceptProposedAction()
                    self.load_nist_file(file_path)
                    return
                else:
                    QMessageBox.warning(
                        self,
                        "Unsupported file",
                        "Please drop a NIST file (.nist, .eft, .an2)."
                    )

        event.ignore()

    def _is_supported_file(self, file_path: str) -> bool:
        """Check if dropped file has a supported NIST extension."""
        return file_path.lower().endswith(('.nist', '.eft', '.an2'))

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
            # Clear previous views before loading new content
            self.file_panel.clear()
            self.data_panel.clear()
            self.image_panel.clear()

            # Load into panels
            self.file_panel.load_nist_file(nist_file)
            self.data_panel.load_nist_file(nist_file)
            self.image_panel.load_nist_file(nist_file)

            # Update window title
            self.setWindowTitle(f"{APP_NAME} - {file_path}")

            # Update status
            self.status_bar.showMessage(f"Loaded: {file_path}", 5000)
            self.update_actions_state(True)

            logger.info(f"Successfully loaded: {file_path}")
        else:
            # Show error
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load NIST file:\n{file_path}\n\nPlease check the file format."
            )
            self.status_bar.showMessage("Failed to load file", 5000)
            self.update_actions_state(self.file_controller.is_file_open())
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
        self.close_current_file(show_message=False)
        logger.info("Application closing")
        event.accept()
