"""Tests for API source integration covering mappers, text utilities, fetchers, and pipeline."""

import pytest
from job_radar.sources import (
    map_adzuna_to_job_result,
    map_authenticjobs_to_job_result,
    strip_html_and_normalize,
    parse_location_to_city_state,
    fetch_adzuna,
    fetch_authenticjobs,
    build_search_queries,
    JobResult,
)


# ==============================================================================
# Adzuna Mapper Tests
# ==============================================================================

def test_map_adzuna_valid_job():
    """Valid Adzuna item maps to JobResult with all fields."""
    item = {
        "title": "Senior Software Engineer",
        "company": {"display_name": "Google Inc"},
        "redirect_url": "https://example.com/job/123",
        "salary_min": 80000.0,
        "salary_max": 120000.0,
        "location": {"display_name": "San Francisco, California, United States"},
        "description": "<p>Great &amp; exciting <b>role</b> working with Python</p>",
        "created": "2026-02-10",
        "contract_type": "permanent",
        "contract_time": "full_time",
    }

    result = map_adzuna_to_job_result(item)

    assert result is not None
    assert result.title == "Senior Software Engineer"
    assert result.company == "Google Inc"
    assert result.location == "San Francisco, CA"
    assert result.salary == "$80,000 - $120,000"
    assert result.salary_min == 80000.0
    assert result.salary_max == 120000.0
    assert result.salary_currency == "USD"
    assert "Great & exciting role" in result.description
    assert "<p>" not in result.description
    assert "&amp;" not in result.description
    assert result.url == "https://example.com/job/123"
    assert result.source == "adzuna"
    assert result.employment_type == "Permanent, Full-time"
    assert result.parse_confidence == "high"


def test_map_adzuna_missing_title_returns_none():
    """Item with empty title returns None (strict validation)."""
    item = {
        "title": "",
        "company": {"display_name": "Google Inc"},
        "redirect_url": "https://example.com/job/123",
    }

    result = map_adzuna_to_job_result(item)

    assert result is None


def test_map_adzuna_missing_company_returns_none():
    """Item with missing company returns None."""
    item = {
        "title": "Software Engineer",
        "company": {},  # Empty company object
        "redirect_url": "https://example.com/job/123",
    }

    result = map_adzuna_to_job_result(item)

    assert result is None


def test_map_adzuna_missing_url_returns_none():
    """Item with empty redirect_url returns None."""
    item = {
        "title": "Software Engineer",
        "company": {"display_name": "Google Inc"},
        "redirect_url": "",
    }

    result = map_adzuna_to_job_result(item)

    assert result is None


@pytest.mark.parametrize("salary_min,salary_max,expected_salary_str", [
    (80000, 120000, "$80,000 - $120,000"),
    (80000, None, "$80,000+"),
    (None, None, "Not specified"),
    (150000.5, 200000.75, "$150,000 - $200,001"),
])
def test_map_adzuna_salary_formatting(salary_min, salary_max, expected_salary_str):
    """Salary formats correctly: range, min-only, not-specified."""
    item = {
        "title": "Engineer",
        "company": {"display_name": "Acme"},
        "redirect_url": "https://example.com/job",
        "salary_min": salary_min,
        "salary_max": salary_max,
    }

    result = map_adzuna_to_job_result(item)

    assert result is not None
    assert result.salary == expected_salary_str


def test_map_adzuna_html_description_cleaned():
    """HTML tags and entities stripped from description."""
    item = {
        "title": "Developer",
        "company": {"display_name": "Tech Co"},
        "redirect_url": "https://example.com/job",
        "description": "<p>Great &amp; exciting <b>role</b></p><ul><li>Python</li><li>React</li></ul>",
    }

    result = map_adzuna_to_job_result(item)

    assert result is not None
    assert "<p>" not in result.description
    assert "<b>" not in result.description
    assert "<ul>" not in result.description
    assert "&amp;" not in result.description
    assert "Great & exciting role" in result.description


