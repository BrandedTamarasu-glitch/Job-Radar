# Project State: Job Radar

**Last Updated:** 2026-02-13T22:01:33Z

## Project Reference

**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

**Current Milestone:** v2.1.0 Source Expansion & Polish

**Milestone Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

## Current Position

**Phase:** 33 - Scoring Configuration Backend
**Current Plan:** 3/3
**Status:** Complete

**Progress:** [██████████] 100%

**Next Action:** Begin Phase 34 (or next milestone phase as defined in ROADMAP.md)

## Performance Metrics

### Velocity (Recent Milestones)

| Milestone | Phases | Plans | Days | Plans/Day |
|-----------|--------|-------|------|-----------|
| v2.0.0 Desktop GUI | 3 | 8 | 2 | 4.0 |
| v1.5.0 Profile Mgmt | 4 | 7 | 7 | 1.0 |
| v1.4.0 Visual Design | 5 | 9 | 1 | 9.0 |
| v1.3.0 Accessibility | 3 | 7 | 1 | 7.0 |

**Average velocity:** ~5 plans/day (varies by complexity)
| Phase 32 P04 | 426 | 2 tasks | 3 files |
| Phase 32 P03 | 330 | 2 tasks | 6 files |
| Phase 31 P02 | 213 | 1 tasks | 5 files |
| Phase 32 P02 | 158 | 2 tasks | 2 files |
| Phase 33 P02 | 408 | 2 tasks | 2 files |
| Phase 33 P03 | 923 | 2 tasks | 2 files |

### Recent Plan Executions

| Plan | Duration (sec) | Tasks | Files | Date |
|------|---------------|-------|-------|------|
| 33-03 | 923 | 2 | 2 | 2026-02-13 |
| 33-02 | 408 | 2 | 2 | 2026-02-13 |
| 33-01 | 165 | 2 | 2 | 2026-02-13 |
| 32-04 | 426 | 2 | 3 | 2026-02-13 |

### Quality Indicators

**Test Coverage:**
- 494 tests across 17 test files
- All passing (v2.1.0 in progress)
- Coverage areas: scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management, GUI, rate limiting, JSearch, USAJobs, schema migration

**Code Stats (v2.0.0):**
- ~19,000 LOC Python (source + tests + GUI)
- 7 GUI modules (2,665 LOC)
- Zero regressions across milestone transitions

**CI/CD:**
- Automated multi-platform builds (Windows, macOS, Linux)
- Accessibility CI (Lighthouse >=95%, axe-core WCAG validation)
- Smoke tests on all platforms

## Accumulated Context

### Key Decisions This Milestone

| Decision | Rationale | Date |
|----------|-----------|------|
| Start phase numbering at 31 | Continue from v2.0.0 (ended at Phase 30) | 2026-02-13 |
| Infrastructure-first ordering | Fix rate limiter before adding APIs prevents technical debt | 2026-02-13 |
| Schema migration as separate phase | Isolate risk, validate backend before GUI | 2026-02-13 |
| Defer Linux DEB/RPM packaging | .tar.gz acceptable for Linux users, focus macOS/Windows | 2026-02-13 |
| Clear limiters before closing connections | pyrate-limiter background threads cause segfaults if connections closed while active | 2026-02-13 |
| BACKEND_API_MAP fallback to source name | Backward compatibility - unmapped sources continue to work | 2026-02-13 |
| Merge config overrides with defaults | Partial rate limit overrides for better UX - users only customize specific APIs | 2026-02-13 |
| Validate and warn on invalid configs | Invalid rate limit configs show warnings and use defaults - graceful degradation | 2026-02-13 |
| JSearch source attribution from job_publisher | Show original board name (LinkedIn/Indeed/Glassdoor) not "JSearch" for accurate attribution | 2026-02-13 |
| All JSearch sources share rate limiter | linkedin/indeed/glassdoor/jsearch_other use single "jsearch" backend to prevent API violations | 2026-02-13 |
| Validate API keys during setup with inline test requests | Immediate feedback to users prevents configuration errors | 2026-02-13 |
| Store keys even on validation failure | Network issues should not block setup - graceful degradation | 2026-02-13 |
| Profile schema forward-compatible design | New optional fields accepted without code changes - extensibility | 2026-02-13 |
| Three-phase source ordering (scrapers -> APIs -> aggregators) | Ensures native sources win in dedup over aggregated duplicates | 2026-02-13 |
| JSearch display source splitting for progress tracking | Shows individual source progress (LinkedIn: 5, Indeed: 7) not "JSearch: 12" | 2026-02-13 |
| Deduplication returns dict with stats and multi-source map | Enables transparency and future multi-source badge feature | 2026-02-13 |
| GUI Settings tab for API key configuration | Non-technical users can configure API keys without terminal | 2026-02-13 |
| Inline API validation with test buttons | Immediate feedback prevents configuration errors | 2026-02-13 |
| Atomic .env writes using tempfile + replace | Prevents corruption on crashes or interrupts | 2026-02-13 |
| DEFAULT_SCORING_WEIGHTS matches hardcoded scoring.py | Preserve score stability for existing users during migration to v2 | 2026-02-13 |
| v0/v1 profiles migrate directly to v2 | Simplified migration using schema_version < 2 check, not incremental | 2026-02-13 |
| Default staffing_preference is 'neutral' | Clean slate for users to configure (differs from old +4.5 boost) | 2026-02-13 |
| Minimum 0.05 per scoring weight component | Prevents zeroing dimensions while allowing customization | 2026-02-13 |
| Graceful fallback for corrupted scoring_weights | Reset to defaults with warning instead of crashing (availability over strict validation) | 2026-02-13 |
| Triple-fallback for scoring weights | profile weights -> DEFAULT_SCORING_WEIGHTS -> hardcoded .get() defaults for defense-in-depth | 2026-02-13 |
| Staffing preference is post-scoring adjustment | Applied AFTER weighted sum to avoid normalization issues (weights must sum to 1.0) | 2026-02-13 |
| Wizard customize_weights defaults to False | Most users skip advanced customization - opt-in for advanced users only | 2026-02-13 |
| Key-based wizard section headers | Stable UI when questions added/reordered (changed from index-based) | 2026-02-13 |
| Wizard custom weights with retry loop | Collect all 6 weights, validate sum-to-1.0, offer retry on failure for good UX | 2026-02-13 |
| Centralized staffing firm handling in score_job | Removed duplicate logic from _score_response_likelihood to prevent double-boost bug | 2026-02-13 |
| Boost capped at 5.0, penalize floored at 1.0 | Preserves score scale integrity (1.0-5.0 range) | 2026-02-13 |

