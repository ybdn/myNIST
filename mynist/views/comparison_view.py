"""Vue de comparaison côte à côte (NIST/Image/PDF) avec calibration DPI enrichie."""

import math
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import io

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QSize, QTimer, QPointF
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
    QGraphicsPixmapItem,
    QToolBar,
    QToolButton,
    QMenu,
    QCheckBox,
    QActionGroup,
    QAction,
    QMessageBox,
    QInputDialog,
    QTabWidget,
    QSplitter,
    QRadioButton,
    QButtonGroup,
    QSizePolicy,
    QDialog,
)
from PIL import Image, ImageEnhance, ImageOps

from mynist.models.nist_file import NISTFile
from mynist.utils.image_tools import locate_image_payload, detect_image_format, exif_transpose
from mynist.utils.image_codecs import decode_wsq, decode_jpeg2000
from mynist.utils.biometric_labels import get_short_label_fr
from mynist.utils.design_tokens import load_svg_icon


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
PAN_MARGIN = 500  # marge pour autoriser un pan plus libre autour de l'image
BACKGROUND_TOLERANCE = 25  # tolérance pour la suppression d'arrière-plan


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
        text_rect = self.text_item.boundingRect()
        offset_x = ANNOTATION_RADIUS + 4
        offset_y = -(ANNOTATION_RADIUS + text_rect.height() + 2)
        self.text_item.setPos(self._center_x + offset_x, self._center_y + offset_y)

    def set_label_visible(self, visible: bool):
        self.text_item.setVisible(visible)


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
        self._labels_visible = True
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
        if enabled:
            self._reset_modes()
            self._annotation_mode = True
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
            self.viewport().setCursor(Qt.CrossCursor)
        else:
            self._annotation_mode = False

    def set_calibration_mode(self, enabled: bool):
        if enabled:
            self._reset_modes()
            self._calibration_mode = True
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
            self.viewport().setCursor(Qt.CrossCursor)
        else:
            self._calibration_mode = False

    def set_measurement_mode(self, enabled: bool):
        if enabled:
            self._reset_modes()
            self._measurement_mode = True
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
            self.viewport().setCursor(Qt.CrossCursor)
        else:
            self._measurement_mode = False
            self._measurement_start = None

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
        point.set_label_visible(self._labels_visible)
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

    def set_labels_visible(self, visible: bool):
        """Affiche/masque les numéros des annotations."""
        self._labels_visible = visible
        for point in self._annotations:
            point.set_label_visible(visible)

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

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # État des images (PIL originales + DPI calibré + navigation NIST)
        self.image_state = {
            "left": {
                "base_image": None,
                "original_image": None,
                "dpi": None,
                "rotation": 0,
                "enhancements": self._default_enhancements(),
                "nist_file": None,          # NISTFile object if loaded
                "nist_images": [],          # List of (record_type, idc, record, label)
                "nist_index": 0,            # Current image index
                "file_path": None,          # Path to loaded file
            },
            "right": {
                "base_image": None,
                "original_image": None,
                "dpi": None,
                "rotation": 0,
                "enhancements": self._default_enhancements(),
                "nist_file": None,
                "nist_images": [],
                "nist_index": 0,
                "file_path": None,
            },
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
        self._pan_link_offset = {"h": 0, "v": 0}
        self.module_frame = None  # conservé pour compat mais non utilisé (popup)
        self.adjust_popup: Optional[QDialog] = None
        self._icon_cache: Dict[str, QIcon] = {}

        # Côté actif pour les ajustements (toggle unique)
        self.active_adjustment_side = "left"
        self._pre_overlay_side = "left"
        self.overlay_enabled = False
        self.overlay_alpha = 0.5
        self.overlay_items = {"left": None}
        self.overlay_popup: Optional[QDialog] = None
        self.adjust_button: Optional[QToolButton] = None
        self._adjust_parent = None
        self.grid_enabled = False
        self.grid_items = {"left": [], "right": []}
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

        # ═══════════════════════════════════════════════════════════════════
        # Colonne gauche
        # ═══════════════════════════════════════════════════════════════════
        self.left_view = AnnotatableView()
        self.left_scene = QGraphicsScene()
        self.left_view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.left_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.left_view.setScene(self.left_scene)

        left_box = QVBoxLayout()
        left_box.setContentsMargins(0, 0, 0, 0)
        left_box.setSpacing(4)

        # Header gauche: [Importer] [filename] ─── [● count]
        left_header = QHBoxLayout()
        left_header.setSpacing(8)
        self.left_import_btn = QPushButton("Importer")
        self.left_import_btn.clicked.connect(lambda: self._browse_and_load("left"))
        left_header.addWidget(self.left_import_btn)

        self.left_label = QLabel("Aucune image")
        self.left_label.setStyleSheet("background: rgba(0,0,0,0.04); padding: 4px 8px; border-radius: 6px;")
        self.left_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_header.addWidget(self.left_label)

        self.left_count_label = QLabel("")
        self.left_count_label.setStyleSheet("color: #22c55e; font-weight: bold; padding: 4px 8px;")
        left_header.addWidget(self.left_count_label)

        left_box.addLayout(left_header)
        left_box.addWidget(self.left_view)

        # Navigation NIST gauche (masquée par défaut)
        self.left_nist_nav = self._build_nist_nav("left")
        left_box.addWidget(self.left_nist_nav)

        main_row.addLayout(left_box, 5)

        # ═══════════════════════════════════════════════════════════════════
        # Colonne droite avec module à droite de l'image
        # ═══════════════════════════════════════════════════════════════════
        self.right_view = AnnotatableView()
        self.right_scene = QGraphicsScene()
        self.right_view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.right_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.right_view.setScene(self.right_scene)

        right_inner = QHBoxLayout()
        right_inner.setContentsMargins(0, 0, 0, 0)
        right_inner.setSpacing(8)

        right_image_col = QVBoxLayout()
        right_image_col.setContentsMargins(0, 0, 0, 0)
        right_image_col.setSpacing(4)

        # Header droite: [Importer] [filename] ─── [● count]
        right_header = QHBoxLayout()
        right_header.setSpacing(8)
        self.right_import_btn = QPushButton("Importer")
        self.right_import_btn.clicked.connect(lambda: self._browse_and_load("right"))
        right_header.addWidget(self.right_import_btn)

        self.right_label = QLabel("Aucune image")
        self.right_label.setStyleSheet("background: rgba(0,0,0,0.04); padding: 4px 8px; border-radius: 6px;")
        self.right_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_header.addWidget(self.right_label)

        self.right_count_label = QLabel("")
        self.right_count_label.setStyleSheet("color: #22c55e; font-weight: bold; padding: 4px 8px;")
        right_header.addWidget(self.right_count_label)

        right_image_col.addLayout(right_header)
        right_image_col.addWidget(self.right_view)

        # Navigation NIST droite (masquée par défaut)
        self.right_nist_nav = self._build_nist_nav("right")
        right_image_col.addWidget(self.right_nist_nav)

        self.right_image_container = QWidget()
        self.right_image_container.setLayout(right_image_col)

        # Module calibrate/resample + amélioration (désormais popup)
        self.adjust_widget = self._build_unified_panel()

        right_inner.addWidget(self.right_image_container, 5)

        main_row.addLayout(right_inner, 5)

        layout.addLayout(main_row)

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

        # ═══════════════════════════════════════════════════════════════════
        # Bouton retour au Hub
        # ═══════════════════════════════════════════════════════════════════
        self.back_action = QAction("Hub", self)
        self.back_action.setToolTip("Retour au hub")
        self._set_icon(self.back_action, "home")
        self.back_action.triggered.connect(self.back_requested.emit)
        toolbar.addAction(self.back_action)

        toolbar.addSeparator()

        # ═══════════════════════════════════════════════════════════════════
        # Groupe 1 : Modes (Main / Annoter / Mesurer)
        # ═══════════════════════════════════════════════════════════════════
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

        # ═══════════════════════════════════════════════════════════════════
        # Groupe 2 : Contrôles d'annotation (Type + Masquer)
        # ═══════════════════════════════════════════════════════════════════
        type_column = QVBoxLayout()
        type_column.setContentsMargins(0, 0, 0, 0)
        type_column.setSpacing(2)
        self.annotation_type_label = QLabel("Type :")
        type_column.addWidget(self.annotation_type_label)

        self.annotation_type_combo = QComboBox()
        for key in ANNOTATION_TYPES.keys():
            self.annotation_type_combo.addItem(key.title(), key)
        self.annotation_type_combo.currentIndexChanged.connect(self._on_annotation_type_changed)
        type_column.addWidget(self.annotation_type_combo)

        self.numbering_checkbox = QCheckBox("Numéroter")
        self.numbering_checkbox.setChecked(True)
        self.numbering_checkbox.toggled.connect(self._on_numbering_toggled)
        type_column.addWidget(self.numbering_checkbox)

        type_wrapper = QWidget()
        type_wrapper.setLayout(type_column)
        toolbar.addWidget(type_wrapper)

        self.visibility_action = QAction("Masquer", self)
        self.visibility_action.setCheckable(True)
        self.visibility_action.toggled.connect(self._on_visibility_toggled)
        self._set_icon(self.visibility_action, "visibility")
        toolbar.addAction(self.visibility_action)

        self.grid_action = QAction("Grille", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setToolTip("Afficher une grille calibree")
        self._set_icon(self.grid_action, "grid")
        self.grid_action.toggled.connect(self._on_grid_toggled)
        toolbar.addAction(self.grid_action)

        self.overlay_action = QAction("Overlay", self)
        self.overlay_action.setCheckable(True)
        self.overlay_action.setToolTip("Superposer droite sur gauche avec transparence")
        self.overlay_action.toggled.connect(self._on_overlay_toggled)
        self._set_icon(self.overlay_action, "overlay")
        self.overlay_button = QToolButton()
        self.overlay_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.overlay_button.setDefaultAction(self.overlay_action)
        self.overlay_button.clicked.connect(self._on_overlay_button_clicked)
        toolbar.addWidget(self.overlay_button)

        # Slider overlay (popup, pas dans la toolbar)
        self.overlay_slider = QSlider(Qt.Horizontal)
        self.overlay_slider.setRange(0, 100)
        self.overlay_slider.setValue(int(self.overlay_alpha * 100))
        self.overlay_slider.setFixedWidth(140)
        self.overlay_slider.valueChanged.connect(self._on_overlay_alpha_changed)

        toolbar.addSeparator()

        # ═══════════════════════════════════════════════════════════════════
        # Groupe 3 : Menu Effacer (dropdown)
        # ═══════════════════════════════════════════════════════════════════
        clear_menu = QMenu(self)

        clear_left_action = QAction("Annotations gauche", self)
        self._set_icon(clear_left_action, "clear_left")
        clear_left_action.triggered.connect(lambda: self._clear_annotations("left"))
        clear_menu.addAction(clear_left_action)

        clear_right_action = QAction("Annotations droite", self)
        self._set_icon(clear_right_action, "clear_right")
        clear_right_action.triggered.connect(lambda: self._clear_annotations("right"))
        clear_menu.addAction(clear_right_action)

        clear_all_action = QAction("Toutes les annotations", self)
        self._set_icon(clear_all_action, "clear_all")
        clear_all_action.triggered.connect(self._clear_all_annotations)
        clear_menu.addAction(clear_all_action)

        clear_menu.addSeparator()

        clear_measures_action = QAction("Mesures", self)
        self._set_icon(clear_measures_action, "measure_clear")
        clear_measures_action.triggered.connect(self._clear_measurements)
        clear_menu.addAction(clear_measures_action)

        clear_button = QToolButton()
        clear_button.setText("Effacer")
        clear_button.setToolTip("Effacer annotations ou mesures")
        clear_button.setMenu(clear_menu)
        clear_button.setPopupMode(QToolButton.InstantPopup)
        clear_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._set_icon_toolbutton(clear_button, "clear_all")
        toolbar.addWidget(clear_button)

        toolbar.addSeparator()

        # ═══════════════════════════════════════════════════════════════════
        # Groupe 4 : Vues (Lier / Reset zoom)
        # ═══════════════════════════════════════════════════════════════════
        self.link_views_action = QAction("Lier", self)
        self.link_views_action.setCheckable(True)
        self.link_views_action.setToolTip("Synchroniser zoom/pan entre gauche et droite")
        self._set_icon(self.link_views_action, "link")
        self.link_views_action.toggled.connect(self._on_link_views_toggled)
        toolbar.addAction(self.link_views_action)

        self.reset_zoom_action = QAction("Reset zoom", self)
        self._set_icon(self.reset_zoom_action, "reset_zoom")
        self.reset_zoom_action.triggered.connect(self.reset_zoom)
        toolbar.addAction(self.reset_zoom_action)

        # ═══════════════════════════════════════════════════════════════════
        # Spacer → pousse les actions suivantes à droite
        # ═══════════════════════════════════════════════════════════════════
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        # ═══════════════════════════════════════════════════════════════════
        # Groupe 5 : Export + Ajustements (à droite)
        # ═══════════════════════════════════════════════════════════════════
        export_action = QAction("Exporter", self)
        export_action.setToolTip("Exporter la comparaison côte à côte")
        self._set_icon(export_action, "export")
        export_action.triggered.connect(self._export_comparison)
        toolbar.addAction(export_action)

        self.toggle_side_panel_action = QAction("Ajustements", self)
        self.toggle_side_panel_action.setCheckable(True)
        self.toggle_side_panel_action.setChecked(False)  # Masqué par défaut
        self.toggle_side_panel_action.setToolTip("Afficher/masquer Calibration, Resample et Amélioration d'image")
        self._set_icon(self.toggle_side_panel_action, "photo_cog")
        self.toggle_side_panel_action.toggled.connect(self._on_toggle_side_panel)
        self.adjust_button = QToolButton()
        self.adjust_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.adjust_button.setDefaultAction(self.toggle_side_panel_action)
        toolbar.addWidget(self.adjust_button)

        layout.addWidget(toolbar)

        # Désactiver les contrôles d'annotation par défaut (mode Main actif)
        self._set_annotation_controls_enabled(False)

    def _build_nist_nav(self, side: str) -> QWidget:
        """Barre de navigation pour les fichiers NIST (hauteur fixe, toujours présente)."""
        widget = QWidget()
        # Hauteur fixe pour éviter le redimensionnement des vues
        widget.setFixedHeight(28)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        # Bouton précédent
        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(28)
        prev_btn.setToolTip("Image précédente")
        prev_btn.clicked.connect(lambda: self._nist_nav_prev(side))
        layout.addWidget(prev_btn)

        # Combo de sélection
        combo = QComboBox()
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combo.setPlaceholderText("— Image standard —")
        combo.currentIndexChanged.connect(lambda idx: self._on_nist_nav_changed(side, idx))
        layout.addWidget(combo)

        # Bouton suivant
        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(28)
        next_btn.setToolTip("Image suivante")
        next_btn.clicked.connect(lambda: self._nist_nav_next(side))
        layout.addWidget(next_btn)

        widget.setLayout(layout)

        # Stocker les références
        if side == "left":
            self._left_nist_combo = combo
            self._left_nist_prev = prev_btn
            self._left_nist_next = next_btn
        else:
            self._right_nist_combo = combo
            self._right_nist_prev = prev_btn
            self._right_nist_next = next_btn

        # Désactivé par défaut (pas de NIST chargé)
        self._set_nist_nav_enabled(side, False)

        return widget

    def _set_nist_nav_enabled(self, side: str, enabled: bool):
        """Active/désactive la barre de navigation NIST."""
        if side == "left":
            self._left_nist_combo.setEnabled(enabled)
            self._left_nist_prev.setEnabled(enabled)
            self._left_nist_next.setEnabled(enabled)
        else:
            self._right_nist_combo.setEnabled(enabled)
            self._right_nist_prev.setEnabled(enabled)
            self._right_nist_next.setEnabled(enabled)

    def _nist_nav_prev(self, side: str):
        """Navigue vers l'image NIST précédente."""
        state = self.image_state[side]
        if not state["nist_images"]:
            return
        new_idx = max(0, state["nist_index"] - 1)
        if new_idx != state["nist_index"]:
            combo = self._left_nist_combo if side == "left" else self._right_nist_combo
            combo.setCurrentIndex(new_idx)

    def _nist_nav_next(self, side: str):
        """Navigue vers l'image NIST suivante."""
        state = self.image_state[side]
        if not state["nist_images"]:
            return
        new_idx = min(len(state["nist_images"]) - 1, state["nist_index"] + 1)
        if new_idx != state["nist_index"]:
            combo = self._left_nist_combo if side == "left" else self._right_nist_combo
            combo.setCurrentIndex(new_idx)

    def _on_nist_nav_changed(self, side: str, index: int):
        """Appelé quand l'utilisateur sélectionne une image dans la navigation NIST."""
        state = self.image_state[side]
        if index < 0 or index >= len(state["nist_images"]):
            return
        state["nist_index"] = index

        # Charger l'image sélectionnée
        record_type, idc, record, label = state["nist_images"][index]
        pil_img, _ = self._record_to_image(record)
        if pil_img:
            state["base_image"] = pil_img
            state["original_image"] = pil_img.copy()
            state["dpi"] = None
            state["rotation"] = 0
            state["enhancements"] = self._default_enhancements()

            # Effacer annotations et mesures
            view = self.left_view if side == "left" else self.right_view
            view.clear_annotations()
            view.clear_measurements()

            self._sync_controls_to_side()
            self._render_image(side)
            self._update_annotation_count()

    def _populate_nist_nav(self, side: str):
        """Remplit le combo de navigation avec les images du fichier NIST."""
        state = self.image_state[side]
        combo = self._left_nist_combo if side == "left" else self._right_nist_combo

        nist_images = state.get("nist_images", [])
        if not nist_images:
            # Désactiver et vider le combo
            combo.blockSignals(True)
            combo.clear()
            combo.blockSignals(False)
            self._set_nist_nav_enabled(side, False)
            return

        # Peupler le combo
        combo.blockSignals(True)
        combo.clear()
        for record_type, idc, record, label in nist_images:
            combo.addItem(f"{label} (T{record_type})", (record_type, idc))
        combo.setCurrentIndex(state.get("nist_index", 0))
        combo.blockSignals(False)

        self._set_nist_nav_enabled(side, True)

    def _build_unified_panel(self) -> QWidget:
        """Panneau unifie reorganise horizontalement avec style ameliore."""
        widget = QWidget()
        widget.setStyleSheet("""
            QFrame.adjustSection {
                background: palette(base);
                border: 1px solid palette(mid);
                border-radius: 8px;
            }
            QLabel.sectionTitle {
                font-weight: bold;
                font-size: 13px;
                padding-bottom: 4px;
            }
            QLabel.sectionHint {
                color: palette(mid);
                font-size: 11px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.overlay_mode_label = QLabel("Mode Overlay : modification du calque superpose")
        self.overlay_mode_label.setStyleSheet("font-weight: bold; color: #2563eb; padding: 6px; background: #dbeafe; border-radius: 4px;")
        self.overlay_mode_label.setVisible(False)
        main_layout.addWidget(self.overlay_mode_label)

        # Bandeau cible
        self.toggle_frame = QFrame()
        self.toggle_frame.setProperty("class", "adjustSection")
        toggle_layout = QHBoxLayout()
        toggle_layout.setContentsMargins(12, 10, 12, 10)
        toggle_layout.setSpacing(16)
        title_toggle = QLabel("Appliquer a :")
        title_toggle.setStyleSheet("font-weight: bold;")
        toggle_layout.addWidget(title_toggle)
        self.side_toggle_group = QButtonGroup(self)
        self.left_radio = QRadioButton("Image gauche")
        self.left_radio.setChecked(True)
        self.right_radio = QRadioButton("Image droite")
        self.side_toggle_group.addButton(self.left_radio, 0)
        self.side_toggle_group.addButton(self.right_radio, 1)
        self.side_toggle_group.buttonClicked.connect(self._on_side_toggle_changed)
        toggle_layout.addWidget(self.left_radio)
        toggle_layout.addWidget(self.right_radio)
        toggle_layout.addStretch()
        self.toggle_frame.setLayout(toggle_layout)
        main_layout.addWidget(self.toggle_frame)

        row = QHBoxLayout()
        row.setSpacing(12)

        # Bloc Calibration / Resample
        calib_group = QFrame()
        calib_group.setProperty("class", "adjustSection")
        calib_layout = QVBoxLayout()
        calib_layout.setContentsMargins(14, 12, 14, 12)
        calib_layout.setSpacing(8)
        calib_title = QLabel("Calibration")
        calib_title.setProperty("class", "sectionTitle")
        calib_layout.addWidget(calib_title)
        self.unified_dpi_label = QLabel("DPI : Non calibre")
        self.unified_dpi_label.setStyleSheet("font-weight: bold; color: #059669;")
        calib_layout.addWidget(self.unified_dpi_label)
        calib_btn = QPushButton("Calibrer (2 points)")
        calib_btn.setToolTip("Cliquez 2 points sur l'image et entrez la distance reelle en mm")
        calib_btn.clicked.connect(self._start_calibration_unified)
        calib_layout.addWidget(calib_btn)
        calib_layout.addSpacing(8)
        resample_label = QLabel("Reechantillonnage")
        resample_label.setProperty("class", "sectionTitle")
        calib_layout.addWidget(resample_label)
        resample_row = QHBoxLayout()
        resample_row.setSpacing(6)
        self.unified_target_dpi = QSpinBox()
        self.unified_target_dpi.setRange(72, 1200)
        self.unified_target_dpi.setValue(500)
        self.unified_target_dpi.setSuffix(" DPI")
        resample_row.addWidget(QLabel("Cible :"))
        resample_row.addWidget(self.unified_target_dpi)
        calib_layout.addLayout(resample_row)
        resample_btn = QPushButton("Reechantillonner")
        resample_btn.setToolTip("Convertir l'image au DPI cible")
        resample_btn.clicked.connect(self._resample_image_unified)
        calib_layout.addWidget(resample_btn)
        calib_layout.addStretch()
        calib_group.setLayout(calib_layout)
        row.addWidget(calib_group, 1)

        # Bloc Ameliorations
        enhance_group = QFrame()
        enhance_group.setProperty("class", "adjustSection")
        enhance_layout = QVBoxLayout()
        enhance_layout.setContentsMargins(14, 12, 14, 12)
        enhance_layout.setSpacing(6)
        title_enh = QLabel("Ameliorations")
        title_enh.setProperty("class", "sectionTitle")
        enhance_layout.addWidget(title_enh)
        enhance_layout.addWidget(QLabel("Luminosite"))
        self.unified_brightness = QSlider(Qt.Horizontal)
        self.unified_brightness.setRange(-100, 100)
        self.unified_brightness.setValue(0)
        self.unified_brightness.setToolTip("Luminosite (-100 a +100)")
        self.unified_brightness.valueChanged.connect(self._on_unified_enhancement_changed)
        enhance_layout.addWidget(self.unified_brightness)
        enhance_layout.addWidget(QLabel("Contraste"))
        self.unified_contrast = QSlider(Qt.Horizontal)
        self.unified_contrast.setRange(50, 200)
        self.unified_contrast.setValue(100)
        self.unified_contrast.setToolTip("Contraste (0.5 a 2.0)")
        self.unified_contrast.valueChanged.connect(self._on_unified_enhancement_changed)
        enhance_layout.addWidget(self.unified_contrast)
        enhance_layout.addWidget(QLabel("Gamma"))
        self.unified_gamma = QSlider(Qt.Horizontal)
        self.unified_gamma.setRange(50, 200)
        self.unified_gamma.setValue(100)
        self.unified_gamma.setToolTip("Gamma (0.5 a 2.0)")
        self.unified_gamma.valueChanged.connect(self._on_unified_enhancement_changed)
        enhance_layout.addWidget(self.unified_gamma)
        inv_row = QHBoxLayout()
        inv_row.setSpacing(6)
        self.unified_invert = QPushButton("Inverser")
        self.unified_invert.setCheckable(True)
        self.unified_invert.setToolTip("Inverser les couleurs (negatif)")
        self.unified_invert.clicked.connect(self._on_unified_enhancement_changed)
        inv_row.addWidget(self.unified_invert)
        self.bg_remove_btn = QPushButton("Suppr. fond")
        self.bg_remove_btn.setToolTip("Rend transparent le fond uni du calque (overlay)")
        self.bg_remove_btn.clicked.connect(self._remove_background_unified)
        self.bg_remove_btn.setEnabled(False)
        inv_row.addWidget(self.bg_remove_btn)
        enhance_layout.addLayout(inv_row)
        reset_btn = QPushButton("Reinitialiser filtres")
        reset_btn.clicked.connect(self._reset_enhancements_unified)
        enhance_layout.addWidget(reset_btn)
        enhance_group.setLayout(enhance_layout)
        row.addWidget(enhance_group, 2)

        # Bloc Orientation
        rot_group = QFrame()
        rot_group.setProperty("class", "adjustSection")
        rot_layout = QVBoxLayout()
        rot_layout.setContentsMargins(14, 12, 14, 12)
        rot_layout.setSpacing(8)
        rot_title = QLabel("Orientation")
        rot_title.setProperty("class", "sectionTitle")
        rot_layout.addWidget(rot_title)
        rot_row1 = QHBoxLayout()
        rot_row1.setSpacing(6)
        btn_ccw = QPushButton("Rot -90")
        btn_ccw.setToolTip("Rotation 90 degres sens anti-horaire")
        btn_ccw.clicked.connect(lambda: self._rotate_image_unified(-90))
        rot_row1.addWidget(btn_ccw)
        btn_cw = QPushButton("Rot +90")
        btn_cw.setToolTip("Rotation 90 degres sens horaire")
        btn_cw.clicked.connect(lambda: self._rotate_image_unified(90))
        rot_row1.addWidget(btn_cw)
        rot_layout.addLayout(rot_row1)
        rot_row2 = QHBoxLayout()
        rot_row2.setSpacing(6)
        btn_flip_h = QPushButton("Miroir H")
        btn_flip_h.setToolTip("Miroir horizontal")
        btn_flip_h.clicked.connect(lambda: self._flip_image_unified(axis="h"))
        rot_row2.addWidget(btn_flip_h)
        btn_flip_v = QPushButton("Miroir V")
        btn_flip_v.setToolTip("Miroir vertical")
        btn_flip_v.clicked.connect(lambda: self._flip_image_unified(axis="v"))
        rot_row2.addWidget(btn_flip_v)
        rot_layout.addLayout(rot_row2)
        btn_reset_rot = QPushButton("Reset orientation")
        btn_reset_rot.clicked.connect(self._reset_rotation_unified)
        rot_layout.addWidget(btn_reset_rot)
        rot_layout.addStretch()
        rot_group.setLayout(rot_layout)
        row.addWidget(rot_group, 1)

        # Bloc Actions
        actions_group = QFrame()
        actions_group.setProperty("class", "adjustSection")
        actions_layout = QVBoxLayout()
        actions_layout.setContentsMargins(14, 12, 14, 12)
        actions_layout.setSpacing(8)
        act_title = QLabel("Actions")
        act_title.setProperty("class", "sectionTitle")
        actions_layout.addWidget(act_title)
        reset_img_btn = QPushButton("Reset image")
        reset_img_btn.setToolTip("Restaurer l'image originale (annule tout)")
        reset_img_btn.clicked.connect(self._reset_image_unified)
        actions_layout.addWidget(reset_img_btn)
        export_img_btn = QPushButton("Exporter JPG")
        export_img_btn.setToolTip("Exporter l'image avec tous les reglages appliques")
        export_img_btn.clicked.connect(self._export_image_unified)
        actions_layout.addWidget(export_img_btn)
        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        row.addWidget(actions_group, 1)

        main_layout.addLayout(row)
        widget.setLayout(main_layout)
        return widget

    def _on_side_toggle_changed(self, button):
        """Appelé quand le toggle gauche/droite change."""
        self.active_adjustment_side = "left" if button == self.left_radio else "right"
        self._sync_controls_to_side()

    def _show_adjust_popup(self):
        """Affiche le panneau d'ajustements (calibrate/resample/rotate/enhance) en flottant."""
        parent = self.window() or self
        if self.adjust_popup is None or self._adjust_parent != parent:
            self._adjust_parent = parent
            self.adjust_popup = QDialog(parent)
            self.adjust_popup.setModal(False)
            self.adjust_popup.setWindowModality(Qt.NonModal)
            self.adjust_popup.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
            self.adjust_popup.setAttribute(Qt.WA_ShowWithoutActivating, True)
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.adjust_widget)
            self.adjust_popup.setLayout(layout)
            self.adjust_popup.setFixedWidth(850)
        # Positionner sous le bouton Ajustements
        btn = self.adjust_button
        if btn:
            global_pos = btn.mapToGlobal(btn.rect().bottomLeft())
            # Contraindre à la fenêtre principale
            win_geo = parent.frameGeometry()
            x = max(win_geo.left(), min(global_pos.x(), win_geo.right() - self.adjust_popup.width()))
            y = max(win_geo.top(), min(global_pos.y(), win_geo.bottom() - self.adjust_popup.height()))
            self.adjust_popup.move(x, y)
        self.adjust_popup.show()

    def _hide_adjust_popup(self):
        if self.adjust_popup and self.adjust_popup.isVisible():
            self.adjust_popup.hide()
            # désynchroniser le toggle si fermeture manuelle
            if self.toggle_side_panel_action.isChecked():
                self.toggle_side_panel_action.blockSignals(True)
                self.toggle_side_panel_action.setChecked(False)
                self.toggle_side_panel_action.blockSignals(False)

    def _show_overlay_slider_popup(self):
        """Affiche un mini-panneau sous le bouton overlay avec la réglette, qui reste visible."""
        if self.overlay_popup is None:
            self.overlay_popup = QDialog(self)
            self.overlay_popup.setModal(False)
            self.overlay_popup.setWindowModality(Qt.NonModal)
            self.overlay_popup.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
            self.overlay_popup.setAttribute(Qt.WA_ShowWithoutActivating, True)
            layout = QVBoxLayout()
            layout.setContentsMargins(6, 6, 6, 6)
            layout.addWidget(self.overlay_slider)
            self.overlay_popup.setLayout(layout)
        # positionner sous le bouton overlay
        btn = self.overlay_button
        if btn:
            global_pos = btn.mapToGlobal(btn.rect().bottomLeft())
            self.overlay_popup.move(global_pos)
        self.overlay_slider.setValue(int(self.overlay_alpha * 100))
        self.overlay_popup.show()

    def _sync_controls_to_side(self):
        """Synchronise les contrôles avec l'état du côté actif."""
        side = self.active_adjustment_side
        state = self.image_state[side]
        enh = state.get("enhancements", self._default_enhancements())

        # Bloquer les signaux pour éviter les boucles
        self.unified_brightness.blockSignals(True)
        self.unified_contrast.blockSignals(True)
        self.unified_gamma.blockSignals(True)
        self.unified_invert.blockSignals(True)

        self.unified_brightness.setValue(int(enh.get("brightness", 0)))
        self.unified_contrast.setValue(int(enh.get("contrast", 1.0) * 100))
        self.unified_gamma.setValue(int(enh.get("gamma", 1.0) * 100))
        self.unified_invert.setChecked(enh.get("invert", False))

        self.unified_brightness.blockSignals(False)
        self.unified_contrast.blockSignals(False)
        self.unified_gamma.blockSignals(False)
        self.unified_invert.blockSignals(False)

        # Mettre à jour le DPI affiché
        self._update_unified_dpi_label()

    def _update_unified_dpi_label(self):
        """Met à jour le label DPI pour le côté actif."""
        side = self.active_adjustment_side
        dpi = self.image_state[side]["dpi"]
        side_name = "gauche" if side == "left" else "droite"
        if dpi:
            self.unified_dpi_label.setText(f"DPI ({side_name}) : {dpi:.1f}")
        else:
            self.unified_dpi_label.setText(f"DPI ({side_name}) : Non calibré")

    def _start_calibration_unified(self):
        """Démarre la calibration pour le côté actif."""
        self._start_calibration(self.active_adjustment_side)

    def _resample_image_unified(self):
        """Rééchantillonne l'image du côté actif."""
        side = self.active_adjustment_side
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

        target_dpi = self.unified_target_dpi.value()

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
        self._update_unified_dpi_label()

        QMessageBox.information(
            self,
            "Rééchantillonnage",
            f"Image rééchantillonnée de {current_dpi:.0f} DPI vers {target_dpi} DPI.\n"
            f"Nouvelle taille : {new_width} x {new_height} px"
        )

    def _on_unified_enhancement_changed(self):
        """Met à jour les améliorations pour le côté actif."""
        side = self.active_adjustment_side
        enh = {
            "brightness": float(self.unified_brightness.value()),
            "contrast": float(self.unified_contrast.value()) / 100.0,
            "gamma": float(self.unified_gamma.value()) / 100.0,
            "invert": self.unified_invert.isChecked(),
        }
        self.image_state[side]["enhancements"] = enh
        self._render_image(side)

    def _remove_background_unified(self):
        """Supprime un fond uni (le rend transparent) sur le côté actif."""
        side = self.active_adjustment_side
        state = self.image_state[side]
        base_img = state.get("base_image")
        if base_img is None:
            QMessageBox.warning(self, "Effacer l'arrière-plan", "Aucune image chargée.")
            return
        cleaned = self._remove_background(base_img)
        state["base_image"] = cleaned
        self._render_image(side)

    def _remove_background(self, img: Image.Image) -> Image.Image:
        """Détecte un fond quasi uni (couleur dominante des coins) et le rend transparent."""
        rgba = img.convert("RGBA")
        w, h = rgba.size
        if w == 0 or h == 0:
            return rgba
        sample = min(40, w, h)
        coords = [
            (0, 0),
            (w - sample, 0),
            (0, h - sample),
            (w - sample, h - sample),
        ]
        pixels = []
        for (x, y) in coords:
            crop = rgba.crop((x, y, x + sample, y + sample))
            pixels.extend(list(crop.getdata()))
        if not pixels:
            return rgba
        avg = (
            sum(p[0] for p in pixels) // len(pixels),
            sum(p[1] for p in pixels) // len(pixels),
            sum(p[2] for p in pixels) // len(pixels),
        )
        tol = BACKGROUND_TOLERANCE
        new_data = []
        for r, g, b, a in rgba.getdata():
            if abs(r - avg[0]) <= tol and abs(g - avg[1]) <= tol and abs(b - avg[2]) <= tol:
                new_data.append((r, g, b, 0))
            else:
                new_data.append((r, g, b, a))
        rgba.putdata(new_data)
        return rgba

    def _reset_enhancements_unified(self):
        """Réinitialise les améliorations pour le côté actif."""
        side = self.active_adjustment_side
        defaults = self._default_enhancements()
        self.image_state[side]["enhancements"] = defaults

        # Mettre à jour les contrôles
        self.unified_brightness.blockSignals(True)
        self.unified_brightness.setValue(0)
        self.unified_brightness.blockSignals(False)

        self.unified_contrast.blockSignals(True)
        self.unified_contrast.setValue(100)
        self.unified_contrast.blockSignals(False)

        self.unified_gamma.blockSignals(True)
        self.unified_gamma.setValue(100)
        self.unified_gamma.blockSignals(False)

        self.unified_invert.blockSignals(True)
        self.unified_invert.setChecked(False)
        self.unified_invert.blockSignals(False)

        self._render_image(side)

    def _rotate_image_unified(self, degrees: int):
        """Rotation pour le côté actif."""
        self._rotate_image(self.active_adjustment_side, degrees)

    def _reset_rotation_unified(self):
        """Reset rotation pour le côté actif."""
        self._reset_rotation(self.active_adjustment_side)

    def _flip_image_unified(self, axis: str):
        """Flip horizontal/vertical pour le côté actif."""
        self._flip_image(self.active_adjustment_side, axis=axis)

    def _export_image_unified(self):
        """Exporte l'image du côté actif avec tous les réglages appliqués."""
        side = self.active_adjustment_side
        state = self.image_state[side]
        base_img = state.get("base_image")

        if base_img is None:
            QMessageBox.warning(self, "Export", "Aucune image chargée.")
            return

        # Appliquer rotation + améliorations
        rotated = self._apply_rotation(base_img, state.get("rotation", 0))
        final_img = self._apply_enhancements(rotated, state.get("enhancements", self._default_enhancements()))

        # Dialogue de sauvegarde
        side_name = "gauche" if side == "left" else "droite"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Exporter l'image {side_name}",
            f"image_{side_name}.jpg",
            "Images JPEG (*.jpg *.jpeg);;Images PNG (*.png)"
        )
        if not file_path:
            return

        try:
            # Préparer les métadonnées DPI si calibré
            dpi = state.get("dpi")
            save_kwargs = {"quality": 95}
            if dpi:
                save_kwargs["dpi"] = (dpi, dpi)

            # Sauvegarder
            final_img.save(file_path, **save_kwargs)
            QMessageBox.information(
                self,
                "Export réussi",
                f"Image exportée vers :\n{file_path}"
                + (f"\n\nDPI : {dpi:.0f}" if dpi else "")
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", f"Impossible de sauvegarder :\n{str(e)}")

    def _reset_image_unified(self):
        """Réinitialise l'image du côté actif à son état original."""
        side = self.active_adjustment_side
        state = self.image_state[side]
        original = state.get("original_image")

        if original is None:
            QMessageBox.warning(self, "Réinitialiser", "Aucune image originale disponible.")
            return

        # Restaurer l'image originale
        state["base_image"] = original.copy()
        state["dpi"] = None
        state["rotation"] = 0
        state["enhancements"] = self._default_enhancements()

        # Effacer annotations et mesures du côté
        view = self.left_view if side == "left" else self.right_view
        view.clear_annotations()
        view.clear_measurements()

        # Synchroniser les contrôles et re-rendre
        self._sync_controls_to_side()
        self._render_image(side)

        side_name = "gauche" if side == "left" else "droite"
        QMessageBox.information(
            self,
            "Image réinitialisée",
            f"L'image {side_name} a été restaurée à son état original."
        )

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

            # Fin du mode calibration (nettoyer AVANT le render)
            self._end_calibration(side)

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
        for item in self.calibration_items[:]:
            try:
                if item.scene() == scene:
                    scene.removeItem(item)
            except RuntimeError:
                pass  # L'objet C++ a déjà été supprimé
        self.calibration_items.clear()
        if self.calibration_line:
            try:
                if self.calibration_line.scene() == scene:
                    scene.removeItem(self.calibration_line)
            except RuntimeError:
                pass
            self.calibration_line = None

    def _update_dpi_label(self, side: str):
        """Met à jour le label DPI (appelle le label unifié si c'est le côté actif)."""
        if side == self.active_adjustment_side:
            self._update_unified_dpi_label()

    # ─────────────────────────────────────────────────────────────────────
    # Rendu (rotation + enhancements)
    # ─────────────────────────────────────────────────────────────────────

    def _apply_rotation(self, img: Image.Image, angle: int) -> Image.Image:
        if angle % 360 == 0:
            return img
        return img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

    def _get_processed_image(self, side: str) -> Optional[Image.Image]:
        """Retourne l'image après rotation + améliorations pour le rendu/overlay."""
        state = self.image_state[side]
        base = state.get("base_image")
        if base is None:
            return None
        rotated = self._apply_rotation(base, state.get("rotation", 0))
        return self._apply_enhancements(rotated, state.get("enhancements", self._default_enhancements()))

    def _apply_enhancements(self, img: Image.Image, enh: Dict[str, float]) -> Image.Image:
        """Applique luminosité/contraste/gamma/inversion en conservant l'alpha éventuel."""
        had_alpha = img.mode == "RGBA"
        alpha = None
        if had_alpha:
            rgb, alpha = img.convert("RGBA").split()[:3], img.getchannel("A")
            result = Image.merge("RGB", rgb)
        else:
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

        if had_alpha and alpha is not None:
            result = result.convert("RGBA")
            result.putalpha(alpha)
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

        enhanced = self._get_processed_image(side)
        if enhanced is None:
            return
        self._display_pil_image(side, enhanced, annotations_meta=annotations_meta, measurements_meta=measurements_meta)

    def _reset_enhancements(self, side: str):
        """Réinitialise les améliorations d'un côté et synchronise les contrôles si actif."""
        defaults = self._default_enhancements()
        self.image_state[side]["enhancements"] = defaults

        # Si c'est le côté actif, mettre à jour les contrôles unifiés
        if side == self.active_adjustment_side:
            self.unified_brightness.blockSignals(True)
            self.unified_brightness.setValue(0)
            self.unified_brightness.blockSignals(False)

            self.unified_contrast.blockSignals(True)
            self.unified_contrast.setValue(100)
            self.unified_contrast.blockSignals(False)

            self.unified_gamma.blockSignals(True)
            self.unified_gamma.setValue(100)
            self.unified_gamma.blockSignals(False)

            self.unified_invert.blockSignals(True)
            self.unified_invert.setChecked(False)
            self.unified_invert.blockSignals(False)

        self._render_image(side)

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

        self._update_scene_rect(side, pix)
        self._fit_view_to_pixmap(view, pix)
        self._refresh_overlay()
        self._refresh_grid(side)
        self._update_annotation_count()

    # ─────────────────────────────────────────────────────────────────────
    # Ajustement vue/image
    # ─────────────────────────────────────────────────────────────────────

    def _fit_view_to_pixmap(self, view: AnnotatableView, pix: QPixmap):
        """Ajuste la vue pour afficher l'image complète sans déformation."""
        if not pix or pix.isNull():
            return
        view.resetTransform()
        scene_rect = QRectF(pix.rect())
        if scene_rect.isValid():
            view.fitInView(scene_rect, Qt.KeepAspectRatio)
        view._zoom_factor = 1.0

    def _update_scene_rect(self, side: str, pix: QPixmap):
        """Élargit la scène pour permettre le pan au-delà des bords visibles."""
        scene = self.left_scene if side == "left" else self.right_scene
        if not scene or not pix or pix.isNull():
            return
        rect = QRectF(pix.rect()).adjusted(-PAN_MARGIN, -PAN_MARGIN, PAN_MARGIN, PAN_MARGIN)
        scene.setSceneRect(rect)

    def _refresh_overlay(self):
        """Affiche/masque la superposition : image droite en calque sur la vue gauche uniquement."""
        if not self.overlay_enabled:
            self._clear_overlay_items()
            return

        # cacher la vue droite quand overlay actif
        self.right_view.setVisible(False)
        if self.right_image_container:
            self.right_image_container.setVisible(False)

        base_img = self._get_processed_image("left")
        other_img = self._get_processed_image("right")
        scene = self.left_scene
        if base_img is None or other_img is None or scene is None:
            return

        overlay = ImageOps.contain(other_img, base_img.size).convert("RGBA")
        ox = (base_img.width - overlay.width) // 2
        oy = (base_img.height - overlay.height) // 2
        pix = self._pil_to_pixmap(overlay)

        # conserver le décalage de l'overlay si déjà déplacé par l'utilisateur
        existing = self.overlay_items.get("left")
        prev_pos = QPointF(ox, oy)
        if existing:
            prev_pos = existing.pos()
            if existing.scene():
                scene.removeItem(existing)

        item: QGraphicsPixmapItem = scene.addPixmap(pix)
        item.setPos(prev_pos)
        item.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        item.setZValue(200)
        item.setOpacity(self.overlay_alpha)
        self.overlay_items["left"] = item

    def _clear_grid(self, side: str):
        items = self.grid_items.get(side, [])
        scene = self.left_scene if side == "left" else self.right_scene
        for it in items:
            if scene and it.scene():
                scene.removeItem(it)
        self.grid_items[side] = []

    def _refresh_grid(self, side: str):
        """Dessine une grille simple si activée."""
        self._clear_grid(side)
        if not self.grid_enabled:
            return
        scene = self.left_scene if side == "left" else self.right_scene
        pix_item = self.left_pixmap_item if side == "left" else self.right_pixmap_item
        if not scene or pix_item is None:
            return
        rect = pix_item.boundingRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        dpi = self.image_state[side].get("dpi")
        if dpi:
            step = max(20, int(dpi * 10 / 25.4))  # grille ~1cm si calibré
        else:
            step = 100
        pen = QPen(QColor(128, 128, 128, 120), 0.5, Qt.DashLine)
        items = []
        x = 0
        while x <= rect.width():
            line = scene.addLine(rect.left() + x, rect.top(), rect.left() + x, rect.top() + rect.height(), pen)
            line.setZValue(190)
            items.append(line)
            x += step
        y = 0
        while y <= rect.height():
            line = scene.addLine(rect.left(), rect.top() + y, rect.left() + rect.width(), rect.top() + y, pen)
            line.setZValue(190)
            items.append(line)
            y += step
        self.grid_items[side] = items

    # ─────────────────────────────────────────────────────────────────────
    # Modes toolbar
    # ─────────────────────────────────────────────────────────────────────

    def _set_annotation_controls_enabled(self, enabled: bool):
        """Active/désactive les contrôles d'annotation (Type combo et Masquer)."""
        self.annotation_type_label.setEnabled(enabled)
        self.annotation_type_combo.setEnabled(enabled)
        self.visibility_action.setEnabled(enabled)

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
            # Verrouiller les contrôles d'annotation
            self._set_annotation_controls_enabled(False)

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
            # Déverrouiller les contrôles d'annotation
            self._set_annotation_controls_enabled(True)
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
        """Met à jour les compteurs d'annotations pour chaque image."""
        def fmt(stats: Dict[str, int]) -> str:
            parts = []
            for key in ("MATCH", "EXCLUSION", "MINUTIA", "CUSTOM"):
                count = stats.get(key, 0)
                if count:
                    parts.append(f"{count}{ANNOTATION_TYPES[key]['prefix']}")
            if not parts:
                return ""
            return "● " + "/".join(parts)

        # Compteur gauche
        left_stats = self.left_view.get_annotation_stats()
        self.left_count_label.setText(fmt(left_stats))

        # Compteur droite
        right_stats = self.right_view.get_annotation_stats()
        self.right_count_label.setText(fmt(right_stats))

    def _on_annotation_type_changed(self):
        if not hasattr(self, "left_view") or self.left_view is None:
            return
        data = self.annotation_type_combo.currentData()
        if data:
            self.left_view.set_annotation_type(data)
            self.right_view.set_annotation_type(data)

    def _on_numbering_toggled(self, checked: bool):
        """Affiche/masque la numérotation des points."""
        self.left_view.set_labels_visible(checked)
        self.right_view.set_labels_visible(checked)

    def _on_overlay_button_clicked(self):
        """Affiche le slider alpha quand on clique sur Overlay."""
        if self.overlay_action.isChecked():
            self._show_overlay_slider_popup()
        else:
            if self.overlay_popup:
                self.overlay_popup.hide()

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
            # Verrouiller les contrôles d'annotation
            self._set_annotation_controls_enabled(False)
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
            self._capture_pan_offset()
        else:
            self._syncing_pan = False

    def _on_toggle_side_panel(self, checked: bool):
        """Affiche/masque le panneau d'ajustements en popup."""
        if checked:
            self._show_adjust_popup()
        else:
            self._hide_adjust_popup()

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
            icon = load_svg_icon(path, size=24)
            self._icon_cache[name] = icon
            action.setIcon(icon)

    def _set_icon_toolbutton(self, button: QToolButton, name: str):
        """Set icon on a QToolButton."""
        path = self._icon_path(name)
        if name in self._icon_cache:
            button.setIcon(self._icon_cache[name])
            return
        if path.exists():
            icon = load_svg_icon(path, size=24)
            self._icon_cache[name] = icon
            button.setIcon(icon)

    def _on_zoom_changed(self, side: str, factor: float):
        if not getattr(self, "views_linked", False):
            return
        source = self.left_view if side == "left" else self.right_view
        target = self.right_view if side == "left" else self.left_view
        self._sync_zoom(source, target)
        # recalcule l'offset pan après un zoom commun pour garder le verrouillage courant
        self._capture_pan_offset()

    def _on_pan_changed(self, side: str, horizontal: bool, value: int):
        if not getattr(self, "views_linked", False) or self._syncing_pan:
            return
        self._syncing_pan = True
        try:
            source = self.left_view if side == "left" else self.right_view
            target = self.right_view if side == "left" else self.left_view
            if horizontal:
                offset = self._pan_link_offset.get("h", 0)
                target.horizontalScrollBar().setValue(value + (offset if side == "left" else -offset))
            else:
                offset = self._pan_link_offset.get("v", 0)
                target.verticalScrollBar().setValue(value + (offset if side == "left" else -offset))
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
        # remplacé par _capture_pan_offset pour ne pas casser la position utilisateur
        pass

    def _capture_pan_offset(self):
        """Capture l'écart actuel entre scrollbars gauche/droite pour verrouiller la position."""
        try:
            lh = self.left_view.horizontalScrollBar().value()
            rh = self.right_view.horizontalScrollBar().value()
            lv = self.left_view.verticalScrollBar().value()
            rv = self.right_view.verticalScrollBar().value()
            self._pan_link_offset = {"h": rh - lh, "v": rv - lv}
        except Exception:
            self._pan_link_offset = {"h": 0, "v": 0}

    def _on_measurement_completed(self, side: str, x1: float, y1: float, x2: float, y2: float):
        pixels = math.hypot(x2 - x1, y2 - y1)
        text = self._measurement_text(side, pixels)
        view = self.left_view if side == "left" else self.right_view
        view.add_measurement((x1, y1), (x2, y2), text)
        self._capture_pan_offset()

    def _measurement_text(self, side: str, pixels: float) -> str:
        dpi = self.image_state[side]["dpi"]
        if dpi:
            mm = pixels / dpi * 25.4
            return f"{pixels:.1f} px / {mm:.2f} mm"
        return f"{pixels:.1f} px"

    def _clear_measurements(self):
        self.left_view.clear_measurements()
        self.right_view.clear_measurements()

    def _restore_checked_mode(self):
        """Réapplique le mode actif (main/annotation/mesure) après interruption."""
        if self.annotate_action.isChecked():
            self._on_annotate_toggled(True)
        elif self.measure_action.isChecked():
            self._on_measure_toggled(True)
        else:
            self._on_pan_toggled(True)

    def _clear_overlay_items(self):
        """Retire les overlays éventuels."""
        for key, item in list(self.overlay_items.items()):
            if item:
                scene = item.scene()
                if scene:
                    scene.removeItem(item)
            self.overlay_items[key] = None

    def _on_grid_toggled(self, checked: bool):
        self.grid_enabled = checked
        self._refresh_grid("left")
        self._refresh_grid("right")

    def _on_overlay_toggled(self, checked: bool):
        self.overlay_enabled = checked
        if checked:
            self._pre_overlay_side = self.active_adjustment_side
            # Forcer le panneau sur le calque (droite)
            self.active_adjustment_side = "right"
            self.overlay_mode_label.setVisible(True)
            self.toggle_frame.setVisible(False)
            # Align radios pour la sortie d'overlay
            self.left_radio.blockSignals(True)
            self.right_radio.blockSignals(True)
            self.right_radio.setChecked(True)
            self.left_radio.blockSignals(False)
            self.right_radio.blockSignals(False)
            self._sync_controls_to_side()
            self.right_image_container.setVisible(False)
            self.right_view.setVisible(False)
            self.left_view.setDragMode(QGraphicsView.NoDrag)
            self.left_view.setCursor(Qt.SizeAllCursor)
            self.left_view.viewport().setCursor(Qt.SizeAllCursor)
            self._set_annotation_controls_enabled(False)
            self.grid_action.setEnabled(False)
        else:
            self.overlay_mode_label.setVisible(False)
            self.toggle_frame.setVisible(True)
            # Restaurer le côté sélectionné avant overlay
            self.active_adjustment_side = self._pre_overlay_side
            self.left_radio.blockSignals(True)
            self.right_radio.blockSignals(True)
            if self.active_adjustment_side == "left":
                self.left_radio.setChecked(True)
            else:
                self.right_radio.setChecked(True)
            self.left_radio.blockSignals(False)
            self.right_radio.blockSignals(False)
            self._sync_controls_to_side()
            self._clear_overlay_items()
            if self.right_image_container:
                self.right_image_container.setVisible(True)
            self.right_view.setVisible(True)
            self.left_view.setVisible(True)
            self.grid_action.setEnabled(True)
            self._restore_checked_mode()
            # Réappliquer explicitement le curseur selon le mode actif
            if self.pan_action.isChecked():
                self.left_view.setCursor(Qt.OpenHandCursor)
                self.left_view.viewport().setCursor(Qt.OpenHandCursor)
                self.right_view.setCursor(Qt.OpenHandCursor)
                self.right_view.viewport().setCursor(Qt.OpenHandCursor)
            elif self.annotate_action.isChecked() or self.measure_action.isChecked():
                self.left_view.setCursor(Qt.CrossCursor)
                self.left_view.viewport().setCursor(Qt.CrossCursor)
                self.right_view.setCursor(Qt.CrossCursor)
                self.right_view.viewport().setCursor(Qt.CrossCursor)
            # forcer un repaint pour éviter les résidus de superposition
            self.left_view.viewport().update()
            self.right_view.viewport().update()
        # Bouton d'effacement d'arrière-plan actif seulement en overlay
        if hasattr(self, "bg_remove_btn"):
            self.bg_remove_btn.setEnabled(self.overlay_enabled)
        # Fermer la popup d'overlay si besoin
        if self.overlay_popup:
            self.overlay_popup.hide()
        # Fermer la popup d'ajustements si on la cachait via overlay off
        if not checked and self.adjust_popup and self.adjust_popup.isVisible():
            self.adjust_popup.hide()
            self.toggle_side_panel_action.setChecked(False)
        # Afficher la réglette si on vient d'activer
        if checked:
            self._show_overlay_slider_popup()
        self._refresh_overlay()

    def _on_overlay_alpha_changed(self, value: int):
        self.overlay_alpha = max(0.0, min(1.0, value / 100.0))
        for item in self.overlay_items.values():
            if item:
                item.setOpacity(self.overlay_alpha)
        if self.overlay_popup:
            self.overlay_popup.adjustSize()

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

    def _transform_meta_for_flip(self, side: str, axis: str) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
        """Applique une transformation miroir aux annotations/mesures."""
        state = self.image_state[side]
        base = state.get("base_image")
        if base is None:
            return [], []
        w, h = base.width, base.height
        view = self.left_view if side == "left" else self.right_view
        annotations = view.get_annotation_meta()
        measurements = view.get_measurement_meta()

        def flip_point(x: float, y: float) -> Tuple[float, float]:
            if axis == "h":
                return (w - x, y)
            return (x, h - y)

        new_annotations = []
        for entry in annotations:
            nx, ny = flip_point(entry["x"], entry["y"])
            new_annotations.append({
                "x": nx,
                "y": ny,
                "type": entry["type"],
                "label": entry["label"],
            })

        new_measurements = []
        for entry in measurements:
            sx, sy = flip_point(*entry["start"])
            ex, ey = flip_point(*entry["end"])
            new_measurements.append({"start": (sx, sy), "end": (ex, ey)})

        return new_annotations, new_measurements

    def _flip_image(self, side: str, axis: str = "h"):
        """Miroir horizontal/vertical en conservant annotations/mesures."""
        base = self.image_state[side].get("base_image")
        if base is None:
            return
        annotations_meta, measurements_meta = self._transform_meta_for_flip(side, axis)
        if axis == "h":
            flipped = ImageOps.mirror(base)
        else:
            flipped = ImageOps.flip(base)
        self.image_state[side]["base_image"] = flipped
        self._render_image(side, annotations_meta=annotations_meta, measurements_meta=measurements_meta)

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
        state = self.image_state[side]
        lower = path.lower()

        # Réinitialiser l'état NIST
        state["nist_file"] = None
        state["nist_images"] = []
        state["nist_index"] = 0
        state["file_path"] = path

        # Réinitialiser la navigation NIST (désactivée par défaut)
        self._populate_nist_nav(side)

        # Charger selon le type de fichier
        if lower.endswith((".nist", ".nst", ".eft", ".an2", ".int")):
            self._load_nist_with_nav(side, path)
        else:
            pil_img = self._path_to_pil(path)
            if not pil_img:
                self._set_status(side, f"Impossible de charger : {path}")
                return
            self._load_single_image(side, pil_img, Path(path).name)

    def _load_single_image(self, side: str, pil_img: Image.Image, filename: str):
        """Charge une image simple (non-NIST)."""
        state = self.image_state[side]
        state["base_image"] = pil_img
        state["original_image"] = pil_img.copy()
        state["dpi"] = None
        state["rotation"] = 0
        state["enhancements"] = self._default_enhancements()

        # Effacer annotations et mesures
        view = self.left_view if side == "left" else self.right_view
        view.clear_annotations()
        view.clear_measurements()

        # Réinitialiser les sliders d'amélioration (déclenche rendu)
        self._reset_enhancements(side)

        # Mettre à jour le label
        label = self.left_label if side == "left" else self.right_label
        label.setText(filename)
        self._update_dpi_label(side)
        self._update_annotation_count()

    def _load_nist_with_nav(self, side: str, path: str):
        """Charge un fichier NIST et peuple la navigation."""
        state = self.image_state[side]
        nist = NISTFile(path)
        if not nist.parse():
            self._set_status(side, f"Erreur parsing NIST : {path}")
            return

        state["nist_file"] = nist

        # Collecter toutes les images avec leurs labels
        nist_images = []
        for rtype in (14, 4, 13, 15, 10, 7):
            recs = nist.get_records_by_type(rtype)
            for idc, rec in recs:
                pil_img, _ = self._record_to_image(rec)
                if pil_img:
                    label = get_short_label_fr(rtype, rec, idc)
                    nist_images.append((rtype, idc, rec, label))

        if not nist_images:
            self._set_status(side, f"Aucune image trouvée dans : {Path(path).name}")
            return

        state["nist_images"] = nist_images
        state["nist_index"] = 0

        # Charger la première image
        record_type, idc, record, label = nist_images[0]
        pil_img, _ = self._record_to_image(record)
        if pil_img:
            state["base_image"] = pil_img
            state["original_image"] = pil_img.copy()
            state["dpi"] = None
            state["rotation"] = 0
            state["enhancements"] = self._default_enhancements()

            # Effacer annotations et mesures
            view = self.left_view if side == "left" else self.right_view
            view.clear_annotations()
            view.clear_measurements()

            self._reset_enhancements(side)

        # Mettre à jour le label avec le nom du fichier
        lbl = self.left_label if side == "left" else self.right_label
        lbl.setText(Path(path).name)

        # Peupler et afficher la navigation NIST
        self._populate_nist_nav(side)
        self._update_dpi_label(side)
        self._update_annotation_count()

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
        """Convertit un PIL Image en QPixmap en préservant l'alpha si présent."""
        mode = img.mode
        if mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in mode else "RGB")
            mode = img.mode

        if mode == "RGBA":
            data = img.tobytes("raw", "RGBA")
            bytes_per_line = img.width * 4
            qimg = QImage(data, img.width, img.height, bytes_per_line, QImage.Format_RGBA8888).copy()
        else:
            img = img.convert("RGB")
            data = img.tobytes("raw", "RGB")
            bytes_per_line = img.width * 3
            qimg = QImage(data, img.width, img.height, bytes_per_line, QImage.Format_RGB888).copy()

        return QPixmap.fromImage(qimg)
