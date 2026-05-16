"""Shared hero and recommended card rendering for generated reports."""

from __future__ import annotations

import html

from .report_controls import html_shortlist_button, html_status_dropdown
from .report_job_attrs import html_job_attrs, report_job_key
from .report_job_details import html_job_detail_items
from .report_matching import html_match_summary
from .report_safety import safe_external_url
from .report_tiers import html_new_badge, html_score_badge, score_tier


def html_job_card(result: dict, index: int, profile: dict, *, hero: bool = False) -> str:
    """Generate one hero or recommended job card."""
    job = result["job"]
    score = result["score"]
    is_new = result.get("is_new", True)
    new_tag = html_new_badge(leading_space=True) if is_new else ""

    score_val = score["overall"]
    tier = "strong" if hero else score_tier(score_val)

    details_html = html_job_detail_items(result, profile)
    match_summary_html = html_match_summary(result)

    job_key_val = report_job_key(job)
    shortlist_button = html_shortlist_button(job_key_val)

    if safe_external_url(job.url):
        data_attrs = html_job_attrs(
            job,
            class_value=_card_class_value(tier, hero=hero, interactive=True),
            score=score_val,
            include_tabindex=True,
        )
    else:
        data_attrs = html_job_attrs(
            job,
            class_value=_card_class_value(tier, hero=hero, interactive=False),
        )

    status_dropdown = html_status_dropdown(extra_classes="ms-2")
    score_badge_html = html_score_badge(
        score_val,
        tier,
        label="Top Match" if hero else None,
    )

    return f"""
        <div {data_attrs}>
          <div class="card-header">
            <h3 class="h5 mb-0">
              {index}. {html.escape(job.title)} — {html.escape(job.company)}
              {score_badge_html}{new_tag}
              {status_dropdown}
              {shortlist_button}
            </h3>
          </div>
          <div class="card-body job-card-body">
            {match_summary_html}
            <ul class="mb-0 job-detail-list">
              {details_html}
            </ul>
          </div>
        </div>
        """


def _card_class_value(tier: str, *, hero: bool, interactive: bool) -> str:
    classes = ["card", "mb-3"]
    if interactive:
        classes.append("job-item")
    if hero:
        classes.append("hero-job")
    classes.append(f"tier-{tier}")
    return " ".join(classes)
