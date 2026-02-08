# Architecture

**Analysis Date:** 2026-02-07

## Pattern Overview

**Overall:** Layered pipeline architecture with parallel fetching.

**Key Characteristics:**
- Linear multi-stage pipeline: fetch → filter → score → track → report
- Parallel execution for job source fetching (4-6 concurrent sources)
- Stateless processing stages with optional state persistence (tracker)
- Profile-driven query generation as single source of truth
- HTML/JSON parsing with fallback and error tolerance

## Layers

**CLI/Entry Point:**
- Purpose: Argument parsing, orchestration, and user output
- Location: `job_radar/search.py` (main function and arg handling)
- Contains: CLI argument parsing, color formatting, date filtering, file opening
- Depends on: All other modules
- Used by: External callers via `python -m job_radar`

**Query Generation:**
- Purpose: Convert candidate profile into searchable queries
- Location: `job_radar/sources.py` (build_search_queries, _HN_SKILL_SLUGS)
- Contains: Query builders for each source, skill-to-search mapping
- Depends on: Profile data structure
- Used by: Fetch orchestration layer

**Fetch & Retrieval:**
- Purpose: Parallel HTTP fetching from multiple job sources
- Location: `job_radar/sources.py` (fetch_* functions, fetch_all, fetch_with_retry wrapper)
- Contains: Site-specific parsers (Dice, HN Hiring, RemoteOK, We Work Remotely), HTML/JSON parsing, JobResult dataclass
- Depends on: HTTP cache layer, network requests
- Used by: Main orchestration

**HTTP Caching & Retry:**
- Purpose: Rate limiting, fault tolerance, and response reuse
- Location: `job_radar/cache.py`
- Contains: TTL-based file cache, exponential backoff retry logic
- Depends on: Filesystem, requests library
- Used by: All fetch operations

**Filtering & Deduplication:**
- Purpose: Filter results by date, deduplicate across fetches
- Location: `job_radar/search.py` (filter_by_date), `job_radar/sources.py` (fetch_all dedup logic)
- Contains: Date parsing with regex fallback, title+company-based dedup
- Depends on: JobResult objects
- Used by: Main pipeline after fetching

**Scoring Engine:**
- Purpose: Rate job-candidate fit (1.0-5.0 scale)
- Location: `job_radar/scoring.py`
- Contains: 6-component weighted scoring (skill match 25%, title 15%, seniority 15%, location 15%, domain 10%, response likelihood 20%), dealbreaker checking, compensation floor logic
- Depends on: JobResult, profile, staffing firm database
- Used by: Main pipeline after filtering

**Persistent Tracking:**
- Purpose: Cross-run state (job seen status, application tracking)
- Location: `job_radar/tracker.py`
- Contains: JSON file-based tracker, dedup key generation, run history (last 90 days)
- Depends on: Filesystem (results/tracker.json)
- Used by: Main pipeline for is_new annotation, stats generation

**Report Generation:**
- Purpose: Markdown report output with ranked listings
- Location: `job_radar/report.py`
- Contains: Markdown table builders, profile summary, scoring breakdowns, manual URL insertion
- Depends on: Scored results, manual URLs, tracker stats
- Used by: Main pipeline as final output step

**Utilities:**
- `job_radar/deps.py`: OS detection, Python version checking, dependency verification, auto-venv creation
- `job_radar/staffing_firms.py`: Known staffing firm lookup (penalty signal for scoring)

## Data Flow

**Primary Execution Flow:**

1. **Load Profile** → Parse JSON, validate required fields (name, target_titles, core_skills)
2. **Build Queries** → Profile → list of dicts with {source, query, location}
3. **Fetch All** → Parallel ThreadPoolExecutor(max_workers=6) → list of JobResult objects, with dedup
4. **Filter by Date** → Parse date_posted with multi-format fallback → filtered list
5. **Score** → For each JobResult, call score_job() → scored list with overall + component scores
6. **Check Dealbreakers** → Early return with 0.0 score if dealbreaker hit
7. **Track** → Load tracker.json, mark is_new flag, record run_history, save updated tracker
8. **Apply Filters** → --new-only and --min-score command-line filters
9. **Generate Report** → Build markdown, write to results/{name}_{date}.md
10. **Display Summary** → Print colored summary to terminal, optionally open file

