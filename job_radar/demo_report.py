"""No-network demo report generation shared by CLI and GUI."""

from __future__ import annotations

from datetime import date

from job_radar.report import generate_report
from job_radar.scoring import score_job
from job_radar.sources import JobResult, generate_manual_urls


def demo_profile() -> dict:
    """Return a realistic sample profile for report previews."""
    return {
        "name": "Demo Candidate",
        "target_titles": ["Backend Engineer", "Senior Python Developer"],
        "core_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "secondary_skills": ["AWS", "Redis", "Kubernetes"],
        "level": "senior",
        "years_experience": 7,
        "location": "Remote",
        "target_market": "Remote",
        "arrangement": ["remote", "hybrid"],
        "domain_expertise": ["fintech", "developer tools"],
        "highlights": [
            "Built Python APIs serving 1M requests per day",
            "Led migration from monolith to containerized services",
        ],
        "comp_floor": 130000,
        "staffing_preference": "neutral",
    }


def demo_jobs() -> list[JobResult]:
    """Return sample jobs that exercise report tiers and explanations."""
    return [
        JobResult(
            title="Senior Backend Engineer",
            company="Northstar Tools",
            location="Remote",
            arrangement="remote",
            salary="$155k-$180k",
            date_posted="Today",
            description=(
                "Build developer tools with Python, FastAPI, PostgreSQL, Docker, "
                "and AWS on a small remote-first team."
            ),
            url="https://example.com/demo/senior-backend-engineer",
            source="Demo",
            employment_type="Full-time",
            parse_confidence="high",
        ),
        JobResult(
            title="Backend Developer",
            company="LedgerWorks",
            location="Remote",
            arrangement="remote",
            salary="$125k-$145k",
            date_posted="Yesterday",
            description="Maintain fintech APIs using Python, Django, PostgreSQL, and Redis.",
            url="https://example.com/demo/backend-developer",
            source="Demo",
            employment_type="Full-time",
            parse_confidence="high",
        ),
        JobResult(
            title="Platform Engineer",
            company="ScaleOps",
            location="Denver, CO",
            arrangement="hybrid",
            salary="Not listed",
            date_posted="2d ago",
            description="Operate Kubernetes and Docker infrastructure for enterprise services.",
            url="https://example.com/demo/platform-engineer",
            source="Demo",
            employment_type="Full-time",
            parse_confidence="high",
        ),
    ]


def generate_demo_report(output_dir: str | None = None, min_score: float = 2.8) -> dict:
    """Generate a no-network sample report and return report metadata."""
    profile = demo_profile()
    today = date.today().isoformat()

    scored = [
        {"job": job, "score": score_job(job, profile), "is_new": True}
        for job in demo_jobs()
    ]
    scored = [
        result for result in scored
        if not result["score"].get("dealbreaker")
        and result["score"]["overall"] >= min_score
    ]
    scored.sort(key=lambda x: x["score"]["overall"], reverse=True)

    return generate_report(
        profile=profile,
        scored_results=scored,
        manual_urls=generate_manual_urls(profile),
        sources_searched=["Demo"],
        from_date=today,
        to_date=today,
        output_dir=output_dir,
        tracker_stats=None,
        min_score=min_score,
    )
