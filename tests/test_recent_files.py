"""Tests for RecentFiles helper."""

from pathlib import Path

from mynist.utils.recent_files import RecentFiles


def test_recent_files_add_and_get(tmp_path):
    storage = tmp_path / "recent.json"
    manager = RecentFiles(storage_path=storage, max_entries=2)

    manager.add(str(tmp_path / "a.nist"), last_mode="viewer", summary_types=[2, 14])
    manager.add(str(tmp_path / "b.nist"), last_mode="pdf", summary_types=[1, 2])

    entries = manager.get_entries()
    assert len(entries) == 2
    assert entries[0]["path"].endswith("b.nist")
    assert entries[0]["last_mode"] == "pdf"
    assert entries[0]["summary_types"] == [1, 2]


def test_recent_files_dedup_and_limit(tmp_path):
    storage = tmp_path / "recent.json"
    manager = RecentFiles(storage_path=storage, max_entries=2)

    first = tmp_path / "a.nist"
    second = tmp_path / "b.nist"
    third = tmp_path / "c.nist"

    manager.add(str(first))
    manager.add(str(second))
    manager.add(str(first))  # dedup brings it to front
    manager.add(str(third))  # exceeds max_entries=2

    entries = manager.get_entries()
    assert len(entries) == 2
    # a.nist re-added before c.nist should now be second after c
    assert entries[0]["path"].endswith("c.nist")
    assert entries[1]["path"].endswith("a.nist")


def test_recent_files_filter_missing(tmp_path):
    storage = tmp_path / "recent.json"
    present = tmp_path / "present.nist"
    present.touch()

    manager = RecentFiles(storage_path=storage, max_entries=4)
    manager.add(str(present))
    manager.add(str(tmp_path / "missing.nist"))

    entries_all = manager.get_entries()
    assert len(entries_all) == 2
    exists_flags = {Path(item["path"]).name: item["exists"] for item in entries_all}
    assert exists_flags["missing.nist"] is False
    assert exists_flags["present.nist"] is True

    entries_only_existing = manager.get_entries(include_missing=False)
    assert len(entries_only_existing) == 1
    assert entries_only_existing[0]["path"].endswith("present.nist")
