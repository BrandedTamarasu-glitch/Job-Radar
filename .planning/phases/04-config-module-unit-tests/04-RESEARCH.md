# Phase 4: Config Module Unit Tests - Research

**Researched:** 2026-02-09
**Domain:** pytest unit testing for JSON config file loading with edge case validation
**Confidence:** HIGH

## Summary

Phase 4 implements comprehensive unit tests for the `config.py` module, closing tech debt from the v1.0 milestone audit. The config module (67 lines) handles JSON config file loading with graceful error handling for missing files, invalid JSON, and unknown keys. The research identifies proven pytest patterns from the existing test suite (test_scoring.py, test_tracker.py) and official documentation.

The standard approach uses pytest 9.0.2 (already installed) with parametrized test cases, tmp_path for file isolation, and capsys for stderr validation. The existing codebase already follows these patterns - Phase 4 extends them to the untested config module.

**Primary recommendation:** Use pytest.mark.parametrize with descriptive IDs for all edge cases, tmp_path for isolated file operations, and capsys for validating stderr warnings. Follow established patterns from test_tracker.py for file-based testing.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test framework | Industry standard, already in use (Phases 1-3) |
| unittest.mock | stdlib | Mocking for isolation | Python standard library, no external deps |
| pathlib | stdlib | Path manipulation | Modern Python path API, matches config.py |
| json | stdlib | JSON parsing | Python standard library |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| capsys | pytest built-in | Capture stderr output | Testing warning messages |
| tmp_path | pytest built-in | Temporary file testing | File I/O isolation |
| parametrize | pytest built-in | Data-driven tests | Multiple input/output scenarios |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tmp_path | tmpdir (legacy) | tmp_path uses pathlib.Path (modern), tmpdir uses py.path.local (deprecated) |
| capsys | capfd | capsys captures at sys.stdout/stderr level (sufficient); capfd captures at file descriptor level (overkill for this) |
| unittest.mock.patch | monkeypatch | patch is familiar from test_tracker.py (consistency); monkeypatch is pytest-native (slight API differences) |

**Installation:**
Already installed - no new dependencies required.

## Architecture Patterns

### Recommended Test File Structure

```python
tests/
├── conftest.py              # Shared fixtures (already exists)
├── test_scoring.py          # Scoring tests (already exists)
├── test_tracker.py          # Tracker tests (already exists)
└── test_config.py           # NEW - Config tests (this phase)
```

### Pattern 1: Parametrized Edge Cases

**What:** Single test function with multiple input scenarios via @pytest.mark.parametrize
**When to use:** Testing the same logic with different inputs (missing file, invalid JSON, unknown keys)
**Example:**

```python
# Source: https://docs.pytest.org/en/stable/how-to/parametrize.html
@pytest.mark.parametrize("content,expected", [
    ('{"min_score": 3.0}', {"min_score": 3.0}),
    ('{"unknown_key": "value"}', {}),  # filtered out
    ('invalid json', {}),  # JSONDecodeError -> {}
], ids=[
    "valid_config",
    "unknown_key_filtered",
    "invalid_json_returns_empty",
])
def test_load_config_scenarios(tmp_path, capsys, content, expected):
    config_file = tmp_path / "config.json"
    config_file.write_text(content)
    result = load_config(str(config_file))
    assert result == expected
```

### Pattern 2: tmp_path for File Isolation

**What:** Use tmp_path fixture to create isolated temporary directories for each test
**When to use:** Any test that reads/writes files (prevents cross-test contamination)
**Example:**

```python
# Source: https://docs.pytest.org/en/stable/how-to/tmp_path.html
def test_load_config_missing_file(tmp_path):
    """Test load_config() with missing file returns {} without errors."""
    nonexistent = tmp_path / "nonexistent.json"
    result = load_config(str(nonexistent))
    assert result == {}
```

### Pattern 3: capsys for stderr Validation

**What:** Use capsys fixture to capture and assert on stderr output
**When to use:** Testing warning messages (config module sends warnings to stderr per decision [02-01])
**Example:**

```python
# Source: https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html
def test_load_config_warns_on_unknown_keys(tmp_path, capsys):
    """Test load_config() warns to stderr for unknown keys."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"unknown_key": "value"}')
    load_config(str(config_file))

    captured = capsys.readouterr()
    assert "Warning: Unrecognized config key: 'unknown_key'" in captured.err
```

### Pattern 4: Path Expansion Testing

**What:** Test DEFAULT_CONFIG_PATH expands ~ to user home directory
**When to use:** Validating tilde expansion in paths
**Example:**

```python
# Source: https://docs.python.org/3/library/pathlib.html
def test_default_config_path_expands_tilde():
    """Test DEFAULT_CONFIG_PATH expands ~ correctly to user home directory."""
    from pathlib import Path
    expanded = DEFAULT_CONFIG_PATH.expanduser()
    home = Path.home()
    assert str(expanded).startswith(str(home))
    assert "~" not in str(expanded)
```

