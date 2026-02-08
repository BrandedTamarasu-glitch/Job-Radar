---
phase: 01-fuzzy-skill-normalization
plan: 01
subsystem: scoring
tags: [regex, normalization, skill-matching, variants, python]

# Dependency graph
requires: []
provides:
  - _normalize_skill() function that strips separator punctuation while preserving # and +
  - _SKILL_VARIANTS_NORMALIZED dict for case/punctuation-insensitive variant lookup
  - Updated _skill_in_text() using normalized key lookup
  - 16 new _SKILL_VARIANTS entries covering common tech stacks
affects:
  - 02-config-file
  - 03-test-suite

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Normalize-then-lookup: apply _normalize_skill() to lookup key only, keep variant values in original form for regex pattern building"
    - "Bidirectional alias entries: both kubernetes and k8s as keys for symmetric matching"

key-files:
  created: []
  modified:
    - job_radar/scoring.py

key-decisions:
  - "Normalize only the lookup key, not the text or variant values -- keeps _build_skill_pattern() unchanged and regex correct"
  - "Use dict comprehension at module level for _SKILL_VARIANTS_NORMALIZED -- zero runtime overhead"
  - "Preserve # and + via negative match on [.\\-\\s]+ -- C# and C++ keep meaningful punctuation"
  - "Bidirectional kubernetes/k8s entries -- both directions work without special-casing"

patterns-established:
  - "Skill normalization: strip [.\\-\\s]+ and lowercase before dict key lookup"
  - "Boundary protection: _BOUNDARY_SKILLS set + len <= 2 check in _build_skill_pattern() unchanged"

# Metrics
duration: 2min
completed: 2026-02-07
---

# Phase 1 Plan 1: Fuzzy Skill Normalization Summary

**Punctuation/casing-insensitive skill variant lookup via _normalize_skill() + normalized dict, with 16 new tech entries covering kubernetes/k8s, cloud providers, and devops tools**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-08T01:32:59Z
- **Completed:** 2026-02-08T01:34:31Z
- **Tasks:** 2 completed
- **Files modified:** 1

## Accomplishments
- Added _normalize_skill() that strips dots, hyphens, spaces while preserving # and + for C#/C++
- Wired normalized lookup into _skill_in_text() so "NodeJS" now matches "node.js" entries and vice versa
- Expanded _SKILL_VARIANTS with 16 new entries including bidirectional kubernetes/k8s, python/python3, go/golang, cloud providers, and devops tools
- All 40 verification checks pass including boundary-skill protection for "go", "r", "c"

## Task Commits

Each task was committed atomically:

1. **Task 1: Add _normalize_skill() and wire normalized variant lookup** - `2f7c426` (feat)
2. **Task 2: Expand _SKILL_VARIANTS with missing common tech variants** - `245b233` (feat)

## Files Created/Modified
- `job_radar/scoring.py` - Added _NORM_RE, _normalize_skill(), _SKILL_VARIANTS_NORMALIZED, updated _skill_in_text(), expanded _SKILL_VARIANTS with 16 entries

## Decisions Made
- Normalize only the lookup key (not the text or variant values) -- this keeps _build_skill_pattern() unchanged so all existing regex patterns remain valid
- Use module-level dict comprehension for _SKILL_VARIANTS_NORMALIZED -- computed once at import, zero per-call overhead
- Preserve # and + in normalization via negative character class [.\\-\\s]+ -- C# and C++ require these for correct variant matching
- Added both "kubernetes" and "k8s" as separate _SKILL_VARIANTS keys to enable bidirectional lookup without special-casing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Skill matching foundation is solid; _normalize_skill() available for any future use
- Phase 2 (config file) can proceed independently
- Phase 3 (test suite) will be able to test all FUZZ-01 through FUZZ-06 assertions

---
*Phase: 01-fuzzy-skill-normalization*
*Completed: 2026-02-08*
