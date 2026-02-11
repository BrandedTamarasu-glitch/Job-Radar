# Phase 17: Application Status Tracking - Research

**Researched:** 2026-02-11
**Domain:** Application status persistence, localStorage with file:// protocol, bidirectional state sync
**Confidence:** HIGH

## Summary

Phase 17 implements persistent application status tracking ("Applied", "Rejected", "Interviewing") that survives across browser sessions and report regenerations. The critical architectural challenge is that HTML reports are standalone files opened via `file://` protocol, where each file has its own localStorage origin. Reports are regenerated with new filenames on each search run (`jobs_2026-02-11_14-30.html`), so traditional localStorage-only approaches fail.

The solution requires bidirectional sync between tracker.json (Python backend, source of truth) and localStorage (browser frontend, per-file ephemeral state). On report generation, Python embeds current application statuses from tracker.json as inline JSON in the HTML template. On page load, JavaScript hydrates from embedded data, merging with any localStorage entries. When users update status via UI, changes write to localStorage AND trigger a sync mechanism to update tracker.json for persistence across future report generations.

Research confirms: (1) localStorage on file:// protocol is scoped per-file, not per-directory, (2) Embedded JSON via `<script type="application/json">` provides safe server-to-client state hydration, (3) localStorage merge patterns require conflict resolution strategy (last-write-wins or tracker.json-wins), (4) Bootstrap 5 dropdown buttons + badge combinations provide standard UI for status changes, (5) File System Access API or manual export/import required for browser → tracker.json sync.

**Primary recommendation:** Implement server-to-client hydration pattern with embedded tracker.json status data. Use localStorage as session cache. Provide "Export Updates" button that generates a JSON patch file users can process (or implement File System Access API for direct tracker.json write on supported browsers). Display status badges on job cards with inline dropdown buttons for status changes.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| localStorage | Native | Session-level status cache | Browser standard, 5-10MB quota, synchronous API |
| JSON.parse/stringify | Native | Status data serialization | Native JSON handling, zero dependencies |
| Bootstrap 5 Dropdowns | 5.3+ | Status change UI (dropdown buttons) | Already in project, accessible, mobile-friendly |
| Bootstrap 5 Badges | 5.3+ | Visual status indicators | Already in project, semantic color system |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| File System Access API | Native (Chrome 86+) | Direct tracker.json write | Chrome/Edge only, requires user permission |
| Blob + Download API | Native | Export JSON patch file | Fallback for all browsers |
| Storage Event API | Native | Cross-tab status sync (same-origin only) | If serving reports via localhost, not file:// |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| localStorage + embed pattern | IndexedDB only | Adds complexity, same file:// origin issue, async API overhead |
| tracker.json as source of truth | localStorage only | Lose status across report regenerations |
| Manual export/import | File System Access API | Works everywhere vs. Chrome-only, extra user step |
| Inline status buttons | Modal dialog | More clicks, worse UX, but cleaner card layout |

**Installation:**
```bash
# No new dependencies - using native browser APIs and existing Bootstrap 5
```

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── tracker.py              # Existing - extend with application status methods
├── report.py               # Modify - embed tracker status in HTML template
└── (HTML reports generated with embedded JS for status management)

HTML template inline JS:
├── statusManager.js        # Embedded: CRUD operations on status
├── statusUI.js             # Embedded: Dropdown handlers, badge updates
└── statusSync.js           # Embedded: Hydration, localStorage merge, export
```

### Pattern 1: Server-to-Client State Hydration
**What:** Embed tracker.json application status as JSON in `<script type="application/json">` tag
**When to use:** Any time server state needs to initialize client state in standalone HTML
**Example:**
```python
# Source: Verified pattern from "Embedding JSON Within Generated HTML"
# In report.py template generation:

def _generate_html_report(...):
    tracker_status = _get_tracker_application_status()  # From tracker.py

    embedded_status_json = json.dumps(tracker_status, indent=2)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <!-- ... existing head content ... -->

  <!-- Embedded tracker status (source of truth) -->
  <script type="application/json" id="tracker-status">
  {embedded_status_json}
  </script>
