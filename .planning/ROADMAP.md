# Roadmap: Job Radar

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2025-12-15)
- ✅ **v1.1 Standalone Distribution** - Phases 5-10 (shipped 2026-01-20)
- ✅ **v1.2.0 API Expansion & Resume Intelligence** - Phases 11-15 (shipped 2026-02-05)
- ✅ **v1.3.0 Critical Friction & Accessibility** - Phases 16-18 (shipped 2026-02-11)
- ✅ **v1.4.0 Visual Design & Polish** - Phases 19-23 (shipped 2026-02-11)
- ✅ **v1.5.0 Profile Management & Workflow Efficiency** - Phases 24-27 (shipped 2026-02-12)
- ✅ **v2.0.0 Desktop GUI Launcher** - Phases 28-30 (shipped 2026-02-13)
- 🚀 **v2.1.0 Source Expansion & Polish** - Phases 31-37 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) - SHIPPED 2025-12-15</summary>

### Phase 1: Core Search
**Goal**: Multi-source job search with profile-based scoring
**Plans**: 3 plans

Plans:
- [x] 01-01: Job fetchers for Dice, HN, RemoteOK, WWR
- [x] 01-02: Scoring engine with 6-component system
- [x] 01-03: Markdown report generation

### Phase 2: Persistence
**Goal**: Cross-run tracking and caching
**Plans**: 2 plans

Plans:
- [x] 02-01: Job deduplication and NEW badge tracking
- [x] 02-02: HTTP response caching with TTL

### Phase 3: Polish
**Goal**: Production-ready CLI experience
**Plans**: 2 plans

Plans:
- [x] 03-01: Config file support and CLI flags
- [x] 03-02: Fuzzy skill matching

### Phase 4: Testing
**Goal**: Reliable test coverage
**Plans**: 1 plan

Plans:
- [x] 04-01: pytest suite for scoring, caching, tracking

</details>

<details>
<summary>✅ v1.1 Standalone Distribution (Phases 5-10) - SHIPPED 2026-01-20</summary>

### Phase 5: Wizard Foundation
**Goal**: Interactive first-run setup
**Plans**: 2 plans

Plans:
- [x] 05-01: Questionary-based wizard with validation
- [x] 05-02: First-run detection and profile recovery

### Phase 6: HTML Reports
**Goal**: Dual-format output with browser integration
**Plans**: 2 plans

Plans:
- [x] 06-01: Bootstrap 5 HTML report generation
- [x] 06-02: Browser auto-launch on completion

### Phase 7: UX Polish
**Goal**: Non-technical user experience
**Plans**: 2 plans

Plans:
- [x] 07-01: Progress indicators and friendly errors
- [x] 07-02: Graceful Ctrl+C handling

### Phase 8: Executables
**Goal**: Cross-platform standalone binaries
**Plans**: 2 plans

Plans:
- [x] 08-01: PyInstaller onedir configuration
- [x] 08-02: Platform-specific build scripts

### Phase 9: CI/CD
**Goal**: Automated multi-platform builds
**Plans**: 1 plan

Plans:
- [x] 09-01: GitHub Actions tag-triggered workflow

### Phase 10: Manual URLs
**Goal**: Extended source coverage
**Plans**: 1 plan

Plans:
- [x] 10-01: Indeed, LinkedIn, Glassdoor URL generation

</details>

<details>
<summary>✅ v1.2.0 API Expansion & Resume Intelligence (Phases 11-15) - SHIPPED 2026-02-05</summary>

### Phase 11: API Sources
**Goal**: Authenticated API integrations
**Plans**: 2 plans

Plans:
- [x] 11-01: Adzuna API with salary data
- [x] 11-02: Authentic Jobs API for design roles

### Phase 12: Credential Management
**Goal**: Secure API key handling
**Plans**: 1 plan

Plans:
- [x] 12-01: python-dotenv with .env file support

### Phase 13: Rate Limiting
**Goal**: Prevent API bans with persistent limits
**Plans**: 1 plan

Plans:
- [x] 13-01: SQLite-backed rate limiter

### Phase 14: Deduplication
**Goal**: Cross-source duplicate detection
**Plans**: 1 plan

Plans:
- [x] 14-01: rapidfuzz 85% similarity matching

### Phase 15: Resume Intelligence
**Goal**: PDF resume parsing and wizard integration
**Plans**: 3 plans

