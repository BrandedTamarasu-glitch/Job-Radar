# Phase 26: Interactive Quick-Edit - Context

**Gathered:** 2026-02-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can update any single profile field through a guided interactive flow that shows changes before saving. Accessible via `--edit-profile` flag and through the `--view-profile` "Want to edit?" prompt (Phase 25). CLI flag updates are Phase 27.

</domain>

<decisions>
## Implementation Decisions

### Edit Entry & Field Selection
- Entry via **both** `--edit-profile` CLI flag AND the `--view-profile` edit prompt
- **Questionary select** menu with arrow-key navigation — consistent with existing wizard UX
- Menu **shows current values** next to each field name (e.g., "Name (Cory)")
- Fields **grouped by category** in the menu — Identity, Search, Filters, etc.

### Diff Preview & Confirmation
- **Side-by-side** diff display (Old: X → New: Y)
- **Bold/plain styling** for changes — bold for new value, plain for old (works without color, respects NO_COLOR)
- Confirmation prompt: **"Apply this change? (y/N)"** — default No for safety
- Cancel message: **"Change discarded — profile unchanged."** — friendly, reassuring

### Input Handling Per Field Type
- List fields (skills, titles, dealbreakers): **add/remove operations** via submenu for surgical edits on long lists
- List values entered as **comma-separated strings** when adding
- Boolean fields (new_only): **explicit Yes/No choice** menu, no auto-toggle
- Text/number inputs **pre-fill current value** so user can modify rather than retype

### Edit Flow After Save
- After saving: **return to field menu** — supports editing multiple fields in one session
- After declining change: **return to field menu** — user can pick another field or retry
- Menu includes **explicit "Done — exit editor" option** as the last item
- After exiting editor: **offer to run a search** — "Profile updated. Run search now? (y/N)"

### Claude's Discretion
- Exact category grouping of fields in the menu
- Add/remove submenu design (how add vs remove are presented)
- Validation error re-prompt behavior
- How pre-fill works technically (questionary default parameter)

</decisions>

<specifics>
## Specific Ideas

- The edit flow should feel like a natural extension of the existing wizard — same questionary patterns, same visual style
- Side-by-side diff should be clear at 80-column terminal width

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 26-interactive-quick-edit*
*Context gathered: 2026-02-12*
