"""Source warning formatting for generated reports."""

from __future__ import annotations

import html

from .report_text import markdown_cell


def failed_source_names(source_failures: list[dict]) -> list[str]:
    """Return sorted unique source names for failure summaries."""
    names = {
        str(failure.get("source", "unknown")).strip() or "unknown"
        for failure in source_failures
    }
    return sorted(names, key=str.casefold)


def markdown_source_failures(source_failures: list[dict]) -> list[str]:
    """Format source failures for the Markdown report."""
    lines = [
        "## Source Warnings",
        "",
        "Some source queries failed, but results from other sources are still included.",
        "",
        "| Source | Query | Error |",
        "|---|---|---|",
    ]
    for failure in source_failures[:10]:
        source = markdown_cell(str(failure.get("source", "unknown")))
        query = markdown_cell(str(failure.get("query", "")) or "N/A")
        error = markdown_cell(str(failure.get("error", "")) or "No detail")
        lines.append(f"| {source} | {query} | {error} |")
    if len(source_failures) > 10:
        lines.append(f"| ... | ... | {len(source_failures) - 10} more failures omitted |")
    lines.append("")
    return lines


def markdown_source_warnings(source_warnings: list[dict]) -> list[str]:
    """Format non-fatal source warnings for the Markdown report."""
    lines = [
        "## Performance Warnings",
        "",
        "Some source queries completed slowly. Results are still included.",
        "",
        "| Source | Query | Elapsed | Threshold |",
        "|---|---|---|---|",
    ]
    for warning in source_warnings[:10]:
        source = markdown_cell(str(warning.get("source", "unknown")))
        query = markdown_cell(str(warning.get("query", "")) or "N/A")
        elapsed = warning.get("elapsed_seconds", "N/A")
        threshold = warning.get("threshold_seconds", "N/A")
        lines.append(f"| {source} | {query} | {elapsed}s | {threshold}s |")
    if len(source_warnings) > 10:
        lines.append(f"| ... | ... | ... | {len(source_warnings) - 10} more warnings omitted |")
    lines.append("")
    return lines


def html_source_failures(source_failures: list[dict]) -> str:
    """Generate HTML for partial source failure warnings."""
    failed_sources = ", ".join(html.escape(name) for name in failed_source_names(source_failures))
    rows = []
    for failure in source_failures[:10]:
        source = html.escape(str(failure.get("source", "unknown")))
        query = html.escape(str(failure.get("query", "")) or "N/A")
        error = html.escape(str(failure.get("error", "")) or "No detail")
        rows.append(f"<li><strong>{source}</strong>: {query} - {error}</li>")

    omitted = ""
    if len(source_failures) > 10:
        omitted = f"<li>{len(source_failures) - 10} more failures omitted</li>"

    return f"""
    <div class="alert alert-warning" role="status">
      <strong>Source warnings:</strong> {len(source_failures)} query failures across {failed_sources}.
      Results from other sources are still included.
      <ul class="mb-0 mt-2">
        {''.join(rows)}
        {omitted}
      </ul>
    </div>
    """


def html_source_warnings(source_warnings: list[dict]) -> str:
    """Generate HTML for non-fatal source performance warnings."""
    warning_sources = ", ".join(html.escape(name) for name in failed_source_names(source_warnings))
    rows = []
    for warning in source_warnings[:10]:
        source = html.escape(str(warning.get("source", "unknown")))
        query = html.escape(str(warning.get("query", "")) or "N/A")
        elapsed = html.escape(str(warning.get("elapsed_seconds", "N/A")))
        threshold = html.escape(str(warning.get("threshold_seconds", "N/A")))
        rows.append(f"<li><strong>{source}</strong>: {query} took {elapsed}s (threshold {threshold}s)</li>")

    omitted = ""
    if len(source_warnings) > 10:
        omitted = f"<li>{len(source_warnings) - 10} more warnings omitted</li>"

    return f"""
    <div class="alert alert-warning" role="status">
      <strong>Performance warnings:</strong> {len(source_warnings)} slow queries across {warning_sources}.
      Results are still included.
      <ul class="mb-0 mt-2">
        {''.join(rows)}
        {omitted}
      </ul>
    </div>
    """
