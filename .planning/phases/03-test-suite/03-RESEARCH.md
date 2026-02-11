# Phase 3: Test Suite - Research

**Researched:** 2026-02-08
**Domain:** Python testing with pytest for CLI scoring and tracking application
**Confidence:** HIGH

## Summary

pytest is the accepted standard for Python testing in 2026, with a mature ecosystem and excellent support for parametrized tests, fixtures, and file isolation. For the Job Radar test suite, the standard approach is to create a `tests/` directory alongside the `job_radar/` package, using pytest's built-in fixtures like `tmp_path` for tracker isolation and `@pytest.mark.parametrize` for comprehensive scoring function coverage.

The key challenge is testing scoring functions with many edge cases (dealbreakers, salary parsing, skill matching) while ensuring tracker tests never touch production data. pytest's parametrize decorator handles the first concern elegantly, and the `tmp_path` fixture provides automatic isolation for the second.

**Primary recommendation:** Use a flat `tests/` directory structure with module-level test files (test_scoring.py, test_tracker.py), a shared conftest.py for fixtures (sample profiles, JobResult factories), and parametrized tests for all `_score_*` functions covering normal cases and edge cases.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.x+ | Test framework | De facto Python testing standard, replaced unittest for new projects in 2026 |
| pytest (tmp_path) | built-in | File isolation | Built-in fixture for temporary directories, automatic cleanup |
| pytest (parametrize) | built-in | Edge case testing | Built-in decorator for data-driven tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-cov | 5.x+ | Coverage reporting | Optional for coverage metrics (not required by success criteria) |
| hypothesis | 6.x+ | Property-based testing | Optional for discovering unforeseen edge cases in parsers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest | unittest | pytest has simpler assertions, better fixtures, cleaner output; unittest is more verbose |
| tmp_path | manual cleanup | tmp_path is automatic, safe, and pytest-native; manual cleanup is error-prone |
| parametrize | test loops | parametrize gives individual test reports per case; loops report as single test |

**Installation:**
```bash
# Add to pyproject.toml dependencies (dev section)
pip install pytest

# Optional coverage reporting
pip install pytest-cov
```

## Architecture Patterns

### Recommended Project Structure
```
Job-Radar/
├── job_radar/          # Source package
│   ├── scoring.py
│   ├── tracker.py
│   └── ...
├── tests/              # Test directory (side-by-side with source)
│   ├── conftest.py     # Shared fixtures
│   ├── test_scoring.py # Scoring function tests
│   ├── test_tracker.py # Tracker tests with tmp_path
│   └── test_config.py  # Config loading tests
├── pyproject.toml
└── pytest.ini          # Optional pytest configuration
```

**Rationale:** pytest's "good practices" guide recommends the side-by-side layout over inlined tests. Tests can run against installed versions, and the structure scales better.

### Pattern 1: Parametrized Scoring Tests
**What:** Use `@pytest.mark.parametrize` to test each scoring function with multiple inputs
**When to use:** All `_score_*` functions that take varied inputs (skills, titles, locations, salary)
**Example:**
```python
# Source: https://docs.pytest.org/en/stable/how-to/parametrize.html
import pytest
from job_radar.scoring import _parse_salary_number

@pytest.mark.parametrize("text,expected", [
    ("$120k", 120000),                    # Normal case: k suffix
    ("$60/hr", 124800),                   # Normal case: hourly
    ("$120,000", 120000),                 # Normal case: comma separator
    ("Not listed", None),                 # Edge: not listed
    ("", None),                           # Edge: empty string
    ("$120k-$150k", 120000),              # Edge: range (parses first)
    ("Competitive salary", None),         # Edge: non-numeric
])
def test_parse_salary_number(text, expected):
    result = _parse_salary_number(text)
    assert result == expected
```

**Benefits:**
- Each parameter set runs as individual test (clear failure reporting)
- Easy to add new edge cases without duplicating test code
- Custom IDs make test output readable: `test_parse_salary[Normal: $120k]`

### Pattern 2: Fixture Factories for Test Data
**What:** Create factory fixtures that return functions to build test objects
**When to use:** When tests need JobResult or profile dict instances with varying attributes
**Example:**
```python
# Source: https://www.fiddler.ai/blog/advanced-pytest-patterns-harnessing-the-power-of-parametrization-and-factory-methods
import pytest
from job_radar.sources import JobResult

@pytest.fixture
def job_factory():
    """Factory fixture for creating JobResult instances with custom attributes."""
    def _make_job(**kwargs):
        defaults = {
            "title": "Senior Python Developer",
            "company": "TestCorp",
            "location": "Remote",
            "arrangement": "remote",
            "salary": "$120k-$150k",
            "date_posted": "2026-02-08",
            "description": "Build scalable systems",
            "url": "https://example.com/job/123",
            "source": "Test",
        }
        return JobResult(**{**defaults, **kwargs})
    return _make_job

def test_dealbreaker_match(job_factory, sample_profile):
    job = job_factory(description="Must relocate to office")
    sample_profile["dealbreakers"] = ["relocate"]
    result = score_job(job, sample_profile)
    assert result["overall"] == 0.0
```

