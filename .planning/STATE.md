# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-11)

**Core value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters.
**Current focus:** Phase 23 - Print & CI Validation

## Current Position

Milestone: v1.4.0 COMPLETE
Phase: — (awaiting next milestone)
Plan: —
Status: Milestone archived, ready for v1.5.0 planning
Last activity: 2026-02-11 — Completed v1.4.0 milestone (Visual Design & Polish)

## Performance Metrics

**Velocity:**
- Total plans completed: 48
- Average duration: 189s (v1.4.0 plans: 159s + 255s + 379s + 147s + 57s + 85s + 200s + 163s + 720s / 9)
- Total execution time: Not tracked

**By Milestone:**

| Milestone | Phases | Status |
|-----------|--------|--------|
| v1.0 | 1-4 | Complete (2025-12-15) |
| v1.1 | 5-10 | Complete (2026-01-20) |
| v1.2.0 | 11-15 | Complete (2026-02-05) |
| v1.3.0 | 16-18 | Complete (2026-02-11) |
| v1.4.0 | 19-23 | ✅ SHIPPED (2026-02-11) |

**Recent Trend:**
- v1.4.0: All phases (19-23) complete, 9 plans total, excellent velocity
- Phase 19: 2 plans, completed in <1 hour (2026-02-11)
- Phase 20: 1 plan, 379s (hero visual hierarchy)
- Phase 21: 2 plans (responsive layout + tests), 147s + 57s = 204s total
- Phase 22: 2 plans (filtering + CSV export), 85s + 200s = 285s total
- Phase 23: 2 plans (print CSS + CI validation), 163s + 720s = 883s total
- Velocity: Excellent (polish features with comprehensive testing)

