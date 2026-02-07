# Job Search Optimization Toolkit — Workflow

**Version 0.02** | [Changelog](CHANGELOG.md)

A Python-based job search tool that fetches listings from multiple sources, scores them against a candidate profile, tracks results across runs, and generates a ranked Markdown report.

## Prerequisites

- Python 3.10+
- Dependencies are **auto-installed** on first run (requests, beautifulsoup4)
- The script detects your OS (macOS, Linux, Windows) and uses appropriate commands

## Quick Start

```bash
# Run from anywhere — the script resolves its own paths
python path/to/search.py --profile profiles/your_name.json
```

By default, the search covers jobs posted within the last 48 hours.

## Full Workflow

### 1. Create a Candidate Profile

Copy the template and fill in your details:
```bash
cp profiles/_template.json profiles/your_name.json
```

Edit the new file with your information. The field reference below explains what each field does and how it affects scoring.

**Required fields:**
- `name` — Full name
- `target_titles` — Ranked list of job titles to search (top 4 are used for Dice queries)
- `core_skills` — Top 5-7 keywords (these drive scoring)

**Recommended fields:**
- `level` — `junior`, `mid`, `senior`, or `principal`
- `years_experience` — Total years of professional experience
- `secondary_skills` — Next 5-10 skills (counted at half weight in scoring)
- `location` — Current city/state
- `arrangement` — List of acceptable options: `remote`, `hybrid`, `onsite`
- `target_market` — Preferred job market (e.g., `Remote`, `Atlanta, GA`)
- `domain_expertise` — Industries you've worked in
- `certifications` — Professional certifications

**Filtering fields:**
- `comp_floor` — Minimum annual compensation in dollars (e.g., `80000`). Jobs with listed salaries below this threshold receive a score penalty proportional to the gap.
- `dealbreakers` — List of disqualifying keywords (e.g., `["clearance required", "C++"]`). Jobs matching any dealbreaker are completely excluded from results.

**Optional fields:**
- `languages` — Spoken languages
- `highlights` — 2-3 standout accomplishments. These are matched against recommended jobs to generate cover letter talking points in the report.

**Tips for filling out your profile:**
- `core_skills` — List only your strongest 5-7 technologies. These carry full weight in scoring, so prioritize what you want to work with most.
- `secondary_skills` — Technologies you know but aren't your focus. These count at half weight.
- `target_titles` — Put your ideal title first. The top 4 are used as Dice search queries.
- `highlights` — Use quantified results (numbers, percentages). These get matched to job requirements to auto-generate cover letter talking points.
- `dealbreakers` — Be specific. `"C++"` will exclude any listing mentioning C++. Case-insensitive matching against title, description, and company name.
- `comp_floor` — Set to `null` to skip salary filtering. When set, jobs below this number get penalized but not excluded.

### 2. Run the Search

```bash
python search.py --profile profiles/<name>.json
```

**Options:**
- `--from YYYY-MM-DD` — Start date filter (default: 48 hours ago)
- `--to YYYY-MM-DD` — End date filter (default: today)
- `--output DIR` — Report output directory (default: `results/`)
- `--open` — Auto-open the report in your default application after generation
- `--dry-run` — Show what queries would be run without fetching anything
- `--verbose` / `-v` — Enable debug logging (shows HTTP requests, cache hits, etc.)
- `--no-cache` — Disable HTTP response caching (forces fresh fetches)
- `--new-only` — Only show new (unseen) results, filtering out previously seen jobs
- `--min-score N` — Set a custom minimum score threshold (default: 2.8)

### 3. Review the Report

Open the generated Markdown file in `results/`:
```
results/<name>_YYYY-MM-DD.md
```

The report only includes results ranked **Recommend** or **Worth Reviewing**:
- **Score 4.0+** (Strong Recommend) — Apply immediately
- **Score 3.5-3.9** (Recommend) — Worth applying
- **Score 2.8-3.4** (Worth Reviewing) — Read the full posting first