**Benefits:**
- Tests only specify attributes they care about
- Reduces test boilerplate
- Easy to create variations for edge cases

### Pattern 3: tmp_path for Tracker Isolation
**What:** Use pytest's built-in `tmp_path` fixture to isolate tracker.json operations
**When to use:** All tests that call tracker functions (mark_seen, get_stats, job_key)
**Example:**
```python
# Source: https://docs.pytest.org/en/stable/how-to/tmp_path.html
import pytest
from job_radar.tracker import mark_seen, _TRACKER_PATH
from unittest.mock import patch

def test_mark_seen_new_job(tmp_path, job_factory):
    """Test that new jobs are marked with is_new=True."""
    # Redirect tracker to tmp_path
    tracker_file = tmp_path / "tracker.json"

    with patch("job_radar.tracker._TRACKER_PATH", str(tracker_file)):
        job = job_factory(title="Python Dev", company="TestCo")
        results = [{"job": job, "score": {"overall": 4.2}}]

        annotated = mark_seen(results)

        assert annotated[0]["is_new"] is True
        assert tracker_file.exists()
```

**Benefits:**
- Automatic cleanup after test finishes
- No risk of polluting production tracker.json
- Each test gets isolated temporary directory
- pathlib.Path objects for modern file operations

### Anti-Patterns to Avoid
- **Testing private functions through public API only:** Job Radar has many `_score_*` helpers that should be tested directly for comprehensive edge case coverage. Public API testing alone won't catch all edge cases efficiently.
- **Shared state across tests:** Never use a global tracker.json or modify module-level state without cleanup. Use tmp_path or monkeypatch to isolate.
- **Non-unique test file names:** pytest's default import mode requires unique test file names across directories. Either use unique names or configure `--import-mode=importlib`.
- **Fixture name collisions with test parameters:** Keep fixture namespaces separate from parametrize parameter names to avoid confusing errors.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Temporary directories | Manual tempfile.mkdtemp + cleanup | pytest's tmp_path fixture | Automatic cleanup, pathlib integration, less code |
| Test data factories | Custom builder classes | pytest fixtures with factory pattern | Standard pattern, better integration with pytest's dependency injection |
| Mocking file paths | Copying test files around | tmp_path + pathlib | Cleaner, isolated, no leftover test files |
| Parametrized tests | Test loops with list of cases | @pytest.mark.parametrize | Individual test reports per case, better failure output |
| Environment mocking | Manual os.environ manipulation | pytest's monkeypatch fixture | Automatic restoration, no test pollution |

**Key insight:** pytest's built-in fixtures (tmp_path, monkeypatch, caplog) handle 90% of common testing needs. Resist the urge to build custom helpers before checking pytest's standard library.

## Common Pitfalls

### Pitfall 1: Tracker Tests Polluting Production Data
**What goes wrong:** Tests call tracker functions without isolation, creating/modifying `results/tracker.json` in the project directory
**Why it happens:** tracker.py uses a hardcoded `_TRACKER_PATH = os.path.join(os.getcwd(), "results", "tracker.json")` that points to production location
**How to avoid:** Use `unittest.mock.patch` to redirect `_TRACKER_PATH` to a tmp_path location for all tracker tests
**Warning signs:** `results/tracker.json` changes after running tests, tests fail when run from different directories

**Solution pattern:**
```python
from unittest.mock import patch

def test_tracker_function(tmp_path):
    tracker_file = tmp_path / "tracker.json"
    with patch("job_radar.tracker._TRACKER_PATH", str(tracker_file)):
        # Test code here - tracker operates on tmp_path
        pass
```

### Pitfall 2: Testing Private Functions vs. Testing Through Public API
**What goes wrong:** Debate over whether to test `_score_skill_match` directly or only test `score_job`
**Why it happens:** Python convention suggests `_` prefix means private, but scoring.py has complex scoring logic in private helpers
**How to avoid:** Test private `_score_*` functions directly. They have clear contracts, many edge cases, and testing through `score_job` would require complex profile setups
**Warning signs:** Tests become overly complex to hit edge cases, coverage gaps in private functions

**Guidance:** For Job Radar, test both:
- Private `_score_*` functions: Direct, parametrized tests for edge cases
- Public `score_job`: Integration-style tests for weighted scoring, dealbreakers, penalties

