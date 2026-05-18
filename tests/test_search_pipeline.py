"""Tests for shared search pipeline helpers."""

from datetime import date

from job_radar.search_pipeline import (
    apply_preferred_skills,
    filter_by_company,
    filter_by_location_strictness,
    parse_company_filter,
    parse_skill_filter,
    resolve_date_filter,
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
