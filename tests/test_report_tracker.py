"""Tests for tracker summary report rendering."""

from __future__ import annotations

from job_radar.report_tracker import html_tracker_stats


def test_html_tracker_stats_renders_lifetime_summary():
    html = html_tracker_stats({
        "total_unique_jobs_seen": 42,
        "total_runs": 7,
        "avg_new_per_run_last_7": 3.5,
    })

    assert "Lifetime stats:" in html
    assert "42 unique jobs seen" in html
    assert "across 7 runs" in html
    assert "Avg 3.5 new/run" in html
