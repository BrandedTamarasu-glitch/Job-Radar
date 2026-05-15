"""Match explanation helpers for generated reports."""

from __future__ import annotations

import html
from typing import Any


def match_highlights(highlights: list[str], matched_skills: list[str], job: Any) -> list[str]:
    """Find profile highlights relevant to this job's matched skills."""
    relevant = []
    searchable = (job.title + " " + job.description).lower()
    for highlight in highlights:
        highlight_lower = highlight.lower()
        if any(skill.lower() in highlight_lower for skill in matched_skills):
            relevant.append(highlight)
        elif any(word in highlight_lower for word in searchable.split()[:20] if len(word) > 4):
            relevant.append(highlight)
    return relevant[:3]


def skill_callout_groups(skill: dict, profile: dict) -> list[tuple[str, list[str]]]:
    """Return grouped must-have/nice-to-have skill callouts."""
    groups = []
    missing_core = list(skill.get("missing_core") or [])
    if missing_core:
        groups.append(("Missing must-have skills", missing_core))

    matched_secondary = list(skill.get("matched_secondary") or [])
    if matched_secondary:
        groups.append(("Nice-to-have matches", matched_secondary))

    secondary_skills = list(profile.get("secondary_skills") or [])
    matched_secondary_lower = {value.casefold() for value in matched_secondary}
    missing_secondary = [
        value for value in secondary_skills
        if value.casefold() not in matched_secondary_lower
    ]
    if missing_secondary:
        groups.append(("Missing nice-to-have skills", missing_secondary))

    return groups


def match_summary_text(result: dict) -> str:
    """Build a concise explanation for why a job matched."""
    score = result["score"]
    components = score.get("components", {})
    skill = components.get("skill_match", {})
    title = components.get("title_relevance", {})
    seniority = components.get("seniority", {})
    response = components.get("response", {})

    parts = []
    if skill.get("ratio"):
        parts.append(f"{skill['ratio']} core skills")
    if title.get("reason"):
        parts.append(f"title: {title['reason']}")
    if seniority.get("reason"):
        parts.append(f"seniority: {seniority['reason']}")
    if response.get("likelihood"):
        parts.append(f"{response['likelihood']} response likelihood")

    if not parts:
        return f"Matched with score {score.get('overall', 'N/A')}"
    return "; ".join(parts)


def html_match_summary(result: dict) -> str:
    """Generate the visible match-summary callout for a job card."""
    return (
        '<p class="match-summary small mb-3">'
        f'<strong>Why this matched:</strong> {html.escape(match_summary_text(result))}'
        '</p>'
    )
