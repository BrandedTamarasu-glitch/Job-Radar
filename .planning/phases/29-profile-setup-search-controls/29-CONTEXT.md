# Phase 29: Profile Setup & Search Controls - Context

**Gathered:** 2026-02-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver complete GUI feature parity with the CLI through profile creation/editing forms, search configuration controls, real search execution with progress feedback, and automatic report opening. Phase 28 provided the GUI shell and threading pattern — this phase fills it with real functionality. Packaging is Phase 30.

</domain>

<decisions>
## Implementation Decisions

### Profile form layout
- Form replaces Profile tab content in-place (same window, same tab) when editing or creating
- Fields organized in grouped sections with headers (e.g., "Identity", "Skills", "Preferences") — one scrollable page
- Resume PDF upload offered as a choice before showing the form: "Upload resume or fill manually?" (mirrors CLI wizard flow)
- List-type fields (skills, titles, dealbreakers) use tag-style chips: type a value, press Enter to add as chip, click X to remove

### Search controls design
- Two date picker widgets for From/To date range (calendar popups or spinner-style)
- Default values match current CLI defaults (no date filter, min score from config file)
- "New only" uses a toggle switch (on/off, modern look)
- Run Search button placement and controls layout at Claude's discretion

### Progress & completion flow
- Immediate visual feedback: switch to progress view with "Starting search..." before first source name appears
- Enhanced source progress: show source name + job count as each completes (e.g., "Dice: 12 jobs found") building a running tally
- On completion: show "Search complete! X jobs found" with an "Open Report" button — user clicks to open (not auto-open)
- Partial source failures: silent success — open report with whatever succeeded, don't mention failures (consistent with Phase 28 context decision)

### Form validation & editing
- Validation fires on field blur (when user leaves a field) — immediate inline feedback per field
- Edit mode accessed via "Edit Profile" button on the profile summary view — switches to form pre-filled with current values
- After saving/creating profile: navigate to Search tab with success message (profile created, ready to search)
- Cancel button with confirmation dialog if fields were modified ("Discard changes?")

### Claude's Discretion
- Search controls layout (above button vs sidebar)
- Date picker widget choice (calendar popup vs spinner — whatever CustomTkinter supports well)
- Exact form section names and field ordering
- Tag chip visual styling
- Success/error message styling
- Window resizing behavior during form display

</decisions>

<specifics>
## Specific Ideas

- The "Upload resume or fill manually?" choice mirrors the existing CLI wizard's first prompt — keeps the experience familiar
- Tag chips for skills/titles should feel lightweight — type, Enter, see the chip, X to remove
- Completion screen with "Open Report" button gives the user a moment to see results count before browser opens
- Enhanced progress tally ("Dice: 12 jobs found") makes the wait feel productive rather than passive

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 29-profile-setup-search-controls*
*Context gathered: 2026-02-13*
