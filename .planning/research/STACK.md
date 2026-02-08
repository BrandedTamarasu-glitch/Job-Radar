# Technology Stack: Job Radar Milestone Additions

**Project:** Job Radar — pytest test suite, fuzzy skill matching, config file support
**Researched:** 2026-02-07
**Scope:** Stack dimension only. Does not re-research existing system.
**Overall confidence:** MEDIUM (network access unavailable for version verification; recommendations based on codebase analysis + training knowledge flagged per source)

---

## Constraint Summary (from Codebase Analysis)

| Constraint | Impact |
|------------|--------|
| Python 3.10+ (not 3.11+) | `tomllib` not in stdlib until 3.11; need backport for TOML reading on 3.10 |
| Deps: requests, beautifulsoup4 only | Adding any new runtime dep requires strong justification |
| pip-based, no lock file | Version pins in pyproject.toml are loose; new deps must be stable |
| argparse for CLI | Config file must integrate with argparse without replacing it |
| Cross-platform (macOS/Linux/Windows) | No platform-specific tooling; pure Python preferred |
| `_SKILL_VARIANTS` dict in scoring.py | Fuzzy matching scoped to single module; don't need a full NLP stack |

---

## Recommended Stack

### 1. Testing: pytest

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| pytest | `>=8.0` | Test runner, fixtures, parametrize | MEDIUM |
| pytest-cov | `>=5.0` | Coverage reports (optional but useful) | MEDIUM |

**Why pytest over unittest:**

The project already has zero tests and needs to bootstrap quickly. pytest's key advantages for this codebase:

- **`tmp_path` fixture** — `tracker.py` and `cache.py` both write to `os.getcwd()` paths. `tmp_path` lets tests override those paths trivially without monkeypatching.
- **`monkeypatch` fixture** — `cache.py` calls `requests.get` directly. `monkeypatch.setattr` can swap it for a mock response without importing unittest.mock explicitly.
- **`@pytest.mark.parametrize`** — `scoring.py` has ~8 scoring functions each with multiple edge cases (salary ranges: "$120k", "$60/hr", "120000"; seniority detection: "senior", "sr.", "sr ", "lead"). Parametrize reduces boilerplate dramatically.
- **No test class required** — plain functions. The codebase is procedural (no OOP), so pytest's function-based style matches naturally.
- **`conftest.py`** — shared fixtures for `JobResult` objects and test profiles can be defined once, available to all test modules without import.

**Why not unittest:**

- No parametrize equivalent without third-party package or verbose subTest patterns
- setUp/tearDown class boilerplate adds noise for a simple CLI tool
- pytest can run unittest tests anyway — no migration cost if unittest tests were to exist

**Why not hypothesis (property-based testing):**

- Overkill for this stage. The scoring module uses bounded numeric ranges (1.0–5.0) and simple string matching. Hand-crafted test cases cover the important edge cases better than random generation.
- Can add later if scoring complexity grows.

**Test scope for this milestone:**

Per the TESTING.md analysis, the highest-value targets are pure functions with no external deps:
1. `scoring.py` — all `_score_*` functions, `_parse_salary_number`, `_check_dealbreakers`
2. `tracker.py` — `job_key`, `mark_seen`, `get_stats` (use `tmp_path` for JSON file)
3. `cache.py` — `_cache_path`, `_read_cache`/`_write_cache` (use `tmp_path`)

**Not in scope for this milestone:** scraper tests (`sources.py`) — these require HTML snapshots and add significant maintenance burden for tests that break when job boards change their HTML.

**Installation (dev dependency only — NOT a runtime dep):**

```toml
# pyproject.toml addition
[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]
```

Install with: `pip install -e ".[dev]"`

**pytest configuration in pyproject.toml:**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

---

### 2. Fuzzy Skill Matching: rapidfuzz

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| rapidfuzz | `>=3.0` | Fuzzy string matching for skill normalization | MEDIUM |

**Why rapidfuzz over alternatives:**

| Library | Status | Rationale |
|---------|--------|-----------|
| **rapidfuzz** | RECOMMENDED | Actively maintained, pure Python wheels available (no C extension required on all platforms), MIT license, drop-in replacement for fuzzywuzzy/thefuzz |
| thefuzz (formerly fuzzywuzzy) | Functional but slower | Original library; python-Levenshtein optional C extension for speed; slower than rapidfuzz without extension |
| jellyfish | AVOID | Designed for name matching (Jaro-Winkler, Soundex), not programming skill tokens |
| difflib (stdlib) | AVOID | SequenceMatcher is not tuned for short token matching; "nodejs" vs "node.js" gives poor scores because it counts punctuation as significant characters |

