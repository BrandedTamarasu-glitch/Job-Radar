"""Tests for API source integration covering mappers, text utilities, fetchers, and pipeline."""

import pytest
from job_radar.sources import (
    map_adzuna_to_job_result,
    map_authenticjobs_to_job_result,
    map_jsearch_to_job_result,
    map_usajobs_to_job_result,
    map_serpapi_to_job_result,
    map_jobicy_to_job_result,
    strip_html_and_normalize,
    parse_location_to_city_state,
    fetch_adzuna,
    fetch_authenticjobs,
    fetch_jsearch,
    fetch_usajobs,
    build_search_queries,
    generate_wellfound_url,
    _slugify_for_wellfound,
    generate_manual_urls,
    JobResult,
)
from job_radar.rate_limits import RATE_LIMITS, BACKEND_API_MAP


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


# ==============================================================================
# Wellfound URL Generator Tests
# ==============================================================================

def test_generate_wellfound_url_with_location():
    """Location-based URL uses /role/l/ pattern."""
    url = generate_wellfound_url("Software Engineer", "San Francisco, CA")

    assert url == "https://wellfound.com/role/l/software-engineer/san-francisco-ca"


def test_generate_wellfound_url_remote():
    """Remote URL uses /role/r/ pattern."""
    url = generate_wellfound_url("Backend Developer", "Remote")

    assert url == "https://wellfound.com/role/r/backend-developer"


def test_generate_wellfound_url_remote_case_insensitive():
    """Remote detection is case-insensitive."""
    url = generate_wellfound_url("Frontend Engineer", "remote - US")

    assert url.startswith("https://wellfound.com/role/r/")
    assert url == "https://wellfound.com/role/r/frontend-engineer"


def test_generate_wellfound_url_slug_special_chars():
    """Slug handles special characters and preserves hyphens."""
    url = generate_wellfound_url("Senior Full-Stack Engineer", "New York, NY")

    assert "senior-full-stack-engineer" in url
    assert "new-york-ny" in url
    assert url == "https://wellfound.com/role/l/senior-full-stack-engineer/new-york-ny"


@pytest.mark.parametrize("text,expected", [
    ("", ""),
    ("  spaces  ", "spaces"),
    ("Multiple   Spaces", "multiple-spaces"),
    ("Already-Hyphenated", "already-hyphenated"),
    ("San Francisco, CA", "san-francisco-ca"),
    ("Senior Full-Stack Developer", "senior-full-stack-developer"),
])
def test_slugify_for_wellfound_edge_cases(text, expected):
    """Slugifier handles edge cases correctly."""
    assert _slugify_for_wellfound(text) == expected


def test_generate_manual_urls_includes_wellfound():
    """Wellfound appears in generate_manual_urls() output."""
    profile = {
        "target_titles": ["Software Engineer"],
        "target_market": "Remote",
    }

    urls = generate_manual_urls(profile)

    sources = [u["source"] for u in urls]
    assert "Wellfound" in sources

    wellfound_urls = [u for u in urls if u["source"] == "Wellfound"]
    assert len(wellfound_urls) > 0
    assert "wellfound.com" in wellfound_urls[0]["url"]


def test_generate_manual_urls_wellfound_first():
    """Wellfound appears BEFORE Indeed in manual URL list."""
    profile = {
        "target_titles": ["Developer"],
        "target_market": "NYC",
    }

    urls = generate_manual_urls(profile)

    sources = [u["source"] for u in urls]
    wellfound_idx = sources.index("Wellfound")
    indeed_idx = sources.index("Indeed")

    assert wellfound_idx < indeed_idx


def test_generate_manual_urls_wellfound_uses_first_three_titles():
    """Wellfound URLs limited to first 3 titles."""
    profile = {
        "target_titles": ["A", "B", "C", "D", "E"],
        "target_market": "Remote",
    }

    urls = generate_manual_urls(profile)

    wellfound_urls = [u for u in urls if u["source"] == "Wellfound"]
    assert len(wellfound_urls) == 3

    titles = {u["title"] for u in wellfound_urls}
    assert titles == {"A", "B", "C"}


# ==============================================================================
# JSearch Mapper Tests
# ==============================================================================