</head>
<body>
  <!-- ... existing body content ... -->
</body>
</html>"""
```

**Why this works:**
- `<script type="application/json">` prevents execution, safe for arbitrary JSON
- Data embedded at generation time, available immediately on page load
- No network request, no CORS issues, works on file:// protocol

### Pattern 2: localStorage Merge with Conflict Resolution
**What:** On page load, merge embedded tracker data with localStorage, with tracker.json as source of truth
**When to use:** When syncing server-authoritative state with client-side modifications
**Example:**
```javascript
// Source: Pattern from localStorage sync discussions + conflict resolution
function hydrateApplicationStatus() {
  // Load embedded tracker status (source of truth)
  const trackerData = JSON.parse(
    document.getElementById('tracker-status').textContent
  );

  // Load localStorage cache (may have pending changes)
  const localData = JSON.parse(localStorage.getItem('job-status') || '{}');

  // Merge strategy: tracker.json wins for existing entries,
  // localStorage provides new entries not yet synced
  const merged = { ...trackerData };

  for (const [key, localEntry] of Object.entries(localData)) {
    if (!merged[key]) {
      // New status from localStorage not yet in tracker.json
      merged[key] = { ...localEntry, pending_sync: true };
    } else if (localEntry.updated > merged[key].updated) {
      // localStorage has newer update (clock skew risk, prefer tracker)
      console.warn(`[status] localStorage newer than tracker for ${key}`);
      merged[key] = { ...localEntry, pending_sync: true };
    }
  }

  return merged;
}
```

### Pattern 3: Bootstrap Dropdown Status Selector
**What:** Inline dropdown button in job card for status changes
**When to use:** Limited set of discrete status options (Applied, Rejected, Interviewing, etc.)
**Example:**
```html
<!-- Source: Bootstrap 5.3 Dropdowns documentation -->
<div class="card job-item" data-job-key="senior-engineer||acme-corp">
  <div class="card-header d-flex justify-content-between align-items-center">
    <h3 class="h5 mb-0">Senior Engineer — Acme Corp</h3>

    <!-- Status badge + dropdown -->
    <div class="d-flex align-items-center gap-2">
      <span class="badge bg-success status-badge" id="status-badge-1">Applied</span>

      <div class="dropdown">
        <button class="btn btn-sm btn-outline-secondary dropdown-toggle"
                type="button"
                data-bs-toggle="dropdown"
                aria-label="Change application status">
          Status
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
          <li><a class="dropdown-item" href="#" data-status="applied">Applied</a></li>
          <li><a class="dropdown-item" href="#" data-status="interviewing">Interviewing</a></li>
          <li><a class="dropdown-item" href="#" data-status="rejected">Rejected</a></li>
          <li><a class="dropdown-item" href="#" data-status="offer">Offer</a></li>
          <li><hr class="dropdown-divider"></li>
          <li><a class="dropdown-item" href="#" data-status="">Clear Status</a></li>
        </ul>
      </div>
    </div>
  </div>
  <!-- ... rest of job card ... -->
</div>
```

### Pattern 4: Status Badge Semantic Colors
**What:** Color-code status badges for quick visual scanning
**When to use:** Always, for status indicators with distinct semantic meanings
**Example:**
```javascript
// Source: Bootstrap 5 badge color classes + UX best practices
const STATUS_BADGE_CONFIG = {
  applied: {
    class: 'bg-success',
    label: 'Applied',
    ariaLabel: 'Application submitted'
  },
  interviewing: {
    class: 'bg-primary',
    label: 'Interviewing',
    ariaLabel: 'Interview scheduled or in progress'
  },
  rejected: {
    class: 'bg-danger',
    label: 'Rejected',
    ariaLabel: 'Application rejected'
  },
  offer: {
    class: 'bg-warning text-dark',
    label: 'Offer',
    ariaLabel: 'Job offer received'
  }
};

function updateStatusBadge(jobKey, status) {
  const badge = document.querySelector(`[data-job-key="${jobKey}"] .status-badge`);
  if (!badge) return;

  const config = STATUS_BADGE_CONFIG[status];
  if (!config) {
    badge.remove();
    return;
  }

  badge.className = `badge ${config.class} status-badge`;
  badge.textContent = config.label;
  badge.setAttribute('aria-label', config.ariaLabel);
}
```

### Pattern 5: Export Pending Changes as JSON Patch
**What:** Generate downloadable JSON file with localStorage changes for manual tracker.json sync
**When to use:** When File System Access API unavailable or user prefers manual sync
**Example:**
```javascript
// Source: Blob API + Download pattern from MDN
function exportPendingStatusUpdates() {
  const localData = JSON.parse(localStorage.getItem('job-status') || '{}');
  const pendingUpdates = Object.entries(localData)
    .filter(([_, entry]) => entry.pending_sync)
    .reduce((acc, [key, entry]) => {
      acc[key] = {
        title: entry.title,
        company: entry.company,
        status: entry.status,
        updated: entry.updated
      };
      return acc;
    }, {});

  if (Object.keys(pendingUpdates).length === 0) {
    notyf.error('No pending status updates to export');
    return;
  }

  const blob = new Blob(
    [JSON.stringify(pendingUpdates, null, 2)],
    { type: 'application/json' }
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `job-status-updates-${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);

  notyf.success(`Exported ${Object.keys(pendingUpdates).length} status updates`);
}
```

### Pattern 6: File System Access API for Direct Write (Chrome/Edge)
**What:** Use modern File System Access API to write directly to tracker.json
**When to use:** Chrome/Edge browsers, when user grants permission
**Example:**
```javascript
// Source: MDN File System Access API documentation
async function syncToTrackerFile() {
  if (!('showSaveFilePicker' in window)) {
    // Fallback to export pattern
    exportPendingStatusUpdates();
    return;
  }

  try {
    const trackerPath = 'results/tracker.json';  // User needs to select this
    const fileHandle = await window.showSaveFilePicker({
      suggestedName: 'tracker.json',
      types: [{
        description: 'Job Radar Tracker',
        accept: { 'application/json': ['.json'] }
      }]
    });

    const writable = await fileHandle.createWritable();

    // Load current tracker, merge localStorage updates
    const currentTracker = JSON.parse(
      document.getElementById('tracker-status').textContent
    );
    const localData = JSON.parse(localStorage.getItem('job-status') || '{}');

    // Merge pending updates into tracker applications section
    for (const [key, entry] of Object.entries(localData)) {
      if (entry.pending_sync) {
        currentTracker.applications[key] = {
          title: entry.title,
          company: entry.company,
          status: entry.status,
          updated: entry.updated
        };
      }
    }

    await writable.write(JSON.stringify(currentTracker, null, 2));
    await writable.close();

    // Clear pending_sync flags
    for (const key in localData) {
      if (localData[key].pending_sync) {
        delete localData[key].pending_sync;
      }
    }
    localStorage.setItem('job-status', JSON.stringify(localData));

    notyf.success('Status synced to tracker.json');
  } catch (err) {
    if (err.name !== 'AbortError') {
      console.error('[statusSync] File System Access failed', err);
      notyf.error('Sync failed — use Export button instead');
    }
  }
}
```

### Anti-Patterns to Avoid
- **Using localStorage as single source of truth:** file:// origin scoping means status lost across report regenerations
- **Not embedding tracker status in HTML:** Client has no server state, can't detect conflicts
- **Ignoring pending_sync flag:** Users lose track of which updates need manual sync
- **Writing to tracker.json without permission:** File System Access API requires explicit user consent
- **Not providing export fallback:** Firefox/Safari don't support File System Access API
- **Storing entire job objects in localStorage:** Bloats storage, use job keys and minimal metadata
- **Not handling clock skew:** User's system clock may be off, prefer tracker.json timestamp on conflict

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| State hydration | Custom base64 encoding | JSON in `<script type="application/json">` | Standard pattern, safe, no encoding overhead |
| File download | Custom iframe hack | Blob API + `<a>` download attribute | Modern, reliable, works everywhere |
| Status change UI | Custom modal | Bootstrap dropdown | Already in stack, accessible, mobile-friendly |
| Conflict resolution | Custom CRDT | Last-write-wins with tracker.json preference | Simpler, sufficient for single-user desktop app |
| Cross-tab sync | Custom polling | Storage Event API (if using localhost) | Native browser API, automatic, efficient |

**Key insight:** State hydration via embedded JSON is standard SSR pattern used by React, Vue, Next.js. The `<script type="application/json">` tag prevents execution while allowing easy JSON.parse() access. Reinventing this risks XSS vulnerabilities from improper escaping.

## Common Pitfalls

### Pitfall 1: localStorage Scoped Per-File on file:// Protocol
**What goes wrong:** User marks job as "Applied" in today's report, opens yesterday's report, status missing
**Why it happens:** Each HTML file opened via file:// has separate localStorage origin
**How to avoid:** Embed tracker.json status in every generated report, hydrate on load
**Warning signs:** Status appears to "reset" when switching between report files

### Pitfall 2: Forgetting to Sync localStorage → tracker.json
**What goes wrong:** User marks 20 jobs as Applied, runs new search, all statuses lost
**Why it happens:** localStorage changes not persisted to tracker.json before next report generation
**How to avoid:** Prominent "Sync Status" or "Export Updates" button, remind user before closing
**Warning signs:** "pending_sync" flags accumulate, users complain about lost status

### Pitfall 3: JSON Injection via Unescaped Embedded Data
**What goes wrong:** Job title contains `</script>`, breaks embedded JSON, potential XSS
**Why it happens:** Python f-string doesn't escape JSON content for HTML context
**How to avoid:** Use `json.dumps()` for JSON serialization, ensure no `</script>` in output
**Warning signs:** Browser console errors, malformed JSON, weird rendering

### Pitfall 4: Clock Skew Breaking Conflict Resolution
**What goes wrong:** User's system clock is wrong, localStorage timestamp newer than tracker, infinite conflict
**Why it happens:** Using timestamp comparison without clock sync validation
**How to avoid:** Prefer tracker.json-wins strategy, or use sequence numbers instead of timestamps
**Warning signs:** Same status update exported repeatedly, never clearing pending_sync

### Pitfall 5: localStorage Quota Exceeded (5-10MB)
**What goes wrong:** After tracking 500+ jobs, localStorage.setItem() throws QuotaExceededError
**Why it happens:** Storing full job objects instead of minimal keys + status
**How to avoid:** Store only `{jobKey: {status, updated}}`, not entire job objects
**Warning signs:** Browser console DOMException, status changes silently failing

### Pitfall 6: No Feedback for Sync Status
**What goes wrong:** User clicks status dropdown, unclear if change saved or pending sync
**Why it happens:** No visual indicator for pending vs. synced status
**How to avoid:** Show badge or icon for pending changes, confirmation message on sync
**Warning signs:** Users repeatedly changing same status, uncertain if it "took"

### Pitfall 7: Dropdown Closes Before Click Registers
**What goes wrong:** User clicks status in dropdown, dropdown closes, status doesn't change
**Why it happens:** Bootstrap dropdown auto-closes on click, event handler timing issue
**How to avoid:** Use event delegation, prevent default, update status before dropdown closes
**Warning signs:** Clicks on dropdown items appear to do nothing

### Pitfall 8: File System Access API Permission Denied
**What goes wrong:** Browser blocks tracker.json write, no fallback offered
**Why it happens:** User denies permission, or browser doesn't support File System Access API
**How to avoid:** Always provide export fallback, handle AbortError gracefully
**Warning signs:** Sync button does nothing on Firefox/Safari

## Code Examples

Verified patterns from official sources:

### Hydration on Page Load (Complete Implementation)
```javascript
// Source: State hydration pattern + localStorage merge
document.addEventListener('DOMContentLoaded', function() {
  // 1. Load embedded tracker status (source of truth)
  const trackerStatusEl = document.getElementById('tracker-status');
  const trackerStatus = trackerStatusEl
    ? JSON.parse(trackerStatusEl.textContent)
    : {};

  // 2. Load localStorage cache
  const localStatus = JSON.parse(
    localStorage.getItem('job-application-status') || '{}'
  );

  // 3. Merge: tracker.json wins, localStorage adds new entries
  const mergedStatus = { ...trackerStatus };
  let pendingCount = 0;

  for (const [jobKey, localEntry] of Object.entries(localStatus)) {
    if (!mergedStatus[jobKey]) {
      // New status not yet in tracker.json
      mergedStatus[jobKey] = { ...localEntry, pending_sync: true };
      pendingCount++;
    } else if (localEntry.updated > mergedStatus[jobKey].updated) {
      // localStorage newer (should be rare if syncing regularly)
      mergedStatus[jobKey] = { ...localEntry, pending_sync: true };
      pendingCount++;
    }
  }

  // 4. Update localStorage with merged state
  localStorage.setItem('job-application-status', JSON.stringify(mergedStatus));

  // 5. Render status badges on job cards
  renderAllStatusBadges(mergedStatus);

  // 6. Show pending sync count if any
  if (pendingCount > 0) {
    showSyncReminder(pendingCount);
  }
});

function renderAllStatusBadges(statusMap) {
  document.querySelectorAll('.job-item').forEach(function(card) {
    const jobKey = card.dataset.jobKey;
    if (!jobKey) return;

    const statusEntry = statusMap[jobKey];
    if (statusEntry && statusEntry.status) {
      renderStatusBadge(card, statusEntry.status, statusEntry.pending_sync);
    }
  });
}
```

### Status Change Handler with localStorage Write
```javascript
// Source: Bootstrap dropdown event handling + localStorage update
document.addEventListener('click', function(event) {
  if (!event.target.matches('.dropdown-item[data-status]')) return;

  event.preventDefault();

  const statusItem = event.target;
  const newStatus = statusItem.dataset.status;
  const dropdown = statusItem.closest('.dropdown');
  const card = dropdown.closest('.job-item');
  const jobKey = card.dataset.jobKey;

  if (!jobKey) {
    console.error('[statusChange] No job key found on card');
    return;
  }

  // Extract job metadata from card data attributes
  const jobTitle = card.dataset.jobTitle || 'Unknown';
  const jobCompany = card.dataset.jobCompany || 'Unknown';

  // Load current status map
  const statusMap = JSON.parse(
    localStorage.getItem('job-application-status') || '{}'
  );

  // Update or remove status
  if (newStatus === '') {
    // Clear status
    delete statusMap[jobKey];
    removeStatusBadge(card);
    notyf.success('Status cleared');
  } else {
    // Set new status
    statusMap[jobKey] = {
      title: jobTitle,
      company: jobCompany,
      status: newStatus,
      updated: new Date().toISOString(),
      pending_sync: true  // Needs sync to tracker.json
    };
    renderStatusBadge(card, newStatus, true);
    notyf.success(`Marked as ${newStatus}`);
  }

  // Save to localStorage
  localStorage.setItem('job-application-status', JSON.stringify(statusMap));

  // Update pending sync count
  updateSyncReminderCount();
});
```

### Render Status Badge with Pending Indicator
```javascript
// Source: Bootstrap badge classes + custom pending indicator
const STATUS_CONFIG = {
  applied: { class: 'bg-success', label: 'Applied' },
  interviewing: { class: 'bg-primary', label: 'Interviewing' },
  rejected: { class: 'bg-danger', label: 'Rejected' },
  offer: { class: 'bg-warning text-dark', label: 'Offer' }
};

function renderStatusBadge(card, status, isPending) {
  const header = card.querySelector('.card-header');
  if (!header) return;

  // Remove existing status badge if present
  const existingBadge = header.querySelector('.status-badge');
  if (existingBadge) existingBadge.remove();

  const config = STATUS_CONFIG[status];
  if (!config) return;

  // Create new badge
  const badge = document.createElement('span');
  badge.className = `badge ${config.class} status-badge me-2`;
  badge.textContent = config.label;

  // Add pending indicator if not synced
  if (isPending) {
    const pendingIcon = document.createElement('span');
    pendingIcon.className = 'badge bg-secondary ms-1';
    pendingIcon.textContent = '●';
    pendingIcon.title = 'Pending sync to tracker.json';
    badge.appendChild(pendingIcon);
  }

  // Insert before dropdown or at end of header
  const dropdown = header.querySelector('.dropdown');
  if (dropdown) {
    dropdown.parentElement.insertBefore(badge, dropdown);
  } else {
    header.appendChild(badge);
  }
}
```

### Export Pending Updates (Fallback for All Browsers)
```javascript
// Source: Blob API + download attribute pattern from MDN
function exportPendingStatusUpdates() {
  const statusMap = JSON.parse(
    localStorage.getItem('job-application-status') || '{}'
  );

  const pendingUpdates = {};
  for (const [jobKey, entry] of Object.entries(statusMap)) {
    if (entry.pending_sync) {
      pendingUpdates[jobKey] = {
        title: entry.title,
        company: entry.company,
        status: entry.status,
        updated: entry.updated
      };
    }
  }

  const count = Object.keys(pendingUpdates).length;
  if (count === 0) {
    notyf.error('No pending status updates to export');
    return;
  }

  // Create downloadable JSON file
  const blob = new Blob(
    [JSON.stringify({ applications: pendingUpdates }, null, 2)],
    { type: 'application/json' }
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `job-status-updates-${new Date().toISOString().split('T')[0]}.json`;
  link.click();
  URL.revokeObjectURL(url);

  notyf.success(`Exported ${count} status update${count > 1 ? 's' : ''}`);
}
```

### Python: Embed Tracker Status in HTML Template
```python
# Source: JSON embedding pattern + Python f-string template
import json
from job_radar import tracker

def _generate_html_report(filepath, profile, scored_results, ...):
    # Load current application statuses from tracker.json
    tracker_data = tracker._load_tracker()
    applications = tracker_data.get('applications', {})

    # Serialize for embedding
    embedded_status = json.dumps(applications, indent=2)

    # Generate HTML with embedded status
    html_content = f"""<!DOCTYPE html>