### Active Constraints

- Python 3.10+ (EOL Oct 2026 - plan migration to 3.11+ by Q4)
- No API keys required for basic usage (tiered approach)
- Backward compatible profiles and CLI flags
- Single-file HTML reports (file:// portability)
- Cross-platform (macOS, Linux, Windows)

### Known Issues

None currently. v2.0.0 shipped clean.

### Todos (Cross-Phase)

- [ ] Research JSearch free tier rate limits (sparse documentation)
- [ ] Test macOS notarization timing (Apple server variability)
- [ ] Document Windows SmartScreen bypass for unsigned installer
- [ ] Validate schema migration with 100+ skill profiles (property-based testing)

### Blockers

None.

## Session Continuity

### What Just Happened

Completed Phase 33 Plan 03: Wizard Integration for Scoring Configuration (PLAN 3 OF 3) - Phase 33 Complete

**Executed:** Updated setup wizard to configure scoring_weights and staffing_preference for new profiles

**Key accomplishments:**
- Task 1: Added scoring weight and staffing preference questions to wizard
- Imported DEFAULT_SCORING_WEIGHTS from profile_manager
- Added staffing_preference select question with 3 descriptive choices (Neutral/Boost/Penalize)
- Added customize_weights confirm question (defaults to False for most users)
- Implemented _prompt_custom_weights helper with interactive validation and retry
- Added select question type handling to wizard prompt loop
- Switched section headers from index-based to key-based for stability
- Added "Scoring Preferences" section between Profile Information and Search Preferences
- Built profile_data with scoring_weights and staffing_preference v2 fields
- Updated summary to display scoring configuration (Default vs Custom, staffing preference)
- Added edit loop support for Scoring Weights and Staffing Firms
- Task 2: Added 5 new tests for wizard v2 schema field output
- test_wizard_profile_has_scoring_weights: verify DEFAULT_SCORING_WEIGHTS used
- test_wizard_profile_has_staffing_preference_neutral/boost/penalize: verify all 3 choices
- test_wizard_default_weights_used_when_not_customized: verify defaults
- All 5 new tests passing, zero regressions

**Commits:**
- 5992765 - feat(33-03): add scoring weights and staffing preference to setup wizard
- d3ab652 - test(33-03): add tests for wizard v2 schema field output

**Duration:** 923 seconds (15min 23s)

### What's Next

Phase 33 complete (3/3 plans done). Ready for next phase as defined in ROADMAP.md.

### Files Changed This Session

- `/home/corye/Claude/Job-Radar/job_radar/wizard.py` - Added scoring configuration questions and handlers (+220 lines)
- `/home/corye/Claude/Job-Radar/tests/test_wizard.py` - Added 5 new v2 schema tests (+274 lines)
- `/home/corye/Claude/Job-Radar/.planning/phases/33-scoring-configuration-backend/33-03-SUMMARY.md` - Created
- `/home/corye/Claude/Job-Radar/.planning/STATE.md` - Updated position, decisions, metrics, marked phase complete

### Context for Next Session

**If continuing:** Phase 33 complete (all 3 plans done) - profile schema v2 with auto-migration, scoring engine using configurable weights, wizard integration complete. Ready for next phase.

**If resuming later:** Read STATE.md for current position, check .planning/phases/33-scoring-configuration-backend/ for summaries. Terminal users can now configure scoring via wizard, scoring engine uses profile weights.

---
*State initialized: 2026-02-13*
*Phase 33 complete - scoring configuration backend ready (schema v2, scoring engine, wizard)*
