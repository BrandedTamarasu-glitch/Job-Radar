"""Score tier helpers for generated reports."""

from __future__ import annotations


def score_tier(score: float) -> str:
    """Return CSS tier class suffix based on score value."""
    if score >= 4.0:
        return "strong"
    if score >= 3.5:
        return "rec"
    return "review"


def tier_icon_class(tier: str) -> str:
    """Return CSS class for tier Unicode icon indicator."""
    return f"tier-icon tier-icon-{tier}"
