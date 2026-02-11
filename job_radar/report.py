"""Dual-format report generator (HTML + Markdown) for job search results."""

import html
import logging
import os
from datetime import date, datetime
from pathlib import Path

log = logging.getLogger(__name__)


def _make_snippet(text: str, max_len: int = 80) -> str:
    """Create a short snippet from description text, safe for markdown tables."""
    if not text:
        return "—"
    # Remove pipe chars that would break the table
    clean = text.replace("|", " ").replace("\n", " ").strip()
    if len(clean) > max_len:
        return clean[:max_len - 3].rsplit(" ", 1)[0] + "..."
    return clean if clean else "—"


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
        sources_searched, from_date, to_date, tracker_stats, min_score
    )

    # Generate HTML report
    html_filename = f"jobs_{timestamp}.html"
    html_path = output_path / html_filename
    _generate_html_report(
        html_path, profile, scored_results, manual_urls,
        sources_searched, from_date, to_date, tracker_stats, min_score
    )

    # Calculate statistics
    filtered_results = [r for r in scored_results if r["score"]["overall"] >= min_score]
    stats = {
        "total": len(filtered_results),
        "new": sum(1 for r in filtered_results if r.get("is_new", True)),
        "high_score": sum(1 for r in filtered_results if r["score"]["overall"] >= 3.5)
    }

    return {
        "markdown": str(md_path),
        "html": str(html_path),
        "stats": stats
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
) -> None:
    """Generate a Markdown report for a candidate's search results.

    This is the original generate_report function, now an internal helper.
    """
    name = profile["name"]
    today = date.today().isoformat()

    # Filter out dealbreakers and poor matches
    scored_results = [r for r in scored_results if r["score"]["overall"] >= min_score]
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

    # All results table
    lines.append("## All Results (sorted by score)")
    lines.append("")
    if scored_results:
        lines.append("| # | Score | New | Title | Company | Salary | Type | Location | Snippet | Link |")
        lines.append("|---|-------|-----|-------|---------|--------|------|----------|---------|------|")
        for i, r in enumerate(scored_results, 1):
            job = r["job"]
            score = r["score"]["overall"]
            rec = r["score"]["recommendation"]
            is_new = r.get("is_new", True)
            new_badge = "NEW" if is_new else ""
            link = f"[{job.source}]({job.url})" if job.url else job.source
            salary = job.salary if job.salary != "Not listed" else "—"
            emp_type = getattr(job, "employment_type", "") or job.arrangement
            snippet = _make_snippet(job.description, 80)
            lines.append(
                f"| {i} | **{score}/5.0** ({rec}) | {new_badge} | {job.title} | {job.company} "
                f"| {salary} | {emp_type} | {job.location} | {snippet} | {link} |"
            )
        lines.append("")
    else:
        lines.append("_No results found._")
        lines.append("")

    # Manual check URLs (grouped by source)
    lines.append("## Manual Check URLs")
    lines.append("_Open these in your browser to check sources that block automated access._")
    lines.append("")
    current_source = None
    for u in manual_urls:
        if u["source"] != current_source:
            current_source = u["source"]
            lines.append(f"**{current_source}:**")
        lines.append(f"- {u['title']}: [{u['source']} Search]({u['url']})")
    lines.append("")

    content = "\n".join(lines)
    filepath.write_text(content, encoding="utf-8")


