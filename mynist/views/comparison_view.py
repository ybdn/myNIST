"""Vue de comparaison côte à côte (NIST/Image/PDF) avec calibration DPI enrichie."""

import math
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import io

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage, QPen, QBrush, QColor, QPainter, QIcon
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QFrame,
    QPushButton,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QSlider,
    QFileDialog,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
    QToolBar,
    QActionGroup,
    QAction,
    QMessageBox,
    QInputDialog,
    QTabWidget,
    QSplitter,
)
from PIL import Image, ImageEnhance, ImageOps

from mynist.models.nist_file import NISTFile
from mynist.utils.image_tools import locate_image_payload, detect_image_format, exif_transpose
from mynist.utils.image_codecs import decode_wsq, decode_jpeg2000


# Constantes pour les annotations typées
ANNOTATION_RADIUS = 10
ANNOTATION_PEN_WIDTH = 2
ANNOTATION_TYPES = {
    "MINUTIA": {"color": QColor(220, 38, 38), "prefix": "N"},
    "MATCH": {"color": QColor(22, 163, 74), "prefix": "M"},
    "EXCLUSION": {"color": QColor(234, 179, 8), "prefix": "E"},
    "CUSTOM": {"color": QColor(37, 99, 235), "prefix": "C"},
}

# Constantes pour les points de calibration
CALIBRATION_COLOR = QColor(0, 128, 255)  # Bleu
CALIBRATION_RADIUS = 6


class AnnotationPoint(QGraphicsEllipseItem):
    """Point d'annotation typé avec label centré."""

    def __init__(self, x: float, y: float, annotation_type: str, label: str, parent=None):
        super().__init__(
            x - ANNOTATION_RADIUS,
            y - ANNOTATION_RADIUS,
            ANNOTATION_RADIUS * 2,
            ANNOTATION_RADIUS * 2,
            parent
        )
        self._center_x = x
        self._center_y = y
        self.annotation_type = annotation_type
        self.label = label

        color = ANNOTATION_TYPES.get(annotation_type, ANNOTATION_TYPES["MINUTIA"])["color"]
        pen = QPen(color)
        pen.setWidth(ANNOTATION_PEN_WIDTH)
        self.setPen(pen)
        self.setBrush(QBrush(Qt.transparent))

        self.text_item = QGraphicsSimpleTextItem(label, self)
        self.text_item.setBrush(QBrush(color))
        self.text_item.setZValue(self.zValue() + 1)
        self._update_text_position()

        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(100)

    @property
    def center(self) -> Tuple[float, float]:
        return (self._center_x, self._center_y)

    def set_center(self, x: float, y: float):
        """Met à jour le centre et la position graphique."""
        self._center_x = x
        self._center_y = y
        self.setRect(
            x - ANNOTATION_RADIUS,
            y - ANNOTATION_RADIUS,
            ANNOTATION_RADIUS * 2,
            ANNOTATION_RADIUS * 2,
        )
        self._update_text_position()

    def contains_point(self, x: float, y: float, tolerance: float = 5) -> bool:
        dx = x - self._center_x
        dy = y - self._center_y
        return (dx * dx + dy * dy) <= (ANNOTATION_RADIUS + tolerance) ** 2

    def _update_text_position(self):
        rect = self.rect()
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            rect.x() + (rect.width() - text_rect.width()) / 2,
            rect.y() + (rect.height() - text_rect.height()) / 2,
        )


class CalibrationPoint(QGraphicsEllipseItem):
    """Point de calibration : cercle bleu plein."""

    def __init__(self, x: float, y: float, parent=None):
        super().__init__(
            x - CALIBRATION_RADIUS,
            y - CALIBRATION_RADIUS,
            CALIBRATION_RADIUS * 2,
            CALIBRATION_RADIUS * 2,
            parent
        )
        self._center_x = x
        self._center_y = y

        pen = QPen(CALIBRATION_COLOR)
        pen.setWidth(2)
        self.setPen(pen)
        self.setBrush(QBrush(CALIBRATION_COLOR))
        self.setZValue(101)

    @property
    def center(self) -> Tuple[float, float]:
        return (self._center_x, self._center_y)


