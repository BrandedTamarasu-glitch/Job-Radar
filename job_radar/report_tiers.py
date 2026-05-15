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


def html_score_badge(score: float, tier: str, *, label: str | None = None) -> str:
    """Return accessible score badge HTML for report cards and rows."""
    tier_icon_html = f'<span class="{tier_icon_class(tier)}" aria-hidden="true"></span>'
    label_html = ""
    if label:
        label_html = f', </span><span class="badge-label">{label}</span>'
    else:
        label_html = "</span>"
    return (
        f'{tier_icon_html}<span class="badge rounded-pill score-badge tier-badge-{tier}">'
        f'<span class="visually-hidden">Score </span>{score:.1f}'
        f'<span class="visually-hidden"> out of 5.0{label_html}</span>'
    )
