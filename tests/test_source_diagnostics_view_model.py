"""Tests for source diagnostics Settings view-model helpers."""

from job_radar.gui.source_diagnostics_view_model import (
    build_cache_totals,
    build_source_diagnostics,
    format_cache_freshness_line,
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
    assert rows[0].health_label == "Needs attention"
    assert rows[0].recommended_action == "retry later or uncheck this source in Search > Sources if failures continue"
    assert rows[0].health_priority == 3


def test_source_diagnostics_tracks_failed_source_without_timing():
    """Failed sources still appear even when they have no completed source row."""
    history = [{"sources": [], "failed_sources": ["Adzuna"]}]

    rows = build_source_diagnostics(history)

    assert len(rows) == 1
    assert rows[0].name == "Adzuna"
    assert rows[0].runs == 0
    assert rows[0].failure_count == 1
    assert rows[0].average_duration is None


def test_source_diagnostics_prioritizes_failures_before_slow_sources():
    """Failed sources stay visible even when slow sources have timing data."""
    history = [
        {
            "sources": [
                {"name": "SlowSource", "job_count": 1, "warning_count": 0, "duration_seconds": 90.0},
            ],
            "failed_sources": ["BrokenSource"],
        },
    ]

    rows = build_source_diagnostics(history)

    assert [row.name for row in rows[:2]] == ["BrokenSource", "SlowSource"]


def test_source_diagnostics_labels_warning_slow_and_healthy_sources():
    """Source health labels make source diagnostics easier to scan."""
    history = [
        {
            "sources": [
                {"name": "WarningSource", "job_count": 1, "warning_count": 1, "duration_seconds": 2.0},
                {"name": "SlowSource", "job_count": 1, "warning_count": 0, "duration_seconds": 45.0},
                {"name": "HealthySource", "job_count": 1, "warning_count": 0, "duration_seconds": 1.0},
            ],
            "failed_sources": [],
        },
    ]

    rows = {row.name: row for row in build_source_diagnostics(history)}

    assert rows["WarningSource"].health_label == "Watch"
    assert rows["WarningSource"].recommended_action == "review warnings before relying on results"
    assert rows["WarningSource"].health_priority == 2
    assert rows["SlowSource"].health_label == "Slow"
    assert rows["SlowSource"].recommended_action == "consider cache freshness or source timeout tuning"
    assert rows["SlowSource"].health_priority == 1
    assert rows["HealthySource"].health_label == "Healthy"
    assert rows["HealthySource"].recommended_action == "no action needed"
    assert rows["HealthySource"].health_priority == 0


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


def test_cache_freshness_line_summarizes_cache_vs_live_requests():
    """Cache freshness copy explains how much recent source data came from cache."""
    assert format_cache_freshness_line({
        "hits": 6,
        "misses": 3,
        "writes": 2,
        "disabled": 1,
    }) == "Cache freshness: 60% served from cache, 3 live refreshes, 1 uncached requests"
    assert format_cache_freshness_line({"hits": 0, "misses": 0, "disabled": 0}) is None


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
        "Source controls: use Search > Sources to temporarily disable unreliable sources, then refresh diagnostics after reruns.",
        "RemoteOK (Slow): avg 1m 05s, max 1m 05s; 1 run; 3 jobs; "
        "0 warnings; 0 failures; consider cache freshness or source timeout tuning",
        "Cache totals: 2 hits, 1 misses, 1 writes, 0 uncached requests",
        "Cache freshness: 67% served from cache, 1 live refreshes",
    ]


def test_format_source_diagnostics_lines_includes_source_control_guidance():
    """Diagnostics explain how source health maps to existing source controls."""
    lines = format_source_diagnostics_lines([
        {
            "sources": [
                {"name": "Dice", "job_count": 1, "warning_count": 0, "duration_seconds": 1.0},
            ],
            "failed_sources": [],
        }
    ])

    assert lines[0] == (
        "Source controls: use Search > Sources to temporarily disable unreliable sources, "
        "then refresh diagnostics after reruns."
    )
