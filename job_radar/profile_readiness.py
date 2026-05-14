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
    scoring_signal_recommendations: tuple[str, ...]

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
    scoring_signal_recommendations: list[str] = []
    score = 0
    max_score = 7

    if _has_text(profile.get("name")):
        score += 1
    else:
        missing_required.append("Add your name")

    if _has_items(profile.get("target_titles")):
        score += 1
        if len(_clean_items(profile.get("target_titles"))) < 2:
            scoring_signal_recommendations.append(
                "Title relevance signal: add adjacent target titles to catch more good matches"
            )
    else:
        missing_required.append("Add at least one target title")
        scoring_signal_recommendations.append(
            "Title relevance signal: add the roles you would actually apply for"
        )

    if _has_items(profile.get("core_skills")):
        score += 1
        if len(_clean_items(profile.get("core_skills"))) < 3:
            scoring_signal_recommendations.append(
                "Skill match signal: add at least three core skills so stack scoring is less brittle"
            )
    else:
        missing_required.append("Add at least one core skill")
        scoring_signal_recommendations.append(
            "Skill match signal: add must-have skills the job listing should mention"
        )

    if _has_int(profile.get("years_experience")):
        score += 1
    else:
        recommendations.append("Add years of experience so seniority matching is more accurate")
        scoring_signal_recommendations.append(
            "Seniority signal: add years of experience so level matching is more accurate"
        )

    if _has_text(profile.get("location")) or _has_items(profile.get("arrangement")):
        score += 1
    else:
        recommendations.append("Add a target location or work arrangement to reduce weak matches")
        scoring_signal_recommendations.append(
            "Location signal: add target location or work arrangement to reduce weak matches"
        )

    if _has_items(profile.get("secondary_skills")):
        score += 1
    else:
        recommendations.append("Add nice-to-have skills to improve tie-breakers and report explanations")
        scoring_signal_recommendations.append(
            "Skill tie-breaker signal: add nice-to-have skills for clearer report explanations"
        )

    if not _has_text(profile.get("target_market")):
        scoring_signal_recommendations.append(
            "Domain signal: add a target market or industry to improve domain relevance scoring"
        )

    if _has_items(profile.get("dealbreakers")) or _has_int(profile.get("comp_floor")):
        score += 1
    else:
        recommendations.append("Add dealbreakers or minimum compensation to filter poor-fit roles")
        scoring_signal_recommendations.append(
            "Filtering signal: add dealbreakers or minimum compensation to reject poor-fit roles"
        )

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
        scoring_signal_recommendations=tuple(scoring_signal_recommendations),
    )


def readiness_guidance_lines(readiness: ProfileReadiness, limit: int = 3) -> list[str]:
    """Return concise next-action guidance for a readiness summary."""
    if readiness.missing_required:
        return list(readiness.missing_required[:limit])
    if readiness.status == "Strong":
        return []
    return list(readiness.recommendations[:limit])


def scoring_signal_guidance_lines(readiness: ProfileReadiness, limit: int = 3) -> list[str]:
    """Return profile-quality guidance tied to scoring components."""
    return list(readiness.scoring_signal_recommendations[:limit])


def _has_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_items(value) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def _clean_items(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _has_int(value) -> bool:
    return isinstance(value, int) and value >= 0
