# Requirements: Job Radar

**Defined:** 2026-02-11
**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters.

## v1.4.0 Requirements

Requirements for v1.4.0: Visual Design & Polish. Each maps to roadmap phases.

### Visual Design

- [ ] **VIS-01**: Hero jobs (score ≥4.0) display with distinct visual hierarchy — elevated card styling with borders, shadows, and prominent score badges
- [ ] **VIS-02**: Semantic color system uses score-tier colors (green for ≥4.0, cyan for 3.5-3.9, indigo for 2.8-3.4) with non-color indicators for colorblind safety
- [ ] **VIS-03**: Enhanced typography uses system font stacks — sans-serif for body text and monospace for scores/numbers — for zero-overhead rendering
- [ ] **VIS-04**: Responsive table hides low-priority columns at <992px, showing 6 core columns (score, title, company, location, status, link)
- [ ] **VIS-05**: Mobile view (<768px) replaces table with stacked card layout preserving all data and ARIA semantics

### Polish

- [ ] **POL-01**: User can filter jobs by application status (hide Applied, hide Rejected) with filter state persisted to localStorage
- [ ] **POL-02**: Accessibility CI runs Lighthouse (5 runs, median score ≥95) and axe-core on every PR, blocking merge on WCAG violations
- [ ] **POL-03**: User can export job results as CSV from browser with proper UTF-8 BOM encoding for Excel compatibility
- [ ] **POL-04**: Print-friendly stylesheet hides navigation chrome, preserves score colors with print-color-adjust, and adds page break control

## v1.5.0 Requirements (Deferred)

Profile management and workflow efficiency features deferred to next milestone.

### Profile Management

- **PROF-01**: User can preview current profile on search startup
- **PROF-02**: User can quick-edit specific profile fields without full wizard re-run
- **PROF-03**: User can update skills via CLI flag (--update-skills)
- **PROF-04**: User can update min-score via CLI flag (--set-min-score)

## Out of Scope

Explicitly excluded from v1.4.0. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Embedded web fonts (Inter, JetBrains Mono WOFF2) | 150-200KB file size overhead violates single-file HTML constraint; system fonts achieve same aesthetic at zero cost |
| Dynamic font loading from CDN | Breaks file:// protocol and offline usage |
| Animated transitions/micro-interactions | Print compatibility issues, accessibility concerns, scope creep |
| Multi-select filter UI (checkboxes, sliders) | Simple toggle filters sufficient for 4 statuses; complexity not justified |
| Server-side CSV generation | Breaks file:// model; browser-side Blob API is simpler and offline-capable |
| Dark mode theme | Significant scope; defer to future milestone |
| Custom color theme picker | Requires additional localStorage + CSS variable management; defer |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| VIS-01 | Phase 20 | Complete |
| VIS-02 | Phase 19 | Complete |
| VIS-03 | Phase 19 | Complete |
| VIS-04 | Phase 21 | Complete |
| VIS-05 | Phase 21 | Complete |
| POL-01 | Phase 22 | Complete |
| POL-02 | Phase 23 | Complete |
| POL-03 | Phase 22 | Complete |
| POL-04 | Phase 23 | Complete |

**Coverage:**
- v1.4.0 requirements: 9 total
- Mapped to phases: 9 (100% coverage)
- Unmapped: 0

---
*Requirements defined: 2026-02-11*
*Last updated: 2026-02-11 after v1.4.0 roadmap creation*
