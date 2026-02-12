# Project Milestones: Job Radar

## v1.4.0 Visual Design & Polish (Shipped: 2026-02-11)

**Delivered:** Improve report scannability through visual hierarchy, responsive design, and quality-of-life polish features

**Phases completed:** 19-23 (9 plans total)

**Key accomplishments:**

- Visual hierarchy with semantic color system (green/cyan/indigo for score tiers) and system font stacks (zero-overhead, instant rendering)
- Hero job visual distinction for top matches (≥4.0) with multi-layer shadows, prominent "Top Match" badges, and elevated styling
- Responsive design: desktop (11 columns) → tablet (7 core columns) → mobile (stacked cards with all data)
- Mobile ARIA role restoration preserves table semantics for screen readers when using display:block transformations
- Interactive status filtering (hide Applied/Rejected/Interviewing/Offer) with localStorage persistence
- CSV export with UTF-8 BOM for Excel compatibility, RFC 4180 escaping, and formula injection protection
- Print-optimized stylesheet preserves tier colors (print-color-adjust: exact), hides interactive chrome, prevents page breaks
- Automated accessibility CI with Lighthouse (5 runs, ≥95% median score) and axe-core WCAG validation blocking merge on failures

**Stats:**

- 20 feature commits across 5 phases
- ~1,200 lines of CSS/JS added to inline HTML report
- 5 phases, 9 plans, ~18 tasks
- 1 day (2026-02-11)

**Git range:** `feat(19-01)` → `fix(csv-export)`

**Requirements:** 9/9 satisfied (5 VIS + 4 POL requirements)

**Quality metrics:**
- Phase verification: 5/5 passed
- Cross-phase integration: 23/23 connections verified
- E2E flows: 3/3 complete (visual hierarchy, interactive features, accessibility)
- Known issues: 0 (CSV NEW badge bug fixed before archival)

**What's next:** New milestone planning or production deployment

---

## v1.2.0 Enhanced Sources & Onboarding (Shipped: 2026-02-10)

**Delivered:** Expand job source coverage and reduce onboarding friction through PDF resume import

**Phases completed:** 12-15 (9 plans total)

**Key accomplishments:**

- Adzuna and Authentic Jobs API integration with secure credential management (.env), SQLite-backed rate limiting, and salary data extraction
- Cross-source fuzzy deduplication with rapidfuzz (85% similarity threshold) prevents duplicate listings across 6 sources
- Wellfound manual URL generation positioned as first source with /role/r/ (remote) and /role/l/ (location) patterns
- PDF resume parser extracts name, years, titles, skills from uploaded PDFs with UTF-8 support and graceful partial extraction
- Interactive wizard PDF upload option pre-fills profile fields with heuristic parsing and actionable error messages
- PyInstaller-ready with pdfplumber dependencies configured for standalone executable compatibility

**Stats:**

- 18 feature commits across 4 phases
- ~3,200 lines of Python added (modules + tests)
- 4 phases, 9 plans, ~14 tasks
- 5 days from first commit to ship (2026-02-06 → 2026-02-10)

**Git range:** `feat(12-01)` → `test(15-02)`

**Requirements:** 17/17 satisfied (7 API + 10 PDF requirements)

**What's next:** Continue expanding job sources and improving onboarding experience

---

## v1.1 Standalone Executable (Shipped: 2026-02-09)

**Delivered:** Make Job Radar accessible to non-technical users through standalone executables with interactive setup

**Phases completed:** 6-11 (15 plans total)

**Key accomplishments:**

- Standalone executables for all platforms (Windows .exe, macOS .app, Linux binary) with PyInstaller onedir mode achieving 0.18s startup (well under 10s threshold)
- Interactive first-run wizard with Questionary library providing examples, inline validation, and atomic profile/config generation
- Wizard-to-search integration with first-run detection, profile recovery, and seamless pipeline flow
- Dual-format reports (Bootstrap 5 HTML + Markdown) with headless detection and cross-platform browser auto-launch
- Non-technical UX polish including plain-text banner, source-level progress callbacks, friendly error messages, and graceful Ctrl+C handling
- Automated CI/CD distribution via tag-triggered GitHub Actions workflow building all platforms with pytest gates and auto-generated release notes

**Stats:**

- 21 files created/modified
- 4,093 lines of Python
- 6 phases, 15 plans, ~25 tasks
- 3 days from first commit to ship (2026-02-06 → 2026-02-09)

**Git range:** `feat(06-01)` → `docs(11-02)`

**What's next:** TBD - next milestone planning

---

## v1.0 Foundation (Shipped: 2026-02-09)

**Delivered:** Fuzzy skill normalization, persistent config file support, and comprehensive pytest test suite

**Phases completed:** 1-5 (7 plans total)

**Key accomplishments:**

- Fuzzy skill matching handles punctuation and casing variants (NodeJS ↔ node.js, k8s ↔ kubernetes)
- Config file support at ~/.job-radar/config.json eliminates repetitive CLI flag typing
- Test suite with 78 parametrized tests covers all scoring functions, config edge cases, and tracker isolation
- Expanded _SKILL_VARIANTS with 16+ common tech variants (postgres/postgresql, .NET/dotnet, etc.)
- Zero regressions: all existing functionality preserved while adding new features
- Comprehensive edge case coverage: invalid JSON, missing files, dealbreakers, salary parsing

**Stats:**

- 7 files created/modified (config.py, test_config.py, test_scoring.py updates, test_tracker.py)
- 3,300 lines of Python (source + tests)
- 5 phases, 7 plans, ~30 tasks
- 3 days from first commit to ship (2026-02-06 → 2026-02-09)

**Git range:** `feat(01-01)` → `feat(05-01)`

**What's next:** v1.1 will focus on job data aggregation (LinkedIn/Indeed API integration) and application tracking CLI commands

---

## v1.3.0 Critical Friction & Accessibility (Shipped: 2026-02-11)

**Delivered:** Eliminate application flow friction and achieve WCAG 2.1 Level AA compliance for HTML reports and CLI

**Phases completed:** 16-18 (7 plans total)

**Key accomplishments:**

- One-click copy buttons and batch "Copy All Recommended" action on HTML reports with Clipboard API + execCommand fallback for file:// compatibility
- C/A keyboard shortcuts for clipboard operations with modifier key passthrough and input field protection
- Application status tracking (Applied/Interviewing/Rejected/Offer) with localStorage persistence and embedded tracker.json hydration
- Bidirectional sync: server-embedded status JSON + client-side localStorage merge + downloadable JSON export
- WCAG 2.1 Level AA compliance: skip navigation, ARIA landmarks, accessible tables with scope attributes, screen reader badge context ("Score 4.2 out of 5.0"), focus indicators, 4.5:1 contrast minimum
- Terminal accessibility: NO_COLOR standard support, --no-color CLI flag, colorblind-safe output with text labels paired to all colors

**Stats:**

- 25 files changed, +6,646 / -179 lines
- 3 phases, 7 plans, ~12 tasks
- 1 day (2026-02-11)

**Git range:** `feat(16-01)` → `docs(phase-18)`

**Requirements:** 17/17 satisfied (7 APPLY + 10 A11Y requirements)

**What's next:** v1.4.0 visual hierarchy and enhanced scannability, or new milestone planning

---

