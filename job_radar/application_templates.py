"""Reusable note templates for application follow-through."""

from __future__ import annotations

from dataclasses import dataclass
from string import Template
from typing import Any


@dataclass(frozen=True)
class ApplicationNoteTemplate:
    """Display and rendering metadata for an application note template."""

    key: str
    label: str
    description: str
    body: str


APPLICATION_NOTE_TEMPLATES = {
    "follow_up": ApplicationNoteTemplate(
        key="follow_up",
        label="Follow-up",
        description="Short reminder after applying or interviewing.",
        body=(
            "Follow up with ${company} about the ${title} role. "
            "Mention ${candidate_name}'s fit around ${skills} and ask about next steps."
        ),
    ),
    "recruiter_response": ApplicationNoteTemplate(
        key="recruiter_response",
        label="Recruiter Response",
        description="Prep notes for replying to a recruiter.",
        body=(
            "Reply to ${company} recruiter about ${title}. Confirm interest, availability, "
            "target compensation, and highlight ${skills}."
        ),
    ),
    "cover_letter_prep": ApplicationNoteTemplate(
        key="cover_letter_prep",
        label="Cover Letter Prep",
        description="Drafting checklist for a tailored cover letter.",
        body=(
            "Draft cover letter for ${title} at ${company}: connect the role to "
            "${candidate_name}'s ${skills}, then add one measurable project highlight."
        ),
    ),
}


def get_application_note_templates() -> list[ApplicationNoteTemplate]:
    """Return note templates in display order."""
    return list(APPLICATION_NOTE_TEMPLATES.values())


def render_application_note_template(
    template_key: str,
    application: dict[str, Any] | None = None,
    profile: dict[str, Any] | None = None,
) -> str:
    """Render a note template with application/profile context."""
    template = APPLICATION_NOTE_TEMPLATES.get(template_key)
    if template is None:
        raise KeyError(f"Unknown application note template: {template_key}")

    values = _template_values(application or {}, profile or {})
    return Template(template.body).safe_substitute(values)


def _template_values(application: dict[str, Any], profile: dict[str, Any]) -> dict[str, str]:
    skills = profile.get("core_skills") or profile.get("secondary_skills") or []
    if isinstance(skills, list):
        skills_text = ", ".join(str(skill) for skill in skills[:3] if str(skill).strip())
    else:
        skills_text = str(skills).strip()

    return {
        "title": str(application.get("title") or "the role"),
        "company": str(application.get("company") or "the company"),
        "candidate_name": str(profile.get("name") or "the candidate"),
        "skills": skills_text or "relevant experience",
    }
