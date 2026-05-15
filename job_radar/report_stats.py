"""Report statistics helpers."""

from __future__ import annotations


def calculate_report_stats(scored_results: list[dict], min_score: float) -> dict[str, int]:
    """Return summary stats for results included at the selected score threshold."""
    filtered_results = [
        result for result in scored_results
        if result["score"]["overall"] >= min_score
    ]
    return {
        "total": len(filtered_results),
        "new": sum(1 for result in filtered_results if result.get("is_new", True)),
        "high_score": sum(
            1 for result in filtered_results
            if result["score"]["overall"] >= 3.5
        ),
    }
