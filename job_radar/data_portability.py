"""Portable app-data export helpers for backup and migration."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from job_radar.paths import get_data_dir


@dataclass(frozen=True)
class PortableDataFile:
    """One app-data file that can be included in a portability bundle."""

    source: Path
    archive_name: str
    description: str


PORTABLE_DATA_FILES = (
    ("profile.json", "profile.json", "Profile and scoring preferences"),
    ("config.json", "config.json", "App settings"),
    ("saved_searches.json", "saved_searches.json", "Saved and recent searches"),
    ("review_state.json", "review_state.json", "Search review queue"),
    ("results/tracker.json", "results/tracker.json", "Tracker, applications, and diagnostics"),
)


def list_portable_data_files(data_dir: Path | None = None) -> list[PortableDataFile]:
    """Return existing app-data files that belong in a portability export."""
    root = data_dir or get_data_dir()
    files = []
    for relative_path, archive_name, description in PORTABLE_DATA_FILES:
        source = root / relative_path
        if source.is_file():
            files.append(
                PortableDataFile(
                    source=source,
                    archive_name=archive_name,
                    description=description,
                )
            )
    return files


def export_app_data_bundle(
    output_path: str | Path,
    *,
    data_dir: Path | None = None,
    now: datetime | None = None,
) -> Path:
    """Create a ZIP bundle containing portable Job Radar app data."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = list_portable_data_files(data_dir)
    manifest = {
        "version": 1,
        "created_at": _timestamp(now),
        "files": [
            {
                "path": file.archive_name,
                "description": file.description,
            }
            for file in files
        ],
    }

    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        for file in files:
            archive.write(file.source, file.archive_name)

    return destination


def _timestamp(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).isoformat()
