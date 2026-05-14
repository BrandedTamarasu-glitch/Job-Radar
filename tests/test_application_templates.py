"""Tests for application follow-through note templates."""

import pytest

from job_radar.application_templates import (
    APPLICATION_NOTE_TEMPLATES,
    get_application_note_templates,
    render_application_note_template,
)


def test_application_note_templates_cover_sprint_i_use_cases():
    """Built-in templates cover follow-up, recruiter response, and cover letter prep."""
    assert set(APPLICATION_NOTE_TEMPLATES) == {
        "follow_up",
        "recruiter_response",
        "cover_letter_prep",
    }


def test_get_application_note_templates_returns_display_order():
    templates = get_application_note_templates()

    assert [template.key for template in templates] == [
        "follow_up",
        "recruiter_response",
        "cover_letter_prep",
    ]
    assert all(template.label for template in templates)
    assert all(template.description for template in templates)


def test_render_application_note_template_uses_application_and_profile_context():
    rendered = render_application_note_template(
        "follow_up",
        {"title": "Backend Engineer", "company": "Acme"},
        {"name": "Jane", "core_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]},
    )

    assert "Acme" in rendered
    assert "Backend Engineer" in rendered
    assert "Jane" in rendered
    assert "Python, FastAPI, PostgreSQL" in rendered
    assert "Docker" not in rendered


def test_render_application_note_template_has_safe_fallbacks():
    rendered = render_application_note_template("cover_letter_prep", {}, {})

    assert "the role" in rendered
    assert "the company" in rendered
    assert "the candidate" in rendered
    assert "relevant experience" in rendered


def test_render_application_note_template_rejects_unknown_template():
    with pytest.raises(KeyError, match="Unknown application note template"):
        render_application_note_template("unknown")
