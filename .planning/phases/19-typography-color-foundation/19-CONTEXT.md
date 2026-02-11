# Phase 19: Typography & Color Foundation - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the visual design foundation for HTML reports: system font stacks for professional typography and a semantic color system that maps score tiers to distinct colors. This phase delivers CSS variables and base styles that all subsequent v1.4.0 phases build on. No structural HTML changes, no new JavaScript, no new features — pure visual foundation.

</domain>

<decisions>
## Implementation Decisions

### Color Palette
- Claude's discretion on how much to depart from Bootstrap default blue (accent-only vs full custom)
- Simplify to 3 tiers (not 4): green (strong, >=4.0), cyan/teal (recommended, 3.5-3.9), neutral gray (worth reviewing, 2.8-3.4)
- Warm-to-cool gradient feel: green (warm, positive) → cyan (cool, neutral) → gray (muted)
- Dark mode via `prefers-color-scheme` media query — automatic, zero user interaction
- Same hue per tier in dark mode, just inverted (dark backgrounds with lighter text/borders)
- Semantic colors extend to BOTH job cards AND all-results table rows
- Subtle tint intensity — light pastel backgrounds with colored left border (GitHub issue label style, not Jira bold fills)
- No specific color reference app — trust WCAG compliance + research to pick values

### Typography Choices
- System UI default stack: `system-ui, -apple-system, Segoe UI, etc.` — native feel per platform
- Monospace for score badges ONLY — not for salary, employment type, or other table data
- Stronger type hierarchy: larger report title, clear section headers with weight/size differences, smaller body text — newspaper-style scanning
- Comfortable spacing: more line height and padding for easier scanning over density

### Non-color Indicators
- Claude's discretion on indicator type (left border + icon, border thickness variation, or combination)
- Claude's discretion on whether NEW badge gets visual refresh to match new color system
- Claude's discretion on whether indicators appear in table rows (dense) or cards only
- Claude's discretion on whether score badges include tier name text ("Strong Match") alongside numeric score

### Score Badge Styling
- Pill-shaped badges (rounded, like GitHub labels)
- Inline accent — badge sits next to title at similar size, title is primary
- Same pill style in both cards and table — visual consistency, no size reduction for table
- Application status badges (Applied, Interviewing, etc.) also get refreshed to pill style matching new palette

### Claude's Discretion
- Exact departure from Bootstrap blue theme
- Non-color indicator implementation approach (borders, icons, or both)
- NEW badge refresh (yes/no based on design coherence)
- Table row indicator density
- Tier name text on badges (yes/no based on space and readability)
- Exact color hex values (must pass WCAG AA 4.5:1)
- Dark mode color adaptation details

</decisions>

<specifics>
## Specific Ideas

- Subtle tint backgrounds like GitHub issue labels — not bold/saturated like Jira
- Pill badges like GitHub's label pills — modern, distinctive, consistent in cards and table
- "Newspaper-style scanning" — clear visual hierarchy where you can quickly find the best matches
- Dark mode should feel natural — same hues, inverted contrast, not a jarring color shift

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 19-typography-color-foundation*
*Context gathered: 2026-02-11*
