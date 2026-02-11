# Roadmap: Job Radar

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2025-12-15)
- ✅ **v1.1 Standalone Distribution** - Phases 5-10 (shipped 2026-01-20)
- ✅ **v1.2.0 API Expansion & Resume Intelligence** - Phases 11-15 (shipped 2026-02-05)
- ✅ **v1.3.0 Critical Friction & Accessibility** - Phases 16-18 (shipped 2026-02-11)
- 🚧 **v1.4.0 Visual Design & Polish** - Phases 19-23 (in progress)

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

### 🚧 v1.4.0 Visual Design & Polish (In Progress)

**Milestone Goal:** Improve report scannability through visual hierarchy, responsive design, and quality-of-life polish features

#### Phase 19: Typography & Color Foundation
**Goal**: Establish visual design foundation with system font stacks and semantic color system
**Depends on**: Phase 18 (builds on accessibility compliance)
**Requirements**: VIS-02, VIS-03
**Success Criteria** (what must be TRUE):
  1. Report displays with professional typography using system font stacks (sans-serif body, monospace scores) without any external font files
  2. Score tiers have distinct semantic colors (green for ≥4.0, cyan for 3.5-3.9, indigo for 2.8-3.4, slate for <2.8) with WCAG AA contrast maintained
  3. Dark mode support works with automatically adjusted semantic colors preserving readability
  4. Color system includes non-color indicators (icons, borders) for colorblind accessibility
  5. Typography and colors render instantly with zero file size overhead
**Plans**: 2 plans

Plans:
- [x] 19-01-PLAN.md — CSS variables for typography, font stacks, and 3-tier semantic color system with dark mode
- [x] 19-02-PLAN.md — Tier classes on cards/table rows, pill badges, non-color indicators, and tests

#### Phase 20: Hero Jobs Visual Hierarchy
**Goal**: Top-scoring jobs (≥4.0) display with prominent visual distinction to prioritize user attention
**Depends on**: Phase 19 (requires semantic color system)
**Requirements**: VIS-01
**Success Criteria** (what must be TRUE):
  1. Jobs with score ≥4.0 display with elevated card styling (borders, shadows, increased padding) distinct from other listings
  2. Hero jobs show prominent score badges using semantic green color with "Top Match" or "Excellent Match" label
  3. Hero job section appears at top of report before other listings with clear visual separation
  4. Focus indicators on hero jobs remain visible and meet WCAG AA contrast requirements
**Plans**: 1 plan

Plans:
- [x] 20-01-PLAN.md — Hero CSS (shadows, badge labels, divider), hero section split, and tests

#### Phase 21: Responsive Layout
**Goal**: Report adapts to different screen sizes with tablet column reduction and mobile card layout
**Depends on**: Phase 19 (uses typography system)
**Requirements**: VIS-04, VIS-05
**Success Criteria** (what must be TRUE):
  1. Desktop view (≥992px) displays all 11 table columns with full data
  2. Tablet view (<992px) reduces to 7 core columns (#, score, title, company, location, status, link) while hiding 4 low-priority columns
  3. Mobile view (<768px) replaces table with stacked card layout showing all job data in readable format
  4. Table semantics preserved with explicit ARIA roles when using display:block for mobile cards
  5. Screen readers announce table structure correctly on all viewport sizes
  6. All interactive elements (copy buttons, status dropdowns, links) remain accessible on mobile
**Plans**: 2 plans

Plans:
- [ ] 21-01-PLAN.md — Responsive CSS (tablet column hiding, mobile card layout, dark mode), data-label attributes, ARIA restoration JS
- [ ] 21-02-PLAN.md — Responsive layout tests and browser verification checkpoint

#### Phase 22: Interactive Features
**Goal**: Users can filter by application status and export results as CSV for external tracking
**Depends on**: Phase 21 (reuses data attributes from responsive layout)
**Requirements**: POL-01, POL-03
**Success Criteria** (what must be TRUE):
  1. User can filter jobs by status using dropdown controls (hide Applied, hide Rejected, show All)
  2. Filter state persists across browser sessions via localStorage
  3. Filter count updates display with ARIA live region announcements for screen readers
  4. User can click "Export CSV" button to download job results with proper UTF-8 BOM encoding
  5. CSV export includes all visible job data with commas and quotes properly escaped
  6. CSV export respects current filter state (only exports visible jobs)
  7. CSV opens correctly in Excel on Windows with no character corruption
**Plans**: TBD

Plans:
- [ ] 22-01: TBD

#### Phase 23: Print & CI Validation
**Goal**: Print-optimized report output and automated accessibility enforcement in CI pipeline
**Depends on**: Phase 22 (validates all visual features)
**Requirements**: POL-04, POL-02
**Success Criteria** (what must be TRUE):
  1. Print view hides navigation chrome and interactive elements (copy buttons, status dropdowns)
  2. Score colors preserve in print output using print-color-adjust CSS property
  3. Print layout includes page break control to avoid splitting job entries
  4. Print stylesheet overrides Bootstrap's background-color stripping with higher specificity
  5. GitHub Actions CI runs Lighthouse accessibility audit (5 runs, median score ≥95) on every PR
  6. CI runs axe-core checks for WCAG violations blocking merge on failures
  7. Accessibility test reports upload as GitHub Actions artifacts for inspection
  8. CI handles localStorage hydration timing with explicit waits for dynamic content
**Plans**: TBD

Plans:
- [ ] 23-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 19 → 20 → 21 → 22 → 23

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
| 21. Responsive Layout | v1.4.0 | 0/2 | Planned | - |
| 22. Interactive Features | v1.4.0 | 0/0 | Not started | - |
| 23. Print & CI Validation | v1.4.0 | 0/0 | Not started | - |

---
*Last updated: 2026-02-11 after Phase 21 planning complete*