Plans:
- [x] 15-01: PDF parser with pdfplumber
- [x] 15-02: Wizard PDF upload option
- [x] 15-03: PDF validation and error handling

</details>

<details>
<summary>✅ v1.3.0 Critical Friction & Accessibility (Phases 16-18) - SHIPPED 2026-02-11</summary>

### Phase 16: Application Flow Essentials
**Goal**: Users can copy job URLs efficiently with single-click buttons and keyboard shortcuts
**Plans**: 2 plans

Plans:
- [x] 16-01: Copy buttons, clipboard JS, keyboard shortcuts, and toast notifications in HTML report
- [x] 16-02: Tests for clipboard UI elements and browser verification checkpoint

### Phase 17: Application Status Tracking
**Goal**: Users can track application status across sessions with persistent visual indicators
**Plans**: 2 plans

Plans:
- [x] 17-01: Status dropdown UI, embedded tracker hydration, localStorage sync, and export
- [x] 17-02: Tests for status UI elements and browser verification checkpoint

### Phase 18: WCAG 2.1 Level AA Compliance
**Goal**: HTML reports and CLI wizard meet WCAG 2.1 Level AA standards for all users including those with disabilities
**Plans**: 3 plans

Plans:
- [x] 18-01: HTML semantic structure, ARIA landmarks, accessible tables, screen reader text, focus indicators, and contrast fixes
- [x] 18-02: CLI NO_COLOR support, colorblind-safe terminal output, and screen reader documentation
- [x] 18-03: Accessibility test suite and Lighthouse verification checkpoint

</details>

<details>
<summary>✅ v1.4.0 Visual Design & Polish (Phases 19-23) - SHIPPED 2026-02-11</summary>

### Phase 19: Typography & Color Foundation
**Goal**: Establish visual design foundation with system font stacks and semantic color system
**Plans**: 2 plans

Plans:
- [x] 19-01: CSS variables for typography, font stacks, and 3-tier semantic color system with dark mode
- [x] 19-02: Tier classes on cards/table rows, pill badges, non-color indicators, and tests

### Phase 20: Hero Jobs Visual Hierarchy
**Goal**: Top-scoring jobs display with prominent visual distinction to prioritize user attention
**Plans**: 1 plan

Plans:
- [x] 20-01: Hero CSS (shadows, badge labels, divider), hero section split, and tests

### Phase 21: Responsive Layout
**Goal**: Report adapts to different screen sizes with tablet column reduction and mobile card layout
**Plans**: 2 plans

Plans:
- [x] 21-01: Responsive CSS (tablet column hiding, mobile card layout, dark mode), data-label attributes, ARIA restoration JS
- [x] 21-02: Responsive layout tests and browser verification checkpoint

### Phase 22: Interactive Features
**Goal**: Users can filter by application status and export results as CSV for external tracking
**Plans**: 2 plans

Plans:
- [x] 22-01: Status filtering UI with localStorage persistence and ARIA announcements
- [x] 22-02: CSV export with UTF-8 BOM, RFC 4180 escaping, and tests for both features

### Phase 23: Print & CI Validation
**Goal**: Print-optimized report output and automated accessibility enforcement in CI pipeline
**Plans**: 2 plans

Plans:
- [x] 23-01: Print CSS expansion with interactive element hiding, color preservation, and 4 tests
- [x] 23-02: Accessibility CI workflow with Lighthouse (5 runs, >=95) + axe-core WCAG checks

</details>

<details>
<summary>✅ v1.5.0 Profile Management & Workflow Efficiency (Phases 24-27) - SHIPPED 2026-02-12</summary>

### Phase 24: Profile Infrastructure
**Goal**: Centralize profile I/O with atomic writes, backups, validation, and schema versioning
**Plans**: 2 plans

Plans:
- [x] 24-01: profile_manager.py with atomic writes, backups, validation, schema versioning
- [x] 24-02: Wire wizard.py and search.py to profile_manager, plus unit tests

### Phase 25: Profile Preview
**Goal**: Formatted profile display on startup and via --view-profile command
**Plans**: 2 plans

Plans:
- [x] 25-01: profile_display.py with tabulate dependency and display_profile()
- [x] 25-02: CLI integration, --view-profile flag, and tests

### Phase 26: Interactive Quick-Edit
**Goal**: Guided field editing with diff preview and confirmation
**Plans**: 2 plans

Plans:
- [x] 26-01: profile_editor.py with field menu, type dispatching, diff preview
- [x] 26-02: --edit-profile flag, --view-profile editor wiring, tests

