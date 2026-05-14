"""Tests for review-state GUI view-model helpers."""

from job_radar.gui.review_state_view_model import format_review_state_summary


def test_format_review_state_summary_orders_nonzero_counts():
    assert format_review_state_summary({
        "dismissed": 3,
        "shortlisted": 1,
        "maybe_later": 2,
    }) == [
        "1 shortlisted job",
        "2 maybe later jobs",
        "3 dismissed jobs",
    ]


def test_format_review_state_summary_omits_empty_counts():
    assert format_review_state_summary({
        "shortlisted": 0,
        "maybe_later": 4,
        "dismissed": 0,
    }) == ["4 maybe later jobs"]


def test_format_review_state_summary_handles_missing_counts():
    assert format_review_state_summary({}) == []
    assert format_review_state_summary(None) == []
