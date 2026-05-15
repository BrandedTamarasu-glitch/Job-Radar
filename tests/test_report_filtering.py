"""Tests for report filtering data helpers."""

from __future__ import annotations

from job_radar.report_filtering import filter_explanation_text, filtered_out_results


def test_filtered_out_results_returns_jobs_below_threshold():
    results = [
        {"score": {"overall": 4.0}},
        {"score": {"overall": 3.4}},
        {"score": {"overall": 0.0, "dealbreaker": "relocation required"}},
    ]

    assert filtered_out_results(results, min_score=3.5) == results[1:]


def test_filter_explanation_text_prioritizes_dealbreakers():
    result = {"score": {"overall": 0.0, "components": {}, "dealbreaker": "relocation required"}}

    assert filter_explanation_text(result, min_score=3.5) == (
        "Rejected by dealbreaker: relocation required"
    )


def test_filter_explanation_text_summarizes_low_score_components():
    result = {
        "score": {
            "overall": 2.8,
            "components": {
                "skill_match": {"ratio": "1/3"},
                "title_relevance": {"reason": "Mismatch"},
                "seniority": {"reason": "Too junior"},
            },
        }
    }

    assert filter_explanation_text(result, min_score=3.5) == (
        "Below 3.5 threshold at 2.8/5.0: "
        "1/3 core skills; title: Mismatch; seniority: Too junior"
    )
