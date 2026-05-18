"""Tests for source API response mappers."""

from job_radar.source_mappers import (
    map_adzuna_to_job_result,
    map_authenticjobs_to_job_result,
    map_jsearch_to_job_result,
)


def test_map_adzuna_to_job_result_maps_valid_item():
    result = map_adzuna_to_job_result({
        "title": "Software Engineer",
        "company": {"display_name": "Acme"},
        "redirect_url": "https://example.com/job",
        "location": {"display_name": "San Francisco, California, United States"},
        "description": "<p>Remote Python role</p>",
        "salary_min": 100000,
        "salary_max": 140000,
        "created": "2026-05-18",
        "contract_type": "permanent",
        "contract_time": "full_time",
    })

    assert result is not None
    assert result.source == "adzuna"
    assert result.location == "San Francisco, CA"
    assert result.salary == "$100,000 - $140,000"
    assert result.employment_type == "Permanent, Full-time"


def test_map_adzuna_to_job_result_rejects_missing_required_fields():
    assert map_adzuna_to_job_result({"title": "Software Engineer"}) is None


def test_map_authenticjobs_to_job_result_maps_valid_item():
    result = map_authenticjobs_to_job_result({
        "title": "Frontend Developer",
        "company": {
            "name": "Design Studio",
            "location": {"name": "Austin, Texas, United States"},
        },
        "url": "https://example.com/job",
        "description": "<div>Hybrid React role</div>",
        "post_date": "2026-05-18",
        "type": {"name": "Full-time"},
    })

    assert result is not None
    assert result.source == "authentic_jobs"
    assert result.location == "Austin, TX"
    assert result.arrangement == "hybrid"
    assert result.employment_type == "Full-time"


def test_map_authenticjobs_to_job_result_rejects_missing_required_fields():
    assert map_authenticjobs_to_job_result({"title": "Frontend Developer"}) is None


def test_map_jsearch_to_job_result_preserves_known_publisher_source():
    result = map_jsearch_to_job_result({
        "job_title": "Backend Engineer",
        "employer_name": "Acme",
        "job_apply_link": "https://example.com/apply",
        "job_publisher": "LinkedIn",
        "job_city": "Seattle",
        "job_state": "WA",
        "job_description": "<p>Remote Python role</p>",
        "job_posted_at_datetime_utc": "2026-05-18T12:00:00Z",
        "job_employment_type": "FULLTIME",
        "job_min_salary": 120000,
        "job_max_salary": 150000,
    })

    assert result is not None
    assert result.source == "linkedin"
    assert result.location == "Seattle, WA"
    assert result.salary == "$120,000 - $150,000"
    assert result.date_posted == "2026-05-18"


def test_map_jsearch_to_job_result_maps_unknown_publisher_to_other():
    result = map_jsearch_to_job_result({
        "job_title": "Backend Engineer",
        "employer_name": "Acme",
        "job_apply_link": "https://example.com/apply",
        "job_publisher": "Other Board",
        "job_is_remote": True,
    })

    assert result is not None
    assert result.source == "jsearch_other"
    assert result.location == "Remote"
