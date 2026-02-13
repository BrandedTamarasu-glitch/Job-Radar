---
status: complete
phase: 33-scoring-configuration-backend
source: 33-01-SUMMARY.md, 33-02-SUMMARY.md, 33-03-SUMMARY.md
started: 2026-02-13T23:15:00Z
updated: 2026-02-13T23:25:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Existing profiles auto-migrate to v2
expected: Run `job-radar --view-profile` with an existing v1 profile. Profile loads without errors, displays normally. A backup file is created in the data directory. Profile now contains schema_version: 2.
result: pass

### 2. Default scoring weights match previous behavior
expected: Run a job search with an existing profile (no custom weights configured). Scores should be identical to previous runs — no score changes after the migration. The scoring engine uses DEFAULT_SCORING_WEIGHTS as fallback.
result: pass

### 3. Staffing preference defaults to neutral
expected: After migration, staffing firm listings should receive no special boost or penalty. Previously staffing firms got a +4.5 boost — that old behavior should be gone. Staffing firm jobs should score based purely on their match quality.
result: pass

### 4. Wizard asks staffing preference question
expected: Run `job-radar` as a new user (or delete profile to trigger wizard). After entering basic profile info and dealbreakers, the wizard asks "How should staffing/recruiting firms be scored?" with three choices: Neutral, Boost, and Penalize. Each choice includes a parenthetical explanation.
result: pass

### 5. Wizard offers optional weight customization
expected: After the staffing preference question, the wizard asks "Customize scoring component weights?" defaulting to No. If you select No, default weights are used. If you select Yes, it prompts for 6 weight values that must sum to 1.0.
result: pass

### 6. New profile includes v2 schema fields
expected: After completing the wizard, check the saved profile.json. It should contain `scoring_weights` (object with 6 components summing to ~1.0), `staffing_preference` (one of boost/neutral/penalize), and `schema_version: 2`.
result: pass

### 7. Scoring with custom weights changes results
expected: Edit profile.json to set a custom scoring_weights (e.g., skill_match: 0.50, others reduced). Run a search. Jobs with strong skill matches should score noticeably higher than before. The weights are actually being used by the scoring engine.
result: pass

### 8. Staffing boost/penalize adjustments work
expected: Set staffing_preference to "boost" in profile.json. Run a search. Any staffing firm listings should score ~0.5 points higher than their base score (capped at 5.0). Set to "penalize" — staffing firms should score ~1.0 point lower (floored at 1.0).
result: pass

### 9. Full test suite passes
expected: Run `pytest tests/` — all 509 tests pass with zero failures, zero errors. No hanging tests or excessive memory usage.
result: pass

## Summary

total: 9
passed: 9
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