class MeasurementLine(QGraphicsLineItem):
    """Segment de mesure avec label centré."""

    def __init__(self, x1: float, y1: float, x2: float, y2: float, text: str, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        pen = QPen(QColor(80, 80, 80))
        pen.setWidth(2)
        self.setPen(pen)
        self.setZValue(90)
        self.label_item = QGraphicsSimpleTextItem(text, self)
        self.label_item.setBrush(QBrush(QColor(60, 60, 60)))
        self._update_label_position()

    def update_geometry(self, x1: float, y1: float, x2: float, y2: float, text: str):
        self.setLine(x1, y1, x2, y2)
        self.label_item.setText(text)
        self._update_label_position()

    def _update_label_position(self):
        line = self.line()
        mid_x = (line.x1() + line.x2()) / 2
        mid_y = (line.y1() + line.y2()) / 2
        text_rect = self.label_item.boundingRect()
        self.label_item.setPos(mid_x - text_rect.width() / 2, mid_y - text_rect.height() / 2)


class AnnotatableView(QGraphicsView):
    """QGraphicsView avec zoom/pan, annotations typées, mesures et calibration."""

    annotations_changed = pyqtSignal()
    calibration_point_added = pyqtSignal(float, float)  # x, y en coordonnées scène
    measurement_completed = pyqtSignal(float, float, float, float)  # start_x, start_y, end_x, end_y
    zoom_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._zoom_factor = 1.0
        self._block_zoom_signal = False
        self._annotation_mode = False
        self._calibration_mode = False
        self._measurement_mode = False
        self._measurement_start: Optional[Tuple[float, float]] = None
        self._annotations: List[AnnotationPoint] = []
        self._annotations_visible = True
        self._type_counters: Dict[str, int] = {k: 0 for k in ANNOTATION_TYPES.keys()}
        self._current_annotation_type = "MINUTIA"
        self._measurements: List[MeasurementLine] = []

    # --- Zoom / Pan ---

    def wheelEvent(self, event):
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self._zoom_factor *= factor
        self.scale(factor, factor)
        if not self._block_zoom_signal:
            self.zoom_changed.emit(self._zoom_factor)

    def apply_zoom_ratio(self, ratio: float):
        """Applique un zoom relatif sans réémettre de signal."""
        if ratio <= 0:
            return
        self._block_zoom_signal = True
        self._zoom_factor *= ratio
        self.scale(ratio, ratio)
        self._block_zoom_signal = False

    def reset_zoom(self):
        self.resetTransform()
        self._zoom_factor = 1.0

    # --- Modes ---

    def _reset_modes(self):
        self._annotation_mode = False
        self._calibration_mode = False
        self._measurement_mode = False
        self._measurement_start = None
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setCursor(Qt.ArrowCursor)
        self.viewport().setCursor(Qt.ArrowCursor)

    def set_annotation_mode(self, enabled: bool):
        self._reset_modes()
        if enabled:
            self._annotation_mode = True
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
            self.viewport().setCursor(Qt.CrossCursor)

    def set_calibration_mode(self, enabled: bool):
        self._reset_modes()
        if enabled:
            self._calibration_mode = True
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
            self.viewport().setCursor(Qt.CrossCursor)

    def set_measurement_mode(self, enabled: bool):
        self._reset_modes()
        if enabled:
            self._measurement_mode = True
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
            self.viewport().setCursor(Qt.CrossCursor)

    def is_annotation_mode(self) -> bool:
        return self._annotation_mode

    def is_calibration_mode(self) -> bool:
        return self._calibration_mode

    def is_measurement_mode(self) -> bool:
        return self._measurement_mode

    # --- Annotations ---

    def set_annotation_type(self, annotation_type: str):
        if annotation_type in ANNOTATION_TYPES:
            self._current_annotation_type = annotation_type

    def _next_label_for_type(self, annotation_type: str) -> str:
        prefix = ANNOTATION_TYPES.get(annotation_type, ANNOTATION_TYPES["MINUTIA"])["prefix"]
        self._type_counters[annotation_type] += 1
        return f"{prefix}{self._type_counters[annotation_type]}"

    def _update_counter_from_label(self, annotation_type: str, label: str):
        prefix = ANNOTATION_TYPES.get(annotation_type, ANNOTATION_TYPES["MINUTIA"])["prefix"]
        if label.startswith(prefix):
            try:
                num = int(label[len(prefix):])
                self._type_counters[annotation_type] = max(self._type_counters[annotation_type], num)
            except Exception:
                pass

    def _add_annotation(self, x: float, y: float, annotation_type: Optional[str] = None, label: Optional[str] = None):
        scene = self.scene()
        if scene is None:
            return
        a_type = annotation_type or self._current_annotation_type
        label_to_use = label or self._next_label_for_type(a_type)
        if label:
            self._update_counter_from_label(a_type, label)
        point = AnnotationPoint(x, y, a_type, label_to_use)
        point.setVisible(self._annotations_visible)
        scene.addItem(point)
        self._annotations.append(point)
        self.annotations_changed.emit()

    def _remove_annotation(self, point: AnnotationPoint):
        scene = self.scene()
        if scene is None:
            return
        scene.removeItem(point)
        self._annotations.remove(point)
        self.annotations_changed.emit()

    def clear_annotations(self):
        scene = self.scene()
        if scene is None:
            return
        for point in self._annotations[:]:
            scene.removeItem(point)
        self._annotations.clear()
        self._type_counters = {k: 0 for k in ANNOTATION_TYPES.keys()}
        self.annotations_changed.emit()

    def set_annotations_visible(self, visible: bool):
        self._annotations_visible = visible
        for point in self._annotations:
            point.setVisible(visible)

    def are_annotations_visible(self) -> bool:
        return self._annotations_visible

    def annotation_count(self) -> int:
        return len(self._annotations)

    def get_annotations(self) -> List[Tuple[float, float]]:
        return [point.center for point in self._annotations]

    def get_annotation_meta(self) -> List[Dict[str, object]]:
        """Retourne les annotations avec type/label pour conserver l'état après rotation."""
        meta = []
        for point in self._annotations:
            meta.append({
                "x": point.center[0],
                "y": point.center[1],
                "type": point.annotation_type,
                "label": point.label,
            })
        return meta

    def rebuild_annotations(self, meta: List[Dict[str, object]]):
        self.clear_annotations()
        for entry in meta:
            self._add_annotation(
                entry.get("x", 0),
                entry.get("y", 0),
                annotation_type=entry.get("type", "MINUTIA"),
                label=entry.get("label"),
            )

    def get_annotation_stats(self) -> Dict[str, int]:
        stats = {k: 0 for k in ANNOTATION_TYPES.keys()}
        for p in self._annotations:
            stats[p.annotation_type] = stats.get(p.annotation_type, 0) + 1
        return stats

    # --- Mesures ---

    def add_measurement(self, start: Tuple[float, float], end: Tuple[float, float], text: str):
        scene = self.scene()
        if scene is None:
            return
        line = MeasurementLine(start[0], start[1], end[0], end[1], text)
        scene.addItem(line)
        self._measurements.append(line)

    def clear_measurements(self):
        scene = self.scene()
        if scene is None:
            return
        for line in self._measurements[:]:
            scene.removeItem(line)
        self._measurements.clear()
        self._measurement_start = None

    def remove_last_measurement(self):
        if not self._measurements:
            return
        scene = self.scene()
        if scene is None:
            return
        last = self._measurements.pop()
        if last.scene():
            scene.removeItem(last)

    def get_measurement_meta(self) -> List[Dict[str, object]]:
        meta = []
        for line in self._measurements:
            l = line.line()
            meta.append({
                "start": (l.x1(), l.y1()),
                "end": (l.x2(), l.y2()),
                "text": line.label_item.text(),
            })
        return meta

    # --- Events ---

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())

        if self._measurement_mode and event.button() == Qt.RightButton:
            self.remove_last_measurement()
            return

        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        if self._calibration_mode:
            self.calibration_point_added.emit(scene_pos.x(), scene_pos.y())
            return

        if self._measurement_mode:
            if self._measurement_start is None:
                self._measurement_start = (scene_pos.x(), scene_pos.y())
            else:
                self.measurement_completed.emit(
                    self._measurement_start[0],
                    self._measurement_start[1],
                    scene_pos.x(),
                    scene_pos.y(),
                )
                self._measurement_start = None
            return

        if self._annotation_mode:
            x, y = scene_pos.x(), scene_pos.y()
            for point in self._annotations[:]:
                if point.contains_point(x, y):
                    self._remove_annotation(point)
                    return
            self._add_annotation(x, y)
            return

        super().mousePressEvent(event)


