---
phase: 20-hero-jobs-visual-hierarchy
plan: 01
subsystem: report-generation
tags: [visual-design, ui-enhancement, accessibility, hero-jobs]
dependency_graph:
  requires:
    - phase: 19
      plan: 01
      reason: "Typography and color foundation CSS variables"
    - phase: 19
      plan: 02
      reason: "Semantic tier system (tier-strong class definition)"
  provides:
    - hero-section-rendering
    - elevated-card-styling
    - top-match-badges
    - hero-recommended-split
  affects:
    - html-report-layout
    - score-badge-presentation
    - section-organization
tech_stack:
  added: []
  patterns:
    - Multi-layer CSS box-shadows for visual elevation
    - Conditional section rendering (hero only if jobs >= 4.0)
    - Score-based job filtering and categorization (hero vs recommended)
    - Enhanced focus indicators for elevated elements
key_files:
  created: []
  modified:
    - path: job_radar/report.py
      changes: "Added hero CSS (--shadow-hero, .hero-job, .badge-label, .section-divider, enhanced focus), created _html_hero_section() function, split hero from recommended (4.0+ vs 3.5-3.9), added copyAllHeroUrls() JS function"
    - path: tests/test_report.py
      changes: "Added 10 tests for hero visual hierarchy (section existence, elevated styling, shadow CSS, badge labels, ordering, divider, focus indicators, updated heading, no-hero fallback, dark mode)"
decisions:
  - decision: "Multi-layer shadow with 3 depth levels (1px/4px/8px) for hero cards"
    rationale: "Creates perceptible depth without overwhelming visual weight, follows material design elevation principles"
    alternatives: "Single shadow (too subtle), 5-layer shadow (too heavy)"
  - decision: "Separate hero section at top of report (not mixed with recommended)"
    rationale: "Immediate visual prominence for best matches, clear information hierarchy, easier scanning"
    alternatives: "Color/border differentiation only (less prominent), sorting only (no visual distinction)"
  - decision: "Hero threshold at score >= 4.0 (not 3.8 or 4.2)"
    rationale: "Round number, maintains meaningful gap from recommended (3.5-3.9), aligns with 5.0 scale quartiles"
    alternatives: "3.8 threshold (too close to recommended), 4.2 (too exclusive, might yield zero results)"
  - decision: "Badge label 'Top Match' (not 'Hero' or 'Excellent')"
    rationale: "User-focused language, clear meaning, matches section heading terminology"
    alternatives: "'Hero' (developer jargon), 'Excellent' (subjective/vague)"
metrics:
  duration: 379s
  tasks_completed: 2
  tests_added: 10
  files_modified: 2
  commits: 2
  deviations: 1
completed: 2026-02-11
---

# Phase 20 Plan 01: Hero Jobs Visual Hierarchy Summary

**One-liner:** Hero jobs (score >= 4.0) rendered in elevated section with multi-layer shadows, "Top Match" badges, and enhanced focus indicators, separated from recommended jobs (3.5-3.9) by visual divider.

## What Was Built

Implemented visual hierarchy for top-scoring jobs through:

1. **Hero Section CSS:**
   - Multi-layer `--shadow-hero` variable (3 depth levels: 1px, 4px, 8px blur with decreasing opacity)
   - `.hero-job` class applying shadow + increased padding (1.5rem vs 1.25rem)
   - `.badge-label` for "Top Match" text (uppercase, 0.85em, letter-spacing)
   - `.section-divider` gradient separator between sections
   - Enhanced focus indicators (3px outline + 3px offset for hero cards)
   - Dark mode shadow adaptation (higher opacity: 0.3/0.2/0.15 vs 0.12/0.08/0.05)

