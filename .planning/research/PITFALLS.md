# Domain Pitfalls

**Domain:** Python CLI tool quality improvements — pytest test suite, fuzzy skill matching, config file support
**Researched:** 2026-02-07
**Overall confidence:** HIGH (codebase analysis + established Python ecosystem patterns)

---

## Critical Pitfalls

Mistakes that cause rewrites or invalidate the work entirely.

---

### Pitfall 1: Testing Against Live State Instead of Isolated Fixtures

**What goes wrong:** Tests for scoring, tracking, and caching read from the real `results/tracker.json` and `.cache/` on disk. Tests pass on the developer machine and fail or produce different results on a clean checkout. The tracker accumulates state from test runs, corrupting production data.

**Why it happens:** `_TRACKER_PATH` and `_CACHE_DIR` in `tracker.py` and `cache.py` are module-level constants resolved at import time via `os.getcwd()`. Tests that call `mark_seen()` or `_load_tracker()` directly hit the production tracker file. Tests that call any fetcher hit the production cache directory.

**Consequences:** CI fails because `tracker.json` does not exist on a fresh checkout. Test runs permanently add fake job entries to the production tracker. Cache files from tests pollute the 4-hour TTL window and shadow real fetches.

**Prevention:**
- Use pytest's `tmp_path` fixture to create isolated directories for each test.
- Monkeypatch `job_radar.tracker._TRACKER_PATH` and `job_radar.cache._CACHE_DIR` to point at `tmp_path` paths before any tracker/cache test.
- Never let `tracker.py` or `cache.py` initialize path constants from `os.getcwd()` in production paths that tests can hit — refactor to accept path as parameter or read from a settable module variable that fixtures override.

**Warning signs:**
- Tests pass when run alone, fail when run in a different order.
- Running `pytest` changes the content of `results/tracker.json`.
- Test suite requires `results/` directory to pre-exist.

**Phase:** Test suite phase — must be addressed before writing any tracker or cache tests.

---

### Pitfall 2: Fuzzy Matching Increases False Positive Skill Matches

**What goes wrong:** A normalization function collapses "ba" (business analyst abbreviation) into matching "java", "scala", "data", or "database" because it strips punctuation and lowercases everything. Short skills (2-3 characters) become dangerously ambiguous after normalization.

**Why it happens:** The current `_BOUNDARY_SKILLS` set (`{"go", "r", "c", "ai", "ml", "qa", "pm", "ci", "cd", "ts", "js"}`) exists specifically because short skills false-positive in substring search. Fuzzy normalization that removes punctuation and whitespace makes this worse: "C#" → "c" matches "c" in "technical", ".NET" → "net" matches "internet", "ba" in "business analysis" variant matches against "database".

**Consequences:** Jobs score higher than they should because skill_match detects phantom matches. The scoring system becomes less trustworthy. Users see "Strong Recommend" jobs that do not actually match their skills.

**Prevention:**
- Apply normalization only when the resulting normalized form is longer than 2 characters. Keep single-character and two-character skills on a word-boundary-only path regardless of normalization.
- Test normalization against the full `_SKILL_VARIANTS` dict: for every variant, confirm that normalizing it does NOT create a string that matches any variant of a different skill.
- Add a test fixture with known-bad pairs: ("BA", "database"), ("Go", "Django"), (".NET", "network") and assert no cross-match.
- Phase: Fuzzy matching phase — write the false-positive test cases before implementing normalization.

**Warning signs:**
- Normalized form of one skill is a substring of a common English word.
- A skill with 2 or fewer characters in its normalized form.
- Any skill that, after normalization, collides with a top-20 English word (the, and, for, are, etc.).

---

### Pitfall 3: Config File Silently Overrides Without Precedence Rules

**What goes wrong:** User sets `min_score: 3.0` in config file but passes `--min-score 2.5` on the CLI for a specific run. The CLI value is ignored because config loading happens after argument parsing and overwrites the namespace. The user cannot override config via CLI for one-off runs.

**Why it happens:** The natural implementation is: parse args → load config → merge. If merge is done by simple dict update, config file wins over CLI. The correct precedence order for a CLI tool is: CLI flag > config file > hardcoded default. This is easy to implement wrong.

**Consequences:** User cannot do ad-hoc overrides without editing the config file. Trust in the tool erodes. Users stop using the config file and go back to typing all flags.

