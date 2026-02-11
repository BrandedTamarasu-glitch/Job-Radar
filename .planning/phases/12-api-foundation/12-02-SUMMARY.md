---
phase: 12-api-foundation
plan: 02
subsystem: cli
tags: [api, cli, testing, questionary, pytest, integration]
requires:
  - phase: 12-01
    provides: api_config.py and rate_limits.py modules
provides:
  - interactive-api-setup-wizard
  - api-validation-commands
  - comprehensive-test-coverage
affects: [13-api-integrations, user-documentation]
tech-stack:
  added: []
  patterns: [questionary-interactive-prompts, atomic-file-writes, pytest-fixtures]
key-files:
  created: [job_radar/api_setup.py, tests/test_api_config.py, tests/test_rate_limits.py]
  modified: [job_radar/search.py]
decisions:
  - slug: api-setup-ux
    chosen: Interactive questionary prompts with skip-on-Enter
    why: Match existing wizard.py pattern, user-friendly credential collection
  - slug: test-isolation
    chosen: pytest tmp_path and monkeypatch fixtures
    why: Prevent cross-test contamination, clean filesystem and environment state
  - slug: rate-limiter-cleanup
    chosen: Autouse fixture with sleep before connection close
    why: Avoid segfault from background leaker thread accessing closed SQLite connection
metrics:
  duration: 3.5 min
  completed: 2026-02-10
---

# Phase 12 Plan 02: API Setup Commands and Test Coverage Summary

**One-liner:** Interactive --setup-apis wizard and --test-apis validation with comprehensive test coverage for api_config and rate_limits modules

## Performance

- **Duration:** 3.5 min (207 seconds)
- **Started:** 2026-02-10T15:44:07Z
- **Completed:** 2026-02-10T15:47:34Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Interactive API setup wizard using questionary for user-friendly credential collection
- API validation command that tests configured credentials with real HTTP requests
- Comprehensive test coverage: 7 tests for api_config, 6 tests for rate_limits (13 total)
- CLI integration with early-exit handlers (no profile needed for API commands)
- load_api_credentials() wired into main() pipeline before fetching

## Task Commits

Each task was committed atomically:

1. **Task 1: Create api_setup.py and integrate CLI flags** - `b403d1e` (feat)
2. **Task 2: Create tests for api_config and rate_limits modules** - `411796f` (test)

## Files Created/Modified

**Created:**
- `job_radar/api_setup.py` - Interactive setup_apis() wizard and test_apis() validation
- `tests/test_api_config.py` - 7 tests covering credential loading, key retrieval, .env.example
- `tests/test_rate_limits.py` - 6 tests covering rate limit config, allow/deny, persistence

**Modified:**
- `job_radar/search.py` - Added --setup-apis and --test-apis CLI flags, integrated load_api_credentials() call

## Implementation Details

### api_setup.py Module

**setup_apis() function:**
- Prompts for Adzuna credentials (ADZUNA_APP_ID and ADZUNA_APP_KEY)
- Prompts for Authentic Jobs credentials (AUTHENTIC_JOBS_API_KEY)
- Shows signup URLs for each service
- Supports skip-on-Enter for optional sources
- Displays summary of configured vs skipped sources
- Confirms before saving
- Atomic .env write using tempfile.mkstemp() + Path.replace() (crash-safe)
- Handles KeyboardInterrupt gracefully

**test_apis() function:**
- Loads credentials from .env using load_api_credentials()
- Tests each configured API with minimal request:
  - Adzuna: GET /v1/api/jobs/us/search/1 with results_per_page=1
  - Authentic Jobs: GET /?method=aj.jobs.search&keywords=test
- Reports pass (200), fail (401/403), or error (network/timeout)
- Provides summary: X/Y configured APIs working
- Suggests --setup-apis if any failed

### CLI Integration (search.py)

**Added argument group:**
```python
api_group = parser.add_argument_group('API Options')
api_group.add_argument("--setup-apis", ...)
api_group.add_argument("--test-apis", ...)
```

**Early exit handlers in main():**
```python
if args.setup_apis:
    from .api_setup import setup_apis
    setup_apis()
    sys.exit(0)

if args.test_apis:
    from .api_setup import test_apis
    test_apis()
    sys.exit(0)
```

Placed after args parsing but before profile loading - these commands don't need a profile.

