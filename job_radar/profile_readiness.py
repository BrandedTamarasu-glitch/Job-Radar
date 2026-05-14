"""Profile readiness checks for onboarding and match-quality guidance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileReadiness:
    """Human-readable readiness summary for a saved profile."""

    status: str
    score: int
    max_score: int
    missing_required: tuple[str, ...]
    recommendations: tuple[str, ...]

    @property
    def is_search_ready(self) -> bool:
        """Return True when the profile has the minimum search fields."""
        return not self.missing_required


def assess_profile_readiness(profile: dict | None) -> ProfileReadiness:
    """Assess whether a profile is ready for useful search results.

    Required fields mirror profile validation. Recommendations focus on fields
    that materially improve scoring, filtering, and report explanations.
    """
    profile = profile or {}
    missing_required: list[str] = []
    recommendations: list[str] = []
    score = 0
    max_score = 7

    if _has_text(profile.get("name")):
        score += 1
    else:
        missing_required.append("Add your name")

    if _has_items(profile.get("target_titles")):
        score += 1
    else:
        missing_required.append("Add at least one target title")

    if _has_items(profile.get("core_skills")):
        score += 1
    else:
        missing_required.append("Add at least one core skill")

    if _has_int(profile.get("years_experience")):
        score += 1
    else:
        recommendations.append("Add years of experience so seniority matching is more accurate")

    if _has_text(profile.get("location")) or _has_items(profile.get("arrangement")):
        score += 1
    else:
        recommendations.append("Add a target location or work arrangement to reduce weak matches")

    if _has_items(profile.get("secondary_skills")):
        score += 1
    else:
        recommendations.append("Add nice-to-have skills to improve tie-breakers and report explanations")

    if _has_items(profile.get("dealbreakers")) or _has_int(profile.get("comp_floor")):
        score += 1
    else:
        recommendations.append("Add dealbreakers or minimum compensation to filter poor-fit roles")

    if missing_required:
        status = "Needs setup"
    elif score >= 6:
        status = "Strong"
    elif score >= 5:
        status = "Good"
    else:
        status = "Basic"

    return ProfileReadiness(
        status=status,
        score=score,
        max_score=max_score,
        missing_required=tuple(missing_required),
        recommendations=tuple(recommendations),
    )


def readiness_guidance_lines(readiness: ProfileReadiness, limit: int = 3) -> list[str]:
    """Return concise next-action guidance for a readiness summary."""
    if readiness.missing_required:
        return list(readiness.missing_required[:limit])
    if readiness.status == "Strong":
        return []
    return list(readiness.recommendations[:limit])


def _has_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_items(value) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def _has_int(value) -> bool:
    return isinstance(value, int) and value >= 0
