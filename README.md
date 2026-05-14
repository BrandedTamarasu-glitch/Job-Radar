# Job Radar

A desktop job search tool that searches multiple job boards, scores listings against your profile, and generates ranked reports. Available as both a **desktop GUI application** (double-click to launch) and a **CLI** for power users and scripting. Features include multi-source search (11 API sources: Dice, HN Hiring, RemoteOK, We Work Remotely, Adzuna, Authentic Jobs, JSearch, USAJobs, SerpAPI, Jobicy, hiring.cafe + 4 manual URLs: Wellfound, Indeed, LinkedIn, Glassdoor), PDF resume import, fuzzy skill matching, user-configurable scoring weights, cross-source deduplication with richness scoring, real-time API quota tracking, in-app auto-updates, and dual-format HTML and Markdown reports with shortlist state, compact/detail review, keyboard navigation, application status tracking, and WCAG 2.1 Level AA accessibility.

## What's New in v2.5.0

- **More precise GUI searches:** Presets, source toggles, company filters, must-have and nice-to-have skill controls, location strictness, and freshness presets are now available directly from the GUI.
- **Application follow-through:** The GUI now includes an Applications tab, application notes/next actions, follow-up queueing, timeline-aware CSV export, and report filtering for rejected/skipped entries.
- **Performance visibility:** Search summaries and Settings now show source timing, source health history, cache hit/miss counters, slowest-source diagnostics, source-specific cache TTLs, and improved cancellation boundaries.
- **Faster report review:** Reports now include shortlist state, keyboard navigation, compact/detail mode, mobile review improvements, why-this-matched summaries, filtered-out explanations, and grouped must-have/nice-to-have skill callouts.

## Installation

### Download

