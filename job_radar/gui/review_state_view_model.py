"""View-model helpers for persisted search review state."""

from __future__ import annotations


REVIEW_STATE_LABELS = {
    "shortlisted": "shortlisted",
    "maybe_later": "maybe later",
    "dismissed": "dismissed",
}


def format_review_state_summary(counts: dict[str, int] | None) -> list[str]:
    """Return compact GUI summary lines for persisted search review state."""
    counts = counts or {}
    ordered = ("shortlisted", "maybe_later", "dismissed")
    lines = []
    for state in ordered:
        count = int(counts.get(state) or 0)
        if count:
            label = REVIEW_STATE_LABELS[state]
            job_word = "job" if count == 1 else "jobs"
            lines.append(f"{count} {label} {job_word}")
    return lines
