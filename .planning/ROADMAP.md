# Roadmap: Job Radar

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2025-12-15)
- ✅ **v1.1 Standalone Distribution** - Phases 5-10 (shipped 2026-01-20)
- ✅ **v1.2.0 API Expansion & Resume Intelligence** - Phases 11-15 (shipped 2026-02-05)
- ✅ **v1.3.0 Critical Friction & Accessibility** - Phases 16-18 (shipped 2026-02-11)
- ✅ **v1.4.0 Visual Design & Polish** - Phases 19-23 (shipped 2026-02-11)
- ✅ **v1.5.0 Profile Management & Workflow Efficiency** - Phases 24-27 (shipped 2026-02-12)
- 🚧 **v2.0.0 Desktop GUI Launcher** - Phases 28-30 (in progress)

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

### 🚧 v2.0.0 Desktop GUI Launcher (In Progress)

**Milestone Goal:** Replace the terminal-first experience with a desktop GUI window so non-technical users never need to touch a command prompt

#### Phase 28: GUI Foundation & Threading

**Goal:** Establish non-blocking UI architecture with separate entry points for CLI and GUI

**Depends on:** Phase 27 (v1.5.0 complete)

**Requirements:** GUI-01, GUI-02, GUI-03, GUI-04

**Success Criteria** (what must be TRUE):
1. Double-clicking the executable opens a desktop window with CustomTkinter GUI (no terminal window)
2. Running with CLI flags (e.g., `job-radar --min-score 3.5`) uses the existing CLI path without launching GUI
3. GUI window remains responsive during simulated long-running operations (10+ second mock tasks)
4. Progress updates from worker threads appear correctly in GUI without crashes or freezes
5. Separate executables exist for CLI (with console) and GUI (without console) modes

**Plans:** 3 plans

Plans:
- [ ] 28-01-PLAN.md — GUI window shell + entry point detection
- [ ] 28-02-PLAN.md — Threading infrastructure + progress demo
- [ ] 28-03-PLAN.md — Human verification checkpoint

#### Phase 29: Profile Setup & Search Controls

**Goal:** Deliver complete GUI feature parity with CLI through forms, search configuration, and visual feedback

**Depends on:** Phase 28

**Requirements:** PROF-01, PROF-02, PROF-03, PROF-04, SRCH-01, SRCH-02, SRCH-03, SRCH-04, SRCH-05, PROG-01, PROG-02

**Success Criteria** (what must be TRUE):
1. User can create a new profile via GUI form fields without touching the terminal
2. User can upload a PDF resume via file dialog that pre-fills profile fields using existing parser
3. Profile form validates input and shows clear error messages for invalid fields before submission
4. User can edit an existing profile through the same form (pre-filled with current values)
5. User can click "Run Search" button to start a job search with configurable parameters
6. User can set date range (from/to), minimum score, and "new only" mode through GUI controls
7. Visual progress indicator displays during search execution showing current source being queried
8. Error messages appear in GUI when search fails (network errors, source failures) with actionable text
9. HTML report auto-opens in the default browser when search completes successfully
10. All GUI operations integrate correctly with existing business logic modules (sources.py, scoring.py, report.py, profile_manager.py) without code duplication

**Plans:** TBD

Plans:
- [ ] 29-01: TBD
- [ ] 29-02: TBD
- [ ] 29-03: TBD

#### Phase 30: Packaging & Distribution

**Goal:** Produce production-ready GUI executables for all platforms with proper code signing and CI/CD integration

**Depends on:** Phase 29

**Requirements:** PKG-01, PKG-02, PKG-03

**Success Criteria** (what must be TRUE):
1. PyInstaller builds produce a GUI executable for Windows, macOS, and Linux that launches without errors
2. GUI executable is separate from CLI executable with both included in distribution packages
3. CustomTkinter theme files (.json, .otf fonts) are bundled correctly and GUI displays proper styling in executables
4. Executables work on clean machines without Python installed (verified on all three platforms)
5. macOS .app bundle is code-signed with proper entitlements (com.apple.security.cs.allow-unsigned-executable-memory)
6. GitHub Actions CI/CD workflow builds all platforms on tag triggers and publishes to releases
7. GUI executable does not show console window on Windows when launched by double-click

**Plans:** TBD

Plans:
- [ ] 30-01: TBD
- [ ] 30-02: TBD

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1-4 | v1.0 | 8/8 | Complete | 2025-12-15 |
| 5-10 | v1.1 | 10/10 | Complete | 2026-01-20 |
| 11-15 | v1.2.0 | 8/8 | Complete | 2026-02-05 |
| 16-18 | v1.3.0 | 7/7 | Complete | 2026-02-11 |
| 19-23 | v1.4.0 | 9/9 | Complete | 2026-02-11 |
| 24-27 | v1.5.0 | 7/7 | Complete | 2026-02-12 |
| 28 | v2.0.0 | 0/TBD | Not started | - |
| 29 | v2.0.0 | 0/TBD | Not started | - |
| 30 | v2.0.0 | 0/TBD | Not started | - |

**Total: 27 completed phases (49 plans, 6 milestones shipped) + 3 planned phases for v2.0.0**

---
*Last updated: 2026-02-12 after v2.0.0 roadmap creation*
