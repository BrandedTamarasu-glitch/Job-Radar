"""Shared hero and recommended card rendering for generated reports."""

from __future__ import annotations

import html

from .report_controls import html_copy_action_bar, html_shortlist_button, html_status_dropdown
from .report_job_attrs import html_job_attrs, report_job_key
from .report_job_details import html_job_detail_items
from .report_matching import html_match_summary
from .report_safety import safe_external_url
from .report_tiers import html_new_badge, html_score_badge, score_tier


def html_hero_section(hero_jobs: list[dict], profile: dict) -> str:
    """Generate HTML for the top-match hero jobs section."""
    if not hero_jobs:
        return ""

    cards_html = "".join(
        html_job_card(result, index, profile, hero=True)
        for index, result in enumerate(hero_jobs, 1)
    )

    return f"""
    <section aria-labelledby="hero-heading" class="hero-jobs-section">
      <div class="mb-4">
        <h2 id="hero-heading" class="h4 mb-3">Top Matches (Score >= 4.0)</h2>
        <p class="text-muted mb-4">These jobs are excellent matches for your profile.</p>
        {html_copy_action_bar("hero")}
        {cards_html}
      </div>
    </section>
    """


def html_recommended_section(recommended: list[dict], profile: dict) -> str:
    """Generate HTML for the recommended roles section."""
    if not recommended:
        return """
        <section aria-labelledby="recommended-heading">
          <div class="card mb-4">
            <div class="card-header">
              <h2 id="recommended-heading" class="h4 mb-0">Recommended Roles (Score 3.5 - 3.9)</h2>
            </div>
            <div class="card-body">
              <p class="text-muted mb-0"><em>No results scored 3.5 to 3.9 in this search run.</em></p>
            </div>
          </div>
        </section>
        """

    cards_html = "".join(
        html_job_card(result, index, profile)
        for index, result in enumerate(recommended, 1)
    )

    return f"""
    <section aria-labelledby="recommended-heading">
      <div class="mb-4">
        <h2 id="recommended-heading" class="h4 mb-3">Recommended Roles (Score 3.5 - 3.9)</h2>
        {html_copy_action_bar("recommended")}
        {cards_html}
      </div>
    </section>
    """


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
