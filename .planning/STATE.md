# Project State: Job Radar

**Last Updated:** 2026-02-14T17:53:23Z

## Project Reference

**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

**Current Milestone:** v2.1.0 Source Expansion & Polish

**Milestone Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

## Current Position

**Phase:** 36 - GUI Uninstall Feature
**Current Plan:** 2/2
**Status:** Phase complete

**Progress:** [████████████████████████] 100% (phase 36: 2/2 plans complete)

**Next Action:** Phase 36 complete - Ready for next milestone phase

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
| 36-02 | 213 | 2 | 3 | 2026-02-14 |
| 36-01 | 225 | 2 | 2 | 2026-02-14 |
| 35-02 | 410 | 3 | 4 | 2026-02-14 |
| 35-01 | 230 | 2 | 2 | 2026-02-14 |
| 34-02 | 89 | 3 | 2 | 2026-02-14 |

### Quality Indicators

**Test Coverage:**
- 566 tests across 19 test files
- All passing (v2.1.0 in progress)
- Coverage areas: scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management, GUI, rate limiting, JSearch, USAJobs, schema migration, scoring config widget, uninstaller

**Code Stats (v2.1.0 in progress):**
- ~20,450 LOC Python (source + tests + GUI)
- 9 GUI modules (3,899 LOC)
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
| SerpAPI conservative 50/min rate limit | Free tier has 100 searches/month cap, conservative rate prevents exhaustion | 2026-02-14 |
| Jobicy 1/hour rate limit | Per API documentation ("once per hour"), strict public API limit | 2026-02-14 |
| SerpAPI in aggregator phase, Jobicy in API phase | SerpAPI is Google Jobs aggregator (runs last), Jobicy is native remote source (runs middle) | 2026-02-14 |
| get_quota_usage() queries SQLite bucket directly | Read-only SELECT on rate_limits table for (used, limit, period) tuples enables real-time quota display | 2026-02-14 |
| Jobicy requires non-empty description after HTML cleaning | Skip jobs with empty description to ensure scoring quality | 2026-02-14 |
| Quota labels show 'X/Y this period' format | Real-time feedback next to each API section in GUI Settings tab | 2026-02-14 |
| Color-coded quota warnings (gray/orange/red) | Orange at 80% usage, red at 100% for quota awareness | 2026-02-14 |
| update_quota_display() called after search | Updates quota labels from SQLite buckets for immediate feedback | 2026-02-14 |
| Jobicy displayed as always-available in wizard | Public API with no key required, rate limited to 1/hour | 2026-02-14 |
| shutil.rmtree onerror for Python 3.10+ compatibility | Use onerror parameter (not onexc) for backward compatibility with Python 3.10-3.11 | 2026-02-14 |
| Best-effort deletion with error collection | Continue deletion on failures, return list of (path, error) tuples for transparency | 2026-02-14 |
| macOS .app bundle resolution for Trash | Walk path upward to find .app directory, move entire bundle to Trash (not just binary) | 2026-02-14 |
| Cleanup SQLite connections before deletion | Call _cleanup_connections() before shutil.rmtree to prevent "database is locked" errors | 2026-02-14 |
| Native file picker for backup | Use tkinter.filedialog.asksaveasfilename for backup ZIP location - familiar OS-native experience | 2026-02-14 |
| Threading for deletion | Run delete_app_data() in background thread with polling to prevent GUI freeze during uninstall | 2026-02-14 |
| Checkbox-gated red button | Red "Uninstall" button starts disabled until "I understand" checkbox checked - prevents accidental clicks | 2026-02-14 |
| Three-step confirmation for uninstall | Path preview -> Final confirmation with checkbox -> Progress provides transparency and multiple escape hatches | 2026-02-14 |

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

Completed Phase 36 Plan 02: GUI Uninstall Dialogs

**Executed:** Complete GUI uninstall flow with dialogs and orchestration

**Key accomplishments:**
- Created job_radar/gui/uninstall_dialog.py with 4 dialog classes (413 lines):
  - BackupOfferDialog: backup offer with native file picker
  - PathPreviewDialog: scrollable path list with descriptions
  - FinalConfirmationDialog: checkbox-gated red button
  - DeletionProgressDialog: indeterminate progress during deletion
- Wired uninstall button into Settings tab with Danger Zone section
- Implemented _start_uninstall() orchestration method (156 lines):
  - Backup offer -> path preview -> final confirmation
  - Threaded deletion with progress dialog
  - Partial failure reporting with error list
  - Binary cleanup script generation for frozen apps
  - Auto-quit after completion
- Added 4 integration tests (144 lines)
- Total test suite: 566 tests, all passing with zero regressions

**Commits:**
- d1ef217 - feat(36-02): create uninstall dialog classes
- fd026bd - feat(36-02): wire uninstall button and orchestration to Settings tab

**Duration:** 213 seconds (3.55 min)

**Phase 36 Complete:** GUI uninstall feature fully delivered (PKG-01, PKG-02, PKG-03, PKG-06)

### What's Next

Phase 36 complete - Ready for next milestone phase

### Files Changed This Session

- `job_radar/gui/uninstall_dialog.py` - Created 4 dialog classes (+413 lines)
- `job_radar/gui/main_window.py` - Added Danger Zone section, uninstall button, orchestration method (+158 lines)
- `tests/test_uninstaller.py` - Added 4 integration tests (+144 lines)
- `.planning/phases/36-gui-uninstall-feature/36-02-SUMMARY.md` - Created
- `.planning/STATE.md` - Updated position, decisions, metrics

### Context for Next Session

**If continuing:** Phase 36 complete. GUI uninstall feature delivered with full backup-preview-confirm-delete-quit flow. Settings tab has red "Uninstall Job Radar" button in Danger Zone section.

**If resuming later:** Read STATE.md for current position. Phase 36 delivered complete user-facing uninstall experience with three-step confirmation, optional backup, progress feedback, and automatic quit.

---
*State initialized: 2026-02-13*
*Phase 35 Plan 01 complete - SerpAPI and Jobicy backend integration delivered*
