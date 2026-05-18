"""Tests for source API response mappers."""

from job_radar.source_mappers import map_adzuna_to_job_result


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