**Prevention:**
- Establish explicit precedence before writing config loading: CLI > config > default.
- After argparse produces the namespace, check each config-file key: only apply it if the corresponding argparse argument was NOT explicitly set on the command line.
- Use `argparse`'s `set_defaults()` approach: load config first, call `parser.set_defaults(**config_values)`, then parse args. This gives CLI flags natural override priority because `parse_args()` applied after defaults always wins. This is the correct implementation pattern.
- Test: run with config setting `min_score=3.0` and CLI `--min-score 2.5`; assert effective min_score is 2.5.

**Warning signs:**
- Config loading happens after `parser.parse_args()` completes.
- Any code path that does `args.min_score = config.get("min_score")` unconditionally.
- No test for "CLI value overrides config value".

**Phase:** Config file phase.

---

### Pitfall 4: Config File Format Introduces a New Runtime Dependency

**What goes wrong:** Config file is implemented in YAML or TOML, adding `pyyaml` or `tomli` as a dependency. This contradicts the explicit project constraint: "no additional runtime dependencies beyond requests/bs4". An alternative is to use Python's standard `tomllib` (Python 3.11+), but the project targets Python 3.10+, so `tomllib` is not available.

**Why it happens:** TOML/YAML feel ergonomic for config. `tomllib` is standard library in Python 3.11+ but NOT in 3.10. If the project targets 3.10 (per `pyproject.toml`), using `tomllib` without a compatibility shim silently breaks for 3.10 users.

**Consequences:** Introducing `pyyaml` or `tomli` violates the minimal-dependency constraint. Using `tomllib` without testing on Python 3.10 causes `ModuleNotFoundError` on valid installs.

**Prevention:**
- Use JSON for the config file format. `json` is standard library, zero new dependencies, already used throughout the codebase for profiles and tracker. The only downside is no comment support, which is acceptable for a few CLI default flags.
- Alternatively, if TOML is required, use a try/except import: `try: import tomllib except ImportError: import tomli as tomllib` and add `tomli` as an optional dependency with `python_requires` guard. But JSON avoids this complexity entirely.
- Config file format recommendation: JSON, named `~/.job-radar/config.json` or `.job-radarrc.json` in the project root.

**Warning signs:**
- Any import of `yaml`, `toml`, `tomllib`, `tomli` in the config loading module.
- No test that runs on Python 3.10.
- `pyproject.toml` dependencies list grows beyond requests/bs4.

**Phase:** Config file phase — choose format before writing any code.

---

## Moderate Pitfalls

Mistakes that cause delays or technical debt.

---

### Pitfall 5: Tests That Mock Too Much and Test Nothing Real

**What goes wrong:** Every test mocks every dependency so aggressively that the test is just asserting that mock returns what you told it to return. Scoring tests mock `_skill_in_text()` so `_score_skill_match()` tests never exercise real skill matching logic. The test suite shows 85% coverage but catches zero bugs.

**Why it happens:** It feels safe to mock everything. Mocking is necessary for network calls but should not extend to pure logic functions within the same module.

**Consequences:** Bugs in `_skill_in_text()`, `_build_skill_pattern()`, `_check_dealbreakers()` go undetected. The test suite becomes maintenance burden with no safety value.

**Prevention:**
- Establish a clear boundary: mock at the network edge (`fetch_with_retry`) and filesystem edge (tracker/cache paths), never inside pure-logic functions.
- `score_job()` tests should use real `JobResult` objects and real profile dicts, not mocks. The only mock needed is if `score_job` calls external I/O, which it does not.
- Run coverage with `--cov-branch` and inspect which branches are actually exercised in scoring tests.

**Warning signs:**
- Any `mock.patch` on a function in `scoring.py`.
- Tests that import `MagicMock` for non-I/O functions.
- A test that only asserts the mock was called, not the return value.

**Phase:** Test suite phase.

---

### Pitfall 6: Fuzzy Normalization Changes Existing Behavior for Already-Working Skills

**What goes wrong:** Skills like "PostgreSQL" currently match correctly because "postgres" is in `_SKILL_VARIANTS["postgresql"]`. Adding fuzzy normalization that strips punctuation and lowercases changes the matching path and could accidentally skip the variant table. Existing matches break silently.

**Why it happens:** Normalization is added as a preprocessing step that transforms the skill string before it reaches `_skill_in_text()`. If normalization converts "postgresql" → "postgresql" (no change) but the variant lookup is keyed on the original form, the dict lookup fails for normalized forms.

**Consequences:** Skills that worked before normalization now miss matches. Users see score regression without understanding why. Hard to debug because the variant table is still correct.

**Prevention:**
- Normalize both the key and the lookup. When normalizing skill strings, also normalize all keys in `_SKILL_VARIANTS` so the dict lookup still works.
- Write regression tests for all existing `_SKILL_VARIANTS` entries BEFORE implementing normalization. Run these tests after normalization is added. Any failure indicates a regression.
- The normalization function should be pure and tested in isolation with a table of input → expected output pairs.

