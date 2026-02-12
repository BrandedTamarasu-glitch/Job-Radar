# Roadmap: Job Radar

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2025-12-15)
- ✅ **v1.1 Standalone Distribution** - Phases 5-10 (shipped 2026-01-20)
- ✅ **v1.2.0 API Expansion & Resume Intelligence** - Phases 11-15 (shipped 2026-02-05)
- ✅ **v1.3.0 Critical Friction & Accessibility** - Phases 16-18 (shipped 2026-02-11)
- ✅ **v1.4.0 Visual Design & Polish** - Phases 19-23 (shipped 2026-02-11)
- 🚧 **v1.5.0 Profile Management & Workflow Efficiency** - Phases 24-27 (in progress)

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

### v1.5.0 Profile Management & Workflow Efficiency (In Progress)

**Milestone Goal:** Reduce friction in profile updates and improve daily workflow efficiency by centralizing profile I/O, enabling quick profile viewing, and supporting interactive and CLI-driven profile edits with data safety guarantees.

- [x] **Phase 24: Profile Infrastructure** - Centralize profile I/O with atomic writes, backups, validation, and schema versioning
- [x] **Phase 25: Profile Preview** - Users can view their current profile settings on startup and on demand
- [x] **Phase 26: Interactive Quick-Edit** - Users can update individual profile fields interactively with diff preview and confirmation
- [ ] **Phase 27: CLI Update Flags** - Users can update profile fields via CLI flags for scripted and rapid workflows

#### Phase 24: Profile Infrastructure
**Goal**: All profile read/write operations flow through a centralized module with atomic writes, automatic backups, shared validation, and schema versioning
**Depends on**: Phase 23 (builds on existing codebase; no feature dependency)
**Requirements**: SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05, SAFE-06, SAFE-07, SAFE-08
**Success Criteria** (what must be TRUE):
  1. Profile saves never produce corrupted JSON files, even if the process is interrupted mid-write (atomic temp-file-plus-rename pattern)
  2. A timestamped backup copy of the profile is created automatically before every update, and old backups beyond the 10 most recent are deleted
  3. Profile JSON includes a `schema_version` field set to 1, written on every save
  4. Invalid profile data (wrong types, out-of-range values, missing required fields) is rejected with a clear error message before any file is written
  5. All profile I/O in the codebase routes through `profile_manager.py` -- wizard, quick-edit, and CLI flags share the same load/save/validate functions
**Plans**: 2 plans

Plans:
- [x] 24-01-PLAN.md — Create profile_manager.py with atomic writes, backups, validation, and schema versioning
- [x] 24-02-PLAN.md — Wire wizard.py and search.py to use profile_manager, plus unit tests

#### Phase 25: Profile Preview
**Goal**: Users can see their current profile settings in a clear, formatted display both automatically on startup and via explicit command
**Depends on**: Phase 24 (uses profile_manager.py for profile loading)
**Requirements**: VIEW-01, VIEW-02, VIEW-03, VIEW-04, VIEW-05
**Success Criteria** (what must be TRUE):
  1. Running `job-radar` displays a formatted profile summary (name, skills, titles, experience, location, dealbreakers, min_score, new_only) before the search begins
  2. Running `job-radar --view-profile` displays the profile summary and exits without running a search
  3. Profile display uses a table layout with clear section headers that is readable in terminals of 80 columns or wider
  4. Running `job-radar --no-wizard` suppresses the automatic profile preview on startup
  5. Running `job-radar --help` documents all profile management commands and flags (--view-profile, --update-skills, --set-min-score, --no-wizard)
**Plans**: 2 plans

Plans:
- [x] 25-01-PLAN.md — Create profile_display.py module with tabulate dependency and display_profile() function
- [x] 25-02-PLAN.md — Wire profile preview into search.py CLI flow, add --view-profile flag, and create tests