### Pitfall 3: Parametrize ID Conflicts with Marks
**What goes wrong:** Using same string as parametrize `id` and a pytest mark causes namespace collision
**Why it happens:** pytest uses marks and IDs in overlapping namespaces internally
**How to avoid:** Never use `@pytest.mark.X` where X matches a parametrize ID; use descriptive ID strings
**Warning signs:** Confusing pytest errors about mark registration

### Pitfall 4: Forgetting to Test Empty/None Cases
**What goes wrong:** Scoring functions crash on empty strings, None values, missing profile keys
**Why it happens:** Happy-path testing focuses on "normal" inputs
**How to avoid:** Always include edge cases in parametrize: empty string, None, missing dict keys, empty lists
**Warning signs:** KeyError or AttributeError in production when profiles are incomplete

**Checklist for each scoring function:**
- [ ] Normal case (expected input)
- [ ] Empty string
- [ ] None value
- [ ] Missing profile key (use `.get()` with defaults)
- [ ] Empty list (for skills, titles)

### Pitfall 5: Test File Name Collisions
**What goes wrong:** Two test files named `test_utils.py` in different directories cause import errors
**Why it happens:** pytest's default `prepend` import mode manipulates sys.path, causing name conflicts
**How to avoid:** Use unique test file names OR configure `--import-mode=importlib` in pytest.ini
**Warning signs:** `ImportError` or "cannot import name" errors in test discovery

**For Job Radar:** Use unique names (test_scoring.py, test_tracker.py, test_config.py) - no conflicts expected.

## Code Examples

Verified patterns from official sources:

### Testing Dealbreaker Detection (Parametrized)
```python
# Source: https://docs.pytest.org/en/stable/how-to/parametrize.html
import pytest
from job_radar.scoring import _check_dealbreakers
from job_radar.sources import JobResult

@pytest.mark.parametrize("description,dealbreakers,expected", [
    # Exact match
    ("Must relocate to NYC", ["relocate"], "relocate"),
    # Substring match
    ("Requires on-site presence", ["on-site"], "on-site"),
    # Case-insensitive
    ("RELOCATION REQUIRED", ["relocation"], "relocation"),
    # No match
    ("Remote-friendly team", ["on-site"], None),
    # Empty dealbreakers
    ("Any description", [], None),
], ids=[
    "exact_match",
    "substring_match",
    "case_insensitive",
    "no_match",
    "no_dealbreakers",
])
def test_check_dealbreakers(job_factory, description, dealbreakers, expected):
    job = job_factory(description=description)
    profile = {"dealbreakers": dealbreakers}
    result = _check_dealbreakers(job, profile)
    assert result == expected
```

### Testing Salary Parsing (Edge Cases)
```python
# Source: https://docs.pytest.org/en/stable/example/parametrize.html
import pytest
from job_radar.scoring import _parse_salary_number

@pytest.mark.parametrize("text,expected", [
    # Normal cases
    ("$120k", 120000),
    ("$60/hr", 124800),  # 60 * 2080 hours
    ("$120,000", 120000),
    # Ranges (parses first value)
    ("$100k-$120k", 100000),
    ("$50/hr - $70/hr", 104000),
    # Edge cases
    ("Not listed", None),
    ("", None),
    (None, None),  # If function can receive None
    ("Competitive", None),
    ("$150000", 150000),  # No comma
    ("150k", 150000),  # No dollar sign
])
def test_parse_salary_number_edge_cases(text, expected):
    result = _parse_salary_number(text)
    assert result == expected
```

### Testing Tracker with tmp_path Isolation
```python
# Source: https://docs.pytest.org/en/stable/how-to/tmp_path.html
import pytest
from unittest.mock import patch
from job_radar.tracker import mark_seen, job_key, get_stats

def test_job_key_stable(job_factory):
    """Test that job_key generates consistent dedup keys."""
    job1 = job_factory(title="Python Developer", company="TestCorp")
    job2 = job_factory(title="  python developer  ", company="  TESTCORP  ")

    # Keys should match despite whitespace/case differences
    assert job_key(job1.title, job1.company) == job_key(job2.title, job2.company)

def test_mark_seen_isolates_tracker(tmp_path, job_factory):
    """Test mark_seen with isolated tmp_path to avoid touching production tracker."""
    tracker_file = tmp_path / "tracker.json"

    with patch("job_radar.tracker._TRACKER_PATH", str(tracker_file)):
        job = job_factory(title="Python Dev", company="TestCo")
        results = [{"job": job, "score": {"overall": 4.2}}]

        # First run: job is new
        annotated = mark_seen(results)
        assert annotated[0]["is_new"] is True
        assert tracker_file.exists()

        # Second run: same job is seen
        annotated2 = mark_seen(results)
        assert annotated2[0]["is_new"] is False

def test_get_stats_aggregation(tmp_path, job_factory):
    """Test get_stats computes correct aggregations."""
    tracker_file = tmp_path / "tracker.json"

    with patch("job_radar.tracker._TRACKER_PATH", str(tracker_file)):
        # Mark some jobs seen to populate tracker
        jobs = [job_factory(title=f"Job {i}", company=f"Co {i}") for i in range(5)]
        results = [{"job": j, "score": {"overall": 3.5}} for j in jobs]
        mark_seen(results)

        stats = get_stats()
        assert stats["total_unique_jobs_seen"] == 5
        assert stats["total_runs"] == 1
```

