"""Filtering data helpers for generated reports."""

from __future__ import annotations


def filtered_out_results(scored_results: list[dict], min_score: float) -> list[dict]:
    """Return jobs rejected by dealbreaker or minimum score threshold."""
    return [
        result for result in scored_results
        if result.get("score", {}).get("overall", 0.0) < min_score
    ]


def filter_explanation_text(result: dict, min_score: float) -> str:
    """Build a concise explanation for why a job was filtered out."""
    score = result.get("score", {})
    dealbreaker = score.get("dealbreaker")
    if dealbreaker:
        return f"Rejected by dealbreaker: {dealbreaker}"

    overall = score.get("overall", 0.0)
    components = score.get("components", {})
    reasons = []

    skill = components.get("skill_match", {})
    missing_core = skill.get("missing_core") or []
    if missing_core:
        reasons.append(f"missing core skills: {', '.join(missing_core[:3])}")
    elif skill.get("ratio"):
        reasons.append(f"{skill['ratio']} core skills")

    title = components.get("title_relevance", {})
    if title.get("reason"):
        reasons.append(f"title: {title['reason']}")

    seniority = components.get("seniority", {})
    if seniority.get("reason"):
        reasons.append(f"seniority: {seniority['reason']}")

    location = components.get("location", {})
    if location.get("score", 5.0) < 3.0 and location.get("reason"):
        reasons.append(f"location: {location['reason']}")

    if not reasons:
        reasons.append("score below the selected threshold")

    return f"Below {min_score:g} threshold at {overall}/5.0: " + "; ".join(reasons[:3])
