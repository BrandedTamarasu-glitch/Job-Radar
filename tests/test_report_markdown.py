"""Tests for Markdown report section rendering."""

from __future__ import annotations

from job_radar.report_markdown import (
    append_all_results_table,
    append_detailed_result,
    append_manual_urls_section,
    markdown_filtered_out_section,
    markdown_result_row,
)


def _result(job, *, score: float = 3.8, is_new: bool = True) -> dict:
    return {
        "job": job,
        "score": {
            "overall": score,
            "recommendation": "Good match",
            "components": {
                "skill_match": {
                    "ratio": "2/3",
                    "matched_core": ["Python", "FastAPI"],
                    "missing_core": ["PostgreSQL"],
                    "matched_secondary": ["Docker"],
                },
                "title_relevance": {"reason": "Related"},
                "seniority": {"reason": "Matches level"},
                "response": {"likelihood": "High", "reason": "Strong fit"},
                "comp_note": "Below target floor",
                "parse_note": "Parsed confidently",
            },
        },
        "is_new": is_new,
    }


def test_markdown_filtered_out_section_renders_limited_table(job_factory):
    filtered_out = [_result(job_factory(title=f"Backend | {index}"), score=2.1) for index in range(12)]

    lines = markdown_filtered_out_section(filtered_out, 2.8)
    content = "\n".join(lines)

    assert "## Filtered Out" in content
    assert "| Title | Company | Score | Why |" in content
    assert "Backend \\| 0" in content
    assert "2.1/5.0" in content
    assert "2 more filtered jobs omitted" in content


def test_markdown_filtered_out_section_omits_empty_section():
    assert markdown_filtered_out_section([], 2.8) == []


def test_append_manual_urls_section_groups_sources_and_sanitizes_urls():
    lines = []
    manual_urls = [
        {"source": "Dice", "title": "Backend", "url": "https://example.com/dice"},
        {"source": "Dice", "title": "Python", "url": "https://example.com/python"},
        {"source": "Unsafe", "title": "Bad", "url": "javascript:alert(1)"},
    ]

    append_manual_urls_section(lines, manual_urls)
    content = "\n".join(lines)

    assert "## Manual Check URLs" in content
    assert "**Dice:**" in content
    assert "- Backend: [Dice Search](https://example.com/dice)" in content
    assert "- Python: [Dice Search](https://example.com/python)" in content
    assert "**Unsafe:**" in content
    assert "javascript:alert" not in content
    assert "- Bad: Unsafe Search URL unavailable" in content


def test_append_manual_urls_section_renders_heading_for_empty_urls():
    lines = []

    append_manual_urls_section(lines, [])

    assert lines == [
        "## Manual Check URLs",
        "_Open these in your browser to check sources that block automated access._",
        "",
        "",
    ]


def test_markdown_result_row_renders_safe_link_and_listing_fields(job_factory):
    row = markdown_result_row(_result(job_factory()), 2)

    assert row.startswith("| 2 | **3.8/5.0** (Good match) | NEW |")
    assert "Senior Python Developer" in row
    assert "TestCorp" in row
    assert "$120k-$150k" in row
    assert "Full-time" in row
    assert "Remote" in row
    assert "[Test](https://example.com/job/123)" in row


def test_markdown_result_row_neutralizes_unsafe_link_and_not_listed_salary(job_factory):
    row = markdown_result_row(
        _result(job_factory(url="javascript:alert(1)", salary="Not listed"), is_new=False),
        1,
    )

    assert "javascript:alert" not in row
    assert "|  |" in row
    assert "| — |" in row
    assert "| Test |" in row


def test_append_all_results_table_renders_rows(job_factory):
    lines = []

    append_all_results_table(lines, [_result(job_factory())])
    content = "\n".join(lines)

    assert "## All Results (sorted by score)" in content
    assert "| # | Score | New | Title | Company | Salary | Type | Location | Snippet | Link |" in content
    assert "Senior Python Developer" in content


def test_append_all_results_table_renders_empty_state():
    lines = []

    append_all_results_table(lines, [])
    content = "\n".join(lines)

    assert "_No results found._" in content
    assert "### Try Next" in content
    assert "Lower the minimum score threshold" in content


def test_append_detailed_result_renders_recommended_entry(job_factory, sample_profile):
    lines = []
    profile = dict(sample_profile)
    profile["highlights"] = ["Built Python APIs at scale"]

    append_detailed_result(lines, 1, _result(job_factory()), profile)
    content = "\n".join(lines)

    assert "### 1. Senior Python Developer — TestCorp — Score: 3.8/5.0 [NEW]" in content
    assert "- **Posted:** 2026-02-08" in content
    assert "- **Stack match:** 2/3" in content
    assert "- **Missing must-have skills:** PostgreSQL" in content
    assert "- **Nice-to-have matches:** Docker" in content
    assert "- **Response likelihood:** High — Strong fit" in content
    assert "- **Comp warning:** Below target floor" in content
    assert "- **Note:** Parsed confidently" in content
    assert "- **Link:** [Test](https://example.com/job/123)" in content
    assert "- **Talking points:**" in content


def test_append_detailed_result_neutralizes_unsafe_url_and_non_new(job_factory, sample_profile):
    lines = []

    append_detailed_result(
        lines,
        1,
        _result(job_factory(url="javascript:alert(1)"), is_new=False),
        sample_profile,
    )
    content = "\n".join(lines)

    assert "[NEW]" not in content
    assert "javascript:alert" not in content
    assert "- **Link:** Test URL unavailable" in content
