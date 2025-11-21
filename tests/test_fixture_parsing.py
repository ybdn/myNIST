"""Integration checks on curated fixtures (Types 1/4/7/9/10/14/15, EFTS/INT, tronqués)."""

from pathlib import Path

import pytest

from mynist.models.nist_file import NISTFile


BASE = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "relative, required_types, should_parse",
    [
        ("type4/HR_12883247_3190184.nist", {2, 4, 9, 15}, True),
        ("type7/TR_000000df_H.int", {2, 4, 7, 10}, True),
        ("type10/TR_000000df_H.int", {2, 4, 7, 10}, True),
        ("type10/Interpol_FRA_24000000448327A_FI.nist", {2, 10}, True),
        ("type9/HR_12883247_3190184.nist", {9}, True),
        ("palm15/109018515_export_test.nist", {14, 15}, True),
        ("efts_int/USA_TEST_efts.nist", {2, 4}, True),
        ("efts_int/TR_000000df_H.int", {2, 4, 7, 10}, True),
        ("signa/102556281_export_test.nist", {2, 14, 15}, True),
        ("signa/109018515_export_test.nist", {2, 14, 15}, True),
        ("tronques/Interpol_FABLStemp8865791272998619994.NST-neu.nst", set(), False),
        ("tronques/Interpol_NIST_File_INTERPOL_V5.03_-_730020_06N.nst", set(), False),
    ],
)
def test_fixture_parsing(relative, required_types, should_parse):
    fixture_path = BASE / relative
    assert fixture_path.exists(), f"Fixture missing: {fixture_path}"

    nist_file = NISTFile(str(fixture_path))
    parsed = nist_file.parse()

    if not should_parse:
        assert parsed is False
        return

    assert parsed is True
    types = set(nist_file.get_record_types())
    for t in required_types:
        assert t in types, f"Type-{t} absent in {relative}"
