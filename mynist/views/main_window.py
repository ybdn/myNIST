"""Main application window."""

from pathlib import Path
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPalette
from PyQt5.QtSvg import QSvgRenderer
from mynist.views.file_panel import FilePanel
from mynist.views.data_panel import DataPanel
from mynist.views.image_panel import ImagePanel
from mynist.views.home_view import HomeView
from mynist.views.pdf_export_view import PdfExportView
from mynist.views.comparison_view import ComparisonView
from mynist.views.image2nist_view import Image2NISTView
from mynist.controllers.file_controller import FileController
from mynist.controllers.export_controller import ExportController
from mynist.controllers.pdf_controller import PDFController
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
from mynist.utils.design_tokens import (
    Colors, Typography, Spacing, Radius, Dimensions
)

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with 3-panel layout."""

    def __init__(self):
        """Initialize MainWindow."""
        super().__init__()
        self.file_controller = FileController()
        self.export_controller = ExportController()
        self.pdf_controller = PDFController()
        self.base_title = APP_NAME
        self.recent_files = RecentFiles()
        self.active_mode = "home"
        self.last_non_home_mode = "viewer"
        self.is_modified = False
        self.last_change = None
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
        self.pdf_view = PdfExportView(self)
        self.comparison_view = ComparisonView(self)
        self.image2nist_view = Image2NISTView(self)
        self.stacked_widget.addWidget(self.home_view)        # index 0
        self.stacked_widget.addWidget(self.viewer_page)      # index 1
        self.stacked_widget.addWidget(self.pdf_view)         # index 2
        self.stacked_widget.addWidget(self.comparison_view)  # index 3
        self.stacked_widget.addWidget(self.image2nist_view)  # index 4
        self.setCentralWidget(self.stacked_widget)

        # Connect HomeView signals
        self.home_view.open_file_requested.connect(self.open_file)
        self.home_view.open_recent_requested.connect(self.on_open_recent)
        self.home_view.mode_requested.connect(self.on_mode_requested)
        self.home_view.clear_recents_requested.connect(self.on_clear_recents)
        self.home_view.resume_requested.connect(self.on_resume_last_mode)
        self.pdf_view.back_requested.connect(self.switch_to_home)
        self.pdf_view.browse_requested.connect(self.export_pdf_report)
        self.pdf_view.export_requested.connect(self.export_pdf_report_with_path)
        self.image2nist_view.back_requested.connect(self.switch_to_home)
        self.comparison_view.back_requested.connect(self.switch_to_home)

        # Create menu bar
        self.create_menus()

        # Quick action toolbar (cachée)
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
        """Create viewer page containing header bar and 3-panel splitter."""
        container = QWidget()
        container.setObjectName("ViewerRoot")

        # Apply NIST Studio Design System
        palette = self.palette()
        window = palette.color(QPalette.Window)
        is_dark = window.value() < 128

        if is_dark:
            window_bg = Colors.BG_DARK
            header_bg = Colors.SURFACE_DARK
            text_color = Colors.TEXT_PRIMARY_DARK
            border_color = Colors.BORDER_DARK
        else:
            window_bg = Colors.BG_LIGHT
            header_bg = Colors.SURFACE_LIGHT
            text_color = Colors.TEXT_PRIMARY_LIGHT
            border_color = Colors.BORDER_SUBTLE

        container.setStyleSheet(f"""
            #ViewerRoot {{
                background-color: {window_bg};
            }}
            #viewerHeader {{
                background: {header_bg};
                border-bottom: 1px solid {border_color};
            }}
            #viewerHeader QLabel {{
                color: {text_color};
            }}
            #viewerTitleLabel {{
                font-size: {Typography.SIZE_MEDIUM}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                color: {Colors.PRIMARY if not is_dark else text_color};
            }}
            #viewerFileLabel {{
                font-size: {Typography.SIZE_SMALL}px;
                color: {Colors.TEXT_SECONDARY};
            }}
            #hubButton {{
                background: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: {Radius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-weight: {Typography.WEIGHT_MEDIUM};
            }}
            #hubButton:hover {{
                background: {Colors.HOVER_ACCENT};
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QFrame()
        header.setObjectName("viewerHeader")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(
            Spacing.HEADER_PADDING_H, Spacing.HEADER_PADDING_V,
            Spacing.HEADER_PADDING_H, Spacing.HEADER_PADDING_V
        )

        # Hub button
        hub_btn = QPushButton("Retour au Hub")
        hub_btn.setObjectName("hubButton")
        hub_btn.setCursor(Qt.PointingHandCursor)
        hub_btn.clicked.connect(self.switch_to_home)
        hub_icon = self._load_hub_icon("home", 20)
        if not hub_icon.isNull():
            hub_btn.setIcon(hub_icon)
        header_layout.addWidget(hub_btn)

        header_layout.addStretch()

        # Title
        title = QLabel("NIST-Viewer")
        title.setObjectName("viewerTitleLabel")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # File info label
        self.viewer_file_label = QLabel("Aucun fichier")
        self.viewer_file_label.setObjectName("viewerFileLabel")
        header_layout.addWidget(self.viewer_file_label)

        header.setLayout(header_layout)
        layout.addWidget(header)

        # 3-panel splitter
        splitter = QSplitter(Qt.Horizontal)

        self.file_panel = FilePanel(self)
        self.data_panel = DataPanel(self)
        self.image_panel = ImagePanel(self)

        splitter.addWidget(self.file_panel)
        splitter.addWidget(self.data_panel)
        splitter.addWidget(self.image_panel)
        splitter.setSizes(PANEL_SIZES)

        layout.addWidget(splitter, 1)
        container.setLayout(layout)

        # Connect signals
        self.file_panel.record_selected.connect(self.on_record_selected)
        self.data_panel.field_changed.connect(self.on_field_changed)

        return container

    def _load_hub_icon(self, name: str, size: int = 24) -> QIcon:
        """Load SVG icon from hub folder."""
        path = Path(__file__).parent.parent / "resources" / "icons" / "hub" / f"{name}.svg"
        if not path.exists():
            return QIcon()

        renderer = QSvgRenderer(str(path))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()

        # ═══════════════════════════════════════════════════════════════════
        # Menu Fichier
        # ═══════════════════════════════════════════════════════════════════
        file_menu = menubar.addMenu('&Fichier')

        self.open_action = QAction('&Ouvrir...', self)
        self.open_action.setShortcut('Ctrl+O')
        self.open_action.setStatusTip('Ouvrir un fichier NIST')
        self.open_action.triggered.connect(self.open_file)
        file_menu.addAction(self.open_action)

        self.close_action = QAction('&Fermer', self)
        self.close_action.setShortcut('Ctrl+W')
        self.close_action.setStatusTip('Fermer le fichier courant')
        self.close_action.triggered.connect(self.close_current_file)
        self.close_action.setEnabled(False)
        file_menu.addAction(self.close_action)

        file_menu.addSeparator()

        self.save_action = QAction('&Enregistrer', self)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.setStatusTip('Enregistrer les modifications')
        self.save_action.triggered.connect(self.save_file_as)
        self.save_action.setEnabled(False)
        file_menu.addAction(self.save_action)

        self.save_as_action = QAction('Enregistrer &sous...', self)
        self.save_as_action.setShortcut('Ctrl+Shift+S')
        self.save_as_action.setStatusTip('Enregistrer sous un nouveau nom')
        self.save_as_action.triggered.connect(self.save_file_as)
        self.save_as_action.setEnabled(False)
        file_menu.addAction(self.save_as_action)

        file_menu.addSeparator()

        # Sous-menu Exports
        export_menu = file_menu.addMenu('E&xports')

        self.export_signa_action = QAction('Export Signa &Multiple...', self)
        self.export_signa_action.setShortcut('Ctrl+E')
        self.export_signa_action.setStatusTip('Exporter avec modifications Signa Multiple')
        self.export_signa_action.triggered.connect(self.export_signa_multiple)
        self.export_signa_action.setEnabled(False)
        export_menu.addAction(self.export_signa_action)

        # Supprime l'ancien export_pdf_action du menu Fichier (maintenant dans Outils)

        file_menu.addSeparator()

        self.quit_action = QAction('&Quitter', self)
        self.quit_action.setShortcut('Ctrl+Q')
        self.quit_action.setStatusTip("Quitter l'application")
        self.quit_action.triggered.connect(self.close)
        file_menu.addAction(self.quit_action)

        # ═══════════════════════════════════════════════════════════════════
        # Menu Outils
        # ═══════════════════════════════════════════════════════════════════
        tools_menu = menubar.addMenu('&Outils')

        self.nav_home_action = QAction('&Accueil', self)
        self.nav_home_action.setShortcut('Alt+1')
        self.nav_home_action.setStatusTip('Retour a l\'accueil')
        self.nav_home_action.triggered.connect(self.switch_to_home)
        tools_menu.addAction(self.nav_home_action)

        tools_menu.addSeparator()

        self.nav_viewer_action = QAction('NIST-&Viewer', self)
        self.nav_viewer_action.setShortcut('Alt+2')
        self.nav_viewer_action.setStatusTip('Visualiser et editer des fichiers NIST')
        self.nav_viewer_action.triggered.connect(self.switch_to_viewer)
        self.nav_viewer_action.setEnabled(False)
        tools_menu.addAction(self.nav_viewer_action)

        self.nav_compare_action = QAction('NIST-&Compare', self)
        self.nav_compare_action.setShortcut('Alt+3')
        self.nav_compare_action.setStatusTip('Comparer cote a cote deux images')
        self.nav_compare_action.triggered.connect(self.switch_to_comparison)
        tools_menu.addAction(self.nav_compare_action)

        self.nav_pdf_action = QAction('NIST-2-&PDF', self)
        self.nav_pdf_action.setShortcut('Alt+4')
        self.nav_pdf_action.setStatusTip('Exporter un releve decadactylaire PDF')
        self.nav_pdf_action.triggered.connect(self.switch_to_pdf_view)
        self.nav_pdf_action.setEnabled(False)
        tools_menu.addAction(self.nav_pdf_action)

        self.nav_image2nist_action = QAction('&Image-2-NIST', self)
        self.nav_image2nist_action.setShortcut('Alt+5')
        self.nav_image2nist_action.setStatusTip('Convertir une image en fichier NIST (a venir)')
        self.nav_image2nist_action.triggered.connect(self.switch_to_image2nist)
        self.nav_image2nist_action.setEnabled(False)
        tools_menu.addAction(self.nav_image2nist_action)

        # ═══════════════════════════════════════════════════════════════════
        # Menu Aide
        # ═══════════════════════════════════════════════════════════════════
        help_menu = menubar.addMenu('&Aide')

        self.about_action = QAction('A &propos de NIST Studio', self)
        self.about_action.setStatusTip('A propos de NIST Studio')
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)

    def create_toolbar(self):
        """Create quick action toolbar with icons."""
        toolbar = QToolBar("Quick Actions", self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setVisible(False)  # toolbar masquée pour ne pas occuper l'UI

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

        self.save_action = QAction('Enregistrer', self)
        self.save_action.setIcon(self._build_magic_icon())
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.triggered.connect(self.save_file_as)
        self.save_action.setEnabled(False)
        toolbar.addAction(self.save_action)

        self.undo_action = QAction('Annuler', self)
        self.undo_action.setShortcut('Ctrl+Z')
        self.undo_action.triggered.connect(self.undo_last_change)
        self.undo_action.setEnabled(False)
        toolbar.addAction(self.undo_action)

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
        self.nav_viewer_action.setEnabled(file_open)
        self.nav_pdf_action.setEnabled(file_open)
        self.resume_action.setEnabled(file_open)
        self.save_as_action.setEnabled(file_open)
        self.save_action.setEnabled(file_open and self.is_modified)
        self.undo_action.setEnabled(self.last_change is not None)
        self.nav_compare_action.setEnabled(True)

    def close_current_file(self, show_message: bool = True):
        """Close and clear the currently loaded NIST file."""
        if not self.file_controller.is_file_open():
            return

        if not self._confirm_discard_changes():
            return

        self.file_controller.close_file()
        self.file_panel.clear()
        self.data_panel.clear()
        self.image_panel.clear()
        self.setWindowTitle(self.base_title)
        self.update_actions_state(False)
        self.home_view.set_current_file(None)
        self._update_viewer_file_label(None)
        self.switch_to_home()
        self.is_modified = False
        self.last_change = None

        if show_message:
            self.status_bar.showMessage("Closed current NIST file", 4000)

    def _update_viewer_file_label(self, path: str = None):
        """Update the file label in viewer header."""
        if hasattr(self, 'viewer_file_label'):
            if path:
                name = Path(path).name
                self.viewer_file_label.setText(f"Fichier : {name}")
            else:
                self.viewer_file_label.setText("Aucun fichier")

    def dragEnterEvent(self, event):
        """Accept drag if it contains a supported local file."""
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths and self._is_supported_file(paths[0]):
                event.acceptProposedAction()
                self.status_bar.showMessage(f"Déposez pour ouvrir : {paths[0]}", 3000)
                return

        event.ignore()

    def dropEvent(self, event):
        """Load a NIST file dropped onto the window."""
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths:
                file_path = paths[0]
                if self._is_supported_file(file_path):
                    if not self._confirm_discard_changes():
                        event.ignore()
                        return
                    event.acceptProposedAction()
                    self.load_nist_file(file_path)
                    return
                else:
                    QMessageBox.warning(
                        self,
                        "Fichier non supporté",
                        "Merci de déposer un fichier NIST (.nist, .nst, .eft, .an2, .int)."
                    )

        event.ignore()

    def _is_supported_file(self, file_path: str) -> bool:
        """Check if dropped file has a supported NIST extension."""
        return file_path.lower().endswith(('.nist', '.nst', '.eft', '.an2', '.int'))

    def open_file(self):
        """Open NIST file dialog and load file."""
        if not self._confirm_discard_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un fichier NIST",
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
        self.status_bar.showMessage(f"Chargement de {file_path}...")

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
            self.status_bar.showMessage(f"Fichier chargé : {file_path}", 5000)
            self.update_actions_state(True)

            logger.info(f"Successfully loaded: {file_path}")

            # Update recents and navigation state
            record_types = nist_file.get_record_types()
            self.recent_files.add(file_path, last_mode="viewer", summary_types=record_types)
            self.refresh_recent_entries()
            self.home_view.set_current_file(file_path, "viewer")
            self.pdf_view.set_current_file(file_path)
            self._update_viewer_file_label(file_path)
            self.is_modified = False
            self.last_change = None
            self._refresh_title()
            self.switch_to_viewer()
        else:
            # Show error
            details = self.file_controller.format_last_error()
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de charger le fichier NIST :\n{file_path}\n\n{details}"
            )
            self.status_bar.showMessage("Échec du chargement", 5000)
            self.update_actions_state(self.file_controller.is_file_open())
            logger.error(f"Failed to load: {file_path} ({details})")

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
        self.status_bar.showMessage(f"Affichage du record Type-{record_type} (IDC {idc})")

    def export_signa_multiple(self):
        """Export NIST file with Signa Multiple modifications."""
        # Check if file is loaded
        if not self.file_controller.is_file_open():
            QMessageBox.warning(
                self,
                "Aucun fichier",
                "Merci d'ouvrir un fichier NIST avant d'exporter."
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
            self.status_bar.showMessage(f"Export en cours vers {output_path}...")

            # Get current NIST file
            nist_file = self.file_controller.get_current_file()

            # Export with modifications
            success = self.export_controller.export_signa_multiple(nist_file, output_path)

            if success:
                QMessageBox.information(
                    self,
                    "Export réussi",
                    f"Export effectué vers :\n{output_path}\n\n"
                    "Modifications appliquées :\n"
                    "- Suppression du champ 2.215\n"
                    "- Champ 2.217 = '11707'"
                )
                self.status_bar.showMessage(f"Exporté : {output_path}", 5000)
                logger.info(f"Export Signa Multiple successful: {output_path}")
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Échec de l'export vers :\n{output_path}\n\n"
                    "Consultez les logs pour plus de détails."
                )
                self.status_bar.showMessage("Export en échec", 5000)
                logger.error(f"Export Signa Multiple failed: {output_path}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"A propos de {APP_NAME}",
            f"<h2>{APP_NAME} {APP_VERSION}</h2>"
            "<p>Suite d'outils biometriques NIST</p>"
            "<p><b>Outils integres :</b></p>"
            "<ul>"
            "<li><b>NIST-Viewer</b> : Visualisation et edition de fichiers ANSI/NIST-ITL</li>"
            "<li><b>NIST-Compare</b> : Comparaison cote a cote d'images biometriques</li>"
            "<li><b>NIST-2-PDF</b> : Export de releves decadactylaires PDF</li>"
            "<li><b>Image-2-NIST</b> : Conversion d'images en fichiers NIST (a venir)</li>"
            "</ul>"
            "<p>Motorise par nistitl (Idemia) et PyQt5</p>"
        )

    def show_export_info(self):
        """Show Export Signa Multiple information."""
        info_text = self.export_controller.get_export_info()

        QMessageBox.information(
            self,
            "Informations Export Signa Multiple",
            info_text
        )

    def closeEvent(self, event):
        """
        Handle window close event.

        Args:
            event: Close event
        """
        if not self._confirm_discard_changes():
            event.ignore()
            return
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

    def switch_to_pdf_view(self):
        """Show PDF export view."""
        self.active_mode = "pdf"
        self.last_non_home_mode = "pdf"
        self.stacked_widget.setCurrentIndex(2)
        self.status_bar.showMessage("Export PDF", 3000)

    def switch_to_comparison(self):
        """Show comparison view."""
        self.active_mode = "comparison"
        self.last_non_home_mode = "comparison"
        self.stacked_widget.setCurrentIndex(3)
        self.status_bar.showMessage("NIST-Compare", 3000)

    def switch_to_image2nist(self):
        """Show Image-2-NIST view (placeholder)."""
        self.active_mode = "image2nist"
        self.stacked_widget.setCurrentIndex(4)
        self.status_bar.showMessage("Image-2-NIST (en developpement)", 3000)

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

        if not self._confirm_discard_changes():
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
            self.switch_to_comparison()
        elif mode == "pdf":
            self.switch_to_pdf_view()
        elif mode == "image2nist":
            self.switch_to_image2nist()

    def on_resume_last_mode(self):
        """Resume last non-home mode when a file is open."""
        if not self.file_controller.is_file_open():
            QMessageBox.information(self, "Aucun fichier", "Ouvrez un fichier pour reprendre la navigation.")
            return
        if self.last_non_home_mode == "viewer":
            self.switch_to_viewer()
        elif self.last_non_home_mode == "comparison":
            self.switch_to_comparison()
        elif self.last_non_home_mode == "pdf":
            self.switch_to_pdf_view()
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

    def on_field_changed(self, record_type: int, idc: int, field_key: str, old: str, new: str):
        """Mark state dirty after an edit in DataPanel."""
        self.is_modified = True
        field_num = int(field_key.split(".")[1])
        self.last_change = {
            "record_type": record_type,
            "idc": idc,
            "field_num": field_num,
            "old": old,
            "new": new,
        }
        self.undo_action.setEnabled(True)
        self.save_action.setEnabled(True)
        self._refresh_title()
        self.status_bar.showMessage(f"Modifié: {field_key} → {new}", 4000)

    def undo_last_change(self):
        """Undo the last single change."""
        if not self.last_change or not self.file_controller.is_file_open():
            QMessageBox.information(self, "Annuler", "Aucune modification à annuler.")
            return

        change = self.last_change
        nist_file = self.file_controller.get_current_file()
        if not nist_file:
            return

        record_type = change["record_type"]
        idc = change["idc"]
        field_num = change["field_num"]
        old = change["old"]

        if old == "":
            nist_file.delete_field(record_type, field_num, idc=idc)
        else:
            nist_file.modify_field(record_type, field_num, old, idc=idc)

        # Refresh current view
        self.data_panel.display_record(record_type, idc)
        self.is_modified = False
        self.last_change = None
        self.undo_action.setEnabled(False)
        self.save_action.setEnabled(False)
        self._refresh_title()
        self.status_bar.showMessage("Dernier changement annulé", 3000)

    def save_file_as(self):
        """Save current file to a new path."""
        if not self.file_controller.is_file_open():
            QMessageBox.information(self, "Aucun fichier", "Ouvrez un fichier avant d'enregistrer.")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer sous",
            "",
            NIST_FILE_FILTER
        )
        if not output_path:
            return

        current_file = self.file_controller.get_current_file()
        if not current_file:
            return

        success = current_file.export(output_path)
        if success:
            self.is_modified = False
            self.last_change = None
            self._refresh_title()
            self.status_bar.showMessage(f"Enregistré: {output_path}", 4000)
            self.recent_files.add(output_path, last_mode="viewer", summary_types=current_file.get_record_types())
            self.refresh_recent_entries()
        else:
            QMessageBox.critical(self, "Erreur", "Impossible d'enregistrer le fichier.")

    def export_pdf_report(self):
        """Exporte un relevé PDF décadactylaire."""
        if not self.file_controller.is_file_open():
            QMessageBox.information(self, "Aucun fichier", "Ouvrez un fichier avant d'exporter.")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter le relevé PDF",
            "",
            "PDF (*.pdf);;Tous les fichiers (*)"
        )
        if not output_path:
            return

        nist_file = self.file_controller.get_current_file()
        if not nist_file:
            return

        self._perform_pdf_export(output_path, nist_file)

    def export_pdf_report_with_path(self, output_path: str):
        """Exporte vers un chemin fourni (depuis la vue PDF)."""
        if not output_path:
            QMessageBox.information(self, "Chemin manquant", "Indiquez un chemin de sortie pour le PDF.")
            return
        if not output_path.lower().endswith(".pdf"):
            output_path = f"{output_path}.pdf"

        if not self.file_controller.is_file_open():
            QMessageBox.information(self, "Aucun fichier", "Ouvrez un fichier avant d'exporter.")
            return

        nist_file = self.file_controller.get_current_file()
        if not nist_file:
            return

        self._perform_pdf_export(output_path, nist_file)

    def _perform_pdf_export(self, output_path: str, nist_file):
        """Mutualise l'export PDF et l'affichage de statut."""
        ok, message = self.pdf_controller.export_dacty_pdf(nist_file, output_path)
        if ok:
            QMessageBox.information(
                self,
                "PDF exporté",
                f"Relevé PDF généré :\n{output_path}"
            )
            self.status_bar.showMessage(f"PDF exporté : {output_path}", 4000)
        else:
            QMessageBox.critical(
                self,
                "Erreur PDF",
                message or "Échec de la génération du PDF."
            )
            self.status_bar.showMessage("Échec export PDF", 4000)

    def _confirm_discard_changes(self) -> bool:
        """Prompt user if there are unsaved changes."""
        if not self.is_modified:
            return True

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Modifications non sauvegardées")
        msg.setText("Des modifications Type-2 ne sont pas enregistrées.")
        save_btn = msg.addButton("Enregistrer", QMessageBox.AcceptRole)
        discard_btn = msg.addButton("Fermer sans enregistrer", QMessageBox.DestructiveRole)
        cancel_btn = msg.addButton("Annuler", QMessageBox.RejectRole)
        msg.setDefaultButton(save_btn)
        msg.exec_()

        clicked = msg.clickedButton()
        if clicked == save_btn:
            self.save_file_as()
            return not self.is_modified
        if clicked == discard_btn:
            return True
        return False

    def _refresh_title(self):
        """Update window title with modified marker and file name."""
        current_path = self.file_controller.current_filepath if self.file_controller else None
        suffix = " *" if self.is_modified else ""
        if current_path:
            self.setWindowTitle(f"{APP_NAME} - {current_path}{suffix}")
        else:
            self.setWindowTitle(self.base_title + suffix)
