# Phase 10: UX Polish - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Improve user-facing messaging and error handling for non-technical users running the Job Radar CLI application. This phase polishes existing flows (wizard, search, help text) with friendly progress indicators, helpful error messages, graceful interruption handling, and clear launch messaging. No new features — just better UX for what already exists.

</domain>

<decisions>
## Implementation Decisions

### Progress messaging style
- **Verbosity:** Minimal — "Fetching Indeed... (1/4)" format, one line per source, no job counts during fetch
- **Visual style:** Plain text only — no colors, no symbols (works everywhere, CI-friendly)
- **Update behavior:** Stack vertically — each source gets its own line (no in-place updates)
- **Completion feedback:** Brief confirmation after each source ("Indeed complete", "LinkedIn complete")

### Error message tone and detail
- **Network errors:** Friendly + actionable — "Couldn't reach Indeed — check your internet connection" (no HTTP codes or tracebacks)
- **Zero results:** Encouraging — "No matches yet — try broadening your skills or lowering min_score"
- **Python tracebacks:** Never show to users — catch all exceptions, show friendly message, log technical details to error file for debugging
- **Critical errors:** Exit with explanation — print error, suggest fix, exit cleanly with code 1 (don't try to continue with partial data)

### Welcome/launch messaging
- **Banner frequency:** Every run — users should know what version they're running
- **Banner style:** Boxed text — text surrounded by border characters (more visual than plain text, less space than ASCII art)
- **Banner content:** Name + version + profile name — "Job Radar v1.1 — Searching for [Your Name]" (personalized)
- **Help hint:** Yes — add "Run with --help for options" below the banner

### Help text structure
- **Wizard explanation:** Wizard-first approach — explain interactive wizard at top, then "Or use these flags to skip wizard" section
- **Usage examples:** Include 2-3 examples — common scenarios like first run, custom score, custom profile path
- **Flag grouping:** By function — "Search Options", "Output Options", "Profile Options" sections (not alphabetical)
- **Description length:** One-line descriptions — brief but clear, e.g., "--min-score: Minimum match score (1-5, default 2.8)"

### Claude's Discretion
- Exact box drawing characters for banner
- Error log file location and format
- Specific wording of error messages (as long as friendly + actionable)
- Ctrl+C interrupt handling implementation (just needs to exit gracefully without traceback)

</decisions>

<specifics>
## Specific Ideas

- Progress messages should feel like they're making progress — users need reassurance during the 10-30 second fetch
- Error messages should never blame the user or feel judgmental — just explain what happened and suggest what to try
- The welcome banner is a chance to remind users what version they're on (helpful for debugging)
- Help text should teach the wizard-first flow, since that's the designed UX for non-technical users

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-ux-polish*
*Context gathered: 2026-02-09*