**State Management:**

- **Profile**: Immutable input (loaded once from JSON)
- **Results**: Stateless data (JobResult objects) flowing through pipeline
- **Tracker state**: Persistent JSON file (results/tracker.json)
  - seen_jobs: {key → {first_seen, title, company, source, score}}
  - applications: {key → {status, updated}}
  - run_history: [{date, timestamp, total_results, new_results}] (last 90 days)

**Error Handling:**

- Fetch failures: Individual source failures caught, logged, empty list returned, pipeline continues
- Parse failures: Best-effort extraction with parse_confidence field (high/medium/low), low confidence penalizes score by -0.3
- Date parsing: Multi-format fallback → regex fallback → heuristic freshness check → include on parse error (inclusive strategy)
- Cache failures: Logged warning, fetch continues without cache
- Tracker load failures: Returns empty tracker, pipeline continues

## Key Abstractions

**JobResult Dataclass:**
- Purpose: Normalized job listing representation
- Examples: Created by fetch_* functions, passed through pipeline, scored, reported
- Pattern: Single canonical format with optional fields (parse_confidence, employment_type, apply_info)
- Fields: title, company, location, arrangement, salary, date_posted, description, url, source, apply_info, employment_type, parse_confidence

**Profile Dictionary:**
- Purpose: Candidate configuration and scoring rules
- Pattern: JSON file loaded once, immutable during run
- Key fields: name, target_titles, core_skills, secondary_skills, level, location, arrangement, dealbreakers, comp_floor, domain_expertise, certifications

**Score Dictionary:**
- Purpose: Detailed job-candidate fit breakdown
- Pattern: Returned by score_job(), annotated on result object
- Structure: {overall (float), components (dict of 6 scores), recommendation (str), [dealbreaker (str)], [comp_note (str)], [parse_note (str)]}

**Search Query Dictionary:**
- Purpose: Specifies which fetcher to use and what to search
- Pattern: Generated by build_search_queries(), passed to fetch_all()
- Structure: {source (str), query (str), location (optional str)}

## Entry Points

**CLI Entry Point:**
- Location: `job_radar/__main__.py` (delegates to `job_radar/search.py:main()`)
- Triggers: `python -m job_radar [args]` or `job-radar [args]` (after pip install)
- Responsibilities:
  - Parse CLI arguments (profile, date range, filters, options)
  - Load and validate profile
  - Orchestrate pipeline stages in sequence
  - Handle logging configuration
  - Provide colored terminal output with progress
  - Auto-open report if requested

**Programmatic Entry Point:**
- `fetch_all(profile, on_progress=None)` in `job_radar/sources.py`
  - Can be called directly to get raw JobResult list
  - on_progress callback for custom UI handling

- `score_job(job, profile)` in `job_radar/scoring.py`
  - Can be called on any JobResult to score it

## Cross-Cutting Concerns

**Logging:**
- Framework: Python standard logging module
- Per-module loggers: `logging.getLogger(__name__)`
- Levels: DEBUG (cache hits, fetch attempts) → INFO (fetch summaries) → WARNING (failures, issues) → ERROR (critical)
- Suppressed during progress: fetch_loggers temporarily raised to WARNING when showing progress bar

**Validation:**
- Profile: Required fields checked in load_profile() before pipeline
- Results: JobResult fields cleaned/truncated to max lengths (_MAX_TITLE=100, _MAX_COMPANY=80, _MAX_LOCATION=60)
- Dates: Multi-format fallback parsing with inclusive strategy (include on parse error)

**HTTP Requests:**
- User-Agent: Hardcoded Firefox string to avoid bot detection
- Cache: Automatic 4-hour TTL, disableable via --no-cache
- Retry: 3 attempts with exponential backoff (2^attempt seconds)
- Timeout: 15 second per request

**Output:**
- ANSI colors: Conditional on TTY + platform (Windows Terminal/VS Code support detected)
- Report: Always Markdown (no color), saved to results/ directory with timestamp
- Dry-run: Shows queries without hitting network

---

*Architecture analysis: 2026-02-07*