def test_map_adzuna_location_normalized():
    """Location normalized to City, State format."""
    item = {
        "title": "Engineer",
        "company": {"display_name": "Acme"},
        "redirect_url": "https://example.com/job",
        "location": {"display_name": "San Francisco, California, United States"},
    }

    result = map_adzuna_to_job_result(item)

    assert result is not None
    assert result.location == "San Francisco, CA"


# ==============================================================================
# Authentic Jobs Mapper Tests
# ==============================================================================

def test_map_authenticjobs_valid_job():
    """Valid Authentic Jobs item maps to JobResult."""
    item = {
        "title": "Frontend Developer",
        "company": {
            "name": "Design Studio",
            "location": {"name": "Austin, TX"},
        },
        "url": "https://example.com/job/456",
        "description": "<div>Work with <strong>React</strong> and <em>TypeScript</em></div>",
        "post_date": "2026-02-10",
        "type": {"name": "Full-time"},
    }

    result = map_authenticjobs_to_job_result(item)

    assert result is not None
    assert result.title == "Frontend Developer"
    assert result.company == "Design Studio"
    assert result.location == "Austin, TX"
    assert result.url == "https://example.com/job/456"
    assert result.source == "authentic_jobs"
    assert "React" in result.description
    assert "<strong>" not in result.description
    assert result.employment_type == "Full-time"


def test_map_authenticjobs_missing_required_fields_returns_none():
    """Item missing title/company/url returns None."""
    # Missing title
    item1 = {
        "title": "",
        "company": {"name": "Studio"},
        "url": "https://example.com/job",
    }
    assert map_authenticjobs_to_job_result(item1) is None

    # Missing company name
    item2 = {
        "title": "Developer",
        "company": {},
        "url": "https://example.com/job",
    }
    assert map_authenticjobs_to_job_result(item2) is None

    # Missing URL
    item3 = {
        "title": "Developer",
        "company": {"name": "Studio"},
        "url": "",
    }
    assert map_authenticjobs_to_job_result(item3) is None


def test_map_authenticjobs_defensive_nested_access():
    """Handles non-dict company field defensively."""
    # Company as string instead of dict
    item = {
        "title": "Designer",
        "company": "String Company",
        "url": "https://example.com/job",
    }

    result = map_authenticjobs_to_job_result(item)

    assert result is not None
    assert result.company == "String Company"
    assert result.location == "Unknown"  # Can't extract location from string


# ==============================================================================
# Text Utility Tests
# ==============================================================================

def test_strip_html_and_normalize_basic():
    """Strips tags and normalizes whitespace."""
    text = "<p>Hello   world</p><div>Test</div>"

    result = strip_html_and_normalize(text)

    assert result == "Hello world Test"
    assert "<p>" not in result
    assert "<div>" not in result


def test_strip_html_and_normalize_entities():
    """Decodes HTML entities: &amp; -> &, &#39; -> ', &nbsp; -> space."""
    text = "Great &amp; exciting role with &#39;Python&#39;&nbsp;skills"

    result = strip_html_and_normalize(text)

    assert result == "Great & exciting role with 'Python' skills"
    assert "&amp;" not in result
    assert "&#39;" not in result
    assert "&nbsp;" not in result


def test_strip_html_and_normalize_empty():
    """Empty string returns empty string."""
    assert strip_html_and_normalize("") == ""
    assert strip_html_and_normalize(None) == ""


def test_strip_html_and_normalize_nested_tags():
    """Handles nested HTML tags correctly."""
    text = "<div><p><strong>Bold <em>and italic</em></strong> text</p></div>"

    result = strip_html_and_normalize(text)

    assert result == "Bold and italic text"
    assert "<" not in result
    assert ">" not in result


@pytest.mark.parametrize("input_loc,expected", [
    ("San Francisco, CA", "San Francisco, CA"),
    ("San Francisco, California, United States", "San Francisco, CA"),
    ("Remote", "Remote"),
    ("remote work available", "Remote"),
    ("New York, NY 10001", "New York, NY"),
    ("London, UK", "London, UK"),
    ("", "Unknown"),
    ("Austin, Texas", "Austin, TX"),
    ("Seattle, Washington", "Seattle, WA"),
    ("REMOTE", "Remote"),
    ("Boston, MA", "Boston, MA"),
])
def test_parse_location_to_city_state(input_loc, expected):
    """Location parsing handles various formats."""
    assert parse_location_to_city_state(input_loc) == expected