**Why the existing approach (`_SKILL_VARIANTS` dict) is insufficient:**

The current dict requires manually adding every variant. Known gaps per PROJECT.md: "NodeJS" vs "node.js" doesn't match. The problem space is open-ended — users add new skills to their profile JSON, and the dict doesn't cover them. Fuzzy matching solves the punctuation/casing normalization problem generically.

**Specific problem being solved:**

```python
# Current: "NodeJS" vs "node.js" — FAILS
# Current: "C#" vs "c sharp" — FAILS (no variant)
# Current: "Python3" vs "python" — FAILS
# Current: ".NET" vs ".net" vs "dotnet" — works (has variant)
```

The fix is NOT to replace `_SKILL_VARIANTS` entirely — it should remain for semantically distinct aliases (e.g., "rpa" → "robotic process automation" cannot be fuzzy-matched). The addition is a fuzzy pre-pass that handles punctuation normalization and casing before checking the variant dict.

**Recommended integration pattern:**

```python
from rapidfuzz import fuzz

def _skill_in_text(skill: str, text: str) -> bool:
    """Check if a skill appears in text, with fuzzy normalization for punctuation/casing."""
    # Existing direct match (keep for exact and word-boundary cases)
    pattern = _build_skill_pattern(skill)
    if pattern.search(text):
        return True

    # Existing variant dict (keep for semantic aliases like rpa -> robotic process automation)
    variants = _SKILL_VARIANTS.get(skill.lower(), [])
    for v in variants:
        if _build_skill_pattern(v).search(text):
            return True

    # NEW: fuzzy pass for punctuation/casing normalization
    # Only apply to tokens extracted from the text, not full text comparison
    # Use token_sort_ratio to handle word order and punctuation
    skill_normalized = _normalize_skill(skill)
    for token in _extract_skill_tokens(text):
        if fuzz.token_sort_ratio(skill_normalized, token) >= 85:
            return True

    return False
```

**Threshold guidance:** 85 for `token_sort_ratio` balances precision vs recall for short programming skill tokens. Lower values (< 80) risk false positives ("python" matching "pycharm"). Higher values (> 90) miss legitimate variations.

**Dependency classification:** runtime (not dev-only), because fuzzy matching runs during scoring which runs during every invocation.

```toml
dependencies = ["requests", "beautifulsoup4", "rapidfuzz>=3.0"]
```

**Fallback strategy:** If the team decides NOT to add rapidfuzz (to maintain zero new runtime deps), the alternative is an expanded `_SKILL_VARIANTS` dict plus a normalization preprocessing step that strips punctuation and lowercases before matching. This covers 80% of cases without a dependency but requires ongoing manual maintenance.

---

### 3. Config File: tomli (backport) + standard TOML

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| tomli | `>=2.0` | TOML parsing on Python 3.10 | MEDIUM |
| (stdlib tomllib) | Python 3.11+ | TOML parsing on Python 3.11+ | HIGH — confirmed stdlib |

**The Python version split:**

- Python 3.11+ has `tomllib` in the standard library (read-only TOML parser)
- Python 3.10 does NOT — requires `tomli` backport
- The project requires Python 3.10+, so both must be handled

**Standard pattern for pyproject.toml-based projects:**

```python
# config.py
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # backport for 3.10
    except ImportError:
        tomllib = None  # graceful degradation
```

This is the established community pattern used by pip itself and many major libraries.

**Why TOML over alternatives:**

| Format | Verdict | Rationale |
|--------|---------|-----------|
| **TOML** | RECOMMENDED | Already used by pyproject.toml; familiar to Python developers; comments supported; clean syntax for simple key-value config |
| JSON | AVOID | No comments; ugly for user-edited config files; already used for profiles |
| INI (configparser) | AVOID | stdlib, zero deps; but limited type support (everything is strings); less readable for nested config |
| YAML | AVOID | PyYAML is a heavy dependency; YAML parsing has security gotchas (arbitrary code execution via `yaml.load`); overkill |
| dotenv | AVOID | For environment secrets, not user preferences; wrong abstraction for this use case |

**Config file location strategy:**

The config file saves persistent defaults for CLI flags. It should mirror the pyproject.toml convention:

```toml
# ~/.config/job-radar/config.toml  (user-level, XDG on Linux/macOS)
# OR: ./job-radar.toml             (project-level, in working directory)
```

**Recommended lookup order (standard for CLI tools):**
1. CLI flags (highest priority — explicit always wins)
2. `./job-radar.toml` (project-level)
3. `~/.config/job-radar/config.toml` (user-level)
4. Compiled defaults (lowest priority)

