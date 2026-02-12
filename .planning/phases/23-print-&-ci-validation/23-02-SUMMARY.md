---
phase: 23-print-ci-validation
plan: 02
subsystem: ci-testing
tags: [lighthouse, axe-core, github-actions, accessibility, wcag, ci-cd]

# Dependency graph
requires:
  - phase: 18-wcag-compliance
    provides: WCAG 2.1 AA compliant HTML report with semantic structure and ARIA labels
  - phase: 22-interactive-features
    provides: localStorage-based status tracking and filtering
provides:
  - Automated accessibility CI pipeline running on every PR
  - Lighthouse CI with 5 runs and 0.95 median accessibility threshold
  - axe-core WCAG 2.1 AA validation with blocking failures
  - Sample report generation script for CI testing
  - Artifact uploads for Lighthouse and axe-core results
affects: [future-phases-adding-ui-features, ui-regression-testing]

# Tech tracking
tech-stack:
  added: [treosh/lighthouse-ci-action@v12, @axe-core/cli]
  patterns: [ci-accessibility-validation, artifact-uploads, sample-data-generation]

key-files:
  created: [.github/workflows/accessibility.yml, lighthouserc.js, scripts/generate_ci_report.py]
  modified: []

key-decisions:
  - "Lighthouse CI configured with 5 runs for median score stability (reduces flakiness)"
  - "disableStorageReset: true handles localStorage hydration timing without explicit waits"
  - "axe-core --exit flag ensures CI fails on WCAG violations (exit code 0 without it)"
  - "--load-delay 2000 gives DOMContentLoaded scripts time to complete before axe audit"
  - "staticDistDir makes Lighthouse host files internally; python server only for axe-core"
  - "CI report generation script creates multi-tier sample data (hero/recommended/review)"

patterns-established:
  - "CI report generation: Python script produces realistic HTML with index.html naming for predictable paths"
  - "Dual tool approach: Lighthouse for overall score, axe-core for specific WCAG rule violations"
  - "Artifact persistence: Upload results even on failure (if: always()) for debugging"

# Metrics
duration: ~12min (estimated from checkpoint pattern)
completed: 2026-02-11
---

# Phase 23 Plan 02: Accessibility CI Pipeline Summary

**Automated Lighthouse and axe-core accessibility validation on every PR with 5-run median scoring and WCAG 2.1 AA enforcement**

## Performance

- **Duration:** ~12 minutes (estimated across checkpoint pause)
- **Started:** 2026-02-11T18:37:00Z (estimated)
- **Completed:** 2026-02-11T18:51:46Z
- **Tasks:** 2 (1 automated + 1 checkpoint verification)
- **Files modified:** 3

## Accomplishments
- Created GitHub Actions workflow triggering on PRs with Lighthouse CI (5 runs, median >= 0.95) and axe-core (WCAG 2.1 AA)
- Implemented sample report generation script producing realistic multi-tier job results (hero/recommended/review)
- Configured localStorage hydration timing handling via disableStorageReset
- Set up artifact uploads for both Lighthouse and axe-core results with always() condition

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CI report generation script, Lighthouse config, and accessibility workflow** - `d7ef268` (feat)
   - Bug fix: `39ffcfa` (fix) - Added missing from_date and to_date parameters to generate_report call

2. **Task 2: Human verification checkpoint** - Approved by user

**Plan metadata:** (to be committed after this summary)

## Files Created/Modified
- `.github/workflows/accessibility.yml` - GitHub Actions workflow running Lighthouse CI and axe-core on PRs to main branch
- `lighthouserc.js` - Lighthouse CI configuration with 5 runs, 0.95 accessibility threshold, disableStorageReset for timing
- `scripts/generate_ci_report.py` - Python script generating realistic HTML report with 3 tiers of jobs, renames to index.html

## Decisions Made

**1. Five-run median scoring for stability**
- Lighthouse CI runs 5 times and uses median score to reduce flakiness from timing variations
- Threshold set at 0.95 (95%) to enforce high accessibility standards

**2. localStorage hydration timing handled automatically**
- `disableStorageReset: true` in Lighthouse config prevents storage clearing between runs
- Allows status tracking to persist and hydrate correctly
- `--load-delay 2000` in axe-core gives DOMContentLoaded scripts time to complete

**3. Dual tool approach for comprehensive coverage**
- Lighthouse CI: Overall accessibility score with performance context
- axe-core: Specific WCAG 2.1 AA rule violations with detailed reporting
- Both upload artifacts for debugging (even on failure via `if: always()`)

**4. Critical exit flag on axe-core**
- `--exit` flag makes axe-core return non-zero exit code on violations
- Without this flag, violations would return 0 and CI would never fail

**5. Static dist directory pattern**
- Lighthouse CI uses `staticDistDir: './ci-report'` to host files internally
- Separate Python HTTP server only needed for axe-core testing
- Simplifies workflow by avoiding dual server setup

**6. Sample data generation for CI**
- Python script creates realistic multi-tier report (hero/recommended/review)
- Renames timestamped output to `index.html` for predictable path
- Matches test fixture patterns from test_report.py

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing from_date and to_date parameters**
- **Found during:** Task 1 (CI report generation script)
- **Issue:** generate_report() call was missing required from_date and to_date parameters, causing script to fail
- **Fix:** Added from_date="2026-02-06" and to_date="2026-02-08" matching the date_posted range in sample data
- **Files modified:** scripts/generate_ci_report.py
- **Verification:** Script runs without errors, produces ci-report/index.html successfully
- **Committed in:** 39ffcfa (separate fix commit after feat commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Bug fix necessary for script to execute. No scope changes.

## Issues Encountered

None - execution proceeded smoothly after bug fix.

## User Setup Required

None - no external service configuration required. The workflow will automatically run on future PRs to main branch.

## Next Phase Readiness

**Phase 23 complete** - This was the final plan in Phase 23 (Print & CI Validation).

**v1.4.0 milestone complete** - All phases (19-23) for the v1.4.0 feature release are now done:
- ✓ Phase 19: Typography and color foundation
- ✓ Phase 20: Hero visual hierarchy
- ✓ Phase 21: Responsive layout
- ✓ Phase 22: Interactive features (filtering + CSV export)
- ✓ Phase 23: Print CSS and CI validation

**Accessibility enforcement active:**
- All future PRs will run Lighthouse and axe-core validation
- Accessibility regressions will block merge (score must be >= 0.95)
- WCAG 2.1 AA compliance established in Phase 18 is now protected by automation

**Ready for:** Production deployment or additional feature development with accessibility guardrails in place.

---
*Phase: 23-print-ci-validation*
*Completed: 2026-02-11*
