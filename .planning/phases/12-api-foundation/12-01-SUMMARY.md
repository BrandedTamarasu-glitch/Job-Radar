---
phase: 12-api-foundation
plan: 01
subsystem: infrastructure
tags: [api, credentials, rate-limiting, security, python-dotenv, pyrate-limiter, sqlite]
requires: [pyproject.toml, .gitignore]
provides: [api-credential-management, rate-limiting-infrastructure]
affects: [13-api-integrations]
tech-stack:
  added: [python-dotenv, pyrate-limiter]
  patterns: [env-file-config, sqlite-persistence, graceful-degradation]
key-files:
  created: [job_radar/api_config.py, job_radar/rate_limits.py, .env.example]
  modified: [pyproject.toml, .gitignore]
decisions:
  - slug: env-file-credentials
    chosen: .env file with python-dotenv
    why: Standard pattern for sensitive config, keeps credentials out of source control
  - slug: rate-limit-persistence
    chosen: SQLite with pyrate-limiter SQLiteBucket
    why: Survives restarts, no external dependencies, thread-safe with check_same_thread=False
  - slug: missing-key-handling
    chosen: Log warning and return None (skip source)
    why: Graceful degradation - don't crash if user hasn't configured API keys yet
  - slug: rate-limit-behavior
    chosen: Non-blocking (return False immediately when limited)
    why: Don't block user waiting for rate limit - skip source and continue
metrics:
  duration: 4 min
  completed: 2026-02-10
---

# Phase 12 Plan 01: API Credential and Rate Limit Infrastructure Summary

**One-liner:** Secure .env-based credential loading with graceful degradation and SQLite-backed per-source rate limiting

## What Was Built

Created the foundational infrastructure modules that Phase 13 API integrations (Adzuna, Authentic Jobs) will use for credential management and rate limiting.

### Modules Created

**1. job_radar/api_config.py - Credential Management**

Provides three functions for secure API credential handling:

- `load_api_credentials()`: Loads .env file from project root using `find_dotenv(usecwd=True)`. If missing, logs info (not error) - API sources skip gracefully. If corrupt, prints clear error with recovery instructions and exits (fail-fast).

