# Job Radar

## What This Is

A Python-based job search tool that searches multiple job boards (Dice, HN Hiring, RemoteOK, We Work Remotely, Adzuna, Authentic Jobs), scores listings against a candidate profile, tracks new vs. seen jobs across runs, and generates ranked HTML + Markdown reports. Available as both a desktop GUI application and a CLI for power users. Reports include one-click URL copying, application status tracking, and WCAG 2.1 Level AA accessibility compliance. Built for daily use during an active job search.

## Core Value

Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

## Requirements

### Validated

- ✓ Multi-source job fetching (Dice, HN Hiring, RemoteOK, WWR) — v1.0
- ✓ Profile-driven scoring with 6-component weighted system — v1.0
- ✓ Cross-run job tracking and deduplication — v1.0
- ✓ Ranked Markdown report generation with skill breakdowns — v1.0
- ✓ HTTP response caching with 4-hour TTL — v1.0
- ✓ CLI with date filtering, score thresholds, dry-run mode — v1.0
- ✓ Manual search URL generation for Indeed/LinkedIn/Glassdoor — v1.0
- ✓ Cover letter talking points for top matches — v1.0
- ✓ Staffing firm detection in scoring — v1.0
- ✓ Test suite with pytest covering scoring, caching, and tracking — v1.0
- ✓ Fuzzy skill matching — normalize punctuation/casing so "NodeJS" matches "node.js" — v1.0
- ✓ Config file support — save default CLI options — v1.0
- ✓ Standalone executables (Windows, macOS, Linux) with PyInstaller onedir mode — v1.1
- ✓ Interactive first-run wizard with Questionary prompts — v1.1
- ✓ Wizard-to-search integration with first-run detection and profile recovery — v1.1
- ✓ Dual-format reports (Bootstrap 5 HTML + Markdown) with browser auto-launch — v1.1
- ✓ Non-technical UX (progress indicators, friendly errors, graceful Ctrl+C) — v1.1
- ✓ Automated CI/CD via GitHub Actions with tag-triggered multi-platform builds — v1.1
- ✓ Adzuna API integration with salary data extraction — v1.2.0
- ✓ Authentic Jobs API integration for design/creative roles — v1.2.0
- ✓ Wellfound manual search URL generation — v1.2.0
- ✓ Secure API credential management with python-dotenv and .env file — v1.2.0
- ✓ SQLite-backed rate limiting with cross-restart persistence — v1.2.0
- ✓ Cross-source fuzzy deduplication with rapidfuzz (85% threshold) — v1.2.0
- ✓ PDF resume parser extracts name, years, titles, skills — v1.2.0
- ✓ Interactive wizard PDF upload option pre-fills profile fields — v1.2.0
- ✓ PDF validation rejects image-only, encrypted, oversized PDFs — v1.2.0
- ✓ PyInstaller-ready with pdfplumber dependencies configured — v1.2.0
- ✓ One-click copy buttons and batch "Copy All Recommended" action — v1.3.0
- ✓ Keyboard shortcuts (C/A) for clipboard operations — v1.3.0
- ✓ Application status tracking (Applied/Interviewing/Rejected/Offer) with localStorage — v1.3.0
- ✓ Embedded tracker.json hydration with bidirectional sync — v1.3.0
- ✓ Skip navigation link for keyboard users — v1.3.0
- ✓ ARIA landmarks (banner, main, contentinfo) for screen readers — v1.3.0
- ✓ Accessible table with scope attributes and caption — v1.3.0
- ✓ Screen reader badge context ("Score 4.2 out of 5.0", "New listing") — v1.3.0
- ✓ Focus indicators on all interactive elements — v1.3.0
- ✓ WCAG AA contrast compliance (4.5:1 minimum) — v1.3.0
- ✓ CLI screen reader documentation and --profile bypass — v1.3.0
- ✓ NO_COLOR standard support and --no-color CLI flag — v1.3.0
- ✓ Lighthouse accessibility score ≥95 — v1.3.0
- ✓ Hero job visual hierarchy (≥4.0) with multi-layer shadows and prominent badges — v1.4.0
- ✓ Semantic color system (green/cyan/indigo tiers) with system font stacks — v1.4.0
- ✓ Responsive design: desktop (11 cols) → tablet (7 cols) → mobile (stacked cards) — v1.4.0
- ✓ Mobile ARIA role restoration for screen reader table semantics — v1.4.0
- ✓ Status filtering with localStorage persistence — v1.4.0
- ✓ CSV export with UTF-8 BOM, RFC 4180 escaping, formula injection protection — v1.4.0
- ✓ Print stylesheet with color preservation and page break control — v1.4.0
- ✓ Automated accessibility CI (Lighthouse + axe-core) blocking merge on failures — v1.4.0
- ✓ Centralized profile I/O with atomic writes, backups, validation, and schema versioning — v1.5.0
- ✓ Profile preview on startup and via --view-profile command — v1.5.0
- ✓ Interactive quick-edit with categorized field menu, diff preview, and confirmation — v1.5.0
- ✓ CLI update flags (--update-skills, --set-min-score, --set-titles) with validation — v1.5.0

### Active

## Current Milestone: v2.0.0 Desktop GUI Launcher

**Goal:** Replace the terminal-first experience with a desktop GUI window so non-technical users never need to touch a command prompt.