**Warning signs:**
- Skill match scores drop for jobs that were previously matching well.
- `_SKILL_VARIANTS` dict lookup returns empty list for a skill that has known variants.
- Normalization is applied to the skill key but not to `_SKILL_VARIANTS` dict keys.

**Phase:** Fuzzy matching phase.

---

### Pitfall 7: Config File Path Uses os.getcwd() Like Tracker and Cache

**What goes wrong:** Config file is looked up in the current working directory: `config.json` at `os.getcwd() + "/config.json"`. When the user runs `job-radar` from different directories (home directory, project directory, desktop), the config file is not found and defaults silently apply.

**Why it happens:** The existing codebase already has this pattern for `_TRACKER_PATH` and `_CACHE_DIR`. It is tempting to follow the same pattern.

**Consequences:** Config file only works when run from the project root. Cross-platform inconsistency (macOS/Linux users likely run from home; Windows users from anywhere). User sets up config once, never sees it take effect because they run from a different directory.

**Prevention:**
- Use a user-level config directory: `~/.job-radar/config.json` or platform-aware via `pathlib.Path.home() / ".job-radar" / "config.json"`.
- Search in order: (1) path from `--config` CLI flag, (2) `~/.job-radar/config.json`, (3) no config, use defaults.
- `pathlib.Path` is standard library and handles cross-platform path separator differences correctly.

**Warning signs:**
- Config loading uses `os.getcwd()` or a relative path.
- No `--config` override flag to specify a custom config location.
- Config file tests require running from a specific directory.

**Phase:** Config file phase.

---

### Pitfall 8: Broad except Exception Blocks Hide Test Failures

**What goes wrong:** The existing `except Exception` pattern in `sources.py` is preserved when testing scrapers. A test passes HTML fixture data to `fetch_dice()`, the BeautifulSoup parse raises an unexpected AttributeError, it is swallowed by the broad except, and the test asserts `len(results) == 0` which passes — but only because parsing silently failed.

**Why it happens:** The broad exception handling was designed for production resilience (do not crash the CLI), but in test context it turns real failures into false passes.

**Consequences:** Tests appear green when the parsing code has a bug. The broad exception pattern makes it harder to diagnose failures introduced during refactoring.

**Prevention:**
- In test fixtures for parsers, temporarily set `log.setLevel(logging.ERROR)` and assert that no error was logged during parsing. Better: refactor parsers to raise specific exceptions that the top-level orchestrator catches, so tests can assert on specific exception types.
- As part of addressing the broad-except tech debt (already documented in CONCERNS.md), replace `except Exception` with `except (json.JSONDecodeError, AttributeError, KeyError)` in parser-specific locations. This lets unexpected exceptions propagate to test output.
- At minimum, add an assertion in scraper tests: mock out `log.error` and assert it was NOT called.

**Warning signs:**
- Scraper test returns 0 results and the test asserts `== 0` without checking why.
- No assertion about parse confidence or error log calls in scraper tests.
- All scraper tests pass even when the HTML fixture is completely empty.

**Phase:** Test suite phase (scraper tests specifically).

---

### Pitfall 9: Parametrize Tests Without Covering Edge Cases in Skill Matching

**What goes wrong:** `@pytest.mark.parametrize` tests for skill matching only cover happy-path cases: "Python" matches "Python engineer". Edge cases specific to this codebase are never tested: skills with special characters ("C#", ".NET", "node.js"), skills with word-boundary collisions ("go" in "Django"), the `_BOUNDARY_SKILLS` set behavior, and the salary parsing edge cases documented in CONCERNS.md.

**Why it happens:** It is easy to write 5 parametrize cases of "skill X matches job description Y" and call it done. The edge cases require understanding the specific failure modes of the regex/variant system.

**Consequences:** The skill matching system's most fragile parts (short skills, punctuation-containing skills) have no test coverage. Regressions during fuzzy matching implementation go undetected.

**Prevention:**
- Derive parametrize cases from the existing `_SKILL_VARIANTS` dict and `_BOUNDARY_SKILLS` set. For each skill in `_BOUNDARY_SKILLS`, write a test that confirms it does NOT match as a substring in unrelated text.
- Add negative test cases: "go" should NOT match "Django framework", "r" should NOT match "React", "ts" should NOT match "typescript" when "ts " (space-bounded) is the variant.
- Use the known bugs listed in CONCERNS.md as a test derivation checklist: each bug listed is a test case to write.

