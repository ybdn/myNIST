#!/usr/bin/env python3
"""
Debug script to analyze NIST files and test image extraction.
"""

import sys
from pathlib import Path

# Add mynist to path
sys.path.insert(0, str(Path(__file__).parent))

from mynist.models.nist_file import NISTFile

def analyze_nist_file(filepath):
    """Analyze a NIST file in detail."""
    print("=" * 80)
    print(f"Analyzing: {filepath}")
    print("=" * 80)

    nist = NISTFile(filepath)
    if not nist.parse():
        print("ERROR: Failed to parse file!")
        return

    print(f"\n✓ File parsed successfully")
    print(f"Total records: {len(nist.records)}")
    print()

    # List all record types
    print("Record Types Found:")
    for record_type in nist.get_record_types():
        records = nist.get_records_by_type(record_type)
        print(f"  - Type {record_type}: {len(records)} record(s)")

    print()

    # Analyze Type-2 fields
    print("=" * 80)
    print("TYPE-2 FIELDS (Alphanumeric Data)")
    print("=" * 80)

    type2_fields = nist.get_type2_fields()
    if type2_fields:
        for field, value in sorted(type2_fields.items()):
            value_str = str(value)[:100]  # Limit display
            print(f"  {field}: {value_str}")

            # Highlight fields 2.215 and 2.217
            if field == "2.215":
                print(f"    ⚠️  FIELD 2.215 FOUND (should be deleted in Export Signa)")
            if field == "2.217":
                print(f"    ⚠️  FIELD 2.217 = '{value}' (should be '11707' in Export Signa)")
    else:
        print("  (No Type-2 fields found)")

    print()

    # Analyze fingerprint records
    print("=" * 80)
    print("FINGERPRINT/IMAGE RECORDS")
    print("=" * 80)

    fingerprint_records = nist.get_fingerprint_records()
    if fingerprint_records:
        for rec_type, idc, record in fingerprint_records:
            print(f"\n  Type-{rec_type} (IDC {idc}):")

            # Try to get image data
            print(f"    Record type: {type(record)}")
            print(f"    Record class: {record.__class__.__name__}")

            # Try different ways to access image data
            # For Type-14 and Type-15, image data is usually in field 999
            image_attrs = ['_999', 'DATA', 'data', 'image', 'Image', 'BDB', '_009']
            found_image = False

            for attr in image_attrs:
                try:
                    data = getattr(record, attr, None)
                    if data and isinstance(data, (bytes, bytearray)):
                        print(f"    ✓ Found image data in '{attr}': {len(data)} bytes")
                        found_image = True

                        # Check image format
                        if data[:2] == b'\xff\xd8':
                            print(f"      Format: JPEG")
                        elif data[:8] == b'\x89PNG\r\n\x1a\n':
                            print(f"      Format: PNG")
                        elif data[:2] in [b'BM', b'BA']:
                            print(f"      Format: BMP")
                        else:
                            print(f"      Format: Unknown (first bytes: {data[:10].hex()})")
                        break
                except Exception as e:
                    continue

            if not found_image:
                print(f"    ✗ No image data found in standard attributes")

                # Try to list fields numerically
                print(f"    Trying to access fields by number...")
                for field_num in [1, 2, 3, 4, 5, 6, 7, 8, 9, 999]:
                    try:
                        attr_name = f'_{field_num:03d}'
                        val = getattr(record, attr_name, None)
                        if val is not None:
                            if isinstance(val, (bytes, bytearray)):
                                print(f"      - Field {field_num} ({attr_name}): {len(val)} bytes")
                                if len(val) > 100:
                                    print(f"        First bytes: {val[:20].hex()}")
                            elif isinstance(val, str):
                                print(f"      - Field {field_num} ({attr_name}): '{val[:50]}'")
                            else:
                                print(f"      - Field {field_num} ({attr_name}): {type(val).__name__}")
                    except Exception as e:
                        pass
    else:
        print("  (No fingerprint records found)")

    print()
    print("=" * 80)
    print()


