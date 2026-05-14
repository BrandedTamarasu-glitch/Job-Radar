"""Portable app-data export helpers for backup and migration."""

from __future__ import annotations

import json
import shutil
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


@dataclass(frozen=True)
class PortableBundleValidation:
    """Validation result for an app-data portability bundle."""

    is_valid: bool
    files: list[str]
    errors: list[str]


@dataclass(frozen=True)
class PortableRestoreResult:
    """Result of restoring files from a portability bundle."""

    restored_files: list[str]
    backup_files: list[str]


PORTABLE_DATA_FILES = (
    ("profile.json", "profile.json", "Profile and scoring preferences"),
    ("config.json", "config.json", "App settings"),
    ("saved_searches.json", "saved_searches.json", "Saved and recent searches"),
    ("review_state.json", "review_state.json", "Search review queue"),
    ("results/tracker.json", "results/tracker.json", "Tracker, applications, and diagnostics"),
)
SUPPORTED_ARCHIVE_PATHS = {archive_name for _, archive_name, _ in PORTABLE_DATA_FILES}


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


def validate_app_data_bundle(bundle_path: str | Path) -> PortableBundleValidation:
    """Validate a portability ZIP before restore code mutates app data."""
    path = Path(bundle_path)
    errors: list[str] = []
    files: list[str] = []

    if not path.is_file():
        return PortableBundleValidation(False, [], [f"Bundle not found: {path}"])

    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "manifest.json" not in names:
                return PortableBundleValidation(False, [], ["Bundle is missing manifest.json"])

            try:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return PortableBundleValidation(False, [], ["Bundle manifest is not valid JSON"])

            if manifest.get("version") != 1:
                errors.append("Unsupported bundle manifest version")

            manifest_files = manifest.get("files")
            if not isinstance(manifest_files, list):
                errors.append("Bundle manifest files must be a list")
                manifest_files = []

            for item in manifest_files:
                if not isinstance(item, dict):
                    errors.append("Bundle manifest contains an invalid file entry")
                    continue
                archive_name = str(item.get("path") or "")
                if archive_name not in SUPPORTED_ARCHIVE_PATHS:
                    errors.append(f"Unsupported bundle file path: {archive_name}")
                    continue
                if archive_name not in names:
                    errors.append(f"Manifest file missing from bundle: {archive_name}")
                    continue
                files.append(archive_name)

            unexpected = sorted(
                name for name in names
                if name != "manifest.json" and name not in SUPPORTED_ARCHIVE_PATHS
            )
            for name in unexpected:
                errors.append(f"Unexpected bundle file: {name}")
    except zipfile.BadZipFile:
        return PortableBundleValidation(False, [], ["Bundle is not a valid ZIP file"])

    return PortableBundleValidation(not errors, files, errors)


def restore_app_data_bundle(
    bundle_path: str | Path,
    *,
    data_dir: Path | None = None,
    backup_existing: bool = True,
    now: datetime | None = None,
) -> PortableRestoreResult:
    """Restore a validated app-data bundle into the app data directory."""
    validation = validate_app_data_bundle(bundle_path)
    if not validation.is_valid:
        raise ValueError("; ".join(validation.errors))

    root = data_dir or get_data_dir()
    backup_files: list[str] = []
    timestamp = _compact_timestamp(now)

    with zipfile.ZipFile(bundle_path) as archive:
        for archive_name in validation.files:
            destination = root / archive_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if backup_existing and destination.exists():
                backup_path = destination.with_name(f"{destination.name}.{timestamp}.bak")
                shutil.copy2(destination, backup_path)
                backup_files.append(str(backup_path.relative_to(root)))
            with archive.open(archive_name) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)

    return PortableRestoreResult(
        restored_files=list(validation.files),
        backup_files=backup_files,
    )


def _timestamp(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).isoformat()


def _compact_timestamp(now: datetime | None = None) -> str:
    return _timestamp(now).replace("+00:00", "Z").replace(":", "").replace("-", "")