def _format_detailed_result(lines: list, rank: int, result: dict, profile: dict):
    """Format a single detailed result entry for the recommended section."""
    job = result["job"]
    score = result["score"]
    components = score["components"]
    skill = components["skill_match"]
    response = components["response"]
    is_new = result.get("is_new", True)
    new_tag = " [NEW]" if is_new else ""

    lines.append(f"### {rank}. {job.title} — {job.company} — Score: {score['overall']}/5.0{new_tag}")
    lines.append(f"- **Posted:** {job.date_posted}")
    lines.append(f"- **Rate/Salary:** {job.salary}")
    emp_type = getattr(job, "employment_type", "")
    type_str = f" | {emp_type}" if emp_type else ""
    lines.append(f"- **Location:** {job.location} | {job.arrangement}{type_str}")
    lines.append(f"- **Stack match:** {skill['ratio']} — matched: {', '.join(skill['matched_core']) if skill['matched_core'] else 'none'}")
    if skill.get("matched_secondary"):
        lines.append(f"- **Secondary skills:** {', '.join(skill['matched_secondary'])}")
    title_rel = components.get("title_relevance", {})
    if title_rel:
        lines.append(f"- **Title match:** {title_rel.get('reason', 'N/A')}")
    lines.append(f"- **Seniority:** {components['seniority']['reason']}")
    lines.append(f"- **Response likelihood:** {response['likelihood']} — {response['reason']}")

    # Compensation note
    if components.get("comp_note"):
        lines.append(f"- **Comp warning:** {components['comp_note']}")

    # Parse confidence note
    if components.get("parse_note"):
        lines.append(f"- **Note:** {components['parse_note']}")

    if job.apply_info:
        lines.append(f"- **Apply:** {job.apply_info}")
    if job.url:
        lines.append(f"- **Link:** [{job.source}]({job.url})")

    # Talking points from profile highlights matched to this job
    highlights = profile.get("highlights", [])
    matched_core = skill.get("matched_core", [])
    if highlights and matched_core:
        relevant = _match_highlights(highlights, matched_core, job)
        if relevant:
            lines.append(f"- **Talking points:**")
            for h in relevant:
                lines.append(f"  - {h}")

    lines.append("")


def _match_highlights(highlights: list[str], matched_skills: list[str], job) -> list[str]:
    """Find profile highlights relevant to this job's matched skills."""
    relevant = []
    searchable = (job.title + " " + job.description).lower()
    for h in highlights:
        h_lower = h.lower()
        # Check if the highlight mentions any matched skill or job keyword
        if any(s.lower() in h_lower for s in matched_skills):
            relevant.append(h)
        elif any(w in h_lower for w in searchable.split()[:20] if len(w) > 4):
            relevant.append(h)
    return relevant[:3]  # max 3 talking points


def _score_tier(score: float) -> str:
    """Return CSS tier class suffix based on score value."""
    if score >= 4.0:
        return "strong"
    elif score >= 3.5:
        return "rec"
    else:
        return "review"


