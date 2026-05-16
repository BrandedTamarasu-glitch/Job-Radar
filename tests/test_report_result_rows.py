"""Tests for all-results report row rendering."""

from __future__ import annotations

from job_radar.report_result_rows import html_result_row


def _result(job, *, score: float = 3.2, is_new: bool = True) -> dict:
    return {
        "job": job,
        "score": {
            "overall": score,
            "recommendation": "Worth reviewing",
        },
        "is_new": is_new,
    }


def test_html_result_row_renders_job_fields_and_controls(job_factory):
    row = html_result_row(_result(job_factory()), 2)

    assert '<th scope="row" data-label="#">2</th>' in row
    assert "Senior Python Developer" in row
    assert "TestCorp" in row
    assert "$120k-$150k" in row
    assert "Full-time" in row
    assert "Remote" in row
    assert "Worth reviewing" in row
    assert 'href="https://example.com/job/123"' in row
    assert 'data-review-state="shortlisted"' in row
    assert 'aria-label="Change application status"' in row
    assert "New" in row
    assert 'class="job-item tier-' in row
    assert 'tabindex="0"' in row


def test_html_result_row_escapes_text_fields(job_factory):
    job = job_factory(
        title="<Backend>",
        company="<Acme>",
        location="<Remote>",
        description="<script>alert(1)</script>",
    )

    row = html_result_row(_result(job), 1)

    assert "<Backend>" not in row
    assert "&lt;Backend&gt;" in row
    assert "<Acme>" not in row
    assert "&lt;Acme&gt;" in row
    assert "<Remote>" not in row
    assert "&lt;Remote&gt;" in row
    assert "<script>" not in row


def test_html_result_row_neutralizes_unsafe_url_and_can_hide_new_badge(job_factory):
    job = job_factory(url="javascript:alert(1)")

    row = html_result_row(_result(job, is_new=False), 1)

    assert "javascript:alert" not in row
    assert "URL unavailable" in row
    assert 'class="job-item tier-' not in row
    assert 'tabindex="0"' not in row
    assert ">New<" not in row
