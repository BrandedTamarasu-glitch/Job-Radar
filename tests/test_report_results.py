"""Tests for shared report result-table rendering."""

from __future__ import annotations

from job_radar.report_results import (
    html_collapsed_results_section,
    html_results_table_header,
    html_zero_results_section,
)


def test_html_collapsed_results_section_renders_lower_score_table():
    html = html_collapsed_results_section(
        hidden_count=3,
        rows_html="<tr><td>Job</td></tr>",
    )

    assert 'id="lower-score-results"' in html
    assert "Show 3 additional lower-score results" in html
    assert "Additional lower-score job results sorted by relevance score" in html
    assert "<tr><td>Job</td></tr>" in html
    assert "additional lower-score rows omitted" not in html


def test_html_collapsed_results_section_renders_omitted_note():
    html = html_collapsed_results_section(
        hidden_count=203,
        rows_html="<tr><td>Job</td></tr>",
        omitted_count=2,
    )

    assert "2 additional lower-score rows omitted from the HTML view" in html
    assert "to keep large reports responsive" in html


def test_html_zero_results_section_renders_empty_state_tips():
    html = html_zero_results_section(["Broaden titles", "Add Python"])

    assert 'aria-labelledby="results-heading"' in html
    assert "All Results (sorted by score)" in html
    assert "No results found." in html
    assert "Try next" in html
    assert "<li>Broaden titles</li>" in html
    assert "<li>Add Python</li>" in html


def test_html_zero_results_section_escapes_tips():
    html = html_zero_results_section(['Add <script>alert("x")</script>'])

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


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
