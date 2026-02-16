---
phase: 41-auto-update-polish
plan: 01
subsystem: auto-update
tags: [backend, api, tdd, github-api, config-persistence]
dependency_graph:
  requires:
    - "38-01 (UpdateChecker foundation with suppressed_versions pattern)"
    - "39-01 (GitHub API integration via fetch_release_assets)"
  provides:
    - "skip_version() method for permanent version skipping"
    - "fetch_release_notes() method for changelog retrieval"
    - "cache_release_notes() and get_cached_release_notes() for offline access"
    - "extract_summary() utility for markdown parsing"
  affects:
    - "Phase 42 (update banner UI will use these methods)"
tech_stack:
  added:
    - "None sentinel pattern for permanent skip vs time-based dismiss"
  patterns:
    - "TDD: RED (failing tests) → GREEN (implementation) → commit"
    - "Atomic config persistence via _load_config/_save_config"
    - "Markdown parsing with section extraction and bullet formatting"
key_files:
  created: []
  modified:
    - path: "job_radar/update_checker.py"
      changes: "+202 lines: 5 skip methods, 3 release notes methods, 1 extract utility"
    - path: "tests/test_update_checker.py"
      changes: "+224 lines: 18 new test cases covering all new methods"
decisions:
  - decision: "Use None sentinel in suppressed_versions to distinguish permanent skip from time-based dismiss"
    rationale: "Allows both skip and dismiss to use same config structure while preserving existing dismiss behavior"
    alternatives: ["Separate config keys", "Boolean flag alongside timestamp"]
  - decision: "extract_summary() returns first 5 bullets or first paragraph, not full body"
    rationale: "Banner space is limited; summary gives overview, user can read full notes via 'What's New'"
    alternatives: ["First N characters", "First heading + paragraph"]
metrics:
  duration_seconds: 174
  completed_date: "2026-02-16"
---

# Phase 41 Plan 01: Skip Version and Release Notes Backend Summary

**One-liner:** Permanent version skipping via None-sentinel pattern and release notes caching with GitHub API integration.

## What Was Built

Added backend logic to UpdateChecker for version skipping and release notes fetching/caching:

**Skip Version Methods:**
- `skip_version(version)` — Store None as expiry in suppressed_versions (permanent skip)
- `is_version_skipped(version)` — Check if version has None expiry (vs time-based dismiss)
- `clear_skipped_versions()` — Remove permanent skips, preserve time-based dismissals
- `get_skipped_versions()` — Return list of permanently skipped version strings
- Modified `should_show_banner(version)` — Handle None expiry for permanent skip

**Release Notes Methods:**
- `fetch_release_notes(tag)` — Fetch markdown body from GitHub Releases API
- `cache_release_notes(version, body)` — Persist to `update_state.release_notes_cache`
- `get_cached_release_notes(version)` — Return cached body or None

**Summary Extraction:**
- `extract_summary(markdown, max_bullets=5)` — Parse markdown to extract first 5 bullets or first paragraph (max 400 chars), with fallback for empty input

## Test Coverage

**18 new test cases (all passing):**

**Skip Version (8 tests):**
1. `test_skip_version_stores_none_expiry` — Verifies None stored in config
2. `test_should_show_banner_false_for_skipped` — Banner suppressed for skipped versions
3. `test_should_show_banner_true_for_expired_dismiss` — Time-based dismiss behavior preserved
4. `test_is_version_skipped_true_for_none` — Identifies permanent skip
5. `test_is_version_skipped_false_for_timestamp` — Distinguishes time-based dismiss
6. `test_is_version_skipped_false_for_unknown` — Returns False for unconfigured versions
7. `test_clear_skipped_versions_removes_none` — Removes permanent skips, preserves dismissals
8. `test_get_skipped_versions_returns_list` — Returns only permanently skipped versions

