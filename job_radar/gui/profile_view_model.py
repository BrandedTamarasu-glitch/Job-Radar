"""View-model helpers for the Profile tab summary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProfileSummaryRow:
    """Display-ready profile summary row."""

    label: str
    value: str


@dataclass(frozen=True)
class ProfileReadinessDisplay:
    """Display-ready profile readiness text."""

    summary: str
    guidance_text: str | None
    scoring_signals_text: str | None


def build_profile_readiness_display(readiness: Any, scoring_items: list[str]) -> ProfileReadinessDisplay:
    """Return Profile tab readiness summary and detail text."""
    summary = f"{readiness.status} ({readiness.score}/{readiness.max_score})"
    guidance_items = list(readiness.missing_required or readiness.recommendations[:3])
    guidance_text = "\n".join(f"- {item}" for item in guidance_items) if guidance_items else None
    scoring_signals_text = "\n".join(scoring_items) if scoring_items else None
    return ProfileReadinessDisplay(
        summary=summary,
        guidance_text=guidance_text,
        scoring_signals_text=scoring_signals_text,
    )


def build_profile_summary_rows(profile: dict[str, Any]) -> list[ProfileSummaryRow]:
    """Return display rows for the Profile tab summary."""
    rows = [
        ProfileSummaryRow("Name:", str(profile.get("name") or "N/A")),
        ProfileSummaryRow("Target Titles:", _join_list(profile.get("target_titles"))),
        ProfileSummaryRow("Core Skills:", _join_list(profile.get("core_skills"))),
    ]

    if profile.get("secondary_skills"):
        rows.append(ProfileSummaryRow("Secondary Skills:", _join_list(profile.get("secondary_skills"))))

    level = profile.get("level", "N/A")
    years = profile.get("years_experience", "N/A")
    rows.append(ProfileSummaryRow("Level / Experience:", f"{level} / {years} years"))

    location = profile.get("location", "N/A")
    arrangement = _join_list(profile.get("arrangement"))
    rows.append(ProfileSummaryRow("Location / Arrangement:", f"{location} / {arrangement}"))

    if profile.get("dealbreakers"):
        rows.append(ProfileSummaryRow("Dealbreakers:", _join_list(profile.get("dealbreakers"))))

    if profile.get("comp_floor"):
        rows.append(ProfileSummaryRow("Compensation Floor:", f"${int(profile['comp_floor']):,}"))

    return rows


def profile_load_error_message(error: object) -> str:
    """Return Profile tab load failure text."""
    return f"Could not load profile: {error}"


def _join_list(value: object) -> str:
    if not value:
        return "N/A"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "N/A"
    return str(value)