@pytest.mark.parametrize("job_publisher,expected_source", [
    ("LinkedIn", "linkedin"),
    ("Indeed", "indeed"),
    ("Glassdoor", "glassdoor"),
    ("Monster", "jsearch_other"),
    ("ZipRecruiter", "jsearch_other"),
    ("", "jsearch_other"),
])
def test_jsearch_maps_job_publisher_to_source(job_publisher, expected_source):
    """JSearch results use job_publisher for source attribution."""
    item = {
        "job_title": "Software Engineer",
        "employer_name": "Google Inc",
        "job_apply_link": "https://example.com/job/123",
        "job_publisher": job_publisher,
    }

    result = map_jsearch_to_job_result(item)

    assert result is not None
    assert result.source == expected_source


def test_jsearch_requires_title_company_url():
    """JSearch returns None when required fields missing."""
    # Missing title
    item1 = {
        "job_title": "",
        "employer_name": "Google",
        "job_apply_link": "https://example.com/job",
        "job_publisher": "LinkedIn",
    }
    assert map_jsearch_to_job_result(item1) is None

    # Missing company
    item2 = {
        "job_title": "Engineer",
        "employer_name": "",
        "job_apply_link": "https://example.com/job",
        "job_publisher": "LinkedIn",
    }
    assert map_jsearch_to_job_result(item2) is None

    # Missing URL
    item3 = {
        "job_title": "Engineer",
        "employer_name": "Google",
        "job_apply_link": "",
        "job_publisher": "LinkedIn",
    }
    assert map_jsearch_to_job_result(item3) is None


def test_jsearch_maps_remote_location():
    """JSearch remote flag maps to 'Remote' location."""
    item = {
        "job_title": "Software Engineer",
        "employer_name": "Google Inc",
        "job_apply_link": "https://example.com/job/123",
        "job_publisher": "LinkedIn",
        "job_is_remote": True,
    }

    result = map_jsearch_to_job_result(item)

    assert result is not None
    assert result.location == "Remote"


def test_jsearch_maps_salary():
    """JSearch salary formatting from min/max fields."""
    item = {
        "job_title": "Engineer",
        "employer_name": "Acme",
        "job_apply_link": "https://example.com/job",
        "job_publisher": "Indeed",
        "job_min_salary": 100000,
        "job_max_salary": 150000,
    }

    result = map_jsearch_to_job_result(item)

    assert result is not None
    assert result.salary == "$100,000 - $150,000"
    assert result.salary_min == 100000
    assert result.salary_max == 150000


def test_fetch_jsearch_handles_auth_error(monkeypatch):
    """JSearch returns empty list on 401/403."""
    monkeypatch.setattr("job_radar.sources.get_api_key", lambda key, source: "fake_key")
    monkeypatch.setattr("job_radar.sources.check_rate_limit", lambda source, verbose=False: True)

    # Mock fetch_with_retry to return None (simulates auth error)
    monkeypatch.setattr("job_radar.sources.fetch_with_retry", lambda *args, **kwargs: None)

    result = fetch_jsearch("python developer")

    assert result == []


def test_fetch_jsearch_handles_missing_api_key(monkeypatch):
    """JSearch returns empty list when API key missing."""
    monkeypatch.setattr("job_radar.sources.get_api_key", lambda key, source: None)

    result = fetch_jsearch("python developer")

    assert result == []


# ==============================================================================
# USAJobs Mapper Tests
# ==============================================================================

def test_usajobs_maps_nested_descriptor():
    """USAJobs extracts from MatchedObjectDescriptor structure."""
    item = {
        "MatchedObjectDescriptor": {
            "PositionTitle": "Software Developer",
            "OrganizationName": "Department of Treasury",
            "PositionURI": "https://usajobs.gov/job/123",
            "PositionLocationDisplay": "Washington, DC",
        }
    }

    result = map_usajobs_to_job_result(item)

    assert result is not None
    assert result.title == "Software Developer"
    assert result.company == "Department of Treasury"
    assert result.location == "Washington, DC"
    assert result.url == "https://usajobs.gov/job/123"
    assert result.source == "usajobs"


def test_usajobs_maps_salary_from_remuneration():
    """USAJobs salary mapping from PositionRemuneration array."""
    item = {
        "MatchedObjectDescriptor": {
            "PositionTitle": "Engineer",
            "OrganizationName": "NASA",
            "PositionURI": "https://usajobs.gov/job/456",
            "PositionRemuneration": [
                {
                    "MinimumRange": "80000",
                    "MaximumRange": "120000",
                }
            ]
        }
    }

    result = map_usajobs_to_job_result(item)

    assert result is not None
    assert result.salary == "$80,000 - $120,000"
    assert result.salary_min == 80000.0
    assert result.salary_max == 120000.0