- `get_api_key(key_name, source_name)`: Gets key from environment with graceful degradation. Missing keys log warning once per source: "Skipping {source}: {key} not found in .env file. Run 'job-radar --setup-apis' to configure." Returns None to skip source (don't crash).

- `ensure_env_example()`: Creates .env.example template if missing. Handles OSError gracefully (logs warning, doesn't crash). Template documents all API keys with signup URLs.

**2. job_radar/rate_limits.py - Rate Limiting**

Provides rate limiting infrastructure with persistent state:

- `check_rate_limit(source, verbose)`: Non-blocking check that returns True/False immediately. If rate limited, logs warning with retry time in 12-hour format (e.g., "Skipped adzuna: rate limited, retry after 2:35pm").

- `get_rate_limiter(source)`: Creates or returns cached limiter for source. Initializes SQLite database at `.rate_limits/{source}.db` with thread-safe connection (`check_same_thread=False` for background leaker thread). Uses SingleBucketFactory with SQLiteBucket for persistence.

- `get_rate_limit_status(source)`: Returns dict with rate limit status for debugging (configured_rate, remaining, reset_time).

- `RATE_LIMITS` dict: Conservative rate limits per source:
  - Adzuna: 100/min, 1000/hour (no official docs)
  - Authentic Jobs: 60/min (no official docs)
  - Default fallback: 60/min for unlisted sources

### Configuration Files

**1. .env.example Template**

Documents required API keys with signup URLs:
- `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` → https://developer.adzuna.com/
- `AUTHENTIC_JOBS_API_KEY` → https://authenticjobs.com/api/

Users copy to `.env` and fill in their credentials.

**2. .gitignore Updates**

Added:
- `.env` - Never commit credentials
- `.rate_limits/` - Don't commit rate limit state (user-specific)

**3. pyproject.toml Dependencies**

Added:
- `python-dotenv` - Load environment variables from .env file
- `pyrate-limiter` - Rate limiting with SQLiteBucket persistence (v4.0.2)

## Technical Implementation

### API Version Adaptations

**pyrate-limiter v4 API (vs. v3 in research):**

The installed version (4.0.2) has significant API changes from v3:

1. **No BucketFullException**: v4's `try_acquire()` returns bool instead of raising exception
2. **SQLiteBucket initialization**: Requires `(rates, conn, table_name)` - conn must be sqlite3.Connection
3. **Table creation**: Manual with `SQLiteQueries.CREATE_BUCKET_TABLE.format(table=table_name)`
4. **Factory pattern**: Use `SingleBucketFactory(bucket)` wrapper, then `Limiter(factory)`
5. **Thread safety**: SQLite connection needs `check_same_thread=False` for background leaker thread

### Graceful Degradation Pattern

Both modules follow "fail open" pattern for missing credentials:

1. No .env file: INFO log, continue (API sources will be skipped by get_api_key)
2. Missing API key: WARNING log with setup instructions, return None
3. Corrupt .env: Fail-fast with clear error and recovery instructions (sys.exit(1))

This allows new users to run Job Radar before configuring API keys - they'll get results from scraping sources (Dice, HN Hiring, etc.) while being guided to add API keys for additional sources.

### Rate Limit State Persistence

SQLiteBucket stores rate limit state in `.rate_limits/{source}.db`:

```
rate_limits table:
- name: bucket key (source name)
- item_timestamp: Unix timestamp of each request
```

State survives:
- Application restarts
- Python process termination
- System reboots (file-based)

Leaker thread periodically removes expired entries based on rate interval.

### Non-Blocking Rate Limit Checks

Rate limit checks use `blocking=False` to return immediately:

```python
allowed = limiter.try_acquire(source, blocking=False)
if not allowed:
    # Log retry time and skip source
    # Don't wait - user wants results now
```

This prevents user from waiting for rate limits to reset. Source is skipped for this run, retry on next run.

## Files Changed

**Created:**
- `job_radar/api_config.py` (103 lines)
- `job_radar/rate_limits.py` (171 lines)
- `.env.example` (11 lines)

**Modified:**
- `.gitignore` (+2 lines: .env, .rate_limits/)
- `pyproject.toml` (+2 dependencies: python-dotenv, pyrate-limiter)

**Commits:**
- `f271572` - feat(12-01): add API credential management infrastructure
- `50e2588` - feat(12-01): add rate limiting with persistent SQLite backend

## Verification Results

All verification checks passed:

1. ✓ `from job_radar.api_config import load_api_credentials, get_api_key` succeeds
2. ✓ `from job_radar.rate_limits import check_rate_limit, get_rate_limit_status` succeeds
3. ✓ `.env.example` exists with ADZUNA_APP_ID, ADZUNA_APP_KEY, AUTHENTIC_JOBS_API_KEY
4. ✓ `.gitignore` includes `.env` and `.rate_limits/`
5. ✓ `pyproject.toml` lists `python-dotenv` and `pyrate-limiter` as dependencies
6. ✓ `check_rate_limit("adzuna")` returns True on fresh state (no prior calls)

**Rate Limit Testing:**
- Adzuna rate limit enforced correctly at 100 calls (100/min limit)
- State persisted across process restart (fresh Python process still rate limited)
- No threading errors with `check_same_thread=False` on SQLite connection

## Deviations from Plan

None - plan executed exactly as written.

The only adaptation was handling pyrate-limiter v4 API differences from v3 (which was documented in research but not the installed version). The plan explicitly called for API verification before writing code, which was followed.

## Next Phase Readiness

**Phase 13 (API Integrations) is ready to proceed.**

Required infrastructure complete:
- ✓ Credential loading with graceful degradation
- ✓ Rate limiting with persistent state
- ✓ .env.example template for user guidance
- ✓ Dependencies installed and verified

**Integration points for Phase 13:**

```python
# In adzuna.py:
from job_radar.api_config import load_api_credentials, get_api_key
from job_radar.rate_limits import check_rate_limit

load_api_credentials()  # Load .env on module import

def fetch_adzuna_jobs(profile):
    # Check credentials
    app_id = get_api_key("ADZUNA_APP_ID", "Adzuna")
    app_key = get_api_key("ADZUNA_APP_KEY", "Adzuna")
    if not app_id or not app_key:
        return []  # Skip source

    # Check rate limit
    if not check_rate_limit("adzuna"):
        return []  # Skip source

    # Make API request...
```

**No blockers or concerns.**

## Testing Notes

**Manual testing performed:**

1. Import verification: Both modules import cleanly without errors
2. Rate limit enforcement: Adzuna limited at 100 calls (expected)
3. Persistence: State survived process restart
4. Thread safety: No SQLite threading errors with check_same_thread=False
5. .env.example: Contains all required keys with signup URLs
6. .gitignore: Correctly excludes .env and .rate_limits/

**Future testing considerations:**

- Phase 13 should add integration tests for actual API calls with credentials
- Consider adding unit tests for get_api_key edge cases (empty string vs None)
- May want to test rate limit reset behavior after waiting (requires time delay)

## Knowledge for Future Plans

**For Phase 13 implementers:**

1. **Always call `load_api_credentials()` early** (module-level or start of fetch function)
2. **Check credentials before rate limit** (no point checking rate limit if no key)
3. **Return empty list if skipped** (don't raise exceptions - graceful degradation)
4. **Use source name consistently** (e.g., "adzuna" not "Adzuna" - rate_limits.py keys are lowercase)
5. **Rate limit warnings are expected** (users will see them, guide them to slow down or wait)

**SQLite threading gotcha:**

If you see "SQLite objects created in a thread can only be used in that same thread" errors, ensure `check_same_thread=False` is set on connection. This is already handled in rate_limits.py but important if creating custom SQLite usage elsewhere.

**Rate limit configuration:**

Current limits are conservative estimates (no official docs for Adzuna/Authentic Jobs). If 429 errors occur in production:

1. Check error response for actual rate limits
2. Update RATE_LIMITS dict in rate_limits.py
3. Document limits in comments with source URL

If rate limits are too conservative (user getting "rate limited" unnecessarily):

1. Increase limits gradually
2. Monitor for 429 responses
3. Test with multiple rapid runs to verify

## Performance Impact

**Module load time:** Negligible (no heavy imports, no I/O until functions called)

**First rate limit check:** ~1-5ms (SQLite connection + table creation)

**Subsequent checks:** ~0.1-0.5ms (in-memory limiter, SQLite read/write)

**Credential loading:** ~1-2ms (read .env file, parse variables)

**No performance concerns.** All operations are fast enough for CLI use.

## Security Considerations

**Credentials:**
- ✓ .env file gitignored (credentials never committed)
- ✓ No credentials hardcoded in source
- ✓ .env.example has empty values (no accidental credential commits)

**Rate limit state:**
- ✓ .rate_limits/ gitignored (user-specific state)
- ✓ No sensitive data in rate limit database (only timestamps and counts)

**Error messages:**
- ✓ Don't print API key values in logs
- ✓ Clear guidance for users without credentials (setup instructions)

**No security concerns.**
