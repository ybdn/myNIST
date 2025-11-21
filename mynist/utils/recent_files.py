"""Recent files persistence and helpers."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any


DEFAULT_RECENT_PATH = Path.home() / ".config" / "mynist" / "recent_files.json"


@dataclass
class RecentFileEntry:
    """Represents a recent file entry."""

    path: str
    opened_at: str
    last_mode: str = "viewer"
    summary_types: Optional[List[int]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecentFileEntry":
        """Create entry from dict, being lenient on missing keys."""
        return cls(
            path=data.get("path", ""),
            opened_at=data.get("opened_at", ""),
            last_mode=data.get("last_mode", "viewer"),
            summary_types=data.get("summary_types") or None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise entry for JSON."""
        payload = asdict(self)
        if payload.get("summary_types") is None:
            payload.pop("summary_types")
        return payload


class RecentFiles:
    """Manage persistence and retrieval of recent files."""

    def __init__(self, storage_path: Optional[Path] = None, max_entries: int = 8):
        self.storage_path = storage_path or DEFAULT_RECENT_PATH
        self.max_entries = max_entries
        self.entries: List[RecentFileEntry] = []
        self.load()

    def load(self):
        """Load recent files from disk."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, "r", encoding="utf-8") as handle:
                    raw = json.load(handle)
                self.entries = [
                    RecentFileEntry.from_dict(item)
                    for item in raw
                    if isinstance(item, dict) and item.get("path")
                ]
            else:
                self.entries = []
        except Exception:
            # Do not fail app start on JSON issues; start clean list.
            self.entries = []

    def save(self):
        """Persist current entries to disk."""
        try:
            storage_path = Path(self.storage_path)
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(storage_path, "w", encoding="utf-8") as handle:
                json.dump([entry.to_dict() for entry in self.entries], handle, indent=2)
        except Exception:
            # Intentionally swallow errors to avoid crashing UI flows.
            return

    def clear(self):
        """Remove all persisted recents."""
        self.entries = []
        self.save()

    def remove(self, path: str):
        """Remove a specific path from recents."""
        normalized = str(Path(path).expanduser())
        self.entries = [entry for entry in self.entries if entry.path != normalized]
        self.save()

    def add(
        self,
        path: str,
        last_mode: str = "viewer",
        summary_types: Optional[List[int]] = None,
    ):
        """
        Add or update a recent entry.

        Args:
            path: File path to store.
            last_mode: Last mode used with this file (viewer/comparison/pdf).
            summary_types: Optional list of record types present.
        """
        if not path:
            return

        normalized = str(Path(path).expanduser())
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        new_entry = RecentFileEntry(
            path=normalized,
            opened_at=timestamp,
            last_mode=last_mode,
            summary_types=summary_types or None,
        )

        # Deduplicate on path, keeping newest first.
        existing = [entry for entry in self.entries if entry.path != normalized]
        self.entries = [new_entry] + existing
        self.entries = self.entries[: self.max_entries]
        self.save()

    def get_entries(self, include_missing: bool = True) -> List[Dict[str, Any]]:
        """
        Return entries formatted for UI consumption.

        Args:
            include_missing: When False, filter out files that no longer exist.
        """
        formatted: List[Dict[str, Any]] = []
        for entry in self.entries:
            exists = Path(entry.path).exists()
            if not exists and not include_missing:
                continue

            formatted.append(
                {
                    "path": entry.path,
                    "opened_at": entry.opened_at,
                    "last_mode": entry.last_mode,
                    "summary_types": entry.summary_types or [],
                    "exists": exists,
                }
            )
        return formatted
