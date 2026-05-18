"""Tests for source API response mappers."""

from job_radar.source_mappers import (
    map_adzuna_to_job_result,
    map_authenticjobs_to_job_result,
    map_hiringcafe_to_job_result,
    map_jobicy_to_job_result,
    map_jsearch_to_job_result,
    map_serpapi_to_job_result,
    map_usajobs_to_job_result,
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


def test_map_usajobs_to_job_result_maps_valid_descriptor():
    result = map_usajobs_to_job_result({
        "MatchedObjectDescriptor": {
            "PositionTitle": "Program Analyst",
            "OrganizationName": "Agency",
            "PositionURI": "https://www.usajobs.gov/job/1",
            "PositionLocationDisplay": "Washington, DC",
            "PositionRemuneration": [{
                "MinimumRange": "80000",
                "MaximumRange": "100000",
            }],
            "UserArea": {"Details": {"JobSummary": "<p>Hybrid policy work</p>"}},
            "PublicationStartDate": "2026-05-18T00:00:00Z",
            "PositionSchedule": [{"Name": "Full-time"}],
        }
    })

    assert result is not None
    assert result.source == "usajobs"
    assert result.salary == "$80,000 - $100,000"
    assert result.date_posted == "2026-05-18"
    assert result.arrangement == "hybrid"


def test_map_usajobs_to_job_result_rejects_missing_required_fields():
    assert map_usajobs_to_job_result({"MatchedObjectDescriptor": {}}) is None


def test_map_serpapi_to_job_result_maps_apply_option():
    result = map_serpapi_to_job_result({
        "title": "Software Engineer",
        "company_name": "Acme",
        "apply_options": [{"link": "https://example.com/apply"}],
        "location": "Austin, Texas, United States",
        "description": "<p>Work from anywhere</p>",
        "detected_extensions": {"work_from_home": True, "schedule_type": "Full-time"},
    })

    assert result is not None
    assert result.source == "serpapi"
    assert result.url == "https://example.com/apply"
    assert result.arrangement == "remote"


def test_map_jobicy_to_job_result_requires_clean_description():
    assert map_jobicy_to_job_result({
        "jobTitle": "Backend Engineer",
        "companyName": "Acme",
        "url": "https://example.com/job",
        "jobDescription": "",
        "jobExcerpt": "",
    }) is None


def test_map_jobicy_to_job_result_maps_salary_range():
    result = map_jobicy_to_job_result({
        "jobTitle": "Backend Engineer",
        "companyName": "Acme",
        "url": "https://example.com/job",
        "jobDescription": "Build APIs",
        "annualSalaryMin": "120000",
        "annualSalaryMax": "150000",
        "salaryCurrency": "USD",
    })

    assert result is not None
    assert result.source == "jobicy"
    assert result.salary == "USD 120,000-150,000/yr"
    assert result.arrangement == "remote"


def test_map_hiringcafe_to_job_result_normalizes_hourly_salary():
    result = map_hiringcafe_to_job_result({
        "title": "Backend Engineer",
        "company": "Acme",
        "url": "https://example.com/job",
        "location": "Remote",
        "description": "Remote API work",
        "salary_min": 75,
        "salary_max": 100,
        "salary_period": "hourly",
    })

    assert result is not None
    assert result.source == "hiringcafe"
    assert result.salary == "$156K - $208K"
    assert result.arrangement == "remote"
