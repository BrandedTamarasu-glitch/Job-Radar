# Job Radar

## What This Is

A Python CLI that searches multiple job boards (Dice, HN Hiring, RemoteOK, We Work Remotely), scores listings against a candidate profile, tracks new vs. seen jobs across runs, and generates a ranked Markdown report. Built for daily use during an active job search.

## Core Value

Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

## Requirements

### Validated

- ✓ Multi-source job fetching (Dice, HN Hiring, RemoteOK, WWR) — existing
- ✓ Profile-driven scoring with 6-component weighted system — existing
- ✓ Cross-run job tracking and deduplication — existing
- ✓ Ranked Markdown report generation with skill breakdowns — existing
- ✓ HTTP response caching with 4-hour TTL — existing
- ✓ CLI with date filtering, score thresholds, dry-run mode — existing
- ✓ Manual search URL generation for Indeed/LinkedIn/Glassdoor — existing
- ✓ Cover letter talking points for top matches — existing
- ✓ Staffing firm detection in scoring — existing

### Active

- [ ] Test suite with pytest covering scoring, caching, and tracking
- [ ] Fuzzy skill matching — normalize punctuation/casing so "NodeJS" matches "node.js", "Python" matches "python3"
- [ ] Config file support — save default CLI options (min-score, new-only, output dir) so they don't need to be retyped every run

### Out of Scope

- LinkedIn/Indeed direct scraping — both sites aggressively block automation; unreliable long-term
- Job data aggregator API (SerpAPI, JSearch) — deferred; revisit after core improvements ship
- Web UI or email digest — CLI + Markdown report is the current workflow and works
- Application tracking CLI commands — tracker.py has the functions but exposing them is deferred
- Mobile app — desktop CLI tool

## Context

- User reads reports in a Markdown viewer, manually copies links to find/apply to jobs
- Tool is run daily during active job search
- Python 3.10+ codebase with requests + BeautifulSoup for fetching/parsing
- No test suite exists — zero coverage across all modules
- Scoring weights are hardcoded; skill variant matching is incomplete
- Broad `except Exception` patterns throughout scrapers for crash tolerance
- `_SKILL_VARIANTS` dict in scoring.py has gaps (e.g., "NodeJS" vs "node.js" doesn't match)

## Constraints

- **Tech stack**: Python 3.10+, pip, no additional runtime dependencies beyond requests/bs4
- **No API keys required**: Current sources are all public; keep it zero-config for basic usage
- **Cross-platform**: Must work on macOS, Linux, and Windows
- **Backward compatible**: Existing profiles and CLI flags must continue to work

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Skip LinkedIn/Indeed scraping | Both sites actively block automation; fragile and risky | ✓ Good |
| Defer job aggregator API | Focus on core quality improvements first; aggregator adds API key dependency | — Pending |
| pytest for test framework | Standard Python testing, good fixtures/parametrize support | — Pending |
| Config file over environment vars | Profile-based tool; config file fits the pattern better than env vars | — Pending |

---
*Last updated: 2026-02-07 after initialization*