### Shared Fixtures in conftest.py
```python
# Source: https://docs.pytest.org/en/stable/how-to/fixtures.html
# tests/conftest.py
import pytest
from job_radar.sources import JobResult

@pytest.fixture
def sample_profile():
    """Sample candidate profile for testing scoring functions."""
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
    """Factory fixture for creating JobResult instances with custom attributes."""
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
        return JobResult(**{**defaults, **kwargs})
    return _make_job
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| unittest framework | pytest | ~2020-2023 | pytest is now the accepted standard in 2026, simpler assertions |
| tmpdir fixture | tmp_path fixture | pytest 5.x+ (2019) | tmp_path returns pathlib.Path objects, modern API |
| Manual parametrization (loops) | @pytest.mark.parametrize | Standard since pytest 3.x | Individual test reports per case |
| Manual test discovery | Automatic discovery (test_*.py) | Always standard | No boilerplate |
| py.path.local | pathlib.Path | pytest 6.x+ emphasis | More pythonic, standard library |

**Deprecated/outdated:**
- `tmpdir` fixture: Use `tmp_path` instead (returns pathlib.Path, not deprecated py.path.local)
- `python setup.py test`: pytest docs warn this "may stop working" - use `pytest` directly
- `--import-mode=prepend`: New projects should use `--import-mode=importlib` to avoid sys.path manipulation

## Open Questions

Things that couldn't be fully resolved:

1. **Should tracker.py be refactored to accept path as parameter?**
   - What we know: Current design uses module-level `_TRACKER_PATH`, requiring patch() in tests
   - What's unclear: Whether refactoring to accept path parameter is in scope for this phase
   - Recommendation: Use patch() for now (works reliably), defer refactoring to future phase

2. **How much coverage is "enough" for scoring functions?**
   - What we know: Requirements specify edge cases for each function category
   - What's unclear: Whether 100% coverage of all branches is expected
   - Recommendation: Focus on requirement coverage (TEST-01 through TEST-07), not coverage percentage

3. **Should tests validate score ranges (1.0-5.0)?**
   - What we know: Scoring functions return scores in 1.0-5.0 range
   - What's unclear: Whether tests should assert score is always in valid range
   - Recommendation: Add range assertions as sanity checks (catch bugs like score > 5.0)

## Sources

### Primary (HIGH confidence)
- [pytest Documentation: Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) - Project structure, test discovery
- [pytest Documentation: How to use tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html) - File isolation patterns
- [pytest Documentation: How to parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) - Parametrized testing
- [pytest Documentation: How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) - Fixture patterns
- [pytest Documentation: Fixtures reference](https://docs.pytest.org/en/stable/reference/fixtures.html) - Built-in fixtures

### Secondary (MEDIUM confidence)
- [Pytest with Eric: Pytest tmp_path](https://pytest-with-eric.com/pytest-best-practices/pytest-tmp-path/) - Practical tmp_path examples
- [Pytest with Eric: Pytest Conftest](https://pytest-with-eric.com/pytest-best-practices/pytest-conftest/) - Conftest organization patterns
- [Fiddler AI: Advanced Pytest Patterns](https://www.fiddler.ai/blog/advanced-pytest-patterns-harnessing-the-power-of-parametrization-and-factory-methods) - Factory fixture pattern
- [Better Stack: Pytest Fixtures Guide](https://betterstack.com/community/guides/testing/pytest-fixtures-guide/) - Fixture best practices

### Tertiary (LOW confidence)
- Various blog posts on pytest patterns - Used for validation only, not primary source

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pytest is well-documented standard, official docs verified
- Architecture: HIGH - Project structure from official pytest docs, patterns verified in multiple sources
- Pitfalls: MEDIUM/HIGH - Common issues documented in official warnings and community experience

**Research date:** 2026-02-08
**Valid until:** ~2026-09-08 (6 months - pytest is stable, but best practices evolve)
