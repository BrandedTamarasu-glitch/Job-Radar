"""Tests for source data models."""

from job_radar.source_models import JobResult


def test_job_result_hash_uses_title_company_and_source():
    job = JobResult(
        title="Software Engineer",
        company="Acme",
        location="Remote",
        arrangement="remote",
        salary="Not specified",
        date_posted="2026-05-18",
        description="Build products",
        url="https://example.com/job",
        source="dice",
    )

    assert hash(job) == hash(("Software Engineer", "Acme", "dice"))
