# Codebase Concerns

**Analysis Date:** 2026-02-07

## Tech Debt

**Overly Broad Exception Handling:**
- Issue: Multiple modules catch generic `Exception` instead of specific exception types, hiding bugs and making error diagnostics difficult
- Files: `job_radar/sources.py` (lines 182, 286, 489, 581, 785), `job_radar/search.py` (lines 54, 230, 252)
- Impact: Errors are logged but not actionable; transient failures (network) treated the same as parse errors (data quality); difficult to add retry logic for specific failure modes
- Fix approach: Replace generic `except Exception` with specific exception types (`requests.RequestException`, `json.JSONDecodeError`, etc.). Create custom exceptions for parse failures vs. network failures. Add context managers to wrap fetchers with targeted recovery behavior.

**Fragile HTML/JSON Parsing with Silent Failures:**
- Issue: BeautifulSoup selectors and JSON field access fail silently by returning None/empty strings instead of raising errors, making it hard to detect when scraping patterns break
- Files: `job_radar/sources.py` (lines 113-182, 203-290, 527-585), specifically selectors like `soup.select_one()` and `item.get()`
- Impact: When job board HTML structure changes, fetchers return "Unknown" values without alerting that the page pattern is stale; misleads users with low-quality parsing marked as "high confidence"
- Fix approach: Add explicit validation after parsing steps. For Dice, verify that at least company and title are non-empty before marking as "high confidence". Add logging that differentiates between "page structure unrecognized" vs. "page structure recognized but field missing". Consider telemetry for parse confidence scores over time.

**Undifferentiated Data Quality Markers:**
- Issue: `parse_confidence` field (line 32 in sources.py) is binary (high/medium/low) but doesn't explain _why_ parse confidence is degraded
- Files: `job_radar/sources.py` (lines 141, 235, 250, 256), `job_radar/scoring.py` (line 63)
- Impact: Users can't distinguish between "we scraped freeform text with loose heuristics" vs. "we parsed structured data but a critical field was missing"
- Fix approach: Replace `parse_confidence` string with a dict containing confidence level + reason codes (e.g., `{"level": "medium", "reason": "no_employment_type_match"}`). Update `scoring.py` to penalize based on specific parse failure modes, not just presence/absence.

## Scaling & Performance Limitations

**Hardcoded Fetch Worker Pool Size:**
- Issue: ThreadPoolExecutor uses fixed max_workers=6 (line 773 in sources.py)
- Files: `job_radar/sources.py` (line 773)
- Impact: On a slow connection or if sources add network delays, 6 workers may bottleneck; on a faster connection, 6 is too conservative. No tuning mechanism.
- Fix approach: Make worker pool size configurable via CLI flag or environment variable (`JOB_RADAR_MAX_WORKERS`). Default to `min(10, (os.cpu_count() or 1) + 4)` heuristic. Log actual parallelism achieved.

**Cache Invalidation by Single Field:**
- Issue: HTTP cache TTL is global (4 hours) but job boards update at different rates. Dice posts multiple times per hour; RemoteOK updates less frequently. No per-source cache strategy.
- Files: `job_radar/cache.py` (lines 15, 32)
- Impact: Either all caches expire together (wasteful for slow sources) or we miss fresh Dice results (staleness issue). Cache is stored in working directory, portable but not cleared between systems.
- Fix approach: Move cache to `~/.cache/job-radar/` (platform-aware via `appdirs` or similar). Add per-source TTL config (e.g., Dice=1hr, RemoteOK=8hr). Add `--cache-age-only SOURCE` flag to refresh only one source.

**Memory Buildup in Tracker Over Time:**
- Issue: `tracker.json` stores all jobs ever seen + full run history (line 13 in tracker.py). No pagination or archival strategy.
- Files: `job_radar/tracker.py` (lines 13, 77-78 keeps last 90 days of run_history but `seen_jobs` is unbounded)
- Impact: If user runs 1000s of searches over years, `seen_jobs` dict grows linearly; tracker file becomes megabytes; JSON loading/saving gets slower
- Fix approach: Implement tiered retention: archive `seen_jobs` older than 180 days to separate file, keep recent 180 days in main tracker. Add `tracker.py` function `prune_old_jobs()` that can be called periodically or automatically after each run.