class ComparisonView(QWidget):
    """Vue de comparaison côte à côte avec calibration DPI et rééchantillonnage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # État des images (PIL originales + DPI calibré)
        self.image_state = {
            "left": {"base_image": None, "dpi": None, "rotation": 0, "enhancements": self._default_enhancements()},
            "right": {"base_image": None, "dpi": None, "rotation": 0, "enhancements": self._default_enhancements()},
        }
        # Points de calibration temporaires
        self.calibration_points: List[Tuple[float, float]] = []
        self.calibration_items: List[QGraphicsEllipseItem] = []
        self.calibration_line: Optional[QGraphicsLineItem] = None
        self.active_calibration_side: Optional[str] = None

        self.left_pixmap_item = None
        self.right_pixmap_item = None
        self.views_linked = False
        self._syncing_pan = False
        self.module_frame = None
        self._icon_cache: Dict[str, QIcon] = {}

        self._build_ui()
        self._connect_signals()

    def _default_enhancements(self) -> Dict[str, float]:
        """Valeurs par défaut pour les filtres d'amélioration."""
        return {"brightness": 0.0, "contrast": 1.0, "gamma": 1.0, "invert": False}

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Toolbar actions + outils
        self._build_annotation_toolbar(layout)

        # Vues côte à côte + module latéral intégré à droite
        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(8)

        # Colonne gauche
        self.left_label = QLabel("Aucune image chargée (gauche)")
        self.left_label.setStyleSheet("background: rgba(0,0,0,0.04); padding: 4px 8px; border-radius: 6px;")
        self.left_view = AnnotatableView()
        self.left_scene = QGraphicsScene()
        self.left_view.setScene(self.left_scene)
        left_box = QVBoxLayout()
        left_box.setContentsMargins(0, 0, 0, 0)
        left_box.setSpacing(4)
        left_header = QHBoxLayout()
        self.left_import_btn = QPushButton("Importer gauche")
        self.left_import_btn.clicked.connect(lambda: self._browse_and_load("left"))
        left_header.addWidget(self.left_import_btn)
        left_header.addWidget(self.left_label)
        left_box.addLayout(left_header)
        left_box.addWidget(self.left_view)
        main_row.addLayout(left_box, 5)

        # Colonne droite avec module à droite de l'image
        self.right_label = QLabel("Aucune image chargée (droite)")
        self.right_label.setStyleSheet("background: rgba(0,0,0,0.04); padding: 4px 8px; border-radius: 6px;")
        self.right_view = AnnotatableView()
        self.right_scene = QGraphicsScene()
        self.right_view.setScene(self.right_scene)

        right_inner = QHBoxLayout()
        right_inner.setContentsMargins(0, 0, 0, 0)
        right_inner.setSpacing(8)

        right_image_col = QVBoxLayout()
        right_image_col.setContentsMargins(0, 0, 0, 0)
        right_image_col.setSpacing(4)
        right_header = QHBoxLayout()
        self.right_import_btn = QPushButton("Importer droite")
        self.right_import_btn.clicked.connect(lambda: self._browse_and_load("right"))
        right_header.addWidget(self.right_import_btn)
        right_header.addWidget(self.right_label)
        right_image_col.addLayout(right_header)
        right_image_col.addWidget(self.right_view)

        # Module calibrate/resample + amélioration à droite de l'image
        self.module_frame = QWidget()
        self.module_frame.setMinimumWidth(260)
        mod_layout = QVBoxLayout()
        mod_layout.setContentsMargins(6, 6, 6, 6)
        mod_layout.setSpacing(8)
        mod_tabs = QTabWidget()
        mod_tabs.addTab(self._build_calibration_panel(), "Calibrate / Resample")
        mod_tabs.addTab(self._build_enhancement_panel(), "Amélioration")
        mod_layout.addWidget(mod_tabs)
        self.module_frame.setLayout(mod_layout)

        right_inner.addLayout(right_image_col, 4)
        right_inner.addWidget(self.module_frame, 1)

        main_row.addLayout(right_inner, 5)

        layout.addLayout(main_row)

        # Label compteur
        self.annotation_count_label = QLabel("Annotations : G=0 | D=0")
        layout.addWidget(self.annotation_count_label)

        # Type d'annotation par défaut
        self._on_annotation_type_changed()

        # Assurer la visibilité initiale du module de réglages
        self._on_toggle_side_panel(self.toggle_side_panel_action.isChecked())

        self.setLayout(layout)

    def _build_annotation_toolbar(self, layout: QVBoxLayout):
        toolbar = QToolBar("Annotations")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(28, 28))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setStyleSheet("QToolBar { spacing: 6px; }")

        # Groupe exclusif pour les modes (pan / annoter / mesurer)
        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)

        self.pan_action = QAction("Main", self)
        self.pan_action.setCheckable(True)
        self.pan_action.setChecked(True)
        self.pan_action.setToolTip("Mode déplacement")
        self._set_icon(self.pan_action, "pan")
        self.pan_action.toggled.connect(self._on_pan_toggled)
        mode_group.addAction(self.pan_action)
        toolbar.addAction(self.pan_action)

        self.annotate_action = QAction("Annoter", self)
        self.annotate_action.setCheckable(True)
        self.annotate_action.setToolTip("Mode annotation (clic = ajouter, clic sur point = supprimer)")
        self._set_icon(self.annotate_action, "annotate")
        self.annotate_action.toggled.connect(self._on_annotate_toggled)
        mode_group.addAction(self.annotate_action)
        toolbar.addAction(self.annotate_action)

        self.measure_action = QAction("Mesurer", self)
        self.measure_action.setCheckable(True)
        self.measure_action.setToolTip("Mode mesure : 2 clics = distance, clic droit = supprimer la dernière")
        self._set_icon(self.measure_action, "measure")
        self.measure_action.toggled.connect(self._on_measure_toggled)
        mode_group.addAction(self.measure_action)
        toolbar.addAction(self.measure_action)

        toolbar.addSeparator()

        clear_left_action = QAction("Effacer G", self)
        self._set_icon(clear_left_action, "clear_left")
        clear_left_action.triggered.connect(lambda: self._clear_annotations("left"))
        toolbar.addAction(clear_left_action)

        clear_right_action = QAction("Effacer D", self)
        self._set_icon(clear_right_action, "clear_right")
        clear_right_action.triggered.connect(lambda: self._clear_annotations("right"))
        toolbar.addAction(clear_right_action)

        clear_all_action = QAction("Tout effacer", self)
        self._set_icon(clear_all_action, "clear_all")
        clear_all_action.triggered.connect(self._clear_all_annotations)
        toolbar.addAction(clear_all_action)

        clear_measures_action = QAction("Effacer mesures", self)
        self._set_icon(clear_measures_action, "measure_clear")
        clear_measures_action.triggered.connect(self._clear_measurements)
        toolbar.addAction(clear_measures_action)

        toolbar.addSeparator()

        self.visibility_action = QAction("Masquer", self)
        self.visibility_action.setCheckable(True)
        self.visibility_action.toggled.connect(self._on_visibility_toggled)
        self._set_icon(self.visibility_action, "visibility")
        toolbar.addAction(self.visibility_action)

        toolbar.addSeparator()

        # Type d'annotation
        toolbar.addWidget(QLabel("Type :"))
        self.annotation_type_combo = QComboBox()
        for key in ANNOTATION_TYPES.keys():
            self.annotation_type_combo.addItem(key.title(), key)
        self.annotation_type_combo.currentIndexChanged.connect(self._on_annotation_type_changed)
        toolbar.addWidget(self.annotation_type_combo)

        toolbar.addSeparator()

        self.link_views_action = QAction("Lier les vues", self)
        self.link_views_action.setCheckable(True)
        self.link_views_action.setToolTip("Synchroniser zoom/pan entre gauche et droite")
        self._set_icon(self.link_views_action, "link")
        self.link_views_action.toggled.connect(self._on_link_views_toggled)
        toolbar.addAction(self.link_views_action)

        self.toggle_side_panel_action = QAction("Réglages", self)
        self.toggle_side_panel_action.setCheckable(True)
        self.toggle_side_panel_action.setChecked(True)
        self.toggle_side_panel_action.setToolTip("Afficher/masquer les panneaux Calibration/Amélioration")
        self._set_icon(self.toggle_side_panel_action, "tune")
        self.toggle_side_panel_action.toggled.connect(self._on_toggle_side_panel)
        toolbar.addAction(self.toggle_side_panel_action)

        self.reset_zoom_action = QAction("Reset zoom", self)
        self._set_icon(self.reset_zoom_action, "reset_zoom")
        self.reset_zoom_action.triggered.connect(self.reset_zoom)
        toolbar.addAction(self.reset_zoom_action)

        export_action = QAction("Exporter JPG", self)
        self._set_icon(export_action, "export")
        export_action.triggered.connect(self._export_comparison)
        toolbar.addAction(export_action)

        layout.addWidget(toolbar)

    def _build_calibration_panel(self) -> QWidget:
        """Panneau de calibration DPI et rééchantillonnage."""
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Carte gauche
        main_layout.addWidget(self._build_calib_card("left", "Image gauche"))
        # Carte droite
        main_layout.addWidget(self._build_calib_card("right", "Image droite"))

        # Rotation (commune)
        rot_group = QGroupBox("Rotation")
        rot_layout = QVBoxLayout()
        rot_layout.setContentsMargins(8, 6, 8, 6)
        rot_layout.setSpacing(6)

        rot_left_row = QHBoxLayout()
        rot_left_row.addWidget(QLabel("Gauche"))
        btn_l_cw = QPushButton("↻ 90°")
        btn_l_cw.clicked.connect(lambda: self._rotate_image("left", 90))
        rot_left_row.addWidget(btn_l_cw)
        btn_l_ccw = QPushButton("↺ 90°")
        btn_l_ccw.clicked.connect(lambda: self._rotate_image("left", -90))
        rot_left_row.addWidget(btn_l_ccw)
        btn_l_reset = QPushButton("Reset")
        btn_l_reset.clicked.connect(lambda: self._reset_rotation("left"))
        rot_left_row.addWidget(btn_l_reset)
        rot_layout.addLayout(rot_left_row)

        rot_right_row = QHBoxLayout()
        rot_right_row.addWidget(QLabel("Droite"))
        btn_r_cw = QPushButton("↻ 90°")
        btn_r_cw.clicked.connect(lambda: self._rotate_image("right", 90))
        rot_right_row.addWidget(btn_r_cw)
        btn_r_ccw = QPushButton("↺ 90°")
        btn_r_ccw.clicked.connect(lambda: self._rotate_image("right", -90))
        rot_right_row.addWidget(btn_r_ccw)
        btn_r_reset = QPushButton("Reset")
        btn_r_reset.clicked.connect(lambda: self._reset_rotation("right"))
        rot_right_row.addWidget(btn_r_reset)
        rot_layout.addLayout(rot_right_row)

        rot_group.setLayout(rot_layout)
        main_layout.addWidget(rot_group)

        widget.setLayout(main_layout)
        return widget

    def _build_calib_card(self, side: str, title: str) -> QWidget:
        """Carte visuelle combinant calibrage et rééchantillonnage pour un côté."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(
            """
            QFrame {
                border: 1px solid rgba(128,128,128,0.25);
                border-radius: 10px;
                background: transparent;
            }
            """
        )
        outer = QVBoxLayout()
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)
        outer.addWidget(QLabel(f"<b>{title}</b>"))

        # Ligne Calibrate / Resample côte à côte
        row = QHBoxLayout()
        row.setSpacing(10)

        # Bloc Calibrate
        calib_box = QVBoxLayout()
        calib_box.setSpacing(6)
        dpi_label = QLabel("DPI : Non calibré")
        if side == "left":
            self.left_dpi_label = dpi_label
        else:
            self.right_dpi_label = dpi_label
        calib_box.addWidget(dpi_label)

        calib_btn = QPushButton("Calibrer (2 points)")
        calib_btn.setToolTip("Cliquez 2 points sur l'image et entrez la distance réelle en mm")
        calib_btn.clicked.connect(lambda: self._start_calibration(side))
        calib_box.addWidget(calib_btn)

        # Bloc Resample
        res_box = QVBoxLayout()
        res_box.setSpacing(6)
        target = QSpinBox()
        target.setRange(72, 1200)
        target.setValue(500)
        target.setSuffix(" DPI")
        if side == "left":
            self.left_target_dpi = target
        else:
            self.right_target_dpi = target
        res_btn = QPushButton("Rééchantillonner")
        res_btn.setToolTip("Convertir l'image au DPI cible")
        res_btn.clicked.connect(lambda: self._resample_image(side))
        res_box.addWidget(target)
        res_box.addWidget(res_btn)

        row.addLayout(calib_box)
        row.addLayout(res_box)
        row.addStretch()
        outer.addLayout(row)

        frame.setLayout(outer)
        return frame

    def _build_enhancement_panel(self) -> QWidget:
        """Panneau d'amélioration d'image (luminosité, contraste, gamma, inversion)."""
        group = QGroupBox("Amélioration d'image")
        group_layout = QHBoxLayout()
        group_layout.setContentsMargins(8, 6, 8, 6)
        group_layout.setSpacing(20)

        self.enhance_controls = {"left": {}, "right": {}}

        for side, title in (("left", "Image gauche"), ("right", "Image droite")):
            box = QVBoxLayout()
            box.addWidget(QLabel(f"<b>{title}</b>"))

            # Luminosité
            bright_slider = QSlider(Qt.Horizontal)
            bright_slider.setRange(-100, 100)
            bright_slider.setValue(0)
            bright_slider.setToolTip("Luminosité (-100 à +100)")
            bright_slider.valueChanged.connect(lambda _v, s=side: self._on_enhancement_changed(s))
            box.addWidget(QLabel("Luminosité"))
            box.addWidget(bright_slider)

            # Contraste
            contrast_slider = QSlider(Qt.Horizontal)
            contrast_slider.setRange(50, 200)  # 0.5 à 2.0
            contrast_slider.setValue(100)
            contrast_slider.setToolTip("Contraste (0.5 à 2.0)")
            contrast_slider.valueChanged.connect(lambda _v, s=side: self._on_enhancement_changed(s))
            box.addWidget(QLabel("Contraste"))
            box.addWidget(contrast_slider)

            # Gamma
            gamma_slider = QSlider(Qt.Horizontal)
            gamma_slider.setRange(50, 200)  # 0.5 à 2.0
            gamma_slider.setValue(100)
            gamma_slider.setToolTip("Gamma (0.5 à 2.0)")
            gamma_slider.valueChanged.connect(lambda _v, s=side: self._on_enhancement_changed(s))
            box.addWidget(QLabel("Gamma"))
            box.addWidget(gamma_slider)

            invert_btn = QPushButton("Inverser (négatif)")
            invert_btn.setCheckable(True)
            invert_btn.clicked.connect(lambda _checked, s=side: self._on_enhancement_changed(s))
            box.addWidget(invert_btn)

            reset_btn = QPushButton("Réinitialiser")
            reset_btn.clicked.connect(lambda _checked=False, s=side: self._reset_enhancements(s))
            box.addWidget(reset_btn)

            self.enhance_controls[side] = {
                "brightness": bright_slider,
                "contrast": contrast_slider,
                "gamma": gamma_slider,
                "invert": invert_btn,
            }

            group_layout.addLayout(box)

        group_layout.addStretch()
        group.setLayout(group_layout)
        return group

    def _connect_signals(self):
        self.left_view.annotations_changed.connect(self._update_annotation_count)
        self.right_view.annotations_changed.connect(self._update_annotation_count)
        self.left_view.calibration_point_added.connect(
            lambda x, y: self._on_calibration_point("left", x, y)
        )
        self.right_view.calibration_point_added.connect(
            lambda x, y: self._on_calibration_point("right", x, y)
        )
        self.left_view.measurement_completed.connect(
            lambda x1, y1, x2, y2: self._on_measurement_completed("left", x1, y1, x2, y2)
        )
        self.right_view.measurement_completed.connect(
            lambda x1, y1, x2, y2: self._on_measurement_completed("right", x1, y1, x2, y2)
        )
        self.left_view.zoom_changed.connect(lambda factor: self._on_zoom_changed("left", factor))
        self.right_view.zoom_changed.connect(lambda factor: self._on_zoom_changed("right", factor))
        self.left_view.horizontalScrollBar().valueChanged.connect(
            lambda value: self._on_pan_changed("left", horizontal=True, value=value)
        )
        self.left_view.verticalScrollBar().valueChanged.connect(
            lambda value: self._on_pan_changed("left", horizontal=False, value=value)
        )
        self.right_view.horizontalScrollBar().valueChanged.connect(
            lambda value: self._on_pan_changed("right", horizontal=True, value=value)
        )
        self.right_view.verticalScrollBar().valueChanged.connect(
            lambda value: self._on_pan_changed("right", horizontal=False, value=value)
        )

    # ─────────────────────────────────────────────────────────────────────
    # Calibration DPI
    # ─────────────────────────────────────────────────────────────────────

    def _start_calibration(self, side: str):
        """Démarre le mode calibration pour un côté."""
        state = self.image_state[side]
        base_img = state.get("base_image")
        if base_img is None:
            QMessageBox.warning(self, "Calibration", "Veuillez d'abord charger une image.")
            return

        # Nettoyer calibration précédente
        self._clear_calibration_items(side)
        self.calibration_points = []
        self.active_calibration_side = side

        # Activer le mode calibration sur la vue concernée
        view = self.left_view if side == "left" else self.right_view
        view.set_calibration_mode(True)

        # Désactiver les autres modes
        self.pan_action.blockSignals(True)
        self.pan_action.setChecked(False)
        self.pan_action.blockSignals(False)
        self.annotate_action.blockSignals(True)
        self.annotate_action.setChecked(False)
        self.annotate_action.blockSignals(False)
        self.measure_action.blockSignals(True)
        self.measure_action.setChecked(False)
        self.measure_action.blockSignals(False)

        QMessageBox.information(
            self,
            "Calibration",
            f"Cliquez sur 2 points de l'image {side.upper()} dont vous connaissez la distance réelle."
        )

    def _on_calibration_point(self, side: str, x: float, y: float):
        """Appelé quand un point de calibration est cliqué."""
        if self.active_calibration_side != side:
            return

        scene = self.left_scene if side == "left" else self.right_scene

        # Ajouter le point visuel
        point = CalibrationPoint(x, y)
        scene.addItem(point)
        self.calibration_items.append(point)
        self.calibration_points.append((x, y))

        # Si 2 points, tracer la ligne et demander la distance
        if len(self.calibration_points) == 2:
            p1, p2 = self.calibration_points
            line = QGraphicsLineItem(p1[0], p1[1], p2[0], p2[1])
            pen = QPen(CALIBRATION_COLOR)
            pen.setWidth(2)
            line.setPen(pen)
            line.setZValue(100)
            scene.addItem(line)
            self.calibration_line = line

            # Calculer la distance en pixels
            dist_pixels = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

            # Demander la distance réelle
            dist_mm, ok = QInputDialog.getDouble(
                self,
                "Distance réelle",
                f"Distance en pixels : {dist_pixels:.1f}\n\nEntrez la distance réelle en mm :",
                10.0, 0.1, 1000.0, 2
            )

            if ok and dist_mm > 0:
                # Calculer le DPI : pixels / (mm / 25.4)
                dpi = dist_pixels / (dist_mm / 25.4)
                self.image_state[side]["dpi"] = dpi
                self._update_dpi_label(side)
                # Recalculer l'affichage (texte mesures avec mm)
                self._render_image(side)
                QMessageBox.information(
                    self,
                    "Calibration réussie",
                    f"DPI calculé : {dpi:.1f}"
                )

            # Fin du mode calibration
            self._end_calibration(side)

    def _end_calibration(self, side: str):
        """Termine le mode calibration."""
        view = self.left_view if side == "left" else self.right_view
        view.set_calibration_mode(False)
        self.active_calibration_side = None

        # Nettoyer les items visuels après un délai (ou immédiatement)
        self._clear_calibration_items(side)

        # Revenir au mode pan
        self.pan_action.blockSignals(True)
        self.pan_action.setChecked(True)
        self.pan_action.blockSignals(False)

    def _clear_calibration_items(self, side: str):
        """Supprime les éléments visuels de calibration."""
        scene = self.left_scene if side == "left" else self.right_scene
        for item in self.calibration_items:
            if item.scene() == scene:
                scene.removeItem(item)
        self.calibration_items = [i for i in self.calibration_items if i.scene() is not None]
        if self.calibration_line and self.calibration_line.scene() == scene:
            scene.removeItem(self.calibration_line)
            self.calibration_line = None

    def _update_dpi_label(self, side: str):
        """Met à jour le label DPI."""
        dpi = self.image_state[side]["dpi"]
        label = self.left_dpi_label if side == "left" else self.right_dpi_label
        if dpi:
            label.setText(f"DPI : {dpi:.1f}")
        else:
            label.setText("DPI : Non calibré")

    # ─────────────────────────────────────────────────────────────────────
    # Rendu (rotation + enhancements)
    # ─────────────────────────────────────────────────────────────────────

    def _apply_rotation(self, img: Image.Image, angle: int) -> Image.Image:
        if angle % 360 == 0:
            return img
        return img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

    def _apply_enhancements(self, img: Image.Image, enh: Dict[str, float]) -> Image.Image:
        result = img.convert("RGB")

        # Luminosité : map -100/100 vers facteur 0..2
        bright_factor = 1.0 + float(enh.get("brightness", 0.0)) / 100.0
        result = ImageEnhance.Brightness(result).enhance(max(0.0, bright_factor))

        contrast_factor = float(enh.get("contrast", 1.0))
        result = ImageEnhance.Contrast(result).enhance(max(0.1, contrast_factor))

        gamma = float(enh.get("gamma", 1.0))
        if gamma != 1.0:
            inv_gamma = 1.0 / max(gamma, 1e-6)
            lut = [pow(i / 255.0, inv_gamma) * 255 for i in range(256)]
            lut = [min(255, max(0, int(v))) for v in lut]
            result = result.point(lut * 3)

        if enh.get("invert", False):
            result = ImageOps.invert(result)

        return result

    def _render_image(
        self,
        side: str,
        annotations_meta: Optional[List[Dict[str, object]]] = None,
        measurements_meta: Optional[List[Dict[str, object]]] = None,
    ):
        state = self.image_state[side]
        base = state.get("base_image")
        if base is None:
            return
        view = self.left_view if side == "left" else self.right_view
        if annotations_meta is None:
            annotations_meta = view.get_annotation_meta()
        if measurements_meta is None:
            measurements_meta = view.get_measurement_meta()

        rotated = self._apply_rotation(base, state.get("rotation", 0))
        enhanced = self._apply_enhancements(rotated, state.get("enhancements", self._default_enhancements()))
        self._display_pil_image(side, enhanced, annotations_meta=annotations_meta, measurements_meta=measurements_meta)

    def _reset_enhancements(self, side: str):
        """Réinitialise les sliders et le rendu."""
        defaults = self._default_enhancements()
        enh = self.enhance_controls[side]
        enh["brightness"].blockSignals(True)
        enh["brightness"].setValue(0)
        enh["brightness"].blockSignals(False)
        enh["contrast"].blockSignals(True)
        enh["contrast"].setValue(100)
        enh["contrast"].blockSignals(False)
        enh["gamma"].blockSignals(True)
        enh["gamma"].setValue(100)
        enh["gamma"].blockSignals(False)
        enh["invert"].blockSignals(True)
        enh["invert"].setChecked(False)
        enh["invert"].blockSignals(False)

        self.image_state[side]["enhancements"] = defaults
        self._render_image(side)

    # ─────────────────────────────────────────────────────────────────────
    # Rééchantillonnage
    # ─────────────────────────────────────────────────────────────────────

    def _resample_image(self, side: str):
        """Rééchantillonne l'image au DPI cible."""
        state = self.image_state[side]
        pil_img = state["base_image"]
        current_dpi = state["dpi"]

        if pil_img is None:
            QMessageBox.warning(self, "Rééchantillonnage", "Aucune image chargée.")
            return

        if current_dpi is None:
            QMessageBox.warning(
                self,
                "Rééchantillonnage",
                "Veuillez d'abord calibrer l'image pour déterminer son DPI actuel."
            )
            return

        target_dpi = self.left_target_dpi.value() if side == "left" else self.right_target_dpi.value()

        if abs(target_dpi - current_dpi) < 1:
            QMessageBox.information(self, "Rééchantillonnage", "L'image est déjà au DPI cible.")
            return

        # Calculer le ratio de redimensionnement
        ratio = target_dpi / current_dpi
        new_width = int(pil_img.width * ratio)
        new_height = int(pil_img.height * ratio)

        # Rééchantillonner
        resampled = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Mettre à jour l'état
        state["base_image"] = resampled
        state["dpi"] = target_dpi

        # Mettre à jour annotations + mesures en fonction du ratio
        annotations_meta = self._scale_annotation_meta(side, ratio)
        measurements_meta = self._scale_measurement_meta(side, ratio)

        self._render_image(side, annotations_meta=annotations_meta, measurements_meta=measurements_meta)
        self._update_dpi_label(side)

        QMessageBox.information(
            self,
            "Rééchantillonnage",
            f"Image rééchantillonnée de {current_dpi:.0f} DPI vers {target_dpi} DPI.\n"
            f"Nouvelle taille : {new_width} x {new_height} px"
        )

    def _display_pil_image(
        self,
        side: str,
        pil_img: Image.Image,
        annotations_meta: Optional[List[Dict[str, object]]] = None,
        measurements_meta: Optional[List[Dict[str, object]]] = None,
    ):
        """Affiche une image PIL dans la scène (et restaure annotations/mesures si fournies)."""
        pix = self._pil_to_pixmap(pil_img)
        if side == "left":
            view = self.left_view
            scene = self.left_scene
            self.left_pixmap_item = None
        else:
            view = self.right_view
            scene = self.right_scene
            self.right_pixmap_item = None

        view.clear_annotations()
        view.clear_measurements()
        scene.clear()

        if side == "left":
            self.left_pixmap_item = scene.addPixmap(pix)
        else:
            self.right_pixmap_item = scene.addPixmap(pix)

        if annotations_meta:
            view.rebuild_annotations(annotations_meta)
        if measurements_meta:
            for entry in measurements_meta:
                start = entry.get("start")
                end = entry.get("end")
                if start and end:
                    text = self._measurement_text(side, math.hypot(end[0] - start[0], end[1] - start[1]))
                    view.add_measurement(start, end, text)

        self._update_annotation_count()

    # ─────────────────────────────────────────────────────────────────────
    # Modes toolbar
    # ─────────────────────────────────────────────────────────────────────

    def _on_pan_toggled(self, checked: bool):
        if checked:
            self.left_view.set_annotation_mode(False)
            self.right_view.set_annotation_mode(False)
            self.left_view.set_measurement_mode(False)
            self.right_view.set_measurement_mode(False)
            self.left_view.setCursor(Qt.OpenHandCursor)
            self.left_view.viewport().setCursor(Qt.OpenHandCursor)
            self.right_view.setCursor(Qt.OpenHandCursor)
            self.right_view.viewport().setCursor(Qt.OpenHandCursor)

    def _on_annotate_toggled(self, checked: bool):
        if checked:
            self.left_view.set_annotation_mode(True)
            self.right_view.set_annotation_mode(True)
            self.left_view.set_measurement_mode(False)
            self.right_view.set_measurement_mode(False)
            self.left_view.setCursor(Qt.CrossCursor)
            self.left_view.viewport().setCursor(Qt.CrossCursor)
            self.right_view.setCursor(Qt.CrossCursor)
            self.right_view.viewport().setCursor(Qt.CrossCursor)
        else:
            # si on sort du mode annotation, appliquer le mode actif (mesure ou pan)
            if self.measure_action.isChecked():
                self._on_measure_toggled(True)
            else:
                self._on_pan_toggled(True)

    def _on_visibility_toggled(self, checked: bool):
        visible = not checked
        self.left_view.set_annotations_visible(visible)
        self.right_view.set_annotations_visible(visible)
        self.visibility_action.setText("Afficher" if checked else "Masquer")

    def _clear_annotations(self, side: str):
        if side == "left":
            self.left_view.clear_annotations()
        else:
            self.right_view.clear_annotations()

    def _clear_all_annotations(self):
        self.left_view.clear_annotations()
        self.right_view.clear_annotations()

    def _update_annotation_count(self):
        left_stats = self.left_view.get_annotation_stats()
        right_stats = self.right_view.get_annotation_stats()

        def fmt(stats: Dict[str, int]) -> str:
            parts = []
            for key in ("MATCH", "EXCLUSION", "MINUTIA", "CUSTOM"):
                count = stats.get(key, 0)
                if count:
                    parts.append(f"{count}{ANNOTATION_TYPES[key]['prefix']}")
            return "/".join(parts) if parts else "0"

        self.annotation_count_label.setText(f"Annotations : G={fmt(left_stats)} | D={fmt(right_stats)}")

    def _on_annotation_type_changed(self):
        if not hasattr(self, "left_view") or self.left_view is None:
            return
        data = self.annotation_type_combo.currentData()
        if data:
            self.left_view.set_annotation_type(data)
            self.right_view.set_annotation_type(data)

    def _on_measure_toggled(self, checked: bool):
        if checked:
            self.left_view.set_measurement_mode(True)
            self.right_view.set_measurement_mode(True)
            self.left_view.set_annotation_mode(False)
            self.right_view.set_annotation_mode(False)
            self.left_view.setCursor(Qt.CrossCursor)
            self.left_view.viewport().setCursor(Qt.CrossCursor)
            self.right_view.setCursor(Qt.CrossCursor)
            self.right_view.viewport().setCursor(Qt.CrossCursor)
        else:
            self.left_view.set_measurement_mode(False)
            self.right_view.set_measurement_mode(False)
            self.left_view._measurement_start = None
            self.right_view._measurement_start = None
            if self.annotate_action.isChecked():
                self._on_annotate_toggled(True)
            else:
                self._on_pan_toggled(True)

    def _on_link_views_toggled(self, checked: bool):
        self.views_linked = checked
        if checked:
            # Aligner les scrolls et le zoom tout de suite
            self._sync_zoom(self.left_view, self.right_view)
            self._sync_zoom(self.right_view, self.left_view)
            self._sync_pans_initial()

    def _on_toggle_side_panel(self, checked: bool):
        """Affiche/masque le panneau latéral pour maximiser la zone image."""
        if not self.module_frame:
            return
        self.module_frame.setVisible(checked)

    def _icon_path(self, name: str) -> Path:
        icons_root = Path(__file__).parent.parent / "resources" / "icons"
        # Priorité au dossier dédié comparaison_toolbar s'il existe
        candidate = icons_root / "comparison_toolbar" / f"tool_{name}.svg"
        if candidate.exists():
            return candidate
        return icons_root / f"tool_{name}.svg"

    def _set_icon(self, action: QAction, name: str):
        path = self._icon_path(name)
        if name in self._icon_cache:
            action.setIcon(self._icon_cache[name])
            return
        if path.exists():
            icon = QIcon(str(path))
            self._icon_cache[name] = icon
            action.setIcon(icon)

    def _on_zoom_changed(self, side: str, factor: float):
        if not self.views_linked:
            return
        source = self.left_view if side == "left" else self.right_view
        target = self.right_view if side == "left" else self.left_view
        self._sync_zoom(source, target)

    def _on_pan_changed(self, side: str, horizontal: bool, value: int):
        if not self.views_linked or self._syncing_pan:
            return
        self._syncing_pan = True
        try:
            source = self.left_view if side == "left" else self.right_view
            target = self.right_view if side == "left" else self.left_view
            if horizontal:
                target.horizontalScrollBar().setValue(value)
            else:
                target.verticalScrollBar().setValue(value)
        finally:
            self._syncing_pan = False

    def _sync_zoom(self, source: AnnotatableView, target: AnnotatableView):
        """Applique le zoom du source sur la cible."""
        if target is None or source is None:
            return
        ratio = source._zoom_factor / max(target._zoom_factor, 1e-6)
        if abs(ratio - 1.0) < 1e-3:
            return
        target.apply_zoom_ratio(ratio)
        # aligner les scrollbars sur la zone visible
        self._sync_pans_initial()

    def _sync_pans_initial(self):
        """Réaligne les scrollbars pour que les vues restent proches."""
        self._syncing_pan = True
        try:
            self.right_view.horizontalScrollBar().setValue(self.left_view.horizontalScrollBar().value())
            self.right_view.verticalScrollBar().setValue(self.left_view.verticalScrollBar().value())
        finally:
            self._syncing_pan = False

    def _on_measurement_completed(self, side: str, x1: float, y1: float, x2: float, y2: float):
        pixels = math.hypot(x2 - x1, y2 - y1)
        text = self._measurement_text(side, pixels)
        view = self.left_view if side == "left" else self.right_view
        view.add_measurement((x1, y1), (x2, y2), text)

    def _measurement_text(self, side: str, pixels: float) -> str:
        dpi = self.image_state[side]["dpi"]
        if dpi:
            mm = pixels / dpi * 25.4
            return f"{pixels:.1f} px / {mm:.2f} mm"
        return f"{pixels:.1f} px"

    def _clear_measurements(self):
        self.left_view.clear_measurements()
        self.right_view.clear_measurements()

    def _on_enhancement_changed(self, side: str):
        """Met à jour l'état d'amélioration et rerend l'image."""
        ctrl = self.enhance_controls[side]
        enh = {
            "brightness": float(ctrl["brightness"].value()),
            "contrast": float(ctrl["contrast"].value()) / 100.0,
            "gamma": float(ctrl["gamma"].value()) / 100.0,
            "invert": ctrl["invert"].isChecked(),
        }
        self.image_state[side]["enhancements"] = enh
        self._render_image(side)

    def _scale_annotation_meta(self, side: str, ratio: float) -> List[Dict[str, object]]:
        view = self.left_view if side == "left" else self.right_view
        meta = view.get_annotation_meta()
        scaled = []
        for entry in meta:
            scaled.append({
                "x": entry["x"] * ratio,
                "y": entry["y"] * ratio,
                "type": entry["type"],
                "label": entry["label"],
            })
        return scaled

    def _scale_measurement_meta(self, side: str, ratio: float) -> List[Dict[str, object]]:
        view = self.left_view if side == "left" else self.right_view
        meta = view.get_measurement_meta()
        scaled = []
        for entry in meta:
            sx, sy = entry["start"]
            ex, ey = entry["end"]
            scaled.append({
                "start": (sx * ratio, sy * ratio),
                "end": (ex * ratio, ey * ratio),
            })
        return scaled

    # ─────────────────────────────────────────────────────────────────────
    # Rotation
    # ─────────────────────────────────────────────────────────────────────

    def _rotate_point_forward(self, w: int, h: int, angle: int, x: float, y: float) -> Tuple[float, float]:
        angle = angle % 360
        if angle == 0:
            return x, y
        if angle == 90:
            return y, w - x
        if angle == 180:
            return w - x, h - y
        if angle == 270:
            return h - y, x
        return x, y

    def _rotate_point_backward(self, w: int, h: int, angle: int, x: float, y: float) -> Tuple[float, float]:
        """Inverse de _rotate_point_forward (rotated -> base)."""
        angle = angle % 360
        if angle == 0:
            return x, y
        if angle == 90:
            return w - y, x
        if angle == 180:
            return w - x, h - y
        if angle == 270:
            return y, h - x
        return x, y

    def _transform_meta_for_rotation(
        self,
        side: str,
        delta_deg: int
    ) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], int]:
        """Transforme annotations + mesures pour une rotation donnée."""
        state = self.image_state[side]
        base = state.get("base_image")
        if base is None:
            return [], [], state.get("rotation", 0)

        old_angle = state.get("rotation", 0) % 360
        new_angle = (old_angle + delta_deg) % 360
        w, h = base.width, base.height

        view = self.left_view if side == "left" else self.right_view
        annotations = view.get_annotation_meta()
        measurements = view.get_measurement_meta()

        new_annotations: List[Dict[str, object]] = []
        for entry in annotations:
            bx, by = self._rotate_point_backward(w, h, old_angle, entry["x"], entry["y"])
            nx, ny = self._rotate_point_forward(w, h, new_angle, bx, by)
            new_annotations.append({
                "x": nx,
                "y": ny,
                "type": entry["type"],
                "label": entry["label"],
            })

        new_measurements: List[Dict[str, object]] = []
        for entry in measurements:
            sx, sy = entry["start"]
            ex, ey = entry["end"]
            bsx, bsy = self._rotate_point_backward(w, h, old_angle, sx, sy)
            bex, bey = self._rotate_point_backward(w, h, old_angle, ex, ey)
            nsx, nsy = self._rotate_point_forward(w, h, new_angle, bsx, bsy)
            nex, ney = self._rotate_point_forward(w, h, new_angle, bex, bey)
            new_measurements.append({
                "start": (nsx, nsy),
                "end": (nex, ney),
            })

        return new_annotations, new_measurements, new_angle

    def _rotate_image(self, side: str, degrees: int):
        """Rotation par pas fixes (90/180) en ajustant annotations/mesures."""
        sides = ["left", "right"] if side == "both" else [side]
        for s in sides:
            base = self.image_state[s].get("base_image")
            if base is None:
                continue
            annotations_meta, measurements_meta, new_angle = self._transform_meta_for_rotation(s, degrees)
            self.image_state[s]["rotation"] = new_angle
            self._render_image(s, annotations_meta=annotations_meta, measurements_meta=measurements_meta)

    def _reset_rotation(self, side: str):
        sides = ["left", "right"] if side == "both" else [side]
        for s in sides:
            current = self.image_state[s].get("rotation", 0)
            if current == 0:
                continue
            self._rotate_image(s, -current)

    # ─────────────────────────────────────────────────────────────────────
    # Export
    # ─────────────────────────────────────────────────────────────────────

    def _export_comparison(self):
        if not self.left_scene.items() and not self.right_scene.items():
            QMessageBox.warning(self, "Export impossible", "Veuillez charger au moins une image.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter la comparaison", "comparison.jpg",
            "Images JPEG (*.jpg *.jpeg);;Images PNG (*.png)"
        )
        if not file_path:
            return

        left_img = self._capture_view(self.left_view, self.left_scene)
        right_img = self._capture_view(self.right_view, self.right_scene)
        combined = self._combine_images(left_img, right_img)

        try:
            combined.save(file_path, quality=95)
            QMessageBox.information(self, "Export réussi", f"Comparaison exportée vers :\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", f"Impossible de sauvegarder :\n{str(e)}")

    def _capture_view(self, view: AnnotatableView, scene: QGraphicsScene) -> Image.Image:
        rect = scene.itemsBoundingRect()
        if rect.isEmpty():
            return Image.new("RGB", (400, 400), color=(240, 240, 240))

        width = int(rect.width())
        height = int(rect.height())
        if width <= 0 or height <= 0:
            return Image.new("RGB", (400, 400), color=(240, 240, 240))

        qimg = QImage(width, height, QImage.Format_RGB888)
        qimg.fill(Qt.white)

        painter = QPainter(qimg)
        painter.setRenderHint(QPainter.Antialiasing)
        scene.render(painter, QRectF(0, 0, width, height), rect)
        painter.end()

        ptr = qimg.bits()
        ptr.setsize(qimg.byteCount())
        return Image.frombytes("RGB", (width, height), bytes(ptr), "raw", "RGB")

    def _combine_images(self, left: Image.Image, right: Image.Image) -> Image.Image:
        max_height = max(left.height, right.height)
        if left.height != max_height:
            ratio = max_height / left.height
            left = left.resize((int(left.width * ratio), max_height), Image.Resampling.LANCZOS)
        if right.height != max_height:
            ratio = max_height / right.height
            right = right.resize((int(right.width * ratio), max_height), Image.Resampling.LANCZOS)

        gap = 10
        combined_width = left.width + gap + right.width
        combined = Image.new("RGB", (combined_width, max_height), color=(255, 255, 255))
        combined.paste(left, (0, 0))
        combined.paste(right, (left.width + gap, 0))
        return combined

    # ─────────────────────────────────────────────────────────────────────
    # Chargement fichiers
    # ─────────────────────────────────────────────────────────────────────

    def _browse_and_load(self, side: str):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionnez un fichier (NIST/Image/PDF)",
            "",
            "NIST/Image/PDF (*.nist *.nst *.eft *.an2 *.int *.png *.jpg *.jpeg *.bmp *.tif *.tiff *.pdf);;Tous (*)"
        )
        if not file_path:
            return
        self.load_path(side, file_path)

    def reset_zoom(self):
        self.left_view.reset_zoom()
        self.right_view.reset_zoom()

    def load_path(self, side: str, path: str):
        pil_img = self._path_to_pil(path)
        if not pil_img:
            self._set_status(side, f"Impossible de charger : {path}")
            return

        # Stocker l'image PIL originale
        self.image_state[side]["base_image"] = pil_img
        self.image_state[side]["dpi"] = None
        self.image_state[side]["rotation"] = 0
        self.image_state[side]["enhancements"] = self._default_enhancements()

        # Réinitialiser les sliders d'amélioration (déclenche rendu)
        self._reset_enhancements(side)

        # Mettre à jour le label
        label = self.left_label if side == "left" else self.right_label
        label.setText(Path(path).name)
        self._update_dpi_label(side)

    def _set_status(self, side: str, text: str):
        if side == "left":
            self.left_label.setText(text)
        else:
            self.right_label.setText(text)

    def _path_to_pil(self, path: str) -> Optional[Image.Image]:
        lower = path.lower()
        try:
            if lower.endswith((".nist", ".nst", ".eft", ".an2", ".int")):
                return self._load_nist_pil(path)
            if lower.endswith(".pdf"):
                return self._load_pdf_pil(path)
            return self._load_image_pil(path)
        except Exception:
            return None

    def _load_image_pil(self, path: str) -> Optional[Image.Image]:
        img = Image.open(path)
        return exif_transpose(img).convert("RGB")

    def _load_pdf_pil(self, path: str) -> Optional[Image.Image]:
        try:
            img = Image.open(path)
            return img.convert("RGB")
        except Exception:
            return None

    def _load_nist_pil(self, path: str) -> Optional[Image.Image]:
        nist = NISTFile(path)
        if not nist.parse():
            return None
        for rtype in (14, 4, 10, 7, 15):
            recs = nist.get_records_by_type(rtype)
            for idc, rec in recs:
                pil_img, _ = self._record_to_image(rec)
                if pil_img:
                    return pil_img
        return None

    def _record_to_image(self, record) -> Tuple[Optional[Image.Image], str]:
        data = None
        for attr in ("_999", "_009", "DATA", "data", "image", "Image", "BDB", "value"):
            try:
                val = getattr(record, attr, None)
                if val and isinstance(val, (bytes, bytearray)):
                    data = bytes(val)
                    break
            except Exception:
                continue
        if not data:
            return None, ""
        payload, fmt = locate_image_payload(data)
        if fmt == "WSQ":
            img, _ = decode_wsq(payload)
            if img:
                return img, fmt
            return None, fmt
        if fmt == "JPEG2000":
            img, _ = decode_jpeg2000(payload)
            if img:
                return exif_transpose(img), fmt
            return None, fmt
        try:
            img = Image.open(io.BytesIO(payload))
            img = exif_transpose(img).convert("RGB")
            return img, detect_image_format(payload)
        except Exception:
            return None, fmt

    def _pil_to_pixmap(self, img: Image.Image) -> QPixmap:
        img = img.convert("RGB")
        data = img.tobytes("raw", "RGB")
        qimg = QImage(data, img.width, img.height, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)