*Updated after each plan completion*
| Phase 19 P01 | 159s | 2 tasks | 1 files |
| Phase 19 P02 | 255s | 3 tasks | 2 files |
| Phase 20 P01 | 379s | 2 tasks | 2 files |
| Phase 21 P01 | 147s | 2 tasks | 1 files |
| Phase 21 P02 | 57s | 2 tasks | 1 files |
| Phase 22 P01 | 85s | 2 tasks | 1 files |
| Phase 22 P02 | 200s | 2 tasks | 2 files |
| Phase 23 P01 | 163s | 2 tasks | 2 files |
| Phase 23 P02 | 720s | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v1.4.0 planning: System font stacks chosen over base64-embedded fonts (zero overhead, instant rendering, better performance)
- v1.4.0 planning: CSS-first additive integration (all features as inline CSS/JS enhancements to report.py)
- v1.4.0 planning: Lighthouse CI with 5 runs for median score + axe-core as primary tool (handles dynamic content, avoids flakiness)
- [Phase 19-01]: HSL color variables split into H/S/L components for dark mode lightness inversion
- [Phase 19-01]: System font stacks (system-ui/monospace) chosen for zero overhead and instant rendering
- [Phase 19-02]: Tier classes applied to cards (background + border) and table rows (border only) for different visual densities
- [Phase 19-02]: Border thickness variation (5px/4px/3px) provides non-color tier distinction for colorblind users
- [Phase 19-02]: All badges unified with pill style (score, status, NEW) for visual coherence
- [Phase 20-01]: Multi-layer shadow depth (3 levels: 1px/4px/8px) for hero cards creates perceptible elevation without overwhelming
- [Phase 20-01]: Hero threshold at score >= 4.0 maintains meaningful gap from recommended (3.5-3.9), aligns with quartile thinking
- [Phase 20-01]: Separate hero section at top (not mixed) provides immediate prominence and clearer information hierarchy
- [Phase 20-01]: "Top Match" badge label chosen for user-focused language over developer jargon ("Hero") or vague terms
- [Phase 21-01]: Tablet breakpoint at 991px hides 4 low-priority columns (New, Salary, Type, Snippet) to preserve readability while keeping 7 essential columns visible
- [Phase 21-01]: Mobile breakpoint at 767px transforms table to stacked cards showing ALL columns including tablet-hidden ones, with 7em label column for consistent alignment
- [Phase 21-01]: AddTableARIA() runs immediately (not on DOMContentLoaded) since script is at end of body after table DOM is loaded
- [Phase 21-02]: 10 test functions verify responsive patterns via string assertions on generated HTML output
- [Phase 21-02]: Human verification required for three-breakpoint visual behavior (desktop/tablet/mobile)
- [Phase 21-02]: Checkpoint pattern established: automated setup, human approval, continuation flow
- [Phase 22-01]: Filter state persisted to separate localStorage key 'job-radar-filter-state' for cleaner separation from status map
- [Phase 22-01]: Filter operates on data-job-key attribute reading from 'job-radar-application-status' map to maintain single source of truth
- [Phase 22-01]: Filter hides with display:none + aria-hidden='true' to preserve DOM structure while removing from accessibility tree
- [Phase 22-01]: ARIA announcements clear after 1000ms timeout allowing screen readers to re-announce on repeated changes
- [Phase 22-01]: Show All button clears all filters at once (not individual clear buttons) for simpler UX
- [Phase 22-02]: Export CSV button placed after Show All button in filter bar for logical grouping with filter controls
- [Phase 22-02]: CSV includes 11 columns (Rank, Score, New, Status, Title, Company, Salary, Type, Location, Snippet, URL) matching table order
- [Phase 22-02]: Formula injection protection prefixes =+-@ characters with single quote (standard mitigation, preserves value visually)
- [Phase 22-02]: UTF-8 BOM (\uFEFF) prepended to CSV ensures Excel on Windows correctly interprets UTF-8 encoding
- [Phase 22-02]: Dual extraction logic for table rows vs cards handles different DOM structures for hero/recommended cards and table
- [Phase 22-02]: Tests verify string patterns in generated HTML (not functional behavior) for fast execution following existing pattern
- [Phase 23-01]: Both print-color-adjust (standard) and -webkit-print-color-adjust (Safari) included for cross-browser color preservation
- [Phase 23-01]: Both break-inside: avoid (modern) and page-break-inside: avoid (legacy) for maximum browser compatibility
- [Phase 23-01]: All tier color classes receive print-color-adjust to override Bootstrap background stripping with higher specificity
- [Phase 23-01]: Box shadows removed from .card and .hero-job in print media query to avoid rendering artifacts
- [Phase 23-02]: Lighthouse CI configured with 5 runs for median score stability (reduces flakiness)
- [Phase 23-02]: disableStorageReset: true handles localStorage hydration timing without explicit waits
- [Phase 23-02]: axe-core --exit flag ensures CI fails on WCAG violations (exit code 0 without it)
- [Phase 23-02]: --load-delay 2000 gives DOMContentLoaded scripts time to complete before axe audit
- [Phase 23-02]: staticDistDir makes Lighthouse host files internally; python server only for axe-core
- [Phase 23-02]: CI report generation script creates multi-tier sample data (hero/recommended/review)

### Pending Todos

None yet.

### Blockers/Concerns

**Phase 21 (Responsive Layout):**
- Complex ARIA semantics when using display:block on tables
- Safari pre-2024 may drop table semantics with display changes
- Mitigation: explicit ARIA role restoration, test with NVDA/VoiceOver

**Phase 23 (Print & CI Validation):** ✓ RESOLVED
- Lighthouse CI must handle localStorage hydration timing (status tracking loads on DOMContentLoaded)
- Mitigation implemented: disableStorageReset: true in Lighthouse config + --load-delay 2000 for axe-core

**CSV Export (Phase 22):** ✓ RESOLVED
- CSV formula injection risk if job titles contain =SUM() or similar
- Mitigation implemented: escapeCSVField() prefixes values starting with =+-@ with single quote

## Session Continuity

Last session: 2026-02-11 (milestone completion)
Stopped at: v1.4.0 shipped and archived
Resume file: None

**Next action:** Start v1.5.0 milestone planning with `/gsd:new-milestone`, or deploy v1.4.0 to production.
