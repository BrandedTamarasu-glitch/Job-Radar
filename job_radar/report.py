"""Dual-format report generator (HTML + Markdown) for job search results."""

import html
import logging
import os
from datetime import date, datetime
from pathlib import Path

from .report_assets import (
    html_external_scripts as _html_external_scripts,
    html_external_stylesheets as _html_external_stylesheets,
)
from .report_cards import html_hero_section as _render_html_hero_section
from .report_cards import html_recommended_section as _render_html_recommended_section
from .report_controls import html_filter_controls as _html_filter_controls
from .report_filtering import filter_explanation_text as _filter_explanation_text
from .report_filtering import filtered_out_results as _filtered_out_results
from .report_filtering import html_filtered_out_section as _html_filtered_out_section
from .report_manual import html_manual_urls_section as _html_manual_urls_section
from .report_markdown import append_all_results_table as _append_all_results_table
from .report_markdown import append_detailed_result as _append_detailed_result
from .report_markdown import append_manual_urls_section as _append_manual_urls_section
from .report_markdown import markdown_filtered_out_section as _render_markdown_filtered_out_section
from .report_matching import match_summary_text as _match_summary_text
from .report_matching import skill_callout_groups as _skill_callout_groups
from .report_profile import html_profile_section as _html_profile_section
from .report_result_rows import html_result_row as _render_html_result_row
from .report_results import COLLAPSE_RESULTS_AFTER, COLLAPSED_RESULTS_RENDER_LIMIT, ZERO_RESULTS_TIPS
from .report_results import html_results_table as _html_results_table_renderer
from .report_source_warnings import failed_source_names as _failed_source_names
from .report_source_warnings import html_source_failures as _html_source_failures
from .report_source_warnings import html_source_warnings as _html_source_warnings
from .report_source_warnings import markdown_source_failures as _markdown_source_failures
from .report_source_warnings import markdown_source_warnings as _markdown_source_warnings
from .report_stats import calculate_report_stats
from .report_tracker import html_tracker_stats as _html_tracker_stats


log = logging.getLogger(__name__)


