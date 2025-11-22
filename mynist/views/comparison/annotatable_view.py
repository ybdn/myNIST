"""Composants graphiques pour la vue de comparaison : AnnotatableView et éléments d'annotation."""

from typing import Optional, Tuple, List, Dict

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtWidgets import (
    QGraphicsView,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
)


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
CALIBRATION_COLOR = QColor(0, 128, 255)
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
    calibration_point_added = pyqtSignal(float, float)
    measurement_completed = pyqtSignal(float, float, float, float)
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
