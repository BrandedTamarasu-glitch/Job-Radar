# Job Radar — Workflow

**Version 1.5.0** | [Changelog](CHANGELOG.md)

A Python-based job search tool that fetches listings from multiple sources, scores them against a candidate profile, tracks results across runs, and generates ranked HTML + Markdown reports with interactive features and WCAG 2.1 AA accessibility.

## Prerequisites

- Python 3.10+
- Install with `pip install -e .` (see [README](README.md#install))

Or download a standalone executable from the [Releases page](https://github.com/BrandedTamarasu-glitch/Job-Radar/releases/latest) (no Python required).

## Quick Start

```bash
# First launch — interactive wizard guides profile creation
job-radar

# Subsequent launches — shows profile preview, then searches
job-radar
```

By default, the search covers jobs posted within the last 48 hours.

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

For additional job sources (Adzuna and Authentic Jobs), set up API keys:

```bash
job-radar --setup-apis
```

API keys are optional — the tool works without them using the 4 scraper-based sources.

## Scoring Rubric

| Criteria | Weight | What it measures |
|---|---|---|
| Stack/skill match | 25% | Core + secondary skills found in job description (word-boundary matching) |
| Title relevance | 15% | How well the job title matches your target titles |
| Seniority alignment | 15% | Level and years of experience match |
| Location/arrangement | 15% | Remote/hybrid/onsite + geography fit |
| Domain relevance | 10% | Industry keyword overlap |
| Response likelihood | 20% | Staffing firm, direct email, company size signals |

**Adjustments applied after scoring:**
- **Comp floor penalty** — Jobs below your `comp_floor` lose 0.5-1.5 points based on gap size
- **Parse confidence** — Low-confidence parsed listings lose 0.3 points
- **Dealbreakers** — Hard disqualification (score 0, excluded from report)

## Automated Sources

| Source | Method | Strengths |
|---|---|---|
| Dice.com | HTML scraping | Staffing firms, structured data, salary info |
| HN Hiring (hnhiring.com) | HTML scraping | Direct apply, small teams, quality postings |
| RemoteOK | JSON API | Remote-focused, salary data, no scraping needed |
| We Work Remotely | HTML scraping | Remote-focused, curated listings |
| Adzuna | REST API (key required) | Salary data, large volume, UK/US/EU coverage |
| Authentic Jobs | REST API (key required) | Design and creative roles |

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
│   ├── __main__.py         # python -m job_radar entry point
│   ├── search.py           # CLI entry point (job-radar command)
│   ├── sources.py          # Dice + HN Hiring + RemoteOK + WWR fetchers
│   ├── api_sources.py      # Adzuna + Authentic Jobs API fetchers
│   ├── scoring.py          # Weighted scoring engine with word-boundary matching
│   ├── report.py           # HTML + Markdown report generator
│   ├── tracker.py          # Cross-run dedup, stats, application tracking
│   ├── cache.py            # HTTP caching and retry-with-backoff layer
│   ├── config.py           # Config file loading (~/.job-radar/config.json)
│   ├── wizard.py           # Interactive first-run setup wizard
│   ├── profile_manager.py  # Centralized profile I/O (atomic writes, backups, validation)
│   ├── profile_display.py  # Formatted profile preview (tabulate tables)
│   ├── profile_editor.py   # Interactive profile field editor
│   ├── paths.py            # Path resolution for data, backup, and config dirs
│   ├── pdf_parser.py       # PDF resume parser (pdfplumber)
│   ├── dedup.py            # Cross-source fuzzy deduplication (rapidfuzz)
│   ├── rate_limiter.py     # SQLite-backed API rate limiting
│   ├── deps.py             # OS detection utility
│   └── staffing_firms.py   # Known staffing firm list for response scoring
├── tests/                  # 452 automated tests
├── scripts/                # Build scripts for standalone executables
├── results/                # Generated reports (auto-created)
│   └── tracker.json        # Cross-run dedup and stats
├── .cache/                 # HTTP response cache (auto-created)
├── pyproject.toml          # Package metadata and dependencies
├── README.md               # Quick-start guide and command reference
├── CHANGELOG.md            # Version history and release notes
└── WORKFLOW.md             # Full documentation and workflow details
```
