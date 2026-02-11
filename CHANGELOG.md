# Changelog

## v1.3.0 — 2026-02-11

### Application Flow
- **One-click copy buttons** — Copy URL button on every job card and table row for instant clipboard access
- **Batch copy** — "Copy All Recommended" button copies all high-scoring (≥3.5) job URLs at once, separated by newlines
- **Keyboard shortcuts** — Press `C` to copy focused job URL, `A` to copy all recommended URLs. Modifier keys (Ctrl+C) and input fields are not intercepted
- **Toast notifications** — Notyf-powered confirmations for all clipboard and status actions with ARIA live region announcements

### Application Status Tracking
- **Status dropdown** — Mark jobs as Applied, Interviewing, Rejected, or Offer with color-coded badges on every job card and table row
- **Persistent status** — Application statuses saved to localStorage and embedded tracker.json, surviving browser refreshes and multi-day gaps
- **Bidirectional sync** — Status data hydrated from tracker.json on report generation, merged with localStorage on page load
- **JSON export** — Download pending status updates as JSON for importing into tracker.json or external tools

### Accessibility (WCAG 2.1 Level AA)
- **Skip navigation** — "Skip to main content" link as first focusable element for keyboard users
- **ARIA landmarks** — Semantic HTML structure with explicit `role="banner"`, `role="main"`, `role="contentinfo"` for screen reader navigation
- **Accessible tables** — `scope="col"` and `scope="row"` attributes on all table headers with visually-hidden caption
- **Screen reader badge context** — Score badges announce as "Score 4.2 out of 5.0" (not "4.2/5.0"), NEW badges announce as "New listing, not seen in previous searches"
- **Focus indicators** — Visible 2px outline on all interactive elements (links, buttons, dropdowns, job items) via `:focus-visible`
- **Contrast compliance** — All text meets 4.5:1 minimum contrast ratio; Bootstrap `.text-muted` overridden from #6c757d to #595959
- **ARIA live region** — Dynamic content changes (clipboard copies, status updates) announced to screen readers
- **NO_COLOR support** — `NO_COLOR=1` environment variable and `--no-color` CLI flag disable all terminal ANSI codes per no-color.org standard
- **Colorblind-safe output** — All terminal colors paired with text labels (scores show numbers, "[NEW]" tag, "Error:" prefix)
- **Screen reader documentation** — CLI help documents `--profile` flag as wizard bypass for screen reader users

## v1.2.0 — 2026-02-05

### API Sources
- **Adzuna API** — Job search via Adzuna REST API with app_id/app_key authentication and salary data extraction
- **Authentic Jobs API** — Design and creative role search with key-based authentication
- **Wellfound URLs** — Manual search URL generation with /role/r/ (remote) and /role/l/ (location) patterns

### Credential Management
- **python-dotenv** — Secure API key storage in `.env` file (gitignored) with automatic loading via `find_dotenv()`

### Rate Limiting
- **SQLite-backed limiter** — Persistent rate limiting with pyrate-limiter prevents API bans across restarts

### Deduplication
- **Cross-source matching** — rapidfuzz fuzzy matching at 85% similarity threshold prevents duplicate listings from different sources

### Resume Intelligence
- **PDF parser** — Extract name, years of experience, job titles, and skills from uploaded PDF resumes using pdfplumber
- **Wizard integration** — PDF upload option in setup wizard pre-fills profile fields with extracted data (editable before saving)
- **Validation** — Rejects image-only, encrypted, oversized, and corrupted PDFs with actionable error messages

## v1.1.0 — 2026-01-20

### Interactive Setup
- **First-run wizard** — Questionary-based interactive setup with examples, validation, and profile generation
- **Profile recovery** — Detects existing profiles and offers to reuse or recreate

### HTML Reports
- **Bootstrap 5 HTML** — Dual-format report generation (HTML + Markdown) with responsive design
- **Browser auto-launch** — Reports open automatically in the default browser with headless detection

### UX Polish
- **Progress indicators** — Source-level progress callbacks during search
- **Friendly errors** — Non-technical error messages with recovery suggestions
- **Graceful Ctrl+C** — Clean shutdown with partial results preserved

### Distribution
- **Standalone executables** — PyInstaller onedir builds for Windows, macOS (.app bundle), and Linux
- **CI/CD** — GitHub Actions tag-triggered workflow builds all platforms with pytest gates
- **Manual URLs** — Indeed, LinkedIn, Glassdoor URL generation for manual searching

## v1.0.0 — 2026-02-08