**Credential loading:**
```python
# Load API credentials from .env (before fetching)
from .api_config import load_api_credentials
load_api_credentials()
```

Placed after logging setup (line ~530), before any API fetching.

### Test Coverage

**test_api_config.py (7 tests):**
1. `test_load_api_credentials_no_env_file` - No crash when .env missing, logs info
2. `test_load_api_credentials_loads_env_file` - Loads credentials from .env correctly
3. `test_get_api_key_returns_value_when_set` - Returns key when environment variable set
4. `test_get_api_key_returns_none_when_missing` - Returns None when key missing
5. `test_get_api_key_logs_warning_when_missing` - Logs warning with source name and --setup-apis suggestion
6. `test_ensure_env_example_creates_file` - Creates .env.example template with signup URLs
7. `test_ensure_env_example_does_not_overwrite` - Doesn't overwrite existing .env.example

**test_rate_limits.py (6 tests):**
1. `test_rate_limits_dict_has_expected_sources` - RATE_LIMITS dict contains adzuna and authentic_jobs
2. `test_check_rate_limit_allows_first_call` - First call returns True (not limited)
3. `test_check_rate_limit_returns_bool` - Returns boolean type
4. `test_get_rate_limit_status_returns_dict` - Returns dict with remaining/configured_rate/reset_time
5. `test_rate_limit_creates_db_file` - Creates .rate_limits/{source}.db SQLite file
6. `test_independent_source_limits` - Different sources have independent limits (separate DBs)

**Test isolation patterns:**
- `tmp_path` fixture for filesystem isolation (no shared state)
- `monkeypatch` fixture for environment variable isolation
- `caplog` fixture with `caplog.set_level(logging.INFO)` for log message assertions
- Autouse fixture `reset_limiter_cache()` clears module-level _limiters and _connections dicts
- Sleep 0.05s before closing connections to let background leaker thread finish (avoid segfault)

All tests pass cleanly with no cross-contamination.

## Decisions Made

**1. Interactive prompts with questionary**
- Match existing wizard.py pattern for consistency
- Skip-on-Enter for optional sources (user-friendly)
- Custom style for cross-platform safe colors

**2. Atomic .env writes**
- Use tempfile.mkstemp() + Path.replace() pattern from wizard.py
- Ensures .env never partially written on crash/interrupt
- fsync() before rename for durability

**3. Test isolation with fixtures**
- tmp_path for filesystem isolation
- monkeypatch for environment variable isolation
- Autouse fixture to reset module-level state between tests
- Prevents flaky tests from shared state

**4. Rate limiter cleanup timing**
- Sleep 0.05s before closing SQLite connections
- Gives background leaker thread time to finish asyncio operations
- Avoids "Cannot operate on a closed database" ProgrammingError

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**1. Test log level for caplog**
- Issue: caplog.text was empty for info-level logs in test_load_api_credentials_no_env_file
- Fix: Added `caplog.set_level(logging.INFO)` before calling load_api_credentials()
- Why: pytest caplog defaults to WARNING level, info messages not captured

**2. Rate limiter background thread segfault**
- Issue: pytest segfaulted when closing SQLite connections in fixture cleanup
- Root cause: pyrate-limiter's background leaker thread still running asyncio operations
- Fix: Added time.sleep(0.05) before closing connections in reset_limiter_cache fixture
- Why: Gives background thread time to complete leak() operations before connection closes
- Trade-off: Adds 0.05s per test (acceptable for test suite stability)

Both issues resolved during Task 2 execution with minimal impact.

## Next Phase Readiness

**Ready for Phase 13 (API Integrations):**
- ✓ API credential infrastructure tested and working
- ✓ Rate limiting infrastructure tested and working
- ✓ Interactive setup wizard for credential collection
- ✓ Validation command to verify credentials
- ✓ CLI integration complete (flags and load call in main)

**User flow enabled:**
1. User runs `job-radar --setup-apis` to configure credentials
2. User runs `job-radar --test-apis` to verify credentials work
3. User runs `job-radar` normally - credentials auto-loaded before fetching

Phase 13 can now implement Adzuna and Authentic Jobs fetchers using get_api_key() and check_rate_limit() from the tested infrastructure.

**No blockers.**

---
*Phase: 12-api-foundation*
*Completed: 2026-02-10*
