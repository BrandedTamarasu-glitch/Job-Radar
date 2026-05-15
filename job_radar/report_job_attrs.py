"""Job key and data attribute helpers for HTML reports."""

from __future__ import annotations

import html
from typing import Any

from .report_safety import safe_external_url


def report_job_key(job: Any) -> str:
    """Return the report/tracker key for a job-like object."""
    return f"{job.title.lower().strip()}||{job.company.lower().strip()}"


def html_job_attrs(
    job: Any,
    *,
    class_value: str,
    score: float | None = None,
    include_tabindex: bool = False,
) -> str:
    """Return HTML attributes for report job cards and rows."""
    safe_url = safe_external_url(job.url)
    attrs = [f'class="{html.escape(class_value)}"']
    if include_tabindex and safe_url:
        attrs.append('tabindex="0"')
    if safe_url:
        attrs.append(f'data-job-url="{html.escape(safe_url)}"')
        if score is not None:
            attrs.append(f'data-score="{score:.1f}"')
    attrs.extend([
        f'data-job-key="{html.escape(report_job_key(job))}"',
        f'data-job-title="{html.escape(job.title)}"',
        f'data-job-company="{html.escape(job.company)}"',
    ])
    return " ".join(attrs)