### Anti-Patterns to Avoid

- **Testing implementation details:** Don't test internal dict lookups - test observable behavior (return values, stderr output)
- **Hardcoding home directory:** Don't use `/Users/username` in tests - use `Path.home()` for portability
- **Forgetting capsys:** When testing stderr warnings, always use capsys to verify the warning was actually printed
- **Mixing test concerns:** Each test should verify one specific edge case (parametrize handles multiple cases cleanly)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Temporary files | Manual tempfile.mkdtemp() + cleanup | pytest tmp_path fixture | Automatic cleanup, unique per test, retains last 3 runs for debugging |
| Output capture | Redirecting sys.stderr with contextlib | pytest capsys fixture | Built-in, thread-safe, cleaner API |
| Test data variations | Copy-paste test functions | pytest.mark.parametrize | Reduces duplication, readable IDs, easier to add cases |
| Path mocking | String manipulation for ~ expansion | Path.expanduser() + Path.home() | Cross-platform, handles edge cases (missing HOME var) |

**Key insight:** pytest's built-in fixtures (tmp_path, capsys) handle cleanup, isolation, and edge cases that manual implementations miss. The existing test suite (Phases 1-3) already uses these patterns successfully.

## Common Pitfalls

### Pitfall 1: Not Isolating File Tests

**What goes wrong:** Tests share the same config file path, causing failures when run in parallel or in different orders
**Why it happens:** Hardcoding paths like `~/.job-radar/config.json` in tests
**How to avoid:** Use tmp_path to create unique temporary directories for each test
**Warning signs:** Tests pass individually but fail when run together; tests fail when run in different order

### Pitfall 2: Forgetting to Test Warnings

**What goes wrong:** Config validation warnings go untested because they're printed to stderr, not returned
**Why it happens:** Focus on return values, forget about side effects
**How to avoid:** Use capsys.readouterr().err to capture and assert on stderr output
**Warning signs:** Code coverage shows print statements are hit, but no tests verify the message content

### Pitfall 3: Path.expanduser() vs Path.exists()

