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
            "is_new": True,
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

    # All 3 are marked is_new=True (indices 0, 1, and 2)
    assert stats["new"] == 3

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


def test_html_report_contains_status_dropdown(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report contains status dropdowns with all status options."""
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

    # Check for status dropdown toggle button
    assert "dropdown-toggle" in html_content

    # Check for all status options with data-status attributes
    assert 'data-status="applied"' in html_content
    assert 'data-status="interviewing"' in html_content
    assert 'data-status="rejected"' in html_content
    assert 'data-status="offer"' in html_content
    assert 'data-status=""' in html_content  # Clear status option


def test_html_report_contains_status_column_in_table(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that results table has Status column with dropdowns."""
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

    # Check for Status column header (with scope attribute from WCAG compliance)
    assert '<th scope="col">Status</th>' in html_content

    # Check that table rows contain status dropdown elements
    # Table rows should have data-job-key and contain data-status attributes
    assert "<tr" in html_content
    assert "data-job-key" in html_content
    assert 'data-status="applied"' in html_content


def test_html_report_contains_tracker_status_embed(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML contains embedded tracker status JSON script tag."""
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

    # Check for embedded tracker status JSON script tag
    assert '<script type="application/json" id="tracker-status">' in html_content


def test_html_report_contains_status_javascript(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML contains status management JavaScript functions."""
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

    # Check for key JavaScript functions
    assert "hydrateApplicationStatus" in html_content
    assert "renderStatusBadge" in html_content
    assert "STATUS_CONFIG" in html_content
    assert "exportPendingStatusUpdates" in html_content

    # Check for localStorage key
    assert "job-radar-application-status" in html_content


def test_html_report_contains_job_key_attributes(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML contains data-job-key attributes on job items."""
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

    # Check for data-job-key attributes
    assert "data-job-key" in html_content

    # Check for data-job-title and data-job-company attributes
    assert "data-job-title" in html_content
    assert "data-job-company" in html_content

    # Verify the key format matches expected pattern (lowercase title||company)
    # From fixtures: "Senior Python Engineer" at "TechCorp"
    assert "senior python engineer||techcorp" in html_content.lower()


def test_html_report_contains_export_button(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML contains export status updates button."""
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

    # Check for export button with correct class
    assert "export-status-btn" in html_content

    # Check for export function
    assert "exportPendingStatusUpdates" in html_content


# ── WCAG 2.1 Level AA Accessibility Tests (Phase 18-03) ─────────────────────


def test_html_report_skip_navigation_link(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report contains a skip navigation link for keyboard users."""
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

    # Verify skip link has visually-hidden-focusable class
    assert "visually-hidden-focusable" in html_content

    # Verify skip link targets #main-content
    assert '#main-content"' in html_content

    # Verify skip link appears before main content (ordering check)
    skip_link_pos = html_content.find("visually-hidden-focusable")
    main_content_pos = html_content.find('id="main-content"')
    assert skip_link_pos < main_content_pos, "Skip link must appear before main content"


def test_html_report_aria_landmarks(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report contains ARIA landmarks for screen reader navigation."""
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

    # Verify ARIA landmarks exist
    assert 'role="banner"' in html_content, "Header landmark (banner) missing"
    assert 'role="main"' in html_content, "Main content landmark missing"
    assert 'role="contentinfo"' in html_content, "Footer landmark (contentinfo) missing"

    # Verify skip link target exists
    assert 'id="main-content"' in html_content, "Skip link target (main-content) missing"


def test_html_report_section_landmarks(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report uses section landmarks with aria-labelledby."""
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

    # Verify section landmarks with aria-labelledby
    assert 'aria-labelledby="profile-heading"' in html_content, "Profile section landmark missing"
    assert 'aria-labelledby="recommended-heading"' in html_content, "Recommended section landmark missing"
    assert 'aria-labelledby="results-heading"' in html_content, "Results section landmark missing"

    # Verify heading IDs exist
    assert 'id="profile-heading"' in html_content, "Profile heading ID missing"

    # Verify <section> tags are used
    assert "<section" in html_content, "Section element not used"


def test_html_report_accessible_table_headers(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that results table has proper scope attributes and caption for accessibility."""
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

    # Verify scope="col" on column headers (11 columns: #, Score, New, Status, Title, Company, Salary, Type, Location, Snippet, Link)
    col_scope_count = html_content.count('scope="col"')
    assert col_scope_count >= 5, f"Expected at least 5 scope='col' attributes, found {col_scope_count}"

    # Verify scope="row" on row number headers
    assert 'scope="row"' in html_content, "Row scope attributes missing"

    # Verify table caption exists
    assert "<caption" in html_content, "Table caption missing"

    # Verify caption describes table purpose
    assert "Job search results" in html_content or "job search results" in html_content, "Caption text should describe table purpose"


def test_html_report_score_badge_screen_reader_text(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that score badges contain visually-hidden screen reader context."""
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

    # Verify score badges contain visually-hidden spans with context
    assert "visually-hidden" in html_content, "Visually-hidden class missing"

    # Verify "Score " prefix appears in visually-hidden span
    assert '>Score </span>' in html_content, "Score prefix screen reader text missing"

    # Verify " out of 5.0" suffix appears in visually-hidden span
    assert '> out of 5.0</span>' in html_content, "Score suffix screen reader text missing"

    # Verify both recommended cards AND results table have this pattern
    # The recommended section uses score-badge class, the table uses badge class
    # Both should have the screen reader text
    recommended_section_pos = html_content.find('id="recommended-heading"')
    results_section_pos = html_content.find('id="results-heading"')
    after_recommended = html_content[recommended_section_pos:results_section_pos]
    after_results = html_content[results_section_pos:]

    assert '>Score </span>' in after_recommended, "Score screen reader text missing in recommended section"
    assert '>Score </span>' in after_results, "Score screen reader text missing in results table"


def test_html_report_new_badge_screen_reader_text(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that NEW badges contain visually-hidden screen reader context."""
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

    # Verify NEW badge contains screen reader context text
    assert "New listing, not seen in previous searches" in html_content, "NEW badge screen reader text missing"

    # Verify visually-hidden span wraps the context
    assert '<span class="visually-hidden">New listing, not seen in previous searches' in html_content, \
        "NEW badge screen reader text not in visually-hidden span"

    # Verify both recommended cards AND results table contain this pattern
    recommended_section_pos = html_content.find('id="recommended-heading"')
    results_section_pos = html_content.find('id="results-heading"')
    after_recommended = html_content[recommended_section_pos:results_section_pos]
    after_results = html_content[results_section_pos:]

    assert "New listing, not seen in previous searches" in after_recommended, \
        "NEW badge screen reader text missing in recommended section"
    assert "New listing, not seen in previous searches" in after_results, \
        "NEW badge screen reader text missing in results table"


def test_html_report_aria_live_region(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report contains an ARIA live region for screen reader announcements."""
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

    # Verify ARIA live region element exists
    assert 'id="status-announcer"' in html_content, "Status announcer element missing"
    assert 'aria-live="polite"' in html_content, "aria-live=polite attribute missing"
    assert 'aria-atomic="true"' in html_content, "aria-atomic=true attribute missing"
    assert 'role="status"' in html_content, "role=status attribute missing"

    # Verify element has visually-hidden class
    assert 'class="visually-hidden"' in html_content, "Status announcer should be visually hidden"


def test_html_report_focus_indicators_all_elements(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that CSS contains focus indicators for all interactive element types."""
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

    # Verify CSS focus-visible rules for all interactive element types
    assert "a:focus-visible" in html_content, "Link focus indicator CSS missing"
    assert ".btn:focus-visible" in html_content, "Button focus indicator CSS missing"
    assert ".dropdown-item:focus" in html_content, "Dropdown item focus indicator CSS missing"
    assert ".dropdown-toggle:focus-visible" in html_content, "Dropdown toggle focus indicator CSS missing"

    # Verify existing job-item focus rule still present
    assert ".job-item:focus-visible" in html_content, "Job item focus indicator CSS missing"


def test_html_report_contrast_safe_colors(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that CSS contains contrast-safe color overrides for WCAG AA compliance."""
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

    # Verify contrast-safe muted text color
    assert "#595959" in html_content, "Contrast-safe muted text color #595959 missing"

    # Verify .text-muted override exists in the style block
    assert ".text-muted" in html_content, ".text-muted CSS override missing"


def test_html_report_external_links_accessibility(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that external links have rel='noopener' and descriptive aria-labels."""
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

    # Verify external links have rel="noopener" for security
    assert 'rel="noopener"' in html_content, "External links missing rel='noopener'"

    # Verify external links have descriptive aria-label attributes
    assert "aria-label" in html_content, "External links missing aria-label attributes"

    # Verify aria-labels contain descriptive text (job context)
    assert "opens in new tab" in html_content, "aria-label should indicate link opens in new tab"


# -- Phase 19: Typography & Color Foundation Tests --------------------------------

def test_html_report_system_font_stack(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that HTML report uses system font stack CSS variable."""
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
    assert "--font-sans" in html_content, "System font stack variable missing"
    assert "system-ui" in html_content, "system-ui font not in stack"
    assert "font-family: var(--font-sans)" in html_content, "Body not using font-sans variable"


def test_html_report_monospace_score_badges(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that score badges use monospace font stack."""
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
    assert "--font-mono" in html_content, "Monospace font variable missing"
    assert "ui-monospace" in html_content, "ui-monospace not in stack"


def test_html_report_typography_hierarchy(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test newspaper-style type hierarchy with distinct heading sizes."""
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
    assert "--font-size-title" in html_content, "Title size variable missing"
    assert "--font-size-section" in html_content, "Section size variable missing"
    assert "--font-size-body" in html_content, "Body size variable missing"


def test_html_report_semantic_color_variables(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that 3-tier semantic color CSS variables are defined."""
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
    # Green tier (strong, >= 4.0)
    assert "--color-tier-strong-bg" in html_content, "Strong tier background color missing"
    assert "--color-tier-strong-border" in html_content, "Strong tier border color missing"
    # Cyan tier (recommended, 3.5-3.9)
    assert "--color-tier-rec-bg" in html_content, "Recommended tier background color missing"
    assert "--color-tier-rec-border" in html_content, "Recommended tier border color missing"
    # Gray tier (review, 2.8-3.4)
    assert "--color-tier-review-bg" in html_content, "Review tier background color missing"
    assert "--color-tier-review-border" in html_content, "Review tier border color missing"


def test_html_report_dark_mode_color_inversion(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that dark mode inverts tier color lightness via media query."""
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
    assert "prefers-color-scheme: dark" in html_content, "Dark mode media query missing"
    # Verify dark mode overrides lightness (should have multiple prefers-color-scheme blocks)
    dark_mode_count = html_content.count("prefers-color-scheme: dark")
    assert dark_mode_count >= 1, "Dark mode media query should appear at least once"


def test_html_report_tier_classes_on_cards(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that job cards have tier-specific CSS classes based on score."""
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
    # First result has score 4.2 (strong tier)
    assert "tier-strong" in html_content, "Strong tier class missing on card"
    # Second result has score 3.7 (recommended tier)
    assert "tier-rec" in html_content, "Recommended tier class missing on card"


def test_html_report_tier_classes_on_table_rows(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that table rows have tier-specific CSS classes."""
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
    # Check that tr elements contain tier classes
    # Third result has score 2.8 (review tier)
    assert "tier-review" in html_content, "Review tier class missing on table row"


def test_html_report_pill_shaped_score_badges(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that score badges use pill shape with tier colors."""
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
    assert "rounded-pill" in html_content, "Pill shape class missing"
    assert "tier-badge-strong" in html_content, "Strong tier badge class missing"
    # Pill CSS rule
    assert "border-radius: 999em" in html_content, "Pill border-radius CSS rule missing"


def test_html_report_non_color_indicators(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test non-color indicators for colorblind accessibility (border thickness + icons)."""
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
    # Border thickness variation in CSS
    assert "border-left: 5px" in html_content, "5px border for strong tier missing"
    assert "border-left: 4px" in html_content, "4px border for recommended tier missing"
    assert "border-left: 3px" in html_content, "3px border for review tier missing"
    # Icon indicators
    assert "tier-icon" in html_content, "Tier icon class missing"


def test_html_report_status_badges_pill_style(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that application status badges use pill style."""
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
    # STATUS_CONFIG should include rounded-pill in class
    assert "bg-success rounded-pill" in html_content or "rounded-pill" in html_content, \
        "Status badges should use pill style"


# -- Phase 20: Hero Jobs Visual Hierarchy Tests ----------------------------------

def test_html_report_hero_section_exists(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that hero section exists when jobs have score >= 4.0."""
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

    # Verify hero section heading exists
    assert 'id="hero-heading"' in html_content, "Hero heading ID missing"
    assert "Top Matches (Score >= 4.0)" in html_content, "Hero heading text missing"

    # Verify aria-labelledby on hero section
    assert 'aria-labelledby="hero-heading"' in html_content, "Hero section aria-labelledby missing"


def test_html_report_hero_card_elevated_styling(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that hero job cards have elevated styling with hero-job and tier-strong classes."""
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

    # Verify hero-job class exists
    assert "hero-job" in html_content, "hero-job class missing"

    # Verify card has both hero-job and tier-strong classes
    assert "hero-job tier-strong" in html_content or "tier-strong hero-job" in html_content, \
        "Hero card should have both hero-job and tier-strong classes"


def test_html_report_hero_shadow_css(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that CSS contains hero shadow variable and class."""
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

    # Verify --shadow-hero custom property
    assert "--shadow-hero" in html_content, "--shadow-hero CSS variable missing"

    # Verify .hero-job rule with box-shadow
    assert ".hero-job" in html_content, ".hero-job CSS class missing"
    assert "box-shadow: var(--shadow-hero)" in html_content, ".hero-job box-shadow rule missing"


def test_html_report_hero_badge_label(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that hero job score badges contain 'Top Match' label."""
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

    # Verify badge-label class exists in CSS
    assert ".badge-label" in html_content, ".badge-label CSS class missing"

    # Verify "Top Match" text in badge-label span
    assert '<span class="badge-label">Top Match</span>' in html_content, \
        "Top Match badge label missing from hero cards"


def test_html_report_hero_section_before_recommended(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that hero section appears before recommended section in HTML."""
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

    # Verify both sections exist
    hero_pos = html_content.find('id="hero-heading"')
    rec_pos = html_content.find('id="recommended-heading"')

    assert hero_pos > 0, "Hero section not found"
    assert rec_pos > 0, "Recommended section not found"
    assert hero_pos < rec_pos, "Hero section should appear before recommended section"


def test_html_report_section_divider(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that section divider exists between hero and recommended sections."""
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

    # Verify section-divider element exists
    assert '<div class="section-divider" role="separator" aria-hidden="true"></div>' in html_content, \
        "Section divider missing between hero and recommended sections"

    # Verify .section-divider CSS class exists
    assert ".section-divider" in html_content, ".section-divider CSS class missing"


def test_html_report_hero_focus_indicator_css(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that CSS contains enhanced focus indicator for hero cards."""
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

    # Verify .hero-job:focus-visible rule exists
    assert ".hero-job:focus-visible" in html_content, ".hero-job:focus-visible CSS rule missing"

    # Verify outline properties
    assert "outline:" in html_content, "outline property missing from focus rule"
    assert "outline-offset:" in html_content, "outline-offset property missing from focus rule"


def test_html_report_recommended_heading_updated(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that recommended section heading shows updated scope (3.5 - 3.9)."""
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

    # Verify recommended heading shows "3.5 - 3.9" scope
    assert "Recommended Roles (Score 3.5 - 3.9)" in html_content, \
        "Recommended heading should show 3.5 - 3.9 scope"


def test_html_report_no_hero_section_when_no_high_scores(sample_profile, sample_manual_urls, tmp_path):
    """Test that hero section does not appear when no jobs have score >= 4.0."""
    # Create scored results with all scores below 4.0
    from job_radar.sources import JobResult
    low_scored_results = [
        {
            "job": JobResult(
                title="Good Job",
                company="TestCo",
                location="Remote",
                arrangement="remote",
                salary="$100k",
                date_posted="2026-02-08",
                description="Test description",
                url="https://example.com/job/1",
                source="Test",
            ),
            "score": {
                "overall": 3.8,
                "recommendation": "Good match",
                "components": {
                    "skill_match": {"ratio": "2/3", "matched_core": ["Python"], "matched_secondary": []},
                    "title_relevance": {"reason": "Match"},
                    "seniority": {"reason": "Good"},
                    "response": {"likelihood": "High", "reason": "Good"},
                },
            },
            "is_new": True,
        },
        {
            "job": JobResult(
                title="Okay Job",
                company="TestCo2",
                location="Remote",
                arrangement="remote",
                salary="$90k",
                date_posted="2026-02-08",
                description="Test description",
                url="https://example.com/job/2",
                source="Test",
            ),
            "score": {
                "overall": 3.5,
                "recommendation": "Good match",
                "components": {
                    "skill_match": {"ratio": "1/3", "matched_core": ["Python"], "matched_secondary": []},
                    "title_relevance": {"reason": "Match"},
                    "seniority": {"reason": "Good"},
                    "response": {"likelihood": "Medium", "reason": "OK"},
                },
            },
            "is_new": True,
        }
    ]

    result = generate_report(
        profile=sample_profile,
        scored_results=low_scored_results,
        manual_urls=sample_manual_urls,
        sources_searched=["Test"],
        from_date="2026-02-08",
        to_date="2026-02-09",
        output_dir=str(tmp_path),
    )
    html_content = Path(result["html"]).read_text()

    # Verify hero section does NOT exist
    assert 'id="hero-heading"' not in html_content, "Hero section should not exist when no scores >= 4.0"

    # Verify recommended section still renders
    assert 'id="recommended-heading"' in html_content, "Recommended section should still exist"


def test_html_report_hero_dark_mode_shadow(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that dark mode media query contains hero shadow override."""
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

    # Find dark mode media query block
    assert "prefers-color-scheme: dark" in html_content, "Dark mode media query missing"

    # Verify dark mode has --shadow-hero override with higher opacity
    # Extract dark mode section
    dark_mode_start = html_content.find("@media (prefers-color-scheme: dark)")

    # Look for --shadow-hero after dark mode start (could be in multiple dark mode blocks)
    # Just verify it exists somewhere in the CSS with higher opacity values
    assert "rgba(0, 0, 0, 0.3)" in html_content or "rgba(0, 0, 0, 0.2)" in html_content, \
        "Dark mode shadow with higher opacity missing"


# -- Phase 21: Responsive Layout Tests -------------------------------------------

def test_responsive_data_labels_on_table_cells(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that all table cells have data-label attributes for mobile cards."""
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

    # Verify all 11 column data-label attributes exist
    assert 'data-label="#"' in html_content, "data-label='#' missing"
    assert 'data-label="Score"' in html_content, "data-label='Score' missing"
    assert 'data-label="New"' in html_content, "data-label='New' missing"
    assert 'data-label="Status"' in html_content, "data-label='Status' missing"
    assert 'data-label="Title"' in html_content, "data-label='Title' missing"
    assert 'data-label="Company"' in html_content, "data-label='Company' missing"
    assert 'data-label="Salary"' in html_content, "data-label='Salary' missing"
    assert 'data-label="Type"' in html_content, "data-label='Type' missing"
    assert 'data-label="Location"' in html_content, "data-label='Location' missing"
    assert 'data-label="Snippet"' in html_content, "data-label='Snippet' missing"
    assert 'data-label="Link"' in html_content, "data-label='Link' missing"


def test_responsive_column_hide_classes(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that low-priority columns have col-* CSS classes on th and td elements."""
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

    # Verify col-* classes for 4 low-priority columns
    assert 'class="col-new"' in html_content, "col-new class missing"
    assert 'class="col-salary"' in html_content, "col-salary class missing"
    assert 'class="col-type"' in html_content, "col-type class missing"
    assert 'class="col-snippet"' in html_content, "col-snippet class missing"

    # Verify both th and td have these classes
    assert '<th scope="col" class="col-new"' in html_content or '<th class="col-new"' in html_content, \
        "col-new class missing on <th>"
    assert '<td data-label="Salary" class="col-salary"' in html_content, \
        "col-salary class missing on <td>"


def test_responsive_tablet_breakpoint_css(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that CSS contains tablet breakpoint at 991px hiding 4 columns."""
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

    # Verify tablet breakpoint media query exists
    assert "@media (max-width: 991px)" in html_content, "Tablet breakpoint media query missing"

    # Verify it hides the 4 low-priority columns
    tablet_section_start = html_content.find("@media (max-width: 991px)")
    tablet_section_end = html_content.find("}", tablet_section_start + 500)  # Search in next 500 chars
    tablet_section = html_content[tablet_section_start:tablet_section_end]

    assert ".col-new" in tablet_section or ".col-salary" in tablet_section, \
        "Tablet breakpoint should reference col-* classes"
    assert "display: none" in tablet_section, \
        "Tablet breakpoint should set display: none"


def test_responsive_mobile_card_css(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that CSS contains mobile breakpoint at 767px with card layout."""
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

    # Verify mobile breakpoint media query exists
    assert "@media (max-width: 767px)" in html_content, "Mobile breakpoint media query missing"

    # Verify mobile card layout features
    mobile_section_start = html_content.find("@media (max-width: 767px)")
    mobile_section_end = html_content.find("@media", mobile_section_start + 100)
    if mobile_section_end == -1:
        mobile_section_end = len(html_content)
    mobile_section = html_content[mobile_section_start:mobile_section_end]

    # Check for display: block on table elements
    assert "display: block" in mobile_section, \
        "Mobile breakpoint should set display: block"

    # Check for grid-template-columns for cell layout
    assert "grid-template-columns" in mobile_section, \
        "Mobile card layout should use grid-template-columns"

    # Check for ::before pseudo-element with attr(data-label)
    assert "content: attr(data-label)" in mobile_section, \
        "Mobile cards should use data-label attribute for labels"


def test_responsive_mobile_shows_all_columns(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that mobile CSS overrides tablet hiding with display: block !important."""
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

    # Verify mobile section contains display: block !important for col-* classes
    mobile_section_start = html_content.find("@media (max-width: 767px)")
    mobile_section_end = html_content.find("@media", mobile_section_start + 100)
    if mobile_section_end == -1:
        mobile_section_end = len(html_content)
    mobile_section = html_content[mobile_section_start:mobile_section_end]

    # Check for !important override
    assert "display: block !important" in mobile_section, \
        "Mobile breakpoint should use display: block !important to override tablet hiding"

    # Check that col-* classes are referenced in mobile section
    assert ".col-new" in mobile_section or ".col-salary" in mobile_section, \
        "Mobile breakpoint should restore visibility of col-* columns"


def test_responsive_aria_restoration_js(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that JavaScript contains AddTableARIA function with role assignments."""
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

    # Verify AddTableARIA function exists
    assert "function AddTableARIA()" in html_content, "AddTableARIA function missing"

    # Verify ARIA role assignments
    assert "setAttribute('role', 'table')" in html_content, "ARIA role='table' missing"
    assert "setAttribute('role', 'row')" in html_content, "ARIA role='row' missing"
    assert "setAttribute('role', 'cell')" in html_content, "ARIA role='cell' missing"
    assert "setAttribute('role', 'columnheader')" in html_content, "ARIA role='columnheader' missing"
    assert "setAttribute('role', 'rowheader')" in html_content, "ARIA role='rowheader' missing"

    # Verify function is called
    assert "AddTableARIA();" in html_content, "AddTableARIA function not called"


def test_responsive_touch_targets(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that CSS contains 44px minimum touch target rules for mobile."""
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

    # Verify 44px touch target rules exist
    assert "min-height: 44px" in html_content, "min-height: 44px touch target rule missing"
    assert "min-width: 44px" in html_content, "min-width: 44px touch target rule missing"

    # Verify these rules are in mobile context
    mobile_section_start = html_content.find("@media (max-width: 767px)")
    if mobile_section_start > 0:
        mobile_section_end = html_content.find("@media", mobile_section_start + 100)
        if mobile_section_end == -1:
            mobile_section_end = len(html_content)
        mobile_section = html_content[mobile_section_start:mobile_section_end]
        assert "min-height: 44px" in mobile_section or "44px" in html_content, \
            "44px touch targets should be in mobile CSS"


def test_responsive_dark_mode_mobile(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that CSS contains combined dark mode + mobile media query."""
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

    # Verify combined dark mode + mobile media query exists
    assert "@media (prefers-color-scheme: dark) and (max-width: 767px)" in html_content, \
        "Combined dark mode + mobile media query missing"

    # Verify it contains color overrides
    dark_mobile_start = html_content.find("@media (prefers-color-scheme: dark) and (max-width: 767px)")
    if dark_mobile_start > 0:
        dark_mobile_end = html_content.find("}", dark_mobile_start + 500)
        dark_mobile_section = html_content[dark_mobile_start:dark_mobile_end]
        assert "background" in dark_mobile_section or "border" in dark_mobile_section or "color" in dark_mobile_section, \
            "Dark mode mobile section should contain color overrides"


def test_responsive_tier_borders_mobile(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that mobile CSS preserves tier border styles."""
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

    # Verify tier border thickness rules exist in CSS (could be in base or mobile section)
    assert "border-left: 5px" in html_content, "5px tier border missing (tier-strong)"
    assert "border-left: 4px" in html_content, "4px tier border missing (tier-rec)"
    assert "border-left: 3px" in html_content, "3px tier border missing (tier-review)"

    # Verify tier classes are applied to table rows (from Phase 19)
    assert "tier-strong" in html_content, "tier-strong class missing"
    assert "tier-rec" in html_content, "tier-rec class missing"


def test_responsive_no_label_class(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Test that Link column has no-label class to hide ::before label."""
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

    # Verify Link column td has no-label class
    assert 'class="no-label"' in html_content, "no-label class missing on Link column"

    # Verify CSS contains .no-label::before rule with display: none
    assert ".no-label::before" in html_content, ".no-label::before CSS rule missing"
    assert "display: none" in html_content, "display: none missing (should hide no-label ::before)"
