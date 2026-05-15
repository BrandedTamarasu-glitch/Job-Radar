"""Tests for shared report control rendering."""

from __future__ import annotations

from job_radar.report_controls import html_shortlist_button


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
