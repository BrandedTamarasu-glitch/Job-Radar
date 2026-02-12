"""Centralized profile I/O with atomic writes, backups, validation, and schema versioning."""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from .paths import get_backup_dir

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CURRENT_SCHEMA_VERSION = 1
MAX_BACKUPS = 10


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class ProfileValidationError(Exception):
    """Base exception for profile validation errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class MissingFieldError(ProfileValidationError):
    """One or more required fields are missing from the profile."""

    def __init__(self, fields: list[str]):
        self.fields = fields
        names = ", ".join(fields)
        message = f"Missing required field(s): {names}"
        super().__init__(message)


class InvalidTypeError(ProfileValidationError):
    """A field has the wrong type or is empty when it should not be."""

    def __init__(self, field: str, expected: str, got: type):
        self.field = field
        self.expected = expected
        self.got = got
        message = f"Field '{field}' must be {expected}, got {got.__name__}"
        super().__init__(message)


class ProfileNotFoundError(ProfileValidationError):
    """Profile file does not exist at the expected path."""

    def __init__(self, path: Path):
        self.path = path
        message = f"Profile not found at {path} -- please run the setup wizard or check the file path."
        super().__init__(message)


class ProfileCorruptedError(ProfileValidationError):
    """Profile file contains invalid JSON."""

    def __init__(self, path: Path, reason: str):
        self.path = path
        self.reason = reason
        message = f"Profile at {path} is corrupted: {reason}"
        super().__init__(message)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_profile(profile: dict) -> None:
    """Validate profile structure and field constraints.

    Checks required fields, types, and value ranges. Raises a
    ProfileValidationError subclass on the first problem found.

    Unknown fields are silently preserved (forward-compatible).
    """
    if not isinstance(profile, dict):
        raise InvalidTypeError("profile", "dict", type(profile))

    # Required fields (what the scoring engine needs)
    required = ["name", "target_titles", "core_skills"]
    missing = [f for f in required if f not in profile]
    if missing:
        raise MissingFieldError(missing)

    # Type checks for required list fields
    if not isinstance(profile["target_titles"], list) or not profile["target_titles"]:
        raise InvalidTypeError(
            "target_titles", "non-empty list", type(profile["target_titles"])
        )

    if not isinstance(profile["core_skills"], list) or not profile["core_skills"]:
        raise InvalidTypeError(
            "core_skills", "non-empty list", type(profile["core_skills"])
        )

    # Optional field validation
    if "years_experience" in profile:
        years = profile["years_experience"]
        if not isinstance(years, int):
            raise InvalidTypeError("years_experience", "integer", type(years))
        if not (0 <= years <= 50):
            raise ProfileValidationError(
                f"Your years_experience value of {years} is out of range "
                "-- it must be between 0 and 50."
            )

    if "comp_floor" in profile:
        comp = profile["comp_floor"]
        if not isinstance(comp, (int, float)):
            raise InvalidTypeError("comp_floor", "number", type(comp))
        if not (0 <= comp <= 1_000_000):
            raise ProfileValidationError(
                f"Your comp_floor value of {comp} is out of range "
                "-- it must be between 0 and 1,000,000."
            )

    if "arrangement" in profile:
        arr = profile["arrangement"]
        if not isinstance(arr, list):
            raise InvalidTypeError("arrangement", "list", type(arr))

    if "min_score" in profile:
        score = profile["min_score"]
        if not isinstance(score, (int, float)):
            raise InvalidTypeError("min_score", "number", type(score))
        if not (1.0 <= float(score) <= 5.0):
            raise ProfileValidationError(
                f"Your min_score value of {score} is out of range "
                "-- it must be between 1.0 and 5.0."
            )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _create_backup(profile_path: Path) -> Path | None:
    """Create a timestamped backup of the current profile.

    Returns the backup path on success, or None if the profile does not
    exist or the backup fails. Backup failure is logged as a warning but
    never blocks the caller.
    """
    if not profile_path.exists():
        return None

    try:
        backup_dir = get_backup_dir()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = backup_dir / f"profile_{timestamp}.json"

        # Simple file copy (not atomic -- backup corruption is recoverable)
        backup_path.write_text(profile_path.read_text(encoding="utf-8"), encoding="utf-8")
        return backup_path
    except Exception:
        log.warning("Could not create backup for %s", profile_path)
        return None


def _rotate_backups(backup_dir: Path, max_backups: int = MAX_BACKUPS) -> None:
    """Keep only the *max_backups* most recent backup files.

    Sorts by modification time (newest first) and silently deletes any
    beyond the limit.
    """
    backups = sorted(
        backup_dir.glob("profile_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for old_backup in backups[max_backups:]:
        try:
            old_backup.unlink()
        except Exception:
            pass  # silent rotation per user decision


def _write_json_atomic(path: Path, data: dict) -> None:
    """Write *data* as JSON to *path* using the temp-file-plus-rename pattern.

    Extracted from wizard.py for reuse. Guarantees that *path* is never
    left in a partially-written state.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        Path(tmp_path).replace(path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise


# ---------------------------------------------------------------------------
# Public I/O
# ---------------------------------------------------------------------------

def save_profile(profile_data: dict, profile_path: Path) -> None:
    """Validate, back up, and atomically save a profile.

    1. Validates *profile_data* -- never writes invalid data.
    2. Sets ``schema_version`` if absent.
    3. Creates a timestamped backup of the existing file (if any).
    4. Rotates old backups (keeps ``MAX_BACKUPS`` most recent).
    5. Atomically writes the new profile.
    """
    validate_profile(profile_data)

    profile_data.setdefault("schema_version", CURRENT_SCHEMA_VERSION)

    # Backup existing file
    file_existed = profile_path.exists()
    backup_result = _create_backup(profile_path)

    if backup_result is not None:
        print("Profile backed up")
    elif file_existed:
        log.warning("Could not create backup for %s, continuing with save", profile_path)

    _rotate_backups(get_backup_dir())
    _write_json_atomic(profile_path, profile_data)


def load_profile(profile_path: Path) -> dict:
    """Load, migrate, validate, and return a profile dict.

    - Raises ``ProfileNotFoundError`` if the file is missing.
    - Raises ``ProfileCorruptedError`` if the JSON is invalid.
    - Migrates schema version 0 (pre-v1.5.0) to current and auto-saves.
    - Silently ignores unknown (future) schema versions.
    - Validates the profile before returning.
    """
    if not profile_path.exists():
        raise ProfileNotFoundError(profile_path)

    try:
        with open(profile_path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        raise ProfileCorruptedError(profile_path, str(e)) from e

    # Schema migration
    schema_version = profile.get("schema_version", 0)

    if schema_version == 0:
        # Pre-v1.5.0 profile -- add schema_version and auto-save
        profile["schema_version"] = CURRENT_SCHEMA_VERSION
        save_profile(profile, profile_path)
    # schema_version > CURRENT_SCHEMA_VERSION: ignore silently (best-effort)

    validate_profile(profile)
    return profile
