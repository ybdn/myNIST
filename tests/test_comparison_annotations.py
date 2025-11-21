"""Tests pour la vue comparaison (annotations typées, rotation, mesures, liens)."""

import pytest

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QGraphicsScene

from PIL import Image

from mynist.views.comparison_view import (
    AnnotationPoint,
    CalibrationPoint,
    AnnotatableView,
    ComparisonView,
    ANNOTATION_TYPES,
    CALIBRATION_COLOR,
    ANNOTATION_RADIUS,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestAnnotationPoint:
    def test_creation_with_type_and_label(self, qapp):
        point = AnnotationPoint(100, 200, "MATCH", "M1")
        assert point.center == (100, 200)
        assert point.label == "M1"
        assert point.pen().color() == ANNOTATION_TYPES["MATCH"]["color"]
        assert point.contains_point(100, 200) is True
        assert point.contains_point(100 + ANNOTATION_RADIUS * 3, 200) is False


class TestCalibrationPoint:
    def test_calibration_point_color(self, qapp):
        point = CalibrationPoint(10, 20)
        assert point.center == (10, 20)
        assert point.pen().color() == CALIBRATION_COLOR
        assert point.brush().color() == CALIBRATION_COLOR


class TestAnnotatableView:
    def test_annotation_numbering_by_type(self, qapp):
        view = AnnotatableView()
        scene = QGraphicsScene()
        view.setScene(scene)
        view.set_annotation_type("MATCH")
        view._add_annotation(10, 10)
        view._add_annotation(20, 20)
        labels = [a["label"] for a in view.get_annotation_meta()]
        assert labels == ["M1", "M2"]

    def test_measurement_mode_adds_and_removes(self, qapp):
        view = AnnotatableView()
        scene = QGraphicsScene()
        view.setScene(scene)
        view.add_measurement((0, 0), (100, 0), "test")
        assert len(view.get_measurement_meta()) == 1
        view.remove_last_measurement()
        assert len(view.get_measurement_meta()) == 0


class TestComparisonView:
    def test_state_initialisation(self, qapp):
        view = ComparisonView()
        assert view.image_state["left"]["base_image"] is None
        assert view.image_state["left"]["dpi"] is None
        assert view.image_state["left"]["rotation"] == 0
        assert view.image_state["right"]["base_image"] is None
        assert view.views_linked is False

    def test_rotation_transforms_annotations(self, qapp):
        view = ComparisonView()
        img = Image.new("RGB", (100, 50), color="white")
        view.image_state["left"]["base_image"] = img
        view.left_view.setScene(QGraphicsScene())
        view.left_view._add_annotation(10, 20, annotation_type="MATCH", label="M1")
        view._render_image("left")
        view._rotate_image("left", 90)
        coords = view.left_view.get_annotations()[0]
        assert coords == (20, 100 - 10)

    def test_enhancement_sliders_update_state(self, qapp):
        view = ComparisonView()
        img = Image.new("RGB", (10, 10), color="gray")
        view.image_state["left"]["base_image"] = img
        ctrl = view.enhance_controls["left"]
        ctrl["brightness"].setValue(50)
        ctrl["contrast"].setValue(150)
        ctrl["gamma"].setValue(80)
        ctrl["invert"].setChecked(True)
        view._on_enhancement_changed("left")
        enh = view.image_state["left"]["enhancements"]
        assert enh["brightness"] == 50.0
        assert enh["contrast"] == 1.5
        assert enh["gamma"] == 0.8
        assert enh["invert"] is True

    def test_measurement_text_includes_mm_when_dpi(self, qapp):
        view = ComparisonView()
        view.image_state["left"]["dpi"] = 254  # 10 px/mm
        text = view._measurement_text("left", 100)
        assert "mm" in text

    def test_link_views_action_sets_flag(self, qapp):
        view = ComparisonView()
        view.link_views_action.setChecked(True)
        assert view.views_linked is True