### Phase 27: CLI Update Flags
**Goal**: CLI flags for scripted profile updates without interactive mode
**Plans**: 1 plan

Plans:
- [x] 27-01: --update-skills, --set-min-score, --set-titles with validators and tests

</details>

<details>
<summary>✅ v2.0.0 Desktop GUI Launcher (Phases 28-30) - SHIPPED 2026-02-13</summary>

### Phase 28: GUI Foundation & Threading
**Goal**: Establish non-blocking UI architecture with separate entry points for CLI and GUI
**Plans**: 3 plans

Plans:
- [x] 28-01: GUI window shell + entry point detection
- [x] 28-02: Threading infrastructure + progress demo
- [x] 28-03: Human verification checkpoint

### Phase 29: Profile Setup & Search Controls
**Goal**: Deliver complete GUI feature parity with CLI through forms, search configuration, and visual feedback
**Plans**: 3 plans

Plans:
- [x] 29-01: Tag chip widget + profile form with validation, PDF upload, and dirty tracking
- [x] 29-02: Search controls widget + real search worker replacing mock
- [x] 29-03: Main window integration + visual verification checkpoint

### Phase 30: Packaging & Distribution
**Goal**: Produce production-ready GUI executables for all platforms with proper code signing and CI/CD integration
**Plans**: 2 plans

Plans:
- [x] 30-01: Entitlements, spec file updates, CI smoke tests and symlink fix
- [x] 30-02: Local build verification and human executable testing checkpoint

</details>

---

## v2.1.0 Source Expansion & Polish

**Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

**Phases:** 31-37 (7 phases)

### Phase 31: Rate Limiter Infrastructure
**Goal:** Fix rate limiter connection leaks and establish shared backend API management before adding new sources

**Dependencies:** None (foundation work)

**Requirements:** INFRA-01, INFRA-02, INFRA-03

**Plans:** 2 plans

Plans:
- [x] 31-01-PLAN.md — Add atexit cleanup and shared backend API rate limiters
- [x] 31-02-PLAN.md — Load rate limit configs from config.json

**Success Criteria:**
1. Rate limiter SQLite connections are cleaned up on app exit with atexit handler
2. Sources sharing the same backend API use a single shared rate limiter instance
3. Rate limit configurations are loaded from config.json instead of hardcoded values
4. Application exits without "database is locked" errors after running searches

---

### Phase 32: Job Aggregator APIs (JSearch, USAJobs)
**Goal:** Users can receive job listings from major aggregator APIs covering LinkedIn, Indeed, Glassdoor, and federal jobs

**Dependencies:** Phase 31 (requires rate limiter infrastructure)

**Requirements:** SRC-01, SRC-02, SRC-05, SRC-06, SRC-08

**Plans:** 4 plans

Plans:
- [x] 32-01-PLAN.md — JSearch + USAJobs fetch functions, response mapping, rate limiter config
- [x] 32-02-PLAN.md — API setup wizard extension + profile schema (federal fields)
- [x] 32-03-PLAN.md — Search pipeline integration (query builder, fetch_all, dedup enhancements)
- [x] 32-04-PLAN.md — GUI API key settings + comprehensive tests

**Success Criteria:**
1. Users can run searches that return results from JSearch API (LinkedIn, Indeed, Glassdoor aggregation)
2. Users can run searches that return results from USAJobs API for federal government jobs
3. Each job listing displays its original source attribution (e.g., "via LinkedIn", "via USAJobs")
4. Duplicate jobs are automatically removed based on exact URL/job ID matching
5. Users can configure API keys for new sources via CLI setup wizard

---

### Phase 33: Scoring Configuration Backend
**Goal:** Profile schema supports user-customizable scoring weights with backward-compatible migration

**Dependencies:** None (backend change independent of sources)

**Requirements:** SCORE-03

**Plans:** 3 plans

Plans:
- [x] 33-01-PLAN.md — Profile schema v2 migration with scoring weights and validation (TDD)
- [x] 33-02-PLAN.md — Scoring engine configurable weights and staffing preference (TDD)
- [x] 33-03-PLAN.md — Wizard integration for v2 profile fields

**Success Criteria:**
1. Existing v1 profiles automatically migrate to v2 schema on first load without data loss
2. New profiles include scoring_weights object with default values in profile template
3. Scoring engine accepts optional weights parameter and uses profile weights when provided
4. Old profiles without scoring_weights fall back to hardcoded defaults (zero errors)

