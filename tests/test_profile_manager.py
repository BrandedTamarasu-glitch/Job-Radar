"""Tests for profile_manager module -- centralized profile I/O."""

import json
import re
import time

import pytest
from pathlib import Path
from unittest.mock import patch

from job_radar.profile_manager import (
    validate_profile,
    save_profile,
    load_profile,
    _rotate_backups,
    ProfileValidationError,
    MissingFieldError,
    InvalidTypeError,
    ProfileNotFoundError,
    ProfileCorruptedError,
    CURRENT_SCHEMA_VERSION,
    MAX_BACKUPS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_profile():
    """Minimal valid profile with only required fields."""
    return {
        "name": "Test User",
        "target_titles": ["Software Engineer", "Backend Developer"],
        "core_skills": ["Python", "PostgreSQL"],
    }


@pytest.fixture
def full_profile(valid_profile):
    """Valid profile with all optional fields populated."""
    return {
        **valid_profile,
        "years_experience": 7,
        "level": "senior",
        "location": "Remote",
        "arrangement": ["remote", "hybrid"],
        "domain_expertise": ["fintech"],
        "comp_floor": 120000,
        "dealbreakers": ["relocation required"],
        "min_score": 3.0,
    }


@pytest.fixture
def profile_path(tmp_path):
    """Path for a profile file inside tmp_path."""
    return tmp_path / "profile.json"


@pytest.fixture
def mock_backup_dir(tmp_path):
    """Mock get_backup_dir to return a temp directory."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    with patch("job_radar.profile_manager.get_backup_dir", return_value=backup_dir):
        yield backup_dir


# ---------------------------------------------------------------------------
# 1. Validation tests
# ---------------------------------------------------------------------------


def test_validate_valid_profile(valid_profile):
    """Minimal valid profile (name, target_titles, core_skills) passes validation."""
    validate_profile(valid_profile)  # should not raise


def test_validate_valid_profile_with_optional_fields(full_profile):
    """Profile with all optional fields populated passes validation."""
    validate_profile(full_profile)  # should not raise


def test_validate_missing_required_fields():
    """MissingFieldError is raised listing all missing required fields."""
    with pytest.raises(MissingFieldError) as exc_info:
        validate_profile({})
    assert "name" in exc_info.value.fields
    assert "target_titles" in exc_info.value.fields
    assert "core_skills" in exc_info.value.fields


def test_validate_invalid_type_target_titles(valid_profile):
    """InvalidTypeError raised when target_titles is not a list."""
    valid_profile["target_titles"] = "Software Engineer"
    with pytest.raises(InvalidTypeError) as exc_info:
        validate_profile(valid_profile)
    assert exc_info.value.field == "target_titles"


def test_validate_invalid_type_core_skills_empty(valid_profile):
    """InvalidTypeError raised when core_skills is an empty list."""
    valid_profile["core_skills"] = []
    with pytest.raises(InvalidTypeError) as exc_info:
        validate_profile(valid_profile)
    assert exc_info.value.field == "core_skills"


def test_validate_years_experience_out_of_range(valid_profile):
    """ProfileValidationError raised for years_experience outside 0-50."""
    valid_profile["years_experience"] = 51
    with pytest.raises(ProfileValidationError, match="out of range"):
        validate_profile(valid_profile)

    valid_profile["years_experience"] = -1
    with pytest.raises(ProfileValidationError, match="out of range"):
        validate_profile(valid_profile)


def test_validate_preserves_unknown_fields(valid_profile):
    """Unknown fields do not cause validation errors (forward-compatible)."""
    valid_profile["custom_field"] = "some custom value"
    valid_profile["future_feature"] = [1, 2, 3]
    validate_profile(valid_profile)  # should not raise


# ---------------------------------------------------------------------------
# 2. Atomic write tests
# ---------------------------------------------------------------------------


def test_save_creates_file(valid_profile, profile_path, mock_backup_dir):
    """save_profile creates the profile file at the specified path."""
    save_profile(valid_profile, profile_path)
    assert profile_path.exists()


def test_save_atomic_content(valid_profile, profile_path, mock_backup_dir):
    """Saved file contains valid JSON with all profile fields."""
    save_profile(valid_profile, profile_path)

    loaded = json.loads(profile_path.read_text(encoding="utf-8"))
    assert loaded["name"] == "Test User"
    assert loaded["target_titles"] == ["Software Engineer", "Backend Developer"]
    assert loaded["core_skills"] == ["Python", "PostgreSQL"]


def test_save_adds_schema_version(valid_profile, profile_path, mock_backup_dir):
    """schema_version is set to CURRENT_SCHEMA_VERSION even when not in input."""
    assert "schema_version" not in valid_profile
    save_profile(valid_profile, profile_path)

    loaded = json.loads(profile_path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == CURRENT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# 3. Backup tests
# ---------------------------------------------------------------------------


def test_save_creates_backup(valid_profile, profile_path, mock_backup_dir):
    """Second save creates a backup file in the backup directory."""
    save_profile(valid_profile, profile_path)
    # No backup yet (first save, file didn't exist before)
    assert len(list(mock_backup_dir.glob("profile_*.json"))) == 0

    # Second save should create a backup
    valid_profile["name"] = "Updated User"
    save_profile(valid_profile, profile_path)
    backups = list(mock_backup_dir.glob("profile_*.json"))
    assert len(backups) == 1


def test_backup_has_timestamp_filename(valid_profile, profile_path, mock_backup_dir):
    """Backup filename matches profile_YYYY-MM-DD_HH-MM-SS.json pattern."""
    save_profile(valid_profile, profile_path)
    save_profile(valid_profile, profile_path)

    backups = list(mock_backup_dir.glob("profile_*.json"))
    assert len(backups) == 1
    pattern = re.compile(r"^profile_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.json$")
    assert pattern.match(backups[0].name)


def test_backup_rotation_keeps_max(valid_profile, profile_path, mock_backup_dir):
    """Creating more than MAX_BACKUPS backups deletes oldest, keeps MAX_BACKUPS."""
    # Create initial file
    save_profile(valid_profile, profile_path)

    # Create MAX_BACKUPS + 2 additional saves (each creates a backup)
    for i in range(MAX_BACKUPS + 2):
        # Create backup files with distinct timestamps
        backup_file = mock_backup_dir / f"profile_2026-01-{i+1:02d}_12-00-00.json"
        backup_file.write_text("{}")
        # Touch to set mtime in order
        backup_file.touch()
        time.sleep(0.01)  # Ensure distinct mtime

    # There should be MAX_BACKUPS + 2 files now
    assert len(list(mock_backup_dir.glob("profile_*.json"))) == MAX_BACKUPS + 2

    # Rotate should trim to MAX_BACKUPS
    _rotate_backups(mock_backup_dir)
    remaining = list(mock_backup_dir.glob("profile_*.json"))
    assert len(remaining) == MAX_BACKUPS


def test_first_save_no_backup(valid_profile, profile_path, mock_backup_dir):
    """First save (no existing file) does not create a backup."""
    assert not profile_path.exists()
    save_profile(valid_profile, profile_path)

    backups = list(mock_backup_dir.glob("profile_*.json"))
    assert len(backups) == 0


# ---------------------------------------------------------------------------
# 4. Schema versioning tests
# ---------------------------------------------------------------------------


def test_load_adds_schema_version_to_legacy(valid_profile, profile_path, mock_backup_dir):
    """Loading a legacy profile (no schema_version) auto-migrates to v1 and saves."""
    # Write a legacy profile directly (no schema_version key)
    profile_path.write_text(json.dumps(valid_profile), encoding="utf-8")

    loaded = load_profile(profile_path)
    assert loaded["schema_version"] == CURRENT_SCHEMA_VERSION

    # Verify the file on disk was updated
    on_disk = json.loads(profile_path.read_text(encoding="utf-8"))
    assert on_disk["schema_version"] == CURRENT_SCHEMA_VERSION


def test_load_preserves_current_schema(valid_profile, profile_path, mock_backup_dir):
    """Loading a profile with current schema_version returns it unchanged."""
    valid_profile["schema_version"] = CURRENT_SCHEMA_VERSION
    profile_path.write_text(json.dumps(valid_profile), encoding="utf-8")

    loaded = load_profile(profile_path)
    assert loaded["schema_version"] == CURRENT_SCHEMA_VERSION


def test_load_ignores_future_schema(valid_profile, profile_path, mock_backup_dir):
    """Loading a profile with future schema_version does not error."""
    valid_profile["schema_version"] = 99
    profile_path.write_text(json.dumps(valid_profile), encoding="utf-8")

    loaded = load_profile(profile_path)
    assert loaded["schema_version"] == 99


# ---------------------------------------------------------------------------
# 5. Error handling tests
# ---------------------------------------------------------------------------


def test_load_missing_file_raises(tmp_path):
    """ProfileNotFoundError raised for non-existent file, with path in message."""
    missing = tmp_path / "nonexistent.json"
    with pytest.raises(ProfileNotFoundError) as exc_info:
        load_profile(missing)
    assert str(missing) in str(exc_info.value)


def test_load_corrupt_json_raises(profile_path):
    """ProfileCorruptedError raised for invalid JSON content."""
    profile_path.write_text("{not valid json!!!", encoding="utf-8")
    with pytest.raises(ProfileCorruptedError):
        load_profile(profile_path)


def test_save_rejects_invalid_profile(profile_path, mock_backup_dir):
    """ProfileValidationError raised before any file write for invalid data."""
    # Create a file first to verify it remains unchanged
    original = {"existing": "data"}
    profile_path.write_text(json.dumps(original), encoding="utf-8")

    with pytest.raises(ProfileValidationError):
        save_profile({}, profile_path)

    # Verify original file is untouched
    on_disk = json.loads(profile_path.read_text(encoding="utf-8"))
    assert on_disk == original


# ---------------------------------------------------------------------------
# 6. Round-trip tests
# ---------------------------------------------------------------------------


def test_round_trip_preserves_data(full_profile, profile_path, mock_backup_dir):
    """Save then load returns identical data (plus schema_version)."""
    save_profile(full_profile, profile_path)
    loaded = load_profile(profile_path)

    for key in full_profile:
        assert loaded[key] == full_profile[key], f"Mismatch on key '{key}'"
    assert loaded["schema_version"] == CURRENT_SCHEMA_VERSION


def test_round_trip_preserves_unknown_fields(valid_profile, profile_path, mock_backup_dir):
    """Custom fields survive a save + load round-trip (forward-compatible)."""
    valid_profile["custom_field"] = "user extension"
    valid_profile["nested_data"] = {"a": 1, "b": [2, 3]}

    save_profile(valid_profile, profile_path)
    loaded = load_profile(profile_path)

    assert loaded["custom_field"] == "user extension"
    assert loaded["nested_data"] == {"a": 1, "b": [2, 3]}
