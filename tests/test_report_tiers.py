"""Tests for report score tier helpers."""

from __future__ import annotations

from job_radar.report_tiers import html_new_badge, html_score_badge, score_tier, tier_icon_class


def test_score_tier_classifies_report_thresholds():
    assert score_tier(4.0) == "strong"
    assert score_tier(3.9) == "rec"
    assert score_tier(3.5) == "rec"
    assert score_tier(3.4) == "review"


def test_tier_icon_class_matches_css_convention():
    assert tier_icon_class("strong") == "tier-icon tier-icon-strong"


def test_html_score_badge_includes_accessible_score_and_optional_label():
    badge = html_score_badge(4.25, "strong", label="Top Match")

    assert 'tier-icon tier-icon-strong' in badge
    assert 'tier-badge-strong' in badge
    assert '<span class="visually-hidden">Score </span>4.2' in badge
    assert '<span class="badge-label">Top Match</span>' in badge


def test_html_score_badge_omits_label_when_not_provided():
    badge = html_score_badge(3.5, "rec")

    assert 'tier-badge-rec' in badge
    assert "badge-label" not in badge
    assert "out of 5.0" in badge


def test_html_new_badge_supports_card_and_table_variants():
    card_badge = html_new_badge(leading_space=True)
    row_badge = html_new_badge(rounded=True)

    assert card_badge.startswith(" ")
    assert 'class="badge bg-primary"' in card_badge
    assert 'class="badge bg-primary rounded-pill"' in row_badge
    assert "New listing, not seen in previous searches" in row_badge
