"""Formatting helpers for GUI search completion summaries."""

from __future__ import annotations

from job_radar.profile_readiness import assess_profile_readiness, readiness_guidance_lines
from job_radar.report import ZERO_RESULTS_TIPS


def completion_message(job_count: int) -> str:
    """Return the primary GUI completion message for a search."""
    if job_count == 0:
        return "Search complete. No matching jobs found."
    noun = "job" if job_count == 1 else "jobs"
    return f"Search complete! {job_count} {noun} found"


def completion_color(job_count: int) -> str:
    """Return the primary completion label color."""
    return "green" if job_count else "orange"


def source_warning_message(summary: dict | None) -> str | None:
    """Return a concise warning message for partial source failures."""
    if not summary:
        return None
    failures = int(summary.get("query_failures") or 0)
    if failures <= 0:
        return None

    failed_sources = summary.get("failed_sources") or []
    source_text = ", ".join(failed_sources) if failed_sources else "one or more sources"
    noun = "query" if failures == 1 else "queries"
    return (
        f"Warning: {failures} source {noun} failed across {source_text}. "
        "The report includes results from sources that completed."
    )


def source_summary_lines(summary: dict | None) -> list[str]:
    """Return per-source summary lines for the GUI completion view."""
    if not summary:
        return []

    lines: list[str] = []
    for source in summary.get("sources", []):
        name = source.get("name", "Unknown source")
        job_count = int(source.get("job_count") or 0)
        warning_count = int(source.get("warning_count") or 0)
        duration_seconds = source.get("duration_seconds")
        noun = "job" if job_count == 1 else "jobs"
        line = f"{name}: {job_count} {noun}"
        if duration_seconds is not None:
            line += f" in {_format_duration(float(duration_seconds))}"
        if warning_count:
            query_noun = "query warning" if warning_count == 1 else "query warnings"
            line += f" ({warning_count} {query_noun})"
        lines.append(line)

    return lines


def cache_summary_line(summary: dict | None) -> str | None:
    """Return a compact cache hit/miss summary for completed searches."""
    if not summary:
        return None

    cache_stats = summary.get("cache_stats") or {}
    hits = int(cache_stats.get("hits") or 0)
    misses = int(cache_stats.get("misses") or 0)
    writes = int(cache_stats.get("writes") or 0)
    disabled = int(cache_stats.get("disabled") or 0)
    if hits == 0 and misses == 0 and writes == 0 and disabled == 0:
        return None

    parts = [f"{hits} hits", f"{misses} misses"]
    if writes:
        parts.append(f"{writes} writes")
    if disabled:
        parts.append(f"{disabled} uncached requests")
    return "Cache: " + ", ".join(parts)


def source_fetching_message(source_name: str) -> str:
    """Return GUI progress text for a source fetch."""
    return f"Fetching {source_name}..."


def source_progress_count_text(current: int, total: int) -> str:
    """Return compact source progress counter text."""
    return f"Source {current} of {total}"


def source_job_count_line(source_name: str, job_count: int) -> str:
    """Return one source job-count line for the live progress log."""
    return f"{source_name}: {job_count} jobs found\n"


def search_context_lines(
    summary: dict | None,
    search_config: dict | None = None,
    limit: int = 3,
) -> list[str]:
    """Return bounded context explaining why a search may have changed."""
    lines: list[str] = []
    summary = summary or {}
    search_config = search_config or {}

    if int(summary.get("query_failures") or 0) > 0:
        lines.append("Some source queries failed, so totals may be lower than usual.")

    cache_stats = summary.get("cache_stats") or {}
    hits = int(cache_stats.get("hits") or 0)
    misses = int(cache_stats.get("misses") or 0)
    writes = int(cache_stats.get("writes") or 0)
    if hits and not misses and not writes:
        lines.append("This run was served from cache, so results may match a recent run.")
    elif misses or writes:
        lines.append("Fresh source requests ran for uncached results.")

    filter_parts = _active_filter_parts(search_config)
    if filter_parts:
        lines.append(f"Active filters: {', '.join(filter_parts)}.")

    return lines[:max(1, limit)]


def bullet_block_text(title: str, lines: list[str]) -> str | None:
    """Return titled bullet text for compact GUI labels."""
    if not lines:
        return None
    return f"{title}:\n" + "\n".join(f"- {line}" for line in lines)


def review_queue_text(lines: list[str]) -> str | None:
    """Return compact review queue summary text."""
    if not lines:
        return None
    return "Review queue: " + " | ".join(lines)


def _active_filter_parts(search_config: dict) -> list[str]:
    parts: list[str] = []
    if search_config.get("new_only"):
        parts.append("new-only")
    min_score = search_config.get("min_score")
    if min_score not in (None, "", 0):
        parts.append(f"minimum score {min_score}")
    if search_config.get("required_skills"):
        parts.append("must-have skills")
    if search_config.get("preferred_skills"):
        parts.append("nice-to-have skills")
    if search_config.get("include_companies") or search_config.get("exclude_companies"):
        parts.append("company filters")
    strictness = search_config.get("location_strictness")
    if strictness and strictness != "profile":
        parts.append(f"{str(strictness).replace('_', ' ')} location")
    selected_sources = search_config.get("selected_sources") or []
    selected_manual_sources = search_config.get("selected_manual_sources") or []
    if selected_sources or selected_manual_sources:
        parts.append("custom source selection")
    return parts


def _format_duration(seconds: float) -> str:
    """Format short source timings for compact GUI display."""
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining_seconds = int(round(seconds % 60))
    if remaining_seconds == 60:
        minutes += 1
        remaining_seconds = 0
    return f"{minutes}m {remaining_seconds:02d}s"


def zero_result_lines(job_count: int, profile: dict | None = None) -> list[str]:
    """Return next-action guidance for an empty search result."""
    if job_count != 0:
        return []

    lines: list[str] = []
    if profile:
        readiness = assess_profile_readiness(profile)
        lines.extend(readiness_guidance_lines(readiness, limit=2))

    for tip in ZERO_RESULTS_TIPS:
        if tip not in lines:
            lines.append(tip)
    return lines


def cancellation_message() -> str:
    """Return the GUI message for a cancelled search."""
    return (
        "Search cancelled. No new report was generated for this run. "
        "You can adjust settings or start a new search."
    )


def error_message(error: str) -> str:
    """Return the GUI message for a failed search."""
    detail = (error or "Unknown error").strip()
    return (
        "Search failed before a report could be generated. "
        f"Details: {detail}"
    )
