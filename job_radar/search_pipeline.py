"""Shared search pipeline helpers for CLI and GUI search flows."""

from __future__ import annotations

from datetime import date, timedelta


FRESHNESS_DAY_WINDOWS = {
    "past_24h": 1,
    "past_48h": 2,
    "past_7d": 7,
}


def parse_company_filter(value: str | list[str] | None) -> list[str]:
    """Parse comma-separated company filter text into normalized terms."""
    if not value:
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = value
    return [
        item.strip().casefold()
        for item in raw_items
        if item and item.strip()
    ]


def parse_skill_filter(value: str | list[str] | None) -> list[str]:
    """Parse comma-separated skill filter text while preserving display casing."""
    if not value:
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = value
    return [
        item.strip()
        for item in raw_items
        if item and item.strip()
    ]


def apply_preferred_skills(profile: dict, preferred_skills=None) -> dict:
    """Return a profile copy with per-search nice-to-have skills appended."""
    parsed_skills = parse_skill_filter(preferred_skills)
    if not parsed_skills:
        return profile

    search_profile = profile.copy()
    secondary_skills = list(search_profile.get("secondary_skills", []))
    seen = {skill.casefold() for skill in secondary_skills}
    for skill in parsed_skills:
        if skill.casefold() not in seen:
            secondary_skills.append(skill)
            seen.add(skill.casefold())
    search_profile["secondary_skills"] = secondary_skills
    return search_profile


def filter_by_company(results: list, include=None, exclude=None) -> list:
    """Filter jobs by company include/exclude terms."""
    include_terms = parse_company_filter(include)
    exclude_terms = parse_company_filter(exclude)
    if not include_terms and not exclude_terms:
        return results

    filtered = []
    for result in results:
        company = getattr(result, "company", "").casefold()
        if include_terms and not any(term in company for term in include_terms):
            continue
        if exclude_terms and any(term in company for term in exclude_terms):
            continue
        filtered.append(result)
    return filtered


def filter_by_required_skills(results: list, required_skills=None) -> list:
    """Filter jobs that do not contain every required skill."""
    if not required_skills:
        return results

    from job_radar.scoring import missing_required_skills

    return [
        result for result in results
        if not missing_required_skills(result, required_skills)
    ]


def infer_job_arrangement(result) -> str:
    """Infer normalized job arrangement from arrangement/location/description."""
    arrangement = getattr(result, "arrangement", "") or "unknown"
    arrangement = arrangement.strip().casefold()
    if arrangement == "on-site":
        arrangement = "onsite"
    if arrangement in {"remote", "hybrid", "onsite"}:
        return arrangement

    text = " ".join([
        getattr(result, "location", "") or "",
        getattr(result, "description", "") or "",
    ]).casefold()
    if "hybrid" in text:
        return "hybrid"
    if "remote" in text:
        return "remote"
    if "on-site" in text or "onsite" in text or "in-office" in text:
        return "onsite"
    return "unknown"


def filter_by_location_strictness(results: list, strictness: str | None = None) -> list:
    """Apply hard arrangement filtering requested from search controls."""
    if not strictness or strictness == "profile":
        return results

    filtered = []
    for result in results:
        arrangement = infer_job_arrangement(result)
        if strictness == "remote_only" and arrangement == "remote":
            filtered.append(result)
        elif strictness == "remote_or_hybrid" and arrangement in {"remote", "hybrid"}:
            filtered.append(result)
        elif strictness == "hybrid_only" and arrangement == "hybrid":
            filtered.append(result)
        elif strictness == "onsite_only" and arrangement == "onsite":
            filtered.append(result)
        elif strictness == "exclude_onsite" and arrangement != "onsite":
            filtered.append(result)
    return filtered


def resolve_date_filter(search_config: dict, today: date | None = None) -> tuple[str | None, str | None]:
    """Resolve freshness/custom settings into date-filter boundaries."""
    from_date = search_config.get("from_date")
    to_date = search_config.get("to_date")
    if from_date and to_date:
        return from_date, to_date

    freshness = search_config.get("freshness") or "any"
    days = FRESHNESS_DAY_WINDOWS.get(freshness)
    if days is None:
        return None, None

    today = today or date.today()
    return (today - timedelta(days=days)).isoformat(), today.isoformat()