# ==============================================================================
# Fetch Function Error Handling Tests
# ==============================================================================

def test_fetch_adzuna_missing_credentials(monkeypatch):
    """Returns empty list when API credentials missing."""
    monkeypatch.setattr("job_radar.sources.get_api_key", lambda key, source: None)

    result = fetch_adzuna("python developer")

    assert result == []


def test_fetch_adzuna_rate_limited(monkeypatch):
    """Returns empty list when rate limited."""
    monkeypatch.setattr("job_radar.sources.get_api_key", lambda key, source: "fake_key")
    monkeypatch.setattr("job_radar.sources.check_rate_limit", lambda source, verbose=False: False)

    result = fetch_adzuna("python developer")

    assert result == []


def test_fetch_authenticjobs_missing_credentials(monkeypatch):
    """Returns empty list when API key missing."""
    monkeypatch.setattr("job_radar.sources.get_api_key", lambda key, source: None)

    result = fetch_authenticjobs("designer")

    assert result == []


def test_fetch_authenticjobs_rate_limited(monkeypatch):
    """Returns empty list when rate limited."""
    monkeypatch.setattr("job_radar.sources.get_api_key", lambda key, source: "fake_key")
    monkeypatch.setattr("job_radar.sources.check_rate_limit", lambda source, verbose=False: False)

    result = fetch_authenticjobs("designer")

    assert result == []


# ==============================================================================
# Pipeline Integration Tests
# ==============================================================================

def test_build_search_queries_includes_api_sources():
    """build_search_queries includes adzuna and authentic_jobs sources."""
    profile = {
        "name": "Test User",
        "target_titles": ["Software Engineer"],
        "core_skills": ["python"],
        "target_market": "New York, NY",
    }

    queries = build_search_queries(profile)

    sources = {q["source"] for q in queries}
    assert "adzuna" in sources
    assert "authentic_jobs" in sources


def test_build_search_queries_api_includes_location():
    """API queries include location from profile."""
    profile = {
        "name": "Test User",
        "target_titles": ["Developer"],
        "core_skills": ["python"],
        "target_market": "San Francisco, CA",
    }

    queries = build_search_queries(profile)

    api_queries = [q for q in queries if q["source"] in ("adzuna", "authentic_jobs")]
    for q in api_queries:
        assert q.get("location") == "San Francisco, CA"


def test_build_search_queries_multiple_titles_generate_adzuna_queries():
    """Each target title generates an Adzuna query."""
    profile = {
        "name": "Test User",
        "target_titles": ["Software Engineer", "Backend Developer", "Full Stack Developer"],
        "core_skills": ["python"],
        "target_market": "Seattle, WA",
    }

    queries = build_search_queries(profile)

    adzuna_queries = [q for q in queries if q["source"] == "adzuna"]
    assert len(adzuna_queries) == 3
    assert all(q.get("location") == "Seattle, WA" for q in adzuna_queries)
    query_titles = {q["query"] for q in adzuna_queries}
    assert "Software Engineer" in query_titles
    assert "Backend Developer" in query_titles
    assert "Full Stack Developer" in query_titles


def test_build_search_queries_authentic_jobs_uses_top_2_titles():
    """Authentic Jobs queries use top 2 titles only."""
    profile = {
        "name": "Test User",
        "target_titles": ["UX Designer", "Product Designer", "UI Designer", "Visual Designer"],
        "core_skills": ["figma"],
        "target_market": "Austin, TX",
    }

    queries = build_search_queries(profile)

    authentic_queries = [q for q in queries if q["source"] == "authentic_jobs"]
    assert len(authentic_queries) == 2
    query_titles = {q["query"] for q in authentic_queries}
    assert "UX Designer" in query_titles
    assert "Product Designer" in query_titles
    assert "UI Designer" not in query_titles  # 3rd title not included
