"""Tests for source diagnostics Settings view-model helpers."""

from job_radar.gui.source_diagnostics_view_model import (
    build_cache_totals,
    build_source_diagnostics,
    format_cache_freshness_line,
    format_preset_strategy_lines,
    format_pre_run_source_strategy_lines,
    format_source_selection_strategy_lines,
    format_source_coverage_lines,
    format_source_diagnostics_lines,
    format_source_toggle_recommendations,
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
    assert rows[0].reliability_score == 85


def test_source_diagnostics_tracks_failed_source_without_timing():
    """Failed sources still appear even when they have no completed source row."""
    history = [{"sources": [], "failed_sources": ["Adzuna"]}]

    rows = build_source_diagnostics(history)

    assert len(rows) == 1
    assert rows[0].name == "Adzuna"
    assert rows[0].runs == 0
    assert rows[0].failure_count == 1
    assert rows[0].average_duration is None
    assert rows[0].recommended_action == "temporarily uncheck this source in Search > Sources, then retry later"


def test_source_diagnostics_normalizes_source_keys_to_display_names():
    """Source keys from saved search config and failures render as user-facing names."""
    history = [
        {
            "search_config": {"preset": "remote-backend", "selected_sources": ["dice"]},
            "sources": [{"name": "Dice", "job_count": 3, "duration_seconds": 1.0}],
            "failed_sources": ["dice"],
            "total_jobs": 3,
        }
    ]

    rows = build_source_diagnostics(history)

    assert len(rows) == 1
    assert rows[0].name == "Dice"
    assert rows[0].runs == 1
    assert rows[0].failure_count == 1
    assert format_preset_strategy_lines(history) == [
        "Preset strategy: remote-backend had 1 source failure across 1 recent run; "
        "review Source controls before rerunning."
    ]
    assert "across 1 source" in format_preset_strategy_lines([
        {
            "search_config": {"preset": "remote-backend", "selected_sources": ["dice"]},
            "sources": [{"name": "Dice", "job_count": 3}],
            "failed_sources": [],
            "total_jobs": 3,
        }
    ])[0]


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
    assert rows["HealthySource"].reliability_score == 100


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
        "0 warnings; 0 failures; reliability 90/100; consider cache freshness or source timeout tuning",
        "Source selection: keep RemoteOK enabled for similar searches (3.0 jobs/run, no recent failures).",
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


def test_source_toggle_recommendations_call_out_unreliable_sources():
    rows = build_source_diagnostics([
        {
            "sources": [
                {"name": "HealthySource", "job_count": 2, "warning_count": 0, "duration_seconds": 1.0},
            ],
            "failed_sources": ["BrokenSource", "BrokenSource"],
        }
    ])

    assert format_source_toggle_recommendations(rows) == [
        "Source toggle recommendation: disable BrokenSource temporarily and rerun the search."
    ]
    lines = format_source_diagnostics_lines([
        {
            "sources": [
                {"name": "HealthySource", "job_count": 2, "warning_count": 0, "duration_seconds": 1.0},
            ],
            "failed_sources": ["BrokenSource", "BrokenSource"],
        }
    ])
    assert "Source toggle recommendation: disable BrokenSource temporarily and rerun the search." in lines


def test_source_coverage_lines_group_gaps_by_preset():
    history = [
        {
            "search_config": {"preset": "remote-backend"},
            "sources": [
                {"name": "Dice", "job_count": 0},
                {"name": "RemoteOK", "job_count": 3},
            ],
            "failed_sources": ["Adzuna"],
        },
        {
            "search_config": {"preset": "contract"},
            "sources": [{"name": "Dice", "job_count": 0}],
            "failed_sources": [],
        },
    ]

    assert format_source_coverage_lines(history) == [
        "Coverage gap: contract had no recent jobs from Dice.",
        "Coverage gap: remote-backend had no recent jobs from Adzuna, Dice.",
    ]
    lines = format_source_diagnostics_lines(history)
    assert "Coverage gap: remote-backend had no recent jobs from Adzuna, Dice." in lines


def test_preset_strategy_lines_recommend_source_and_preset_actions():
    history = [
        {
            "search_config": {"preset": "remote-backend", "selected_sources": ["Dice", "RemoteOK"]},
            "sources": [{"name": "Dice", "job_count": 0}, {"name": "RemoteOK", "job_count": 0}],
            "failed_sources": ["Dice"],
            "total_jobs": 0,
        },
        {
            "search_config": {"preset": "broad-local", "selected_sources": ["USAJobs"]},
            "sources": [{"name": "USAJobs", "job_count": 7}],
            "failed_sources": [],
            "total_jobs": 7,
        },
        {
            "search_config": {"preset": "entry-level", "selected_sources": ["Adzuna"]},
            "sources": [{"name": "Adzuna", "job_count": 0}],
            "failed_sources": [],
            "total_jobs": 0,
        },
    ]

    assert format_preset_strategy_lines(history, limit=2) == [
        "Preset strategy: remote-backend had 1 source failure across 1 recent run; "
        "review Source controls before rerunning.",
        "Preset strategy: entry-level averaged 0.0 jobs per run; broaden filters or try another preset before rerunning.",
    ]

    lines = format_source_diagnostics_lines(history)
    assert (
        "Preset strategy: broad-local averaged 7.0 jobs per run across 1 source."
        in lines
    )


def test_pre_run_source_strategy_lines_prioritize_actionable_guidance():
    history = [
        {
            "search_config": {"preset": "remote-backend", "selected_sources": ["Dice"]},
            "sources": [{"name": "Dice", "job_count": 0, "duration_seconds": 1.0}],
            "failed_sources": ["Dice", "Dice"],
            "total_jobs": 0,
        },
        {
            "search_config": {"preset": "local-hybrid", "selected_sources": ["RemoteOK"]},
            "sources": [{"name": "RemoteOK", "job_count": 0, "duration_seconds": 1.0}],
            "failed_sources": [],
            "total_jobs": 0,
        },
    ]

    assert format_pre_run_source_strategy_lines(history, limit=2) == [
        "Before rerunning: Dice has recent reliability issues; consider unchecking it in Sources.",
        "Before rerunning: RemoteOK has been low-yield recently (0.0 jobs/run); pair it with broader sources.",
    ]


def test_pre_run_source_strategy_lines_returns_empty_without_history():
    assert format_pre_run_source_strategy_lines([]) == []


def test_source_selection_strategy_lines_recommend_specific_source_choices():
    history = [
        {
            "sources": [
                {"name": "RemoteOK", "job_count": 8},
                {"name": "Dice", "job_count": 0},
                {"name": "Adzuna", "job_count": 0},
            ],
            "failed_sources": ["Dice", "Dice"],
        },
        {
            "sources": [
                {"name": "RemoteOK", "job_count": 4},
                {"name": "Adzuna", "job_count": 0},
            ],
            "failed_sources": [],
        },
    ]

    assert format_source_selection_strategy_lines(history) == [
        "Source selection: uncheck Dice for the next rerun unless you need its coverage "
        "(2 recent failures, 0.0 jobs/run).",
        "Source selection: Adzuna has been low-yield recently (0.0 jobs/run); pair it with broader sources.",
        "Source selection: keep RemoteOK enabled for similar searches (6.0 jobs/run, no recent failures).",
    ]

    lines = format_source_diagnostics_lines(history)
    assert (
        "Source selection: uncheck Dice for the next rerun unless you need its coverage "
        "(2 recent failures, 0.0 jobs/run)."
    ) in lines


def test_pre_run_source_strategy_lines_include_source_selection_fallbacks():
    history = [
        {
            "sources": [
                {"name": "RemoteOK", "job_count": 6},
                {"name": "Adzuna", "job_count": 0},
            ],
            "failed_sources": [],
        }
    ]

    assert format_pre_run_source_strategy_lines(history, limit=2) == [
        "Before rerunning: Adzuna has been low-yield recently (0.0 jobs/run); pair it with broader sources.",
        "Before rerunning: keep RemoteOK enabled for similar searches (6.0 jobs/run, no recent failures).",
    ]
