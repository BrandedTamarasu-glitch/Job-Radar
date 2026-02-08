# Phase 02: Config File Support - Research

**Researched:** 2026-02-07
**Domain:** Python argparse config-file integration, stdlib JSON config loading
**Confidence:** HIGH

## Summary

This phase adds a persistent JSON config file at `~/.job-radar/config.json` that supplies default values for CLI flags. The entire implementation uses Python's stdlib — `json`, `argparse`, `pathlib`, and `os`. No new dependencies are required.

The standard Python pattern for this problem is `argparse.set_defaults()`. Config values are loaded from JSON and fed into `parser.set_defaults(**config_values)` before `parser.parse_args()` is called. Because argparse processes CLI arguments after applying `set_defaults`, any flag explicitly passed on the command line automatically overrides the config value. If no config file exists, `set_defaults` is never called and behavior is identical to today.

The one non-obvious concern is boolean flags with `action="store_true"`. The current `--new-only` flag defaults to `False`. If a user sets `"new_only": true` in config but later wants to override it back to `false` on the CLI, there is no `--no-new-only` flag to do so. The correct fix is to use `argparse.BooleanOptionalAction` which auto-generates both `--new-only` and `--no-new-only`. This is a Python 3.9+ feature and the project already requires Python 3.10+.

**Primary recommendation:** Implement config loading in a new `job_radar/config.py` module; call `load_config()` from `search.py`'s `main()` right before `parse_args()`; use `parser.set_defaults(**config)` to inject values; convert `--new-only` to `BooleanOptionalAction`.

## Standard Stack

This phase uses zero third-party libraries. Everything is stdlib.

### Core

| Module | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| `json` | stdlib | Parse `~/.job-radar/config.json` | Already used in project for profile loading |
| `pathlib.Path` | stdlib (3.4+) | Resolve `~` in config path, check existence | Cleaner than `os.path` for path manipulation |
| `argparse` | stdlib | `set_defaults()` to inject config values | Already used for all CLI parsing |
| `os` | stdlib | `os.makedirs` for creating config directory if needed | Already imported in `search.py` |

### Supporting

| Module | Version | Purpose | When to Use |
|--------|---------|---------|-------------|
| `warnings` | stdlib | Emit config-key warnings without `sys.exit` | For CONF-05 unknown key warnings |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `json` stdlib | `tomli` (TOML) | TOML is explicitly OUT OF SCOPE: requires backport for 3.10 |
| `pathlib.Path` | `os.path.expanduser` | `Path.expanduser()` is cleaner; both work, Path is preferred per codebase conventions |
| `set_defaults` pattern | Manual arg post-processing | Post-processing is fragile: cannot distinguish "user passed None" from "default None" |

**Installation:** No new packages needed.

## Architecture Patterns

### Recommended Project Structure

```
job_radar/
├── config.py        # NEW: load_config(), validate_config(), DEFAULT_CONFIG_PATH
├── search.py        # MODIFIED: import load_config, call before parse_args
└── (all others unchanged)
```

### Pattern 1: Config-Then-CLI with set_defaults

**What:** Load JSON config, inject as argparse defaults, then parse CLI. Argparse priority ensures CLI wins.
**When to use:** Any CLI tool where persistent defaults are needed without breaking existing users.

```python
# Source: https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.set_defaults
def main():
    # 1. Load config BEFORE creating the parser args
    config = load_config()  # returns {} if no config file

    # 2. Build parser as usual
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument("--new-only", action=argparse.BooleanOptionalAction, default=False)
    # ... other args ...

    # 3. Inject config values as defaults (CLI will override these)
    parser.set_defaults(**config)

    # 4. Parse CLI - CLI flags override config defaults
    args = parser.parse_args()
```

**Why this works:** `add_argument(default=...)` sets argument-level defaults. `set_defaults()` sets parser-level defaults which take priority over argument-level defaults. When user passes a CLI flag, it overrides everything.

### Pattern 2: Config Loading Module

**What:** Isolate config I/O in its own module so `search.py` stays focused on orchestration.

```python
# job_radar/config.py
# Source: Python docs - json, pathlib, argparse patterns
import json
import warnings
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("~/.job-radar/config.json")

KNOWN_KEYS = {"min_score", "new_only", "output", "profile"}

def load_config(config_path: str | None = None) -> dict:
    """Load config from JSON file. Returns {} if file does not exist.

    Never raises — missing config is not an error.
    """
    path = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH.expanduser()

    if not path.exists():
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        # Bad JSON is a user error worth surfacing
        print(f"Warning: config file {path} has invalid JSON: {e}", file=sys.stderr)
        return {}

    return validate_config(raw)


def validate_config(raw: dict) -> dict:
    """Warn on unknown keys, return only recognized keys."""
    result = {}
    for key, value in raw.items():
        if key not in KNOWN_KEYS:
            print(f"Warning: config file contains unrecognized key '{key}' — ignored")
        else:
            result[key] = value
    return result
```

### Pattern 3: BooleanOptionalAction for Boolean Flags

