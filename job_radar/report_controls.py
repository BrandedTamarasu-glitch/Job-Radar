"""Shared interactive control rendering for generated reports."""

from __future__ import annotations

import html


def html_shortlist_button(job_key_val: str, *, compact: bool = False) -> str:
    """Generate accessible review-state controls."""
    margin_class = " mt-1" if compact else ""
    escaped_key = html.escape(job_key_val)
    return (
        f'<span class="review-state-controls{margin_class}">'
        f'<button type="button" class="btn btn-sm btn-outline-warning shortlist-btn" '
        f'data-shortlist-key="{escaped_key}" data-review-state="shortlisted" '
        'aria-pressed="false" aria-label="Toggle shortlist for this job">Shortlist</button> '
        f'<button type="button" class="btn btn-sm btn-outline-secondary review-state-btn" '
        f'data-review-key="{escaped_key}" data-review-state="maybe_later" '
        'aria-pressed="false" aria-label="Mark this job as maybe later">Maybe Later</button> '
        f'<button type="button" class="btn btn-sm btn-outline-danger review-state-btn" '
        f'data-review-key="{escaped_key}" data-review-state="dismissed" '
        'aria-pressed="false" aria-label="Dismiss this job from review">Dismiss</button>'
        '</span>'
    )
