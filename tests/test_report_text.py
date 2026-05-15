"""Tests for shared report text helpers."""

from __future__ import annotations

from job_radar.report_text import make_snippet, markdown_cell


def test_make_snippet_normalizes_empty_and_table_unsafe_text():
    assert make_snippet("") == "—"
    assert make_snippet("Python|Django\nRemote") == "Python Django Remote"


def test_make_snippet_truncates_at_word_boundary():
    assert make_snippet("Python Django FastAPI PostgreSQL", max_len=18) == "Python Django..."


def test_markdown_cell_escapes_table_separators_and_newlines():
    assert markdown_cell("Python|Django\nRemote") == "Python\\|Django Remote"
