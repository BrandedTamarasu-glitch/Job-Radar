"""Tests for shared report result-table rendering."""

from __future__ import annotations

from job_radar.report_results import (
    COLLAPSE_RESULTS_AFTER,
    COLLAPSED_RESULTS_RENDER_LIMIT,
    html_collapsed_results_section,
    html_results_section,
    html_results_table,
    html_results_table_header,
    html_zero_results_section,
)


def test_html_results_table_uses_row_renderer_for_visible_and_collapsed_rows():
    scored_results = [{"job": f"job-{index}"} for index in range(COLLAPSE_RESULTS_AFTER + 2)]
    rendered_indexes = []

    def row_renderer(result, index):
        rendered_indexes.append(index)
        return f"<tr><td>{result['job']}:{index}</td></tr>"

    html = html_results_table(
        scored_results,
        row_renderer=row_renderer,
        filter_controls="<div>Filters</div>",
    )

    assert rendered_indexes == list(range(1, COLLAPSE_RESULTS_AFTER + 3))
    assert "Show 2 additional lower-score results" in html
    assert "<div>Filters</div>" in html
    assert "job-0:1" in html
    assert f"job-{COLLAPSE_RESULTS_AFTER + 1}:{COLLAPSE_RESULTS_AFTER + 2}" in html


def test_html_results_table_caps_collapsed_row_rendering():
    total_results = COLLAPSE_RESULTS_AFTER + COLLAPSED_RESULTS_RENDER_LIMIT + 3
    scored_results = [{"job": f"job-{index}"} for index in range(total_results)]
    rendered_indexes = []

    def row_renderer(result, index):
        rendered_indexes.append(index)
        return f"<tr><td>{result['job']}:{index}</td></tr>"

    html = html_results_table(
        scored_results,
        row_renderer=row_renderer,
        filter_controls="<div>Filters</div>",
    )

    assert len(rendered_indexes) == COLLAPSE_RESULTS_AFTER + COLLAPSED_RESULTS_RENDER_LIMIT
    assert rendered_indexes[-1] == COLLAPSE_RESULTS_AFTER + COLLAPSED_RESULTS_RENDER_LIMIT
    assert "3 additional lower-score rows omitted from the HTML view" in html


def test_html_results_table_renders_zero_results_without_filter_controls():
    html = html_results_table(
        [],
        row_renderer=lambda _result, _index: "<tr></tr>",
        filter_controls="<div>Filters</div>",
    )

    assert "No results found." in html
    assert "<div>Filters</div>" not in html


def test_html_results_section_renders_visible_and_collapsed_results():
    html = html_results_section(
        filter_controls="<div>Filters</div>",
        visible_rows_html="<tr><td>Visible</td></tr>",
        collapsed_rows_html="<details>More</details>",
    )

    assert 'aria-labelledby="results-heading"' in html
    assert "<div>Filters</div>" in html
    assert "All Results (sorted by score)" in html
    assert "Job search results sorted by relevance score, highest first" in html
    assert "<tr><td>Visible</td></tr>" in html
    assert "<details>More</details>" in html


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
