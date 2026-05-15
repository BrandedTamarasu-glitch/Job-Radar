"""Tests for shared report result-table rendering."""

from __future__ import annotations

from job_radar.report_results import html_results_table_header


def test_html_results_table_header_renders_common_columns():
    html = html_results_table_header("Job search results sorted by relevance score")

    assert '<caption class="visually-hidden">Job search results sorted by relevance score</caption>' in html
    assert '<th scope="col">#</th>' in html
    assert '<th scope="col">Score</th>' in html
    assert '<th scope="col" class="col-new">New</th>' in html
    assert '<th scope="col">Status</th>' in html
    assert '<th scope="col">Title</th>' in html
    assert '<th scope="col">Company</th>' in html
    assert '<th scope="col" class="col-salary">Salary</th>' in html
    assert '<th scope="col" class="col-type">Type</th>' in html
    assert '<th scope="col">Location</th>' in html
    assert '<th scope="col" class="col-snippet">Snippet</th>' in html
    assert '<th scope="col">Link</th>' in html


def test_html_results_table_header_escapes_caption():
    html = html_results_table_header('<script>alert("x")</script>')

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
