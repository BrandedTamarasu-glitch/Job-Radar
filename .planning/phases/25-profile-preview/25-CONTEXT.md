# Phase 25: Profile Preview - Context

**Gathered:** 2026-02-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can see their current profile settings in a formatted display — automatically on every startup (after wizard check, before search) and on demand via `--view-profile`. Display only; editing is Phase 26.

</domain>

<decisions>
## Implementation Decisions

### Display Layout & Density
- **Sectioned with headers** — grouped into logical sections (e.g., Identity, Skills, Preferences, Filters) with clear section headers
- **Bordered table** using tabulate or box-drawing characters for structured grid appearance
- **Branded header** line to clearly demarcate the profile section (e.g., "═══ Job Radar Profile ═══")
- **Only show set fields** — hide fields that are empty or at default values to reduce noise

### Startup Behavior
- Profile preview displays **after wizard check, before search** — profile always reflects the latest state
- Preview shows **every run** — consistent experience, user always knows what they're searching with
- `--view-profile` **prints profile then offers to edit** — asks "Want to edit? (y/N)" as a convenient shortcut
- If `--view-profile` and no profile exists, **launch wizard automatically** to create one
- **Clear separator line** between profile preview and search output

### Field Presentation
- List fields (skills, titles, dealbreakers) displayed as **comma-separated inline** — compact, fits in table cells
- **Show all items** in lists — no truncation, user sees exactly what's configured
- Numeric fields show **just the value** — no range hints (e.g., "Min Score: 3.5" not "3.5 (0.0-5.0)")
- Boolean fields use **friendly labels** — "Yes" / "No" or "Enabled" / "Disabled" instead of true/false

### Suppression & Control
- **--no-wizard covers preview suppression** — one flag for quiet mode, no separate --no-preview flag
- Preview **respects NO_COLOR** automatically (Phase 18 infrastructure already in place)
- Edit mode from --view-profile **launches quick-edit menu** (Phase 26's interactive flow, once available)

### Claude's Discretion
- Exact section grouping of fields
- Table style (tabulate format choice)
- Separator line style
- Color scheme for the preview (within NO_COLOR constraints)

</decisions>

<specifics>
## Specific Ideas

- The branded header should feel like the existing CLI output style — not too flashy, just clearly delineated
- tabulate 0.9.0 was chosen during milestone research for table display

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 25-profile-preview*
*Context gathered: 2026-02-12*