**Target features:**
- Desktop window application with search controls (Run Search button, date range, min score, etc.)
- GUI-based profile setup (form fields, PDF upload button) replacing terminal wizard for new users
- Visual progress feedback during search
- Opens existing HTML report in browser when search completes
- CLI preserved alongside GUI for power users and scripting

### Out of Scope

- LinkedIn/Indeed direct scraping — both sites aggressively block automation; unreliable long-term
- Job data aggregator API (SerpAPI, JSearch) — deferred; revisit after core improvements ship
- Web UI or email digest — desktop app + report is the workflow; no server needed
- Application tracking CLI commands — tracker.py has the functions but exposing them is deferred
- Mobile app — desktop tool
- Cloud-based application tracking — Job Radar is privacy-focused and offline-first
- AI-powered job matching — core value is transparent scoring algorithm
- Real-time notifications — batch daily search workflow is intentional design
- Multiple profiles support — context switching pattern unclear for job search use case
- Profile export/import — no collaboration use case identified yet
- Undo last change — complex; wait for actual user mistakes in the wild

## Context

### Current State (v2.0.0 in progress)

- v1.5.0 shipped with 16,449 LOC Python (source + tests)
- Tech stack: Python 3.10+, pytest, requests, BeautifulSoup, questionary, PyInstaller, pdfplumber, rapidfuzz, python-dotenv, pyrate-limiter, tabulate
- Test suite: 452 tests across scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management
- Job sources: 6 API sources + 4 manual URLs (Wellfound, Indeed, LinkedIn, Glassdoor)
- Standalone executables for Windows, macOS, and Linux (currently terminal-based)
- HTML reports: Bootstrap 5 with visual hierarchy, responsive layout, status filtering, CSV export, print, WCAG 2.1 AA
- Profile management: centralized I/O (atomic writes, backups, schema versioning), preview, interactive editor, CLI flags
- Current workflow: download executable → terminal wizard → daily searches → HTML reports in browser
- Target workflow: download executable → GUI setup → click Run Search → HTML reports in browser
- Automated accessibility CI: Lighthouse (≥95%) and axe-core WCAG validation on every PR

### Development

- Tool is run daily during active job search
- User reads HTML reports in browser, uses copy buttons and keyboard shortcuts
- Scoring weights are hardcoded (validated by test suite)
- Broad `except Exception` patterns throughout scrapers for crash tolerance (intentional)
- Questionary library screen reader support is unknown; --profile flag bypasses wizard

## Constraints

- **Tech stack**: Python 3.10+, pip, no additional runtime dependencies beyond requests/bs4
- **No API keys required**: Current sources are all public; keep it zero-config for basic usage
- **Cross-platform**: Must work on macOS, Linux, and Windows
- **Backward compatible**: Existing profiles and CLI flags must continue to work
- **Single-file HTML**: Reports must be self-contained (all CSS/JS inline) for file:// portability

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Skip LinkedIn/Indeed scraping | Both sites actively block automation | ✓ Good |
| Defer job aggregator API | Focus on core quality first | ✓ Good |
| pytest for test framework | Standard Python testing, good fixtures | ✓ Good |
| Config file over env vars | Profile-based tool; config file fits better | ✓ Good |
| Normalize skills at lookup time | Zero runtime overhead, clean separation | ✓ Good |
| Two-pass CLI parsing | Extract --config before full argparse | ✓ Good |
| Test private functions directly | Granular test failures, clear debugging | ✓ Good |
| Two-tier clipboard (Clipboard API + execCommand) | Clipboard API fails on file://; execCommand is universal fallback | ✓ Good |
| Inline JS in HTML reports | Single-file portability; no external dependencies | ✓ Good |
| Embedded tracker.json as script tag | Server-to-client state hydration without API | ✓ Good |
| localStorage as session cache | Enables browser-side persistence for file:// protocol | ✓ Good |
| Export-based sync (Blob download) | Broader browser support than File System Access API | ✓ Good |
| Bootstrap visually-hidden-focusable for skip link | Battle-tested implementation, handles focus/blur correctly | ✓ Good |
| Explicit ARIA roles alongside HTML5 elements | Older screen readers need explicit role attributes | ✓ Good |
| Override text-muted to #595959 | Bootstrap default (#6c757d) fails WCAG AA at 4.28:1 | ✓ Good |
| Nested visually-hidden spans for badge context | Screen readers get full context without visual clutter | ✓ Good |
| ARIA live region with 1s timeout | Prevents screen reader announcement queue buildup | ✓ Good |
| NO_COLOR as first check in _colors_supported() | no-color.org standard: env var takes precedence over all | ✓ Good |
| --profile flag as screen reader bypass | Questionary has unknown screen reader support; bypass is safe | ✓ Good |
| Atomic temp-file-plus-rename for profile writes | Prevents corruption on interrupted writes | ✓ Good |
| Centralized profile_manager.py for all I/O | Single source of truth; wizard, editor, CLI flags all share | ✓ Good |
| Schema versioning with auto-migration | Forward-compatible; v0 profiles auto-upgrade to v1 | ✓ Good |
| Reuse wizard validators in profile editor | Zero duplication; single validation source of truth | ✓ Good |
| argparse type validators for CLI flags | Parse-time validation with friendly error messages | ✓ Good |
| Mutually exclusive update flag group | Prevents ambiguous multi-update commands | ✓ Good |

---
*Last updated: 2026-02-12 after v2.0.0 milestone start*