Results are tagged as **NEW** or previously seen to help you focus on fresh listings.

Recommended roles include **talking points** auto-generated from your profile highlights matched to the job's skill requirements.

### 4. Check Manual URLs

The report includes pre-built search URLs for Indeed, LinkedIn, Glassdoor, and We Work Remotely, grouped by source. These sites block automated access, so open them in your browser.

### 5. Deep Analysis (Optional)

For top-scoring roles, paste the full job description into Claude Code and ask:
```
Rate this job for [candidate name] based on their profile at profiles/<name>.json.
Give a detailed fit analysis and suggest talking points for the cover letter.
```

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
- **Parse confidence** — Low-confidence parsed listings (freeform HN posts) lose 0.3 points
- **Dealbreakers** — Hard disqualification (score 0, excluded from report)

## Automated Sources

| Source | Method | Strengths |
|---|---|---|
| Dice.com | HTML scraping | Staffing firms, structured data, salary info |
| HN Hiring (hnhiring.com) | HTML scraping | Direct apply, small teams, quality postings |
| RemoteOK | JSON API | Remote-focused, salary data, no scraping needed |
| We Work Remotely | HTML scraping | Remote-focused, curated listings |

## Cross-Run Tracking

The tool maintains a `results/tracker.json` file that persists across runs:

- **Deduplication** — Jobs seen in previous runs are marked as "seen" (not "NEW") in reports
- **Run history** — Tracks total results and new results per run for the last 90 days
- **Lifetime stats** — Shows total unique jobs seen and average new jobs per run in the report header

## Caching

HTTP responses are cached for 4 hours in `.cache/` to avoid hammering sources during development or repeated runs. Use `--no-cache` to force fresh fetches.

## Customization

### Adding Skill Variants

If your skills have abbreviations or alternate names (e.g., "P2P" for "Procure-to-Pay"), add them to the `_SKILL_VARIANTS` dict in `scoring.py` to improve matching. Short skills (2 characters or less) and known ambiguous terms automatically use word-boundary matching to prevent false positives.

### Adding Staffing Firms

Add known staffing/consulting firm names to the list in `staffing_firms.py`. Staffing firms get a response likelihood boost since they're incentivized to place candidates.

### Adding HN Hiring Technology Slugs

HN Hiring uses specific lowercase slugs for technology filters. If your skills aren't being searched on HN Hiring, add mappings to the `_HN_SKILL_SLUGS` dict in `sources.py`.

## Tips

- Run searches daily during active job hunts — new postings appear constantly
- Use `--dry-run` to verify your profile generates sensible queries before a full run
- Use `--open` to immediately review results after a search
- The `NEW` tag helps you focus on fresh listings you haven't seen before
- Staffing firm postings (flagged in response likelihood) have the highest callback rates
- Keep profiles updated as search focus shifts
- Set `comp_floor` and `dealbreakers` to automatically filter noise
- Add 2-3 highlights to get auto-generated talking points for recommended roles

## File Structure

```
job-search/
├── profiles/           # Candidate profile JSON files
│   └── _template.json  # Copy this to create your profile
├── results/            # Generated Markdown reports (auto-created)
│   └── tracker.json    # Cross-run dedup and stats
├── .cache/             # HTTP response cache (auto-created, gitignore-able)
├── search.py           # CLI entry point
├── deps.py             # OS-aware dependency checker and auto-installer
├── sources.py          # Dice + HN Hiring + RemoteOK + WWR fetchers
├── scoring.py          # Weighted scoring engine with word-boundary matching
├── report.py           # Markdown report generator with talking points
├── tracker.py          # Cross-run dedup, stats, application tracking
├── cache.py            # HTTP caching and retry-with-backoff layer
├── staffing_firms.py   # Known staffing firm list for response scoring
├── README.md           # Quick-start guide and command reference
├── CHANGELOG.md        # Version history and release notes
└── WORKFLOW.md         # Full documentation and workflow details
```
