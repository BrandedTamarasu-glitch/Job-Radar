# Project Research Summary

**Project:** Job Radar — pytest test suite, fuzzy skill matching, config file support
**Domain:** Python CLI tool quality improvements (testing, matching, persistence)
**Researched:** 2026-02-07
**Confidence:** HIGH

## Executive Summary

Job Radar is an existing, working Python CLI tool for job search aggregation with a scoring engine. This milestone adds three quality improvements to an already functional codebase: a pytest test suite, fuzzy skill normalization to fix the "NodeJS" vs "node.js" matching gap, and config file support to persist default CLI flags. The project has unusually clean architecture for having zero tests — scoring is all pure functions, and tracker/cache have clear filesystem seams that can be isolated with monkeypatching. The primary challenge is not building new functionality but doing so without breaking what already works.

The recommended approach is to use pure string normalization (lowercase + strip punctuation) for skill matching rather than adding a fuzzy matching library, use JSON for config file format to avoid new runtime dependencies, and use pytest with the standard `tmp_path` + `monkeypatch` pattern to isolate filesystem-dependent tests. All three features can be implemented as additive changes — no existing module signatures need to change. The correct implementation order is: fuzzy normalization first (pure function change, zero risk), config file second (argparse integration), tests third (validates both).

The key risk is false positive skill matches introduced by normalization — specifically, short skills (2-3 characters like "go", "r", "c#") becoming ambiguous after punctuation stripping. The existing `_BOUNDARY_SKILLS` set addresses this pattern, and regression tests against the full `_SKILL_VARIANTS` dict must be written before implementing normalization to catch regressions. The second major risk is config precedence: the correct pattern is `parser.set_defaults(**config)` before `parse_args()` so CLI flags always win — any other approach silently overrides explicit user input.

## Key Findings

### Recommended Stack

The milestone requires minimal new dependencies. The codebase targets Python 3.10+ with a strict constraint against new runtime dependencies. The recommended additions are: `pytest>=8.0` and `pytest-cov>=5.0` as dev-only dependencies, and no new runtime dependencies. For config format, JSON is the correct choice because `json` is already in the standard library, already used throughout the project for profiles and tracker, and requires zero new packages. TOML (via `tomllib`) is only in stdlib from Python 3.11+, making it a liability for a 3.10-targeted tool. For fuzzy skill matching, the stated problem ("NodeJS" vs "node.js") is a punctuation and casing problem, not a semantic fuzzy matching problem — a `_normalize_skill()` function that strips `.`, `-`, spaces and lowercases resolves it without any new runtime dependency.

**Core technologies:**
- pytest `>=8.0`: test runner — parametrize, tmp_path, monkeypatch fixtures match the codebase's functional style exactly
- pytest-cov `>=5.0`: coverage reporting — dev only, validates scoring engine coverage
- No new runtime deps: json (stdlib) for config; pure string normalization for skill matching

### Expected Features

The milestone scope is fixed: three features, all table stakes for a tool expected to be reliable.

**Must have (table stakes):**
- pytest suite covering scoring.py pure functions, tracker.py key logic, cache.py read/write — this is the entire point of the milestone's test feature
- Fuzzy skill normalization for punctuation/casing variants ("NodeJS" = "node.js") — explicitly noted as a known gap in PROJECT.md
- Config file for persistent CLI defaults (`min_score`, `new_only`, `output`) — users should not retype the same flags daily

**Should have (competitive):**
- Parametrized tests covering negative cases: `_BOUNDARY_SKILLS` should NOT match as substrings in unrelated text
- Config validation on load with helpful error messages for unknown keys
- Named constant for any fuzzy threshold used: `_FUZZY_MATCH_THRESHOLD` rather than magic numbers

**Defer (v2+):**
- rapidfuzz library integration for title matching (adds dependency, requires threshold tuning)
- Profile-specific config auto-loading (`cory.json` → `cory.config.json`)
- Application tracking CLI commands (explicitly out of scope per PROJECT.md)
- Scraper tests with HTML fixture snapshots (high maintenance, ties to job board HTML structure)

### Architecture Approach

The existing codebase is a sequential pipeline: CLI args -> fetch (sources.py) -> filter -> score (scoring.py) -> track (tracker.py) -> report (report.py). All three new features slot cleanly into this pipeline without changing existing module interfaces. Fuzzy normalization lives entirely inside `scoring.py` as a preprocessing step inside `_skill_in_text()`. Config loading inserts between argparse setup and `parse_args()` using `parser.set_defaults()`. The test suite lives in a `tests/` directory mirroring `job_radar/` package structure.

**Major components:**
1. `scoring.py` — receives a `_normalize_skill()` helper and updated `_skill_in_text()` with normalization pre-pass
2. `search.py` + optional `config.py` — receives `load_config()` and `parser.set_defaults(**config)` integration
3. `tests/` (new) — `conftest.py`, `test_scoring.py`, `test_tracker.py`, `test_cache.py`, `test_sources.py`

### Critical Pitfalls

1. **Tests contaminating production tracker/cache** — `_TRACKER_PATH` and `_CACHE_DIR` are module-level constants set from `os.getcwd()`. Use `monkeypatch.setattr()` to redirect them to `tmp_path` in every tracker/cache test; never let test runs touch the production JSON files.
2. **Fuzzy normalization causing false positive skill matches** — short skills (2-3 chars) become dangerous after punctuation stripping. Keep `_BOUNDARY_SKILLS` on a word-boundary-only path regardless of normalization; apply normalization only when normalized form is longer than 2 characters.
3. **Config precedence inversion** — if config loading happens after `parser.parse_args()` completes, CLI flags get silently overridden. Use `parser.set_defaults(**config_values)` before parsing; test explicitly that `--min-score 2.5` wins over config `min_score: 3.0`.
4. **New runtime dependency for config format** — YAML or TOML both require packages not in Python 3.10 stdlib. Use JSON to stay at zero new runtime dependencies.
5. **Normalization breaking existing _SKILL_VARIANTS lookups** — if normalization transforms skill keys before dict lookup, the variant table stops working. Normalize both the query skill and the dict keys in tandem; write regression tests for all existing variants before implementing.