**What:** Replaces `action="store_true"` with `BooleanOptionalAction` so users can explicitly pass `--no-new-only` to override a config that sets `new_only: true`.

```python
# Source: https://docs.python.org/3/library/argparse.html (Python 3.9+)
parser.add_argument(
    "--new-only",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Only show new (unseen) results in the report.",
)
# Now both --new-only and --no-new-only are valid
```

**Why needed:** With `action="store_true"`, once config sets `new_only=true`, the user cannot override it back to `false` from the CLI without editing the config file. `BooleanOptionalAction` solves this.

### Anti-Patterns to Avoid

- **Post-processing args manually:** Don't inspect `args.min_score is None` after `parse_args()` and conditionally apply config. This pattern fails for boolean flags where `False` is ambiguous (default vs. explicit). Use `set_defaults()` instead.
- **Mutating args namespace directly:** Don't do `args.min_score = config.get("min_score", args.min_score)`. This is the brittle manual version of what `set_defaults()` does cleanly.
- **Requiring the config file:** The tool MUST work identically when no config exists (CONF-03). Never `sys.exit()` on missing config.
- **Storing config in the repo:** `~/.job-radar/config.json` is user-global, not project-local. Don't add it to `.gitignore` as a project concern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI-overrides-config precedence | Manual conditional logic on each arg | `argparse.set_defaults()` | Argparse handles the priority stack correctly; manual logic is fragile and misses edge cases |
| Boolean flag toggling | Custom `--enable-X`/`--disable-X` flags | `argparse.BooleanOptionalAction` | stdlib feature since 3.9; auto-generates `--no-X` variant |
| JSON parsing | Custom tokenizer | `json.load()` stdlib | JSON format is zero-dep; already used for profile loading |
| Path expansion | Manual string replacement of `~` | `Path.expanduser()` | Handles edge cases on all platforms |

**Key insight:** The entire implementation is a thin wrapper around stdlib features that already exist. The risk is over-engineering it — keep the module small.

## Common Pitfalls

### Pitfall 1: Boolean Flag Ambiguity with store_true

**What goes wrong:** Config sets `new_only=true`. User runs without `--new-only`. Gets `True` from config. User cannot override back to `False` without editing config file.
**Why it happens:** `action="store_true"` can only produce `True` when the flag is present; it cannot produce `False` on demand.
**How to avoid:** Switch `--new-only` to `action=argparse.BooleanOptionalAction` before adding `set_defaults`.
**Warning signs:** Users complain they can't turn off a config-enabled feature from the CLI.

### Pitfall 2: Confusing Argument-Level vs Parser-Level Defaults

**What goes wrong:** Developer adds `default=2.8` to `add_argument("--min-score", ...)`, then calls `set_defaults(min_score=3.0)` from config, expects config to win. It does — but they're confused when `set_defaults` wins over `add_argument`'s default.
**Why it happens:** Argparse priority: parser-level (`set_defaults`) overrides argument-level (`default=`).
**How to avoid:** Keep `default=None` on all configurable arguments. Hard-code fallbacks only in the actual logic (`min_score if min_score is not None else 2.8`), not in `add_argument`.
**Warning signs:** Config values seem to have no effect on arguments with explicit `default=`.

### Pitfall 3: Config Key Names vs CLI Flag Names

**What goes wrong:** CLI flag is `--min-score` (hyphen), but JSON key is `min_score` (underscore). Config loads `min-score` as the key, `set_defaults(min-score=3.0)` fails silently because argparse uses `min_score` internally.
**Why it happens:** Argparse converts hyphens to underscores in `dest` names. JSON doesn't.
**How to avoid:** Define config keys using underscore names (`min_score`, `new_only`, `from_date`, `to_date`). Document this clearly in validation and in user-facing help.
**Warning signs:** Config values are loaded but never applied.

### Pitfall 4: Crashing When Config File Has Invalid JSON

**What goes wrong:** User accidentally saves config with a typo (`{min_score: 3.0}` — missing quotes). Tool crashes with `JSONDecodeError` on startup.
**Why it happens:** `json.load()` raises on invalid JSON.
**How to avoid:** Wrap `json.load()` in try/except `json.JSONDecodeError`, print a warning, return empty dict. Never `sys.exit()` for a missing or malformed config.
**Warning signs:** Any user-reported crash before search even starts.

### Pitfall 5: Config File Expanding Profile Path Makes --profile Optional Prematurely

**What goes wrong:** Config supports a `profile` key. Developer marks `--profile` as `required=True` in argparse but config could supply it. Argparse validates `required` before `set_defaults` values are visible.
**Why it happens:** Argparse `required=True` check happens at parse time, ignoring `set_defaults` values.
**How to avoid:** Change `--profile` to `required=False` with `default=None`. After `parse_args()`, check `if args.profile is None` and exit with a helpful message. Or keep `required=True` and do not put `profile` in KNOWN_KEYS for now (simpler: defer profile defaulting to a future phase).
**Warning signs:** Users get argparse "required argument missing" error even when profile is in config.

## Code Examples

