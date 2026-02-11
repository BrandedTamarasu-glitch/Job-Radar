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
- ✓ Test suite with pytest covering scoring, caching, and tracking — v1.0
- ✓ Fuzzy skill matching — normalize punctuation/casing so "NodeJS" matches "node.js", "Python" matches "python3" — v1.0
- ✓ Config file support — save default CLI options (min-score, new-only, output dir) so they don't need to be retyped every run — v1.0
- ✓ Standalone executables (Windows .exe, macOS .app, Linux binary) with PyInstaller onedir mode and <10s startup — v1.1
- ✓ Interactive first-run wizard with Questionary prompts, examples, and validation — v1.1
- ✓ Wizard-to-search integration with first-run detection and profile recovery — v1.1
- ✓ Dual-format reports (Bootstrap 5 HTML + Markdown) with browser auto-launch — v1.1
- ✓ Non-technical UX (progress indicators, friendly errors, graceful Ctrl+C) — v1.1
- ✓ Automated CI/CD via GitHub Actions with tag-triggered multi-platform builds — v1.1
- ✓ Adzuna API integration with app_id/app_key authentication and salary data extraction — v1.2.0
- ✓ Authentic Jobs API integration with key-based authentication for design/creative roles — v1.2.0
- ✓ Wellfound manual search URL generation with /role/r/ (remote) and /role/l/ (location) patterns — v1.2.0
- ✓ Secure API credential management with python-dotenv and .env file (gitignored) — v1.2.0
- ✓ SQLite-backed rate limiting with cross-restart persistence prevents API bans — v1.2.0
- ✓ Cross-source fuzzy deduplication with rapidfuzz (85% similarity threshold) — v1.2.0
- ✓ PDF resume parser extracts name, years, titles, skills with UTF-8 support — v1.2.0
- ✓ Interactive wizard PDF upload option pre-fills profile fields (editable) — v1.2.0
- ✓ PDF validation rejects image-only, encrypted, oversized, corrupted PDFs with actionable errors — v1.2.0
- ✓ PyInstaller-ready with pdfplumber dependencies configured — v1.2.0

### Active

## Current Milestone: v1.3.0 Critical Friction & Accessibility

**Goal:** Eliminate application flow friction and achieve WCAG 2.1 Level AA compliance for HTML reports

**Target features:**
- Copy URL buttons and batch actions to eliminate manual copy-paste overhead
- WCAG 2.1 Level AA compliance (skip navigation, ARIA landmarks, accessible table markup, screen reader testing)
- Application status tracking with localStorage
- Keyboard shortcuts in HTML reports
- Accessible badge markup and color contrast fixes

**Research findings:** Exploratory research identified three critical improvement areas: application friction (5-10 min wasted per session on manual copy-paste), accessibility compliance (multiple WCAG violations block users with disabilities), and visual hierarchy gaps (deferred to v1.4)

### Out of Scope

- LinkedIn/Indeed direct scraping — both sites aggressively block automation; unreliable long-term
- Job data aggregator API (SerpAPI, JSearch) — deferred; revisit after core improvements ship
- Web UI or email digest — CLI + Markdown report is the current workflow and works
- Application tracking CLI commands — tracker.py has the functions but exposing them is deferred
- Mobile app — desktop CLI tool

## Context

### Current State (v1.2.0 shipped)

- Shipped v1.2.0 with 10,238 LOC Python (source + tests)
- Tech stack: Python 3.10+, pytest, requests, BeautifulSoup, questionary, PyInstaller, pdfplumber, rapidfuzz, python-dotenv, pyrate-limiter
- Test suite: 284 tests passing (scoring, config, tracker, wizard, report, browser, UX, API, PDF parser, deduplication)
- Job sources: 6 sources (Dice, HN Hiring, RemoteOK, WWR, Adzuna API, Authentic Jobs API) + 3 manual URLs (Wellfound, Indeed, LinkedIn)
- Standalone executables for Windows, macOS, and Linux with 0.18s startup time
- Interactive first-run wizard with optional PDF resume upload for auto-extraction
- Dual-format reports: Bootstrap 5 HTML (auto-opens in browser) + Markdown
- Automated distribution: GitHub Actions builds all platforms on tag push
- User workflow: download executable → wizard setup (optional PDF import) → daily searches → HTML reports in browser

### Development

- Tool is run daily during active job search
- User reads reports in a Markdown viewer, manually copies links to find/apply to jobs
- Scoring weights are hardcoded (validated by test suite)
- Broad `except Exception` patterns throughout scrapers for crash tolerance (intentional for reliability)

## Constraints

- **Tech stack**: Python 3.10+, pip, no additional runtime dependencies beyond requests/bs4
- **No API keys required**: Current sources are all public; keep it zero-config for basic usage
- **Cross-platform**: Must work on macOS, Linux, and Windows
- **Backward compatible**: Existing profiles and CLI flags must continue to work

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Skip LinkedIn/Indeed scraping | Both sites actively block automation; fragile and risky | ✓ Good |
| Defer job aggregator API | Focus on core quality improvements first; aggregator adds API key dependency | ✓ Good (v1.0 focused on reliability) |
| pytest for test framework | Standard Python testing, good fixtures/parametrize support | ✓ Good (78 tests, parametrize pattern works well) |
| Config file over environment vars | Profile-based tool; config file fits the pattern better than env vars | ✓ Good (two-pass parsing enables clean defaults) |
| Normalize skills at lookup time | Keep _build_skill_pattern() unchanged, normalize only lookup key | ✓ Good (zero runtime overhead, clean separation) |
| Two-pass CLI parsing | Extract --config before full argparse, enables set_defaults | ✓ Good (CLI flags override config cleanly) |
| Test private functions directly | Test _score_* functions rather than only public API | ✓ Good (granular test failures, clear debugging) |

---
*Last updated: 2026-02-11 after v1.3.0 milestone started*
