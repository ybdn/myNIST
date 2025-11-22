"""Constants for NIST Studio application."""

# Application metadata
APP_NAME = "NIST Studio"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Suite d'outils biométriques NIST"

# NIST Record Types
RECORD_TYPE_NAMES = {
    1: "Type-1: Transaction / Header",
    2: "Type-2: Descriptive Text (user-defined)",
    3: "Type-3: Low-Resolution Grayscale Fingerprint (deprecated)",
    4: "Type-4: High-Resolution Grayscale Fingerprint",
    5: "Type-5: Low-Resolution Binary Fingerprint (deprecated)",
    6: "Type-6: High-Resolution Binary Fingerprint (deprecated)",
    7: "Type-7: User-Defined Image (raster)",
    8: "Type-8: Signature Image",
    9: "Type-9: Minutiae Data",
    10: "Type-10: Facial / SMT Image",
    11: "Type-11: Forensic & Investigative Voice Data (reserved)",
    12: "Type-12: Forensic Dental & Oral Data (reserved)",
    13: "Type-13: Latent Image (variable resolution)",
    14: "Type-14: Fingerprint Image (variable resolution)",
    15: "Type-15: Palmprint Image (variable resolution)",
    16: "Type-16: User-Defined Testing Image",
    17: "Type-17: Iris Image",
    18: "Type-18: DNA Data (reserved)",
    19: "Type-19: Plantar Image",
    20: "Type-20: Source Representation",
    21: "Type-21: Associated Context",
    98: "Type-98: Information Assurance",
    99: "Type-99: CBEFF Biometric Data Record",
}

# Fingerprint-related record types
FINGERPRINT_TYPES = [4, 13, 14, 15]

# Image-related record types
IMAGE_TYPES = [4, 7, 8, 10, 13, 14, 15, 16, 17, 19, 20]

# Alphanumeric record types
TEXT_TYPES = [1, 2, 9]

# Export Signa Multiple configuration
SIGNA_MULTIPLE_RULES = {
    'delete_fields': [215],  # Fields to delete from Type-2
    'replace_fields': {
        217: "11707"  # Field 217 -> value "11707"
    }
}

# UI Configuration
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 800
PANEL_SIZES = [300, 550, 550]  # Default sizes for 3 panels

# File filters (extended to .nst/.int as variants)
NIST_FILE_FILTER = "NIST Files (*.nist *.nst *.eft *.an2 *.int);;All Files (*)"