def _tier_icon_class(tier: str) -> str:
    """Return CSS class for tier Unicode icon indicator."""
    return f"tier-icon tier-icon-{tier}"


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
) -> None:
    """Generate an HTML report with Bootstrap 5.3 styling."""
    # Import tracker locally to avoid circular dependency
    from . import tracker

    name = html.escape(profile["name"])
    today = date.today().isoformat()

    # Filter results
    scored_results = [r for r in scored_results if r["score"]["overall"] >= min_score]
    total = len(scored_results)
    hero_jobs = [r for r in scored_results if r["score"]["overall"] >= 4.0]
    recommended = [r for r in scored_results if 3.5 <= r["score"]["overall"] < 4.0]
    new_count = sum(1 for r in scored_results if r.get("is_new", True))

    # Load application statuses for embedding
    import json as json_module
    all_statuses = tracker.get_all_application_statuses()
    embedded_status_json = json_module.dumps(all_statuses, indent=2)

    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en" data-bs-theme="auto">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>Job Search Results — {name}</title>

  <!-- Bootstrap 5.3 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

  <!-- Notyf toast notifications -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css">

  <!-- Prism.js syntax highlighting -->
  <link href="https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism.css" rel="stylesheet">

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
      .no-print {{ display: none !important; }}
      body {{ background: white !important; }}
      .card {{ border: 1px solid #ddd !important; }}
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
        padding: 1rem;
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
        grid-template-columns: 7em 1fr;
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
    </div>
  </header>

  <main id="main-content" role="main">
    <div class="container">
      {_html_profile_section(profile)}

      {_html_hero_section(hero_jobs, profile)}

      {'<div class="section-divider" role="separator" aria-hidden="true"></div>' if hero_jobs and recommended else ''}

      {_html_recommended_section(recommended, profile)}

      {_html_results_table(scored_results)}

      {_html_manual_urls_section(manual_urls)}

      <div id="status-announcer" role="status" aria-live="polite" aria-atomic="true" class="visually-hidden"></div>
    </div>
  </main>

  <footer role="contentinfo">
    <div class="container my-4">
      <p class="text-muted text-center mb-0">Generated by Job Radar on {today}</p>
    </div>
  </footer>

  <!-- Bootstrap JS bundle -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

  <!-- Notyf toast notifications -->
  <script src="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js"></script>

  <!-- Prism.js for syntax highlighting -->
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-core.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/plugins/autoloader/prism-autoloader.min.js"></script>

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

    // Keyboard shortcuts: C = copy focused, A = copy all recommended
    document.addEventListener('keydown', function(event) {{
      // Don't interfere with form inputs
      if (event.target.matches('input, textarea, select')) return;
      // Don't interfere with browser shortcuts (Ctrl+C, Ctrl+A, etc.)
      if (event.ctrlKey || event.metaKey || event.altKey) return;

      var key = event.key.toLowerCase();

      if (key === 'c') {{
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
      hideOffer: false
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

        // Determine if job should be hidden
        var shouldHide = false;
        if (jobStatus === 'applied' && filterState.hideApplied) {{
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

      // Derive state key from checkbox id (filter-applied -> hideApplied)
      var stateKey = 'hide' + checkboxId.replace('filter-', '').charAt(0).toUpperCase() +
                     checkboxId.replace('filter-', '').slice(1);

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
      saveFilterState();

      // Update checkbox UI
      document.getElementById('filter-applied').checked = false;
      document.getElementById('filter-rejected').checked = false;
      document.getElementById('filter-interviewing').checked = false;
      document.getElementById('filter-offer').checked = false;

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

      // Attach event listeners
      document.getElementById('filter-applied').addEventListener('change', handleFilterChange);
      document.getElementById('filter-rejected').addEventListener('change', handleFilterChange);
      document.getElementById('filter-interviewing').addEventListener('change', handleFilterChange);
      document.getElementById('filter-offer').addEventListener('change', handleFilterChange);
      document.getElementById('clear-filters').addEventListener('click', clearAllFilters);

      // Apply persisted filter state
      applyFilter();
    }}

    // Initialize filters after status hydration
    document.addEventListener('DOMContentLoaded', function() {{
      initializeFilters();
    }});

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
      if (/^[=+\-@]/.test(str)) {{
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
        var scoreMatch = scoreText.match(/(\d+\.\d+)/);
        data.push(scoreMatch ? scoreMatch[1] : scoreText);

        // NEW badge (cell 2)
        var newText = cells[2] ? cells[2].textContent.trim() : '';
        data.push(newText === 'NEW' ? 'Yes' : 'No');

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


def _html_tracker_stats(tracker_stats: dict) -> str:
    """Generate HTML for tracker statistics."""
    return f"""
    <div class="alert alert-secondary">
      <strong>Lifetime stats:</strong> {tracker_stats['total_unique_jobs_seen']} unique jobs seen
      across {tracker_stats['total_runs']} runs |
      Avg {tracker_stats['avg_new_per_run_last_7']} new/run (last 7)
    </div>
    """


def _html_profile_section(profile: dict) -> str:
    """Generate HTML for candidate profile summary."""
    name = html.escape(profile.get("name", "N/A"))
    level = html.escape(profile.get("level", "N/A"))
    years = profile.get("years_experience", "N/A")
    target_titles = html.escape(", ".join(profile.get("target_titles", []))) or "N/A"
    core_skills = html.escape(", ".join(profile.get("core_skills", []))) or "N/A"
    location = html.escape(profile.get("location", "N/A"))
    arrangement = html.escape(", ".join(profile.get("arrangement", []))) or "N/A"
    target_market = html.escape(profile.get("target_market", "N/A"))

    cert_row = ""
    if profile.get("certifications"):
        certs = html.escape(", ".join(profile["certifications"]))
        cert_row = f"<li><strong>Certifications:</strong> {certs}</li>"

    comp_row = ""
    if profile.get("comp_floor"):
        comp_floor = profile["comp_floor"]
        comp_row = f"<li><strong>Comp floor:</strong> ${comp_floor:,.0f}</li>"

    dealbreaker_row = ""
    if profile.get("dealbreakers"):
        dealbreakers = html.escape(", ".join(profile["dealbreakers"]))
        dealbreaker_row = f"<li><strong>Dealbreakers:</strong> {dealbreakers}</li>"

    return f"""
    <section aria-labelledby="profile-heading">
      <div class="card mb-4">
        <div class="card-header">
          <h2 id="profile-heading" class="h4 mb-0">Candidate Profile Summary</h2>
        </div>
        <div class="card-body">
          <ul class="list-unstyled mb-0">
            <li><strong>Level:</strong> {level}</li>
            <li><strong>Experience:</strong> {years} years</li>
            <li><strong>Target titles:</strong> {target_titles}</li>
            <li><strong>Core skills:</strong> {core_skills}</li>
            <li><strong>Location:</strong> {location}</li>
            <li><strong>Arrangement:</strong> {arrangement}</li>
            <li><strong>Target market:</strong> {target_market}</li>
            {cert_row}
            {comp_row}
            {dealbreaker_row}
          </ul>
        </div>
      </div>
    </section>
    """


def _html_hero_section(hero_jobs: list[dict], profile: dict) -> str:
    """Generate HTML for hero jobs section (score >= 4.0)."""
    if not hero_jobs:
        return ""

    cards = []
    for i, r in enumerate(hero_jobs, 1):
        job = r["job"]
        score = r["score"]
        components = score["components"]
        skill = components["skill_match"]
        response = components["response"]
        is_new = r.get("is_new", True)
        new_tag = ' <span class="badge bg-primary"><span class="visually-hidden">New listing, not seen in previous searches. </span>NEW</span>' if is_new else ""

        # Hero jobs are always tier-strong (score >= 4.0)
        tier = "strong"
        score_val = score["overall"]

        # Build details list
        details = []
        details.append(f"<li><strong>Posted:</strong> {html.escape(job.date_posted)}</li>")
        details.append(f"<li><strong>Rate/Salary:</strong> {html.escape(job.salary)}</li>")

        emp_type = getattr(job, "employment_type", "")
        type_str = f" | {html.escape(emp_type)}" if emp_type else ""
        details.append(f"<li><strong>Location:</strong> {html.escape(job.location)} | {html.escape(job.arrangement)}{type_str}</li>")

        matched_core = ", ".join(skill["matched_core"]) if skill["matched_core"] else "none"
        details.append(f"<li><strong>Stack match:</strong> {html.escape(skill['ratio'])} — matched: {html.escape(matched_core)}</li>")

        if skill.get("matched_secondary"):
            matched_sec = ", ".join(skill["matched_secondary"])
            details.append(f"<li><strong>Secondary skills:</strong> {html.escape(matched_sec)}</li>")

        title_rel = components.get("title_relevance", {})
        if title_rel:
            details.append(f"<li><strong>Title match:</strong> {html.escape(title_rel.get('reason', 'N/A'))}</li>")

        details.append(f"<li><strong>Seniority:</strong> {html.escape(components['seniority']['reason'])}</li>")
        details.append(f"<li><strong>Response likelihood:</strong> {html.escape(response['likelihood'])} — {html.escape(response['reason'])}</li>")

        if components.get("comp_note"):
            details.append(f"<li><strong>Comp warning:</strong> {html.escape(components['comp_note'])}</li>")

        if components.get("parse_note"):
            details.append(f"<li><strong>Note:</strong> {html.escape(components['parse_note'])}</li>")

        if job.apply_info:
            details.append(f"<li><strong>Apply:</strong> {html.escape(job.apply_info)}</li>")

        if job.url:
            source_aria_label = f"View on {job.source}, opens in new tab"
            details.append(f'<li><strong>Link:</strong> <a href="{html.escape(job.url)}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-primary" aria-label="{html.escape(source_aria_label)}">{html.escape(job.source)}</a></li>')
            details.append(f'<li><button class="btn btn-sm btn-outline-secondary copy-btn" onclick="copySingleUrl(this)" data-url="{html.escape(job.url)}">Copy URL</button></li>')

        # Talking points
        highlights = profile.get("highlights", [])
        matched_core_list = skill.get("matched_core", [])
        if highlights and matched_core_list:
            relevant = _match_highlights(highlights, matched_core_list, job)
            if relevant:
                talking_points = "".join(f"<li>{html.escape(h)}</li>" for h in relevant)
                details.append(f"<li><strong>Talking points:</strong><ul>{talking_points}</ul></li>")

        details_html = "".join(details)

        # Generate job key for status tracking
        job_key_val = f"{job.title.lower().strip()}||{job.company.lower().strip()}"

        # Add data attributes (hero-job class IN ADDITION to tier-strong)
        data_attrs = ""
        if job.url:
            data_attrs = f'class="card mb-3 job-item hero-job tier-{tier}" tabindex="0" data-job-url="{html.escape(job.url)}" data-score="{score_val:.1f}" data-job-key="{html.escape(job_key_val)}" data-job-title="{html.escape(job.title)}" data-job-company="{html.escape(job.company)}"'
        else:
            data_attrs = f'class="card mb-3 hero-job tier-{tier}" data-job-key="{html.escape(job_key_val)}" data-job-title="{html.escape(job.title)}" data-job-company="{html.escape(job.company)}"'

        # Status dropdown HTML
        status_dropdown = f"""
          <div class="dropdown d-inline-block ms-2">
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

        # Score badge with "Top Match" label
        tier_icon_html = f'<span class="{_tier_icon_class(tier)}" aria-hidden="true"></span>'
        score_badge_html = f'{tier_icon_html}<span class="badge rounded-pill score-badge tier-badge-{tier}"><span class="visually-hidden">Score </span>{score_val:.1f}<span class="visually-hidden"> out of 5.0, </span><span class="badge-label">Top Match</span></span>'

        card = f"""
        <div {data_attrs}>
          <div class="card-header">
            <h3 class="h5 mb-0">
              {i}. {html.escape(job.title)} — {html.escape(job.company)}
              {score_badge_html}{new_tag}
              {status_dropdown}
            </h3>
          </div>
          <div class="card-body">
            <ul class="mb-0">
              {details_html}
            </ul>
          </div>
        </div>
        """
        cards.append(card)

    cards_html = "".join(cards)

    # Copy All button for hero section
    copy_all_button = f"""
    <div class="d-flex align-items-center mb-3">
      <button class="btn btn-primary copy-all-btn" onclick="copyAllHeroUrls(this)">
        Copy All Top Match URLs
      </button>
      <span class="shortcut-hint ms-2">Keyboard: <kbd>C</kbd> = copy focused, <kbd>A</kbd> = copy all</span>
    </div>
    """

    return f"""
    <section aria-labelledby="hero-heading" class="hero-jobs-section">
      <div class="mb-4">
        <h2 id="hero-heading" class="h4 mb-3">Top Matches (Score >= 4.0)</h2>
        <p class="text-muted mb-4">These jobs are excellent matches for your profile.</p>
        {copy_all_button}
        {cards_html}
      </div>
    </section>
    """


def _html_recommended_section(recommended: list[dict], profile: dict) -> str:
    """Generate HTML for recommended roles section."""
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

    cards = []
    for i, r in enumerate(recommended, 1):
        job = r["job"]
        score = r["score"]
        components = score["components"]
        skill = components["skill_match"]
        response = components["response"]
        is_new = r.get("is_new", True)
        new_tag = ' <span class="badge bg-primary"><span class="visually-hidden">New listing, not seen in previous searches. </span>NEW</span>' if is_new else ""

        # Determine tier based on score
        score_val = score["overall"]
        tier = _score_tier(score_val)

        # Build details list
        details = []
        details.append(f"<li><strong>Posted:</strong> {html.escape(job.date_posted)}</li>")
        details.append(f"<li><strong>Rate/Salary:</strong> {html.escape(job.salary)}</li>")

        emp_type = getattr(job, "employment_type", "")
        type_str = f" | {html.escape(emp_type)}" if emp_type else ""
        details.append(f"<li><strong>Location:</strong> {html.escape(job.location)} | {html.escape(job.arrangement)}{type_str}</li>")

        matched_core = ", ".join(skill["matched_core"]) if skill["matched_core"] else "none"
        details.append(f"<li><strong>Stack match:</strong> {html.escape(skill['ratio'])} — matched: {html.escape(matched_core)}</li>")

        if skill.get("matched_secondary"):
            matched_sec = ", ".join(skill["matched_secondary"])
            details.append(f"<li><strong>Secondary skills:</strong> {html.escape(matched_sec)}</li>")

        title_rel = components.get("title_relevance", {})
        if title_rel:
            details.append(f"<li><strong>Title match:</strong> {html.escape(title_rel.get('reason', 'N/A'))}</li>")

        details.append(f"<li><strong>Seniority:</strong> {html.escape(components['seniority']['reason'])}</li>")
        details.append(f"<li><strong>Response likelihood:</strong> {html.escape(response['likelihood'])} — {html.escape(response['reason'])}</li>")

        if components.get("comp_note"):
            details.append(f"<li><strong>Comp warning:</strong> {html.escape(components['comp_note'])}</li>")

        if components.get("parse_note"):
            details.append(f"<li><strong>Note:</strong> {html.escape(components['parse_note'])}</li>")

        if job.apply_info:
            details.append(f"<li><strong>Apply:</strong> {html.escape(job.apply_info)}</li>")

        if job.url:
            source_aria_label = f"View on {job.source}, opens in new tab"
            details.append(f'<li><strong>Link:</strong> <a href="{html.escape(job.url)}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-primary" aria-label="{html.escape(source_aria_label)}">{html.escape(job.source)}</a></li>')
            details.append(f'<li><button class="btn btn-sm btn-outline-secondary copy-btn" onclick="copySingleUrl(this)" data-url="{html.escape(job.url)}">Copy URL</button></li>')

        # Talking points
        highlights = profile.get("highlights", [])
        matched_core_list = skill.get("matched_core", [])
        if highlights and matched_core_list:
            relevant = _match_highlights(highlights, matched_core_list, job)
            if relevant:
                talking_points = "".join(f"<li>{html.escape(h)}</li>" for h in relevant)
                details.append(f"<li><strong>Talking points:</strong><ul>{talking_points}</ul></li>")

        details_html = "".join(details)

        # Generate job key for status tracking (matches tracker.job_key format)
        job_key_val = f"{job.title.lower().strip()}||{job.company.lower().strip()}"

        # Add data attributes for clipboard and status tracking functionality
        data_attrs = ""
        if job.url:
            data_attrs = f'class="card mb-3 job-item tier-{tier}" tabindex="0" data-job-url="{html.escape(job.url)}" data-score="{score_val:.1f}" data-job-key="{html.escape(job_key_val)}" data-job-title="{html.escape(job.title)}" data-job-company="{html.escape(job.company)}"'
        else:
            data_attrs = f'class="card mb-3 tier-{tier}" data-job-key="{html.escape(job_key_val)}" data-job-title="{html.escape(job.title)}" data-job-company="{html.escape(job.company)}"'

        # Status dropdown HTML
        status_dropdown = f"""
          <div class="dropdown d-inline-block ms-2">
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

        # Score badge with screen reader context and tier icon
        tier_icon_html = f'<span class="{_tier_icon_class(tier)}" aria-hidden="true"></span>'
        score_badge_html = f'{tier_icon_html}<span class="badge rounded-pill score-badge tier-badge-{tier}"><span class="visually-hidden">Score </span>{score_val:.1f}<span class="visually-hidden"> out of 5.0</span></span>'

        card = f"""
        <div {data_attrs}>
          <div class="card-header">
            <h3 class="h5 mb-0">
              {i}. {html.escape(job.title)} — {html.escape(job.company)}
              {score_badge_html}{new_tag}
              {status_dropdown}
            </h3>
          </div>
          <div class="card-body">
            <ul class="mb-0">
              {details_html}
            </ul>
          </div>
        </div>
        """
        cards.append(card)

    cards_html = "".join(cards)

    # Add Copy All button with keyboard hint and Export Status button
    copy_all_button = f"""
    <div class="d-flex align-items-center mb-3">
      <button class="btn btn-primary copy-all-btn" onclick="copyAllRecommendedUrls(this)">
        Copy All Recommended URLs
      </button>
      <button class="btn btn-sm btn-outline-info export-status-btn no-print"
              onclick="exportPendingStatusUpdates()">
        Export Status Updates
      </button>
      <span class="shortcut-hint ms-2">Keyboard: <kbd>C</kbd> = copy focused, <kbd>A</kbd> = copy all</span>
    </div>
    """

    return f"""
    <section aria-labelledby="recommended-heading">
      <div class="mb-4">
        <h2 id="recommended-heading" class="h4 mb-3">Recommended Roles (Score 3.5 - 3.9)</h2>
        {copy_all_button}
        {cards_html}
      </div>
    </section>
    """


def _html_results_table(scored_results: list[dict]) -> str:
    """Generate HTML for all results table."""
    if not scored_results:
        return """
        <section aria-labelledby="results-heading">
          <div class="mb-4">
            <h2 id="results-heading" class="h4 mb-3">All Results (sorted by score)</h2>
            <p class="text-muted"><em>No results found.</em></p>
          </div>
        </section>
        """

    rows = []
    for i, r in enumerate(scored_results, 1):
        job = r["job"]
        score = r["score"]["overall"]
        rec = r["score"]["recommendation"]
        is_new = r.get("is_new", True)
        new_badge = '<span class="badge bg-primary rounded-pill">NEW</span>' if is_new else ''

        # Determine tier based on score
        tier = _score_tier(score)

        salary = html.escape(job.salary) if job.salary != "Not listed" else "—"
        emp_type = getattr(job, "employment_type", "") or job.arrangement
        snippet = _make_snippet(job.description, 80)

        # Generate job key for status tracking
        job_key_val = f"{job.title.lower().strip()}||{job.company.lower().strip()}"

        # Build link and copy button with accessibility attributes
        if job.url:
            view_aria_label = f"View {job.title} at {job.company}, opens in new tab"
            link_html = f'<a href="{html.escape(job.url)}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-primary" aria-label="{html.escape(view_aria_label)}">View</a> <button class="btn btn-sm btn-outline-secondary copy-btn" onclick="copySingleUrl(this)" data-url="{html.escape(job.url)}">Copy</button>'
            row_attrs = f'class="job-item tier-{tier}" tabindex="0" data-job-url="{html.escape(job.url)}" data-score="{score:.1f}" data-job-key="{html.escape(job_key_val)}" data-job-title="{html.escape(job.title)}" data-job-company="{html.escape(job.company)}"'
        else:
            link_html = html.escape(job.source)
            row_attrs = f'class="tier-{tier}" data-job-key="{html.escape(job_key_val)}" data-job-title="{html.escape(job.title)}" data-job-company="{html.escape(job.company)}"'

        # Status dropdown (compact version for table)
        status_dropdown = f"""
          <div class="dropdown d-inline-block">
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

        # Update NEW badge with screen reader context
        new_badge_accessible = '<span class="badge bg-primary rounded-pill"><span class="visually-hidden">New listing, not seen in previous searches. </span>NEW</span>' if is_new else ''

        # Update score badge with screen reader context and tier icon
        tier_icon_html = f'<span class="{_tier_icon_class(tier)}" aria-hidden="true"></span>'
        score_badge_accessible = f'{tier_icon_html}<span class="badge rounded-pill score-badge tier-badge-{tier}"><span class="visually-hidden">Score </span>{score:.1f}<span class="visually-hidden"> out of 5.0</span></span>'

        rows.append(f"""
        <tr {row_attrs}>
          <th scope="row" data-label="#">{i}</th>
          <td data-label="Score">{score_badge_accessible}<br><small class="text-muted">({html.escape(rec)})</small></td>
          <td data-label="New" class="col-new">{new_badge_accessible}</td>
          <td data-label="Status">{status_dropdown}</td>
          <td data-label="Title"><strong>{html.escape(job.title)}</strong></td>
          <td data-label="Company">{html.escape(job.company)}</td>
          <td data-label="Salary" class="col-salary">{salary}</td>
          <td data-label="Type" class="col-type">{html.escape(emp_type)}</td>
          <td data-label="Location">{html.escape(job.location)}</td>
          <td data-label="Snippet" class="col-snippet">{html.escape(snippet)}</td>
          <td data-label="Link" class="no-label">{link_html}</td>
        </tr>
        """)

    rows_html = "".join(rows)

    # Filter controls HTML
    filter_controls = """
    <div class="mb-4 no-print" role="region" aria-labelledby="filter-heading">
      <h3 id="filter-heading" class="h5">Filter by Status</h3>
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <div class="btn-group" role="group" aria-label="Status filter checkboxes">
          <input type="checkbox" class="btn-check" id="filter-applied" autocomplete="off">
          <label class="btn btn-outline-secondary btn-sm" for="filter-applied">Hide Applied</label>

          <input type="checkbox" class="btn-check" id="filter-rejected" autocomplete="off">
          <label class="btn btn-outline-secondary btn-sm" for="filter-rejected">Hide Rejected</label>

          <input type="checkbox" class="btn-check" id="filter-interviewing" autocomplete="off">
          <label class="btn btn-outline-secondary btn-sm" for="filter-interviewing">Hide Interviewing</label>

          <input type="checkbox" class="btn-check" id="filter-offer" autocomplete="off">
          <label class="btn btn-outline-secondary btn-sm" for="filter-offer">Hide Offer</label>
        </div>

        <button class="btn btn-outline-primary btn-sm" id="clear-filters" aria-label="Clear all filters and show all jobs">Show All</button>

        <button class="btn btn-outline-success btn-sm no-print" id="export-csv-btn" onclick="exportVisibleJobsToCSV()" aria-label="Export visible jobs to CSV file">Export CSV</button>

        <span id="filter-count" class="text-muted small ms-2" aria-hidden="true"></span>
      </div>
      <p class="text-muted small mt-2 mb-0">Filter applies to jobs with status set. Unset jobs are always visible.</p>
    </div>
    """

    return f"""
    <section aria-labelledby="results-heading">
      <div class="mb-4">
        {filter_controls}
        <h2 id="results-heading" class="h4 mb-3">All Results (sorted by score)</h2>
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <caption class="visually-hidden">Job search results sorted by relevance score, highest first</caption>
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Score</th>
                <th scope="col" class="col-new">New</th>
                <th scope="col">Status</th>
                <th scope="col">Title</th>
                <th scope="col">Company</th>
                <th scope="col" class="col-salary">Salary</th>
                <th scope="col" class="col-type">Type</th>
                <th scope="col">Location</th>
                <th scope="col" class="col-snippet">Snippet</th>
                <th scope="col">Link</th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>
        </div>
      </div>
    </section>
    """


def _html_manual_urls_section(manual_urls: list[dict]) -> str:
    """Generate HTML for manual check URLs section."""
    if not manual_urls:
        return ""

    groups = {}
    for u in manual_urls:
        source = u["source"]
        if source not in groups:
            groups[source] = []
        groups[source].append(u)

    sections = []
    for source, urls in groups.items():
        links = []
        for u in urls:
            links.append(f'<li>{html.escape(u["title"])}: <a href="{html.escape(u["url"])}" target="_blank" rel="noopener" aria-label="{html.escape(u["title"])} on {html.escape(u["source"])}, opens in new tab">{html.escape(u["source"])} Search</a></li>')
        links_html = "".join(links)
        sections.append(f"""
        <div class="mb-3">
          <h4 class="h6"><strong>{html.escape(source)}:</strong></h4>
          <ul>
            {links_html}
          </ul>
        </div>
        """)

    sections_html = "".join(sections)
    return f"""
    <section aria-labelledby="manual-heading">
      <div class="card mb-4">
        <div class="card-header">
          <h2 id="manual-heading" class="h4 mb-0">Manual Check URLs</h2>
        </div>
        <div class="card-body">
          <p class="text-muted"><em>Open these in your browser to check sources that block automated access.</em></p>
          {sections_html}
        </div>
      </div>
    </section>
    """