## Implications for Roadmap

Based on research, the three features have clear build-order dependencies and can be organized into three sequential phases:

### Phase 1: Fuzzy Skill Normalization
**Rationale:** Pure function change to `scoring.py` with zero integration risk. Self-contained, immediately verifiable, no dependencies on the other two features. Starting here protects existing matches and establishes normalization behavior before writing tests that validate it.
**Delivers:** Correct skill matching for punctuation/casing variants; `_normalize_skill()` helper; updated `_skill_in_text()`.
**Addresses:** The "NodeJS" vs "node.js" known gap from PROJECT.md.
**Avoids:** Regression via pre-implementation documentation of all existing `_SKILL_VARIANTS` entries as the test oracle baseline.

### Phase 2: Config File Support
**Rationale:** Touches `search.py`'s argument parsing — the most integration-heavy change. Getting it stable before the test suite means the test suite can cover the precedence behavior (`load_config()`, `set_defaults()`, CLI override path) in the correct final state.
**Delivers:** `~/.job-radar/config.json` (or `~/.config/job-radar/config.json`) support; persistent defaults for `min_score`, `new_only`, `output`; graceful absence handling.
**Uses:** `json` stdlib, `pathlib.Path.home()` for cross-platform path resolution.
**Implements:** Config loader component feeding into `parse_args()` via `set_defaults()`.

### Phase 3: pytest Test Suite
**Rationale:** Tests are most valuable once they have complete features to validate. Writing tests last means the suite can cover fuzzy normalization regression cases AND config precedence behavior in one pass. Tests also document correct behavior for both completed features.
**Delivers:** `tests/` directory with `conftest.py`, `test_scoring.py` (parametrized edge cases), `test_tracker.py` (tmp_path), `test_cache.py` (tmp_path), coverage reporting.
**Avoids:** Over-mocking pure logic functions; tests contaminating production files; missing `_BOUNDARY_SKILLS` negative cases.

### Phase Ordering Rationale

- Fuzzy matching first because it is the highest-value pure-function change with the lowest risk surface. No external dependencies, no CLI changes.
- Config second because it is the only feature that modifies existing CLI wiring. Resolving it before tests means tests verify the finished implementation.
- Tests last because they verify the completed state of both other features and derive test cases from the implemented normalization logic and config schema.

Note: TDD practitioners may prefer writing tests first. This is valid for the scoring unit tests (no risk). For tracker/cache tests involving monkeypatching, writing the production code first and then the tests avoids the friction of testing against module-level constants before knowing their final form.

### Research Flags

Phases with standard patterns (no additional research needed):
- **Phase 1 (Fuzzy normalization):** Pure string manipulation, well-understood Python patterns. Implement directly.
- **Phase 2 (Config file):** `argparse.set_defaults()` is standard library, documented behavior. `pathlib.Path.home()` is cross-platform stdlib. Implement directly.
- **Phase 3 (pytest suite):** pytest `tmp_path` and `monkeypatch` fixtures are core, well-documented. Implement directly.

No phase requires deeper research before implementation. All patterns are confirmed against actual source code and established Python conventions.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Versions unverifiable without network; package choices (pytest, json, no-dep normalization) are HIGH confidence decisions even if specific version pins need verification |
| Features | HIGH | Based on direct codebase inspection; three milestone features are explicitly stated in PROJECT.md |
| Architecture | HIGH | Based on direct code analysis of all modules; no inference required |
| Pitfalls | HIGH | Derived from direct code inspection of `_TRACKER_PATH`, `_CACHE_DIR` patterns, `_BOUNDARY_SKILLS` set, and `argparse` integration points |

**Overall confidence:** HIGH

### Gaps to Address

- **Exact version pins:** Run `pip index versions pytest rapidfuzz tomli` (if rapidfuzz is added later) to confirm latest stable before pinning. Minimum versions in STACK.md are conservative lower bounds, not pinned releases.
- **Python minimum version decision:** If the project raises minimum to 3.11+, TOML becomes viable for config with zero new deps. Current research assumes 3.10 stays as the floor.
- **Config file location UX:** Research used `~/.job-radar/config.json` as primary recommendation; ARCHITECTURE.md mentioned `~/.config/job-radar/config.json` as an alternative. Either works; pick one and document it. The `--config` flag override makes the default location less critical.

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/job_radar/` — all modules inspected
- Existing codebase docs: `.planning/codebase/STACK.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/CONCERNS.md`
- Python stdlib documentation: `argparse.set_defaults()`, `pathlib.Path`, `json`, `tomllib` (3.11+ only)
- PEP 680: `tomllib` added to Python 3.11 stdlib (HIGH — confirmed standard)

### Secondary (MEDIUM confidence)
- Python ecosystem training knowledge: pytest 8.x, pytest-cov 5.x, rapidfuzz 3.x version ranges
- Community pattern: `try: import tomllib except ImportError: import tomli as tomllib` — widely adopted
- pyproject.toml `[tool.pytest.ini_options]` convention

### Tertiary (LOW confidence)
- None identified; no findings require low-confidence sources for this milestone scope

---
*Research completed: 2026-02-07*
*Ready for roadmap: yes*
