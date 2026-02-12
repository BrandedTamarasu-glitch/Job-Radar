"""Tests for profile_display module and CLI integration.

Covers:
- Display function output (branded header, sections, field rendering)
- Field filtering (empty fields hidden, None fields hidden)
- Boolean/numeric formatting (Yes/No, plain values)
- NO_COLOR compliance (no ANSI codes)
- CLI flag recognition (--view-profile in parse_args)
- Help text documentation (--view-profile, --no-wizard updated)
"""

import os
import sys

import pytest

from job_radar.profile_display import display_profile
from job_radar.search import parse_args


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_profile():
    return {
        "name": "Test User",
        "target_titles": ["Software Engineer"],
        "core_skills": ["Python", "Docker"],
    }


@pytest.fixture
def full_profile(minimal_profile):
    return {
        **minimal_profile,
        "years_experience": 7,
        "level": "senior",
        "location": "Remote",
        "arrangement": ["remote", "hybrid"],
        "secondary_skills": ["React", "TypeScript"],
        "certifications": ["AWS Solutions Architect"],
        "domain_expertise": ["fintech", "healthcare"],
        "dealbreakers": ["PHP", "Salesforce"],
        "comp_floor": 120000,
        "highlights": ["Led team of 5 engineers"],
    }


@pytest.fixture
def sample_config():
    return {"min_score": 3.5, "new_only": True}


# ---------------------------------------------------------------------------
# Display Function Tests
# ---------------------------------------------------------------------------


class TestDisplayProfileBasic:
    """Test basic display output with minimal profile."""

    def test_display_profile_basic(self, minimal_profile, capsys):
        """Minimal profile renders with branded header and section structure."""
        display_profile(minimal_profile)
        output = capsys.readouterr().out

        assert "Job Radar Profile" in output
        assert "Test User" in output
        assert "IDENTITY" in output
        assert "SKILLS" in output

    def test_display_profile_full(self, full_profile, sample_config, capsys):
        """Full profile with all fields shows all populated fields."""
        display_profile(full_profile, sample_config)
        output = capsys.readouterr().out

        # Identity fields
        assert "Test User" in output
        assert "7 years (senior level)" in output
        assert "Remote" in output
        assert "remote, hybrid" in output

        # Skills fields
        assert "Python, Docker" in output
        assert "React, TypeScript" in output
        assert "AWS Solutions Architect" in output
        assert "fintech, healthcare" in output

        # Preferences (from config)
        assert "3.5" in output
        assert "Yes" in output

        # Filters
        assert "PHP, Salesforce" in output
        assert "$120,000" in output
        assert "Software Engineer" in output

    def test_display_profile_filters_empty_fields(self, capsys):
        """Empty lists, None values, and missing keys are NOT shown in output."""
        profile = {
            "name": "Sparse User",
            "target_titles": ["Dev"],
            "core_skills": ["Go"],
            "dealbreakers": [],
            "comp_floor": None,
            "secondary_skills": [],
            "certifications": [],
        }
        display_profile(profile)
        output = capsys.readouterr().out

        # These labels should NOT appear because values are empty/None
        assert "Dealbreakers" not in output
        assert "Min Compensation" not in output
        assert "Secondary Skills" not in output
        assert "Certifications" not in output

        # These should appear
        assert "Sparse User" in output
        assert "Go" in output

    def test_display_profile_lists_comma_separated(self, capsys):
        """core_skills and other list fields render as comma-separated."""
        profile = {
            "name": "List Tester",
            "target_titles": ["SRE", "DevOps"],
            "core_skills": ["Python", "Terraform", "Kubernetes"],
        }
        display_profile(profile)
        output = capsys.readouterr().out

        assert "Python, Terraform, Kubernetes" in output
        assert "SRE, DevOps" in output

    def test_display_profile_boolean_yes_no(self, minimal_profile, capsys):
        """new_only=True shows 'Yes', new_only=False shows 'No'."""
        display_profile(minimal_profile, {"new_only": True})
        output_yes = capsys.readouterr().out
        assert "Yes" in output_yes

        display_profile(minimal_profile, {"new_only": False})
        output_no = capsys.readouterr().out
        assert "No" in output_no

    def test_display_profile_numeric_plain(self, capsys):
        """min_score shows plain number, comp_floor shows formatted dollar amount."""
        profile = {
            "name": "Num User",
            "target_titles": ["Dev"],
            "core_skills": ["Rust"],
            "comp_floor": 120000,
        }
        display_profile(profile, {"min_score": 3.5})
        output = capsys.readouterr().out

        assert "3.5" in output
        assert "$120,000" in output

    def test_display_profile_section_headers(self, full_profile, sample_config, capsys):
        """Output contains section headers (IDENTITY, SKILLS, etc.)."""
        display_profile(full_profile, sample_config)
        output = capsys.readouterr().out

        assert "IDENTITY" in output
        assert "SKILLS" in output
        assert "PREFERENCES" in output
        assert "FILTERS" in output


