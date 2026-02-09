"""Shared fixtures for all test modules."""

import pytest
from job_radar.sources import JobResult


@pytest.fixture
def sample_profile():
    """Return a sample profile dict matching the structure used by scoring.py."""
    return {
        "core_skills": ["Python", "pytest", "FastAPI"],
        "secondary_skills": ["Docker", "PostgreSQL"],
        "target_titles": ["Senior Python Developer", "Backend Engineer"],
        "level": "senior",
        "years_experience": 7,
        "arrangement": ["remote", "hybrid"],
        "location": "San Francisco, CA",
        "target_market": "SF Bay Area",
        "domain_expertise": ["fintech", "healthcare"],
        "dealbreakers": ["relocation required"],
        "comp_floor": 120000,
    }


@pytest.fixture
def job_factory():
    """Return a factory function that creates JobResult instances with sensible defaults."""
    def _make_job(**kwargs):
        defaults = {
            "title": "Senior Python Developer",
            "company": "TestCorp",
            "location": "Remote",
            "arrangement": "remote",
            "salary": "$120k-$150k",
            "date_posted": "2026-02-08",
            "description": "Build scalable Python services with pytest and FastAPI",
            "url": "https://example.com/job/123",
            "source": "Test",
            "apply_info": "",
            "employment_type": "Full-time",
            "parse_confidence": "high",
        }
        defaults.update(kwargs)
        return JobResult(**defaults)

    return _make_job
