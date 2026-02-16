# Phase 41: Auto-Update Polish - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Polish the update experience with two features: "Skip This Version" to permanently dismiss a specific version's notification, and a "What's new?" changelog preview showing formatted release notes from GitHub Releases. Both build on the existing notification banner and Settings Updates section from Phases 38-40.

</domain>

<decisions>
## Implementation Decisions

### Skip Version behavior
- "Skip This Version" button lives in a dropdown/menu (not alongside main banner buttons) — keeps banner clean since skipping is less common
- After skipping: brief "v{version} skipped" confirmation message, then banner dismisses
- If the only available version is skipped: no banner on launch, but Settings tab shows "v{version} available (skipped)" status
- Skip is only available in the notification state — once download starts, Skip is no longer offered (user committed)

### Changelog presentation
- Release notes displayed in a separate dialog (not inline in banner) — more room for content
- Show summary only: first paragraph or first ~5 bullet points, with link to full notes on GitHub
- Basic formatting: bold headings, bullet points — no images or complex markdown
- Empty release notes: show "No release notes available for this version. View on GitHub →"

### "What's new?" trigger
- Version number in the banner is clickable — clicking opens the changelog dialog (no separate "What's new?" button)
- On demand only — user clicks to see notes, banner stays clean by default
- Dialog is view-only: shows notes + Close button. User goes back to banner to download.
- Settings Updates section also shows "View release notes" link when update is available

### Persistence & state
- No limit on skipped versions — list grows unbounded
- Manual check in Settings: shows skipped version but marked as "(skipped)" — user knows they chose to skip
- "Clear skipped versions" button in Settings to un-skip all
- Release notes cached with update state (stored alongside version info) — one fetch per version, avoids re-fetching

### Claude's Discretion
- Dropdown/menu implementation (CTk option menu, right-click context, or "..." button)
- Exact summary extraction logic (first paragraph vs first N bullets)
- Basic markdown rendering approach in CustomTkinter
- "Skipped" confirmation message timing and animation
- How to style the clickable version number to look like a link
- Release notes cache expiry/invalidation strategy

</decisions>

<specifics>
## Specific Ideas

- Clickable version number is subtle and clean — no extra button clutter, power users discover it naturally
- Dropdown for Skip keeps the banner simple for the 90% case (download or dismiss)
- Showing "(skipped)" on manual check respects the user's choice while still giving them info
- Caching release notes avoids hitting GitHub API repeatedly for the same version

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 41-auto-update-polish*
*Context gathered: 2026-02-16*