<html lang="en" data-bs-theme="auto">
<head>
  <!-- ... existing head content ... -->

  <!-- Embedded application status from tracker.json -->
  <script type="application/json" id="tracker-status">
{embedded_status}
  </script>
</head>
<body>
  <!-- ... existing body content ... -->

  <script>
    // Hydration and status management code here
    // (inline for single-file portability)
  </script>
</body>
</html>"""

    filepath.write_text(html_content, encoding='utf-8')
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| localStorage only | localStorage + server hydration | 2018+ (React SSR era) | Enables state sync across generated files |
| Manual JSON escaping | `<script type="application/json">` | 2015+ | Safer, prevents XSS, easier parsing |
| Download via hidden iframe | Blob API + download attribute | 2014+ (IE10+) | Simpler, more reliable, better UX |
| Custom file picker | File System Access API | Chrome 86+ (2020) | Direct file write, but limited browser support |
| Timestamps for conflict resolution | Vector clocks / CRDTs | 2010s (distributed systems) | Overkill for single-user desktop app |
| Storage Event API for cross-tab | Broadcast Channel API | 2016+ | Better ergonomics, but same-origin only |

**Deprecated/outdated:**
- **localStorage-only for persistent state:** Fails with file:// multi-file scenario
- **Hidden iframe download hack:** Blob API + `<a download>` is standard now
- **Custom JSON escape functions:** Use `json.dumps()` + script type="application/json"
- **Polling for cross-tab sync:** Use Storage Event API or Broadcast Channel API

**Current best practices (2026):**
- **Server state hydration via embedded JSON:** Standard SSR pattern, all frameworks use it
- **File System Access API with export fallback:** Graceful degradation for browser support
- **Bootstrap 5 dropdowns for status selectors:** Accessible, mobile-friendly, no custom modals
- **localStorage as session cache, tracker.json as source of truth:** Clear ownership model

## Open Questions

1. **Should we implement auto-sync on page unload (beforeunload event)?**
   - What we know: Could trigger File System Access picker automatically
   - What's unclear: UX friction of permission prompt on every close
   - Recommendation: Provide manual "Sync Now" button, show reminder badge for pending changes

2. **How should conflict resolution work if user edits tracker.json manually?**
   - What we know: tracker.json is source of truth, should win conflicts
   - What's unclear: Whether to preserve localStorage pending changes or discard
   - Recommendation: On next report generation, tracker.json overwrites localStorage (embed pattern handles this)

3. **Should status changes be immediately synced to tracker.json or batched?**
   - What we know: Batching reduces file I/O, but risks data loss
   - What's unclear: User mental model - do they expect instant persistence?
   - Recommendation: Batch updates, show pending count, require explicit sync/export

4. **What happens if user opens multiple reports simultaneously?**
   - What we know: Each file has separate localStorage, Storage Event API doesn't cross file:// origins
   - What's unclear: User expectations for multi-report workflow
   - Recommendation: Document limitation, suggest using latest report only, or serve via localhost for cross-tab sync

5. **Should we support importing status from exported JSON?**
   - What we know: Export produces JSON patch file users can manually merge
   - What's unclear: Whether UX value justifies added complexity
   - Recommendation: Phase 1 - export only, Phase 2 - add import if users request it

6. **What localStorage key naming convention avoids collisions?**
   - What we know: Need scoped key to avoid conflicts with other apps
   - What's unclear: Best prefix pattern
   - Recommendation: Use `job-radar-application-status` as localStorage key

## Sources

### Primary (HIGH confidence)
- [MDN: Window localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) - Storage API, quotas, same-origin policy
- [MDN: File System Access API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API) - Modern file write capabilities
- [MDN: Storage Event](https://developer.mozilla.org/en-US/docs/Web/API/Window/storage_event) - Cross-tab communication
- [Bootstrap 5.3: Dropdowns](https://getbootstrap.com/docs/5.3/components/dropdowns/) - UI component documentation
- [Bootstrap 5.3: Badges](https://getbootstrap.com/docs/5.3/components/badge/) - Badge styling and variants
- [Embedding JSON Within Generated HTML](https://tech.agilitynerd.com/embedding-json-within-generated-html) - Safe JSON embedding pattern

### Secondary (MEDIUM confidence)
- [localStorage on file:// protocol - Bugzilla](https://bugzilla.mozilla.org/show_bug.cgi?id=507361) - file:// origin scoping behavior
- [JavaScript.info: LocalStorage](https://javascript.info/localstorage) - localStorage fundamentals and patterns
- [MDN: Storage Quotas](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria) - 5-10MB limits
- [RxDB: localStorage Guide](https://rxdb.info/articles/localstorage.html) - Modern storage patterns
- [Zustand: localStorage Sync Discussion](https://github.com/pmndrs/zustand/discussions/3199) - State sync patterns
- [5 UX Best Practices for Status Indicators - KoruUX](https://www.koruux.com/blog/ux-best-practices-designing-status-indicators/) - UI design patterns
- [Job Application Tracking Tools 2026](https://yoscareer.com/how-to-keep-track-of-job-applications-2026-guide/) - Domain-specific UX patterns

### Tertiary (LOW confidence - requires validation)
- Community discussions on localStorage limits across browsers - Needs testing
- File System Access API adoption rates 2026 - Should verify current browser support
- Status dropdown vs. modal preferences - Could run UX testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Well-documented browser APIs, existing Bootstrap 5 in project
- Architecture: HIGH - Server hydration is established SSR pattern, localStorage merge pattern verified
- file:// localStorage scoping: HIGH - Confirmed by MDN docs and Firefox bug tracker
- File System Access API: MEDIUM - Chrome/Edge only, requires testing for UX flow
- Conflict resolution: MEDIUM - Simple last-write-wins suitable for single-user, but clock skew edge case
- Status UI patterns: HIGH - Bootstrap standard components, verified accessibility

**Research date:** 2026-02-11
**Valid until:** ~30 days (March 13, 2026) - Stable domain (localStorage, Bootstrap 5), but verify File System Access API browser support during implementation
