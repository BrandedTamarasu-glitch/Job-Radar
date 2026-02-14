# Job Radar — Workflow

**Version 2.1.0** | [Changelog](CHANGELOG.md)

A desktop job search tool that fetches listings from 10 API sources and 4 manual URLs, scores them against your customizable profile, tracks results across runs, and generates ranked HTML + Markdown reports with interactive features and WCAG 2.1 AA accessibility. Available as both a desktop GUI application and CLI for power users.

## Prerequisites

- Python 3.10+
- Install with `pip install -e .` (see [README](README.md#install))

Or download a standalone executable from the [Releases page](https://github.com/BrandedTamarasu-glitch/Job-Radar/releases/latest) (no Python required).

## Quick Start

**GUI (Recommended):**
```bash
# Launch the GUI application
job-radar-gui
# Or double-click the executable from your file browser
```

**CLI (Power Users):**
```bash
# First launch — interactive wizard guides profile creation
job-radar

# Subsequent launches — shows profile preview, then searches
job-radar
```

By default, the search covers jobs posted within the last 48 hours. The GUI provides visual progress tracking, API quota display, scoring customization, and one-click report access.

## Full Workflow

### 1. Create a Candidate Profile

On first launch, Job Radar runs an interactive setup wizard:

1. **Choose setup method:**
   - **Upload PDF resume** (recommended) — extracts name, skills, titles, and experience automatically
   - **Fill manually** — guided prompts for each field
2. **Review and confirm** each field before saving

The wizard creates `~/.job-radar/profile.json` with your settings.

**Profile fields:**

**Required:**
- `name` — Full name
- `target_titles` — Ranked list of job titles to search (top 4 used for Dice queries)
- `core_skills` — Top 5-7 keywords (these drive scoring at full weight)

**Recommended:**
- `level` — `junior`, `mid`, `senior`, or `principal`
- `years_experience` — Total years of professional experience
- `secondary_skills` — Next 5-10 skills (counted at half weight in scoring)
- `location` — Current city/state
- `arrangement` — List of acceptable options: `remote`, `hybrid`, `onsite`
- `target_market` — Preferred job market (e.g., `Remote`, `Atlanta, GA`)
- `domain_expertise` — Industries you've worked in
- `certifications` — Professional certifications

**Filtering:**
- `comp_floor` — Minimum annual compensation in dollars (e.g., `80000`). Jobs below this threshold receive a score penalty proportional to the gap.
- `dealbreakers` — List of disqualifying keywords (e.g., `["clearance required", "C++"]`). Jobs matching any dealbreaker are completely excluded from results.

**Optional:**
- `languages` — Spoken languages
- `highlights` — 2-3 standout accomplishments. Matched against jobs to generate cover letter talking points.

**Tips:**
- `core_skills` — List only your strongest 5-7 technologies. These carry full weight.
- `secondary_skills` — Technologies you know but aren't your focus. Half weight.
- `target_titles` — Put your ideal title first. The top 4 are used as Dice search queries.
- `highlights` — Use quantified results (numbers, percentages) for better talking point matching.
- `dealbreakers` — Be specific. `"C++"` will exclude any listing mentioning C++. Case-insensitive.
- `comp_floor` — Set to `null` to skip salary filtering.

### Scoring Customization (v2.1.0+)

You can customize how jobs are scored using the GUI Settings tab:

**Scoring Weights:**
- Adjust the 6 scoring component weights (skills, seniority, job type, salary alignment, response likelihood, description quality) using sliders
- Live preview shows how weight changes affect a sample job's score
- Normalize button automatically adjusts all weights to sum to 1.0 while preserving relative ratios
- Reset button restores default weights

**Staffing Firm Preference:**
- **Boost** (+30%) — Prefer staffing firms (higher callback rates, more opportunities)
- **Neutral** (0%) — No preference (default for new profiles)
- **Penalize** (-80%) — Avoid staffing firms (prefer direct employers)

Changes are saved to your profile and apply to all future searches. The scoring rubric section below shows the default weights.

### 2. Update Your Profile

After initial setup, update your profile without re-running the wizard:

```bash
# View current profile settings
job-radar --view-profile

# Interactive editor — select field, change value, see diff, confirm
job-radar --edit-profile

# Quick CLI updates (no interactive prompts)
job-radar --update-skills "python,react,typescript"
job-radar --set-min-score 3.5
job-radar --set-titles "Backend Developer,SRE"
```

All updates create automatic backups and use atomic writes to prevent corruption. The interactive editor shows a before/after diff and requires confirmation before saving.

### 3. Run the Search

```bash
job-radar
```

On startup, Job Radar shows your profile preview (unless `--no-wizard` is set), then searches all sources.

**Options:**
- `--from YYYY-MM-DD` — Start date filter (default: 48 hours ago)
- `--to YYYY-MM-DD` — End date filter (default: today)
- `--output DIR` — Report output directory (default: `results/`)
- `--min-score N` — Minimum score threshold (default: 2.8)
- `--new-only` — Only show new (unseen) results
- `--no-open` — Don't auto-open report in browser
- `--dry-run` — Show what queries would run without fetching
- `--verbose` / `-v` — Enable debug logging
- `--no-cache` — Disable HTTP response caching (force fresh fetches)
- `--no-wizard` — Skip wizard check and profile preview (quiet mode)
- `--no-color` — Disable terminal colors (also respects `NO_COLOR` env var)

### 4. Review the Report

The HTML report opens automatically in your browser with interactive features:

**Visual Hierarchy:**
- **Hero Jobs (4.0+)** — Top matches in an elevated section with "Top Match" badges
- **Color-coded tiers** — Green (4.0+), Cyan (3.5-3.9), Indigo (2.8-3.4) with colorblind-safe indicators
- **Responsive design** — Desktop (11 cols) → tablet (7 cols) → mobile (stacked cards)

**Interactive Features:**
- **Copy URL** buttons on each job listing
- **Copy All Recommended** button to batch-copy high-scoring URLs
- **Keyboard shortcuts** — `C` to copy focused URL, `A` to copy all recommended
- **Status tracking** — Mark jobs as Applied, Interviewing, Rejected, or Offer (persists across sessions)
- **Filtering** — Hide jobs by status with persistent filter state
- **CSV Export** — Download visible results as Excel-compatible spreadsheet
- **Print** — Cmd+P/Ctrl+P for clean offline output with preserved tier colors

**Score ratings:**
- **4.0+** (Strong Recommend) — Apply immediately
- **3.5-3.9** (Recommend) — Worth applying
- **2.8-3.4** (Worth Reviewing) — Read the full posting first

Results tagged as **NEW** or previously seen. Recommended roles include **talking points** generated from your profile highlights.

### 5. Check Manual URLs

The report includes pre-built search URLs for Wellfound, Indeed, LinkedIn, and Glassdoor. These sites block automation, so open them in your browser.

### 6. Optional: API Credentials

Job Radar works out-of-the-box with 6 free sources (Dice, HN Hiring, RemoteOK, We Work Remotely, Jobicy, + 4 manual URLs). For additional coverage, configure API keys:

**GUI Method (Recommended):**
1. Open the **Settings** tab in Job Radar GUI
2. Scroll to **API Configuration**
3. Enter API keys and click **Test** to validate
4. View real-time quota usage (e.g., "15/100 daily searches used")
5. Click **Save** to persist changes

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

API keys significantly expand job coverage but are entirely optional.

## Scoring Rubric

**Default weights** (customizable in GUI Settings → Scoring Configuration):

| Criteria | Weight | What it measures |
|---|---|---|
| Stack/skill match | 30% | Core + secondary skills found in job description (word-boundary matching) |
| Seniority alignment | 20% | Level and years of experience match |
| Job type alignment | 15% | Target titles, job type preferences |
| Salary alignment | 15% | Compensation vs. your floor |
| Response likelihood | 10% | Direct email, company size signals |
| Description quality | 10% | Structured data, confidence score |

**Adjustments applied after scoring:**
- **Staffing firm preference** — Boost (+30%), Neutral (0%), or Penalize (-80%) based on your preference in Settings
- **Comp floor penalty** — Jobs below your `comp_floor` lose 0.5-1.5 points based on gap size
- **Parse confidence** — Low-confidence parsed listings lose 0.3 points
- **Dealbreakers** — Hard disqualification (score 0, excluded from report)

**Note:** You can adjust these weights using sliders in the GUI Settings tab (v2.1.0+). The scoring engine uses your custom weights if configured.

## Automated Sources

| Source | Method | API Key Required | Strengths |
|---|---|---|---|
| Dice.com | HTML scraping | No | Staffing firms, structured data, salary info |
| HN Hiring (hnhiring.com) | HTML scraping | No | Direct apply, small teams, quality postings |
| RemoteOK | JSON API | No | Remote-focused, salary data |
| We Work Remotely | HTML scraping | No | Remote-focused, curated listings |
| Adzuna | REST API | Yes | Salary data, large volume, UK/US/EU coverage |
| Authentic Jobs | REST API | Yes | Design and creative roles |
| JSearch | REST API | Yes | Google Jobs aggregator (LinkedIn, Indeed, Glassdoor, company career pages) |
| USAJobs | REST API | Yes | Federal government job listings |
| SerpAPI | REST API | Yes | Alternative Google Jobs aggregator |
| Jobicy | REST API | No (rate limited) | Remote job listings (1/hour limit) |

**Source Attribution:** Each job listing shows its original source (e.g., "via LinkedIn" for JSearch results) for transparency.

**Quota Tracking:** The GUI Settings tab displays real-time API usage with color-coded warnings (orange at 80%, red at 100%).

## Cross-Run Tracking

The tool maintains a `results/tracker.json` file that persists across runs:

- **Deduplication** — Jobs seen in previous runs are marked as "seen" (not "NEW") in reports
- **Cross-source matching** — rapidfuzz fuzzy matching at 85% threshold prevents duplicates from different sources
- **Application status** — Track Applied/Interviewing/Rejected/Offer status in HTML reports (saved to localStorage and tracker.json)
- **Run history** — Tracks total results and new results per run for the last 90 days
- **Lifetime stats** — Shows total unique jobs seen and average new jobs per run in the report header

## Config File

Save persistent defaults in `~/.job-radar/config.json`:

```json
{
  "min_score": 3.0,
  "new_only": true,
  "output": "/path/to/reports"
}
```

Supported keys: `min_score`, `new_only`, `output`. CLI flags always override the config file. Use `--config PATH` to load a different file.

## Caching

HTTP responses are cached for 4 hours in `.cache/` to avoid hammering sources during development or repeated runs. Use `--no-cache` to force fresh fetches.

## Customization

### Adding Skill Variants

If your skills have abbreviations or alternate names (e.g., "P2P" for "Procure-to-Pay"), add them to the `_SKILL_VARIANTS` dict in `job_radar/scoring.py` to improve matching. Short skills (2 characters or less) and known ambiguous terms automatically use word-boundary matching to prevent false positives.

### Adding Staffing Firms

Add known staffing/consulting firm names to the list in `job_radar/staffing_firms.py`. Staffing firms get a response likelihood boost since they're incentivized to place candidates.

### Adding HN Hiring Technology Slugs

HN Hiring uses specific lowercase slugs for technology filters. If your skills aren't being searched on HN Hiring, add mappings to the `_HN_SKILL_SLUGS` dict in `job_radar/sources.py`.

## GUI Features (v2.0.0+)

The desktop GUI application provides a visual interface for all Job Radar features:

**Profile Tab:**
- Create or edit profiles with grouped form sections (Identity, Skills & Titles, Preferences, Filters)
- Upload PDF resume to auto-fill profile fields
- Tag chip widget for list fields (skills, titles) with Enter-to-add, X-to-remove
- Inline validation with error labels
- Dirty tracking with discard confirmation

**Search Tab:**
- One-click "Run Search" button with visual progress tracking
- Per-source progress display showing current source name and job count
- Date range picker, min score slider, new-only toggle
- "Open Report" button to view results in browser

**Settings Tab (v2.1.0+):**
- **API Configuration:** Enter API keys, test validation, view quota usage
- **Scoring Configuration:** Adjust scoring weights with sliders, set staffing firm preference, see live preview
- **Uninstall:** Remove all app data with optional backup creation

## Uninstalling (v2.1.0+)

**GUI Method (Recommended):**
1. Launch Job Radar GUI → Settings tab
2. Scroll to Uninstall section
3. Optional: Click "Create Backup" to save profile/config
4. Check "I understand this will delete all Job Radar data"
5. Click red "Uninstall" button
6. Review confirmation dialog showing paths to be deleted
7. Confirm to proceed

The GUI uninstaller handles platform-specific cleanup automatically (Windows: Add/Remove Programs, macOS: app bundle to Trash, rate limiters, config, cache).

**Manual Uninstall:** See README.md for platform-specific manual uninstall instructions.

## Tips

- Run searches daily during active job hunts — new postings appear constantly
- Use `--view-profile` to quickly check your settings before a search
- Use `--edit-profile` for interactive changes with diff preview and confirmation
- Use `--update-skills` and `--set-min-score` for quick scripted updates
- Use `--dry-run` to verify your profile generates sensible queries before a full run
- The `NEW` tag helps you focus on fresh listings you haven't seen before
- Staffing firm postings (flagged in response likelihood) have the highest callback rates
- Set `comp_floor` and `dealbreakers` to automatically filter noise
- Add 2-3 highlights to get auto-generated talking points for recommended roles
- Use status tracking in the HTML report to keep your application pipeline organized
- Export to CSV for external tracking in spreadsheets

## File Structure

```
Job-Radar/
├── job_radar/              # Python package
│   ├── __init__.py         # Package version
│   ├── __main__.py         # python -m job_radar entry point (GUI/CLI dual mode)
│   ├── search.py           # CLI entry point (job-radar command)
│   ├── sources.py          # Dice + HN Hiring + RemoteOK + WWR fetchers
│   ├── api_sources.py      # Adzuna + Authentic Jobs + JSearch + USAJobs + SerpAPI + Jobicy fetchers
│   ├── scoring.py          # Weighted scoring engine with configurable weights
│   ├── report.py           # HTML + Markdown report generator
│   ├── tracker.py          # Cross-run dedup, stats, application tracking
│   ├── cache.py            # HTTP caching and retry-with-backoff layer
│   ├── config.py           # Config file loading (~/.job-radar/config.json)
│   ├── wizard.py           # Interactive first-run setup wizard
│   ├── profile_manager.py  # Centralized profile I/O (atomic writes, backups, schema migration)
│   ├── profile_display.py  # Formatted profile preview (tabulate tables)
│   ├── profile_editor.py   # Interactive profile field editor
│   ├── paths.py            # Path resolution for data, backup, and config dirs
│   ├── pdf_parser.py       # PDF resume parser (pdfplumber)
│   ├── dedup.py            # Cross-source exact-match URL deduplication
│   ├── rate_limits.py      # SQLite-backed API rate limiting with shared backends
│   ├── api_config.py       # API key storage and validation
│   ├── uninstaller.py      # Platform-specific app data removal
│   ├── update_config.py    # Auto-update infrastructure
│   ├── deps.py             # OS detection utility
│   ├── staffing_firms.py   # Known staffing firm list for response scoring
│   └── gui/                # Desktop GUI modules (v2.0.0+)
│       ├── app.py          # Main GUI application window
│       ├── profile_form.py # Profile creation/editing form
│       ├── search_controls.py # Search tab controls and progress
│       ├── settings_tab.py # API config, scoring config, uninstall
│       ├── scoring_config_widget.py # Scoring weights and staffing preference UI
│       └── tag_chips.py    # Reusable tag chip widget for list fields
├── tests/                  # 566 automated tests (19 test files)
├── scripts/                # Build scripts for standalone executables
├── installers/             # Platform-native installers (v2.1.0+)
│   ├── macos/             # DMG installer build scripts
│   └── windows/           # NSIS installer build scripts
├── results/                # Generated reports (auto-created)
│   └── tracker.json        # Cross-run dedup and stats
├── .cache/                 # HTTP response cache (auto-created)
├── .rate_limits/           # SQLite rate limit databases (auto-created)
├── pyproject.toml          # Package metadata and dependencies
├── README.md               # Quick-start guide and command reference
├── CHANGELOG.md            # Version history and release notes
└── WORKFLOW.md             # Full documentation and workflow details
```
