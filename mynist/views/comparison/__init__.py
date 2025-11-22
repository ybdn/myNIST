"""
Package comparison - Vue de comparaison côte à côte pour NIST Studio.

Ce package contient les composants pour la vue de comparaison d'images :
- annotatable_view: Composants graphiques (AnnotatableView, AnnotationPoint, etc.)
- image_loader: Chargement d'images depuis différentes sources
- image_processor: Traitement d'images (enhancements, rotation, etc.)
- export: Fonctions d'export de la comparaison
"""

from .annotatable_view import (
    AnnotatableView,
    AnnotationPoint,
    CalibrationPoint,
    MeasurementLine,
    ANNOTATION_TYPES,
    ANNOTATION_RADIUS,
    CALIBRATION_COLOR,
    CALIBRATION_RADIUS,
)

from .image_loader import ImageLoader

from .image_processor import (
    ImageProcessor,
    BACKGROUND_TOLERANCE,
)

from .export import capture_scene, combine_images

__all__ = [
    # Vues et composants graphiques
    "AnnotatableView",
    "AnnotationPoint",
    "CalibrationPoint",
    "MeasurementLine",
    # Constantes
    "ANNOTATION_TYPES",
    "ANNOTATION_RADIUS",
    "CALIBRATION_COLOR",
    "CALIBRATION_RADIUS",
    "BACKGROUND_TOLERANCE",
    # Utilitaires
    "ImageLoader",
    "ImageProcessor",
    "capture_scene",
    "combine_images",
]
