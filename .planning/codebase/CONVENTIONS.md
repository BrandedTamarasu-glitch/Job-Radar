# Coding Conventions

**Analysis Date:** 2026-02-07

## Naming Patterns

**Files:**
- Lowercase with underscores: `sources.py`, `scoring.py`, `deps.py`, `cache.py`
- Public modules at package level: `job_radar/search.py`, `job_radar/report.py`
- Private/internal files follow same convention (no special prefix needed due to module-level functions)

**Functions:**
- Lowercase with underscores for all functions
- Private/internal functions prefixed with single underscore: `_colors_supported()`, `_parse_arrangement()`, `_check_dealbreakers()`
- Helper functions scoped within modules: `_clean_field()`, `_recommendation()`, `_on_fetch_progress()`

**Classes:**
- PascalCase: `JobResult`, `_Colors`
- Dataclasses for data structures: `@dataclass class JobResult` in `job_radar/sources.py` (lines 19-34)
- Minimal class usage; most functionality is module-level functions

**Variables:**
- Lowercase with underscores: `all_results`, `scored_results`, `filter_by_date`
- Module-level constants in UPPERCASE: `_MAX_TITLE = 100`, `_MAX_COMPANY = 80`, `HEADERS = {}`
- Single letter for simple loops: `for i, r in enumerate(results)`
- Underscore prefix for private module constants: `_CACHE_DIR`, `_CACHE_MAX_AGE_SECONDS`, `_TRACKER_PATH`

**Type Hints:**
- Used in function signatures for clarity: `def score_job(job, profile: dict) -> dict:`
- Common patterns: `str`, `int`, `float`, `list[T]`, `dict`, `tuple[T, ...]`
- Union types with pipe syntax: `str | None` (Python 3.10+)
- Optional types less common than union syntax

## Code Style

**Formatting:**
- 4-space indentation (PEP 8 standard)
- Line length: Generally under 100 characters
- No explicit formatter configured (relies on PEP 8)

**Linting:**
- No linting configuration detected (`pyproject.toml` has no tool sections for flake8, pylint, or ruff)
- No formal style enforcement in CI

**Comments:**
- Code-level comments explain "why" not "what"
- Example from `job_radar/sources.py` (line 45): `# Max field lengths to prevent mangled data in reports`
- Section dividers using dashes for readability:
  ```python
  # ---------------------------------------------------------------------------
  # Arrangement detection
  # ---------------------------------------------------------------------------
  ```

**Docstrings:**
- Module-level docstrings at file start: `"""Job source fetchers and URL generators."""` (`job_radar/sources.py` line 1)
- Function docstrings for public/important functions:
  ```python
  def score_job(job, profile: dict) -> dict:
      """Score a job result against a candidate profile.

      Returns a dict with overall score (1.0-5.0) and component breakdowns.
      """
  ```
- Simple one-liner docstrings common for helper functions

## Import Organization

**Order:**
1. Standard library imports: `import json`, `import logging`, `import re`
2. Third-party imports: `from bs4 import BeautifulSoup`, `import requests`
3. Local/relative imports: `from .cache import fetch_with_retry`, `from .staffing_firms import is_staffing_firm`

**Aliases:**
- Used sparingly: `import json as _json` in `job_radar/sources.py` (line 2) to avoid name collision
- Relative imports preferred over absolute: `.cache`, `.scoring`, `.tracker`

**Path Style:**
- Relative imports within package: `from .scoring import score_job`
- Modules import their logger: `log = logging.getLogger(__name__)`

## Error Handling

**Patterns:**
- Broad `except Exception as e:` blocks common in scrapers to prevent crashes:
  ```python
  try:
      soup = BeautifulSoup(body, "html.parser")
      # ... parsing logic ...
  except Exception as e:
      log.error("[Dice] Parse error: %s", e)
  ```
  Examples: `job_radar/sources.py` lines 111-182, 203-286, 429-489

- Graceful degradation: Functions return `None` on failure instead of raising:
  ```python
  def fetch_with_retry(...) -> Optional[str]:
      """Fetch a URL with retry, backoff, and optional caching.

      Returns:
          Response body text, or None on failure.
      """
  ```
  (`job_radar/cache.py` lines 47-76)

- Network errors handled with retry logic and exponential backoff in `job_radar/cache.py`

**Return Values:**
- Dataclasses for structured data: `JobResult` with `__hash__` for deduplication
- Dictionaries for complex nested returns: `{"overall": score, "components": scores, "recommendation": rec}`
- List[dict] for collections: `list[dict]` from scoring functions

## Logging

**Framework:** Python built-in `logging` module

**Patterns:**
- Per-module loggers: `log = logging.getLogger(__name__)` at module level
- Source-prefixed log messages for web scrapers: `log.error("[Dice] Parse error: %s", e)`
- Log levels used:
  - `log.debug()` for cache hits: `log.debug("Cache hit: %s", url[:80])`
  - `log.info()` for progress: `log.info("[Dice] Found %d results for '%s'", len(results), query)`
  - `log.warning()` for retries: `log.warning("Fetch attempt %d/%d failed...")`
  - `log.error()` for failures: `log.error("[Dice] Parse error: %s", e)`

- Configured in main entry point: `job_radar/search.py` lines 264-272
- Suppressed for noisy libraries:
  ```python
  logging.getLogger("urllib3").setLevel(logging.WARNING)
  logging.getLogger("requests").setLevel(logging.WARNING)
  ```

## Module Design

**Exports:**
- Modules export public functions needed by other modules
- Private functions use underscore prefix and are not imported elsewhere
- Example: `job_radar/scoring.py` exports `score_job()`, keeps helper functions private with `_` prefix

**Barrel Files:**
- Not used; imports are explicit and direct

**Module Dependencies:**
- Clear separation: `sources.py` (fetching) → `scoring.py` (analysis) → `report.py` (output)
- `search.py` is main orchestrator that imports from all modules
- Utility modules: `cache.py`, `deps.py`, `tracker.py`, `staffing_firms.py`

## Function Design

**Size:**
- Most functions 10-50 lines
- Larger functions break complex logic into steps with internal helper functions
- Example: `score_job()` in `job_radar/scoring.py` (11-72) calls multiple `_score_*` functions

**Parameters:**
- Positional args for primary data, keyword args for options
- Type hints on all public function parameters
- Example: `def fetch_with_retry(url: str, headers: dict, timeout: int = 15, ...)`

**Return Values:**
- Single consistent type per function
- Early returns for error/edge cases
- Multiple return values using tuple: `tuple[float, str]` in `_check_comp_floor()`

## Dataclasses

**JobResult:**
- Defined in `job_radar/sources.py` (lines 19-34)
- 11 fields with defaults for optional: `apply_info = ""`, `employment_type = ""`, `parse_confidence = "high"`
- Custom `__hash__` for deduplication by title+company+source

## Type Unions

**Used:**
- `str | None` for optional values (Python 3.10+): `_check_dealbreakers(...) -> str | None`
- `tuple[float, str]` for multi-return: `_check_comp_floor(...) -> tuple[float, str]`
- `list[JobResult]` for collections: `def fetch_dice(...) -> list[JobResult]`

---

*Convention analysis: 2026-02-07*
