"""Shared job detail rendering for generated HTML reports."""

from __future__ import annotations

import html

from .report_matching import match_highlights, skill_callout_groups
from .report_safety import safe_external_url


def html_job_detail_items(result: dict, profile: dict) -> str:
    """Build the shared detail list for hero and recommended job cards."""
    job = result["job"]
    score = result["score"]
    components = score["components"]
    skill = components["skill_match"]
    response = components["response"]

    details = []
    details.append(f"<li><strong>Posted:</strong> {html.escape(job.date_posted)}</li>")
    details.append(f"<li><strong>Rate/Salary:</strong> {html.escape(job.salary)}</li>")

    emp_type = getattr(job, "employment_type", "")
    type_str = f" | {html.escape(emp_type)}" if emp_type else ""
    details.append(
        f"<li><strong>Location:</strong> {html.escape(job.location)} | "
        f"{html.escape(job.arrangement)}{type_str}</li>"
    )

    matched_core = ", ".join(skill["matched_core"]) if skill["matched_core"] else "none"
    details.append(
        f"<li><strong>Stack match:</strong> {html.escape(skill['ratio'])} — "
        f"matched: {html.escape(matched_core)}</li>"
    )

    for label, values in skill_callout_groups(skill, profile):
        details.append(
            f"<li class=\"skill-callout\"><strong>{html.escape(label)}:</strong> "
            f"{html.escape(', '.join(values))}</li>"
        )

    title_rel = components.get("title_relevance", {})
    if title_rel:
        details.append(
            f"<li><strong>Title match:</strong> "
            f"{html.escape(title_rel.get('reason', 'N/A'))}</li>"
        )

    details.append(
        f"<li><strong>Seniority:</strong> "
        f"{html.escape(components['seniority']['reason'])}</li>"
    )
    details.append(
        f"<li><strong>Response likelihood:</strong> "
        f"{html.escape(response['likelihood'])} — {html.escape(response['reason'])}</li>"
    )

    if components.get("comp_note"):
        details.append(f"<li><strong>Comp warning:</strong> {html.escape(components['comp_note'])}</li>")

    if components.get("parse_note"):
        details.append(f"<li><strong>Note:</strong> {html.escape(components['parse_note'])}</li>")

    if job.apply_info:
        details.append(f"<li><strong>Apply:</strong> {html.escape(job.apply_info)}</li>")

    safe_job_url = safe_external_url(job.url)
    if safe_job_url:
        source_aria_label = f"View on {job.source}, opens in new tab"
        details.append(
            f'<li><strong>Link:</strong> <a href="{html.escape(safe_job_url)}" '
            f'target="_blank" rel="noopener" class="btn btn-sm btn-outline-primary" '
            f'aria-label="{html.escape(source_aria_label)}">{html.escape(job.source)}</a></li>'
        )
        details.append(
            f'<li><button class="btn btn-sm btn-outline-secondary copy-btn" '
            f'onclick="copySingleUrl(this)" data-url="{html.escape(safe_job_url)}">'
            f"Copy URL</button></li>"
        )
    elif job.url:
        details.append(f"<li><strong>Link:</strong> {html.escape(job.source)} URL unavailable</li>")

    highlights = profile.get("highlights", [])
    matched_core_list = skill.get("matched_core", [])
    if highlights and matched_core_list:
        relevant = match_highlights(highlights, matched_core_list, job)
        if relevant:
            talking_points = "".join(f"<li>{html.escape(highlight)}</li>" for highlight in relevant)
            details.append(f"<li><strong>Talking points:</strong><ul>{talking_points}</ul></li>")

    return "".join(details)