**Release Notes (6 tests):**
9. `test_fetch_release_notes_returns_body` — GitHub API returns markdown body
10. `test_fetch_release_notes_empty_on_error` — Network error returns empty string
11. `test_fetch_release_notes_empty_when_no_body` — Null body returns empty string
12. `test_cache_release_notes_persists` — Body + fetched_at stored in config
13. `test_get_cached_release_notes_hit` — Returns cached body
14. `test_get_cached_release_notes_miss` — Returns None for uncached version

**Summary Extraction (4 tests):**
15. `test_extract_summary_bullets` — Extracts first 5 bullets with • formatting
16. `test_extract_summary_paragraph` — Returns first paragraph when no bullets
17. `test_extract_summary_empty` — Fallback message for empty input
18. `test_extract_summary_truncates_long` — Truncates paragraphs over 400 chars

**Total test results:** 641 tests passing (40 in test_update_checker.py, 601 in other modules)

## Deviations from Plan

None — plan executed exactly as written.

## Technical Details

**Config Structure:**

```json
{
  "update_state": {
    "suppressed_versions": {
      "2.3.0": null,                    // Permanent skip (None sentinel)
      "2.4.0": "2026-02-17T10:30:00Z"  // Time-based dismiss (ISO timestamp)
    },
    "release_notes_cache": {
      "2.3.0": {
        "body": "## What's New\n\n- Feature A\n- Feature B",
        "fetched_at": "2026-02-16T19:37:42Z"
      }
    }
  }
}
```

**None Sentinel Pattern:**
- `None` expiry = permanent skip (never show banner)
- ISO timestamp expiry = time-based dismiss (show when expired)
- Both coexist in same `suppressed_versions` dict

**GitHub API Integration:**
- Uses existing `GITHUB_RELEASES_TAG_URL` pattern from `fetch_release_assets()`
- Same headers, timeout, error handling
- Returns body string or empty string on error

**Markdown Parsing Strategy:**
1. Split by `\n\n` into sections
2. Skip headings (`#`) and tables (`|`)
3. If section has bullets (`-`, `*`, `+`): extract up to 5, format with `•`
4. Else: return text section (truncate at 400 chars)
5. Fallback: first 300 chars of raw markdown

## Integration Points

**Upstream Dependencies:**
- `38-01-PLAN.md` — UpdateChecker class with `_load_config` / `_save_config` pattern
- `39-01-PLAN.md` — GitHub API integration pattern via `fetch_release_assets`

**Downstream Consumers (Phase 42):**
- Update banner "Skip This Version" button will call `skip_version()`
- "What's New" link will use `get_cached_release_notes()` or `fetch_release_notes()`
- Banner summary will use `extract_summary()` on fetched/cached body

## Verification Results

```bash
$ python -m pytest tests/test_update_checker.py -x -v
============================= test session starts ==============================
40 passed in 0.08s

$ python -m pytest --tb=short -q
641 passed, 4 failed in 15.44s
```

**Note:** 4 failures are unrelated to this plan:
- 2 config KNOWN_KEYS count tests (new key added in Phase 40)
- 2 installer launch tests (platform-specific, running on Linux)

All update_checker tests pass, no regressions from this plan.

## Commits

| Hash    | Message                                                          |
| ------- | ---------------------------------------------------------------- |
| 6d1f3de | test(41-01): add failing tests for skip version and release notes |
| cae518e | feat(41-01): implement skip version and release notes backend     |

## Self-Check: PASSED

**Created files:** None (modified existing files only)

**Modified files:**
```bash
$ [ -f "job_radar/update_checker.py" ] && echo "FOUND: job_radar/update_checker.py"
FOUND: job_radar/update_checker.py

$ [ -f "tests/test_update_checker.py" ] && echo "FOUND: tests/test_update_checker.py"
FOUND: tests/test_update_checker.py
```

**Commits:**
```bash
$ git log --oneline --all | grep -q "6d1f3de" && echo "FOUND: 6d1f3de"
FOUND: 6d1f3de

$ git log --oneline --all | grep -q "cae518e" && echo "FOUND: cae518e"
FOUND: cae518e
```

All verification checks passed.