**No Parallel Report Generation:**
- Issue: Report generation is synchronous single-thread (report.py lines 21-146). With 200+ results, formatting the full markdown takes noticeable time.
- Files: `job_radar/report.py` (lines 21-146)
- Impact: On a slow machine, report generation can take 5+ seconds for large result sets; all other processing is parallelized
- Fix approach: Use concurrent.futures to batch format result entries in parallel, then join into single report. Only worthwhile if result set > 100 items; profile first.

## Security & Data Validation

**No Input Validation on Profile Loading:**
- Issue: Profile JSON is loaded with minimal validation (search.py lines 156-160 only check 3 fields)
- Files: `job_radar/search.py` (lines 147-162)
- Impact: Malformed profile (e.g., `target_titles` as string instead of list, missing `core_skills`) will cause cryptic errors deep in execution, not at load time
- Fix approach: Add a `validate_profile()` function that checks type of every field, enforces required fields, validates list/string types. Call it immediately after JSON load. Return structured error messages for each validation failure.

**Dealbreaker Matching Is Case-Insensitive but Escaping-Naive:**
- Issue: Dealbreaker matching (scoring.py line 100-103) does case-insensitive substring search without regex escaping or word boundary handling
- Files: `job_radar/scoring.py` (lines 91-105)
- Impact: User sets dealbreaker "C++" → matches "C++", "C+ +", "C#+" (false positive); user sets "Python" → matches "Python", "Monpython" (substring collision)
- Fix approach: Offer two matching modes in profile: `"simple_substring"` (current) and `"regex"` (escaped by default). Provide helper to escape special regex chars. Update scoring.py to switch based on profile setting.

**No Timeout on Network Requests in Cache Module:**
- Issue: `requests.get()` has 15-second timeout (cache.py line 73) but if a source is extremely slow, 15s may still cause UI hang. No adaptive timeout.
- Files: `job_radar/cache.py` (line 52-91)
- Impact: Slow source hangs entire fetch pipeline (though parallel executor will cancel after 15s); user perceives tool as frozen
- Fix approach: Add `--request-timeout` CLI flag (default 10s) that propagates through fetch_all → fetch_with_retry. Log slow responses (>8s) as warnings. Consider circuit breaker: if a source fails 3+ times in a row, skip it temporarily.

## Fragile Areas

**Heuristic-Based Parsing in HN Hiring with Minimal Validation:**
- Issue: HN Hiring parser (sources.py lines 193-290) relies on pipe-separated format but has fallback to freeform parsing with regex patterns. Patterns are loose and can misinterpret fields.
- Files: `job_radar/sources.py` (lines 293-396: extraction helpers)
- Why fragile: If HN Hiring changes post format or a user types a creative post (e.g., "Senior | Python | NY | Contact @twitter"), the `_parse_freeform_hn()` helper may assign fields incorrectly. Example: company extraction (lines 308-321) tries 2 patterns then falls back to first sentence, which could be description.
- Safe modification: Add integration test with 20+ real HN Hiring job posts. Verify extraction outputs against expected values. Make freeform patterns more defensive (require word boundaries, check extracted field length). Log extracted fields at DEBUG level so users can report misparses.
- Test coverage: No unit tests exist; freeform parser is entirely untested

**Skill Variant Matching Table Is Incomplete:**
- Issue: `_SKILL_VARIANTS` dict (scoring.py lines 171-195) has hardcoded skill aliases. New variants added manually; no system for discovering missing variants
- Files: `job_radar/scoring.py` (lines 170-195)
- Why fragile: User adds a skill "Python" but job posts say "python3.11" or "py3" → no match even though intent is clear. Variants like "node.js" have multiple forms listed but "golang" and "go" are missing variants like "go lang"
- Safe modification: Audit the variants table against recent job postings. Add patterns for versioned languages ("Python" → "python3", "python2", "py3", "py2"). Consider a plugin system for custom variants in profile JSON.
- Test coverage: No test for variant matching; purely integration-tested

