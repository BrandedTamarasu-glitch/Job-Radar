"""Tests for source diagnostics Settings view-model helpers."""

from job_radar.gui.source_diagnostics_view_model import (
    build_cache_totals,
    build_source_diagnostics,
    format_source_diagnostics_lines,
)


def test_source_diagnostics_groups_slowest_sources_first():
    """Diagnostics aggregate source timings and sort by average duration."""
    history = [
        {
            "sources": [
                {"name": "Dice", "job_count": 2, "warning_count": 1, "duration_seconds": 2.0},
                {"name": "RemoteOK", "job_count": 4, "warning_count": 0, "duration_seconds": 5.0},
            ],
            "failed_sources": ["Dice"],
        },
        {
            "sources": [
                {"name": "Dice", "job_count": 1, "warning_count": 0, "duration_seconds": 4.0},
                {"name": "RemoteOK", "job_count": 1, "warning_count": 0, "duration_seconds": 1.0},
            ],
            "failed_sources": [],
        },
    ]

    rows = build_source_diagnostics(history)

    assert [row.name for row in rows] == ["Dice", "RemoteOK"]
    assert rows[0].runs == 2
    assert rows[0].total_jobs == 3
    assert rows[0].warning_count == 1
    assert rows[0].failure_count == 1
    assert rows[0].average_duration == 3.0
    assert rows[0].max_duration == 4.0


def test_source_diagnostics_tracks_failed_source_without_timing():
    """Failed sources still appear even when they have no completed source row."""
    history = [{"sources": [], "failed_sources": ["Adzuna"]}]

    rows = build_source_diagnostics(history)

    assert len(rows) == 1
    assert rows[0].name == "Adzuna"
    assert rows[0].runs == 0
    assert rows[0].failure_count == 1
    assert rows[0].average_duration is None


def test_cache_totals_sum_history_cache_stats():
    """Cache totals aggregate persisted per-run cache counters."""
    history = [
        {"cache_stats": {"hits": 2, "misses": 1, "writes": 1, "disabled": 0}},
        {"cache_stats": {"hits": 1, "misses": 3, "writes": 2, "disabled": 4}},
    ]

    assert build_cache_totals(history) == {
        "hits": 3,
        "misses": 4,
        "writes": 3,
        "disabled": 4,
    }


def test_format_source_diagnostics_lines_handles_empty_and_cache_totals():
    """Formatted diagnostics are plain text for the Settings tab."""
    assert format_source_diagnostics_lines([]) == [
        "No source diagnostics recorded yet. Run a search to populate this section."
    ]

    lines = format_source_diagnostics_lines([
        {
            "sources": [
                {"name": "RemoteOK", "job_count": 3, "warning_count": 0, "duration_seconds": 65.0},
            ],
            "failed_sources": [],
            "cache_stats": {"hits": 2, "misses": 1, "writes": 1, "disabled": 0},
        }
    ])

    assert lines == [
        "RemoteOK: avg 1m 05s, max 1m 05s; 1 run; 3 jobs; 0 warnings; 0 failures",
        "Cache totals: 2 hits, 1 misses, 1 writes, 0 uncached requests",
    ]
