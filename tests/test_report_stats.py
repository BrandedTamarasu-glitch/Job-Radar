"""Tests for report statistics helpers."""

from __future__ import annotations

from job_radar.report_stats import calculate_report_stats


def test_calculate_report_stats_counts_threshold_new_and_high_score():
    results = [
        {"score": {"overall": 4.2}, "is_new": True},
        {"score": {"overall": 3.6}, "is_new": False},
        {"score": {"overall": 3.1}},
        {"score": {"overall": 2.7}, "is_new": True},
    ]

    assert calculate_report_stats(results, min_score=2.8) == {
        "total": 3,
        "new": 2,
        "high_score": 2,
    }


def test_calculate_report_stats_handles_empty_results():
    assert calculate_report_stats([], min_score=2.8) == {
        "total": 0,
        "new": 0,
        "high_score": 0,
    }
