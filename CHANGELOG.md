# Changelog

## v2.1.0 — 2026-02-14

### Source Expansion
- **4 new API sources** — JSearch (Google Jobs aggregator covering LinkedIn, Indeed, Glassdoor, company career pages), USAJobs (federal government jobs), SerpAPI (alternative Google Jobs aggregator), Jobicy (remote job listings)
- **10 total API sources** — Expanded from 6 to 10 API-based sources for broader job coverage
- **Source attribution** — Each job listing shows its original source (e.g., "via LinkedIn", "via USAJobs") for transparency
- **Real-time quota tracking** — GUI Settings tab displays API usage (e.g., "15/100 daily searches used") with color-coded warnings (orange at 80%, red at 100%)
- **Jobicy always-available** — Public API with no key required, rate limited to 1/hour per documentation
- **API setup wizard extension** — CLI `--setup-apis` wizard guides through obtaining and validating API keys for all sources
- **GUI API configuration** — Settings tab includes API key input fields with inline Test buttons for immediate validation

### Scoring Customization
- **User-configurable weights** — GUI sliders for the 6 scoring components (skills, seniority, job type, salary alignment, response likelihood, description quality) with proportional normalization
- **Staffing firm preference** — Dropdown to boost (+30%), neutralize, or penalize (-80%) staffing firm job listings
- **Live score preview** — "Sample Job" section shows real-time score breakdown with weighted components as sliders are adjusted
- **Profile schema v2** — Automatic migration from v0/v1 to v2 with backward compatibility, automatic backup creation, and graceful fallback for corrupted scoring_weights
- **Default preservation** — DEFAULT_SCORING_WEIGHTS matches hardcoded scoring.py to preserve score stability during migration
- **Triple-fallback system** — Profile weights → DEFAULT_SCORING_WEIGHTS → hardcoded .get() defaults for defense-in-depth
- **Wizard customization** — Setup wizard offers optional advanced scoring customization (defaults to False for simplicity)
- **Two-tier validation** — Inline orange warning during editing (non-blocking) + error dialog on save (blocking) for good UX

### Uninstall & Packaging
- **GUI uninstall button** — Settings tab includes red "Uninstall" button with checkbox-gated confirmation to remove all app data
- **Backup before uninstall** — Optional ZIP backup of profile and config before deletion with native file picker
- **Three-step confirmation** — Path preview → Final confirmation with checkbox → Progress provides transparency and multiple escape hatches
- **Platform-specific cleanup** — macOS .app bundle resolution for Trash, Windows NSIS uninstaller integration
- **Two-stage cleanup** — Delete data now, schedule binary deletion after exit to work while app is running
- **macOS DMG installer** — Drag-to-Applications installer with custom background, 800x500 window, automatic .jobprofile file association
- **Windows NSIS installer** — Modern UI 2 setup wizard with Desktop/Quick Launch shortcuts, Add/Remove Programs integration, .jobprofile file association
- **Conditional code signing** — Check MACOS_CERT_BASE64/WINDOWS_CERT_BASE64 env vars, skip if not set with clear Gatekeeper/SmartScreen bypass instructions
- **CI/CD automation** — GitHub Actions builds DMG and NSIS installers on tagged releases with matrix strategy (parallel builds)

### Infrastructure
- **Rate limiter cleanup** — atexit handler closes all SQLite connections and clears limiters to prevent "database is locked" errors
- **Shared backend limiters** — Sources using the same backend API (e.g., JSearch display sources: linkedin/indeed/glassdoor/jsearch_other) share a single rate limiter instance
- **BACKEND_API_MAP fallback** — Unmapped sources use source name as backend for backward compatibility
- **Config-driven rate limits** — Rate limit configs loaded from config.json instead of hardcoded values
- **Merge config overrides** — Partial rate limit overrides in config.json merge with defaults for better UX
- **Graceful degradation** — Invalid rate limit configs show warnings and use defaults instead of crashing
- **Quota query utility** — get_quota_usage() queries SQLite bucket directly for real-time quota display in GUI
- **Atomic .env writes** — Tempfile + replace prevents corruption on crashes or interrupts during API key storage

## v2.0.0 — 2026-02-13

### Desktop GUI
- **GUI application** — Double-click the executable to launch a desktop window (CustomTkinter) — no terminal needed
- **Dual-mode entry point** — Running with CLI flags (e.g., `job-radar --min-score 3.5`) uses the existing CLI path; bare invocation opens the GUI
- **Thread-safe architecture** — Queue-based messaging (100ms polling) keeps GUI responsive during search; cooperative cancellation via threading.Event
- **Modal error dialogs** — Search failures show actionable error messages in GUI with forced acknowledgment

