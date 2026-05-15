"""Tests for manual-check URL report rendering."""

from __future__ import annotations

from job_radar.report_manual import html_manual_urls_section


def test_html_manual_urls_section_groups_sources_and_links_safely():
    html = html_manual_urls_section([
        {"source": "Indeed", "title": "Backend", "url": "https://indeed.com/jobs"},
        {"source": "Indeed", "title": "API", "url": "javascript:alert(1)"},
        {"source": "LinkedIn", "title": "<Engineer>", "url": "https://linkedin.com/jobs"},
    ])

    assert 'aria-labelledby="manual-heading"' in html
    assert "Manual Check URLs" in html
    assert "<strong>Indeed:</strong>" in html
    assert "<strong>LinkedIn:</strong>" in html
    assert 'href="https://indeed.com/jobs"' in html
    assert "API: Indeed Search URL unavailable" in html
    assert "javascript:alert" not in html
    assert "&lt;Engineer&gt;" in html


def test_html_manual_urls_section_omits_empty_input():
    assert html_manual_urls_section([]) == ""
