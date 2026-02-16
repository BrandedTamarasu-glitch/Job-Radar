# Phase 38: Auto-Update Foundation (Version Detection) - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can discover new versions via GitHub Releases API and get notified within the GUI. Includes version checking, notification banner, dismiss/remind behavior, and Settings integration. Downloading and installing updates are separate phases (39-41).

</domain>

<decisions>
## Implementation Decisions

### Notification appearance
- Full-width top banner above all content (VS Code style)
- Accent/info color (blue/teal) that stands out but isn't alarming
- Shows version number and Download button: "Version X.Y.Z available" + Download + Remind Later
- X button to dismiss (24-hour suppress) plus Remind Later button (7-day suppress)
- No changelog preview in banner (that's Phase 41 scope)

### Check timing & frequency
- Check GitHub Releases API once per day on launch (skip if already checked within 24 hours)
- Background thread — app loads immediately, banner appears a moment later if update found
- On network failure: silent fail with subtle indicator in Settings showing last check failed
- Store last-checked timestamp and check status inside existing config (not a separate file)

### Dismiss & remind behavior
- X button: suppresses banner for 24 hours
- Remind Later button: suppresses banner for 7 days
- Per-version dismiss — dismissing v2.3 only suppresses v2.3; if v2.4 drops during suppress period, it shows immediately
- After suppress period ends, banner reappears on next daily update check (not automatically mid-session)

### Settings integration
- Dedicated "Updates" section in Settings tab
- Shows current version, last check time, and check status (e.g., "v2.2.0 — Last checked: 2h ago — Up to date")
- "Check for Updates" button with inline status feedback: button text changes "Checking..." → "Up to date!" or "Update available!"
- "Check for updates automatically" toggle — user can disable auto-checks entirely
- Manual check always available regardless of toggle state

### Claude's Discretion
- Exact banner animation/transition
- Version comparison implementation details (semantic versioning parsing)
- GitHub Releases API request specifics (auth, caching headers)
- Error state icon/tooltip design in Settings

</decisions>

<specifics>
## Specific Ideas

- Banner placement and style inspired by VS Code's update notification bar
- "Download" button in banner links to GitHub Releases page in browser (actual in-app download is Phase 39)
- Inline button feedback pattern: text swap on the button itself rather than a dialog or toast

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 38-auto-update-foundation--version-detection-*
*Context gathered: 2026-02-16*
