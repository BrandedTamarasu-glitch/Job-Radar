"""Formatting helpers for GUI search completion summaries."""

from __future__ import annotations

from job_radar.report import ZERO_RESULTS_TIPS


def completion_message(job_count: int) -> str:
    """Return the primary GUI completion message for a search."""
    if job_count == 0:
        return "Search complete. No matching jobs found."
    noun = "job" if job_count == 1 else "jobs"
    return f"Search complete! {job_count} {noun} found"


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


def zero_result_lines(job_count: int) -> list[str]:
    """Return next-action guidance for an empty search result."""
    if job_count != 0:
        return []
    return list(ZERO_RESULTS_TIPS)


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
