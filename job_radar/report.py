"""Markdown report generator for job search results."""

import logging
import os
from datetime import date

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
) -> str:
    """Generate a Markdown report for a candidate's search results.

    Args:
        profile: Candidate profile dict
        scored_results: List of {"job": JobResult, "score": score_dict} sorted by score
        manual_urls: List of manual-check URL dicts
        sources_searched: List of source names
        from_date: Search start date
        to_date: Search end date
        output_dir: Directory to write report to
        tracker_stats: Cross-run statistics dict from tracker module

    Returns:
        Path to the generated report file.
    """
    name = profile["name"]
    today = date.today().isoformat()
    safe_name = name.lower().replace(" ", "_")
    filename = f"{safe_name}_{today}.md"
    filepath = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)

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
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


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
