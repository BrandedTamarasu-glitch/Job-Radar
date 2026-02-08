# Testing Patterns

**Analysis Date:** 2026-02-07

## Test Framework

**Status:** No formal testing framework detected

**Observation:**
- No `tests/` directory found
- No test files (`test_*.py` or `*_test.py`) in codebase
- No testing dependencies in `pyproject.toml` (pytest, unittest, nose not present)
- No test configuration files detected (`pytest.ini`, `setup.cfg` with test section, `tox.ini`)

**Why No Tests:**
- Codebase is a command-line tool focused on web scraping and data transformation
- Testing web scrapers is complex due to external dependencies and dynamic HTML
- Integration testing with live job boards would be fragile

## Current Testing Approach

**Manual Testing:**
- Tool is invoked via CLI with different profiles and options
- Dry-run mode for validation: `job-radar --profile profiles/your_name.json --dry-run`
- Reports are manually inspected in Markdown format
- No automated test suite

## Testing Opportunities

### Unit Testing Candidates

**Low External Dependency:**
- `job_radar/scoring.py` - Pure logic functions that score jobs
  - `score_job()` takes data structure and returns scores
  - `_parse_salary_number()` parses text to float
  - `_check_dealbreakers()` searches terms in job text
  - `_recommendation()` maps scores to text

- `job_radar/tracker.py` - JSON read/write with in-memory logic
  - `job_key()` generates dedup keys
  - `mark_seen()` tracks new vs seen jobs
  - `get_stats()` computes aggregates

- `job_radar/cache.py` - File I/O and retry logic
  - `fetch_with_retry()` could be tested with mock HTTP
  - `_cache_path()` generates filesystem paths

**Testing Strategy for Scoring:**
```python
# Example structure (not implemented)
def test_score_job_strong_match():
    job = JobResult(
        title="Python Engineer",
        company="Acme",
        location="Remote",
        # ... all fields ...
    )
    profile = {
        "target_titles": ["Python Engineer"],
        "core_skills": ["Python"],
        # ... all fields ...
    }
    result = score_job(job, profile)
    assert result["overall"] >= 4.0
    assert result["recommendation"] == "Strong Recommend"

def test_dealbreaker_detection():
    job = JobResult(
        title="Java Engineer",
        description="Staffing firm position",
        # ... all fields ...
    )
    profile = {
        "dealbreakers": ["staffing firm"],
    }
    result = score_job(job, profile)
    assert result["overall"] == 0.0
    assert result["dealbreaker"] == "staffing firm"
```

### Integration Testing Candidates

**Data Flow Tests:**
- End-to-end pipeline with mock data:
  1. Mock `fetch_all()` to return test JobResult list
  2. Score the test data
  3. Filter by date
  4. Generate report
  5. Verify report content

**CLI Tests:**
- Could use `subprocess` or Click testing to invoke CLI with test profiles
- Verify exit codes and report generation

### Scraper Testing Challenges

**Why Not Tested:**
- `job_radar/sources.py` fetches from live websites (Dice, HN Hiring, RemoteOK, WWR)
- HTML structure changes break selectors
- Site-specific scrapers would need regular updates
- Test data would require bundling HTML snapshots

**Testing Strategy if Needed:**
```python
# Would use pytest + fixtures
@pytest.fixture
def mock_dice_response():
    """Load saved HTML response for testing."""
    with open("tests/fixtures/dice_response.html") as f:
        return f.read()

def test_fetch_dice_parsing(mock_dice_response, monkeypatch):
    """Test Dice HTML parsing with fixed snapshot."""
    monkeypatch.setattr("job_radar.cache.fetch_with_retry",
                        lambda *a, **k: mock_dice_response)
    results = fetch_dice("Python")
    assert len(results) > 0
    assert all(isinstance(r, JobResult) for r in results)
```

## Error Handling in Current Code

**Broad Exception Catches:**
- All scrapers use broad `except Exception:` to prevent crashes from parse errors
- Example from `job_radar/sources.py` (lines 182):
  ```python
  except Exception as e:
      log.error("[Dice] Parse error: %s", e)
  ```
