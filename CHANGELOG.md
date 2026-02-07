# Changelog

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
