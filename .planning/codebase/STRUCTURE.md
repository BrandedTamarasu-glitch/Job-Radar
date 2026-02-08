# Codebase Structure

**Analysis Date:** 2026-02-07

## Directory Layout

```
Job-Radar/
├── job_radar/              # Main package
│   ├── __init__.py         # Package init
│   ├── __main__.py         # Entry point for python -m job_radar
│   ├── search.py           # CLI orchestrator and main() function
│   ├── sources.py          # Job fetchers and query builders
│   ├── scoring.py          # Scoring engine
│   ├── report.py           # Markdown report generator
│   ├── tracker.py          # Cross-run state persistence
│   ├── cache.py            # HTTP caching and retry logic
│   ├── deps.py             # OS detection and dependency checking
│   └── staffing_firms.py   # Staffing firm database for scoring
├── profiles/               # Candidate profile directory
│   └── _template.json      # Template for new profiles
├── .cache/                 # HTTP response cache (generated at runtime)
├── results/                # Report output directory (generated at runtime)
│   └── tracker.json        # Cross-run job tracking (generated at runtime)
├── .planning/              # GSD planning documents
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # User guide
├── WORKFLOW.md             # Detailed documentation and scoring rubric
├── CHANGELOG.md            # Version history
└── LICENSE                 # MIT license

```

## Directory Purposes

**job_radar/**
- Purpose: Core application package
- Contains: Python modules for fetching, scoring, reporting
- Key files: See below

**profiles/**
- Purpose: Candidate profile configurations
- Contains: JSON files (one per candidate/job search profile)
- Key files: `_template.json` (template for new profiles)
- User action: Copy `_template.json` to create a new profile, edit to add candidate details

**.cache/**
- Purpose: HTTP response caching for faster re-runs
- Generated: Yes (created at first fetch if not present)
- Committed: No (.gitignore'd)
- TTL: 4 hours per response

**results/**
- Purpose: Report output and cross-run tracking
- Generated: Yes (created at first report generation)
- Committed: No (.gitignore'd)
- Contents:
  - Markdown reports: `{candidate_name}_{YYYY-MM-DD}.md`
  - tracker.json: Persistent job dedup and run history (last 90 days)

## Key File Locations

**Entry Points:**
- `job_radar/__main__.py`: CLI invocation handler (delegates to search.py:main())
- `job_radar/search.py` (main function, line 260): Primary orchestrator, handles CLI args, logging, pipeline execution

**Configuration:**
- `pyproject.toml`: Package metadata, Python version (≥3.10), dependencies (requests, beautifulsoup4)
- `profiles/_template.json`: Profile schema and example values
- `job_radar/cache.py` (lines 14-15): _CACHE_DIR, _CACHE_MAX_AGE_SECONDS (4 hours)
- `job_radar/tracker.py` (line 13): _TRACKER_PATH (results/tracker.json)

**Core Logic:**
- `job_radar/search.py`: CLI arg parsing (line 87), profile loading (line 147), date filtering (line 195), main pipeline orchestration (line 260)
- `job_radar/sources.py`: Job fetchers (fetch_dice line 98, fetch_hn_hiring, fetch_remoteok line 415, fetch_weworkremotely line 505), query builder (line 703), parallel orchestration (line 747)
- `job_radar/scoring.py`: Scoring engine (score_job line 11), 6-component weighted scoring, dealbreaker checking (line 91)
- `job_radar/report.py`: Report generation (generate_report line 21)
- `job_radar/tracker.py`: Cross-run tracking (mark_seen line 43, get_stats line 84)

**Utilities:**
- `job_radar/cache.py`: HTTP caching (fetch_with_retry line 52, clear_cache line 94)
- `job_radar/deps.py`: Dependency checking, OS detection, venv creation
- `job_radar/staffing_firms.py`: Staffing firm lookup for scoring penalty

**Testing:**
- Not present (no test directory or test files)

## Naming Conventions

**Files:**
- Module naming: lowercase with underscores (e.g., `search.py`, `staffing_firms.py`)
- Profile files: `{candidate_name}.json` in profiles/ directory
- Report files: `{candidate_name_lowercase}_{YYYY-MM-DD}.md` in results/ directory
- Cache files: SHA256(url)[:16].json in .cache/ directory

**Directories:**
- Package dir: lowercase package name (`job_radar`)
- Config dirs: lowercase (`profiles`, `results`, `.cache`)

**Functions & Variables:**
- Private module functions: Prefix with underscore (e.g., `_colors_supported()`, `_parse_arrangement()`, `_clean_field()`)
- Logger variables: `log = logging.getLogger(__name__)` per module
- Constants: UPPERCASE (e.g., `STAFFING_FIRMS`, `HEADERS`, `_MAX_TITLE`)

**Classes:**
- PascalCase: `_Colors` (line 58 in search.py), `JobResult` (line 18 in sources.py)

## Where to Add New Code

**New Job Source Fetcher:**
- Implementation: Add function `fetch_{source_name}(query: str, location: str = "") → list[JobResult]` in `job_radar/sources.py`
- Update query builder: Add entry in `build_search_queries()` to generate queries for the new source
- Update fetch_all: Add case in `run_query()` dispatch to call the new fetcher
- Pattern example: See `fetch_dice()` (line 98), `fetch_remoteok()` (line 415), `fetch_weworkremotely()` (line 505)

**New Scoring Component:**
- Implementation: Add `_score_{component}(job, profile) → dict` function in `job_radar/scoring.py`
- Integration: Call in `score_job()` main function, add to weights calculation
- Pattern: Return dict with "score" key (0.0-5.0) and "reason" key (explanation)
- Example: See `_score_skill_match()`, `_score_title_relevance()`

**New Report Section:**
- Implementation: Add markdown generation code in `generate_report()` function in `job_radar/report.py`
- Pattern: Append to `lines` list, use helper functions like `_make_snippet()` for text sanitization
- Example: Profile summary section (lines 78-80), results table (lines 96-120)

**New CLI Option:**
- Implementation: Add argument in `parse_args()` function in `job_radar/search.py` (line 87)
- Integration: Handle in `main()` function with conditional logic
- Pattern: Use argparse methods like `add_argument()`, store result in args namespace
- Example: `--dry-run` (line 118), `--new-only` (line 134), `--min-score` (line 139)

**New Utility/Helper:**
- Shared helpers: `job_radar/` directory (create new module or add to existing utility files)
- Module-specific helpers: Private functions in the relevant module (prefix with underscore)

## Special Directories

**.cache/**
- Purpose: HTTP response cache for 4-hour TTL
- Generated: Yes (auto-created by fetch_with_retry)
- Committed: No (in .gitignore)
- File format: JSON with {url, ts, body} keys
- Clearing: Call `cache.clear_cache()` or use `--no-cache` CLI flag

**results/**
- Purpose: Report output and cross-run tracking
- Generated: Yes (auto-created by generate_report)
- Committed: No (in .gitignore)
- Persistent data: tracker.json (not auto-cleared)
- Reports: Timestamped markdown files (one per run per profile)

**.planning/**
- Purpose: GSD/orchestrator documentation
- Contents: ARCHITECTURE.md, STRUCTURE.md, and future analysis docs
- Committed: Yes

---

*Structure analysis: 2026-02-07*
