"""Tests for report source warning formatters."""

from __future__ import annotations

from job_radar.report_source_warnings import (
    failed_source_names,
    html_source_failures,
    html_source_warnings,
    markdown_source_failures,
    markdown_source_warnings,
)


def test_failed_source_names_are_unique_sorted_and_normalized():
    assert failed_source_names([
        {"source": "dice"},
        {"source": "Adzuna"},
        {"source": "dice"},
        {"source": ""},
    ]) == ["Adzuna", "dice", "unknown"]


def test_markdown_source_failure_table_escapes_cells():
    lines = markdown_source_failures([
        {"source": "dice", "query": "Backend|API", "error": "timeout\nretry"}
    ])

    assert "| dice | Backend\\|API | timeout retry |" in lines


def test_markdown_source_warning_table_includes_timings():
    lines = markdown_source_warnings([
        {"source": "dice", "query": "Backend", "elapsed_seconds": 9.5, "threshold_seconds": 8.0}
    ])

    assert "| dice | Backend | 9.5s | 8.0s |" in lines


def test_html_source_warning_sections_escape_values():
    failure_html = html_source_failures([
        {"source": "<dice>", "query": "Backend", "error": "<timeout>"}
    ])
    warning_html = html_source_warnings([
        {"source": "<dice>", "query": "Backend", "elapsed_seconds": 9.5, "threshold_seconds": 8.0}
    ])

    assert "&lt;dice&gt;" in failure_html
    assert "&lt;timeout&gt;" in failure_html
    assert "Performance warnings" in warning_html
    assert "9.5s" in warning_html
