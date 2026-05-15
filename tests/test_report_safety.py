"""Tests for report safety helpers."""

from __future__ import annotations

from job_radar.report_safety import safe_external_url


def test_safe_external_url_accepts_http_and_https():
    assert safe_external_url("https://example.com/jobs") == "https://example.com/jobs"
    assert safe_external_url(" http://example.com/jobs ") == "http://example.com/jobs"


def test_safe_external_url_rejects_non_external_or_unsafe_urls():
    assert safe_external_url("") == ""
    assert safe_external_url(None) == ""
    assert safe_external_url("/relative/path") == ""
    assert safe_external_url("javascript:alert(1)") == ""
    assert safe_external_url("data:text/html,<script>alert(1)</script>") == ""
