"""Tests for biometric label helpers."""

from types import SimpleNamespace

from mynist.utils.biometric_labels import (
    describe_biometric_record,
    FINGER_POSITIONS,
    IMPRESSION_TYPES,
)


def test_describe_biometric_record_fingerprint():
    record = SimpleNamespace(_003=1, _004=2)  # IMP=1, FGP=2
    text = describe_biometric_record(14, record)
    assert "Right index" in text
    assert "IMP" not in text
    assert "Livescan" in text


def test_describe_biometric_record_type10_default():
    record = SimpleNamespace()
    assert describe_biometric_record(10, record) == "Face/SMT image"


def test_mappings_are_non_empty():
    assert 1 in FINGER_POSITIONS
    assert 1 in IMPRESSION_TYPES
