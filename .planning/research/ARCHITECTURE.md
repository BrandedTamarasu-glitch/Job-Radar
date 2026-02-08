# Architecture Patterns

**Domain:** Python CLI tool — adding pytest test suite, fuzzy skill matching, config file support
**Researched:** 2026-02-07
**Confidence:** HIGH (based on direct codebase analysis + established Python patterns)

---

## Existing Architecture

The codebase is a sequential pipeline driven by `search.py:main()`:

```
CLI args (argparse)
      |
      v
[fetch]   sources.py → ThreadPoolExecutor → JobResult dataclasses
      |
      v
[filter]  search.py → filter_by_date()
      |
      v
[score]   scoring.py → score_job() → score dicts
      |
      v
[track]   tracker.py → mark_seen() → annotates is_new flag
      |
      v
[report]  report.py → generate_report() → Markdown file
```

**Data contract:** `JobResult` dataclass (defined in `sources.py`) is the single inter-module object. All downstream modules receive it.

**I/O boundaries:**
- `sources.py`: HTTP out, `JobResult` in
- `cache.py`: filesystem read/write (`.cache/` relative to `os.getcwd()`)
- `tracker.py`: filesystem read/write (`results/tracker.json` relative to `os.getcwd()`)
- `report.py`: filesystem write (Markdown files)
- `scoring.py`: **pure functions only** — no I/O, no side effects

---

## Component Boundaries for the Three New Features

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `tests/` directory | pytest test suite — unit + integration tests | imports from `job_radar.*` |
| `scoring.py` fuzzy normalizer | normalize skill strings before matching | internal to `scoring.py` |
| `config.py` (new) or config loader in `search.py` | load config file, merge with argparse defaults | `search.py:parse_args()` |

### Where Each Feature Lives

**Fuzzy skill matching** lives entirely inside `scoring.py`. The change is confined to:
- A new `_normalize_skill(s: str) -> str` helper (strip punctuation, lowercase, collapse spaces)
- An updated `_skill_in_text()` that calls `_normalize_skill` on both the skill and the target text before matching
- No new external dependencies required — `difflib.SequenceMatcher` (stdlib) or pure string normalization handles the "NodeJS" vs "node.js" case without a fuzzy library

**Config file support** introduces a new loading step between `parse_args()` and the main pipeline. It feeds into argparse's `set_defaults()`:
```
config file (JSON or TOML)
      |
      v
load_config() → dict of defaults
      |
      v
parser.set_defaults(**config_defaults)  ← before parse_args() returns
      |
      v
CLI args (override config values)
```

