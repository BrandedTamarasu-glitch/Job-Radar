"""Tests for saved search presets."""

from job_radar.search_presets import (
    apply_search_preset,
    format_preset_list,
    preset_choices,
)


def test_preset_choices_are_stable():
    """Preset choices expose the supported CLI names in order."""
    assert preset_choices() == ["remote-backend", "local-hybrid", "contract"]


def test_apply_search_preset_does_not_mutate_profile():
    """Presets are run-specific overlays, not profile rewrites."""
    profile = {
        "name": "Test User",
        "target_titles": ["Software Engineer"],
        "core_skills": ["Python"],
        "location": "Seattle, WA",
        "arrangement": ["onsite"],
    }

    result = apply_search_preset(profile, "remote-backend")

    assert profile["location"] == "Seattle, WA"
    assert profile["arrangement"] == ["onsite"]
    assert result["location"] == "Remote"
    assert result["target_market"] == "Remote"
    assert result["arrangement"] == ["remote"]
    assert result["target_titles"][:4] == [
        "Senior Backend Engineer",
        "Backend Engineer",
        "Python Developer",
        "API Engineer",
    ]
    assert "Software Engineer" in result["target_titles"]


def test_contract_preset_deduplicates_existing_titles_case_insensitively():
    """Preset titles are prepended without duplicate title variants."""
    profile = {
        "name": "Test User",
        "target_titles": ["contract backend engineer", "Platform Engineer"],
        "core_skills": ["Python"],
    }

    result = apply_search_preset(profile, "contract")

    assert result["target_titles"].count("Contract Backend Engineer") == 1
    assert "Platform Engineer" in result["target_titles"]


def test_format_preset_list_includes_descriptions():
    """List output is useful when users are choosing a preset."""
    output = format_preset_list()

    assert "Available search presets" in output
    assert "remote-backend" in output
    assert "local-hybrid" in output
    assert "contract" in output
