# Roadmap: Job Radar

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2025-12-15)
- ✅ **v1.1 Standalone Distribution** - Phases 5-10 (shipped 2026-01-20)
- ✅ **v1.2.0 API Expansion & Resume Intelligence** - Phases 11-15 (shipped 2026-02-05)
- 🚧 **v1.3.0 Critical Friction & Accessibility** - Phases 16-18 (in progress)

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

### 🚧 v1.3.0 Critical Friction & Accessibility (In Progress)

**Milestone Goal:** Eliminate application flow friction and achieve WCAG 2.1 Level AA compliance for HTML reports

#### Phase 16: Application Flow Essentials
**Goal**: Users can copy job URLs efficiently with single-click buttons and keyboard shortcuts
**Depends on**: Phase 15
**Requirements**: APPLY-01, APPLY-02, APPLY-03, APPLY-04
**Success Criteria** (what must be TRUE):
  1. User can copy individual job URL with single click from HTML report
  2. User can copy all recommended job URLs (score >=3.5) with one "Copy All" action
  3. User can press 'C' key to copy focused job URL without mouse
  4. User can press 'A' key to copy all recommended URLs without mouse
  5. Copy actions show visual confirmation (toast notification or button state change)
**Plans**: 2 plans

Plans:
- [ ] 16-01-PLAN.md -- Copy buttons, clipboard JS, keyboard shortcuts, and toast notifications in HTML report
- [ ] 16-02-PLAN.md -- Tests for clipboard UI elements and browser verification checkpoint

#### Phase 17: Application Status Tracking
**Goal**: Users can track application status across sessions with persistent visual indicators
**Depends on**: Phase 16
**Requirements**: APPLY-05, APPLY-06, APPLY-07
**Success Criteria** (what must be TRUE):
  1. User can mark job as "Applied" and status persists when report reopens
  2. User can mark job as "Rejected" or "Interviewing" with distinct visual badges
  3. User can see application status on job cards in all subsequent reports
  4. Status data survives browser refresh and multi-day gaps between searches
**Plans**: 2 plans

Plans:
- [ ] 17-01-PLAN.md -- Status dropdown UI, embedded tracker hydration, localStorage sync, and export
- [ ] 17-02-PLAN.md -- Tests for status UI elements and browser verification checkpoint

#### Phase 18: WCAG 2.1 Level AA Compliance
**Goal**: HTML reports and CLI wizard meet WCAG 2.1 Level AA standards for all users including those with disabilities
**Depends on**: Phase 17
**Requirements**: A11Y-01, A11Y-02, A11Y-03, A11Y-04, A11Y-05, A11Y-06, A11Y-07, A11Y-08, A11Y-09, A11Y-10
**Success Criteria** (what must be TRUE):
  1. Keyboard user can skip to main content with single Tab press (skip navigation link works)
  2. Screen reader announces semantic page structure with ARIA landmarks (header, main, nav, section)
  3. Screen reader can navigate job listing table with proper header/cell associations
  4. Score badges announce as "Score 4.2 out of 5.0" (full context, not just "4.2 slash 5")
  5. NEW badges announce as "New listing, not seen in previous searches" (contextual meaning)
  6. All interactive elements show visible focus indicators for keyboard navigation
  7. All text meets 4.5:1 contrast minimum (WCAG AA standard)
  8. CLI wizard prompts are navigable with NVDA, JAWS, and VoiceOver (tested and documented)
  9. Terminal colors meet contrast requirements for colorblind users
  10. HTML reports achieve Lighthouse accessibility score >=95
**Plans**: TBD

Plans:
- [ ] 18-01: TBD
- [ ] 18-02: TBD
- [ ] 18-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 16 -> 17 -> 18

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
| 16. Application Flow Essentials | v1.3.0 | 0/2 | In progress | - |
| 17. Application Status Tracking | v1.3.0 | 0/2 | Not started | - |
| 18. WCAG 2.1 Level AA Compliance | v1.3.0 | 0/3 | Not started | - |

---
*Last updated: 2026-02-11 after Phase 17 planning*