**Warning signs:**
- All parametrize cases are positive (skill present in text → True).
- No tests for `_BOUNDARY_SKILLS` behavior.
- No tests for skills containing `.`, `#`, or `/`.

**Phase:** Test suite phase.

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

---

### Pitfall 10: Config File Key Names Differ From CLI Flag Names

**What goes wrong:** CLI flag is `--min-score` (hyphenated) but config file key is `min_score` (underscore) or `minScore` (camelCase). The merge logic needs translation between naming conventions, creating a bug surface.

**Prevention:**
- Use argparse's convention: config file keys match the `dest` names from argparse (underscore form: `min_score`, `new_only`, `no_cache`). Document this in the config file schema/README.
- Write a mapping table in the config loader: `CLI_TO_CONFIG_KEY = {"min-score": "min_score", ...}` if needed, but prefer argparse dest names to avoid the mapping entirely.

**Phase:** Config file phase.

---

### Pitfall 11: Test Directory Structure Does Not Match Module Structure

**What goes wrong:** Tests are placed in a flat `tests/` directory without substructure. When there are 40+ test functions across scoring, sources, cache, tracker, and config, finding related tests becomes slow. Test module names like `test_functions.py` do not indicate what they cover.

**Prevention:**
- Mirror the module structure: `tests/test_scoring.py`, `tests/test_cache.py`, `tests/test_tracker.py`, `tests/test_sources.py`, `tests/test_config.py`.
- Add a `tests/fixtures/` subdirectory for HTML snapshots (Dice, HN Hiring, RemoteOK HTML fixture files).
- Add `tests/conftest.py` for shared fixtures (profile dict, sample JobResult, tmp_path wrappers).

**Phase:** Test suite phase — establish structure before writing tests.

---

### Pitfall 12: Fuzzy Threshold Is Hardcoded Without Tunability

**What goes wrong:** If rapidfuzz or a custom similarity threshold is used (e.g., match if score >= 80), the threshold is hardcoded as a magic number. Too high: misses legitimate matches. Too low: false positives. No way to tune without code changes.

**Prevention:**
- Even if the initial threshold is hardcoded, define it as a named constant: `_FUZZY_MATCH_THRESHOLD = 80`. Document why this value was chosen.
- Ideally expose it as a profile-level or config-level setting so power users can tune it.
- Note: For this project's minimal-dependency constraint, a custom normalization approach (strip punctuation, lowercase, then exact match against expanded variant set) is preferable to adding a fuzzy matching library. This eliminates the threshold problem entirely.

**Phase:** Fuzzy matching phase.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| pytest test suite | Tests modify production tracker.json | Monkeypatch _TRACKER_PATH to tmp_path in every tracker test |
| pytest test suite | Broad except swallows real test failures | Assert log.error not called in parser tests |
| pytest test suite | Over-mocking pure logic functions | Mock only at network/filesystem boundary |
| pytest test suite | Missing edge cases for short/special-char skills | Derive parametrize cases from _BOUNDARY_SKILLS and _SKILL_VARIANTS |
| Fuzzy skill matching | False positives for short normalized forms | Keep word-boundary-only path for skills <= 2 chars after normalization |
| Fuzzy skill matching | Regression in existing variant matches | Write regression tests against full _SKILL_VARIANTS before implementing |
| Fuzzy skill matching | New library dependency | Prefer normalization (punctuation strip + lowercase) over fuzzy library |
| Config file | CLI value silently lost when config loaded | Use parser.set_defaults() pattern so CLI args always win |
| Config file | Config path not found in different working dirs | Use ~/.job-radar/config.json via pathlib.Path.home() |
| Config file | Format requires new dependency | Use JSON (standard library, already used everywhere) |
| Config file | Key name translation bugs | Use argparse dest names as config keys (underscore form) |

---

## Sources

- Codebase analysis: `/job_radar/scoring.py`, `/job_radar/sources.py`, `/job_radar/tracker.py`, `/job_radar/cache.py`, `/job_radar/search.py` (HIGH confidence — direct code inspection)
- Existing concern documentation: `/.planning/codebase/CONCERNS.md`, `/.planning/codebase/TESTING.md` (HIGH confidence — same codebase)
- Python standard library behavior: `argparse`, `json`, `pathlib`, `tomllib` availability (HIGH confidence — standard library documentation)
- Pytest fixture/monkeypatch patterns: `tmp_path`, `monkeypatch` (HIGH confidence — established pytest ecosystem patterns)
- Note: WebSearch and WebFetch were unavailable during this research session. All findings derive from direct codebase inspection and established Python/pytest patterns known with high confidence from the library ecosystem.
