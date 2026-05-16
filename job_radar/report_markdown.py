"""Markdown section rendering for generated reports."""

from __future__ import annotations

from .report_filtering import filter_explanation_text
from .report_matching import match_highlights, skill_callout_groups
from .report_results import ZERO_RESULTS_TIPS
from .report_safety import safe_external_url
from .report_text import make_snippet, markdown_cell


def append_manual_urls_section(lines: list[str], manual_urls: list[dict]) -> None:
    """Append grouped manual-check URLs to a Markdown report."""
    lines.append("## Manual Check URLs")
    lines.append("_Open these in your browser to check sources that block automated access._")
    lines.append("")
    current_source = None
    for manual_url in manual_urls:
        if manual_url["source"] != current_source:
            current_source = manual_url["source"]
            lines.append(f"**{current_source}:**")
        safe_url = safe_external_url(manual_url.get("url"))
        if safe_url:
            lines.append(f"- {manual_url['title']}: [{manual_url['source']} Search]({safe_url})")
        else:
            lines.append(f"- {manual_url['title']}: {manual_url['source']} Search URL unavailable")
    lines.append("")


def append_all_results_table(lines: list[str], scored_results: list[dict]) -> None:
    """Append the Markdown all-results table or empty-state guidance."""
    lines.append("## All Results (sorted by score)")
    lines.append("")
    if scored_results:
        lines.append("| # | Score | New | Title | Company | Salary | Type | Location | Snippet | Link |")
        lines.append("|---|-------|-----|-------|---------|--------|------|----------|---------|------|")
        for index, result in enumerate(scored_results, 1):
            lines.append(markdown_result_row(result, index))
        lines.append("")
    else:
        lines.append("_No results found._")
        lines.append("")
        lines.append("### Try Next")
        for tip in ZERO_RESULTS_TIPS:
            lines.append(f"- {tip}")
        lines.append("")


def markdown_result_row(result: dict, index: int) -> str:
    """Return one Markdown all-results table row."""
    job = result["job"]
    score = result["score"]["overall"]
    rec = result["score"]["recommendation"]
    is_new = result.get("is_new", True)
    new_badge = "NEW" if is_new else ""
    safe_job_url = safe_external_url(job.url)
    link = f"[{job.source}]({safe_job_url})" if safe_job_url else job.source
    salary = job.salary if job.salary != "Not listed" else "—"
    emp_type = getattr(job, "employment_type", "") or job.arrangement
    snippet = make_snippet(job.description, 80)
    return (
        f"| {index} | **{score}/5.0** ({rec}) | {new_badge} | {job.title} | {job.company} "
        f"| {salary} | {emp_type} | {job.location} | {snippet} | {link} |"
    )


def markdown_filtered_out_section(filtered_out: list[dict], min_score: float) -> list[str]:
    """Return a concise Markdown section for filtered-out jobs."""
    if not filtered_out:
        return []

    lines = ["", "## Filtered Out", ""]
    lines.append("| Title | Company | Score | Why |")
    lines.append("|-------|---------|-------|-----|")
    for result in filtered_out[:10]:
        job = result["job"]
        score = result.get("score", {}).get("overall", 0.0)
        lines.append(
            f"| {markdown_cell(job.title)} | {markdown_cell(job.company)} | "
            f"{score}/5.0 | {markdown_cell(filter_explanation_text(result, min_score))} |"
        )
    if len(filtered_out) > 10:
        lines.append(f"| ... | ... | ... | {len(filtered_out) - 10} more filtered jobs omitted |")
    lines.append("")
    return lines


def append_detailed_result(lines: list[str], rank: int, result: dict, profile: dict) -> None:
    """Append a single detailed recommended-result entry."""
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
    lines.append(
        f"- **Stack match:** {skill['ratio']} — matched: "
        f"{', '.join(skill['matched_core']) if skill['matched_core'] else 'none'}"
    )
    for label, values in skill_callout_groups(skill, profile):
        lines.append(f"- **{label}:** {', '.join(values)}")
    title_rel = components.get("title_relevance", {})
    if title_rel:
        lines.append(f"- **Title match:** {title_rel.get('reason', 'N/A')}")
    lines.append(f"- **Seniority:** {components['seniority']['reason']}")
    lines.append(f"- **Response likelihood:** {response['likelihood']} — {response['reason']}")

    if components.get("comp_note"):
        lines.append(f"- **Comp warning:** {components['comp_note']}")

    if components.get("parse_note"):
        lines.append(f"- **Note:** {components['parse_note']}")

    if job.apply_info:
        lines.append(f"- **Apply:** {job.apply_info}")
    safe_job_url = safe_external_url(job.url)
    if safe_job_url:
        lines.append(f"- **Link:** [{job.source}]({safe_job_url})")
    elif job.url:
        lines.append(f"- **Link:** {job.source} URL unavailable")

    highlights = profile.get("highlights", [])
    matched_core = skill.get("matched_core", [])
    if highlights and matched_core:
        relevant = match_highlights(highlights, matched_core, job)
        if relevant:
            lines.append("- **Talking points:**")
            for highlight in relevant:
                lines.append(f"  - {highlight}")

    lines.append("")
