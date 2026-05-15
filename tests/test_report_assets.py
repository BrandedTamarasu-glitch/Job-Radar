"""Tests for local report asset primitives."""

from __future__ import annotations

from job_radar.report_assets import html_external_scripts, html_external_stylesheets


def test_report_assets_are_local_bootstrap_compatible_primitives():
    styles = html_external_stylesheets()
    scripts = html_external_scripts()

    assert "job-radar-local-report-primitives" in styles
    assert ".dropdown-menu" in styles
    assert "window.Notyf" in scripts
    assert "data-bs-toggle=\"dropdown\"" in scripts
    assert "cdn.jsdelivr" not in styles + scripts
