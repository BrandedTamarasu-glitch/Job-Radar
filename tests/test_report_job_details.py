"""Tests for shared HTML job detail rendering."""

from __future__ import annotations

from types import SimpleNamespace

from job_radar.report_job_details import html_job_detail_items


def _result(url: str = "https://example.com/job") -> dict:
    job = SimpleNamespace(
        title="Backend Engineer",
        company="Acme",
        date_posted="Today",
        salary="$120K",
        location="Remote",
        arrangement="remote",
        employment_type="full-time",
        apply_info="Apply online",
        source="Dice",
        url=url,
        description="Python backend APIs",
    )
    return {
        "job": job,
        "score": {
            "overall": 4.2,
            "components": {
                "skill_match": {
                    "ratio": "2/3",
                    "matched_core": ["Python", "FastAPI"],
                    "missing_core": ["PostgreSQL"],
                    "matched_secondary": ["Docker"],
                },
                "title_relevance": {"reason": "Exact match"},
                "seniority": {"reason": "Matches level"},
                "response": {"likelihood": "High", "reason": "Strong keyword match"},
                "comp_note": "Meets floor",
                "parse_note": "Parsed confidently",
            },
        },
    }


def test_html_job_detail_items_renders_details_links_and_skill_callouts():
    html = html_job_detail_items(
        _result(),
        {
            "secondary_skills": ["Docker", "Redis"],
            "highlights": ["Built Python APIs", "Reduced frontend bundle size"],
        },
    )

    assert "<strong>Posted:</strong> Today" in html
    assert "Stack match:</strong> 2/3" in html
    assert "Missing must-have skills" in html
    assert "Missing nice-to-have skills" in html
    assert 'href="https://example.com/job"' in html
    assert 'data-url="https://example.com/job"' in html
    assert "Built Python APIs" in html


def test_html_job_detail_items_neutralizes_unsafe_urls():
    html = html_job_detail_items(_result("javascript:alert(1)"), {})

    assert "javascript:alert" not in html
    assert "Dice URL unavailable" in html
