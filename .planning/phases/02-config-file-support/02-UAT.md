---
status: complete
phase: 02-config-file-support
source: [02-01-SUMMARY.md]
started: 2026-02-08T02:20:00Z
updated: 2026-02-08T02:25:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Config file sets CLI defaults
expected: Create ~/.job-radar/config.json with {"min_score": 3.0, "new_only": true}. Run job-radar without those flags — the config values should apply automatically.
result: pass

### 2. CLI flag overrides config
expected: With config containing "min_score": 3.0, run with --min-score 2.5. The 2.5 value should be used, not 3.0 from config.
result: pass

### 3. No config file = no behavior change
expected: Delete (or never create) ~/.job-radar/config.json and run job-radar normally. No errors, no warnings — identical behavior to before this change.
result: pass

### 4. Custom config path via --config
expected: Run job-radar --config /path/to/custom.json pointing to a file with different settings. Those settings apply instead of the default location.
result: pass

### 5. Unknown config key warning
expected: Create a config with {"unknown_key": true, "min_score": 3.0}. Running the tool should print a warning to stderr naming "unknown_key", while still applying min_score.
result: pass

### 6. --no-new-only overrides config
expected: Set "new_only": true in config. Running with --no-new-only should override it back to false (shows all jobs, not just new ones).
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
