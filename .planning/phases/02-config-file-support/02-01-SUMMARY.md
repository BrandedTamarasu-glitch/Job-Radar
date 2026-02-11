---
phase: 02-config-file-support
plan: 01
subsystem: cli
tags: [argparse, json, config, pathlib, BooleanOptionalAction]

# Dependency graph
requires:
  - phase: 01-fuzzy-skill-normalization
    provides: working CLI and scoring pipeline this config layer wraps
provides:
  - Persistent JSON config file at ~/.job-radar/config.json sets CLI defaults
  - --config flag for custom config path
  - --no-new-only flag (via BooleanOptionalAction) to override config-set new_only
  - Unknown config key warnings to stderr
affects:
  - 03-test-suite: config module and two-pass parsing need test coverage

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Two-pass argparse: pre-parser extracts --config, then set_defaults injects config before full parse
    - Config warns but never errors: missing file, invalid JSON, unknown keys all degrade gracefully

key-files:
  created:
    - job_radar/config.py
  modified:
    - job_radar/search.py

key-decisions:
  - "KNOWN_KEYS excludes 'profile' (required=True arg) and 'config' (circular) -- only min_score, new_only, output"
  - "All config warnings go to stderr to avoid polluting piped stdout"
  - "BooleanOptionalAction on --new-only enables --no-new-only to override config-set new_only: true"
  - "Two-pass parse: pre-parser extracts --config path before full parse applies set_defaults"

patterns-established:
  - "Config loading: stdlib only (json, pathlib, sys) -- no third-party dependencies"
  - "Graceful degradation: load_config always returns dict, never raises"

# Metrics
duration: 2min
completed: 2026-02-08
---

# Phase 2 Plan 1: Config File Support Summary

**stdlib-only JSON config loader at ~/.job-radar/config.json with two-pass argparse integration, set_defaults injection, and BooleanOptionalAction for --no-new-only override**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-08T02:13:15Z
- **Completed:** 2026-02-08T02:15:12Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- New `job_radar/config.py` module with `load_config()`, `DEFAULT_CONFIG_PATH`, `KNOWN_KEYS` -- all stdlib, no new dependencies
- Two-pass CLI parsing extracts `--config` path before full parse, then injects config via `parser.set_defaults(**config)`
- `--new-only` upgraded to `BooleanOptionalAction` so `--no-new-only` can override config-set `new_only: true`
- All five CONF requirements (CONF-01 through CONF-05) verified passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create config loading module** - `510db7d` (feat)
2. **Task 2: Integrate config loading into CLI pipeline** - `23d5583` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `job_radar/config.py` - Config loading: DEFAULT_CONFIG_PATH, KNOWN_KEYS, load_config()
- `job_radar/search.py` - Two-pass parsing, --config flag, BooleanOptionalAction, set_defaults integration

## Decisions Made
- KNOWN_KEYS excludes `profile` (required=True, validated before set_defaults applies) and `config` (circular reference) -- only `min_score`, `new_only`, `output` are configurable
- All config warnings use `print(..., file=sys.stderr)` to avoid polluting piped stdout
- `BooleanOptionalAction` on `--new-only` enables `--no-new-only` to override config-set `new_only: true` back to false
- Two-pass parse pattern: pre-parser extracts `--config` path, then full `parse_args(config)` applies `set_defaults`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `python` command not available in shell (macOS default is `python3`) -- used `python3` for verification commands. Not a code issue.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Config module complete and tested; ready for Phase 3 test suite coverage
- No blockers -- `load_config()` is pure stdlib and fully isolated

---
*Phase: 02-config-file-support*
*Completed: 2026-02-08*