---

### Phase 34: GUI Scoring Configuration
**Goal:** Users can customize scoring weights and staffing firm preference through GUI controls

**Dependencies:** Phase 33 (requires v2 schema backend)

**Requirements:** SCORE-01, SCORE-02, SCORE-04, SCORE-05

**Plans:** 2 plans

Plans:
- [x] 34-01-PLAN.md — ScoringConfigWidget with sliders, dropdown, live preview, and validation
- [x] 34-02-PLAN.md — Settings tab integration, tests, and visual verification

**Success Criteria:**
1. Users can adjust 6 scoring component weights via GUI sliders with real-time validation
2. Users can set staffing firm preference to boost (+4.5), neutral (0), or penalize (-2) via dropdown
3. Users can see a live score preview showing how weight changes affect current results
4. Users can reset all scoring weights to defaults with one-click "Reset" button
5. Invalid weight configurations (e.g., sum != 1.0) display validation errors before save

---

### Phase 35: Additional API Sources (SerpAPI, Jobicy)
**Goal:** Expand source coverage with alternative aggregator and remote-focused job boards

**Dependencies:** Phase 31 (requires rate limiter infrastructure), Phase 32 (validates aggregator pattern)

**Requirements:** SRC-03, SRC-04, SRC-07

**Plans:** 2 plans

Plans:
- [ ] 35-01-PLAN.md — SerpAPI + Jobicy backend: fetch functions, mappers, rate limiter config, search pipeline integration, quota tracking utility
- [ ] 35-02-PLAN.md — CLI wizard extension, GUI Settings tab (API sections, test buttons, quota display), comprehensive tests

**Success Criteria:**
1. Users can receive job results from SerpAPI Google Jobs as alternative to JSearch
2. Users can receive job results from Jobicy remote-focused listings
3. GUI displays API quota usage for rate-limited sources (e.g., "15/100 daily searches used")

---

### Phase 36: GUI Uninstall Feature
**Goal:** Users can cleanly uninstall Job Radar with all config, cache, and data removed

**Dependencies:** None (self-contained feature)

**Requirements:** PKG-01, PKG-02, PKG-03, PKG-06

**Success Criteria:**
1. Users can click "Uninstall" button in GUI Settings tab to remove all app data
2. Uninstall shows confirmation dialog listing exact paths that will be deleted before proceeding
3. Users can create a backup ZIP of profile and config before uninstalling
4. Uninstall works while app is running using two-stage cleanup (delete data now, schedule binary deletion after exit)

---

### Phase 37: Platform-Native Installers
**Goal:** Deliver professional installer experiences for macOS and Windows users

**Dependencies:** Phases 31-36 complete (all features ready for packaging)

**Requirements:** PKG-04, PKG-05

**Success Criteria:**
1. macOS users receive a DMG installer with drag-to-Applications folder workflow
2. Windows users receive an NSIS .exe installer with setup wizard and Add/Remove Programs integration
3. macOS installer is properly code-signed to avoid Gatekeeper "damaged app" warnings
4. Windows installer creates Start Menu shortcuts and desktop icon (optional)

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1-4 | v1.0 | 8/8 | Complete | 2025-12-15 |
| 5-10 | v1.1 | 10/10 | Complete | 2026-01-20 |
| 11-15 | v1.2.0 | 8/8 | Complete | 2026-02-05 |
| 16-18 | v1.3.0 | 7/7 | Complete | 2026-02-11 |
| 19-23 | v1.4.0 | 9/9 | Complete | 2026-02-11 |
| 24-27 | v1.5.0 | 7/7 | Complete | 2026-02-12 |
| 28-30 | v2.0.0 | 8/8 | Complete | 2026-02-13 |
| 31 | v2.1.0 | 2/2 | Complete | 2026-02-13 |
| 32 | v2.1.0 | 4/4 | Complete | 2026-02-13 |
| 33 | v2.1.0 | 3/3 | Complete | 2026-02-13 |
| 34 | v2.1.0 | 2/2 | Complete | 2026-02-13 |
| 35 | v2.1.0 | 0/2 | Planned | — |
| 36 | v2.1.0 | 0/? | Pending | — |
| 37 | v2.1.0 | 0/? | Pending | — |

**Total: 34 completed phases + 3 planned phases (68 completed plans, 7 milestones: 7 shipped + 1 in progress)**

---
*Last updated: 2026-02-13 after Phase 34 planning*