The config loader can live in `search.py` itself (it's simple) or in a new `config.py` module if it grows. Config file path should be discoverable: look for `~/.config/job-radar/config.json` (user-level) and `./job-radar.json` or `./job-radar.toml` (project-level).

**pytest test suite** lives in a `tests/` directory at the project root, mirroring the `job_radar/` package:
```
tests/
  conftest.py          ← shared fixtures (sample profiles, JobResult factories)
  test_scoring.py      ← unit tests for scoring.py pure functions
  test_cache.py        ← filesystem tests using tmp_path fixture
  test_tracker.py      ← filesystem tests using tmp_path fixture
  test_sources.py      ← HTTP mocking with unittest.mock.patch
```

---

## Data Flow

### Fuzzy Matching Data Flow

```
profile["core_skills"] list
      |
      v
_normalize_skill(skill)  ← new step
      |
      v
job text (title + description + company) string
      |
      v
_normalize_skill(job_text)  ← new step
      |
      v
_skill_in_text() → bool  ← existing logic unchanged
```

Normalization happens on both sides of the comparison. The `_SKILL_VARIANTS` dict remains as the explicit alias table for cases normalization alone cannot handle (e.g., "RPA" → "Robotic Process Automation").

### Config File Data Flow

```
~/.config/job-radar/config.json  (user defaults)
./job-radar.json  (project overrides)
      |
      v
load_config() → merged dict
      |
      v
parser.set_defaults(**merged_dict)  ← inside parse_args()
      |
      v
sys.argv overrides  ← CLI flags always win
      |
      v
args namespace  ← rest of main() unchanged
```

### Test Data Flow

```
conftest.py fixtures
  sample_profile: dict  ← minimal valid profile
  make_job(title, desc, ...): JobResult  ← factory function
  tmp_tracker_path: Path  ← redirects tracker to tmp_path
  tmp_cache_dir: Path  ← redirects cache to tmp_path
      |
      v
test functions import and call module functions directly
      |
      v
assert expected outputs
```

---

## Patterns to Follow

### Pattern 1: Pure Function Isolation for Testability

`scoring.py` has no I/O. Every scoring function takes data in, returns data out. This means tests for scoring require zero mocking:

```python
def test_skill_match_nodejs_normalization():
    job = make_job(description="Experience with Node.js required")
    profile = {"core_skills": ["nodejs"]}
    result = score_job(job, profile)
    assert result["components"]["skill_match"]["matched_core"] == ["nodejs"]
```

Extend this pattern: keep `_normalize_skill()` as a pure function so it can be tested in isolation before integration into `_skill_in_text()`.

### Pattern 2: tmp_path for Filesystem-Dependent Modules

`cache.py` and `tracker.py` use module-level path constants derived from `os.getcwd()`. Tests must redirect these paths to avoid writing to the real project directory:

```python
# conftest.py
@pytest.fixture(autouse=True)
def redirect_tracker(tmp_path, monkeypatch):
    monkeypatch.setattr("job_radar.tracker._TRACKER_PATH",
                        str(tmp_path / "tracker.json"))
```

This is the standard pytest approach — `monkeypatch` is the correct tool, not global mocking.

### Pattern 3: argparse + set_defaults for Config Merging

The standard Python pattern for config files that don't break existing CLI flags:

```python
def parse_args():
    parser = argparse.ArgumentParser(...)
    # ... add_argument() calls unchanged ...

    # Load config and inject as defaults
    config = load_config()  # returns {} if no config file found
    if config:
        parser.set_defaults(**config)

    return parser.parse_args()
```

CLI flags passed explicitly always override `set_defaults()` values. This is documented argparse behavior — no special handling needed.

### Pattern 4: JSON over TOML for Config (Given 3.10 Constraint)

The project requires `>=3.10`. `tomllib` was added to stdlib in 3.11. The environment is 3.14 but `requires-python = ">=3.10"` means distributable users on 3.10 would need `tomli` (external dep).

Given the project already uses JSON everywhere (profiles, tracker, cache) and has a constraint against adding runtime dependencies, JSON is the correct config format. If the minimum Python requirement is bumped to 3.11+, TOML becomes viable with no new dependencies.

Config file schema example:
```json
{
  "min_score": 3.0,
  "new_only": true,
  "output": "~/job-search/results"
}
```

Only keys that map to argparse flags should be supported — the config is a "saved defaults" mechanism, not a full settings system.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Mocking os.getcwd() Globally

`cache.py` and `tracker.py` read `os.getcwd()` at module import time to set `_CACHE_DIR` and `_TRACKER_PATH`. Mocking `os.getcwd()` globally during tests is fragile because it affects the entire process.

**Instead:** Use `monkeypatch.setattr()` on the specific module-level variables (`job_radar.cache._CACHE_DIR`, `job_radar.tracker._TRACKER_PATH`) after the module is imported. This is surgical and doesn't affect other modules.

### Anti-Pattern 2: External Fuzzy Library for Simple Normalization

`rapidfuzz` or `thefuzz` are powerful but overkill for this use case. The actual problem is:
- "NodeJS" should match "node.js" → solved by stripping punctuation and lowercasing
- "Python" should match "python3" → solved by checking if the skill is a prefix of or contained in the text

True fuzzy matching (Levenshtein distance) would cause false positives: "Java" would partially match "JavaScript." The existing `_BOUNDARY_SKILLS` set exists specifically to prevent this kind of bleed. Stay with deterministic normalization.

**Instead:** A normalization function that removes `.`, `-`, spaces and lowercases is sufficient. Explicit variants in `_SKILL_VARIANTS` handle the remainder.

### Anti-Pattern 3: Config File Replacing CLI Flags

Config file should only provide *defaults*, never override explicit CLI flags. If both specify `min_score`, CLI wins.

**Instead:** Use argparse's `set_defaults()` pattern — it exists precisely for this purpose.

### Anti-Pattern 4: Test Files Inside the Package

Tests should be in `tests/` at the project root, not inside `job_radar/`. This keeps the installed package clean and follows Python packaging conventions.

---

## Build Order

Dependencies between the three features dictate this order:

```
1. Fuzzy skill normalization (scoring.py)
      ↓ no dependencies on 2 or 3

2. Config file support (search.py + config loader)
      ↓ no dependency on 1 or 3, but good to have before

3. pytest test suite (tests/)
      ↓ depends on 1 and 2 being stable to test them
```

**Rationale:**

- **Fuzzy matching first** because it's a self-contained change to a pure-function module. Zero risk of breaking CLI or config. Tests for it can be written immediately after as a verification step.

- **Config file second** because it touches `search.py`'s argument parsing. Getting it stable before the test suite means the test suite can cover config loading behavior (default merging, CLI override, missing file graceful fallback).

- **Tests last** because they test the completed state of both fuzzy matching and config. Writing tests before the features are implemented is valid (TDD), but the test suite as a whole is most useful once it has something to cover.

**Within the test suite, write tests in this order:**
1. `test_scoring.py` — pure functions, no fixtures needed beyond sample data
2. `test_cache.py` — requires `tmp_path` monkeypatching
3. `test_tracker.py` — requires `tmp_path` monkeypatching
4. `test_sources.py` — requires HTTP mocking (most complex)

---

## pyproject.toml Integration Points

The existing `pyproject.toml` is the right place for both pytest configuration and optional dev dependencies:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"

[project.optional-dependencies]
dev = ["pytest>=7.0"]
```

This avoids creating a separate `pytest.ini` or `setup.cfg` and keeps all configuration in one file.

---

## Sources

- Direct codebase analysis: `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/job_radar/`
- Python argparse documentation (stdlib pattern for `set_defaults()`)
- Python pytest documentation (tmp_path, monkeypatch fixtures)
- pyproject.toml PEP 517/518 specification for `[tool.*]` sections
- Python 3.11 release notes (`tomllib` added to stdlib)
- Confidence: HIGH — all patterns verified against actual source code and stdlib documentation
