# Requirements: Job Radar

**Defined:** 2026-02-11
**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters.

## v1.3.0 Requirements

Requirements for v1.3.0: Critical Friction & Accessibility. Each maps to roadmap phases.

### Application Flow

- [ ] **APPLY-01**: User can copy individual job URL with single click from HTML report
- [ ] **APPLY-02**: User can copy all recommended job URLs (score ≥3.5) with single "Copy All" action
- [ ] **APPLY-03**: User can use keyboard shortcut 'C' to copy focused job URL
- [ ] **APPLY-04**: User can use keyboard shortcut 'A' to copy all recommended URLs
- [ ] **APPLY-05**: User can mark job as "Applied" and status persists across sessions (localStorage)
- [ ] **APPLY-06**: User can mark job as "Rejected" or "Interviewing" with visual indicators
- [ ] **APPLY-07**: User can view application status on job cards in subsequent reports

### Accessibility

- [ ] **A11Y-01**: Keyboard user can skip to main content with single Tab press (skip navigation link)
- [ ] **A11Y-02**: Screen reader announces semantic page structure with ARIA landmark regions
- [ ] **A11Y-03**: Screen reader can navigate job listing table with proper header/cell associations
- [ ] **A11Y-04**: Screen reader announces job score badges with full context ("Score 4.2 out of 5.0")
- [ ] **A11Y-05**: Screen reader announces NEW badges with context ("New listing, not seen in previous searches")
- [ ] **A11Y-06**: Keyboard user can see visible focus indicators on all interactive elements
- [ ] **A11Y-07**: All text meets WCAG 2.1 Level AA contrast requirements (4.5:1 minimum)
- [ ] **A11Y-08**: CLI wizard prompts are navigable with screen readers (NVDA, JAWS, VoiceOver tested)
- [ ] **A11Y-09**: Terminal color choices meet contrast requirements for colorblind users
- [ ] **A11Y-10**: HTML reports achieve Lighthouse accessibility score ≥95

## v1.4.0 Requirements (Deferred)

Visual hierarchy and enhanced scannability features deferred to next milestone.

### Visual Design

- **VIS-01**: Hero jobs (≥4.0) display with distinct visual hierarchy (borders, shadows, prominent badges)
- **VIS-02**: Semantic color system uses green (excellent), cyan (good), indigo (acceptable), slate (lower priority)
- **VIS-03**: Enhanced typography with Inter body font and JetBrains Mono for scores/numbers
- **VIS-04**: Responsive table reduces from 10 columns to 6 core columns
- **VIS-05**: Mobile view displays job cards instead of tables for <768px screens

### Polish

- **POL-01**: Status filters allow hiding already-applied jobs
- **POL-02**: Automated accessibility audit blocks releases on violations (Lighthouse + axe in CI)
- **POL-03**: CSV export for external tracking tools
- **POL-04**: Print-friendly stylesheet

## v1.5.0 Requirements (Deferred)

Profile management and workflow efficiency features deferred to future milestone.

### Profile Management

- **PROF-01**: User can preview current profile on search startup
- **PROF-02**: User can quick-edit specific profile fields without full wizard re-run
- **PROF-03**: User can update skills via CLI flag (--update-skills)
- **PROF-04**: User can update min-score via CLI flag (--set-min-score)

## Out of Scope

Explicitly excluded from v1.3.0. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Cloud-based application tracking | Job Radar is privacy-focused and offline-first; localStorage sufficient |
| AI-powered job matching | Core value is transparent scoring algorithm; AI would reduce trust |
| Social features (sharing, following) | Out of domain - Job Radar is personal search tool |
| Mobile app | Desktop CLI tool; responsive HTML reports cover mobile viewing |
| Real-time notifications | Batch daily search workflow is intentional design |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| APPLY-01 | Phase 16 | Pending |
| APPLY-02 | Phase 16 | Pending |
| APPLY-03 | Phase 16 | Pending |
| APPLY-04 | Phase 16 | Pending |
| APPLY-05 | Phase 17 | Pending |
| APPLY-06 | Phase 17 | Pending |
| APPLY-07 | Phase 17 | Pending |
| A11Y-01 | Phase 18 | Pending |
| A11Y-02 | Phase 18 | Pending |
| A11Y-03 | Phase 18 | Pending |
| A11Y-04 | Phase 18 | Pending |
| A11Y-05 | Phase 18 | Pending |
| A11Y-06 | Phase 18 | Pending |
| A11Y-07 | Phase 18 | Pending |
| A11Y-08 | Phase 18 | Pending |
| A11Y-09 | Phase 18 | Pending |
| A11Y-10 | Phase 18 | Pending |

**Coverage:**
- v1.3.0 requirements: 17 total
- Mapped to phases: 17 (100% coverage)
- Unmapped: 0

---
*Requirements defined: 2026-02-11*
*Last updated: 2026-02-10 after roadmap creation*
