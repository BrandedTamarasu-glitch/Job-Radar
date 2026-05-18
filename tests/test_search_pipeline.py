"""Tests for shared search pipeline helpers."""

from datetime import date

from job_radar.search_pipeline import (
    apply_result_filters,
    apply_scored_result_filters,
    apply_preferred_skills,
    filter_application_status_results,
    filter_by_company,
    filter_by_location_strictness,
    filter_min_score_results,
    filter_new_results,
    parse_company_filter,
    parse_skill_filter,
    resolve_date_filter,
    score_results,
)
from job_radar.sources import JobResult


def test_parse_search_pipeline_filters_normalize_inputs():
    assert parse_company_filter(" Northstar, Ledger ") == ["northstar", "ledger"]
    assert parse_company_filter([" RemoteCo ", ""]) == ["remoteco"]
    assert parse_skill_filter(" Python, Kubernetes ") == ["Python", "Kubernetes"]
    assert parse_skill_filter([" Docker ", ""]) == ["Docker"]


def test_apply_preferred_skills_returns_search_profile_copy():
    profile = {"secondary_skills": ["Docker"]}

    search_profile = apply_preferred_skills(profile, "docker, Kubernetes")

    assert search_profile == {"secondary_skills": ["Docker", "Kubernetes"]}
    assert profile == {"secondary_skills": ["Docker"]}


def test_shared_company_and_location_filters():
    jobs = [
        JobResult(
            title="Engineer",
            company="Northstar Tools",
            location="Anywhere",
            arrangement="unknown",
            salary="Not listed",
            date_posted="Today",
            description="Remote team",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="LedgerWorks",
            location="New York, NY",
            arrangement="on-site",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/2",
            source="Dice",
        ),
    ]

    assert [job.company for job in filter_by_company(jobs, include="northstar")] == [
        "Northstar Tools"
    ]
    assert [job.company for job in filter_by_location_strictness(jobs, "exclude_onsite")] == [
        "Northstar Tools"
    ]


def test_apply_result_filters_combines_raw_filters():
    jobs = [
        JobResult(
            title="Engineer",
            company="Northstar Tools",
            location="Anywhere",
            arrangement="unknown",
            salary="Not listed",
            date_posted="2026-05-18",
            description="Remote NodeJS and Kubernetes role",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="LedgerWorks",
            location="New York, NY",
            arrangement="on-site",
            salary="Not listed",
            date_posted="2026-05-18",
            description="Build Python services",
            url="https://example.com/2",
            source="Dice",
        ),
    ]

    def date_filter(results, from_date, to_date):
        assert (from_date, to_date) == ("2026-05-01", "2026-05-18")
        return results

    filtered, from_date, to_date = apply_result_filters(
        jobs,
        {
            "from_date": "2026-05-01",
            "to_date": "2026-05-18",
            "include_companies": "northstar, ledger",
            "exclude_companies": "ledger",
            "required_skills": "node.js",
            "location_strictness": "remote_only",
        },
        date_filter_func=date_filter,
    )

    assert (from_date, to_date) == ("2026-05-01", "2026-05-18")
    assert [job.company for job in filtered] == ["Northstar Tools"]


def test_score_results_filters_dealbreakers_and_sorts_descending():
    jobs = [
        JobResult(
            title="Engineer",
            company="LowCo",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="HighCo",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/2",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="NopeCo",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/3",
            source="Dice",
        ),
    ]

    def score_func(job, _profile):
        scores = {
            "LowCo": {"overall": 3.0},
            "HighCo": {"overall": 4.2},
            "NopeCo": {"overall": 5.0, "dealbreaker": "onsite"},
        }
        return scores[job.company]

    scored, dealbreaker_count = score_results(jobs, {"name": "Test User"}, score_func)

    assert [result["job"].company for result in scored] == ["HighCo", "LowCo"]
    assert dealbreaker_count == 1


def test_apply_scored_result_filters_handles_new_score_and_status_filters():
    scored = [
        {"job": object(), "score": {"overall": 4.0}, "is_new": True},
        {"job": object(), "score": {"overall": 3.0}, "is_new": False},
        {"job": object(), "score": {"overall": 2.0}, "is_new": True},
    ]

    def status_filter(results, statuses):
        assert statuses == {"rejected", "skipped"}
        return results[:1]

    filtered, min_score = apply_scored_result_filters(
        scored,
        {"new_only": True, "min_score": 2.8, "hide_rejected_skipped": True},
        status_filter_func=status_filter,
    )

    assert filtered == [scored[0]]
    assert min_score == 2.8


def test_composable_scored_result_filters_preserve_cli_counting_steps():
    scored = [
        {"job": "new-high", "score": {"overall": 4.0}, "is_new": True},
        {"job": "seen-high", "score": {"overall": 4.5}, "is_new": False},
        {"job": "new-low", "score": {"overall": 2.0}, "is_new": True},
    ]

    assert filter_new_results(scored) == [scored[0], scored[2]]
    assert filter_min_score_results(scored, 3.0) == [scored[0], scored[1]]

    def status_filter(results, statuses):
        assert statuses == {"rejected"}
        return results[:1]

    assert filter_application_status_results(
        scored,
        {"rejected"},
        status_filter_func=status_filter,
    ) == [scored[0]]


def test_resolve_date_filter_supports_custom_dates_and_freshness():
    today = date(2026, 5, 18)

    assert resolve_date_filter({"freshness": "past_48h"}, today=today) == (
        "2026-05-16",
        "2026-05-18",
    )
    assert resolve_date_filter({
        "freshness": "past_48h",
        "from_date": "2026-05-01",
        "to_date": "2026-05-03",
    }, today=today) == ("2026-05-01", "2026-05-03")