### Test Suite
- **pytest integration** — Comprehensive test suite with 48 automated tests covering scoring and tracking systems
- **Parametrized scoring tests** — All `_score_*` functions validated with normal and edge cases (21 test cases across 6 functions)
- **Dealbreaker detection tests** — Verifies exact match, substring match, and case-insensitive matching behavior
- **Salary parsing tests** — Covers all formats: "$120k", "$60/hr", "$120,000", ranges, "Not listed", None, empty strings
- **Tracker tests with isolation** — `job_key()`, `mark_seen()`, and `get_stats()` validated using tmp_path to protect production data
- **Shared test fixtures** — `sample_profile` and `job_factory` in `tests/conftest.py` for reusable test data
- **Zero failures** — All 48 tests pass in 0.03s, providing regression protection for scoring engine

### Milestone Achievement
All v1.0 features delivered:
- ✓ Fuzzy skill normalization (v0.3.0)
- ✓ Config file support (v0.4.0)
- ✓ Comprehensive test suite (v1.0.0)

## v0.4.0 — 2026-02-08

### Config File Support
- **`~/.job-radar/config.json`** — Save persistent defaults (`min_score`, `new_only`, `output`) so common flags apply automatically on every run.
- **`--config PATH`** — Load a custom config file instead of the default location.
- **CLI precedence** — Explicit CLI flags always override config file values.
- **Unknown key warnings** — Unrecognized config keys produce a named warning to stderr without aborting.

## v0.3.0 — 2026-02-07

### Fuzzy Skill Normalization
- **Case and punctuation normalization** — `NodeJS`, `node.js`, and `Node.js` all match the same skill entry. Normalization strips dots, dashes, and spaces before comparison.
- **Expanded skill variants** — Added 16 common tech entries (e.g., `postgres`/`postgresql`, `k8s`/`kubernetes`, `js`/`javascript`).
- **Bidirectional variant lookup** — Variants like `kubernetes`/`k8s` resolve symmetrically without special-casing.
- **Short skill boundary fix** — Word-boundary matching for short skills (`c`, `r`, `go`) extended to handle skills containing `#` or `+` (e.g., `C#`, `C++`) correctly.

## v0.2.0 — 2026-02-06

### Packaging
- **Installable package** — Restructured as a proper Python package (`job_radar/`). Install with `pip install -e .` and run via the `job-radar` CLI command or `python -m job_radar`.
- **pyproject.toml** — Added package metadata, dependencies (`requests`, `beautifulsoup4`), and console entry point.
- **Relative imports** — All inter-module imports converted from bare to relative (e.g., `from .cache import ...`).
- **CWD-relative paths** — Cache and tracker now store data relative to the current working directory instead of the script location, so the tool works correctly when pip-installed.

---

## v0.02 — 2026-02-06

### New Files
- **deps.py** — OS-aware dependency checker and auto-installer. Detects macOS/Linux/Windows, checks Python 3.10+ requirement, auto-installs missing packages (requests, beautifulsoup4). Handles PEP 668 externally-managed Python environments by creating a `.venv` and re-executing the script inside it.
- **tracker.py** — Cross-run job tracking with deduplication. Stores seen jobs, application statuses, and run history in `results/tracker.json`. Tags results as NEW or previously seen. Reports lifetime stats (total unique jobs, avg new per run).
- **cache.py** — HTTP response caching and retry layer. Caches responses for 4 hours in `.cache/` with SHA-256 URL hashing. Retry with exponential backoff (3 attempts, 2x backoff).
- **staffing_firms.py** — Known staffing firm list for response likelihood scoring boost.

### New Sources
- **RemoteOK** fetcher (`sources.py`) — Fetches remote jobs via RemoteOK's JSON API. Extracts salary ranges, tags, and apply URLs.
- **We Work Remotely** fetcher (`sources.py`) — Scrapes WWR search results. Includes Cloudflare detection — gracefully falls back to manual-check URLs when blocked.
- **WWR manual URLs** — WWR added to the manual-check URL list alongside Indeed, LinkedIn, and Glassdoor.

