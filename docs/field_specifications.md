# NIST Field Specifications

This document describes the NIST fields used in myNIST, particularly those involved in the Export Signa Multiple feature.

## Overview

ANSI/NIST-ITL files are structured as records containing fields. Each field is identified by a record type and field number.

**Field Notation:** `RecordType.FieldNumber`

Example: `2.215` means Field 215 in a Type-2 record.

## Type-2 Record: User-Defined Descriptive Text

The Type-2 record contains biographic and demographic information about subjects. The specific fields are often **implementation-dependent** and vary by organization or jurisdiction.

### Standard Type-2 Fields (Examples)

| Field | Mnemonic | Description |
|-------|----------|-------------|
| 2.001 | LEN | Logical record length |
| 2.002 | IDC | Information designation character |
| 2.003 | - | System information |
| 2.004 | SRC | Source agency |
| 2.005 | DAT | Date |
| 2.006 | HLL | Hour/minute/second |
| 2.007 | DAI | Destination agency identifier |
| 2.008 | ORI | Originating agency identifier |
| 2.009 | TCN | Transaction control number |
| 2.010 | TCR | Transaction control reference |

### Fields Modified by Export Signa Multiple

#### Field 2.215

**Status:** User-defined field
**Action in Export Signa Multiple:** **DELETED**

**Notes:**
- This field is not part of the standard ANSI/NIST-ITL specification
- Implementation-specific field (possibly Idemia or organizational)
- The exact purpose depends on your NIST implementation
- When deleted, the field is completely removed from the Type-2 record

**To Discover Field Purpose:**
1. Open a sample NIST file with myNIST
2. View the Type-2 record in the data panel
3. Check the value of field 2.215
4. Consult your organization's NIST specification document

#### Field 2.217

**Status:** User-defined field
**Action in Export Signa Multiple:** **SET TO "11707"**

**Notes:**
- This field is not part of the standard ANSI/NIST-ITL specification
- Implementation-specific field (possibly Idemia or organizational)
- The value "11707" is application-specific
- May represent a quality code, transaction type, or other metadata

**To Discover Field Purpose:**
1. Open a sample NIST file with myNIST
2. View the Type-2 record in the data panel
3. Check the current value of field 2.217
4. Compare with the exported value ("11707")
5. Consult your organization's NIST specification document

## Fingerprint Record Types

### Type-4: High-Resolution Grayscale Fingerprint

| Field | Description |
|-------|-------------|
| 4.001 | Record length |
| 4.002 | IDC |
| 4.003 | Impression type |
| 4.004 | Finger position |
| 4.005 | Image scanning resolution |
| 4.006 | Horizontal line length |
| 4.007 | Vertical line length |
| 4.008 | Grayscale compression algorithm |
| 4.009 | Image data |

### Type-13: Variable-Resolution Latent Image

Used for latent fingerprint images (crime scene prints).

### Type-14: Variable-Resolution Fingerprint Image

Used for variable-resolution rolled or plain fingerprints.

### Type-15: Variable-Resolution Palmprint Image

Used for palmprint images at variable resolutions.

## Image Record Types

### Type-10: Facial & SMT Image

Contains facial photographs and scars, marks, tattoos (SMT) images.

### Type-17: Iris Image

Contains iris biometric images.

## Understanding Your NIST Implementation

NIST files can be customized by different organizations. To understand your specific implementation:

### 1. Check with Your Organization

Contact your biometric system provider or IT department for:
- Field specification document
- NIST implementation profile
- Transaction format guide

### 2. Analyze Sample Files

Use myNIST to analyze your NIST files:
```bash
# Open a sample file
python -m mynist
# File > Open NIST File
# Select Type-2 record
# Review all fields in data panel
```

### 3. Compare Values

Before and after Export Signa Multiple:

**Before:**
- Note value of field 2.215
- Note value of field 2.217

**After:**
- Field 2.215 should be absent
- Field 2.217 should be "11707"

### 4. Consult Standards

Official ANSI/NIST-ITL documentation:
- **NIST SP 500-290**: ANSI/NIST-ITL 1-2011 UPDATE: 2015
- Available at: https://www.nist.gov/itl/iad/image-group/ansinist-itl-standard-references

### 5. Domain-Specific Profiles

Common NIST profiles:
- **FBI EBTS**: Electronic Biometric Transmission Specification (US law enforcement)
- **DoD EBTS**: Department of Defense profile
- **INTERPOL INT-I**: International police cooperation
- **Idemia profiles**: Commercial biometric systems

## Modifying Field Rules

The Export Signa Multiple rules are defined in:

**File:** [mynist/utils/constants.py](../mynist/utils/constants.py)

```python
SIGNA_MULTIPLE_RULES = {
    'delete_fields': [215],  # Fields to delete from Type-2
    'replace_fields': {
        217: "11707"  # Field 217 -> value "11707"
    }
}
```

**To modify rules:**
1. Edit the `SIGNA_MULTIPLE_RULES` dictionary
2. Add fields to `delete_fields` list
3. Add fields and values to `replace_fields` dictionary
4. Rebuild the application: `make build`

**Example - Adding more fields:**
```python
SIGNA_MULTIPLE_RULES = {
    'delete_fields': [215, 216, 218],  # Delete 3 fields
    'replace_fields': {
        217: "11707",
        219: "MODIFIED",
        220: "2025"
    }
}
```

## Field Data Types

NIST fields can contain different data types:

### Text Fields
- ASCII alphanumeric characters
- Example: Field 2.004 (Source agency) = "FBI01"

### Numeric Fields
- Integer or decimal numbers
- Example: Field 2.005 (Date) = "20250121"

### Binary Fields
- Raw binary data (usually images)
- Example: Field 4.009 (Image data)

### Formatted Fields
- Structured data with sub-fields
- Example: Type-9 minutiae data

## Best Practices

### Before Modifying Fields

1. **Backup original files** - Always keep originals
2. **Test on samples** - Verify modifications work correctly
3. **Document changes** - Keep records of field modifications
4. **Validate output** - Re-open exported files to verify

### Field Modification Guidelines

- **Don't modify Type-1 fields** - Transaction integrity
- **Be careful with mandatory fields** - May cause validation errors
- **Test downstream systems** - Ensure compatibility
- **Check field dependencies** - Some fields are related

### Troubleshooting Field Issues

**Field not found:**
- Field may not exist in this NIST file
- Check field is in Type-2 record
- Verify field number is correct

**Export fails:**
- Check Type-2 record exists
- Verify file permissions
- Check disk space

**Modified file rejected by system:**
- Field may be mandatory
- Value format may be incorrect
- Consult receiving system specifications

## Additional Resources

### NIST Resources
- NIST Biometric Standards: https://www.nist.gov/itl/iad/image-group/biometric-standards
- ANSI/NIST-ITL Downloads: https://www.nist.gov/itl/iad/image-group/ansinist-itl

### Idemia Resources
- nistitl Documentation: https://nistitl.readthedocs.io/
- nistitl GitHub: https://github.com/idemia/python-nistitl

### myNIST Documentation
- [User Guide](user_guide.md)
- [Developer Guide](developer_guide.md)
- [README](../README.md)

## Contact

For questions about specific field definitions in your NIST implementation:
1. Contact your biometric system provider
2. Consult your organization's NIST specification document
3. Check with your IT or security department

For myNIST application questions, see the main [README](../README.md).