**What goes wrong:** Tests for DEFAULT_CONFIG_PATH.expanduser() fail because they try to check if the file exists
**Why it happens:** Confusion between path expansion (string operation) and file existence (I/O operation)
**How to avoid:** Test that expanduser() produces a path starting with Path.home(), don't check if file exists
**Warning signs:** Tests fail in CI but pass locally (different home directories exist/don't exist)

### Pitfall 4: Invalid Parametrize IDs

**What goes wrong:** Parametrized tests have cryptic names like "test_load_config[0]", "test_load_config[1]"
**Why it happens:** Omitting the `ids` parameter in @pytest.mark.parametrize
**How to avoid:** Always provide descriptive ids that explain what each test case validates
**Warning signs:** When a test fails, you can't tell from the name which scenario broke

## Code Examples

Verified patterns from official sources and existing codebase:

### Test Structure (Following test_tracker.py pattern)

```python
# Source: tests/test_tracker.py (existing codebase)
"""Parametrized tests for config module with tmp_path isolation."""

import pytest
from job_radar.config import load_config, DEFAULT_CONFIG_PATH, KNOWN_KEYS


# ---------------------------------------------------------------------------
# load_config() edge cases (SUCCESS CRITERIA 1, 2, 3)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario,content,expected", [
    ("valid_config", '{"min_score": 3.5, "new_only": true}', {"min_score": 3.5, "new_only": True}),
    ("unknown_key_filtered", '{"unknown_key": "value"}', {}),
    ("mixed_valid_invalid", '{"min_score": 3.0, "bad_key": "x"}', {"min_score": 3.0}),
], ids=["valid_config", "unknown_key_filtered", "mixed_valid_invalid"])
def test_load_config_validation(tmp_path, scenario, content, expected):
    """Test load_config() filters unknown keys (SUCCESS CRITERIA 3)."""
    config_file = tmp_path / "config.json"
    config_file.write_text(content)
    result = load_config(str(config_file))
    assert result == expected
```

### Missing File Test

```python
# Source: https://docs.pytest.org/en/stable/how-to/tmp_path.html
def test_load_config_missing_file(tmp_path):
    """Test load_config() with missing file returns {} without errors (SUCCESS CRITERIA 1)."""
    nonexistent = tmp_path / "nonexistent.json"
    result = load_config(str(nonexistent))
    assert result == {}
```

### Invalid JSON Test with stderr

```python
# Source: https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html
def test_load_config_invalid_json_warns(tmp_path, capsys):
    """Test load_config() with invalid JSON warns to stderr and returns {} (SUCCESS CRITERIA 2)."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"invalid": json')  # Missing closing brace

    result = load_config(str(config_file))

    assert result == {}
    captured = capsys.readouterr()
    assert "Warning: Could not parse config file" in captured.err
    assert str(config_file) in captured.err
```

### Unknown Keys Warning Test

```python
def test_load_config_warns_on_unknown_keys(tmp_path, capsys):
    """Test load_config() warns to stderr naming each unknown key (SUCCESS CRITERIA 3)."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"unknown_key": "value", "another_bad": 123}')

    load_config(str(config_file))

    captured = capsys.readouterr()
    assert "Warning: Unrecognized config key: 'unknown_key'" in captured.err
    assert "Warning: Unrecognized config key: 'another_bad'" in captured.err
```

### Path Expansion Test

```python
# Source: https://docs.python.org/3/library/pathlib.html
def test_default_config_path_expands_tilde():
    """Test DEFAULT_CONFIG_PATH expands ~ correctly to user home directory (SUCCESS CRITERIA 4)."""
    from pathlib import Path

    # DEFAULT_CONFIG_PATH should start with ~
    assert str(DEFAULT_CONFIG_PATH).startswith("~")

    # expanduser() should replace ~ with actual home
    expanded = DEFAULT_CONFIG_PATH.expanduser()
    home = Path.home()
    assert str(expanded).startswith(str(home))
    assert "~" not in str(expanded)
```

### KNOWN_KEYS Validation Test

```python
@pytest.mark.parametrize("key,is_valid", [
    ("min_score", True),
    ("new_only", True),
    ("output", True),
    ("profile", False),  # excluded: required=True
    ("config", False),   # excluded: circular
    ("unknown", False),
], ids=["min_score_valid", "new_only_valid", "output_valid", "profile_rejected", "config_rejected", "unknown_rejected"])
def test_known_keys_validation(key, is_valid):
    """Test KNOWN_KEYS accepts valid keys and rejects others (SUCCESS CRITERIA 5)."""
    assert (key in KNOWN_KEYS) == is_valid
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tmpdir fixture | tmp_path fixture | pytest 3.9 (2018) | pathlib.Path API (modern), tmpdir deprecated |
| Manual stderr capture | capsys fixture | Always available | Simpler API, automatic cleanup |
| Hardcoded test paths | tmp_path per test | pytest best practice | True isolation, parallel test safety |
| Generic parametrize names | ids parameter | Always available | Readable test output, easier debugging |

**Deprecated/outdated:**
- **tmpdir fixture**: Use tmp_path instead (returns pathlib.Path, not py.path.local)
- **tmpdir_factory**: Use tmp_path_factory instead
- **Manual sys.stderr redirection**: Use capsys fixture

## Open Questions

1. **Non-dict JSON types**
   - What we know: Code handles `if not isinstance(raw, dict)` with warning
   - What's unclear: Should we test arrays, null, primitives separately?
   - Recommendation: Single parametrized test for non-dict types (array, null, string, number) - behavior is same for all

2. **Config file encoding**
   - What we know: load_config() uses `encoding="utf-8"`
   - What's unclear: Do we need tests for non-UTF8 files?
   - Recommendation: Skip - edge case unlikely, UTF-8 is default, no user request

3. **Concurrent access to config file**
   - What we know: Config is read at CLI startup (single-threaded)
   - What's unclear: Do we need file locking tests?
   - Recommendation: Skip - not a use case, CLI is single-process

## Sources

### Primary (HIGH confidence)

- [pytest parametrize documentation](https://docs.pytest.org/en/stable/how-to/parametrize.html) - Parametrization best practices
- [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html) - Temporary directory isolation
- [pytest capsys documentation](https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html) - stderr capture patterns
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html) - Path.expanduser() behavior
- /Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/tests/test_tracker.py - Established patterns (tmp_path + parametrize)
- /Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/tests/test_scoring.py - Parametrize with ids pattern
- /Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/.planning/STATE.md - Prior decisions affecting testing approach

### Secondary (MEDIUM confidence)

- [How to Use pytest Parametrize (2026-02-02)](https://oneuptime.com/blog/post/2026-02-02-pytest-parametrize-guide/view) - Recent best practices
- [Pytest With tmp_path in Plain English](https://thedatasavvycorner.com/blogs/12-pytest-tmp_path) - Practical patterns
- [Mocking Vs. Patching (A Quick Guide For Beginners)](https://pytest-with-eric.com/mocking/mocking-vs-patching/) - unittest.mock.patch usage

### Tertiary (LOW confidence)

None - all findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pytest 9.0.2 already installed and in use (Phases 1-3)
- Architecture: HIGH - patterns verified in existing test_tracker.py and test_scoring.py
- Pitfalls: HIGH - documented in official pytest docs and existing codebase issues

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days - stable ecosystem, pytest patterns don't change frequently)