- Allows tool to continue even if one scraper fails

**Network Retries:**
- `job_radar/cache.py` implements exponential backoff (lines 53-76)
- 3 retries with configurable backoff (default 2.0)
- Graceful failure: returns `None` instead of raising

**Graceful Degradation:**
- Missing fields default to "Unknown" or "Not listed"
- Parse confidence tracked: `parse_confidence = "high"|"medium"|"low"`
- Low confidence results penalized but included (not filtered)

## Test Data Structure

**JobResult Dataclass:**
Required for test fixtures (`job_radar/sources.py` lines 19-34):
```python
JobResult(
    title="Python Engineer",
    company="Acme Corp",
    location="San Francisco, CA",
    arrangement="hybrid",
    salary="$120k-$140k",
    date_posted="2026-02-06",
    description="Build backend systems",
    url="https://example.com/job/123",
    source="Dice",
    apply_info="Apply on Dice",        # optional
    employment_type="Full-time",        # optional
    parse_confidence="high",            # optional
)
```

**Profile Structure:**
Required for scoring tests:
```python
profile = {
    "name": "Jane Doe",
    "level": "Senior",
    "years_experience": 7,
    "target_titles": ["Python Engineer", "Backend Engineer"],
    "core_skills": ["Python", "PostgreSQL", "AWS"],
    "target_market": "US Tech",
    "location": "US",
    "arrangement": ["remote", "hybrid"],
    "certifications": [],
    "comp_floor": 120000,
    "dealbreakers": ["staffing firm", "no benefits"],
}
```

## Manual Testing Approach

**Dry-Run Mode:**
- `job-radar --profile profiles/your_name.json --dry-run`
- Prints queries that would be executed without hitting network
- Located in `job_radar/search.py` (lines 290-305)

**Test Profiles:**
- Profiles in `profiles/` directory (git-tracked examples)
- Each profile is JSON file with candidate preferences
- Can create test profiles to validate scoring logic

**Output Validation:**
- Reports generated as Markdown in `results/` directory
- Manual inspection of generated reports
- Compare against previous runs using tracker stats

## Coverage Insights

**Zero Coverage Areas:**
- `job_radar/sources.py` scrapers (Dice, HN Hiring, RemoteOK, WWR) - 791 lines, mostly untested
- HTML parsing logic fragile to site changes
- Would need HTML snapshots to test reliably

**Partially Testable:**
- `job_radar/scoring.py` (486 lines) - Core logic is pure functions, very testable
- `job_radar/cache.py` (101 lines) - Cacheing/retry logic testable with mocks
- `job_radar/tracker.py` (125 lines) - File I/O testable with temp directories
- `job_radar/report.py` (211 lines) - Report formatting testable with string comparisons

**Missing Tests:**
- No validation of scorer weighting (25% skill, 15% title, etc.)
- No tests for edge cases in salary parsing (`_parse_salary_number()`)
- No tests for location matching logic (`_locations_match()`)
- No tests for seniority scoring rules
- No tests for dealbreaker detection
- No tests for response likelihood scoring

## Recommended Testing Strategy

**Phase 1 - Unit Tests (Highest Value):**
1. Scoring module - test each `_score_*` function with fixtures
2. Salary parsing - edge cases ($120k, $60/hr, ranges)
3. Dealbreaker matching - text search patterns
4. Tracker deduplication - job_key() uniqueness
5. Recommendation logic - score thresholds

**Phase 2 - Integration Tests:**
1. End-to-end score pipeline with test jobs
2. Report generation with test results
3. Tracker cross-run deduplication
4. Filter by date logic

**Phase 3 - Scraper Tests (Lower Priority):**
1. Capture HTML snapshots from each source
2. Test against frozen snapshots
3. Update snapshots when sites change
4. May not be worth maintaining

**Tool Choice:**
- `pytest` recommended for fixtures and parametrization
- Simple `@pytest.mark.parametrize` for multiple score scenarios
- Use `tmp_path` fixture for file I/O tests
- Mock `requests` library for fetch tests

---

*Testing analysis: 2026-02-07*