def test_usajobs_requires_both_credentials(monkeypatch):
    """USAJobs returns empty list when email or API key missing."""
    # Missing API key
    def mock_get_api_key_no_key(key, source):
        if key == "USAJOBS_API_KEY":
            return None
        return "test@example.com"

    monkeypatch.setattr("job_radar.sources.get_api_key", mock_get_api_key_no_key)

    result = fetch_usajobs("engineer")
    assert result == []

    # Missing email
    def mock_get_api_key_no_email(key, source):
        if key == "USAJOBS_EMAIL":
            return None
        return "fake_api_key"

    monkeypatch.setattr("job_radar.sources.get_api_key", mock_get_api_key_no_email)

    result = fetch_usajobs("engineer")
    assert result == []


def test_usajobs_handles_empty_search_result():
    """USAJobs handles empty SearchResultItems gracefully."""
    item = {
        "MatchedObjectDescriptor": {
            "PositionTitle": "",
            "OrganizationName": "",
            "PositionURI": "",
        }
    }

    result = map_usajobs_to_job_result(item)

    assert result is None


def test_fetch_usajobs_passes_federal_filters(monkeypatch):
    """USAJobs passes federal profile filters as query params."""
    monkeypatch.setattr("job_radar.sources.get_api_key", lambda key, source: "fake_value")
    monkeypatch.setattr("job_radar.sources.check_rate_limit", lambda source, verbose=False: True)

    # Capture URL to verify params
    captured_url = []

    def mock_fetch_with_retry(url, headers=None, use_cache=None):
        captured_url.append(url)
        return '{"SearchResult": {"SearchResultItems": []}}'

    monkeypatch.setattr("job_radar.sources.fetch_with_retry", mock_fetch_with_retry)

    profile = {
        "gs_grade_min": 12,
        "gs_grade_max": 14,
        "preferred_agencies": ["TREAS"],
    }

    fetch_usajobs("engineer", profile=profile)

    assert len(captured_url) == 1
    url = captured_url[0]
    assert "PayGradeLow=12" in url
    assert "PayGradeHigh=14" in url
    assert "Organization=TREAS" in url


# ==============================================================================
# Query Builder Tests
# ==============================================================================

def test_build_queries_includes_jsearch():
    """build_search_queries generates jsearch queries."""
    profile = {
        "target_titles": ["Software Engineer"],
        "core_skills": ["python"],
        "target_market": "Remote",
    }

    queries = build_search_queries(profile)

    sources = {q["source"] for q in queries}
    assert "jsearch" in sources


def test_build_queries_includes_usajobs():
    """build_search_queries generates usajobs queries."""
    profile = {
        "target_titles": ["Engineer"],
        "core_skills": ["python"],
        "target_market": "Washington, DC",
    }

    queries = build_search_queries(profile)

    sources = {q["source"] for q in queries}
    assert "usajobs" in sources


def test_build_queries_jsearch_remote_location():
    """JSearch queries map remote arrangement to location=remote."""
    profile = {
        "target_titles": ["Developer"],
        "core_skills": ["python"],
        "target_market": "New York, NY",
        "arrangement": ["remote"],
    }

    queries = build_search_queries(profile)

    jsearch_queries = [q for q in queries if q["source"] == "jsearch"]
    assert len(jsearch_queries) > 0
    assert all(q.get("location") == "remote" for q in jsearch_queries)


# ==============================================================================
# SerpAPI Tests
# ==============================================================================

