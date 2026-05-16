"""Shared all-results row rendering for generated reports."""

from __future__ import annotations

import html

from .report_controls import html_shortlist_button, html_status_dropdown
from .report_job_attrs import html_job_attrs, report_job_key
from .report_job_details import html_result_link, result_row_display_fields
from .report_safety import safe_external_url
from .report_tiers import html_new_badge, html_score_badge, score_tier


def html_result_row(result: dict, index: int) -> str:
    """Generate one HTML row for the all-results table."""
    job = result["job"]
    score = result["score"]["overall"]
    rec = result["score"]["recommendation"]
    is_new = result.get("is_new", True)
    tier = score_tier(score)

    display_fields = result_row_display_fields(job)
    job_key_val = report_job_key(job)

    safe_job_url = safe_external_url(job.url)
    if safe_job_url:
        link_html = html_result_link(job)
        row_attrs = html_job_attrs(
            job,
            class_value=f"job-item tier-{tier}",
            score=score,
            include_tabindex=True,
        )
    else:
        link_html = html_result_link(job)
        row_attrs = html_job_attrs(job, class_value=f"tier-{tier}")

    status_dropdown = html_status_dropdown()
    new_badge_accessible = html_new_badge(rounded=True) if is_new else ""
    shortlist_button = html_shortlist_button(job_key_val, compact=True)
    score_badge_accessible = html_score_badge(score, tier)

    return f"""
    <tr {row_attrs}>
      <th scope="row" data-label="#">{index}</th>
      <td data-label="Score">{score_badge_accessible}<br><small class="text-muted">({html.escape(rec)})</small></td>
      <td data-label="New" class="col-new">{new_badge_accessible}</td>
      <td data-label="Status">{status_dropdown}<br>{shortlist_button}</td>
      <td data-label="Title"><strong>{html.escape(job.title)}</strong></td>
      <td data-label="Company">{html.escape(job.company)}</td>
      <td data-label="Salary" class="col-salary">{display_fields["salary"]}</td>
      <td data-label="Type" class="col-type">{display_fields["employment_type"]}</td>
      <td data-label="Location">{html.escape(job.location)}</td>
      <td data-label="Snippet" class="col-snippet">{display_fields["snippet"]}</td>
      <td data-label="Link" class="no-label">{link_html}</td>
    </tr>
    """
