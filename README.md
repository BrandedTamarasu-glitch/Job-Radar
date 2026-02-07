# Job Radar

A Python CLI that searches multiple job boards, scores listings against your candidate profile, and generates a ranked Markdown report.

## Install

```bash
pip install job-radar
```

Or install from source:

```bash
git clone https://github.com/BrandedTamarasu-glitch/Job-Radar.git
cd Job-Radar
pip install -e .
```

You can also run it without installing via `python -m job_radar`.

## Setup

**Requirements:** Python 3.10+ (macOS, Linux, or Windows).

### Step 1: Create your profile

```bash
cp profiles/_template.json profiles/your_name.json
```

Open the file and fill in your details. At minimum you need:
- `name` — your full name
- `target_titles` — job titles you're searching for (top 4 become Dice queries)
- `core_skills` — your top 5-7 technologies

See [WORKFLOW.md](WORKFLOW.md#1-create-a-candidate-profile) for a full field reference and tips.

### Step 2: Preview your queries

```bash
job-radar --profile profiles/your_name.json --dry-run
```

This shows what search queries will run without fetching anything. Use it to verify your profile produces sensible searches.

### Step 3: Run the search

```bash
job-radar --profile profiles/your_name.json
```

The tool will:
1. Fetch listings from Dice, HN Hiring, RemoteOK, and We Work Remotely
2. Filter by date (default: last 48 hours)
3. Score each listing against your profile
4. Track new vs. previously seen jobs
5. Generate a ranked Markdown report in `results/`

### Step 4: Review results

Open the report at `results/your_name_YYYY-MM-DD.md`. The report includes:
- Ranked job listings scored 1.0-5.0
- Skill match breakdowns per listing
- Auto-generated cover letter talking points for top matches
- Pre-built search URLs for Indeed, LinkedIn, and Glassdoor (open manually in browser)

## Command Reference

| Flag | Description |
|---|---|
| `--profile PATH` | **(Required)** Path to your candidate profile JSON |
| `--dry-run` | Show queries without fetching. Use to validate your profile |
| `--open` | Auto-open the report in your default app after generation |
| `--from YYYY-MM-DD` | Start date filter (default: 48 hours ago) |
| `--to YYYY-MM-DD` | End date filter (default: today) |
| `--new-only` | Hide previously seen jobs, only show new listings |
| `--min-score N` | Minimum score to include in the report (default: 2.8) |
| `--no-cache` | Force fresh fetches, ignoring the 4-hour HTTP cache |
| `--verbose` / `-v` | Show debug output (HTTP requests, cache hits, scoring details) |
| `--output DIR` | Change the report output directory (default: `results/`) |

### Examples

```bash
# Basic daily search
job-radar --profile profiles/your_name.json

# Search a specific date range and auto-open the report
job-radar --profile profiles/your_name.json --from 2026-02-01 --to 2026-02-06 --open

# Only show new listings, skip anything seen before
job-radar --profile profiles/your_name.json --new-only

# Only show strong matches (3.5+)
job-radar --profile profiles/your_name.json --min-score 3.5

# Fresh fetch with debug logging
job-radar --profile profiles/your_name.json --no-cache -v

# Preview queries without running them
job-radar --profile profiles/your_name.json --dry-run
```

## Score Ratings

| Score | Rating | Action |
|---|---|---|
| 4.0+ | Strong Recommend | Apply immediately |
| 3.5-3.9 | Recommend | Worth applying |
| 2.8-3.4 | Worth Reviewing | Read the full posting first |
| < 2.8 | Excluded from report | |

## Further Reading

- [WORKFLOW.md](WORKFLOW.md) — Full documentation: profile field reference, scoring rubric breakdown, source details, customization options, and daily workflow tips
- [CHANGELOG.md](CHANGELOG.md) — Version history
