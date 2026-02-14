# Phase 34: GUI Scoring Configuration - Context

**Gathered:** 2026-02-13
**Status:** Ready for planning

<domain>
## Phase Boundary

GUI controls that let users customize how jobs are scored — adjust 6 scoring component weights via sliders and set staffing firm preference via dropdown, with live preview of scoring changes.

This phase delivers the visual interface for scoring configuration. The backend (profile schema v2, scoring engine integration) was completed in Phase 33.

</domain>

<decisions>
## Implementation Decisions

### Control Design & Layout
- Sliders organized by category grouping (e.g., Skills, Fit, Response sections)
- Visual feedback: Show value + percentage for each slider (e.g., "0.25 (25%)")
- **Claude's Discretion:** Exact category groupings (Skills/Fit/Response vs other logical groups)
- **Claude's Discretion:** Slider precision/granularity (0.01, 0.05, or 0.10 increments)

### Live Preview Behavior
- Preview shows: Sample job score recalculation (e.g., "Was: 3.8 → Now: 4.2")
- Update timing: Real-time updates as user moves any slider
- Preview location: Side panel to the right of the sliders
- Sample data: Use hardcoded example job with known characteristics

### Validation & Feedback
- Validation timing: Both live warning during editing AND save block enforcement
- Auto-normalize helper: "Normalize" button that proportionally adjusts all weights to sum to 1.0
- Reset button: Reset to defaults with confirmation prompt ("Reset all scoring to defaults?")
- **Claude's Discretion:** Error display pattern (banner, inline, or toast)

### Settings Placement
- Location: Within existing Settings tab (not a new dedicated tab)
- Presentation: Collapsible section with expand/collapse control
- Initial state: Expanded on first visit, then remember user's last state
- Help/guidance: Help icon (?) with tooltip explaining each component

</decisions>

<specifics>
## Specific Ideas

- Live preview updates in real-time as user drags sliders — immediate feedback on score impact
- Side panel preview keeps controls and results visible simultaneously
- Normalize button helps users quickly fix sum-to-1.0 violations without manual math
- Collapsible section keeps Settings tab clean while making scoring accessible

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 34-gui-scoring-configuration*
*Context gathered: 2026-02-13*
