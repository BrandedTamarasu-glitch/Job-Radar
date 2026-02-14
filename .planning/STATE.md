# Project State: Job Radar

**Last Updated:** 2026-02-14T02:15:47Z

## Project Reference

**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

**Current Milestone:** v2.1.0 Source Expansion & Polish

**Milestone Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

## Current Position

**Phase:** 34 - GUI Scoring Configuration
**Current Plan:** 1/2
**Status:** In progress

**Progress:** [██████████░] 50% (of phase 34)

**Next Action:** Continue Phase 34 Plan 02 (Settings tab integration)

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
| 34-01 | 182 | 2 | 1 | 2026-02-13 |
| 33-03 | 923 | 2 | 2 | 2026-02-13 |
| 33-02 | 408 | 2 | 2 | 2026-02-13 |
| 33-01 | 165 | 2 | 2 | 2026-02-13 |

### Quality Indicators

**Test Coverage:**
- 494 tests across 17 test files
- All passing (v2.1.0 in progress)
- Coverage areas: scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management, GUI, rate limiting, JSearch, USAJobs, schema migration

**Code Stats (v2.1.0 in progress):**
- ~19,600 LOC Python (source + tests + GUI)
- 8 GUI modules (3,265 LOC)
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
| Sliders organized into semantic groups (Skills & Fit, Context) | Improves discoverability and understanding of scoring components | 2026-02-13 |
| Proportional normalization on weights | Normalize button preserves relative ratios (0.30/0.40 → 0.43/0.57) more intuitive than equal distribution | 2026-02-13 |
| Collapsible section pattern with triangle indicators | Uses ▶/▼ unicode (not emoji) for expand/collapse, standard pattern for Settings sections | 2026-02-13 |
| Live preview with hardcoded sample job | "Senior Python Developer" with consistent scores provides stable demonstration of weight impact | 2026-02-13 |
| Two-tier validation for scoring weights | Inline orange warning during editing (non-blocking) + error dialog on save (blocking) balances UX and correctness | 2026-02-13 |

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

Completed Phase 34 Plan 01: ScoringConfigWidget Implementation (PLAN 1 OF 2)

**Executed:** Created self-contained CustomTkinter widget for scoring configuration UI

**Key accomplishments:**
- Created 600-line ScoringConfigWidget class in job_radar/gui/scoring_config.py
- Implemented 6 weight sliders (0.05-1.0 range, 0.05 increments) organized into Skills & Fit and Context groups
- Built staffing preference dropdown with 3 options (Boost/Neutral/Penalize)
- Added live preview panel showing sample job score calculation with component breakdown
- Integrated with profile_manager for loading and saving scoring configuration
- Implemented normalize button (proportionally adjusts weights to sum to 1.0)
- Implemented reset button (restores defaults with confirmation dialog)
- Added two-tier validation: inline orange warning during editing, blocking error on save
- Widget includes collapsible header with triangle indicators (▶/▼)
- Combined Task 1 and Task 2 into single implementation (profile integration essential to design)

**Commits:**
- b0962b8 - feat(34-01): create ScoringConfigWidget with sliders, dropdown, and collapsible section

**Duration:** 182 seconds (3min 2s)

### What's Next

Phase 34 Plan 02: Embed ScoringConfigWidget in Settings tab of main_window.py

### Files Changed This Session

- `/Users/coryebert/Job-Radar/job_radar/gui/scoring_config.py` - Created ScoringConfigWidget class (+600 lines)
- `/Users/coryebert/Job-Radar/.planning/phases/34-gui-scoring-configuration/34-01-SUMMARY.md` - Created
- `/Users/coryebert/Job-Radar/.planning/STATE.md` - Updated position, decisions, metrics

### Context for Next Session

**If continuing:** Phase 34 Plan 01 complete - ScoringConfigWidget ready for integration. Next step: embed widget in Settings tab with proper layout and initialization.

**If resuming later:** Read STATE.md for current position, check .planning/phases/34-gui-scoring-configuration/ for summaries. Widget is self-contained and ready to integrate.

---
*State initialized: 2026-02-13*
*Phase 34 in progress - GUI scoring configuration widget complete, Settings integration next*