### Scoring Engine Overhaul
- **Title relevance scoring** — New scoring component (15% weight) that compares job titles against the candidate's `target_titles`. Exact match = 5.0, substring match = 4.5, word overlap scored proportionally, no match = 1.5. This prevents irrelevant titles (e.g., "Sales Director") from scoring well just because description keywords overlap.
- **Rebalanced weights** — Skill match 30% → 25%, seniority 20% → 15%, domain 15% → 10%. New title relevance takes 15%. Location and response likelihood unchanged.
- **Word-boundary skill matching** — Short/ambiguous skill names (Go, AI, ML, QA, R, C, etc.) now use `\b` regex boundaries to prevent false positives. Configurable via `_BOUNDARY_SKILLS` set.
- **Skill variants** — `_SKILL_VARIANTS` dict maps alternate names and abbreviations (e.g., "P2P" → "Procure-to-Pay", ".NET" → "dotnet").
- **Compensation floor** — New `comp_floor` profile field. Jobs with listed salaries below the floor receive a 0.5-1.5 point penalty based on gap percentage.
- **Dealbreakers** — New `dealbreakers` profile field. Jobs matching any dealbreaker keyword are hard-disqualified (score 0, excluded from report).
- **Parse confidence demotion** — Low-confidence parsed listings (freeform HN posts) lose 0.3 points.

### Parser Improvements
- **Dice parser** — Switched from fragile positional field indexing to heuristic regex-based field detection. Uses patterns for salary (`$XX,XXX`), dates, employment type, and location. Much more resilient to HTML structure changes.
- **HN Hiring parser** — Added defensive parsing that detects pipe-separated vs freeform post formats. Assigns `parse_confidence` levels (high/medium/low). Truncates overly long fields. Extracts company, title, and location from freeform text using regex patterns.
- **RemoteOK matching fix** — Query matching no longer splits multi-word queries into individual words. "Full Stack Engineer" now requires all significant words present, not just "full" OR "stack" OR "engineer". Dramatically reduces false positives.
- **WWR parser fix** — Added Cloudflare challenge page detection. Multiple fallback CSS selectors for company/title/region. Falls back to link text for titles when selectors miss.

### Report Enhancements
- **Enhanced all-results table** — Added Salary, Type (employment type), and Snippet (first ~80 chars of description) columns.
- **Employment type** — New `employment_type` field on `JobResult` dataclass. Populated by all fetchers: Dice (regex), HN Hiring (text extraction), RemoteOK (API field), WWR. Values: Full-time, Contract, C2H, Part-time. Displayed in both the results table and detailed recommended roles.
- **Title match info** — Detailed recommended roles now show title relevance reasoning.
- **Talking points** — Profile `highlights` are matched against recommended jobs to generate cover letter talking points.
- **Tracker stats** — Report header shows lifetime stats: total unique jobs seen, total runs, avg new per run.

### CLI Improvements
- **`--new-only`** — Filter report to only show new (unseen) results.
- **`--min-score`** — Set custom minimum score threshold (default: 2.8).
- **`--open`** — Auto-open the report in your default application after generation.
- **`--dry-run`** — Preview search queries without fetching anything.
- **`--no-cache`** — Disable HTTP response caching for fresh fetches.
- **`--verbose` / `-v`** — Enable debug logging.
- **Progress indicator** — Displays `Fetching... 3/17 queries complete` during parallel fetch. Log output suppressed during progress to prevent interleaving.
- **Color output** — ANSI color-coded terminal output for scores, new/seen counts, and section headers.

### Date Filtering Fix
- `filter_by_date` was a no-op — every fallback branch included the result. Now properly excludes results with unparseable dates that don't contain freshness keywords (today, yesterday, ago, etc.).

### Cross-Platform Compatibility
- **Windows process handling** — Replaced `os.execv` (which spawns a second process on Windows) with `subprocess.call` + `sys.exit` for venv re-execution.
- **ANSI color support** — Detects modern Windows terminals (Windows Terminal, VS Code) via `WT_SESSION`/`TERM_PROGRAM` env vars. Falls back to enabling VT100 processing via `kernel32.SetConsoleMode`. Non-TTY output disables colors entirely.
- **Command detection** — `_command_exists` now checks `result.returncode == 0` instead of just running without error.
- **UTF-8 encoding** — All `open()` calls across cache.py, tracker.py, report.py, and search.py specify `encoding="utf-8"` to prevent `cp1252` issues on Windows.

### Parallel Fetching
- All source queries run in parallel via `ThreadPoolExecutor` with 6 workers.
- Progress callback API: `fetch_all(profile, on_progress=callback)` reports `(completed, total, source_name)` after each query finishes.
- Deduplication by (title, company) key during aggregation.

### Infrastructure
- **`.gitignore`** — Ignores `.venv/`, `.cache/`, `__pycache__/`, `results/tracker.json`.
- **Auto-venv** — If system Python is externally managed (PEP 668), automatically creates `.venv`, installs dependencies, and re-launches.

---

## v0.01 — Initial Release

- Basic `search.py` with Dice.com scraping
- Simple keyword-based scoring
- Markdown report generation
- Profile-based search queries