2. **Hero Section Rendering:**
   - Created `_html_hero_section(hero_jobs, profile)` function
   - Filters jobs with `score >= 4.0` into separate `hero_jobs` list
   - Updated `recommended` filter to only include `3.5 <= score < 4.0`
   - Hero section appears BEFORE recommended section in layout
   - Section divider conditionally rendered when both sections have content
   - "Copy All Top Match URLs" button with `copyAllHeroUrls()` JS function

3. **Updated Elements:**
   - Recommended section heading: "Score >= 3.5" → "Score 3.5 - 3.9"
   - Report header stats: shows both hero count (4.0+) and recommended count (3.5+)
   - Score badges in hero section include `<span class="badge-label">Top Match</span>`
   - `copyAllRecommendedUrls()` filter updated to only capture 3.5-3.9 range

4. **Test Coverage:**
   - 10 new tests validating hero section existence, styling, ordering, divider, focus, dark mode
   - Updated `sample_scored_results` fixture: job 2 (score 3.7) set to `is_new: True` for coverage
   - All 54 report tests pass (44 original + 10 new)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test fixture missing NEW job in recommended range**
- **Found during:** Task 1 verification (test_html_report_new_badge_screen_reader_text failing)
- **Issue:** After splitting hero from recommended, fixture had no NEW jobs in the 3.5-3.9 range. Job 2 (score 3.7) was `is_new: False`, causing test assertion to fail when checking for NEW badge screen reader text in recommended section.
- **Fix:** Changed job 2 to `is_new: True` in `sample_scored_results` fixture to ensure both hero AND recommended sections have NEW badges for test coverage.
- **Files modified:** tests/test_report.py (fixture update)
- **Commit:** Included in Task 1 commit (4b7c4e7)

**2. [Rule 1 - Bug] Test stats expectation outdated after fixture change**
- **Found during:** Task 1 verification (test_report_stats_accuracy failing)
- **Issue:** After changing job 2 to `is_new: True`, test expected 2 NEW jobs but fixture now has 3.
- **Fix:** Updated test assertion from `assert stats["new"] == 2` to `assert stats["new"] == 3` with comment clarification.
- **Files modified:** tests/test_report.py (test assertion)
- **Commit:** Included in Task 1 commit (4b7c4e7)

## Key Decisions

1. **Multi-layer shadow depth:** Used 3 shadow layers (1px/4px/8px) rather than single shadow for perceptible elevation without overwhelming cards. Follows material design principles.

2. **Hero threshold at 4.0:** Round number maintains meaningful gap from recommended tier (0.5 point separation), aligns with quartile thinking on 5.0 scale. Not 3.8 (too close to recommended) or 4.2 (risk of zero results).

3. **Separate section placement:** Hero section at top (before recommended) provides immediate prominence rather than color-only differentiation. Improves scannability and information hierarchy.

4. **"Top Match" badge label:** User-focused language over developer jargon ("Hero") or vague terms ("Excellent"). Matches section heading terminology.

## Success Criteria Verification

All plan success criteria met:

- ✅ Hero jobs (>=4.0) render in separate section at top with "Top Matches" heading
- ✅ Hero cards have multi-layer box shadows (3 depth levels with decreasing opacity)
- ✅ Hero cards have increased padding (1.5rem vs standard 1.25rem)
- ✅ Score badges on hero cards display "Top Match" label alongside numeric score
- ✅ Section divider separates hero from recommended when both exist
- ✅ Recommended section heading updated to "Score 3.5 - 3.9"
- ✅ Focus indicators enhanced (3px outline + 3px offset) for hero cards
- ✅ Dark mode adapts shadow opacity (0.3/0.2/0.15 vs light 0.12/0.08/0.05)
- ✅ All existing tests continue to pass (328 total tests pass)
- ✅ 10 new hero-specific tests all pass

## Verification Results

