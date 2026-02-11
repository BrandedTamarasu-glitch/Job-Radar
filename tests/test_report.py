"""Tests for dual-format report generation."""

import pytest
import re
from pathlib import Path
from job_radar.sources import JobResult
from job_radar.report import generate_report


@pytest.fixture
def sample_profile():
    """Sample profile for report generation tests."""
    return {
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


@pytest.fixture
def sample_scored_results():
    """Sample scored results with varied scores."""
    return [
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
            "is_new": False,
        },
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


@pytest.fixture
def sample_manual_urls():
    """Sample manual URL list."""
    return [
        {
            "source": "Indeed",
            "title": "Senior Python Developer",
            "url": "https://indeed.com/jobs?q=Senior+Python+Developer",
        },
        {
            "source": "LinkedIn",
            "title": "Backend Engineer",
            "url": "https://linkedin.com/jobs/search?keywords=Backend+Engineer",
        },
    ]


def test_generate_report_returns_dict(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that generate_report returns dict with correct keys."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice", "HN Hiring", "RemoteOK"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    assert isinstance(result, dict)
    assert "markdown" in result
    assert "html" in result
    assert "stats" in result

    # Verify stats structure
    stats = result["stats"]
    assert "total" in stats
    assert "new" in stats
    assert "high_score" in stats


def test_generate_report_creates_both_files(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that both Markdown and HTML files are created."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice", "HN Hiring"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    # Check files exist
    md_path = Path(result["markdown"])
    html_path = Path(result["html"])

    assert md_path.exists()
    assert html_path.exists()
    assert md_path.suffix == ".md"
    assert html_path.suffix == ".html"


def test_html_report_contains_bootstrap(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report includes Bootstrap CDN and responsive metadata."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    assert "bootstrap" in html_content.lower()
    assert "data-bs-theme" in html_content
    assert 'name="viewport"' in html_content
    assert 'name="color-scheme"' in html_content


def test_html_report_contains_job_data(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report includes profile name, job titles, and score badges."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Check profile name
    assert "Jane Developer" in html_content

    # Check job titles appear
    assert "Senior Python Engineer" in html_content
    assert "Backend Developer" in html_content

    # Check score badges exist (Bootstrap badge classes)
    assert "bg-success" in html_content or "bg-warning" in html_content or "bg-secondary" in html_content


def test_html_report_escapes_html_entities(tmp_path):
    """Test that HTML entities are properly escaped to prevent XSS."""
    profile = {
        "name": "<script>alert('xss')</script>",
        "target_titles": ["Developer"],
        "core_skills": ["Python"],
        "level": "senior",
        "years_experience": 5,
        "location": "Remote",
        "arrangement": ["remote"],
    }

    scored_results = [
        {
            "job": JobResult(
                title="Test Job",
                company="TestCo",
                location="Remote",
                arrangement="remote",
                salary="$100k",
                date_posted="2026-02-08",
                description="Test description",
                url="https://example.com",
                source="Test",
            ),
            "score": {
                "overall": 3.5,
                "recommendation": "Good",
                "components": {
                    "skill_match": {"ratio": "1/1", "matched_core": ["Python"], "matched_secondary": []},
                    "title_relevance": {"reason": "Match"},
                    "seniority": {"reason": "Good"},
                    "response": {"likelihood": "High", "reason": "Good"},
                },
            },
            "is_new": True,
        }
    ]

    result = generate_report(
        profile=profile,
        scored_results=scored_results,
        manual_urls=[],
        sources_searched=["Test"],
        from_date="2026-02-08",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Check that script tags are escaped
    assert "&lt;script&gt;" in html_content
    assert "<script>alert" not in html_content


def test_markdown_report_still_generated(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that Markdown report maintains expected format (no regression)."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    md_content = Path(result["markdown"]).read_text()

    assert md_content.startswith("# Job Search Results")
    assert "## Candidate Profile Summary" in md_content
    assert "## All Results" in md_content


def test_file_naming_uses_timestamp(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that filenames use jobs_YYYY-MM-DD_HH-MM format."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    md_filename = Path(result["markdown"]).name
    html_filename = Path(result["html"]).name

    # Check timestamp format: jobs_YYYY-MM-DD_HH-MM
    timestamp_pattern = r"jobs_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}"

    assert re.match(timestamp_pattern + r"\.md$", md_filename)
    assert re.match(timestamp_pattern + r"\.html$", html_filename)


def test_report_stats_accuracy(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that stats accurately reflect the filtered results."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
        min_score=2.8,
    )

    stats = result["stats"]

    # All 3 results have score >= 2.8
    assert stats["total"] == 3

    # 2 are marked is_new=True (indices 0 and 2)
    assert stats["new"] == 2

    # 2 have score >= 3.5 (indices 0 and 1)
    assert stats["high_score"] == 2


def test_empty_results_generates_reports(sample_profile, sample_manual_urls, tmp_path):
    """Test that empty results still generates both reports."""
    result = generate_report(
        profile=sample_profile,
        scored_results=[],
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    # Check files created
    assert Path(result["markdown"]).exists()
    assert Path(result["html"]).exists()

    # Check HTML contains "No results" message
    html_content = Path(result["html"]).read_text()
    assert "No results" in html_content or "no results" in html_content.lower()


def test_generate_report_creates_output_dir(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that output directory is created if it doesn't exist."""
    nested_dir = tmp_path / "nested" / "output" / "dir"

    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(nested_dir),
    )

    # Check directory was created
    assert nested_dir.exists()
    assert nested_dir.is_dir()

    # Check files exist in the nested directory
    assert Path(result["markdown"]).exists()
    assert Path(result["html"]).exists()


def test_html_report_contains_copy_buttons(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report contains copy buttons for individual jobs and batch copy all button."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Check for individual copy buttons
    assert "copy-btn" in html_content
    assert "Copy URL" in html_content or "Copy" in html_content

    # Check for Copy All Recommended button
    assert "copy-all-btn" in html_content
    assert "Copy All Recommended URLs" in html_content


def test_html_report_contains_data_attributes(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report contains data-job-url and data-score attributes."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Check for data attributes from sample fixtures
    assert "data-job-url" in html_content
    assert 'data-job-url="https://example.com/job/1"' in html_content
    assert "data-score" in html_content
    assert 'data-score="4.2"' in html_content

    # Check for keyboard navigation tabindex
    assert 'tabindex="0"' in html_content


def test_html_report_contains_notyf_cdn(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report includes Notyf CDN for toast notifications."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Check for Notyf CSS and JS CDN links
    assert "notyf.min.css" in html_content
    assert "notyf.min.js" in html_content


def test_html_report_contains_clipboard_javascript(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report includes clipboard JavaScript functionality."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Check for clipboard functions and API usage
    assert "copyToClipboard" in html_content
    assert "navigator.clipboard" in html_content
    assert "execCommand" in html_content  # Fallback for file:// protocol

    # Check for keyboard shortcut event listener
    assert "keydown" in html_content


def test_html_report_contains_keyboard_shortcut_hints(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report includes keyboard shortcut hints."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Check for keyboard hint elements (using <kbd> tags)
    assert "<kbd>C</kbd>" in html_content or "<kbd>A</kbd>" in html_content
    assert "Keyboard:" in html_content


def test_html_report_focus_styles(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report includes focus indicator styles for keyboard navigation."""
    result = generate_report(
        profile=sample_profile,
        scored_results=sample_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Dice"],
        from_date="2026-02-06",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Check for focus-visible styles in CSS
    assert "focus-visible" in html_content
    assert "job-item" in html_content


def test_html_report_copy_button_absent_when_no_url(tmp_path):
    """Test that copy buttons are not added for jobs without URLs."""
    profile = {
        "name": "Test User",
        "target_titles": ["Developer"],
        "core_skills": ["Python"],
        "level": "senior",
        "years_experience": 5,
        "location": "Remote",
        "arrangement": ["remote"],
    }

    # Create a job result with empty URL
    scored_results = [
        {
            "job": JobResult(
                title="Test Job",
                company="TestCo",
                location="Remote",
                arrangement="remote",
                salary="$100k",
                date_posted="2026-02-08",
                description="Test description",
                url="",  # Empty URL
                source="Test",
            ),
            "score": {
                "overall": 4.0,
                "recommendation": "Strong match",
                "components": {
                    "skill_match": {"ratio": "1/1", "matched_core": ["Python"], "matched_secondary": []},
                    "title_relevance": {"reason": "Match"},
                    "seniority": {"reason": "Good"},
                    "response": {"likelihood": "High", "reason": "Good"},
                },
            },
            "is_new": True,
        }
    ]

    result = generate_report(
        profile=profile,
        scored_results=scored_results,
        manual_urls=[],
        sources_searched=["Test"],
        from_date="2026-02-08",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )

    html_content = Path(result["html"]).read_text()

    # Verify no empty data-job-url attributes
    assert 'data-job-url=""' not in html_content


def test_html_report_no_copy_all_button_when_no_recommended(sample_profile, tmp_path):
    """Test that Copy All button does not appear when there are no recommended jobs."""
    # Create only low-scored results (below 3.5 threshold)
    low_scored_results = [
        {
            "job": JobResult(
                title="Junior Developer",
                company="TestCo",
                location="Remote",
                arrangement="remote",
                salary="$80k",
                date_posted="2026-02-08",
                description="Entry level position",
                url="https://example.com/job/low",
                source="Test",
            ),
            "score": {
                "overall": 2.9,
                "recommendation": "Below threshold",
                "components": {
                    "skill_match": {"ratio": "1/3", "matched_core": ["Python"], "matched_secondary": []},
                    "title_relevance": {"reason": "Mismatch"},
                    "seniority": {"reason": "Too junior"},
                    "response": {"likelihood": "Low", "reason": "Poor fit"},
                },
            },
            "is_new": True,
        }
    ]

    result = generate_report(
        profile=sample_profile,
        scored_results=low_scored_results,
        manual_urls=[],
        sources_searched=["Test"],
        from_date="2026-02-08",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
        min_score=2.0,  # Lower threshold to include the low-scored result
    )

    html_content = Path(result["html"]).read_text()

    # Verify Copy All button element doesn't appear (no recommended jobs)
    # The button element should not be in the HTML (JavaScript/CSS may still reference it)
    assert '<button class="btn btn-primary copy-all-btn"' not in html_content
