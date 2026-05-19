"""Tests for shared profile schema parsing helpers."""

import re

import pytest

from job_radar.profile_schema import (
    COMPENSATION_INVALID_MESSAGE,
    COMPENSATION_NEGATIVE_MESSAGE,
    COMPENSATION_TOO_HIGH_MESSAGE,
    YEARS_INVALID_MESSAGE,
    YEARS_NEGATIVE_MESSAGE,
    YEARS_TOO_HIGH_MESSAGE,
    derive_level,
    parse_compensation_floor,
    parse_years_experience,
)


def test_parse_years_experience_accepts_valid_input():
    assert parse_years_experience("5") == 5
    assert parse_years_experience(" 0 ") == 0


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("abc", YEARS_INVALID_MESSAGE),
        ("-1", YEARS_NEGATIVE_MESSAGE),
        ("51", YEARS_TOO_HIGH_MESSAGE),
    ],
)
def test_parse_years_experience_rejects_invalid_input(value, message):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_years_experience(value)


@pytest.mark.parametrize(
    ("years", "level"),
    [
        (0, "junior"),
        (2, "mid"),
        (5, "senior"),
        (10, "principal"),
    ],
)
def test_derive_level_uses_profile_thresholds(years, level):
    assert derive_level(years) == level


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", None),
        ("150k", 150000),
        ("$150,000", 150000),
        ("125000.50", 125000),
    ],
)
def test_parse_compensation_floor_accepts_supported_formats(value, expected):
    assert parse_compensation_floor(value) == expected


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("abc", COMPENSATION_INVALID_MESSAGE),
        ("-1", COMPENSATION_NEGATIVE_MESSAGE),
        ("1000001", COMPENSATION_TOO_HIGH_MESSAGE),
    ],
)
def test_parse_compensation_floor_rejects_invalid_input(value, message):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_compensation_floor(value)