**Score Component Weighting Is Hardcoded and Untuned:**
- Issue: Scoring weights (scoring.py lines 47-54) are fixed percentages (skill=25%, title=15%, location=15%, etc.) with no calibration against actual job fit outcomes
- Files: `job_radar/scoring.py` (lines 47-54)
- Why fragile: If user feedback shows that "response likelihood" (20% weight) is a better predictor of success than "skill match" (25%), there's no mechanism to rebalance. Weights are magic numbers with no explanation.
- Safe modification: Add scoring configuration to profile JSON: `scoring_weights: {skill_match: 0.25, title_relevance: 0.15, ...}`. Default to current weights. Document the reasoning for each weight in WORKFLOW.md. Add optional JSON schema validation.
- Test coverage: No unit tests for scoring logic; scoring is end-to-end tested only

**RegEx Patterns for Date/Salary Are Loose and May Over-Match:**
- Issue: `_SALARY_RE` and `_DATE_RE` patterns (sources.py lines 80-90) are permissive and could match text that looks like a salary/date but isn't
- Files: `job_radar/sources.py` (lines 80-90, 400-407)
- Why fragile: Example: salary regex matches "$10-20", "$100-200", "$1000-2000" without context. If a description says "grow from $50-75 impact" it matches. Date regex matches "5 days ago" but also "5 daysago" (concatenation error).
- Safe modification: Make patterns stricter: require word boundaries, require units (k, yr, hr) for salary. Validate extracted salary is in reasonable range (e.g., $15/hr to $500k/yr). Test against 50+ real job postings to ensure no false positives.
- Test coverage: No unit tests; patterns are untested

## Testing Gaps

**No Unit Tests:**
- Issue: Zero test coverage across entire codebase
- Files: No `tests/` directory
- Risk: Regression when modifying parsing, scoring, or cache logic; easy to break on refactor; new developers have no reference for expected behavior
- Priority: **High** — Add pytest-based test suite with at least 60% coverage. Start with:
  1. `test_scoring.py` — Unit tests for score_job, component scorers, skill matching
  2. `test_sources.py` — Mock fetchers to test parsing logic without hitting real websites
  3. `test_cache.py` — Test cache read/write, TTL expiry, retry logic

**No Integration Tests:**
- Issue: No end-to-end tests that run a full search against live sources
- Files: No CI/test infrastructure
- Risk: Refactoring could break the entire tool without detection; sources changing their HTML structure goes unnoticed until user runs it
- Priority: **Medium** — Add smoke tests that run against live Dice, HN Hiring APIs once per week. Alert on parser failures.

**No Error Scenario Testing:**
- Issue: No tests for network failures, malformed responses, timeout conditions
- Files: All fetchers (sources.py)
- Risk: Code paths for retries, backoff, and graceful degradation are untested; may fail under actual network stress
- Priority: **Medium** — Mock requests.RequestException, HTTP 429/500, and timeout scenarios. Verify retry logic and fallback behavior.

## Missing Critical Features

**No Resume/CV Parsing:**
- Issue: Tool requires user to manually fill in `core_skills`, `target_titles`, etc. in JSON profile
- Impact: High friction for new users; requires duplicating information from resume/LinkedIn
- Blocks: Easier onboarding, bulk profile generation from resume text

**No Application Tracking UI:**
- Issue: `tracker.py` has functions to track application status but they're never exposed in CLI or report
- Files: `job_radar/tracker.py` (lines 104-125)
- Impact: Users can call `update_application_status()` but have no way to do it interactively; feature is dead code
- Blocks: Using Job Radar as single source of truth for job search pipeline

**No Dry-Run Report Generation:**
- Issue: `--dry-run` shows queries but doesn't show what the _results_ would be scored like. User can't preview scoring without a live search.
- Files: `job_radar/search.py` (lines 297-308)
- Impact: User sets up profile, runs dry-run, gets 10 queries; no way to know if scoring will be useful without running full search with live data
- Blocks: Quick iteration on profile tuning

