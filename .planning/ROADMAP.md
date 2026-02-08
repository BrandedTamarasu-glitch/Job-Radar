# Roadmap: Job Radar

## Overview

This milestone improves the reliability and usability of Job Radar's scoring engine through three sequential deliveries: fuzzy skill normalization to close known matching gaps, config file support to eliminate repetitive CLI flag typing, and a pytest test suite to validate both new features and existing scoring logic. The build order ensures each phase is self-contained and testable, with the test suite arriving last to cover the completed state of all changes.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Fuzzy Skill Normalization** - Skill matching handles punctuation, casing, and variant differences so "NodeJS" matches "node.js"
- [ ] **Phase 2: Config File Support** - Persistent CLI defaults via JSON config file so users stop retyping the same flags
- [ ] **Phase 3: Test Suite** - pytest coverage of scoring, tracking, and both new features validates correctness

## Phase Details

### Phase 1: Fuzzy Skill Normalization
**Goal**: Users get accurate skill match scores regardless of how job listings format technology names
**Depends on**: Nothing (first phase)
**Requirements**: FUZZ-01, FUZZ-02, FUZZ-03, FUZZ-04, FUZZ-05
**Success Criteria** (what must be TRUE):
  1. A job listing containing "node.js" scores the same skill match as one containing "NodeJS" or "Node.js" when the profile lists any of these variants
  2. Short skills like "go", "r", and "c" still require word-boundary matching and do not false-positive match inside words like "going" or "programming"
  3. All existing `_SKILL_VARIANTS` entries continue to match correctly (zero regressions)
  4. New common tech variants (e.g., "postgres" / "postgresql", "k8s" / "kubernetes") are recognized without manual profile entries
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Add _normalize_skill(), wire normalized variant lookup, expand _SKILL_VARIANTS with 16 common tech entries
- [x] 01-02-PLAN.md — Fix C# boundary guard regression in _build_skill_pattern()

### Phase 2: Config File Support
**Goal**: Users can save their preferred CLI defaults once and have them apply automatically on every run
**Depends on**: Phase 1
**Requirements**: CONF-01, CONF-02, CONF-03, CONF-04, CONF-05
**Success Criteria** (what must be TRUE):
  1. User creates `~/.job-radar/config.json` with `{"min_score": 3.0, "new_only": true}` and those defaults apply without passing CLI flags
  2. Running `job-radar --min-score 2.5` with a config file containing `"min_score": 3.0` uses 2.5 (CLI always wins)
  3. Deleting or never creating a config file causes zero behavior change from today's tool
  4. Running `job-radar --config /path/to/custom.json` loads that file instead of the default location
  5. A config file with `{"unknown_key": true}` produces a clear warning message naming the unrecognized key
**Plans**: 1 plan

Plans:
- [ ] 02-01-PLAN.md — Create config.py module and integrate config loading into CLI pipeline

### Phase 3: Test Suite
**Goal**: Scoring, tracking, and both new features are validated by automated tests that catch regressions before they reach production
**Depends on**: Phase 2
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07
**Success Criteria** (what must be TRUE):
  1. `pytest` runs from the project root and all tests pass with zero failures
  2. Every `_score_*` function in scoring.py has at least one parametrized test covering a normal case and an edge case
  3. Dealbreaker detection tests verify that exact match, substring match, and case-insensitive match all correctly trigger a 0.0 score
  4. Salary parsing tests cover "$120k", "$60/hr", "$120,000", range formats, and "Not listed" without errors
  5. Tracker tests run in isolated temp directories and never touch production tracker.json
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Fuzzy Skill Normalization | 2/2 | Complete ✓ | 2026-02-07 |
| 2. Config File Support | 0/1 | Planned | - |
| 3. Test Suite | 0/0 | Not started | - |

---
*Roadmap created: 2026-02-07*
*Last updated: 2026-02-07*