Download the latest release for your platform from the [GitHub Releases page](https://github.com/BrandedTamarasu-glitch/Job-Radar/releases/latest):

- **Windows (Recommended):** `Job-Radar-Setup-vX.X.X.exe` — NSIS installer with Start Menu shortcuts and Add/Remove Programs integration
- **Windows (Portable):** `job-radar-vX.X.X-windows.zip` — No installation required
- **macOS (Recommended):** `Job-Radar-vX.X.X-macos.dmg` — Drag-to-Applications installer with file associations
- **macOS (Portable):** `job-radar-vX.X.X-macos.zip` — No installation required
- **Linux:** `job-radar-vX.X.X-linux.tar.gz` — Extract and run

> **IMPORTANT: Security Warnings**
>
> These are unsigned executables because code signing certificates cost $300-500/year. This is normal for open-source tools distributed as standalone applications.
>
> **You will see security warnings:**
> - **Windows SmartScreen:** Click "More info" then click "Run anyway"
> - **macOS Gatekeeper:** Right-click the app and select "Open", or System Settings → Privacy & Security → "Open Anyway" (first launch only)
> - **Antivirus software:** May flag the executable as suspicious - this is a false positive common with PyInstaller-packaged applications
>
> These warnings do NOT mean the software is malicious. The source code is publicly available in this repository for inspection.

Each release includes two executables:
- **`job-radar-gui`** (or `job-radar-gui.exe`) — Desktop GUI application (recommended for most users)
- **`job-radar`** (or `job-radar.exe`) — Command-line interface for power users and scripting

### Windows

**Option 1: NSIS Installer (Recommended)**

1. Download `Job-Radar-Setup-vX.X.X.exe` from the Releases page
2. Double-click the installer to run it
3. When Windows SmartScreen appears, click "More info" then "Run anyway"
4. Follow the setup wizard to choose installation location and shortcuts
5. Launch Job Radar from the Start Menu or Desktop shortcut
6. The GUI will guide you through creating your profile

The installer includes:
- Start Menu shortcuts for GUI and CLI
- Desktop shortcut (optional)
- Add/Remove Programs integration
- Automatic file association for `.jobprofile` files
- GUI uninstall option in Settings tab

**Option 2: Portable ZIP (No Installation)**

1. Download `job-radar-vX.X.X-windows.zip` from the Releases page
2. Right-click the ZIP file and select "Extract All"
3. Open the extracted `job-radar` folder
4. Double-click **`job-radar-gui.exe`** to launch the GUI application
5. When Windows SmartScreen appears, click "More info" then "Run anyway"
6. The GUI will guide you through creating your profile

### macOS

**Option 1: DMG Installer (Recommended)**

1. Download `Job-Radar-vX.X.X-macos.dmg` from the Releases page
2. Double-click the DMG file to mount it
3. Drag `JobRadar.app` to the Applications folder shown in the window
4. Eject the DMG (right-click → Eject)
5. Remove the quarantine attribute (required for unsigned apps):
   ```bash
   xattr -d com.apple.quarantine /Applications/JobRadar.app
   ```
6. **Double-click `JobRadar.app`** in Applications to launch the GUI
7. When prompted by Gatekeeper, right-click the app and select "Open", or go to System Settings → Privacy & Security → "Open Anyway"

The installer includes:
- Drag-to-Applications installation
- Automatic file association for `.jobprofile` files
- GUI uninstall option in Settings tab

**Option 2: Portable ZIP (No Installation)**

1. Download `job-radar-vX.X.X-macos.zip` from the Releases page
2. Double-click the ZIP file to extract it
3. Drag `JobRadar.app` to your Applications folder (optional but recommended)
4. Remove the quarantine attribute (required for unsigned apps):
   ```bash
   xattr -d com.apple.quarantine /Applications/JobRadar.app
   ```
5. **Double-click `JobRadar.app`** to launch the GUI

**Alternative: Run CLI from Terminal**

For advanced users or scripting:
```bash
# Run CLI directly
/Applications/JobRadar.app/Contents/MacOS/job-radar

# Or create an alias
echo 'alias job-radar="/Applications/JobRadar.app/Contents/MacOS/job-radar"' >> ~/.zshrc
source ~/.zshrc
```

### Linux

1. Download `job-radar-vX.X.X-linux.tar.gz` from the Releases page
2. Extract the archive:
   ```bash
   tar -xzf job-radar-vX.X.X-linux.tar.gz
   ```
3. Launch the GUI:
   ```bash
   ./job-radar/job-radar-gui
   ```
   Or use the CLI:
   ```bash
   ./job-radar/job-radar
   ```
4. If you see "Permission denied", make the files executable:
   ```bash
   chmod +x job-radar/job-radar job-radar/job-radar-gui
   ```

## Quick Start

### GUI (Recommended)

1. **Launch `job-radar-gui`** (double-click the executable)
2. **Create your profile** on first launch:
   - **Upload PDF resume** (recommended) — automatically extracts name, skills, titles, and experience
   - **Fill manually** — form fields for name, skills, titles, experience, location, and preferences
3. **Click "Run Search"** to start searching job boards
4. **Watch progress** as each source is queried (with per-source job counts)
5. **Click "Open Report"** to view ranked results in your browser

On subsequent launches, you'll go straight to the Search tab. Use the Profile tab to edit your settings anytime.

**Additional GUI Features:**
- **Settings Tab:** Configure API keys, adjust scoring weights, set staffing firm preference, view API quota usage, and uninstall the app
- **Scoring Customization:** Fine-tune the 6 scoring components (skills, seniority, etc.) with sliders and see live preview of score changes
- **API Quota Tracking:** Real-time display of API usage (e.g., "15/100 daily searches used") with color-coded warnings
- **Uninstall:** Clean removal of all app data with optional backup creation

### CLI

The CLI is available for power users and scripting:

1. **Run `job-radar`** from your terminal
2. On first launch, the **interactive wizard** guides you through profile setup
3. **Search runs automatically** after the wizard completes
4. **View your results** in the HTML report that opens in your browser

On subsequent launches, the search runs directly with your saved profile.

### Updating Your Profile

After initial setup, you can update your profile without re-running the full wizard:

```bash
# View your current profile
job-radar --view-profile

# Interactive editor — select a field, change it, see diff, confirm
job-radar --edit-profile

# Quick CLI updates for scripted workflows
job-radar --update-skills "python,react,typescript"
job-radar --set-min-score 3.5
job-radar --set-titles "Backend Developer,SRE"
```

All profile updates use atomic writes (no corruption risk) and create automatic backups.

### Using Your Report

The HTML report includes interactive features and visual hierarchy to help you scan results quickly:

**Visual Hierarchy:**
- **Hero Jobs (4.0+):** Top matches appear in an elevated section at the top with distinct styling and "Top Match" badges
- **Color-coded tiers:** Green (4.0+), Cyan (3.5-3.9), Indigo (2.8-3.4) with colorblind-safe indicators
- **Responsive design:** Adapts from desktop (11 columns) → tablet (7 columns) → mobile (stacked cards)

**Interactive Features:**
- **Copy URL** buttons on each job listing for quick clipboard access
- **Copy All Recommended** button to batch-copy all high-scoring job URLs
- **Keyboard shortcuts:** Press `C` to copy a focused job's URL, `A` to copy all recommended URLs
- **Status tracking:** Mark jobs as Applied, Interviewing, Rejected, or Offer — status persists across sessions
- **Filtering:** Hide jobs by status (Applied, Rejected, Interviewing, Offer) with filter state persistence
- **CSV Export:** Download all visible job results as a spreadsheet (UTF-8, Excel-compatible)
- **Print-optimized:** Press Cmd+P/Ctrl+P for clean offline output with preserved tier colors

### Optional: API Credentials

Job Radar works out-of-the-box with 7 free sources (Dice, HN Hiring, RemoteOK, We Work Remotely, Jobicy, hiring.cafe + 4 manual URLs). To expand coverage with additional API sources, configure API keys:

**GUI Method (Recommended):**
1. Open the **Settings** tab in the Job Radar GUI
2. Scroll to the API Configuration section
3. Enter your API keys and click **Test** to validate
4. View real-time quota usage for each API

**CLI Method:**
```bash
job-radar --setup-apis
```

**Available API Sources:**
- **Adzuna** (requires API key) — Job aggregator with global coverage
- **Authentic Jobs** (requires API key) — Creative and tech job board
- **JSearch** (requires API key) — Google Jobs aggregator (LinkedIn, Indeed, Glassdoor, company sites)
- **USAJobs** (requires API key) — Federal government job listings
- **SerpAPI** (requires API key) — Alternative Google Jobs aggregator
- **Jobicy** (no key required) — Remote job listings (rate limited: 1/hour)
- **hiring.cafe** (no key required) — Tech job aggregator (rate limited: 60/hour)

The wizard will guide you through obtaining and configuring API credentials. API keys are optional but significantly expand job coverage.

For advanced usage and all available options, run:
```bash
job-radar --help
```

## Uninstalling

### GUI Uninstall (Recommended)

The easiest way to uninstall Job Radar is through the built-in GUI uninstaller:

1. **Launch Job Radar GUI**
2. Go to the **Settings** tab
3. Scroll to the **Uninstall** section at the bottom
4. **Optional:** Click "Create Backup" to save your profile and config before uninstalling. Reports and tracker data are not included in this ZIP; copy reports separately if you want to keep them.
5. Check the "I understand this will delete all Job Radar data" checkbox
6. Click the red "Uninstall" button
7. Review the confirmation dialog showing exactly what will be deleted
8. Confirm to proceed

The GUI uninstaller will:
- Remove profile, config, cache, reports, backups, and tracker data
- Remove rate limit databases from the app data directory
- Remove cached data
- On macOS: Move the app bundle to Trash
- On Windows (NSIS installer): Unregister from Add/Remove Programs and remove shortcuts

### Manual Uninstall

#### Windows (NSIS Installer)

1. **Uninstall via Add/Remove Programs:**
   - Press `Win+R`, type `appwiz.cpl`, press Enter
   - Find "Job Radar" in the list
   - Click "Uninstall" and follow the prompts
   - The uninstaller offers a GUI option with backup capability

2. **Or manually delete:**
   - Delete the installation folder (default: `C:\Program Files\Job Radar`)
   - Delete Job Radar app data from the platform application data directory

#### Windows (Portable ZIP)

1. Delete the `job-radar` folder (wherever you extracted it)
2. Delete Job Radar app data from the platform application data directory

#### macOS (DMG or ZIP)

**For unsigned apps like Job Radar, you cannot simply drag to Trash. Follow these steps:**

1. **Remove the app bundle:**
   ```bash
   sudo rm -rf /Applications/JobRadar.app
   ```
   Enter your password when prompted.

2. **Delete configuration files:**
   Delete Job Radar app data from `~/Library/Application Support/JobRadar`.

3. **Clear legacy tracker data:** if present, remove `results/tracker.json` from the directory where you launched Job Radar.

**Why sudo is needed:** macOS prevents unsigned apps from being deleted normally as a security measure. The `sudo rm` command bypasses this restriction.

#### Linux

1. Delete the extracted `job-radar` directory
2. Delete configuration files:
   ```bash
   rm -rf ~/.local/share/JobRadar
   ```
3. Clear legacy tracker data by removing `results/tracker.json` from the directory where you launched Job Radar, if present.

## Runtime Data Locations

Job Radar stores user data outside the application bundle:

| Data | Location |
|---|---|
| Profile | app data `profile.json` |
| Config | app data `config.json` |
| Reports | app data `results/` by default, or `--output DIR` |
| HTTP cache | app data `cache/` |
| Rate limits | app data `rate_limits/` |
| Backups | app data `backups/` |
| Tracker | app data `results/tracker.json`; existing launch-directory trackers are read as a legacy fallback |
| Error log | home directory `job-radar-error.log` |

## Score Ratings

| Score | Rating | Action |
|---|---|---|
| 4.0+ | Strong Recommend | Apply immediately |
| 3.5-3.9 | Recommend | Worth applying |
| 2.8-3.4 | Worth Reviewing | Read the full posting first |
| < 2.8 | Excluded from report | |

## Command Reference

### Search Options

| Flag | Description |
|---|---|
| `--min-score N` | Minimum match score (1.0-5.0, default: 2.8) |
| `--new-only` / `--no-new-only` | Only show new (unseen) results (default: false) |
| `--from YYYY-MM-DD` | Start date for job postings (default: 48 hours ago) |
| `--to YYYY-MM-DD` | End date for job postings (default: today) |
| `--preset NAME` | Apply a saved search preset for this run |
| `--list-presets` | Show available search presets and exit |

### Output Options

| Flag | Description |
|---|---|
| `--output DIR` | Output directory for reports (default: `results/`) |
| `--no-open` | Don't auto-open report in browser after generation |
| `--demo-report` | Generate a sample report without fetching jobs or requiring a profile |

### Profile Options

| Flag | Description |
|---|---|
| `--profile PATH` | Path to candidate profile JSON file |
| `--config PATH` | Path to config file (default: auto-detect) |
| `--view-profile` | Display your current profile settings and exit |
| `--edit-profile` | Launch interactive profile editor |
| `--update-skills "a,b,c"` | Replace skills list and exit (comma-separated) |
| `--set-min-score N` | Set minimum score threshold (0.0-5.0) and exit |
| `--set-titles "a,b"` | Replace target titles and exit (comma-separated) |
| `--validate-profile PATH` | Validate a profile JSON file and exit |

### Accessibility Options

| Flag | Description |
|---|---|
| `--no-color` | Disable all terminal colors (also respects `NO_COLOR` env var) |

### Developer Options

| Flag | Description |
|---|---|
| `--dry-run` | Show search queries without fetching data |
| `--verbose` / `-v` | Enable debug logging |
| `--no-cache` | Disable HTTP response caching (force fresh fetches) |
| `--clear-cache` | Remove cached HTTP responses and exit |
| `--no-wizard` | Skip setup wizard (for automated testing) |
| `--version` | Show version number and exit |

Generate a sample report to preview the ranked report experience without API keys or live job fetching:

```bash
job-radar --demo-report --no-open
```

Use saved presets to run common searches without editing your profile:

```bash
job-radar --list-presets
job-radar --preset remote-backend
job-radar --preset local-hybrid
job-radar --preset contract
```

### Examples

```bash
# Basic search (uses saved profile from wizard)
job-radar

# Search with higher quality threshold
job-radar --min-score 3.5

# Only show new listings from the last week
job-radar --from 2026-02-01 --new-only

# Search a specific date range
job-radar --from 2026-02-01 --to 2026-02-06

# Use a specific profile file
job-radar --profile path/to/profile.json

# Fresh fetch with debug logging
job-radar --no-cache -v

# Limit parallel source queries on slow or constrained networks
JOB_RADAR_MAX_WORKERS=3 job-radar

# Lower HTTP request timeout for flaky sources
JOB_RADAR_REQUEST_TIMEOUT=8 job-radar

# Lower slow-source warning threshold for diagnostics
JOB_RADAR_SLOW_QUERY_SECONDS=5 job-radar

# Preview queries without running them
job-radar --dry-run
```

## Development

### From Source

If you're a developer who wants to run from source or contribute to the project:

```bash
# Clone the repository
git clone https://github.com/BrandedTamarasu-glitch/Job-Radar.git
cd Job-Radar

# Install in development mode with test dependencies
pip install -e .[dev]

# Run the GUI
python -m job_radar

# Run the CLI (pass any flag)
python -m job_radar --help
```

**Requirements:** Python 3.10+ (macOS, Linux, or Windows). GUI requires `customtkinter` (included in dependencies).

### Running Tests

The project includes a comprehensive test suite with 888 automated tests:

```bash
# Install dev dependencies
pip install -e .[dev]

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_scoring.py
```

### Validation Checklist

Before opening a PR or cutting a release:

```bash
# Confirm runtime metadata
python -m job_radar --version

# Run all tests
pytest tests/

# Smoke-test CLI help
python -m job_radar --help
```

For release builds, also run the platform build script and smoke-test the generated `job-radar --version` executable from `dist/`.

**Test coverage:**
- Scoring functions (44 tests) - validates all `_score_*` functions, required-skill matching, expected score bands, and parametrized edge cases
- Scoring config (25 tests) - validates scoring weights, staffing preference, normalization, live preview
- Match calibration (5 tests) - validates broader, balanced, strict, and custom search calibration behavior
- Saved searches (18 tests) - validates recent search storage, named search storage, run metadata, review-count metadata, previous-run deltas, run summary display, config normalization, deduplication, deletion, history caps, and labels
- Review state (5 tests) - validates persisted shortlist, dismissed, and maybe-later search-result review states
- Applications export (3 tests) - validates application pipeline CSV rows, timeline summaries, CSV import normalization, and UTF-8 CSV output
- Application templates (5 tests) - validates follow-up, recruiter response, and cover-letter note template rendering
- Applications view model (9 tests) - validates grouped pipeline statuses, note-only entries, template note appending, status-menu mappings, and GUI detail-input normalization
- Tracker functions (27 tests) - validates deduplication, pruning, app-data storage, application notes/next actions, timeline recording, follow-up queueing, application import merging, application-status report filtering, source health history, and stats aggregation with tmp_path isolation
- Config module (24 tests) - validates config file parsing, CLI override, defaults, validation
- Wizard (38 tests) - validates setup flow, PDF integration, navigation, error handling
- API integration (61 tests) - validates all 11 API sources, mappers, rate limiting, source selection, cache stats propagation, per-source cache TTLs, diagnostics-driven TTL overrides, source cancellation boundaries, manual source links, deduplication
- API config (18 tests) - validates API key storage, validation, GUI integration, quota tracking
- Cache (14 tests) - validates HTTP cache lifecycle, request timeout handling, cache counters, and custom TTL expiry
- Rate limits (16 tests) - validates rate limiter cleanup, shared backends, config loading, quota queries
- Review state view model (3 tests) - validates compact GUI review queue summary text
- Source diagnostics view model (7 tests) - validates source-health priority, diagnostics, source-control recommendations, cache freshness, and cache totals for Settings
- PDF parser (34 tests) - validates extraction, validation, Unicode support, error handling
- Report generation (52 tests) - validates HTML/Markdown output, clipboard UI, status tracking, persisted shortlist/maybe-later/dismiss review state, keyboard navigation, compact/detail view, match summaries, filtered-out explanations, grouped skill callouts, large-report row caps, mobile layout, accessibility
- UX polish (69 tests) - validates banner, help text, progress messages, maintenance commands, error handling
- GUI search summary (25 tests) - validates search completion, source warnings, per-source timing, cache counters, cache controls, cancellation boundaries, progress normalization, GUI preset application, automated/manual source selection, company filters, application-status report filtering, must-have and nice-to-have skill controls, location strictness, freshness presets, and profile-aware zero-result guidance
- GUI onboarding (23 tests) - validates first-run demo report access, welcome/search feedback handling, Search tab profile-readiness guidance, profile-form field hints, profile-aware zero-result guidance wiring, non-blocking recent-search recording, recent-search reapply controls, named saved-search controls, review queue summaries, Applications next-action queue/direct edit wiring, and run metadata recording
- Demo report (2 tests) - validates no-network sample profile/jobs and report generation
- Profile readiness (7 tests) - validates onboarding readiness status, missing required fields, scoring-signal recommendations, match-quality recommendations, and guidance prioritization
- Profile manager (24 tests) - validates atomic writes, default scoring/staffing setup, backups, rotation, schema migration, validation
- Profile display (16 tests) - validates formatted output, field filtering, NO_COLOR compliance
- Profile editor (23 tests) - validates field menu, diff preview, editing, validator reuse
- CLI update flags (40 tests) - validates validators, handlers, mutual exclusion, integration
- Uninstaller (14 tests) - validates backup creation, path enumeration, cleanup scripts, platform detection
- Deduplication (28 tests) - validates fuzzy cross-source dedup, richness scoring, multi-source mapping
- Entry integration (46 tests) - validates GUI/CLI entry points, wizard flow, error handling
- Auto-update (42 tests) - validates detection, download, SHA256 verification, installer launch, skip version
- Release verification (4 tests) - validates release bundle/installer artifact expectations and failure diagnostics
- Browser (12 tests) - validates report opening, platform detection, error handling
- Paths (16 tests) - validates config directory resolution, platform compatibility

## Active Product Iteration

The next product iteration is tracked in `.planning/PRODUCT_ITERATION_SPRINTS_K_O.md`:

- **Sprint K:** application editing and templates
- **Sprint L:** search review workspace
- **Sprint M:** source health controls
- **Sprint N:** data portability and recovery
- **Sprint O:** performance and release trust

### Building Executables

To build standalone executables for distribution:

```bash
# Windows
scripts\build.bat

# macOS and Linux
./scripts/build.sh
```

Build artifacts are created in the `dist/` directory.

## Further Reading

- [WORKFLOW.md](WORKFLOW.md) - Full documentation: profile field reference, scoring rubric breakdown, source details, customization options, and daily workflow tips
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [FAQ.md](FAQ.md) - Frequently asked questions
