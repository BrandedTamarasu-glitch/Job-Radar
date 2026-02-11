---
phase: 17-application-status-tracking
plan: 01
subsystem: reporting
tags: [html-report, application-status, localStorage, bootstrap-dropdown, status-tracking, state-hydration]

dependency-graph:
  requires:
    - phase: 16-application-flow-essentials
      provides: HTML report with Bootstrap 5.3, Notyf toasts, inline JavaScript pattern
  provides:
    - Application status tracking UI with dropdown selectors on every job
    - Status badge rendering with semantic colors (Applied/Interviewing/Rejected/Offer)
    - localStorage + tracker.json bidirectional sync with conflict resolution
    - Pending status export as downloadable JSON
    - get_all_application_statuses() bulk read function in tracker.py
  affects:
    - 17-02 (will use status tracking foundation)
    - 18-accessibility (status dropdowns need ARIA labels)

tech-stack:
  added:
    - localStorage API for client-side status caching
    - Blob API for JSON export downloads
    - tracker.json embedded as <script type="application/json">
  patterns:
    - Server-to-client state hydration via embedded JSON
    - localStorage merge with tracker.json-wins conflict resolution
    - Bootstrap dropdown for status selection UI
    - Semantic badge colors for status visualization
    - pending_sync flag pattern for unsynced localStorage entries

key-files:
  created: []
  modified:
    - job_radar/tracker.py
    - job_radar/report.py

key-decisions:
  - "Embedded tracker.json status in HTML head as JSON script tag for state hydration"
  - "localStorage as session cache, tracker.json as source of truth for persistence"
  - "Tracker.json wins in merge conflicts to handle file:// protocol localStorage scoping"
  - "Export-based sync pattern (not File System Access API) for broader browser support"
  - "Status dropdown on every job (cards and table rows) for consistent UX"

patterns-established:
  - "Status management: hydrateApplicationStatus() → merge tracker.json + localStorage → renderBadges()"
  - "Job key format: {title.lower()}||{company.lower()} matches tracker.job_key()"
  - "Data attributes on job elements: data-job-key, data-job-title, data-job-company for JavaScript access"
  - "Event delegation for dropdown clicks to handle dynamic badge updates"
  - "pending_sync flag indicates localStorage entries not yet in tracker.json"

duration: 4
completed: 2026-02-11
---

# Phase 17 Plan 01: Application Status Tracking UI Summary

**Status dropdown on every job with localStorage persistence, embedded tracker.json hydration, semantic badge colors, and JSON export for pending updates**

## Performance

- **Duration:** 4 minutes
- **Started:** 2026-02-11T15:42:37Z
- **Completed:** 2026-02-11T15:46:45Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- User can select Applied/Interviewing/Rejected/Offer status from dropdown on any job card or table row
- Status appears as color-coded Bootstrap badge (green/blue/red/yellow) on job items
- Status persists across sessions via localStorage cache hydrated from embedded tracker.json data
- Export button downloads pending status updates as JSON file for manual sync
- Tracker.py has bulk read function to avoid repeated file I/O when embedding status for all jobs

## Task Commits

Each task was committed atomically:

1. **Task 1: Add tracker bulk read and embed status data in HTML template** - `f18c471` (feat)
2. **Task 2: Add status management JavaScript (hydration, change handler, badges, export)** - `8e5a10c` (feat)

## Files Created/Modified

- `job_radar/tracker.py` - Added get_all_application_statuses() bulk read function
- `job_radar/report.py` - Embedded tracker status JSON, added status dropdowns to cards and table, added status management JavaScript (hydration, badges, export)

## Decisions Made

**1. Embedded tracker.json status in HTML head as <script type="application/json">**
- Rationale: Enables safe state hydration on page load without network request, works on file:// protocol
- Alternatives: External JSON file (requires serving), inline JavaScript data (XSS risk)
- Trade-offs: Increases HTML file size slightly, but maintains single-file portability

**2. localStorage as session cache, tracker.json as source of truth**
- Rationale: file:// protocol means each HTML file has separate localStorage origin, tracker.json persists across report regenerations
- Alternatives: localStorage only (lose status across reports), IndexedDB (added complexity)
- Trade-offs: Requires manual export/sync step, but works in all browsers

**3. Tracker.json wins in merge conflicts**
- Rationale: Prevents clock skew issues, ensures server state is authoritative
- Alternatives: Last-write-wins (clock skew risk), CRDT (overkill for single-user)
- Trade-offs: User must export localStorage changes before new report generation

**4. Export-based sync pattern (not File System Access API)**
- Rationale: File System Access API only works in Chrome/Edge, export works everywhere
- Alternatives: File System Access API (Chrome-only), manual tracker.json editing (error-prone)
- Trade-offs: Extra user step (download + manual merge), but universal browser support

**5. Status dropdown on every job (cards and table rows)**
- Rationale: Consistent UX, no context switching to mark status
- Alternatives: Modal dialog (more clicks), separate status page (context loss)
- Trade-offs: Slightly busier UI, but faster workflow

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed successfully with no blocking issues.

## User Setup Required

None - no external service configuration required. All functionality is client-side JavaScript using browser APIs.

## Next Phase Readiness

- Application status tracking UI is complete and functional
- Ready for Phase 17 Plan 02 (if planned) or Phase 18 (Accessibility)
- Status dropdowns will need ARIA labels review in Phase 18 for WCAG 2.1 Level AA compliance
- localStorage merge pattern established for future status sync enhancements

## Technical Implementation Details

### State Hydration Flow
1. Page loads → read embedded `<script id="tracker-status">` JSON
2. Read localStorage cache (`job-radar-application-status`)
3. Merge: tracker.json entries win, localStorage adds new with `pending_sync: true`
4. Render status badges on all job items with data-job-key

### Status Change Flow
1. User clicks dropdown item with `data-status="applied"`
2. Event delegation handler finds parent `[data-job-key]` element
3. Update localStorage with new status + `pending_sync: true`
4. Render badge with pending indicator (yellow dot)
5. Show toast confirmation
6. Update export button count

### Export Flow
1. User clicks "Export Status Updates"
2. Filter localStorage entries with `pending_sync: true`
3. Create Blob with `{ applications: { ...pendingUpdates } }` JSON structure
4. Trigger download as `job-status-updates-YYYY-MM-DD.json`
5. User manually merges into tracker.json (future automation possible)

### Browser Compatibility
- Uses `var` and `function` declarations (not `let`/`const`/arrow functions) for maximum compatibility
- localStorage operations wrapped in try/catch for QuotaExceededError handling
- Blob API for download (works in all modern browsers)
- Bootstrap 5.3 dropdowns (standard, accessible)

## Self-Check: PASSED

**Verification:**

Files created: (none)

Files modified:
- FOUND: /home/corye/Claude/Job-Radar/job_radar/report.py
- FOUND: /home/corye/Claude/Job-Radar/job_radar/tracker.py

Commits:
- FOUND: f18c471 (Task 1: Add tracker bulk read and embed status data in HTML template)
- FOUND: 8e5a10c (Task 2: Add status management JavaScript)

All claims verified. Summary is accurate.

---
*Phase: 17-application-status-tracking*
*Completed: 2026-02-11*