class TestMapSerpAPIToJobResult:
    """Tests for SerpAPI response mapper."""

    def test_valid_serpapi_item(self):
        """Complete SerpAPI item maps correctly."""
        item = {
            "title": "Software Engineer",
            "company_name": "Google",
            "location": "Mountain View, CA",
            "description": "Build scalable systems",
            "apply_options": [{"title": "Apply", "link": "https://careers.google.com/apply/123"}],
            "detected_extensions": {
                "posted_at": "2 days ago",
                "schedule_type": "Full-time",
                "work_from_home": False,
            },
            "job_id": "abc123",
        }
        job = map_serpapi_to_job_result(item)
        assert job is not None
        assert job.title == "Software Engineer"
        assert job.company == "Google"
        assert job.source == "serpapi"
        assert job.url == "https://careers.google.com/apply/123"
        assert job.employment_type == "Full-time"
        assert job.parse_confidence == "high"

    def test_serpapi_remote_detection(self):
        """Work from home flag sets arrangement to remote."""
        item = {
            "title": "Remote Developer",
            "company_name": "Remote Co",
            "location": "Anywhere",
            "description": "Work from home position",
            "apply_options": [{"link": "https://example.com"}],
            "detected_extensions": {"work_from_home": True},
        }
        job = map_serpapi_to_job_result(item)
        assert job is not None
        assert job.arrangement == "remote"

    def test_serpapi_missing_title(self):
        """Missing title returns None."""
        item = {
            "title": "",
            "company_name": "Corp",
            "apply_options": [{"link": "https://example.com"}],
        }
        assert map_serpapi_to_job_result(item) is None

    def test_serpapi_missing_company(self):
        """Missing company returns None."""
        item = {
            "title": "Engineer",
            "company_name": "",
            "apply_options": [{"link": "https://example.com"}],
        }
        assert map_serpapi_to_job_result(item) is None

    def test_serpapi_missing_url(self):
        """Missing apply URL returns None."""
        item = {
            "title": "Engineer",
            "company_name": "Corp",
            "apply_options": [],
        }
        assert map_serpapi_to_job_result(item) is None

    def test_serpapi_fallback_share_link(self):
        """Falls back to share_link when apply_options empty."""
        item = {
            "title": "Engineer",
            "company_name": "Corp",
            "location": "Remote",
            "description": "A job",
            "apply_options": [],
            "share_link": "https://google.com/jobs/share/123",
        }
        job = map_serpapi_to_job_result(item)
        assert job is not None
        assert job.url == "https://google.com/jobs/share/123"

    def test_serpapi_description_truncation(self):
        """Long descriptions are truncated to 500 chars."""
        item = {
            "title": "Engineer",
            "company_name": "Corp",
            "location": "NYC",
            "description": "x" * 600,
            "apply_options": [{"link": "https://example.com"}],
        }
        job = map_serpapi_to_job_result(item)
        assert job is not None
        assert len(job.description) <= 500


# ==============================================================================
# Jobicy Tests
# ==============================================================================

class TestMapJobicyToJobResult:
    """Tests for Jobicy response mapper."""

    def test_valid_jobicy_item(self):
        """Complete Jobicy item maps correctly."""
        item = {
            "id": "12345",
            "url": "https://jobicy.com/jobs/12345",
            "jobTitle": "Senior Python Developer",
            "companyName": "Remote Corp",
            "jobGeo": "USA",
            "jobType": "full-time",
            "jobDescription": "<p>Build <b>awesome</b> things with Python.</p>",
            "pubDate": "2026-02-13 10:30:00",
            "annualSalaryMin": "120000",
            "annualSalaryMax": "180000",
            "salaryCurrency": "USD",
        }
        job = map_jobicy_to_job_result(item)
        assert job is not None
        assert job.title == "Senior Python Developer"
        assert job.company == "Remote Corp"
        assert job.source == "jobicy"
        assert job.arrangement == "remote"  # Always remote
        assert "<p>" not in job.description  # HTML stripped
        assert "<b>" not in job.description
        assert "awesome" in job.description
        assert job.salary_min == 120000.0
        assert job.salary_max == 180000.0
        assert "120,000" in job.salary
        assert "180,000" in job.salary

    def test_jobicy_always_remote(self):
        """Jobicy jobs are always marked as remote."""
        item = {
            "jobTitle": "Developer",
            "companyName": "Corp",
            "url": "https://jobicy.com/jobs/1",
            "jobDescription": "A job description",
        }
        job = map_jobicy_to_job_result(item)
        assert job is not None
        assert job.arrangement == "remote"

    def test_jobicy_html_stripping(self):
        """HTML tags are stripped from descriptions."""
        item = {
            "jobTitle": "Dev",
            "companyName": "Corp",
            "url": "https://jobicy.com/jobs/1",
            "jobDescription": "<h1>Title</h1><p>We need a <strong>great</strong> developer.</p><ul><li>Python</li></ul>",
        }
        job = map_jobicy_to_job_result(item)
        assert job is not None
        assert "<" not in job.description
        assert "great" in job.description
        assert "Python" in job.description

    def test_jobicy_missing_title(self):
        """Missing title returns None."""
        item = {
            "jobTitle": "",
            "companyName": "Corp",
            "url": "https://jobicy.com/jobs/1",
        }
        assert map_jobicy_to_job_result(item) is None

    def test_jobicy_missing_company(self):
        """Missing company returns None."""
        item = {
            "jobTitle": "Dev",
            "companyName": "",
            "url": "https://jobicy.com/jobs/1",
        }
        assert map_jobicy_to_job_result(item) is None

    def test_jobicy_empty_description(self):
        """Empty description after HTML stripping returns None."""
        item = {
            "jobTitle": "Dev",
            "companyName": "Corp",
            "url": "https://jobicy.com/jobs/1",
            "jobDescription": "",
            "jobExcerpt": "",
        }
        assert map_jobicy_to_job_result(item) is None

    def test_jobicy_salary_min_only(self):
        """Salary with only minimum formats correctly."""
        item = {
            "jobTitle": "Dev",
            "companyName": "Corp",
            "url": "https://jobicy.com/jobs/1",
            "jobDescription": "A real job",
            "annualSalaryMin": "100000",
            "annualSalaryMax": "",
        }
        job = map_jobicy_to_job_result(item)
        assert job is not None
        assert "100,000" in job.salary

    def test_jobicy_no_salary(self):
        """Missing salary shows 'Not specified'."""
        item = {
            "jobTitle": "Dev",
            "companyName": "Corp",
            "url": "https://jobicy.com/jobs/1",
            "jobDescription": "A job posting",
        }
        job = map_jobicy_to_job_result(item)
        assert job is not None
        assert job.salary == "Not specified"

    def test_jobicy_fallback_to_excerpt(self):
        """Uses jobExcerpt when jobDescription is empty."""
        item = {
            "jobTitle": "Dev",
            "companyName": "Corp",
            "url": "https://jobicy.com/jobs/1",
            "jobDescription": "",
            "jobExcerpt": "A brief excerpt about this job",
        }
        job = map_jobicy_to_job_result(item)
        assert job is not None
        assert "brief excerpt" in job.description


