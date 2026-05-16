"""Tests for Markdown report section rendering."""

from __future__ import annotations

from job_radar.report_markdown import append_detailed_result, markdown_filtered_out_section


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