**Example config schema:**

```toml
# job-radar.toml
[defaults]
min_score = 2.8
new_only = false
output = "results"
# profile is intentionally omitted — should always be explicit
```

**Integration with argparse (important detail):**

argparse does not natively support config files. The standard pattern is to load the config file first, use it to populate argparse defaults, then let CLI flags override:

```python
def load_config(config_path: str | None) -> dict:
    """Load config file if it exists, return empty dict otherwise."""
    ...

def build_effective_args(cli_args, config: dict) -> argparse.Namespace:
    """Apply config file defaults, then override with CLI flags."""
    ...
```

**Dependency classification:**

If Python 3.10 support is required: `tomli` is a runtime dependency.
If minimum is raised to Python 3.11+: zero new deps (use stdlib `tomllib`).

Given the project targets 3.10+, recommend:

```toml
dependencies = ["requests", "beautifulsoup4", "rapidfuzz>=3.0", "tomli>=2.0"]
```

With the try/except import pattern to use stdlib `tomllib` when available on 3.11+.

---

## Complete Dependency Delta

### Runtime additions to `pyproject.toml`:

```toml
[project]
dependencies = [
    "requests",
    "beautifulsoup4",
    "rapidfuzz>=3.0",
    "tomli>=2.0; python_version < '3.11'",  # not needed on 3.11+ (stdlib tomllib)
]
```

Note: The environment marker `; python_version < '3.11'` means `tomli` is only installed on Python 3.10. This is the correct PEP 508 pattern.

### Dev additions:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]
```

---

## What NOT to Use and Why

| Rejected | Category | Reason |
|----------|----------|--------|
| `hypothesis` | Testing | Overkill for bounded scoring logic at this stage |
| `tox` | Testing | Multi-env testing infrastructure; unnecessary for a single-user CLI tool |
| `mock` (standalone) | Testing | `unittest.mock` is stdlib since Python 3.3; no need for separate package |
| `fuzzywuzzy` / `thefuzz` | Fuzzy matching | Superseded by rapidfuzz; slower without optional C extension |
| `jellyfish` | Fuzzy matching | Phonetic algorithms (Soundex, Metaphone) designed for names, not code skill tokens |
| `scikit-learn` / `spacy` | Fuzzy matching | Full NLP stacks; extreme overkill for punctuation normalization |
| `click` | CLI | Replacing argparse mid-project adds risk; argparse handles this project's needs |
| `pydantic` | Config validation | Useful if config schema grows complex, but unnecessary for 3-4 simple defaults |
| `dynaconf` / `python-decouple` | Config | Framework-level config management; too heavy for 3-4 user preferences |
| `yaml` (PyYAML) | Config | Security issues with full YAML load; TOML is cleaner and already familiar |
| `ini` / `configparser` | Config | Functional but type-poor; everything is strings; requires manual casting |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Test runner | pytest | unittest | No parametrize, more boilerplate for this codebase's functional style |
| Fuzzy matching | rapidfuzz | difflib (stdlib) | SequenceMatcher poor for short skill tokens with punctuation differences |
| Config format | TOML | INI (configparser) | Type support better in TOML; already a known format in the Python ecosystem |
| TOML parser on 3.10 | tomli | manually parse | tomli is 200 lines, well-tested, and the standard solution |

---

## Version Verification Status

| Package | Version Claimed | Verified Via | Confidence |
|---------|----------------|-------------|------------|
| pytest | `>=8.0` | Training knowledge (8.x released 2024) | MEDIUM — cannot verify latest patch without network |
| pytest-cov | `>=5.0` | Training knowledge | MEDIUM |
| rapidfuzz | `>=3.0` | Training knowledge (3.x released 2023) | MEDIUM — cannot verify latest without network |
| tomli | `>=2.0` | Training knowledge (2.0 released 2022, stable) | MEDIUM |
| tomllib | stdlib in 3.11+ | Verified: [PEP 680](https://peps.python.org/pep-0680/) | HIGH |

**Action required before implementation:** Run `pip index versions pytest rapidfuzz tomli` or check PyPI to confirm latest stable versions and pin to specific releases in pyproject.toml.

---

## Sources

- Codebase analysis: `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/` (all modules)
- Existing codebase docs: `.planning/codebase/STACK.md`, `.planning/codebase/TESTING.md`
- Python 3.11 tomllib stdlib addition: PEP 680 (HIGH confidence)
- Training knowledge for package ecosystem (MEDIUM confidence, requires version verification)
- Network access unavailable during research; version pins are conservative minimums, not latest

---

*Research authored: 2026-02-07*