**No Configuration File Support:**
- Issue: All options must be passed via CLI flags; no `.job-radarrc` or `job_radar.config.json` for defaults
- Files: All of `search.py`
- Impact: Repeated typing of flags like `--min-score 3.5 --no-cache --output my_results` every run
- Blocks: Ergonomic daily usage

## Known Bugs

**Cache Path Issues on Windows:**
- Issue: Cache path uses `os.getcwd()` which may be unpredictable on Windows; cache dir not cleaned up
- Files: `job_radar/cache.py` (line 14)
- Symptoms: Large .cache directory accumulates in project root; multiple runs create separate caches in different working directories; `--no-cache` flag doesn't clear old cache
- Workaround: Manually delete `.cache/` directory
- Fix: Use `~/.cache/job-radar/` via platform-aware paths; implement cache cleanup on startup if age > max

**Date Filtering Edge Case:**
- Issue: If job date can't be parsed and doesn't contain freshness keywords, it's silently excluded (search.py line 229)
- Files: `job_radar/search.py` (lines 195-233)
- Symptoms: Real jobs are missing from results with no indication why. Log message is not shown to user (happens during background filtering)
- Workaround: Use `--from 2000-01-01 --to 2099-01-01` to disable date filtering
- Fix: When a date can't be parsed, log at INFO level (visible to user) and include the job anyway with confidence penalty

**Skill Variants Don't Handle Fuzzy Matching:**
- Issue: If a job posting says "NodeJS" (no dot) but profile lists "node.js" (with dot), no match occurs
- Files: `job_radar/scoring.py` (lines 202-224, variant matching)
- Symptoms: Job that should match 4/5 core skills only matches 3/5 because variant handling doesn't account for punctuation normalization
- Workaround: Add both "node.js" and "nodejs" to variants table
- Fix: Normalize skills before matching: remove dots, dashes, spaces; match lowercase; then check original variant table

**Report Generation Fails Silently on Bad Output Directory:**
- Issue: If `--output` directory path can't be created (permission error), `os.makedirs()` silently fails and report is written to wrong location
- Files: `job_radar/report.py` (line 52)
- Symptoms: User specifies `--output /root/results` but file is written to `results/` instead; no error shown
- Workaround: Verify directory exists before running
- Fix: Check `os.access(output_dir, os.W_OK)` before attempting write; raise with clear error if not writable

## Dependencies at Risk

**No Pinned Versions in pyproject.toml:**
- Risk: `beautifulsoup4` and `requests` have no version constraints; future major versions could break compatibility
- Files: `job_radar/pyproject.toml` (line 11)
- Impact: `pip install -e .` may install breaking changes; reproducibility issue; CI may pass locally but fail in production with newer versions
- Migration plan: Pin to current stable versions (e.g., `requests>=2.31,<3.0`). Use `pip-compile` or similar to lock transitive dependencies. Test against latest patch versions monthly.

**BeautifulSoup4 Parser Not Specified:**
- Risk: BeautifulSoup defaults to system's best available parser; might differ across machines (html.parser vs lxml vs html5lib)
- Files: `job_radar/sources.py` (lines 112, 204, 527)
- Impact: HTML parsing could produce different results on different systems; parse output is non-deterministic
- Fix: Explicitly specify parser in all `BeautifulSoup()` calls: `BeautifulSoup(body, "html.parser")` (already done in code, but make it explicit everywhere)

**Single Source of Truth for Constants:**
- Risk: Field length limits (`_MAX_TITLE`, etc.) are defined locally in `sources.py` but used in scoring/report without visibility to relationship
- Files: `job_radar/sources.py` (lines 47-49), `job_radar/report.py` (line 10-17)
- Impact: If max title length is increased, report formatting logic doesn't update; could cause markdown table corruption
- Fix: Move all constants to a `job_radar/constants.py` file; import in all modules

---

*Concerns audit: 2026-02-07*
