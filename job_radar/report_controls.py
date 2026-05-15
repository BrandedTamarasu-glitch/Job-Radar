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


def html_status_dropdown(*, extra_classes: str = "") -> str:
    """Generate the application status dropdown control."""
    class_suffix = f" {extra_classes.strip()}" if extra_classes.strip() else ""
    return f"""
      <div class="dropdown d-inline-block{class_suffix}">
        <button class="btn btn-sm btn-outline-secondary dropdown-toggle status-dropdown"
                type="button" data-bs-toggle="dropdown"
                aria-label="Change application status">
          Status
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
          <li><a class="dropdown-item" href="#" data-status="applied">Applied</a></li>
          <li><a class="dropdown-item" href="#" data-status="interviewing">Interviewing</a></li>
          <li><a class="dropdown-item" href="#" data-status="rejected">Rejected</a></li>
          <li><a class="dropdown-item" href="#" data-status="offer">Offer</a></li>
          <li><hr class="dropdown-divider"></li>
          <li><a class="dropdown-item" href="#" data-status="">Clear Status</a></li>
        </ul>
      </div>
    """
