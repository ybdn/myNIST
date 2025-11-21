"""Helpers to describe biometric records (impression type, finger position)."""

from typing import Optional

FINGER_POSITIONS = {
    0: "Unknown position",
    1: "Right thumb",
    2: "Right index",
    3: "Right middle",
    4: "Right ring",
    5: "Right little",
    6: "Left thumb",
    7: "Left index",
    8: "Left middle",
    9: "Left ring",
    10: "Left little",
    13: "Plain right four-fingers",
    14: "Plain left four-fingers",
    15: "Plain thumbs",
}

IMPRESSION_TYPES = {
    0: "Livescan plain",
    1: "Livescan rolled",
    2: "Non-live-scan plain",
    3: "Non-live-scan rolled",
    4: "Latent impression",
    5: "Latent tracing",
    6: "Latent photo",
    7: "Latent photo (enhanced)",
    8: "Sweep (rolled equivalent)",
    9: "Swipe",
}


def _safe_get(record, attr: str) -> Optional[int]:
    """Safely extract integer-like attribute without raising from nistitl."""
    try:
        value = getattr(record, attr, None)
        if value is None or value == "":
            return None
        return int(value)
    except Exception:
        return None


def describe_biometric_record(record_type: int, record) -> str:
    """
    Build a short descriptor for a biometric record using IMP / FGP when available.

    Args:
        record_type: NIST record type (4/7/10/13/14/15/...)
        record: record instance from nistitl
    """
    # Field numbers follow ANSI/NIST; FGP is often field 4, IMP field 3 on fingerprint/palm.
    impression = _safe_get(record, "_003") or _safe_get(record, "IMP")
    finger_pos = _safe_get(record, "_004") or _safe_get(record, "FGP")

    parts = []
    if finger_pos is not None:
        parts.append(FINGER_POSITIONS.get(finger_pos, f"Position {finger_pos}"))
    if impression is not None:
        parts.append(IMPRESSION_TYPES.get(impression, f"IMP {impression}"))

    if record_type == 10 and not parts:
        parts.append("Face/SMT image")
    elif record_type == 7 and not parts:
        parts.append("User-defined image")

    return " — ".join(parts)
