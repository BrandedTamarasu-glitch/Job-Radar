---
phase: 33-scoring-configuration-backend
plan: 01
subsystem: profile-management
tags: [schema-migration, validation, scoring-weights, tdd, profile-v2]

# Dependency graph
requires:
  - phase: 32-job-aggregator-apis
    provides: Rate limiting infrastructure, API configuration management
provides:
  - Profile schema v2 with scoring_weights and staffing_preference fields
  - Automatic v0->v2 and v1->v2 migration with backup creation
  - DEFAULT_SCORING_WEIGHTS constant for scoring.py integration
  - Validation for scoring_weights (6 components, sum-to-1.0, 0.05 minimum)
  - Validation for staffing_preference (boost/neutral/penalize)
  - Graceful fallback for corrupted scoring_weights
affects: [34-scoring-weights-wizard, 35-staffing-preference-ui, scoring-configuration-backend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Schema migration with automatic backup creation before upgrade
    - Graceful fallback for corrupted fields with warning logs
    - Forward-compatible validation (unknown fields preserved)
    - TDD with RED-GREEN-REFACTOR cycle for critical migrations

key-files:
  created: []
  modified:
    - job_radar/profile_manager.py
    - tests/test_profile_manager.py

key-decisions:
  - "DEFAULT_SCORING_WEIGHTS values extracted from current hardcoded scoring.py behavior (lines 47-54) to preserve score stability"
  - "v0 and v1 profiles migrate directly to v2 (not incrementally) using schema_version < 2 check"
  - "Default staffing_preference is 'neutral' (differs from old hardcoded +4.5 boost)"
  - "Corrupted scoring_weights reset to defaults with warning instead of crashing"
  - "Each weight component requires minimum 0.05 (prevents one dimension dominating)"
  - "Sum-to-1.0 validation uses 0.99-1.01 tolerance for float precision"

patterns-established:
  - "Schema migration pattern: backup → add fields → update version → save → validate"
  - "Graceful degradation: detect corruption → log warning → reset to safe defaults → continue"
  - "TDD execution: failing tests first (RED) → implementation (GREEN) → verification"

# Metrics
duration: 165s
completed: 2026-02-13
---

# Phase 33 Plan 01: Profile Schema v2 Migration Summary

**Profile schema v2 with auto-migration, scoring_weights validation, and graceful fallback for corrupted data**

## Performance

- **Duration:** 2min 45s
- **Started:** 2026-02-13T21:39:21Z
- **Completed:** 2026-02-13T21:42:06Z
- **Tasks:** 2 (TDD: RED → GREEN)
- **Files modified:** 2

## Accomplishments

- Bumped profile schema from v1 to v2 with backward-compatible auto-migration
- Added DEFAULT_SCORING_WEIGHTS constant matching current hardcoded behavior exactly
- Implemented v0→v2 and v1→v2 migration with automatic backup creation
- Added comprehensive validation for scoring_weights (6 components, 0.05-1.0 range, sum to 1.0)
- Added validation for staffing_preference (boost/neutral/penalize)
- Graceful fallback resets corrupted scoring_weights to defaults with warning
- All existing data preserved during migration (backward compatible)
- Zero test regressions (494 tests passing, 12 new tests added)

## Task Commits

Each task was committed atomically following TDD RED-GREEN-REFACTOR:

1. **Task 1: RED - Write failing tests for v2 schema migration and validation** - `6a943ad` (test)
   - Added 12 new test cases covering migration, validation, and fallback
   - Tests fail with ImportError on DEFAULT_SCORING_WEIGHTS (expected RED phase)

2. **Task 2: GREEN + REFACTOR - Implement v2 migration and validation** - `78ad414` (feat)
   - Implemented DEFAULT_SCORING_WEIGHTS constant
   - Added v0→v2 and v1→v2 migration logic
   - Extended validate_profile with scoring_weights and staffing_preference checks
   - Added graceful fallback for corrupted scoring_weights
   - All 494 tests passing (GREEN phase achieved)

## Files Created/Modified

- `job_radar/profile_manager.py` - Added DEFAULT_SCORING_WEIGHTS constant, v2 migration logic, extended validation, graceful fallback for corrupted weights
- `tests/test_profile_manager.py` - Added 12 new tests for migration (5 tests), validation (7 tests), and graceful fallback

## Decisions Made

1. **DEFAULT_SCORING_WEIGHTS values match current hardcoded behavior** - Extracted exact values from scoring.py lines 47-54 to preserve score stability for existing users (skill_match: 0.25, title_relevance: 0.15, seniority: 0.15, location: 0.15, domain: 0.10, response_likelihood: 0.20)

2. **Single-step migration from v0/v1 to v2** - Used `schema_version < 2` check instead of incremental v0→v1→v2 migration for simplicity

3. **Default staffing_preference is 'neutral'** - Differs from old hardcoded +4.5 boost, giving users clean slate to configure preference

4. **Minimum 0.05 per weight component** - Prevents any single dimension from being zeroed out while allowing significant customization

5. **Float tolerance 0.99-1.01 for sum validation** - Accommodates floating-point precision issues while enforcing normalization constraint

6. **Graceful fallback for corrupted weights** - Corrupted scoring_weights (wrong type) automatically reset to defaults with warning instead of crashing - prioritizes availability over strict validation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - TDD workflow and clear specifications enabled smooth execution.

## User Setup Required

None - migration happens automatically on first profile load after upgrade.

## Next Phase Readiness

- Profile schema v2 foundation complete
- DEFAULT_SCORING_WEIGHTS exported and ready for import by scoring.py (Phase 33-02)
- Migration tested with comprehensive coverage (v0→v2, v1→v2, backup creation, data preservation)
- Ready for Phase 33-02: Wizard integration for scoring_weights configuration
- Ready for Phase 33-03: Scoring engine integration to read weights from profile

## Verification

All success criteria met:

- [x] CURRENT_SCHEMA_VERSION bumped from 1 to 2
- [x] DEFAULT_SCORING_WEIGHTS constant matches current hardcoded values exactly
- [x] v0 and v1 profiles auto-migrate to v2 with backup on first load
- [x] scoring_weights validated: 6 required components, each 0.05-1.0, sum to 1.0
- [x] staffing_preference validated: must be "boost", "neutral", or "penalize"
- [x] Corrupted scoring_weights gracefully reset with warning
- [x] All existing tests pass (zero regressions)
- [x] 12 new tests covering migration, validation, and graceful fallback

## Self-Check: PASSED

All claimed artifacts verified:

- ✓ SUMMARY.md created at .planning/phases/33-scoring-configuration-backend/33-01-SUMMARY.md
- ✓ job_radar/profile_manager.py modified with DEFAULT_SCORING_WEIGHTS and v2 migration
- ✓ tests/test_profile_manager.py modified with 12 new tests
- ✓ Commit 6a943ad exists (test phase)
- ✓ Commit 78ad414 exists (feat phase)
- ✓ DEFAULT_SCORING_WEIGHTS constant defined with 6 components summing to 1.0
- ✓ CURRENT_SCHEMA_VERSION = 2
- ✓ All 34 profile_manager tests passing (22 existing + 12 new)
- ✓ Full test suite passing (494 tests total)

---
*Phase: 33-scoring-configuration-backend*
*Completed: 2026-02-13*
