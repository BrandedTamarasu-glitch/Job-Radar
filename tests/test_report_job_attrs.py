"""Tests for report job attribute helpers."""

from __future__ import annotations

from types import SimpleNamespace

from job_radar.report_job_attrs import html_job_attrs, report_job_key


def _job(url: str = "https://example.com/job"):
    return SimpleNamespace(
        title=" Backend Engineer ",
        company=" Acme ",
        url=url,
    )


def test_report_job_key_matches_tracker_key_shape():
    assert report_job_key(_job()) == "backend engineer||acme"


def test_html_job_attrs_includes_safe_url_score_and_identity_attrs():
    attrs = html_job_attrs(
        _job(),
        class_value="card job-item",
        score=4.25,
        include_tabindex=True,
    )

    assert 'class="card job-item"' in attrs
    assert 'tabindex="0"' in attrs
    assert 'data-job-url="https://example.com/job"' in attrs
    assert 'data-score="4.2"' in attrs
    assert 'data-job-key="backend engineer||acme"' in attrs
    assert 'data-job-title=" Backend Engineer "' in attrs
    assert 'data-job-company=" Acme "' in attrs


def test_html_job_attrs_omits_unsafe_url_and_tabindex():
    attrs = html_job_attrs(
        _job("javascript:alert(1)"),
        class_value="tier-review",
        score=3.0,
        include_tabindex=True,
    )

    assert "javascript:alert" not in attrs
    assert "data-job-url" not in attrs
    assert "data-score" not in attrs
    assert "tabindex" not in attrs
