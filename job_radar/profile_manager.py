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