#### Phase 26: Interactive Quick-Edit
**Goal**: Users can update any single profile field through a guided interactive flow that shows changes before saving
**Depends on**: Phase 24 (uses profile_manager.py for save, diff, and validation)
**Requirements**: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-08
**Success Criteria** (what must be TRUE):
  1. User can enter quick-edit mode and select a field to update from a menu listing all editable fields (name, skills, titles, experience, location, dealbreakers, min_score, new_only)
  2. After entering a new value, the user sees a before/after diff showing exactly what will change
  3. The user must explicitly confirm the change before the profile is saved; declining discards the edit with no file modification
  4. Invalid input (e.g., non-numeric min_score, score outside 0.0-5.0) is rejected with a clear error and the user is re-prompted
**Plans**: 2 plans

Plans:
- [x] 26-01-PLAN.md — Create profile_editor.py with field menu, type dispatching, list submenu, diff preview, and validator reuse
- [x] 26-02-PLAN.md — Wire editor into search.py CLI (--edit-profile flag, --view-profile integration), tests

#### Phase 27: CLI Update Flags
**Goal**: Users can update common profile fields directly from the command line without entering interactive mode
**Depends on**: Phase 24 (validation, atomic save), Phase 26 (validation patterns proven in interactive mode)
**Requirements**: EDIT-05, EDIT-06, EDIT-07
**Success Criteria** (what must be TRUE):
  1. Running `job-radar --update-skills "python,react,typescript"` replaces the skills list and exits without running a search
  2. Running `job-radar --set-min-score 3.5` updates the minimum score threshold and exits without running a search
  3. Invalid CLI flag values (e.g., `--set-min-score abc` or `--set-min-score 7.0`) are rejected with a clear error message and non-zero exit code
**Plans**: TBD

Plans:
- [ ] 27-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 24 -> 25 -> 26 -> 27

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Search | v1.0 | 3/3 | Complete | 2025-12-15 |
| 2. Persistence | v1.0 | 2/2 | Complete | 2025-12-15 |
| 3. Polish | v1.0 | 2/2 | Complete | 2025-12-15 |
| 4. Testing | v1.0 | 1/1 | Complete | 2025-12-15 |
| 5. Wizard Foundation | v1.1 | 2/2 | Complete | 2026-01-20 |
| 6. HTML Reports | v1.1 | 2/2 | Complete | 2026-01-20 |
| 7. UX Polish | v1.1 | 2/2 | Complete | 2026-01-20 |
| 8. Executables | v1.1 | 2/2 | Complete | 2026-01-20 |
| 9. CI/CD | v1.1 | 1/1 | Complete | 2026-01-20 |
| 10. Manual URLs | v1.1 | 1/1 | Complete | 2026-01-20 |
| 11. API Sources | v1.2.0 | 2/2 | Complete | 2026-02-05 |
| 12. Credential Management | v1.2.0 | 1/1 | Complete | 2026-02-05 |
| 13. Rate Limiting | v1.2.0 | 1/1 | Complete | 2026-02-05 |
| 14. Deduplication | v1.2.0 | 1/1 | Complete | 2026-02-05 |
| 15. Resume Intelligence | v1.2.0 | 3/3 | Complete | 2026-02-05 |
| 16. Application Flow Essentials | v1.3.0 | 2/2 | Complete | 2026-02-11 |
| 17. Application Status Tracking | v1.3.0 | 2/2 | Complete | 2026-02-11 |
| 18. WCAG 2.1 Level AA Compliance | v1.3.0 | 3/3 | Complete | 2026-02-11 |
| 19. Typography & Color Foundation | v1.4.0 | 2/2 | Complete | 2026-02-11 |
| 20. Hero Jobs Visual Hierarchy | v1.4.0 | 1/1 | Complete | 2026-02-11 |
| 21. Responsive Layout | v1.4.0 | 2/2 | Complete | 2026-02-11 |
| 22. Interactive Features | v1.4.0 | 2/2 | Complete | 2026-02-11 |
| 23. Print & CI Validation | v1.4.0 | 2/2 | Complete | 2026-02-11 |
| 24. Profile Infrastructure | v1.5.0 | 2/2 | Complete | 2026-02-12 |
| 25. Profile Preview | v1.5.0 | 2/2 | Complete | 2026-02-12 |
| 26. Interactive Quick-Edit | v1.5.0 | 2/2 | Complete | 2026-02-12 |
| 27. CLI Update Flags | v1.5.0 | 0/TBD | Not started | - |

---
*Last updated: 2026-02-12 after Phase 26 execution*
