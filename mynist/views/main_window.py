"""Main application window."""

from pathlib import Path
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from mynist.views.file_panel import FilePanel
from mynist.views.data_panel import DataPanel
from mynist.views.image_panel import ImagePanel
from mynist.views.home_view import HomeView
from mynist.controllers.file_controller import FileController
from mynist.controllers.export_controller import ExportController
from mynist.utils.constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    PANEL_SIZES,
    NIST_FILE_FILTER,
)
from mynist.utils.logger import get_logger
from mynist.utils.recent_files import RecentFiles

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with 3-panel layout."""

    def __init__(self):
        """Initialize MainWindow."""
        super().__init__()
        self.file_controller = FileController()
        self.export_controller = ExportController()
        self.base_title = f"{APP_NAME} - NIST File Viewer"
        self.recent_files = RecentFiles()
        self.active_mode = "home"
        self.last_non_home_mode = "viewer"
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

        # Build views and stack router
        self.stacked_widget = QStackedWidget()
        self.home_view = HomeView(self)
        self.viewer_page = self._build_viewer_page()
        self.stacked_widget.addWidget(self.home_view)
        self.stacked_widget.addWidget(self.viewer_page)
        self.setCentralWidget(self.stacked_widget)

        # Connect HomeView signals
        self.home_view.open_file_requested.connect(self.open_file)
        self.home_view.open_recent_requested.connect(self.on_open_recent)
        self.home_view.mode_requested.connect(self.on_mode_requested)
        self.home_view.clear_recents_requested.connect(self.on_clear_recents)
        self.home_view.resume_requested.connect(self.on_resume_last_mode)

        # Create menu bar
        self.create_menus()

        # Quick action toolbar
        self.create_toolbar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")

        # Populate initial state
        self.refresh_recent_entries()
        self.switch_to_home()
        self.update_actions_state(False)

    def _build_viewer_page(self) -> QWidget:
        """Create viewer page containing the 3-panel splitter."""
        container = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self.file_panel = FilePanel(self)
        self.data_panel = DataPanel(self)
        self.image_panel = ImagePanel(self)

        splitter.addWidget(self.file_panel)
        splitter.addWidget(self.data_panel)
        splitter.addWidget(self.image_panel)
        splitter.setSizes(PANEL_SIZES)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        container.setLayout(layout)

        # Connect signals
        self.file_panel.record_selected.connect(self.on_record_selected)

        return container

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

        # Navigation menu
        nav_menu = menubar.addMenu('&Navigation')
        self.nav_home_action = QAction('Aller au &hub', self)
        self.nav_home_action.setShortcut('Alt+1')
        self.nav_home_action.setStatusTip('Retour à l\'accueil')
        self.nav_home_action.triggered.connect(self.switch_to_home)
        nav_menu.addAction(self.nav_home_action)

        self.nav_view_action = QAction('Aller au &viewer', self)
        self.nav_view_action.setShortcut('Alt+2')
        self.nav_view_action.setStatusTip('Afficher le viewer 3 panneaux')
        self.nav_view_action.triggered.connect(self.on_resume_last_mode)
        nav_menu.addAction(self.nav_view_action)
        self.nav_view_action.setEnabled(False)

        self.nav_compare_action = QAction('Aller à la &comparaison', self)
        self.nav_compare_action.setShortcut('Alt+3')
        self.nav_compare_action.setStatusTip('Mode comparaison (à venir)')
        self.nav_compare_action.triggered.connect(
            lambda: QMessageBox.information(self, "Comparaison", "Mode comparaison à venir.")
        )
        self.nav_compare_action.setEnabled(False)
        nav_menu.addAction(self.nav_compare_action)

        self.nav_pdf_action = QAction('Aller à l\'export &PDF', self)
        self.nav_pdf_action.setShortcut('Alt+4')
        self.nav_pdf_action.setStatusTip('Mode export PDF (à venir)')
        self.nav_pdf_action.triggered.connect(
            lambda: QMessageBox.information(self, "Export PDF", "Mode export PDF à venir.")
        )
        self.nav_pdf_action.setEnabled(False)
        nav_menu.addAction(self.nav_pdf_action)

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

        # Navigation
        self.home_action = QAction('Hub', self)
        self.home_action.setIcon(self._build_home_icon())
        self.home_action.triggered.connect(self.switch_to_home)
        toolbar.addAction(self.home_action)

        self.resume_action = QAction('Reprendre', self)
        self.resume_action.setIcon(self._build_play_icon())
        self.resume_action.triggered.connect(self.on_resume_last_mode)
        self.resume_action.setEnabled(False)
        toolbar.addAction(self.resume_action)

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
        self.nav_view_action.setEnabled(file_open)
        self.resume_action.setEnabled(file_open)

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
        self.home_view.set_current_file(None)
        self.switch_to_home()

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

            # Update recents and navigation state
            record_types = nist_file.get_record_types()
            self.recent_files.add(file_path, last_mode="viewer", summary_types=record_types)
            self.refresh_recent_entries()
            self.home_view.set_current_file(file_path, "viewer")
            self.switch_to_viewer()
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

    def refresh_recent_entries(self):
        """Refresh recent entries in HomeView."""
        entries = self.recent_files.get_entries()
        self.home_view.set_recent_entries(entries)

    def switch_to_home(self):
        """Show home view."""
        self.active_mode = "home"
        self.stacked_widget.setCurrentIndex(0)
        current_path = self.file_controller.current_filepath if self.file_controller else None
        self.home_view.set_current_file(current_path, self.last_non_home_mode)
        self.status_bar.showMessage("Hub (Alt+1) — sélectionnez un mode", 3000)

    def switch_to_viewer(self):
        """Show viewer page."""
        self.active_mode = "viewer"
        self.last_non_home_mode = "viewer"
        self.stacked_widget.setCurrentIndex(1)
        current_path = self.file_controller.current_filepath if self.file_controller else ""
        if current_path:
            self.status_bar.showMessage(f"Viewer — {current_path}", 4000)
        else:
            self.status_bar.showMessage("Viewer", 3000)

    def on_open_recent(self, path: str):
        """Handle opening a recent file from HomeView."""
        if not Path(path).exists():
            should_remove = QMessageBox.question(
                self,
                "Fichier introuvable",
                f"Le fichier n'existe plus :\n{path}\n\nVoulez-vous le retirer de la liste des récents ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if should_remove == QMessageBox.Yes:
                self.recent_files.remove(path)
                self.refresh_recent_entries()
            return

        self.load_nist_file(path)

    def on_mode_requested(self, mode: str):
        """Handle mode card selection from HomeView."""
        if mode == "viewer":
            if self.file_controller.is_file_open():
                self.switch_to_viewer()
            else:
                self.open_file()
        elif mode == "comparison":
            QMessageBox.information(self, "Comparaison", "Mode comparaison à venir.")
        elif mode == "pdf":
            QMessageBox.information(self, "Export PDF", "Mode export PDF à venir.")

    def on_resume_last_mode(self):
        """Resume last non-home mode when a file is open."""
        if not self.file_controller.is_file_open():
            QMessageBox.information(self, "Aucun fichier", "Ouvrez un fichier pour reprendre la navigation.")
            return
        if self.last_non_home_mode == "viewer":
            self.switch_to_viewer()
        else:
            self.switch_to_viewer()

    def on_clear_recents(self):
        """Clear recent files list."""
        self.recent_files.clear()
        self.refresh_recent_entries()

    def _build_home_icon(self) -> QIcon:
        """Create a simple home-shaped icon."""
        size = 28
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#495057"), 2))
        painter.setBrush(QColor("#e9ecef"))
        points = [
            QPoint(6, size - 8),
            QPoint(size // 2, 6),
            QPoint(size - 6, size - 8),
        ]
        painter.drawPolygon(points[0], points[1], points[2])
        painter.drawRect(10, size - 14, size - 20, 10)
        painter.end()
        return QIcon(pixmap)

    def _build_play_icon(self) -> QIcon:
        """Create a simple play/resume icon."""
        size = 28
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#51cf66"))
        painter.setPen(QPen(QColor("#2b8a3e"), 2))
        painter.drawPolygon(
            QPoint(8, 6),
            QPoint(size - 6, size // 2),
            QPoint(8, size - 6)
        )
        painter.end()
        return QIcon(pixmap)