def generate_report(
    profile: dict,
    scored_results: list[dict],
    manual_urls: list[dict],
    sources_searched: list[str],
    from_date: str,
    to_date: str,
    output_dir: str = "results",
    tracker_stats: dict | None = None,
    min_score: float = 2.8,
    source_failures: list[dict] | None = None,
    source_warnings: list[dict] | None = None,
) -> dict:
    """Generate both HTML and Markdown reports for a candidate's search results.

    Args:
        profile: Candidate profile dict
        scored_results: List of {"job": JobResult, "score": score_dict} sorted by score
        manual_urls: List of manual-check URL dicts
        sources_searched: List of source names
        from_date: Search start date
        to_date: Search end date
        output_dir: Directory to write report to
        tracker_stats: Cross-run statistics dict from tracker module
        min_score: Minimum score threshold for filtering results
        source_failures: Optional per-query source failures from fetch_all
        source_warnings: Optional non-fatal source warnings from fetch_all

    Returns:
        Dict with keys:
            - "markdown": str (path to Markdown file)
            - "html": str (path to HTML file)
            - "stats": dict with keys "total", "new", "high_score"
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Generate Markdown report
    md_filename = f"jobs_{timestamp}.md"
    md_path = output_path / md_filename
    _generate_markdown_report(
        md_path, profile, scored_results, manual_urls,
        sources_searched, from_date, to_date, tracker_stats, min_score, source_failures, source_warnings
    )

    # Generate HTML report
    html_filename = f"jobs_{timestamp}.html"
    html_path = output_path / html_filename
    _generate_html_report(
        html_path, profile, scored_results, manual_urls,
        sources_searched, from_date, to_date, tracker_stats, min_score, source_failures, source_warnings
    )

    return {
        "markdown": str(md_path),
        "html": str(html_path),
        "stats": calculate_report_stats(scored_results, min_score),
    }


def _generate_markdown_report(
    filepath: Path,
    profile: dict,
    scored_results: list[dict],
    manual_urls: list[dict],
    sources_searched: list[str],
    from_date: str,
    to_date: str,
    tracker_stats: dict | None = None,
    min_score: float = 2.8,
    source_failures: list[dict] | None = None,
    source_warnings: list[dict] | None = None,
) -> None:
    """Generate a Markdown report for a candidate's search results.

    This is the original generate_report function, now an internal helper.
    """
    name = profile["name"]
    today = date.today().isoformat()

    all_scored_results = list(scored_results)
    filtered_out = _filtered_out_results(all_scored_results, min_score)

    # Filter out dealbreakers and poor matches
    scored_results = [r for r in all_scored_results if r["score"]["overall"] >= min_score]
    total = len(scored_results)
    recommended = [r for r in scored_results if r["score"]["overall"] >= 3.5]
    new_count = sum(1 for r in scored_results if r.get("is_new", True))

    lines = []
    lines.append(f"# Job Search Results — {name}")
    lines.append(f"**Date:** {today}")
    lines.append(f"**Sources searched:** {', '.join(sources_searched)}")
    lines.append(f"**Date filter:** {from_date} to {to_date}")
    lines.append(f"**Total results:** {total} ({new_count} new)")
    lines.append(f"**Above threshold (3.5+):** {len(recommended)}")
    if source_failures:
        failed_sources = _failed_source_names(source_failures)
        lines.append(
            f"**Source warnings:** {len(source_failures)} query failures across "
            f"{', '.join(failed_sources)}"
        )
    if source_warnings:
        warning_sources = _failed_source_names(source_warnings)
        lines.append(
            f"**Performance warnings:** {len(source_warnings)} slow queries across "
            f"{', '.join(warning_sources)}"
        )

    # Tracker stats
    if tracker_stats:
        lines.append("")
        lines.append(f"> Lifetime: {tracker_stats['total_unique_jobs_seen']} unique jobs seen "
                      f"across {tracker_stats['total_runs']} runs | "
                      f"Avg {tracker_stats['avg_new_per_run_last_7']} new/run (last 7)")

    lines.append("")

    # Profile summary
    lines.append("## Candidate Profile Summary")
    lines.append(f"- **Level:** {profile.get('level', 'N/A')}")
    lines.append(f"- **Experience:** {profile.get('years_experience', 'N/A')} years")
    lines.append(f"- **Target titles:** {', '.join(profile.get('target_titles', []))}")
    lines.append(f"- **Core skills:** {', '.join(profile.get('core_skills', []))}")
    lines.append(f"- **Location:** {profile.get('location', 'N/A')}")
    lines.append(f"- **Arrangement:** {', '.join(profile.get('arrangement', []))}")
    lines.append(f"- **Target market:** {profile.get('target_market', 'N/A')}")
    if profile.get("certifications"):
        lines.append(f"- **Certifications:** {', '.join(profile['certifications'])}")
    if profile.get("comp_floor"):
        lines.append(f"- **Comp floor:** ${profile['comp_floor']:,.0f}")
    if profile.get("dealbreakers"):
        lines.append(f"- **Dealbreakers:** {', '.join(profile['dealbreakers'])}")
    lines.append("")

    # Recommended roles
    if recommended:
        lines.append("## Recommended Roles (Score >= 3.5)")
        lines.append("")
        for i, r in enumerate(recommended, 1):
            _format_detailed_result(lines, i, r, profile)
    else:
        lines.append("## Recommended Roles (Score >= 3.5)")
        lines.append("_No results scored 3.5 or above in this search run._")
        lines.append("")

    _append_all_results_table(lines, scored_results)

    if source_failures:
        lines.extend(_markdown_source_failures(source_failures))
    if source_warnings:
        lines.extend(_markdown_source_warnings(source_warnings))

    lines.extend(_markdown_filtered_out_section(filtered_out, min_score))

    _append_manual_urls_section(lines, manual_urls)

    content = "\n".join(lines)
    filepath.write_text(content, encoding="utf-8")


def _markdown_filtered_out_section(filtered_out: list[dict], min_score: float) -> list[str]:
    """Return a concise Markdown section for filtered-out jobs."""
    return _render_markdown_filtered_out_section(filtered_out, min_score)


def _format_detailed_result(lines: list, rank: int, result: dict, profile: dict):
    """Format a single detailed result entry for the recommended section."""
    _append_detailed_result(lines, rank, result, profile)


def _generate_html_report(
    filepath: Path,
    profile: dict,
    scored_results: list[dict],
    manual_urls: list[dict],
    sources_searched: list[str],
    from_date: str,
    to_date: str,
    tracker_stats: dict | None = None,
    min_score: float = 2.8,
    source_failures: list[dict] | None = None,
    source_warnings: list[dict] | None = None,
) -> None:
    """Generate an HTML report with Bootstrap 5.3 styling."""
    # Import tracker locally to avoid circular dependency
    from . import tracker

    name = html.escape(profile["name"])
    today = date.today().isoformat()

    all_scored_results = list(scored_results)
    filtered_out = _filtered_out_results(all_scored_results, min_score)

    # Filter results
    scored_results = [r for r in all_scored_results if r["score"]["overall"] >= min_score]
    total = len(scored_results)
    hero_jobs = [r for r in scored_results if r["score"]["overall"] >= 4.0]
    recommended = [r for r in scored_results if 3.5 <= r["score"]["overall"] < 4.0]
    new_count = sum(1 for r in scored_results if r.get("is_new", True))

    # Load application statuses and review state for embedding
    import json as json_module
    all_statuses = tracker.get_all_application_statuses()
    embedded_status_json = json_module.dumps(all_statuses, indent=2)
    try:
        from .review_state import load_review_state
        embedded_review_state_json = json_module.dumps(load_review_state(), indent=2)
    except Exception:
        embedded_review_state_json = json_module.dumps({"version": 1, "jobs": {}}, indent=2)

    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en" data-bs-theme="auto">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>Job Search Results — {name}</title>
{_html_external_stylesheets()}

  <style>
    /* CSS Custom Properties Foundation */
    :root {{
      /* Font stacks */
      --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;

      /* Typography scale */
      --font-size-title: 2rem;
      --font-size-section: 1.5rem;
      --font-size-subsection: 1.125rem;
      --font-size-body: 1rem;
      --font-size-small: 0.875rem;
      --line-height-tight: 1.25;
      --line-height-normal: 1.5;
      --line-height-relaxed: 1.6;

      /* Three-tier semantic colors (HSL) */
      /* Tier 1 - Strong (score >= 4.0): Green hue */
      --tier-strong-h: 142;
      --tier-strong-s: 55%;
      --tier-strong-l: 93%;
      --tier-strong-border-l: 33%;
      --tier-strong-text-l: 25%;
      --color-tier-strong-bg: hsl(142, 55%, 93%);
      --color-tier-strong-border: hsl(142, 55%, 33%);
      --color-tier-strong-text: hsl(142, 55%, 25%);

      /* Tier 2 - Recommended (score 3.5-3.9): Cyan/teal hue */
      --tier-rec-h: 180;
      --tier-rec-s: 50%;
      --tier-rec-l: 92%;
      --tier-rec-border-l: 28%;
      --tier-rec-text-l: 22%;
      --color-tier-rec-bg: hsl(180, 50%, 92%);
      --color-tier-rec-border: hsl(180, 50%, 28%);
      --color-tier-rec-text: hsl(180, 50%, 22%);

      /* Tier 3 - Worth Reviewing (score 2.8-3.4): Neutral gray-blue */
      --tier-review-h: 210;
      --tier-review-s: 10%;
      --tier-review-l: 95%;
      --tier-review-border-l: 45%;
      --tier-review-text-l: 35%;
      --color-tier-review-bg: hsl(210, 10%, 95%);
      --color-tier-review-border: hsl(210, 10%, 45%);
      --color-tier-review-text: hsl(210, 10%, 35%);

      /* Hero job shadows (multi-layer elevation) */
      --shadow-hero:
        0 1px 3px rgba(0, 0, 0, 0.12),
        0 4px 8px rgba(0, 0, 0, 0.08),
        0 8px 16px rgba(0, 0, 0, 0.05);
    }}

    /* Dark mode overrides */
    @media (prefers-color-scheme: dark) {{
      :root {{
        /* Invert lightness for all three tiers, preserving hue */
        --tier-strong-l: 14%;
        --tier-strong-border-l: 52%;
        --tier-strong-text-l: 60%;
        --color-tier-strong-bg: hsl(142, 55%, 14%);
        --color-tier-strong-border: hsl(142, 55%, 52%);
        --color-tier-strong-text: hsl(142, 55%, 60%);

        --tier-rec-l: 12%;
        --tier-rec-border-l: 48%;
        --tier-rec-text-l: 55%;
        --color-tier-rec-bg: hsl(180, 50%, 12%);
        --color-tier-rec-border: hsl(180, 50%, 48%);
        --color-tier-rec-text: hsl(180, 50%, 55%);

        --tier-review-l: 16%;
        --tier-review-border-l: 42%;
        --tier-review-text-l: 50%;
        --color-tier-review-bg: hsl(210, 10%, 16%);
        --color-tier-review-border: hsl(210, 10%, 42%);
        --color-tier-review-text: hsl(210, 10%, 50%);

        /* Hero shadow dark mode (higher opacity for visibility) */
        --shadow-hero:
          0 1px 3px rgba(0, 0, 0, 0.3),
          0 4px 8px rgba(0, 0, 0, 0.2),
          0 8px 16px rgba(0, 0, 0, 0.15);
      }}
    }}

    /* Print-friendly styles */
    @media print {{
      /* Hide all interactive/navigation chrome */
      .no-print,
      .copy-btn,
      .copy-all-btn,
      .dropdown,
      .shortcut-hint,
      .export-status-btn,
      .btn-check + label,
      .btn-check,
      #clear-filters,
      #export-csv-btn,
      #filter-heading,
      [role="region"][aria-labelledby="filter-heading"] {{
        display: none !important;
      }}

      /* Override Bootstrap background stripping - preserve tier score colors */
      .tier-strong,
      .tier-rec,
      .tier-review,
      .tier-badge-strong,
      .tier-badge-rec,
      .tier-badge-review,
      .badge {{
        print-color-adjust: exact !important;
        -webkit-print-color-adjust: exact !important;
      }}

      /* Prevent job entries from splitting across pages */
      .card,
      .hero-job,
      tr {{
        break-inside: avoid;
        page-break-inside: avoid;
      }}

      /* Clean up print layout */
      body {{ background: white !important; }}
      .card {{ border: 1px solid #ddd !important; box-shadow: none !important; }}
      .hero-job {{ box-shadow: none !important; }}
      .badge {{ border: 1px solid currentColor; }}
    }}

    /* Dark mode adjustments */
    [data-bs-theme="dark"] {{
      --bs-body-bg: #212529;
      --bs-body-color: #dee2e6;
    }}

    /* Typography application */
    body {{
      font-family: var(--font-sans);
      font-size: var(--font-size-body);
      line-height: var(--line-height-normal);
    }}

    h1, .h1 {{
      font-size: var(--font-size-title);
      line-height: var(--line-height-tight);
      font-weight: 700;
      letter-spacing: -0.01em;
    }}

    h2, .h2 {{
      font-size: var(--font-size-section);
      line-height: 1.3;
      font-weight: 600;
    }}

    h3, .h3 {{
      font-size: var(--font-size-subsection);
      line-height: 1.4;
      font-weight: 600;
    }}

    /* Comfortable spacing */
    .card-body {{
      padding: 1.25rem;
    }}

    .card-body ul {{
      line-height: var(--line-height-relaxed);
    }}

    .card-header h3, .card-header .h5 {{
      line-height: 1.4;
    }}

    .text-small, small, .metadata {{
      font-size: var(--font-size-small);
      line-height: var(--line-height-normal);
    }}

    /* Score badge with monospace font */
    .score-badge {{
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      font-size: 0.9375rem;
      border-radius: 999em;
      padding: 0.35em 0.65em;
    }}

    /* Tier card backgrounds with left border accent */
    .tier-strong {{
      background-color: var(--color-tier-strong-bg) !important;
      border-left: 5px solid var(--color-tier-strong-border);
    }}
    .tier-rec {{
      background-color: var(--color-tier-rec-bg) !important;
      border-left: 4px solid var(--color-tier-rec-border);
    }}
    .tier-review {{
      background-color: var(--color-tier-review-bg) !important;
      border-left: 3px solid var(--color-tier-review-border);
    }}

    /* Table row tier indicators */
    table tr.tier-strong {{
      border-left: 5px solid var(--color-tier-strong-border);
    }}
    table tr.tier-rec {{
      border-left: 4px solid var(--color-tier-rec-border);
    }}
    table tr.tier-review {{
      border-left: 3px solid var(--color-tier-review-border);
    }}

    /* Pill score badges with tier colors */
    .tier-badge-strong {{
      background-color: var(--color-tier-strong-border) !important;
      color: #fff !important;
    }}
    .tier-badge-rec {{
      background-color: var(--color-tier-rec-border) !important;
      color: #fff !important;
    }}
    .tier-badge-review {{
      background-color: var(--color-tier-review-border) !important;
      color: #fff !important;
    }}

    /* Dark mode badge text adjustments */
    @media (prefers-color-scheme: dark) {{
      .tier-badge-strong,
      .tier-badge-rec,
      .tier-badge-review {{
        color: #fff !important;
      }}
    }}

    /* Pill shape for all score and status badges */
    .badge.rounded-pill {{
      border-radius: 999em;
      padding: 0.35em 0.65em;
      font-weight: 500;
    }}

    /* Non-color tier icons for colorblind accessibility */
    .tier-icon::before {{
      margin-right: 0.25em;
      font-weight: bold;
    }}
    .tier-icon-strong::before {{
      content: "\\2605 ";
    }}
    .tier-icon-rec::before {{
      content: "\\2713 ";
    }}
    .tier-icon-review::before {{
      content: "\\25C6 ";
    }}

    /* Status badges inherit pill style */
    .status-badge {{
      margin-right: 0.5rem;
      border-radius: 999em;
      padding: 0.35em 0.65em;
      font-size: 0.75rem;
    }}

    /* NEW badge refresh to pill style */
    .badge.bg-primary {{
      border-radius: 999em;
      padding: 0.35em 0.65em;
    }}

    /* Copy button styling */
    .copy-btn {{
      font-size: 0.75rem;
      padding: 0.2em 0.5em;
      margin-left: 0.5em;
      transition: background-color 0.2s ease;
    }}
    .copy-btn.copied {{
      background-color: #28a745 !important;
      border-color: #28a745 !important;
      color: white !important;
    }}

    /* Focus indicators for keyboard navigation */
    .job-item:focus-visible {{
      outline: 2px solid #005fcc;
      outline-offset: 2px;
      border-radius: 4px;
    }}
    a:focus-visible {{
      outline: 2px solid #0d6efd;
      outline-offset: 2px;
      text-decoration: underline;
    }}
    .btn:focus-visible {{
      outline: 2px solid currentColor;
      outline-offset: 2px;
      box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
    }}
    .dropdown-item:focus {{
      outline: 2px solid #0d6efd;
      outline-offset: -2px;
    }}
    .dropdown-toggle:focus-visible {{
      outline: 2px solid #0d6efd;
      outline-offset: 2px;
    }}

    /* Copy All button styling */
    .copy-all-btn {{
      transition: background-color 0.2s ease;
    }}
    .copy-all-btn.copied {{
      background-color: #28a745 !important;
      border-color: #28a745 !important;
    }}

    /* Keyboard shortcut hint */
    .shortcut-hint {{
      font-size: 0.8rem;
      color: #595959;
    }}

    /* Status badge styling */
    .status-badge {{
      margin-right: 0.5rem;
    }}

    /* Status dropdown compact sizing */
    .status-dropdown {{
      font-size: 0.75rem;
      padding: 0.2em 0.5em;
    }}
    .shortlist-btn {{
      margin-left: 0.5rem;
    }}
    .shortlist-btn.is-shortlisted {{
      color: #212529;
      background-color: #ffc107;
      border-color: #ffc107;
    }}
    body.compact-report .job-detail-list {{
      display: none;
    }}
    body.compact-report .job-card-body {{
      padding-top: 0.75rem;
      padding-bottom: 0.75rem;
    }}
    body.compact-report .col-snippet {{
      display: none;
    }}

    /* Pending sync indicator dot */
    .pending-dot {{
      display: inline-block;
      width: 6px;
      height: 6px;
      background-color: #ffc107;
      border-radius: 50%;
      margin-left: 4px;
      vertical-align: middle;
      title: "Pending sync to tracker.json";
    }}

    /* Export status button */
    .export-status-btn {{
      margin-left: 0.5rem;
    }}

    /* WCAG AA contrast compliance */
    .text-muted {{
      color: #595959 !important;
    }}
    [data-bs-theme="dark"] .text-muted {{
      color: #adb5bd !important;
    }}
    .badge.bg-warning {{
      color: #212529 !important;
    }}

    /* Visually hidden utility for screen readers */
    .visually-hidden {{
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }}

    /* Hero job elevated styling */
    .hero-job {{
      box-shadow: var(--shadow-hero);
      margin-bottom: 1.5rem;
    }}
    .hero-job .card-body {{
      padding: 1.5rem;
    }}

    /* Badge label for "Top Match" text */
    .badge-label {{
      margin-left: 0.5em;
      font-size: 0.85em;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.025em;
    }}

    /* Section divider between hero and recommended */
    .section-divider {{
      height: 1px;
      background: linear-gradient(to right, transparent, #dee2e6 20%, #dee2e6 80%, transparent);
      margin: 3rem 0;
    }}

    /* Enhanced focus indicator for hero cards */
    .hero-job:focus-visible {{
      outline: 3px solid var(--color-tier-strong-border);
      outline-offset: 3px;
    }}

    /* Responsive badge label for mobile */
    @media (max-width: 576px) {{
      .badge-label {{
        font-size: 0.7em;
      }}
    }}

    /* Dark mode section divider */
    @media (prefers-color-scheme: dark) {{
      .section-divider {{
        background: linear-gradient(to right, transparent, #495057 20%, #495057 80%, transparent);
      }}
    }}

    /* ---- Responsive Layout ---- */
    /* Tablet: hide low-priority columns */
    @media (max-width: 991px) {{
      .col-new,
      .col-salary,
      .col-type,
      .col-snippet {{
        display: none;
      }}
    }}

    /* Mobile: table to stacked cards */
    @media (max-width: 767px) {{
      body {{
        font-size: 0.95rem;
      }}
      .container {{
        padding-left: 0.75rem;
        padding-right: 0.75rem;
      }}
      [role="region"][aria-labelledby="filter-heading"] {{
        position: sticky;
        top: 0;
        z-index: 20;
        background: var(--bs-body-bg);
        border-bottom: 1px solid #dee2e6;
        padding-top: 0.75rem;
        padding-bottom: 0.75rem;
      }}
      [role="region"][aria-labelledby="filter-heading"] .btn-group,
      [role="region"][aria-labelledby="filter-heading"] .btn {{
        width: 100%;
      }}
      [role="region"][aria-labelledby="filter-heading"] .btn-group {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.35rem;
      }}
      [role="region"][aria-labelledby="filter-heading"] .btn-group > .btn {{
        border-radius: 0.375rem !important;
        min-height: 44px;
      }}
      .copy-all-btn,
      .export-status-btn,
      #export-csv-btn,
      #view-mode-toggle {{
        width: 100%;
        margin-top: 0.35rem;
        margin-left: 0 !important;
        min-height: 44px;
      }}
      .shortcut-hint {{
        display: block;
        width: 100%;
        margin-left: 0 !important;
        margin-top: 0.5rem;
      }}
      .card-header h3 {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        align-items: center;
      }}
      .status-dropdown,
      .shortlist-btn {{
        min-height: 44px;
        margin-left: 0;
      }}
      .job-card-body {{
        padding: 1rem;
      }}
    .job-detail-list > li {{
        margin-bottom: 0.4rem;
      }}

      /* Visually hide table headers (keep in DOM for ARIA) */
      thead {{
        position: absolute;
        clip: rect(0 0 0 0);
        height: 1px;
        width: 1px;
        overflow: hidden;
        white-space: nowrap;
      }}

      /* Convert table elements to block stacking */
      table.table, table.table tbody, table.table tr, table.table td, table.table th {{
        display: block;
        width: 100%;
      }}

      /* Remove Bootstrap striped/hover on mobile */
      .table-striped > tbody > tr:nth-of-type(odd) > * {{
        --bs-table-bg-type: transparent;
      }}
      .table-hover > tbody > tr:hover > * {{
        --bs-table-bg-state: transparent;
      }}

      /* Each row becomes a card */
      table.table tbody tr {{
        margin-bottom: 1rem;
        padding: 0.85rem;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        background: white;
      }}

      /* Preserve tier left borders on mobile cards */
      table.table tbody tr.tier-strong {{
        border-left: 5px solid var(--color-tier-strong-border);
        background-color: var(--color-tier-strong-bg) !important;
      }}
      table.table tbody tr.tier-rec {{
        border-left: 4px solid var(--color-tier-rec-border);
        background-color: var(--color-tier-rec-bg) !important;
      }}
      table.table tbody tr.tier-review {{
        border-left: 3px solid var(--color-tier-review-border);
        background-color: var(--color-tier-review-bg) !important;
      }}

      /* Show ALL columns in mobile (override tablet hiding) */
      .col-new,
      .col-salary,
      .col-type,
      .col-snippet {{
        display: block !important;
      }}

      /* Grid layout for each cell: label + value */
      table.table td,
      table.table th[scope="row"] {{
        display: grid;
        grid-template-columns: minmax(5.5rem, 35%) 1fr;
        gap: 0.5rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e9ecef;
        align-items: start;
      }}

      table.table td:last-child,
      table.table th[scope="row"]:last-child {{
        border-bottom: none;
      }}

      /* Label from data-label attribute */
      table.table td::before,
      table.table th[scope="row"]::before {{
        content: attr(data-label);
        font-weight: 600;
        color: #6c757d;
        font-size: var(--font-size-small);
      }}

      /* Hide label for cells that don't need one (e.g., Link column with self-explanatory button) */
      table.table td.no-label::before {{
        display: none;
      }}
      table.table td.no-label {{
        grid-template-columns: 1fr;
      }}

      /* Touch targets: minimum 44x44px for interactive elements */
      table.table td button,
      table.table td select,
      table.table td .btn,
      table.table td .dropdown-toggle {{
        min-height: 44px;
        min-width: 44px;
      }}
      table.table td .btn,
      table.table td .dropdown {{
        width: 100%;
      }}

      /* Row number cell: simplify display */
      table.table th[scope="row"] {{
        font-weight: 600;
        color: #6c757d;
        font-size: var(--font-size-small);
        padding-top: 0.75rem;
      }}
    }}

    /* Dark mode + mobile card adjustments */
    @media (prefers-color-scheme: dark) and (max-width: 767px) {{
      [role="region"][aria-labelledby="filter-heading"] {{
        border-bottom-color: #495057;
      }}
      table.table tbody tr {{
        background: #212529;
        border-color: #495057;
      }}
      table.table td,
      table.table th[scope="row"] {{
        border-bottom-color: #343a40;
      }}
      table.table td::before,
      table.table th[scope="row"]::before {{
        color: #adb5bd;
      }}
    }}
  </style>

  <!-- Embedded tracker status (source of truth) -->
  <script type="application/json" id="tracker-status">
{embedded_status_json}
  </script>
  <script type="application/json" id="review-state">
{embedded_review_state_json}
  </script>
</head>
<body>
  <a href="#main-content" class="visually-hidden-focusable">Skip to main content</a>

  <header role="banner">
    <div class="container my-4">
      <h1 class="mb-3">Job Search Results — {name}</h1>

      <div class="alert alert-info">
        <strong>Date:</strong> {today}<br>
        <strong>Sources searched:</strong> {html.escape(', '.join(sources_searched))}<br>
        <strong>Date filter:</strong> {html.escape(from_date)} to {html.escape(to_date)}<br>
        <strong>Total results:</strong> {total} ({new_count} new)<br>
        <strong>Top matches (4.0+):</strong> {len(hero_jobs)} | <strong>Recommended (3.5+):</strong> {len(recommended)}
      </div>

      {_html_tracker_stats(tracker_stats) if tracker_stats else ''}
      {_html_source_failures(source_failures) if source_failures else ''}
      {_html_source_warnings(source_warnings) if source_warnings else ''}
    </div>
  </header>

  <main id="main-content" role="main">
    <div class="container">
      {_html_profile_section(profile)}

      {_html_hero_section(hero_jobs, profile)}

      {'<div class="section-divider" role="separator" aria-hidden="true"></div>' if hero_jobs and recommended else ''}

      {_html_recommended_section(recommended, profile)}

      {_html_results_table(scored_results)}

      {_html_filtered_out_section(filtered_out, min_score)}

      {_html_manual_urls_section(manual_urls)}

      <div id="status-announcer" role="status" aria-live="polite" aria-atomic="true" class="visually-hidden"></div>
    </div>
  </main>

  <footer role="contentinfo">
    <div class="container my-4">
      <p class="text-muted text-center mb-0">Generated by Job Radar on {today}</p>
    </div>
  </footer>
{_html_external_scripts()}

  <!-- Clipboard and keyboard functionality -->
  <script>
    // Initialize Notyf toast notifications
    const notyf = new Notyf({{
      duration: 3000,
      position: {{ x: 'right', y: 'top' }},
      dismissible: true
    }});

    // Two-tier clipboard: Clipboard API (HTTPS/localhost) with execCommand fallback (file://)
    async function copyToClipboard(text) {{
      if (typeof navigator.clipboard === 'object') {{
        try {{
          await navigator.clipboard.writeText(text);
          return true;
        }} catch (err) {{
          console.warn('[clipboard] API failed, trying fallback', err);
        }}
      }}
      // Fallback for file:// protocol
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.focus({{ preventScroll: true }});
      ta.select();
      try {{
        const ok = document.execCommand('copy');
        ta.remove();
        return ok;
      }} catch (err) {{
        console.error('[clipboard] execCommand failed', err);
        ta.remove();
        return false;
      }}
    }}

    // Copy single URL from button click
    function copySingleUrl(btn) {{
      const url = btn.dataset.url;
      if (!url) {{
        const msg = 'No URL available';
        notyf.error(msg);
        announceToScreenReader(msg);
        return;
      }}
      copyToClipboard(url).then(function(ok) {{
        if (ok) {{
          const msg = 'Job URL copied to clipboard';
          notyf.success(msg);
          announceToScreenReader(msg);
          btn.classList.add('copied');
          btn.textContent = 'Copied!';
          setTimeout(function() {{
            btn.classList.remove('copied');
            btn.textContent = btn.closest('tr') ? 'Copy' : 'Copy URL';
          }}, 2000);
        }} else {{
          const msg = 'Copy failed — try Ctrl+C';
          notyf.error(msg);
          announceToScreenReader(msg);
        }}
      }});
    }}

    // Copy all hero URLs (score >= 4.0)
    function copyAllHeroUrls(btn) {{
      const items = document.querySelectorAll('.hero-jobs-section .job-item[data-job-url]');
      const urls = Array.from(items)
        .map(function(el) {{ return el.dataset.jobUrl; }})
        .filter(function(u) {{ return u && u.length > 0; }});

      if (urls.length === 0) {{
        const msg = 'No top match jobs found (score >= 4.0)';
        notyf.error(msg);
        announceToScreenReader(msg);
        return;
      }}

      copyToClipboard(urls.join('\\n')).then(function(ok) {{
        if (ok) {{
          const msg = urls.length + ' job URL' + (urls.length > 1 ? 's' : '') + ' copied to clipboard';
          notyf.success(msg);
          announceToScreenReader(msg);
          if (btn) {{
            btn.classList.add('copied');
            btn.textContent = 'Copied ' + urls.length + ' URLs!';
            setTimeout(function() {{
              btn.classList.remove('copied');
              btn.textContent = 'Copy All Top Match URLs';
            }}, 2000);
          }}
        }} else {{
          const msg = 'Copy failed — try selecting URLs manually';
          notyf.error(msg);
          announceToScreenReader(msg);
        }}
      }});
    }}

    // Copy all recommended URLs (score 3.5 - 3.9)
    function copyAllRecommendedUrls(btn) {{
      const items = document.querySelectorAll('.job-item[data-job-url][data-score]');
      const urls = Array.from(items)
        .filter(function(el) {{
          var s = parseFloat(el.dataset.score);
          return !isNaN(s) && s >= 3.5 && s < 4.0;
        }})
        .map(function(el) {{ return el.dataset.jobUrl; }})
        .filter(function(u) {{ return u && u.length > 0; }});

      if (urls.length === 0) {{
        const msg = 'No recommended jobs found (score 3.5 - 3.9)';
        notyf.error(msg);
        announceToScreenReader(msg);
        return;
      }}

      copyToClipboard(urls.join('\\n')).then(function(ok) {{
        if (ok) {{
          const msg = urls.length + ' job URL' + (urls.length > 1 ? 's' : '') + ' copied to clipboard';
          notyf.success(msg);
          announceToScreenReader(msg);
          if (btn) {{
            btn.classList.add('copied');
            btn.textContent = 'Copied ' + urls.length + ' URLs!';
            setTimeout(function() {{
              btn.classList.remove('copied');
              btn.textContent = 'Copy All Recommended URLs';
            }}, 2000);
          }}
        }} else {{
          const msg = 'Copy failed — try selecting URLs manually';
          notyf.error(msg);
          announceToScreenReader(msg);
        }}
      }});
    }}

    // Track focused job item for keyboard shortcuts
    var currentFocusedJob = null;
    document.querySelectorAll('.job-item').forEach(function(item) {{
      item.addEventListener('focus', function() {{ currentFocusedJob = item; }});
      item.addEventListener('blur', function() {{
        if (currentFocusedJob === item) currentFocusedJob = null;
      }});
    }});

    function visibleJobItems() {{
      return Array.from(document.querySelectorAll('.job-item')).filter(function(item) {{
        return item.style.display !== 'none' && item.getAttribute('aria-hidden') !== 'true';
      }});
    }}

    function focusJobByOffset(offset) {{
      var jobs = visibleJobItems();
      if (jobs.length === 0) {{
        const msg = 'No visible jobs to navigate';
        notyf.error(msg);
        announceToScreenReader(msg);
        return;
      }}

      var currentIndex = currentFocusedJob ? jobs.indexOf(currentFocusedJob) : -1;
      var nextIndex = currentIndex + offset;
      if (currentIndex === -1) {{
        nextIndex = offset > 0 ? 0 : jobs.length - 1;
      }}
      if (nextIndex < 0) nextIndex = jobs.length - 1;
      if (nextIndex >= jobs.length) nextIndex = 0;

      jobs[nextIndex].focus();
      jobs[nextIndex].scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
      announceToScreenReader('Focused job ' + (nextIndex + 1) + ' of ' + jobs.length);
    }}

    // Keyboard shortcuts: J/ArrowDown = next job, K/ArrowUp = previous job,
    // C = copy focused, A = copy all recommended.
    document.addEventListener('keydown', function(event) {{
      // Don't interfere with form inputs
      if (event.target.matches('input, textarea, select')) return;
      // Don't interfere with browser shortcuts (Ctrl+C, Ctrl+A, etc.)
      if (event.ctrlKey || event.metaKey || event.altKey) return;

      var key = event.key.toLowerCase();

      if (key === 'j' || event.key === 'ArrowDown') {{
        event.preventDefault();
        focusJobByOffset(1);
      }} else if (key === 'k' || event.key === 'ArrowUp') {{
        event.preventDefault();
        focusJobByOffset(-1);
      }} else if (key === 'c') {{
        event.preventDefault();
        if (!currentFocusedJob) {{
          const msg = 'No job focused — click a job or use Tab to navigate';
          notyf.error(msg);
          announceToScreenReader(msg);
          return;
        }}
        var url = currentFocusedJob.dataset.jobUrl;
        if (!url) {{
          const msg = 'Focused job has no URL';
          notyf.error(msg);
          announceToScreenReader(msg);
          return;
        }}
        copyToClipboard(url).then(function(ok) {{
          const msg = ok ? 'Job URL copied to clipboard' : 'Copy failed — try Ctrl+C';
          if (ok) notyf.success(msg);
          else notyf.error(msg);
          announceToScreenReader(msg);
        }});
      }} else if (key === 'a') {{
        event.preventDefault();
        copyAllRecommendedUrls(document.querySelector('.copy-all-btn'));
      }}
    }});

    // Helper to announce messages to screen readers via ARIA live region
    function announceToScreenReader(message) {{
      const announcer = document.getElementById('status-announcer');
      if (!announcer) return;
      announcer.textContent = message;
      setTimeout(function() {{
        announcer.textContent = '';
      }}, 1000);
    }}
  </script>

  <!-- Application status management -->
  <script>
    // Status configuration with semantic colors
    var STATUS_CONFIG = {{
      applied:      {{ class: 'bg-success rounded-pill', label: 'Applied' }},
      interviewing: {{ class: 'bg-primary rounded-pill', label: 'Interviewing' }},
      rejected:     {{ class: 'bg-danger rounded-pill',  label: 'Rejected' }},
      offer:        {{ class: 'bg-warning text-dark rounded-pill', label: 'Offer' }}
    }};

    // Hydrate application status from embedded tracker data + localStorage
    function hydrateApplicationStatus() {{
      // Parse embedded tracker status (source of truth)
      var trackerStatusEl = document.getElementById('tracker-status');
      var trackerStatus = trackerStatusEl ? JSON.parse(trackerStatusEl.textContent) : {{}};

      // Parse localStorage cache
      var localStorageKey = 'job-radar-application-status';
      var localStatus = {{}};
      try {{
        var localData = localStorage.getItem(localStorageKey);
        localStatus = localData ? JSON.parse(localData) : {{}};
      }} catch (err) {{
        console.warn('[status] Failed to load localStorage:', err);
      }}

      // Merge: tracker.json wins for existing entries, localStorage adds new with pending_sync flag
      var merged = {{}};
      var pendingCount = 0;

      // Copy tracker.json entries
      for (var key in trackerStatus) {{
        if (trackerStatus.hasOwnProperty(key)) {{
          merged[key] = trackerStatus[key];
        }}
      }}

      // Add localStorage entries that aren't in tracker.json
      for (var key in localStatus) {{
        if (localStatus.hasOwnProperty(key)) {{
          if (!merged[key]) {{
            // New status not yet in tracker.json
            merged[key] = localStatus[key];
            merged[key].pending_sync = true;
            pendingCount++;
          }} else if (localStatus[key].updated && merged[key].updated && localStatus[key].updated > merged[key].updated) {{
            // localStorage has newer update (rare)
            merged[key] = localStatus[key];
            merged[key].pending_sync = true;
            pendingCount++;
          }}
        }}
      }}

      // Save merged state back to localStorage
      try {{
        localStorage.setItem(localStorageKey, JSON.stringify(merged));
      }} catch (err) {{
        console.error('[status] Failed to save to localStorage:', err);
        notyf.error('Status storage quota exceeded');
      }}

      // Render all status badges
      renderAllStatusBadges(merged);

      // Update export button count
      updateExportButtonCount(pendingCount);
    }}

    // Render status badges on all job items
    function renderAllStatusBadges(statusMap) {{
      var jobElements = document.querySelectorAll('[data-job-key]');
      for (var i = 0; i < jobElements.length; i++) {{
        var element = jobElements[i];
        var jobKey = element.getAttribute('data-job-key');
        if (!jobKey) continue;

        var statusEntry = statusMap[jobKey];
        if (statusEntry && statusEntry.status) {{
          var isPending = statusEntry.pending_sync === true;
          renderStatusBadge(element, statusEntry.status, isPending);
        }}
      }}
    }}

    // Render status badge for a single job element
    function renderStatusBadge(jobElement, status, isPending) {{
      var config = STATUS_CONFIG[status];
      if (!config) return;

      // Find card header or table row
      var header = jobElement.querySelector('.card-header');
      var isTableRow = jobElement.tagName === 'TR';

      if (isTableRow) {{
        // For table rows, find the Status column (4th column after #, Score, New)
        var statusCell = jobElement.children[3]; // 0-based: #, Score, New, Status
        if (!statusCell) return;

        // Remove existing badge if present
        var existingBadge = statusCell.querySelector('.status-badge');
        if (existingBadge) existingBadge.remove();

        // Create badge
        var badge = document.createElement('span');
        badge.className = 'badge ' + config.class + ' status-badge';
        badge.textContent = config.label;

        // Add pending indicator if not synced
        if (isPending) {{
          var pendingIcon = document.createElement('span');
          pendingIcon.className = 'pending-dot';
          pendingIcon.title = 'Pending sync to tracker.json';
          badge.appendChild(pendingIcon);
        }}

        // Insert badge before dropdown
        var dropdown = statusCell.querySelector('.dropdown');
        if (dropdown) {{
          statusCell.insertBefore(badge, dropdown);
        }} else {{
          statusCell.appendChild(badge);
        }}
      }} else if (header) {{
        // For cards, insert in header
        // Remove existing badge if present
        var existingBadge = header.querySelector('.status-badge');
        if (existingBadge) existingBadge.remove();

        // Create badge
        var badge = document.createElement('span');
        badge.className = 'badge ' + config.class + ' status-badge';
        badge.textContent = config.label;

        // Add pending indicator if not synced
        if (isPending) {{
          var pendingIcon = document.createElement('span');
          pendingIcon.className = 'pending-dot';
          pendingIcon.title = 'Pending sync to tracker.json';
          badge.appendChild(pendingIcon);
        }}

        // Insert before status dropdown or at end of h3
        var h3 = header.querySelector('h3');
        if (h3) {{
          var dropdown = h3.querySelector('.dropdown');
          if (dropdown) {{
            h3.insertBefore(badge, dropdown);
          }} else {{
            h3.appendChild(badge);
          }}
        }}
      }}
    }}

    // Remove status badge from element
    function removeStatusBadge(jobElement) {{
      var isTableRow = jobElement.tagName === 'TR';
      if (isTableRow) {{
        var statusCell = jobElement.children[3];
        if (statusCell) {{
          var badge = statusCell.querySelector('.status-badge');
          if (badge) badge.remove();
        }}
      }} else {{
        var header = jobElement.querySelector('.card-header');
        if (header) {{
          var badge = header.querySelector('.status-badge');
          if (badge) badge.remove();
        }}
      }}
    }}

    // Status change click handler (event delegation)
    document.addEventListener('click', function(event) {{
      if (!event.target.matches('.dropdown-item[data-status]')) return;

      event.preventDefault();

      var statusItem = event.target;
      var newStatus = statusItem.getAttribute('data-status');
      var dropdown = statusItem.closest('.dropdown');
      if (!dropdown) return;

      // Find parent job element (card or table row)
      var jobElement = dropdown.closest('[data-job-key]');
      if (!jobElement) {{
        console.error('[status] No job element found with data-job-key');
        return;
      }}

      var jobKey = jobElement.getAttribute('data-job-key');
      var jobTitle = jobElement.getAttribute('data-job-title') || 'Unknown';
      var jobCompany = jobElement.getAttribute('data-job-company') || 'Unknown';

      if (!jobKey) {{
        console.error('[status] No job key found');
        return;
      }}

      // Load current status map
      var localStorageKey = 'job-radar-application-status';
      var statusMap = {{}};
      try {{
        var localData = localStorage.getItem(localStorageKey);
        statusMap = localData ? JSON.parse(localData) : {{}};
      }} catch (err) {{
        console.warn('[status] Failed to load localStorage:', err);
      }}

      // Update or remove status
      if (newStatus === '') {{
        // Clear status
        delete statusMap[jobKey];
        removeStatusBadge(jobElement);
        var msg = 'Status cleared';
        notyf.success(msg);
        announceToScreenReader(msg);
      }} else {{
        // Set new status
        statusMap[jobKey] = {{
          title: jobTitle,
          company: jobCompany,
          status: newStatus,
          updated: new Date().toISOString(),
          pending_sync: true
        }};
        renderStatusBadge(jobElement, newStatus, true);
        var statusLabel = STATUS_CONFIG[newStatus] ? STATUS_CONFIG[newStatus].label : newStatus;
        var msg = 'Marked as ' + statusLabel;
        notyf.success(msg);
        announceToScreenReader(msg);
      }}

      // Save to localStorage
      try {{
        localStorage.setItem(localStorageKey, JSON.stringify(statusMap));
      }} catch (err) {{
        console.error('[status] Failed to save to localStorage:', err);
        notyf.error('Status storage quota exceeded');
      }}

      // Re-apply filter after status change (if filter function is available)
      if (typeof applyFilter === 'function') {{
        applyFilter();
      }}

      // Update export button count
      var pendingCount = 0;
      for (var key in statusMap) {{
        if (statusMap.hasOwnProperty(key) && statusMap[key].pending_sync === true) {{
          pendingCount++;
        }}
      }}
      updateExportButtonCount(pendingCount);
    }});

    // Export pending status updates as JSON file
    function exportPendingStatusUpdates() {{
      var localStorageKey = 'job-radar-application-status';
      var statusMap = {{}};
      try {{
        var localData = localStorage.getItem(localStorageKey);
        statusMap = localData ? JSON.parse(localData) : {{}};
      }} catch (err) {{
        console.warn('[status] Failed to load localStorage:', err);
        notyf.error('Failed to load status updates');
        return;
      }}

      // Filter entries with pending_sync flag
      var pendingUpdates = {{}};
      for (var key in statusMap) {{
        if (statusMap.hasOwnProperty(key) && statusMap[key].pending_sync === true) {{
          pendingUpdates[key] = {{
            title: statusMap[key].title,
            company: statusMap[key].company,
            status: statusMap[key].status,
            updated: statusMap[key].updated
          }};
        }}
      }}

      var count = Object.keys(pendingUpdates).length;
      if (count === 0) {{
        var msg = 'No pending status updates to export';
        notyf.error(msg);
        announceToScreenReader(msg);
        return;
      }}

      // Create JSON blob with applications structure
      var exportData = {{ applications: pendingUpdates }};
      var blob = new Blob(
        [JSON.stringify(exportData, null, 2)],
        {{ type: 'application/json' }}
      );
      var url = URL.createObjectURL(blob);
      var link = document.createElement('a');
      link.href = url;
      link.download = 'job-status-updates-' + new Date().toISOString().split('T')[0] + '.json';
      link.click();
      URL.revokeObjectURL(url);

      var msg = 'Exported ' + count + ' status update' + (count > 1 ? 's' : '');
      notyf.success(msg);
      announceToScreenReader(msg);
    }}

    // Update export button count
    function updateExportButtonCount(count) {{
      var btn = document.querySelector('.export-status-btn');
      if (!btn) return;

      if (count > 0) {{
        btn.textContent = 'Export Status Updates (' + count + ')';
      }} else {{
        btn.textContent = 'Export Status Updates';
      }}
    }}

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {{
      hydrateApplicationStatus();
    }});

    // ARIA role restoration for table semantics with display:block
    // Source: Adrian Roselli pattern (2018, updated 2023)
    function AddTableARIA() {{
      try {{
        document.querySelectorAll('table').forEach(function(t) {{ t.setAttribute('role', 'table'); }});
        document.querySelectorAll('caption').forEach(function(c) {{ c.setAttribute('role', 'caption'); }});
        document.querySelectorAll('thead, tbody, tfoot').forEach(function(rg) {{ rg.setAttribute('role', 'rowgroup'); }});
        document.querySelectorAll('tr').forEach(function(r) {{ r.setAttribute('role', 'row'); }});
        document.querySelectorAll('td').forEach(function(c) {{ c.setAttribute('role', 'cell'); }});
        document.querySelectorAll('th').forEach(function(h) {{ h.setAttribute('role', 'columnheader'); }});
        document.querySelectorAll('th[scope=row]').forEach(function(rh) {{ rh.setAttribute('role', 'rowheader'); }});
      }} catch (e) {{
        console.log('AddTableARIA(): ' + e);
      }}
    }}
    AddTableARIA();
  </script>

  <!-- Status filtering with localStorage persistence -->
  <script>
    // Filter state management
    var filterState = {{
      hideApplied: false,
      hideRejected: false,
      hideInterviewing: false,
      hideOffer: false,
      showShortlistOnly: false
    }};

    // Load filter state from localStorage
    function loadFilterState() {{
      try {{
        var saved = localStorage.getItem('job-radar-filter-state');
        if (saved) {{
          var parsed = JSON.parse(saved);
          filterState = Object.assign({{}}, filterState, parsed);
        }}
      }} catch (err) {{
        console.warn('[filter] Failed to load filter state:', err);
      }}
    }}

    // Save filter state to localStorage
    function saveFilterState() {{
      try {{
        localStorage.setItem('job-radar-filter-state', JSON.stringify(filterState));
      }} catch (err) {{
        if (err.name === 'QuotaExceededError') {{
          notyf.error('Storage quota exceeded');
        }}
        console.error('[filter] Failed to save filter state:', err);
      }}
    }}

    // Apply filter to all jobs
    function applyFilter() {{
      // Load application status map
      var statusMap = {{}};
      var shortlistMap = loadShortlistState();
      try {{
        var statusData = localStorage.getItem('job-radar-application-status');
        statusMap = statusData ? JSON.parse(statusData) : {{}};
      }} catch (err) {{
        console.warn('[filter] Failed to load status map:', err);
      }}

      // Query all job elements
      var jobElements = document.querySelectorAll('[data-job-key]');
      var visibleCount = 0;
      var totalCount = jobElements.length;

      for (var i = 0; i < jobElements.length; i++) {{
        var element = jobElements[i];
        var jobKey = element.getAttribute('data-job-key');
        if (!jobKey) continue;

        // Check if job has a status
        var statusEntry = statusMap[jobKey];
        var jobStatus = statusEntry ? statusEntry.status : null;
        var isShortlisted = Boolean(shortlistMap[jobKey]);

        // Determine if job should be hidden
        var shouldHide = false;
        if (filterState.showShortlistOnly && !isShortlisted) {{
          shouldHide = true;
        }} else if (jobStatus === 'applied' && filterState.hideApplied) {{
          shouldHide = true;
        }} else if (jobStatus === 'rejected' && filterState.hideRejected) {{
          shouldHide = true;
        }} else if (jobStatus === 'interviewing' && filterState.hideInterviewing) {{
          shouldHide = true;
        }} else if (jobStatus === 'offer' && filterState.hideOffer) {{
          shouldHide = true;
        }}

        // Apply visibility
        if (shouldHide) {{
          element.style.display = 'none';
          element.setAttribute('aria-hidden', 'true');
        }} else {{
          element.style.display = '';
          element.removeAttribute('aria-hidden');
          visibleCount++;
        }}
      }}

      // Update filter count display and announce to screen readers
      announceFilterCount(visibleCount, totalCount);
      var filterCountEl = document.getElementById('filter-count');
      if (filterCountEl) {{
        if (visibleCount === totalCount) {{
          filterCountEl.textContent = '';
        }} else {{
          filterCountEl.textContent = 'Showing ' + visibleCount + ' of ' + totalCount + ' jobs';
        }}
      }}
    }}

    // Announce filter count to screen readers
    function announceFilterCount(visibleCount, totalCount) {{
      var announcer = document.getElementById('status-announcer');
      if (!announcer) return;

      var message = visibleCount === totalCount
        ? 'Showing all ' + totalCount + ' jobs'
        : 'Showing ' + visibleCount + ' of ' + totalCount + ' jobs';

      announcer.textContent = message;
      setTimeout(function() {{
        announcer.textContent = '';
      }}, 1000);
    }}

    // Handle filter checkbox changes
    function handleFilterChange(event) {{
      var checkbox = event.target;
      var checkboxId = checkbox.id;

      var stateKey = 'hide' + checkboxId.replace('filter-', '').charAt(0).toUpperCase() +
                     checkboxId.replace('filter-', '').slice(1);
      if (checkboxId === 'filter-shortlist') {{
        stateKey = 'showShortlistOnly';
      }}

      filterState[stateKey] = checkbox.checked;
      saveFilterState();
      applyFilter();
    }}

    // Clear all filters
    function clearAllFilters() {{
      filterState.hideApplied = false;
      filterState.hideRejected = false;
      filterState.hideInterviewing = false;
      filterState.hideOffer = false;
      filterState.showShortlistOnly = false;
      saveFilterState();

      // Update checkbox UI
      document.getElementById('filter-applied').checked = false;
      document.getElementById('filter-rejected').checked = false;
      document.getElementById('filter-interviewing').checked = false;
      document.getElementById('filter-offer').checked = false;
      document.getElementById('filter-shortlist').checked = false;

      applyFilter();

      var msg = 'All filters cleared';
      notyf.success(msg);
      announceToScreenReader(msg);
    }}

    // Initialize filters on page load
    function initializeFilters() {{
      loadFilterState();

      // Set checkbox states from loaded filter state
      document.getElementById('filter-applied').checked = filterState.hideApplied;
      document.getElementById('filter-rejected').checked = filterState.hideRejected;
      document.getElementById('filter-interviewing').checked = filterState.hideInterviewing;
      document.getElementById('filter-offer').checked = filterState.hideOffer;
      document.getElementById('filter-shortlist').checked = filterState.showShortlistOnly;

      // Attach event listeners
      document.getElementById('filter-applied').addEventListener('change', handleFilterChange);
      document.getElementById('filter-rejected').addEventListener('change', handleFilterChange);
      document.getElementById('filter-interviewing').addEventListener('change', handleFilterChange);
      document.getElementById('filter-offer').addEventListener('change', handleFilterChange);
      document.getElementById('filter-shortlist').addEventListener('change', handleFilterChange);
      document.getElementById('clear-filters').addEventListener('click', clearAllFilters);

      // Apply persisted filter state
      applyFilter();
    }}

    // Initialize filters after status hydration
    document.addEventListener('DOMContentLoaded', function() {{
      initializeFilters();
      initializeShortlistControls();
      initializeViewModeToggle();
    }});

    function loadShortlistState() {{
      var shortlistMap = loadEmbeddedShortlistState();
      try {{
        var data = localStorage.getItem('job-radar-shortlist-state');
        if (data) {{
          var localMap = JSON.parse(data);
          for (var key in localMap) {{
            if (Object.prototype.hasOwnProperty.call(localMap, key)) {{
              shortlistMap[key] = localMap[key];
            }}
          }}
        }}
      }} catch (err) {{
        console.warn('[shortlist] Failed to load localStorage:', err);
      }}
      return shortlistMap;
    }}

    function loadEmbeddedShortlistState() {{
      var shortlistMap = {{}};
      try {{
        var stateEl = document.getElementById('review-state');
        var data = stateEl ? JSON.parse(stateEl.textContent || '{{}}') : {{}};
        var jobs = data.jobs || {{}};
        for (var key in jobs) {{
          if (
            Object.prototype.hasOwnProperty.call(jobs, key) &&
            jobs[key].state === 'shortlisted'
          ) {{
            shortlistMap[key] = true;
          }}
        }}
      }} catch (err) {{
        console.warn('[shortlist] Failed to load embedded review state:', err);
      }}
      return shortlistMap;
    }}

    function saveShortlistState(shortlistMap) {{
      try {{
        localStorage.setItem('job-radar-shortlist-state', JSON.stringify(shortlistMap));
      }} catch (err) {{
        if (err.name === 'QuotaExceededError') {{
          notyf.error('Storage quota exceeded');
        }}
        console.error('[shortlist] Failed to save localStorage:', err);
      }}
    }}

    function loadReviewState() {{
      var reviewMap = {{}};
      try {{
        var stateEl = document.getElementById('review-state');
        var data = stateEl ? JSON.parse(stateEl.textContent || '{{}}') : {{}};
        var jobs = data.jobs || {{}};
        for (var key in jobs) {{
          if (Object.prototype.hasOwnProperty.call(jobs, key) && jobs[key].state) {{
            reviewMap[key] = jobs[key].state;
          }}
        }}
      }} catch (err) {{
        console.warn('[review] Failed to load embedded review state:', err);
      }}
      try {{
        var localData = localStorage.getItem('job-radar-review-state');
        if (localData) {{
          var localMap = JSON.parse(localData);
          for (var localKey in localMap) {{
            if (Object.prototype.hasOwnProperty.call(localMap, localKey)) {{
              reviewMap[localKey] = localMap[localKey];
            }}
          }}
        }}
      }} catch (err) {{
        console.warn('[review] Failed to load localStorage:', err);
      }}
      return reviewMap;
    }}

    function saveReviewState(reviewMap) {{
      try {{
        localStorage.setItem('job-radar-review-state', JSON.stringify(reviewMap));
      }} catch (err) {{
        if (err.name === 'QuotaExceededError') {{
          notyf.error('Storage quota exceeded');
        }}
        console.error('[review] Failed to save localStorage:', err);
      }}
    }}

    function setShortlistButtonState(button, isShortlisted) {{
      button.classList.toggle('is-shortlisted', isShortlisted);
      button.setAttribute('aria-pressed', isShortlisted ? 'true' : 'false');
      button.textContent = isShortlisted ? 'Shortlisted' : 'Shortlist';
    }}

    function refreshShortlistButtons() {{
      var shortlistMap = loadShortlistState();
      var buttons = document.querySelectorAll('.shortlist-btn[data-shortlist-key]');
      for (var i = 0; i < buttons.length; i++) {{
        var key = buttons[i].getAttribute('data-shortlist-key');
        setShortlistButtonState(buttons[i], Boolean(shortlistMap[key]));
      }}
    }}

    function refreshReviewStateButtons() {{
      var reviewMap = loadReviewState();
      var buttons = document.querySelectorAll('.review-state-btn[data-review-key]');
      for (var i = 0; i < buttons.length; i++) {{
        var button = buttons[i];
        var key = button.getAttribute('data-review-key');
        var state = button.getAttribute('data-review-state');
        var isActive = reviewMap[key] === state;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
      }}
    }}

    function toggleShortlist(jobKey) {{
      var shortlistMap = loadShortlistState();
      var reviewMap = loadReviewState();
      if (shortlistMap[jobKey]) {{
        delete shortlistMap[jobKey];
        if (reviewMap[jobKey] === 'shortlisted') {{
          delete reviewMap[jobKey];
        }}
      }} else {{
        shortlistMap[jobKey] = true;
        reviewMap[jobKey] = 'shortlisted';
      }}
      saveShortlistState(shortlistMap);
      saveReviewState(reviewMap);
      refreshShortlistButtons();
      refreshReviewStateButtons();
      applyFilter();
    }}

    function toggleReviewState(jobKey, state) {{
      var reviewMap = loadReviewState();
      if (reviewMap[jobKey] === state) {{
        delete reviewMap[jobKey];
      }} else {{
        reviewMap[jobKey] = state;
      }}
      saveReviewState(reviewMap);
      refreshReviewStateButtons();
      applyFilter();
    }}

    function initializeShortlistControls() {{
      refreshShortlistButtons();
      refreshReviewStateButtons();
      document.addEventListener('click', function(event) {{
        if (event.target.matches('.shortlist-btn[data-shortlist-key]')) {{
          event.preventDefault();
          toggleShortlist(event.target.getAttribute('data-shortlist-key'));
          return;
        }}
        if (event.target.matches('.review-state-btn[data-review-key]')) {{
          event.preventDefault();
          toggleReviewState(
            event.target.getAttribute('data-review-key'),
            event.target.getAttribute('data-review-state')
          );
        }}
      }});
    }}

    function loadReportViewMode() {{
      try {{
        return localStorage.getItem('job-radar-report-view-mode') || 'detail';
      }} catch (err) {{
        console.warn('[view] Failed to load view mode:', err);
        return 'detail';
      }}
    }}

    function saveReportViewMode(mode) {{
      try {{
        localStorage.setItem('job-radar-report-view-mode', mode);
      }} catch (err) {{
        console.warn('[view] Failed to save view mode:', err);
      }}
    }}

    function setReportViewMode(mode) {{
      var compact = mode === 'compact';
      document.body.classList.toggle('compact-report', compact);
      var toggle = document.getElementById('view-mode-toggle');
      if (toggle) {{
        toggle.setAttribute('aria-pressed', compact ? 'true' : 'false');
        toggle.textContent = compact ? 'Detail View' : 'Compact View';
      }}
      announceToScreenReader(compact ? 'Compact report view enabled' : 'Detail report view enabled');
    }}

    function initializeViewModeToggle() {{
      var toggle = document.getElementById('view-mode-toggle');
      if (!toggle) return;
      setReportViewMode(loadReportViewMode());
      toggle.addEventListener('click', function() {{
        var nextMode = document.body.classList.contains('compact-report') ? 'detail' : 'compact';
        saveReportViewMode(nextMode);
        setReportViewMode(nextMode);
      }});
    }}

    // CSV Export Functions

    // RFC 4180 CSV field escaping with formula injection protection
    function escapeCSVField(value) {{
      // Handle null/undefined/empty
      if (value === null || value === undefined || value === '') {{
        return '';
      }}

      // Convert to string
      var str = String(value);

      // Formula injection protection: prefix dangerous characters
      if (/^[=+\\-@]/.test(str)) {{
        str = "'" + str;
      }}

      // RFC 4180 quoting: wrap if contains comma, quote, newline, or carriage return
      if (/[",\r\n]/.test(str)) {{
        str = '"' + str.replace(/"/g, '""') + '"';
      }}

      return str;
    }}

    // Extract job data from DOM element (table row or card)
    function extractJobDataFromElement(jobElement, rank) {{
      var isTableRow = jobElement.tagName === 'TR';
      var data = [];

      if (isTableRow) {{
        // Extract from table row cells
        var cells = jobElement.querySelectorAll('td, th');

        // Rank
        data.push(rank);

        // Score (cell 1) - extract numeric value
        var scoreText = cells[1] ? cells[1].textContent.trim() : '';
        var scoreMatch = scoreText.match(/(\\d+\\.\\d+)/);
        data.push(scoreMatch ? scoreMatch[1] : scoreText);

        // NEW badge (cell 2) - check for badge element
        var newBadge = cells[2] ? cells[2].querySelector('.badge.bg-primary') : null;
        data.push(newBadge ? 'Yes' : 'No');

        // Status (cell 3) - get from badge, strip bullet
        var statusBadge = cells[3] ? cells[3].querySelector('.status-badge') : null;
        var statusText = statusBadge ? statusBadge.textContent.trim().replace('●', '').trim() : '';
        data.push(statusText);

        // Title (cell 4)
        data.push(cells[4] ? cells[4].textContent.trim() : '');

        // Company (cell 5)
        data.push(cells[5] ? cells[5].textContent.trim() : '');

        // Salary (cell 6)
        data.push(cells[6] ? cells[6].textContent.trim() : '');

        // Type (cell 7)
        data.push(cells[7] ? cells[7].textContent.trim() : '');

        // Location (cell 8)
        data.push(cells[8] ? cells[8].textContent.trim() : '');

        // Snippet (cell 9)
        data.push(cells[9] ? cells[9].textContent.trim() : '');

        // URL from data attribute
        data.push(jobElement.getAttribute('data-job-url') || '');

      }} else {{
        // Extract from card
        data.push(rank);

        // Score from data-score attribute
        data.push(jobElement.getAttribute('data-score') || '');

        // NEW badge - check for badge element
        var newBadge = jobElement.querySelector('.badge.bg-primary');
        data.push(newBadge ? 'Yes' : 'No');

        // Status from badge
        var statusBadge = jobElement.querySelector('.status-badge');
        var statusText = statusBadge ? statusBadge.textContent.trim().replace('●', '').trim() : '';
        data.push(statusText);

        // Title from data attribute
        data.push(jobElement.getAttribute('data-job-title') || '');

        // Company from data attribute
        data.push(jobElement.getAttribute('data-job-company') || '');

        // Salary - parse from card body list items
        var salary = '';
        var listItems = jobElement.querySelectorAll('.card-body li');
        for (var i = 0; i < listItems.length; i++) {{
          var itemText = listItems[i].textContent;
          if (itemText.includes('Rate/Salary:')) {{
            salary = itemText.replace('Rate/Salary:', '').trim();
            break;
          }}
        }}
        data.push(salary);

        // Type - not available in cards, empty
        data.push('');

        // Location - parse from card body list items
        var location = '';
        for (var i = 0; i < listItems.length; i++) {{
          var itemText = listItems[i].textContent;
          if (itemText.includes('Location:')) {{
            location = itemText.replace('Location:', '').trim();
            break;
          }}
        }}
        data.push(location);

        // Snippet - not available in cards, empty
        data.push('');

        // URL from data attribute
        data.push(jobElement.getAttribute('data-job-url') || '');
      }}

      return data;
    }}

    // Export visible jobs to CSV file
    function exportVisibleJobsToCSV() {{
      // Get all job elements
      var allJobs = document.querySelectorAll('[data-job-key]');
      var visibleJobs = [];

      // Filter to visible jobs only
      for (var i = 0; i < allJobs.length; i++) {{
        var job = allJobs[i];
        // Check if hidden by filter (inline style or CSS class)
        if (job.style.display !== 'none' && job.offsetParent !== null) {{
          visibleJobs.push(job);
        }}
      }}

      // Check if there are visible jobs
      if (visibleJobs.length === 0) {{
        notyf.error('No visible jobs to export');
        announceToScreenReader('No visible jobs to export');
        return;
      }}

      // Build CSV header
      var headers = ['Rank', 'Score', 'New', 'Status', 'Title', 'Company', 'Salary', 'Type', 'Location', 'Snippet', 'URL'];
      var csvRows = [];
      csvRows.push(headers.map(escapeCSVField).join(','));

      // Build data rows
      for (var i = 0; i < visibleJobs.length; i++) {{
        var rowData = extractJobDataFromElement(visibleJobs[i], i + 1);
        csvRows.push(rowData.map(escapeCSVField).join(','));
      }}

      // Join rows with CRLF
      var csvContent = csvRows.join('\r\n');

      // Prepend UTF-8 BOM for Excel compatibility
      var csvWithBOM = '\uFEFF' + csvContent;

      // Create Blob and download
      var blob = new Blob([csvWithBOM], {{ type: 'text/csv;charset=utf-8;' }});
      var url = URL.createObjectURL(blob);

      // Create temporary download link
      var downloadLink = document.createElement('a');
      var filename = 'job-radar-export-' + new Date().toISOString().split('T')[0] + '.csv';
      downloadLink.href = url;
      downloadLink.download = filename;

      // Trigger download
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);

      // Clean up object URL
      URL.revokeObjectURL(url);

      // Show success notification
      var msg = 'Exported ' + visibleJobs.length + ' jobs to CSV';
      notyf.success(msg);
      announceToScreenReader(msg);
    }}
  </script>

  <!-- Dark mode handler -->
  <script>
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-bs-theme', prefersDark ? 'dark' : 'light');
  </script>
</body>
</html>"""

    filepath.write_text(html_content, encoding="utf-8")


def _html_hero_section(hero_jobs: list[dict], profile: dict) -> str:
    """Generate HTML for hero jobs section (score >= 4.0)."""
    return _render_html_hero_section(hero_jobs, profile)


def _html_recommended_section(recommended: list[dict], profile: dict) -> str:
    """Generate HTML for recommended roles section."""
    return _render_html_recommended_section(recommended, profile)


def _html_results_table(scored_results: list[dict]) -> str:
    """Generate HTML for all results table."""
    return _html_results_table_renderer(
        scored_results,
        row_renderer=_html_result_row,
        filter_controls=_html_filter_controls(),
    )


def _html_result_row(result: dict, index: int) -> str:
    """Generate one HTML row for the all-results table."""
    return _render_html_result_row(result, index)
