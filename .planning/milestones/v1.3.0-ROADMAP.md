# Roadmap: Job Radar

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2025-12-15)
- ✅ **v1.1 Standalone Distribution** - Phases 5-10 (shipped 2026-01-20)
- ✅ **v1.2.0 API Expansion & Resume Intelligence** - Phases 11-15 (shipped 2026-02-05)
- ✅ **v1.3.0 Critical Friction & Accessibility** - Phases 16-18 (shipped 2026-02-11)

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
| 16. Application Flow Essentials | v1.3.0 | 2/2 | Complete | 2026-02-11 |
| 17. Application Status Tracking | v1.3.0 | 2/2 | Complete | 2026-02-11 |
| 18. WCAG 2.1 Level AA Compliance | v1.3.0 | 3/3 | Complete | 2026-02-11 |

---
*Last updated: 2026-02-11 after v1.3.0 milestone completion*
