"""Tests for profile summary report rendering."""

from __future__ import annotations

from job_radar.report_profile import html_profile_section


def test_html_profile_section_renders_landmarks_and_profile_fields():
    html = html_profile_section({
        "level": "senior",
        "years_experience": 8,
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python", "FastAPI"],
        "location": "Remote",
        "arrangement": ["remote"],
        "target_market": "SaaS",
        "certifications": ["AWS"],
        "comp_floor": 140000,
        "dealbreakers": ["relocation required"],
    })

    assert 'aria-labelledby="profile-heading"' in html
    assert 'id="profile-heading"' in html
    assert "Backend Engineer" in html
    assert "Python, FastAPI" in html
    assert "Comp floor:</strong> $140,000" in html
    assert "relocation required" in html


def test_html_profile_section_escapes_profile_values():
    html = html_profile_section({
        "level": "<senior>",
        "target_titles": ["<Backend>"],
        "core_skills": ["Python"],
    })

    assert "&lt;senior&gt;" in html
    assert "&lt;Backend&gt;" in html
    assert "<senior>" not in html
