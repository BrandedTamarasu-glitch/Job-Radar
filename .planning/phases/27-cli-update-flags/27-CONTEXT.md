# Phase 27: CLI Update Flags - Context

**Gathered:** 2026-02-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can update common profile fields directly from the command line without entering interactive mode. Flags for skills, min_score, and titles. Always exits after update — no search. Interactive editing is Phase 26.

</domain>

<decisions>
## Implementation Decisions

### Flag Naming & Syntax
- **Long flags only** — no short aliases (--update-skills, --set-min-score, --set-titles)
- Skills format: **comma-separated quoted** string (--update-skills "python,react,typescript")
- --update-skills **replaces the entire list** — simple, predictable
- **Add --set-titles** flag in addition to --update-skills and --set-min-score (titles change often enough)

### Output & Feedback
- Success output shows **confirmation + diff** (e.g., "Skills updated.\n  Old: python, react\n  New: python, react, typescript")
- **Same backup message** as interactive mode ("Profile backed up") — consistent across all update paths
- **Always show output** — same messages whether interactive or piped, no TTY detection
- --set-min-score shows **context hint** ("Min score updated to 3.5 (jobs scoring below 3.5 will be hidden)")

### Error Handling & Exit Codes
- **Exit code 1** for all errors — simple, conventional
- Errors **always suggest valid range** (e.g., "min_score must be 0.0-5.0, got 7.0") — matches Phase 24 friendly tone
- No profile exists: **error with guidance** ("No profile found. Run 'job-radar' first to create one.")
- **Allow clearing** skills list with empty string — user might want to start fresh

### Flag Scope & Combinations
- **One update flag per command** — error if multiple update flags used, avoids partial-failure
- Update flags **always exit** without searching — clean separation of concerns
- Update flags and --view-profile are **mutually exclusive** — avoids order-of-operations confusion
- --help text **includes examples** for each update flag

### Claude's Discretion
- Exact argparse configuration and help text formatting
- Error message wording beyond the established friendly tone
- How empty string clearing interacts with validation (may need special case)

</decisions>

<specifics>
## Specific Ideas

- CLI flags should work well in shell scripts and CI — consistent exit codes, predictable output
- Examples in --help should show the most common use case for each flag

</specifics>

<deferred>
## Deferred Ideas

- --add-skill / --remove-skill granular flags — deferred per "Replace only for v1.5" decision, add later if users need them
- --run flag to combine update + search — keep exit-only for now, revisit based on usage

</deferred>

---

*Phase: 27-cli-update-flags*
*Context gathered: 2026-02-12*
