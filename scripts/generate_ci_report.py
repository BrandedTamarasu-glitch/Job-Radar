#!/usr/bin/env python3
"""
Generate a realistic HTML report for CI accessibility testing.

This script creates a sample report with jobs spanning all score tiers:
- Hero tier (score >= 4.0): Strong match
- Recommended tier (score 3.5-3.9): Good match
- Review tier (score 2.8-3.4): Below threshold

The generated report is used by GitHub Actions to test Lighthouse and axe-core
accessibility compliance.
"""

import os
from pathlib import Path
from glob import glob

from job_radar.report import generate_report
from job_radar.sources import JobResult


def main():
    """Generate CI test report with multi-tier job results."""

    # Create output directory
    output_dir = Path("./ci-report")
    output_dir.mkdir(exist_ok=True)

    # Sample profile matching test fixture pattern
    profile = {
        "name": "Jane Developer",
        "target_titles": ["Senior Python Developer", "Backend Engineer"],
        "core_skills": ["Python", "FastAPI", "PostgreSQL"],
        "level": "senior",
        "years_experience": 7,
        "location": "San Francisco, CA",
        "arrangement": ["remote", "hybrid"],
        "dealbreakers": ["relocation required"],
        "highlights": ["Built API serving 1M requests/day", "Led team of 5 developers"],
    }

    # Sample scored results covering all three tiers
    scored_results = [
        # Hero tier: score >= 4.0
        {
            "job": JobResult(
                title="Senior Python Engineer",
                company="TechCorp",
                location="Remote",
                arrangement="remote",
                salary="$140k-$160k",
                date_posted="2026-02-08",
                description="Build scalable Python services with FastAPI and PostgreSQL",
                url="https://example.com/job/1",
                source="Dice",
                employment_type="Full-time",
                parse_confidence="high",
            ),
            "score": {
                "overall": 4.2,
                "recommendation": "Strong match",
                "components": {
                    "skill_match": {
                        "ratio": "3/3",
                        "matched_core": ["Python", "FastAPI", "PostgreSQL"],
                        "matched_secondary": [],
                    },
                    "title_relevance": {"reason": "Exact match"},
                    "seniority": {"reason": "Matches level"},
                    "response": {"likelihood": "High", "reason": "Good fit"},
                },
            },
            "is_new": True,
        },
        # Recommended tier: score 3.5-3.9
        {
            "job": JobResult(
                title="Backend Developer",
                company="StartupCo",
                location="San Francisco, CA",
                arrangement="hybrid",
                salary="$120k-$140k",
                date_posted="2026-02-07",
                description="Work on backend services with Python and Django",
                url="https://example.com/job/2",
                source="HN Hiring",
                employment_type="Full-time",
                parse_confidence="high",
            ),
            "score": {
                "overall": 3.7,
                "recommendation": "Good match",
                "components": {
                    "skill_match": {
                        "ratio": "1/3",
                        "matched_core": ["Python"],
                        "matched_secondary": [],
                    },
                    "title_relevance": {"reason": "Related"},
                    "seniority": {"reason": "Appropriate level"},
                    "response": {"likelihood": "Medium", "reason": "Decent fit"},
                },
            },
            "is_new": True,
        },
        # Review tier: score 2.8-3.4
        {
            "job": JobResult(
                title="Junior Python Developer",
                company="MegaCorp",
                location="New York, NY",
                arrangement="onsite",
                salary="$80k-$100k",
                date_posted="2026-02-06",
                description="Entry level Python position for new graduates",
                url="https://example.com/job/3",
                source="RemoteOK",
                employment_type="Full-time",
                parse_confidence="high",
            ),
            "score": {
                "overall": 2.8,
                "recommendation": "Below threshold",
                "components": {
                    "skill_match": {
                        "ratio": "1/3",
                        "matched_core": ["Python"],
                        "matched_secondary": [],
                    },
                    "title_relevance": {"reason": "Mismatch"},
                    "seniority": {"reason": "Too junior"},
                    "response": {"likelihood": "Low", "reason": "Poor fit"},
                },
            },
            "is_new": True,
        },
    ]

    # Generate report
    manual_urls = []
    sources_searched = ["CI Test"]

    generate_report(
        profile=profile,
        scored_results=scored_results,
        manual_urls=manual_urls,
        sources_searched=sources_searched,
        output_dir=str(output_dir),
    )

    # Find the generated file (has timestamp: jobs_YYYY-MM-DD_HH-MM.html)
    html_files = list(output_dir.glob("jobs_*.html"))

    if not html_files:
        raise FileNotFoundError(f"No HTML report found in {output_dir}")

    generated_file = html_files[0]
    target_file = output_dir / "index.html"

    # Rename to index.html for Lighthouse CI staticDistDir
    generated_file.rename(target_file)

    print(f"✓ CI report generated: {target_file}")
    print(f"  Hero tier: 1 job (score 4.2)")
    print(f"  Recommended tier: 1 job (score 3.7)")
    print(f"  Review tier: 1 job (score 2.8)")


if __name__ == "__main__":
    main()
