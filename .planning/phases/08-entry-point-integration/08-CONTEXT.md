# Phase 8: Entry Point Integration - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Connect the wizard (Phase 7) to the search pipeline so wizard-generated profiles flow seamlessly into job search. The wizard already creates `~/.job-radar/profile.json` and config files, but the search still requires explicit `--profile` flag. This phase makes the profile path automatic while preserving developer flexibility and backward compatibility.

</domain>

<decisions>
## Implementation Decisions

### Profile path handling
- **Config file setting**: Wizard writes `profile_path` field to `config.json` pointing to the created profile
- **CLI override precedence**: Command-line `--profile` flag always takes precedence over config.json setting
- **Legacy config handling**: If config.json exists but has no `profile_path` setting (v1.0 config), default to `get_data_dir()/profile.json`
- **Wizard integration**: Wizard updates config.json with `profile_path` field after creating profile.json (seamless for user)

### Error handling flow
- **Missing profile behavior**: If config.json points to missing profile.json, treat as first-run and launch wizard to recreate it
- **Corrupt JSON handling**: Backup corrupt file to `profile.json.bak`, then launch wizard to create fresh profile
- **Invalid structure handling**: Treat structure errors (missing required fields) same as corrupt JSON - backup and re-run wizard
- **Emergency override**: `--profile` flag always works as escape hatch, even if default profile fails or wizard fails

### Development mode behavior
- **Consistent experience**: `python -m job_radar` (dev mode) behaves identically to frozen .exe - same wizard, same profile paths, same flow
- **Backward compatibility interpretation**: "Still works for development" means it runs successfully WITH wizard integration (not OLD v1.0 behavior)
- **Wizard bypass option**: Add `--no-wizard` flag so developers can skip wizard and use `--profile` explicitly (useful for testing different profiles)

### Profile validation timing
- **Validation at startup**: Load and validate profile during `__main__.py` startup, fail fast if invalid (before search execution)
- **Automatic error handling**: On validation failure, backup corrupt file and re-run wizard automatically (don't require manual editing)
- **Debug flag**: Add `--validate-profile` flag to check profile.json without running search (prints validation results and exits)

### Claude's Discretion
- Validation strictness (permissive vs strict on extra fields) - choose based on forward compatibility needs
- Exact error message wording for validation failures
- How to display backup file location to user
- Whether to log validation details to file for debugging

</decisions>

<specifics>
## Specific Ideas

- Profile path flow: wizard creates `~/.job-radar/profile.json` → wizard updates config.json with `{"profile_path": "~/.job-radar/profile.json"}` → search.py reads profile_path from config → fallback to `--profile` flag if specified
- Error recovery pattern: corrupt/missing profile → backup to `.bak` → launch wizard → continue to search
- Developer workflow: `python -m job_radar --no-wizard --profile /path/to/test.json` for testing alternate profiles

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 08-entry-point-integration*
*Context gathered: 2026-02-09*
