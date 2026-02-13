---
phase: 33-scoring-configuration-backend
plan: 03
subsystem: wizard
tags: [wizard, scoring-weights, staffing-preference, v2-schema, setup]

# Dependency graph
requires:
  - phase: 33-scoring-configuration-backend
    plan: 01
    provides: Profile schema v2 with scoring_weights and staffing_preference fields, DEFAULT_SCORING_WEIGHTS constant
provides:
  - Wizard integration for scoring_weights and staffing_preference configuration
  - Staffing preference question with 3 choices (Neutral/Boost/Penalize)
  - Optional scoring weight customization with validation
  - New profiles created via wizard include v2 schema fields
  - Scoring Preferences section in wizard flow
affects: [profile-management, setup-wizard, scoring-configuration-backend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Interactive scoring weight customization with sum-to-1.0 validation
    - Key-based section headers for stable wizard UI
    - Select question type for multi-choice options
    - Optional advanced customization with sensible defaults

key-files:
  created: []
  modified:
    - job_radar/wizard.py
    - tests/test_wizard.py

key-decisions:
  - "Staffing preference question uses select type with descriptive choices including explanations"
  - "Customize_weights defaults to False (most users skip advanced customization)"
  - "Custom weight prompt shows current defaults and validates sum-to-1.0 before accepting"
  - "Section headers switched to key-based logic for stability when questions are added/reordered"
  - "Scoring Preferences section added between Profile Information and Search Preferences"
  - "Summary displays 'Default (balanced)' vs 'Custom' for weights, shows staffing preference"
  - "Edit loop supports resetting weights to defaults or re-customizing"

patterns-established:
  - "Optional advanced settings pattern: confirm question gates complex sub-flow"
  - "Interactive validation pattern: collect all values, validate, offer retry on failure"
  - "Summary display pattern: show simplified 'Default' vs detailed 'Custom' based on complexity"

# Metrics
duration: 923s
completed: 2026-02-13
---

# Phase 33 Plan 03: Wizard Integration for Scoring Configuration Summary

**Setup wizard updated to configure scoring_weights and staffing_preference for new profiles created via CLI**

## Performance

- **Duration:** 15min 23s
- **Started:** 2026-02-13T21:46:09Z
- **Completed:** 2026-02-13T22:01:33Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added staffing_preference select question with 3 descriptive choices
- Added customize_weights confirm question (defaults to False for most users)
- Implemented _prompt_custom_weights helper for interactive weight customization with validation
- Updated wizard to handle 'select' question type for multi-choice options
- Switched section headers from index-based to key-based for stability
- Added "Scoring Preferences" section between Profile Information and Search Preferences
- New profiles include scoring_weights (DEFAULT_SCORING_WEIGHTS or custom)
- New profiles include staffing_preference based on user selection
- Summary displays scoring configuration (Default vs Custom weights, staffing preference)
- Edit loop supports modifying Scoring Weights and Staffing Firms settings
- All 5 new tests pass, zero regressions in test suite

## Task Commits

Each task was committed atomically:

1. **Task 1: Add scoring weight and staffing preference questions to wizard** - `5992765` (feat)
   - Imported DEFAULT_SCORING_WEIGHTS from profile_manager
   - Added staffing_preference and customize_weights questions to questions list
   - Implemented _prompt_custom_weights helper with validation
   - Added select question type handling in prompt loop
   - Updated section headers to key-based logic
   - Built profile_data with v2 schema fields
   - Updated celebration summary to display scoring configuration
   - Added edit loop support for scoring settings

2. **Task 2: Add tests for wizard v2 schema field output** - `d3ab652` (test)
   - test_wizard_profile_has_scoring_weights: verifies scoring_weights with DEFAULT_SCORING_WEIGHTS
   - test_wizard_profile_has_staffing_preference_neutral/boost/penalize: verify all 3 choices
   - test_wizard_default_weights_used_when_not_customized: verify defaults used
   - All 5 new tests pass, profiles include v2 fields

## Files Created/Modified

- `job_radar/wizard.py` - Added DEFAULT_SCORING_WEIGHTS import, staffing_preference and customize_weights questions, _prompt_custom_weights helper, select handling, key-based section headers, v2 field building, summary display, edit loop support (+220 lines)
- `tests/test_wizard.py` - Added 5 new tests for v2 schema field integration (+274 lines)

## Decisions Made

1. **Staffing preference select with descriptive choices** - Each choice includes explanation in parentheses ("Neutral (treat same as direct employers)") for clarity without additional help text

2. **Customize_weights defaults to False** - Most users should use balanced defaults; advanced customization is opt-in to avoid overwhelming new users

3. **Custom weight validation with retry** - _prompt_custom_weights collects all 6 weights, validates sum-to-1.0 (with 0.99-1.01 tolerance), and offers retry on validation failure for good UX

4. **Key-based section headers** - Switched from index-based (`idx == 5`) to key-based (`key == 'min_score'`) headers for stability when questions are added/reordered

5. **Scoring Preferences section** - New section appears between Profile Information and Search Preferences (triggered by `key == 'staffing_preference'`)

6. **Summary display simplification** - Shows "Default (balanced)" for standard weights vs "Custom" with per-component breakdown for customized weights

7. **Edit loop reset option** - When editing Scoring Weights, user can reset to defaults, customize, or keep current (3-way choice for flexibility)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward wizard extension following existing patterns.

## User Setup Required

None - changes apply to new profile creation via wizard (existing profiles unaffected).

## Next Phase Readiness

- Wizard creates profiles with v2 schema fields (scoring_weights, staffing_preference)
- Terminal users can configure scoring via CLI wizard (per user decision)
- Ready for Phase 33-04 (if it exists) or integration with scoring engine to consume these fields
- DEFAULT_SCORING_WEIGHTS properly imported and used throughout wizard

## Verification

All success criteria met:

- [x] Wizard asks staffing preference question with Neutral/Boost/Penalize choices
- [x] Wizard offers optional scoring weight customization (defaults to "No")
- [x] New profiles include scoring_weights with DEFAULT_SCORING_WEIGHTS values
- [x] New profiles include staffing_preference based on user selection
- [x] Summary shows scoring configuration
- [x] Edit loop supports modifying scoring settings
- [x] All existing + new tests pass (5 new tests, zero regressions)
- [x] `pytest tests/test_wizard.py::test_wizard_profile_has_scoring_weights` - PASSED
- [x] `pytest tests/test_wizard.py::test_wizard_profile_has_staffing_preference_neutral` - PASSED
- [x] `pytest tests/test_wizard.py::test_wizard_profile_has_staffing_preference_boost` - PASSED
- [x] `pytest tests/test_wizard.py::test_wizard_profile_has_staffing_preference_penalize` - PASSED
- [x] `pytest tests/test_wizard.py::test_wizard_default_weights_used_when_not_customized` - PASSED
- [x] `python -c "from job_radar.wizard import run_setup_wizard"` - imports cleanly
- [x] `python -c "from job_radar.profile_manager import DEFAULT_SCORING_WEIGHTS; print(DEFAULT_SCORING_WEIGHTS)"` - constant importable

## Self-Check: PASSED

All claimed artifacts verified:

- ✓ SUMMARY.md created at .planning/phases/33-scoring-configuration-backend/33-03-SUMMARY.md
- ✓ job_radar/wizard.py modified with scoring configuration questions and handlers
- ✓ tests/test_wizard.py modified with 5 new v2 schema tests
- ✓ Commit 5992765 exists (feat - wizard changes)
- ✓ Commit d3ab652 exists (test - test additions)
- ✓ DEFAULT_SCORING_WEIGHTS imported in wizard.py
- ✓ staffing_preference question with 3 choices in questions list
- ✓ customize_weights question in questions list
- ✓ _prompt_custom_weights helper function implemented
- ✓ Select question type handling added to prompt loop
- ✓ Key-based section headers implemented
- ✓ Scoring Preferences section header added
- ✓ profile_data includes scoring_weights and staffing_preference
- ✓ Summary displays scoring configuration
- ✓ Edit loop supports Scoring Weights and Staffing Firms editing
- ✓ All 5 new wizard tests passing
- ✓ Wizard imports cleanly without errors

---
*Phase: 33-scoring-configuration-backend*
*Completed: 2026-02-13*
