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


def apply_result_filters(
    results: list,
    search_config: dict,
    *,
    date_filter_func=None,
) -> tuple[list, str | None, str | None]:
    """Apply date, company, skill, and location filters to raw search results."""
    if date_filter_func is None:
        from job_radar.search import filter_by_date

        date_filter_func = filter_by_date

    from_date, to_date = resolve_date_filter(search_config)
    if from_date and to_date:
        results = date_filter_func(results, from_date, to_date)

    results = filter_by_company(
        results,
        include=search_config.get("include_companies"),
        exclude=search_config.get("exclude_companies"),
    )
    results = filter_by_required_skills(
        results,
        search_config.get("required_skills"),
    )
    results = filter_by_location_strictness(
        results,
        search_config.get("location_strictness"),
    )
    return results, from_date, to_date


def score_results(results: list, profile: dict, score_func=None) -> tuple[list[dict], int]:
    """Score results, remove dealbreakers, and sort highest score first."""
    if score_func is None:
        from job_radar.scoring import score_job

        score_func = score_job

    scored = []
    dealbreaker_count = 0
    for result in results:
        score = score_func(result, profile)
        if score.get("dealbreaker"):
            dealbreaker_count += 1
            continue
        scored.append({"job": result, "score": score})

    scored.sort(key=lambda item: item["score"]["overall"], reverse=True)
    return scored, dealbreaker_count


def apply_scored_result_filters(
    scored: list[dict],
    search_config: dict,
    *,
    status_filter_func=None,
) -> tuple[list[dict], float]:
    """Apply new-only, min-score, and optional tracker-status filters."""
    if search_config.get("new_only", False):
        scored = [result for result in scored if result.get("is_new", True)]

    min_score = search_config.get("min_score", 2.8)
    scored = [result for result in scored if result["score"]["overall"] >= min_score]

    if search_config.get("hide_rejected_skipped", False):
        if status_filter_func is None:
            from job_radar.tracker import filter_scored_by_application_status

            status_filter_func = filter_scored_by_application_status
        scored = status_filter_func(scored, {"rejected", "skipped"})

    return scored, min_score


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
