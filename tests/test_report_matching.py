"""Tests for report match explanation helpers."""

from __future__ import annotations

from types import SimpleNamespace

from job_radar.report_matching import (
    match_highlights,
    match_summary_text,
    skill_callout_groups,
)


def test_skill_callout_groups_split_must_have_and_nice_to_have():
    skill = {
        "missing_core": ["FastAPI"],
        "matched_secondary": ["Docker"],
    }
    profile = {"secondary_skills": ["Docker", "Redis"]}

    assert skill_callout_groups(skill, profile) == [
        ("Missing must-have skills", ["FastAPI"]),
        ("Nice-to-have matches", ["Docker"]),
        ("Missing nice-to-have skills", ["Redis"]),
    ]


def test_match_summary_text_uses_score_components():
    result = {
        "score": {
            "overall": 4.2,
            "components": {
                "skill_match": {"ratio": "3/3"},
                "title_relevance": {"reason": "Exact match"},
                "seniority": {"reason": "Matches level"},
                "response": {"likelihood": "High"},
            },
        }
    }

    assert match_summary_text(result) == (
        "3/3 core skills; title: Exact match; seniority: Matches level; "
        "High response likelihood"
    )


def test_match_summary_text_falls_back_to_score():
    assert match_summary_text({"score": {"overall": 3.1, "components": {}}}) == (
        "Matched with score 3.1"
    )


def test_match_highlights_limits_relevant_talking_points():
    job = SimpleNamespace(title="Backend Platform Engineer", description="Python APIs")
    highlights = [
        "Built Python APIs",
        "Led backend platform migrations",
        "Scaled engineer onboarding",
        "Managed unrelated billing work",
    ]

    assert match_highlights(highlights, ["Python"], job) == [
        "Built Python APIs",
        "Led backend platform migrations",
        "Scaled engineer onboarding",
    ]
