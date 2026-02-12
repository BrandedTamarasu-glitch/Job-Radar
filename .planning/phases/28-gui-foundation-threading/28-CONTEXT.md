# Phase 28: GUI Foundation & Threading - Context

**Gathered:** 2026-02-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the desktop GUI shell with CustomTkinter, dual entry points (GUI vs CLI detection from a single executable), and non-blocking threading infrastructure so long-running searches don't freeze the window. Profile forms and search execution are Phase 29 — this phase delivers the skeleton, threading proof, and entry point logic.

</domain>

<decisions>
## Implementation Decisions

### Window appearance
- Medium window size (700x500) on launch
- Follow system theme automatically (dark/light) — CustomTkinter handles this
- Tabbed sections for organization (Profile / Search tabs at minimum)
- Header area with app name and icon/logo placeholder at top of window

### Entry point behavior
- Single executable with auto-detection: opens GUI when double-clicked (no flags), uses CLI when run with flags from terminal
- First launch (no profile): welcome screen explaining what Job Radar does, "Get Started" button leads to profile form
- Returning user (profile exists): profile summary shown as default view, user navigates to search tab
- No console window by default; console visible in verbose mode (--verbose flag)

### Progress display
- Progress indicator replaces the search area (center of window) while running
- Shows source name: "Fetching Dice..." as each source runs
- Cancel button available during search to stop the operation
- Claude's discretion on determinate bar vs indeterminate spinner (pick based on existing on_progress callback feasibility)

### Error presentation
- Errors shown as popup dialog boxes (modal)
- Partial source failures: show results silently — open the report with whatever succeeded, don't mention failures (CLI already handles graceful degradation)
- No profile state: Run Search button disabled (grayed out) with tooltip "Profile required" until profile exists
- Profile form validation: inline red text under each specific field that has an error

### Claude's Discretion
- Progress indicator type (determinate bar vs indeterminate spinner)
- Exact tab names and ordering
- Welcome screen layout and copy
- Icon/logo design (placeholder is fine)
- Window resizing behavior (fixed vs resizable)

</decisions>

<specifics>
## Specific Ideas

- Single executable approach: `len(sys.argv) > 1` (or similar heuristic) to detect CLI vs GUI mode
- The threading proof in this phase should use mock/simulated long operations (10+ seconds) to validate the pattern before real search integration in Phase 29
- Profile summary on returning-user launch should feel like the existing `--view-profile` output but in GUI form

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 28-gui-foundation-threading*
*Context gathered: 2026-02-12*
