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
    name = html.escape(profile["name"])
    today = date.today().isoformat()

    # Filter results
    scored_results = [r for r in scored_results if r["score"]["overall"] >= min_score]
    total = len(scored_results)
    recommended = [r for r in scored_results if r["score"]["overall"] >= 3.5]
    new_count = sum(1 for r in scored_results if r.get("is_new", True))

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

  <!-- Prism.js syntax highlighting -->
  <link href="https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism.css" rel="stylesheet">

  <style>
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

    /* Score badge sizing */
    .score-badge {{
      font-size: 1rem;
      padding: 0.5em 0.75em;
    }}
  </style>
</head>
<body>
  <div class="container my-4">
    <h1 class="mb-3">Job Search Results — {name}</h1>

    <div class="alert alert-info">
      <strong>Date:</strong> {today}<br>
      <strong>Sources searched:</strong> {html.escape(', '.join(sources_searched))}<br>
      <strong>Date filter:</strong> {html.escape(from_date)} to {html.escape(to_date)}<br>
      <strong>Total results:</strong> {total} ({new_count} new)<br>
      <strong>Above threshold (3.5+):</strong> {len(recommended)}
    </div>

    {_html_tracker_stats(tracker_stats) if tracker_stats else ''}

    {_html_profile_section(profile)}

    {_html_recommended_section(recommended, profile)}

    {_html_results_table(scored_results)}

    {_html_manual_urls_section(manual_urls)}
  </div>

  <!-- Bootstrap JS bundle -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

  <!-- Prism.js for syntax highlighting -->
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-core.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/prismjs@1/plugins/autoloader/prism-autoloader.min.js"></script>

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
    <div class="card mb-4">
      <div class="card-header">
        <h2 class="h4 mb-0">Candidate Profile Summary</h2>
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
    """


def _html_recommended_section(recommended: list[dict], profile: dict) -> str:
    """Generate HTML for recommended roles section."""
    if not recommended:
        return """
        <div class="card mb-4">
          <div class="card-header">
            <h2 class="h4 mb-0">Recommended Roles (Score >= 3.5)</h2>
          </div>
          <div class="card-body">
            <p class="text-muted mb-0"><em>No results scored 3.5 or above in this search run.</em></p>
          </div>
        </div>
        """

    cards = []
    for i, r in enumerate(recommended, 1):
        job = r["job"]
        score = r["score"]
        components = score["components"]
        skill = components["skill_match"]
        response = components["response"]
        is_new = r.get("is_new", True)
        new_tag = ' <span class="badge bg-primary">NEW</span>' if is_new else ""

        # Determine score badge color
        score_val = score["overall"]
        if score_val >= 4.0:
            badge_class = "bg-success"
        elif score_val >= 3.5:
            badge_class = "bg-warning"
        else:
            badge_class = "bg-secondary"

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
            details.append(f'<li><strong>Link:</strong> <a href="{html.escape(job.url)}" target="_blank" class="btn btn-sm btn-outline-primary">{html.escape(job.source)}</a></li>')

        # Talking points
        highlights = profile.get("highlights", [])
        matched_core_list = skill.get("matched_core", [])
        if highlights and matched_core_list:
            relevant = _match_highlights(highlights, matched_core_list, job)
            if relevant:
                talking_points = "".join(f"<li>{html.escape(h)}</li>" for h in relevant)
                details.append(f"<li><strong>Talking points:</strong><ul>{talking_points}</ul></li>")

        details_html = "".join(details)

        card = f"""
        <div class="card mb-3">
          <div class="card-header">
            <h3 class="h5 mb-0">
              {i}. {html.escape(job.title)} — {html.escape(job.company)}
              <span class="badge {badge_class} score-badge">{score_val:.1f}/5.0</span>{new_tag}
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
    return f"""
    <div class="mb-4">
      <h2 class="h4 mb-3">Recommended Roles (Score >= 3.5)</h2>
      {cards_html}
    </div>
    """


def _html_results_table(scored_results: list[dict]) -> str:
    """Generate HTML for all results table."""
    if not scored_results:
        return """
        <div class="mb-4">
          <h2 class="h4 mb-3">All Results (sorted by score)</h2>
          <p class="text-muted"><em>No results found.</em></p>
        </div>
        """

    rows = []
    for i, r in enumerate(scored_results, 1):
        job = r["job"]
        score = r["score"]["overall"]
        rec = r["score"]["recommendation"]
        is_new = r.get("is_new", True)
        new_badge = '<span class="badge bg-primary rounded-pill">NEW</span>' if is_new else ''

        # Badge color based on score
        if score >= 4.0:
            badge_class = "bg-success"
        elif score >= 3.5:
            badge_class = "bg-warning"
        else:
            badge_class = "bg-secondary"

        salary = html.escape(job.salary) if job.salary != "Not listed" else "—"
        emp_type = getattr(job, "employment_type", "") or job.arrangement
        snippet = _make_snippet(job.description, 80)

        link_html = f'<a href="{html.escape(job.url)}" target="_blank" class="btn btn-sm btn-outline-primary">View</a>' if job.url else html.escape(job.source)

        rows.append(f"""
        <tr>
          <td>{i}</td>
          <td><span class="badge {badge_class}">{score:.1f}/5.0</span><br><small class="text-muted">({html.escape(rec)})</small></td>
          <td>{new_badge}</td>
          <td><strong>{html.escape(job.title)}</strong></td>
          <td>{html.escape(job.company)}</td>
          <td>{salary}</td>
          <td>{html.escape(emp_type)}</td>
          <td>{html.escape(job.location)}</td>
          <td>{html.escape(snippet)}</td>
          <td>{link_html}</td>
        </tr>
        """)

    rows_html = "".join(rows)
    return f"""
    <div class="mb-4">
      <h2 class="h4 mb-3">All Results (sorted by score)</h2>
      <div class="table-responsive">
        <table class="table table-striped table-hover">
          <thead>
            <tr>
              <th>#</th>
              <th>Score</th>
              <th>New</th>
              <th>Title</th>
              <th>Company</th>
              <th>Salary</th>
              <th>Type</th>
              <th>Location</th>
              <th>Snippet</th>
              <th>Link</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>
    </div>
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
            links.append(f'<li>{html.escape(u["title"])}: <a href="{html.escape(u["url"])}" target="_blank">{html.escape(u["source"])} Search</a></li>')
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
    <div class="card mb-4">
      <div class="card-header">
        <h2 class="h4 mb-0">Manual Check URLs</h2>
      </div>
      <div class="card-body">
        <p class="text-muted"><em>Open these in your browser to check sources that block automated access.</em></p>
        {sections_html}
      </div>
    </div>
    """