### GUI Profile Form
- **Profile creation** — Full form with grouped sections (Identity, Skills & Titles, Preferences, Filters) — create a profile without touching the terminal
- **PDF resume upload** — File dialog to select a PDF; pre-fills form fields using existing parser with success/error feedback
- **Tag chip widget** — Reusable input for list fields (skills, titles) with Enter-to-add, X-to-remove, and duplicate prevention
- **Inline validation** — Blur validation on entry fields, save-time validation on tag widgets, with red error labels below each field
- **Dirty tracking** — Compares form snapshot against original values; shows discard confirmation dialog on cancel if changes exist
- **Edit mode** — Same form pre-filled with current profile values for editing existing profiles

### GUI Search Controls
- **Run Search button** — Click to start a job search with configurable parameters
- **Date range** — Opt-in date filtering (unchecked by default, matching CLI behavior)
- **Min score threshold** — 0.0-5.0 entry with validation
- **New-only toggle** — Switch to filter only unseen listings
- **Per-source progress** — Visual progress bar with current source name and job count during search
- **Open Report** — Completion view shows results count and button to open HTML report in default browser

### Packaging
- **Dual executables** — Separate CLI (with console) and GUI (without console) executables in distribution packages
- **CustomTkinter bundling** — Theme JSON files and OTF fonts bundled via PyInstaller `--add-data`
- **macOS entitlements** — `com.apple.security.cs.allow-unsigned-executable-memory` for Python JIT compilation
- **CI smoke tests** — `--version` test on all 3 platforms after build; CustomTkinter asset verification step
- **macOS archive fix** — `--symlinks` flag preserves symbolic links in macOS zip archives

## v1.5.0 — 2026-02-12

### Profile Infrastructure
- **Centralized profile I/O** — All profile reads/writes route through `profile_manager.py` with atomic writes (temp file + fsync + rename), preventing corruption on interrupted saves
- **Automatic backups** — Timestamped backup created before every profile update; keeps the 10 most recent, deletes older
- **Schema versioning** — Profile JSON includes `schema_version` field; legacy v0 profiles auto-migrate to v1 on load
- **Shared validation** — Single `validate_profile()` function used by wizard, interactive editor, and CLI flags with friendly error messages

### Profile Preview
- **Startup preview** — Running `job-radar` shows a formatted profile summary (name, skills, titles, experience, location, preferences) before the search begins
- **View command** — `job-radar --view-profile` displays your current profile settings and exits without running a search
- **Sectioned display** — Profile table with bordered sections (Identity, Skills, Preferences, Filters) using tabulate library
- **Quiet mode** — `--no-wizard` suppresses both the setup wizard and the profile preview

### Interactive Quick-Edit
- **Edit command** — `job-radar --edit-profile` launches an interactive editor with a categorized field menu
- **Field types** — Text fields pre-fill current value; list fields offer add/remove/replace submenu; booleans use Yes/No choice
- **Diff preview** — Before/after comparison shown before every save with "Apply this change? (y/N)" confirmation (default No)
- **Validator reuse** — All field validators imported from wizard module (zero duplication)
- **Multi-field editing** — After each save or cancel, returns to field menu for additional edits; "Done" exits

### CLI Update Flags
- **`--update-skills "python,react,typescript"`** — Replace skills list and exit without running a search
- **`--set-min-score 3.5`** — Update minimum score threshold (0.0-5.0 range enforced) and exit
- **`--set-titles "Backend Developer,SRE"`** — Replace target titles list and exit
- **Diff output** — All update flags show old/new values after saving
- **Mutual exclusion** — Update flags cannot be combined with each other or with `--view-profile`/`--edit-profile`
- **Validation** — Invalid values rejected at parse time with friendly error messages and non-zero exit code

## v1.4.0 — 2026-02-11

### Visual Hierarchy
- **Hero jobs** — Top matches (score ≥4.0) appear in an elevated section with multi-layer shadows, "Top Match" badges, and distinct styling
- **Semantic color system** — Green (4.0+), Cyan (3.5-3.9), Indigo (2.8-3.4) tier colors with CSS variables and dark mode support
- **System font stacks** — Zero-overhead fonts using OS native type for instant rendering

### Responsive Design
- **Desktop** — Full 11-column table layout
- **Tablet** — Reduced to 7 core columns at 992px breakpoint
- **Mobile** — Stacked card layout at 768px with all data preserved via `data-label` attributes
- **ARIA restoration** — JavaScript restores table semantics (`role="row"`, `role="cell"`) for screen readers when CSS transforms layout to `display: block`

### Interactive Features
- **Status filtering** — Hide/show jobs by application status (Applied, Interviewing, Rejected, Offer) with localStorage persistence
- **CSV export** — Download visible results as spreadsheet with UTF-8 BOM for Excel compatibility, RFC 4180 escaping, and formula injection protection (`=`/`+`/`-`/`@` prefix protection)

### Print & CI
- **Print stylesheet** — `@media print` rules preserve tier colors (`print-color-adjust: exact`), hide interactive chrome, prevent mid-card page breaks
- **Accessibility CI** — GitHub Actions workflow runs Lighthouse (5 runs, ≥95% median) and axe-core WCAG checks, blocking merge on failures

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
