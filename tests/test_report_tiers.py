"""Tests for report score tier helpers."""

from __future__ import annotations

from job_radar.report_tiers import score_tier, tier_icon_class


def test_score_tier_classifies_report_thresholds():
    assert score_tier(4.0) == "strong"
    assert score_tier(3.9) == "rec"
    assert score_tier(3.5) == "rec"
    assert score_tier(3.4) == "review"


def test_tier_icon_class_matches_css_convention():
    assert tier_icon_class("strong") == "tier-icon tier-icon-strong"