**Code patterns verified:**
- `grep -c "hero-job" job_radar/report.py` → 8 occurrences (CSS + HTML usage)
- `grep -c "--shadow-hero" job_radar/report.py` → 3 (root, dark mode, usage)
- `grep -c "badge-label" job_radar/report.py` → 3 (CSS + HTML)
- `grep -c "section-divider" job_radar/report.py` → 3 (CSS + HTML)
- `grep -c "_html_hero_section" job_radar/report.py` → 2 (def + call)
- `grep -c "copyAllHeroUrls" job_radar/report.py` → 2 (function + button)
- `grep -c "Top Match" job_radar/report.py` → 6 (badge labels + headings)

**Test coverage:**
- All 328 tests pass (including 54 report-specific tests)
- 10 new hero tests covering: existence, styling, shadow CSS, badge labels, ordering, divider, focus, heading update, no-hero fallback, dark mode
- No test regressions

## Files Changed

**Modified:**
- `job_radar/report.py` (250 insertions, 11 deletions)
  - Added hero CSS variables and classes
  - Created `_html_hero_section()` function
  - Split hero from recommended filtering logic
  - Added `copyAllHeroUrls()` JavaScript function
  - Updated report header stats and recommended heading

- `tests/test_report.py` (267 insertions)
  - Added 10 hero visual hierarchy tests
  - Updated `sample_scored_results` fixture (job 2 is_new: True)
  - Updated `test_report_stats_accuracy` assertion (3 NEW jobs)

## Commits

1. **feat(20-01): add hero CSS and split hero section from recommended** (4b7c4e7)
   - Hero shadow CSS, .hero-job class, badge-label, section-divider
   - `_html_hero_section()` function, hero/recommended split logic
   - Updated header stats, recommended heading, copyAllHeroUrls() JS
   - Fixture updates for test coverage

2. **test(20-01): add 10 tests for hero visual hierarchy elements** (c57e6ca)
   - Tests for section existence, elevated styling, shadow CSS, badge labels
   - Tests for ordering, divider, focus, heading update, no-hero fallback, dark mode
   - All 54 report tests pass

## Performance Impact

- **CSS size:** +47 lines (hero variables, classes, media queries)
- **HTML size:** Variable (+hero section when score >= 4.0, +divider when both sections exist)
- **JavaScript size:** +23 lines (copyAllHeroUrls function)
- **Rendering:** No performance impact (CSS-only visual changes, existing DOM structure)
- **Accessibility:** Improved (enhanced focus indicators, semantic section separation)

## Next Steps

This plan completes Phase 20 Plan 01. Next:

1. **Phase 20 Plan 02 (if exists):** Continue hero visual hierarchy enhancements
2. **Phase 21:** Responsive layout for mobile/tablet (likely needs hero card stacking adaptations)
3. **Phase 22:** CSV export (include hero designation in export columns)
4. **Phase 23:** Print CSS + Lighthouse CI validation (ensure hero shadows print correctly)

## Self-Check: PASSED

**Files created:** ✅ None expected

**Files modified:** ✅ All exist and contain expected changes
- ✅ FOUND: job_radar/report.py (hero CSS, _html_hero_section, split logic)
- ✅ FOUND: tests/test_report.py (10 new hero tests)

**Commits:** ✅ All exist in git history
- ✅ FOUND: 4b7c4e7 (feat: hero CSS and section split)
- ✅ FOUND: c57e6ca (test: 10 hero visual hierarchy tests)

**Tests:** ✅ All pass
- ✅ 328 total tests pass (including 54 report tests)
- ✅ 10 new hero tests validate all requirements

**Verification commands run:**
```bash
# All tests pass
python -m pytest tests/ -x -q  # 328 passed in 14.29s

# Tier logic unchanged
python -c "from job_radar.report import _score_tier; assert _score_tier(4.2) == 'strong'"

# Code patterns verified
grep -c "hero-job" job_radar/report.py      # 8
grep -c "--shadow-hero" job_radar/report.py # 3
grep -c "badge-label" job_radar/report.py   # 3
grep -c "Top Match" job_radar/report.py     # 6
```