# ---------------------------------------------------------------------------
# Field Filtering Tests
# ---------------------------------------------------------------------------


class TestFieldFiltering:
    """Test that empty/missing fields are properly hidden."""

    def test_empty_dealbreakers_hidden(self, capsys):
        """dealbreakers=[] does not appear in output."""
        profile = {
            "name": "No Deals",
            "target_titles": ["Engineer"],
            "core_skills": ["Java"],
            "dealbreakers": [],
        }
        display_profile(profile)
        output = capsys.readouterr().out
        assert "Dealbreakers" not in output

    def test_none_comp_floor_hidden(self, capsys):
        """comp_floor=None does not appear in output."""
        profile = {
            "name": "No Comp",
            "target_titles": ["Engineer"],
            "core_skills": ["Java"],
            "comp_floor": None,
        }
        display_profile(profile)
        output = capsys.readouterr().out
        assert "Min Compensation" not in output

    def test_no_config_skips_preferences(self, minimal_profile, capsys):
        """When config is None or empty {}, no PREFERENCES section appears."""
        display_profile(minimal_profile, None)
        output_none = capsys.readouterr().out
        assert "PREFERENCES" not in output_none

        display_profile(minimal_profile, {})
        output_empty = capsys.readouterr().out
        assert "PREFERENCES" not in output_empty


# ---------------------------------------------------------------------------
# NO_COLOR Compliance Test
# ---------------------------------------------------------------------------


class TestNoColor:
    """Test NO_COLOR compliance."""

    def test_display_profile_no_color(self, minimal_profile, monkeypatch, capsys):
        """With NO_COLOR=1, output contains no ANSI escape codes."""
        monkeypatch.setenv("NO_COLOR", "1")

        # Disable colors on _Colors class (same approach as --no-color handler)
        from job_radar.search import _Colors
        original_attrs = {}
        color_attrs = ["RESET", "BOLD", "GREEN", "YELLOW", "RED", "CYAN", "DIM"]
        for attr in color_attrs:
            original_attrs[attr] = getattr(_Colors, attr)
            monkeypatch.setattr(_Colors, attr, "")
        monkeypatch.setattr(_Colors, "_enabled", False)

        display_profile(minimal_profile)
        output = capsys.readouterr().out

        # No ANSI escape sequences
        assert "\033" not in output


# ---------------------------------------------------------------------------
# CLI Integration Tests
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    """Test CLI flag recognition and help text."""

    def test_view_profile_flag_in_args(self, monkeypatch):
        """parse_args() recognizes --view-profile as boolean flag."""
        monkeypatch.setattr(sys, "argv", ["prog", "--view-profile"])
        args = parse_args()
        assert args.view_profile is True

    def test_view_profile_default_false(self, monkeypatch):
        """--view-profile defaults to False when not specified."""
        monkeypatch.setattr(sys, "argv", ["prog"])
        args = parse_args()
        assert args.view_profile is False

    def test_no_wizard_help_text_updated(self, monkeypatch, capsys):
        """--help output mentions 'profile preview' in --no-wizard description."""
        monkeypatch.setattr(sys, "argv", ["prog", "--help"])
        with pytest.raises(SystemExit) as exc_info:
            parse_args()
        assert exc_info.value.code == 0

        output = capsys.readouterr().out
        assert "profile preview" in output

    def test_help_documents_view_profile(self, monkeypatch, capsys):
        """--help output contains --view-profile."""
        monkeypatch.setattr(sys, "argv", ["prog", "--help"])
        with pytest.raises(SystemExit):
            parse_args()

        output = capsys.readouterr().out
        assert "--view-profile" in output

    def test_help_documents_profile_management(self, monkeypatch, capsys):
        """help epilog mentions profile management section."""
        monkeypatch.setattr(sys, "argv", ["prog", "--help"])
        with pytest.raises(SystemExit):
            parse_args()

        output = capsys.readouterr().out
        assert "Profile Management:" in output
        assert "--view-profile" in output
        assert "--no-wizard" in output