### Complete load_config() Implementation

```python
# Source: Python stdlib docs — json, pathlib, argparse patterns verified 2026-02-07
import json
import sys
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("~/.job-radar/config.json")

# Underscore names match argparse's internal dest names for CLI flags
KNOWN_KEYS = {"min_score", "new_only", "output", "profile"}


def load_config(config_path: str | None = None) -> dict:
    """Load JSON config from ~/.job-radar/config.json or custom path.

    Returns empty dict if file does not exist — absence is not an error.
    Prints warning and returns {} on invalid JSON.
    Prints warning for each unrecognized key.
    """
    path = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH.expanduser()

    if not path.exists():
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Warning: {path} contains invalid JSON: {e.msg} (line {e.lineno})")
        return {}

    if not isinstance(raw, dict):
        print(f"Warning: {path} must contain a JSON object, not {type(raw).__name__}")
        return {}

    result = {}
    for key, value in raw.items():
        if key not in KNOWN_KEYS:
            print(f"Warning: config file contains unrecognized key '{key}' — ignored")
        else:
            result[key] = value
    return result
```

### Integration in search.py main()

```python
# Source: argparse set_defaults pattern — Python docs verified 2026-02-07
def parse_args(config: dict):
    parser = argparse.ArgumentParser(
        description="Search and score job listings for a candidate profile."
    )
    parser.add_argument("--config", default=None, help="Path to config file")
    parser.add_argument("--profile", default=None, ...)
    parser.add_argument("--min-score", type=float, default=None, ...)
    parser.add_argument(
        "--new-only",
        action=argparse.BooleanOptionalAction,
        default=False,
        ...
    )
    # ... other args ...

    # Inject config values as defaults; CLI overrides these
    parser.set_defaults(**config)

    return parser.parse_args()


def main():
    # Two-pass: first parse just --config to know where to load from
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", default=None)
    pre_args, _ = pre_parser.parse_known_args()

    config = load_config(pre_args.config)
    args = parse_args(config)
    # ... rest of main ...
```

### Config File Example (for documentation/help text)

```json
{
  "min_score": 3.0,
  "new_only": true,
  "output": "results"
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `args.X = config.get(X, args.X)` post-processing | `parser.set_defaults(**config)` | argparse has had set_defaults since Python 2.7 | Cleaner, less error-prone |
| `action="store_true"` for booleans | `BooleanOptionalAction` | Python 3.9 | Users can explicitly disable boolean flags |
| `os.path.expanduser()` | `pathlib.Path.expanduser()` | Python 3.4 | Path objects preferred in Python 3.6+ codebases |

**Deprecated/outdated:**
- `optparse`: Replaced by argparse in Python 3.2. Not relevant here.
- `configparser` (INI format): Valid alternative, but JSON is already used in this project and is explicitly chosen.

## Open Questions

1. **Should `--profile` be configurable via config file?**
   - What we know: `--profile` is currently `required=True`. argparse requires presence before `set_defaults` values are applied.
   - What's unclear: Whether users would actually want a default profile path.
   - Recommendation: Exclude `profile` from KNOWN_KEYS for now. Keep `--profile` required. Add profile defaulting in a future enhancement.

2. **Should `--config` itself be parseable from within the config file?**
   - What we know: This would be circular.
   - What's unclear: Nothing — it's clearly not valid.
   - Recommendation: `--config` is CLI-only, never in config.

3. **Should config loading print warnings to stdout or stderr?**
   - What we know: The project currently uses `print()` for user-facing messages in `search.py` and `log.*` for internal messages.
   - What's unclear: Whether warnings about config issues should be interleaved with normal output.
   - Recommendation: Use `print(..., file=sys.stderr)` for config warnings so they don't pollute report output when stdout is piped.

## Sources

### Primary (HIGH confidence)

- https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.set_defaults — set_defaults behavior and priority
- https://docs.python.org/3/library/argparse.html#default — default vs set_defaults precedence, SUPPRESS sentinel
- https://docs.python.org/3/library/argparse.html#the-add-argument-method — BooleanOptionalAction documentation
- https://docs.python.org/3/library/pathlib.html#pathlib.Path.expanduser — Path.expanduser() for ~ resolution
- https://docs.python.org/3/library/json.html#json.load — json.load with JSONDecodeError handling

### Secondary (MEDIUM confidence)

- Project codebase (`job_radar/search.py`) — existing argparse structure, current flag names and types
- Project codebase (`.planning/codebase/CONVENTIONS.md`) — coding style (underscore names, error handling patterns)
- Project codebase (`.planning/codebase/STACK.md`) — confirmed stdlib-only approach, Python 3.10+ requirement

### Tertiary (LOW confidence)

- None needed — all claims verified with official docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib only, verified against Python docs
- Architecture: HIGH — set_defaults is the documented pattern for this exact use case
- Pitfalls: HIGH — all derived from documented argparse behavior or direct code inspection

**Research date:** 2026-02-07
**Valid until:** 2026-04-07 (stdlib documentation changes very slowly; 60-day validity)