def test_export_signa_multiple(filepath):
    """Test Export Signa Multiple functionality."""
    print("=" * 80)
    print("TESTING EXPORT SIGNA MULTIPLE")
    print("=" * 80)

    # Parse original file
    nist = NISTFile(filepath)
    if not nist.parse():
        print("ERROR: Failed to parse file!")
        return

    print(f"Original file: {filepath}")

    # Check Type-2 fields before
    print("\nBEFORE Export Signa Multiple:")
    type2_fields = nist.get_type2_fields()

    field_215_before = type2_fields.get('2.215', '(not found)')
    field_217_before = type2_fields.get('2.217', '(not found)')

    print(f"  Field 2.215: {field_215_before}")
    print(f"  Field 2.217: {field_217_before}")

    # Apply Export Signa Multiple modifications
    print("\nApplying modifications...")

    # Get Type-2 record
    type2_records = nist.get_records_by_type(2)
    if not type2_records:
        print("ERROR: No Type-2 record found!")
        return

    idc, _ = type2_records[0]

    # Delete field 2.215
    result_delete = nist.delete_field(2, 215, idc)
    print(f"  Delete field 2.215: {'✓ Success' if result_delete else '✗ Failed'}")

    # Modify field 2.217
    result_modify = nist.modify_field(2, 217, "11707", idc)
    print(f"  Set field 2.217 = '11707': {'✓ Success' if result_modify else '✗ Failed'}")

    # Check fields after modification
    print("\nAFTER modifications (in memory):")
    type2_fields_after = nist.get_type2_fields()

    field_215_after = type2_fields_after.get('2.215', '(not found)')
    field_217_after = type2_fields_after.get('2.217', '(not found)')

    print(f"  Field 2.215: {field_215_after}")
    print(f"  Field 2.217: {field_217_after}")

    # Export to test file
    output_path = Path(filepath).parent / f"{Path(filepath).stem}_export_test.nist"
    print(f"\nExporting to: {output_path}")

    success = nist.export(str(output_path))
    print(f"Export result: {'✓ Success' if success else '✗ Failed'}")

    if success and output_path.exists():
        print(f"Exported file size: {output_path.stat().st_size} bytes")

        # Re-parse exported file to verify
        print("\nVerifying exported file...")
        nist_verify = NISTFile(str(output_path))
        if nist_verify.parse():
            type2_verify = nist_verify.get_type2_fields()

            field_215_verify = type2_verify.get('2.215', '(not found)')
            field_217_verify = type2_verify.get('2.217', '(not found)')

            print(f"  Field 2.215 in exported file: {field_215_verify}")
            print(f"  Field 2.217 in exported file: {field_217_verify}")

            # Check if modifications were successful
            if field_215_verify == '(not found)':
                print("  ✓ Field 2.215 successfully deleted")
            else:
                print("  ✗ Field 2.215 still present!")

            if field_217_verify == "11707":
                print("  ✓ Field 2.217 successfully set to '11707'")
            else:
                print(f"  ✗ Field 2.217 = '{field_217_verify}' (expected '11707')")

    print()
    print("=" * 80)
    print()


def main():
    """Main function."""
    nist_dir = Path(__file__).parent / "nist-files"

    if not nist_dir.exists():
        print(f"ERROR: Directory not found: {nist_dir}")
        sys.exit(1)

    nist_files = list(nist_dir.glob("*.nist")) + list(nist_dir.glob("*.eft")) + list(nist_dir.glob("*.an2"))

    if not nist_files:
        print(f"ERROR: No NIST files found in {nist_dir}")
        sys.exit(1)

    print(f"Found {len(nist_files)} NIST file(s)")
    print()

    for nist_file in nist_files:
        analyze_nist_file(str(nist_file))
        print()
        test_export_signa_multiple(str(nist_file))
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
