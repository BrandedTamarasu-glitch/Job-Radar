"""Tests for shared report control rendering."""

from __future__ import annotations

import pytest

from job_radar.report_controls import (
    html_copy_action_bar,
    html_filter_controls,
    html_shortlist_button,
    html_status_dropdown,
)


def test_html_copy_action_bar_renders_hero_copy_controls():
    html = html_copy_action_bar("hero")

    assert "Copy All Top Match URLs" in html
    assert 'onclick="copyAllHeroUrls(this)"' in html
    assert "shortcut-hint" in html
    assert "<kbd>J</kbd>/<kbd>K</kbd>" in html
    assert "exportPendingStatusUpdates" not in html


def test_html_copy_action_bar_renders_recommended_copy_and_export_controls():
    html = html_copy_action_bar("recommended")

    assert "Copy All Recommended URLs" in html
    assert 'onclick="copyAllRecommendedUrls(this)"' in html
    assert "Export Status Updates" in html
    assert 'onclick="exportPendingStatusUpdates()"' in html
    assert "shortcut-hint" in html


def test_html_copy_action_bar_rejects_unknown_sections():
    with pytest.raises(ValueError, match="Unknown copy action bar section"):
        html_copy_action_bar("saved")


def test_html_filter_controls_render_status_filters_and_export_actions():
    html = html_filter_controls()

    assert 'role="region"' in html
    assert 'aria-labelledby="filter-heading"' in html
    assert 'id="filter-applied"' in html
    assert 'id="filter-rejected"' in html
    assert 'id="filter-interviewing"' in html
    assert 'id="filter-offer"' in html
    assert 'id="filter-shortlist"' in html
    assert 'id="clear-filters"' in html
    assert 'onclick="exportVisibleJobsToCSV()"' in html
    assert 'id="view-mode-toggle"' in html
    assert 'id="filter-count"' in html


def test_html_shortlist_button_renders_all_review_states():
    html = html_shortlist_button("backend||acme")

    assert 'data-shortlist-key="backend||acme"' in html
    assert 'data-review-state="shortlisted"' in html
    assert 'data-review-state="maybe_later"' in html
    assert 'data-review-state="dismissed"' in html
    assert 'aria-label="Toggle shortlist for this job"' in html


def test_html_shortlist_button_supports_compact_spacing_and_escapes_key():
    html = html_shortlist_button("<backend>||acme", compact=True)

    assert "review-state-controls mt-1" in html
    assert "&lt;backend&gt;||acme" in html
    assert "<backend>" not in html


def test_html_status_dropdown_renders_status_choices_and_optional_spacing():
    html = html_status_dropdown(extra_classes="ms-2")

    assert "dropdown d-inline-block ms-2" in html
    assert 'aria-label="Change application status"' in html
    assert 'data-status="applied"' in html
    assert 'data-status="interviewing"' in html
    assert 'data-status="rejected"' in html
    assert 'data-status="offer"' in html
    assert 'data-status=""' in html