# ==============================================================================
# Search Pipeline Integration Tests
# ==============================================================================

class TestSearchPipelineSerpAPIJobicy:
    """Tests for SerpAPI and Jobicy integration in search pipeline."""

    def test_build_search_queries_includes_serpapi(self):
        """build_search_queries generates SerpAPI queries."""
        profile = {
            "target_titles": ["Software Engineer"],
            "core_skills": ["python"],
            "target_market": "San Francisco, CA",
        }
        queries = build_search_queries(profile)
        serpapi_queries = [q for q in queries if q["source"] == "serpapi"]
        assert len(serpapi_queries) >= 1
        assert serpapi_queries[0]["query"] == "Software Engineer"

    def test_build_search_queries_includes_jobicy(self):
        """build_search_queries generates Jobicy queries."""
        profile = {
            "target_titles": ["Python Developer", "Backend Engineer"],
            "core_skills": ["python"],
            "target_market": "Remote",
        }
        queries = build_search_queries(profile)
        jobicy_queries = [q for q in queries if q["source"] == "jobicy"]
        assert len(jobicy_queries) >= 1
        assert len(jobicy_queries) <= 2  # Limited to top 2 titles

    def test_serpapi_query_has_location(self):
        """SerpAPI queries include location from profile."""
        profile = {
            "target_titles": ["Engineer"],
            "core_skills": ["python"],
            "target_market": "New York, NY",
        }
        queries = build_search_queries(profile)
        serpapi_queries = [q for q in queries if q["source"] == "serpapi"]
        assert serpapi_queries[0].get("location") == "New York, NY"


# ==============================================================================
# Rate Limit Config Tests
# ==============================================================================

class TestRateLimitConfigSerpAPIJobicy:
    """Tests for SerpAPI and Jobicy rate limiter configuration."""

    def test_serpapi_in_rate_limits(self):
        """SerpAPI has rate limit configuration."""
        assert "serpapi" in RATE_LIMITS
        rates = RATE_LIMITS["serpapi"]
        assert len(rates) >= 1

    def test_jobicy_in_rate_limits(self):
        """Jobicy has rate limit configuration."""
        assert "jobicy" in RATE_LIMITS
        rates = RATE_LIMITS["jobicy"]
        assert len(rates) >= 1

    def test_serpapi_in_backend_api_map(self):
        """SerpAPI is in BACKEND_API_MAP."""
        assert "serpapi" in BACKEND_API_MAP
        assert BACKEND_API_MAP["serpapi"] == "serpapi"

    def test_jobicy_in_backend_api_map(self):
        """Jobicy is in BACKEND_API_MAP."""
        assert "jobicy" in BACKEND_API_MAP
        assert BACKEND_API_MAP["jobicy"] == "jobicy"
