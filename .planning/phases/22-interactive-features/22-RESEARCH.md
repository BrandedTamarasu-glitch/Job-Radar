# Phase 22: Interactive Features - Research

**Researched:** 2026-02-11
**Domain:** Client-side JavaScript filtering and CSV export for static HTML reports
**Confidence:** HIGH

## Summary

Phase 22 adds two client-side interactive features to the single-file HTML report: status filtering (hide/show jobs by application status) and CSV export (download job results as CSV file from the browser). Both features must work in a file:// protocol environment with no server, using only inline JavaScript already established in the report architecture.

The technical domain splits cleanly: (1) **Status filtering** uses vanilla JavaScript to toggle CSS display:none on table rows and card elements based on dropdown selections, persisting filter state to localStorage and announcing count updates via ARIA live regions. (2) **CSV export** uses Blob URLs with UTF-8 BOM encoding to generate RFC 4180-compliant CSV files with proper quote escaping and formula injection protection, triggered by the HTML5 download attribute on a dynamically created anchor element.

Critical findings: The report already has all infrastructure needed (data-job-key attributes, localStorage status tracking, ARIA live region, status dropdown values). Filtering is a simple querySelectorAll + classList operation. CSV export requires UTF-8 BOM prefix (`"\uFEFF"`) for Excel compatibility on Windows, double-quote escaping per RFC 4180, and formula injection mitigation by prefixing cells starting with `=+-@` with a single quote character. Both features work reliably in file:// protocol (blob: URLs and download attribute are protocol-independent). Display:none is CORRECT for filtering because it removes hidden jobs from accessibility tree, giving screen reader users an equal experience to sighted users (they only hear visible results).

**Primary recommendation:** Build filtering with display:none toggling via classList, persist filter state as JSON object in localStorage["job-radar-filter-state"], announce count updates to existing ARIA live region. Build CSV export with UTF-8 BOM Blob, RFC 4180 escaping function, formula injection sanitizer, and URL.createObjectURL download pattern. All inline JavaScript in existing `<script>` block, zero external dependencies.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vanilla JavaScript | ES6+ (2026 browsers) | DOM manipulation, filtering, CSV generation | Zero dependencies, works in file:// protocol, native browser features |
| localStorage API | Web Storage standard | Persist filter state across sessions | Built-in browser API, synchronous, simple JSON storage |
| Blob API | File API standard | Generate CSV file in-memory | Native browser feature for binary data, works with download attribute |
| URL.createObjectURL | File API standard | Create downloadable blob URL | Standard pattern for client-side downloads, excellent browser support |
| ARIA live regions | WAI-ARIA 1.3 | Announce filter count updates to screen readers | Already present in report.py, extends existing accessibility infrastructure |
| CSS display:none | CSS2.1 standard | Hide filtered-out jobs from visual and accessibility tree | Correct approach for filtering (removes from screen readers) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| HTML5 download attribute | HTML5 standard | Force browser download of blob URL | Already supported in all modern browsers, works in file:// protocol |
| JSON.stringify/parse | ES5 standard | Serialize filter state to localStorage | Built-in, handles nested objects, error-prone so wrap in try/catch |
| Array.prototype.filter | ES5 standard | Filter job data for CSV export | Native array method, clean syntax for visibility checks |
| RFC 4180 escaping | CSV standard | Escape commas, quotes, newlines in CSV fields | Industry standard for CSV generation, prevents parsing errors |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| display:none | visibility:hidden or aria-hidden | visibility:hidden keeps in accessibility tree (BAD for filtering), aria-hidden doesn't hide visually |
| Vanilla JS filtering | Third-party table filter library | Libraries add dependencies, increase file size, overkill for simple show/hide |
| Blob + download | Server-side CSV generation | No server in file:// protocol, defeats single-file HTML goal |
| localStorage | sessionStorage | sessionStorage clears on tab close (bad UX for filter persistence) |
| UTF-8 BOM | Plain UTF-8 | Excel on Windows requires BOM to detect UTF-8, otherwise defaults to windows-1252 |
| Single quote escaping | Tab character for formula injection | Single quote is simpler and works across Excel/Google Sheets/LibreOffice |

**Installation:**

No installation required — all features are native browser APIs supported in modern browsers (Chrome, Firefox, Safari, Edge).

## Architecture Patterns

### Pattern 1: Status Filtering with CSS Class Toggling

**What:** Use dropdown controls to toggle display:none on table rows and card elements based on selected status filter, persisting state to localStorage

**When to use:** Client-side filtering where hidden items should be removed from accessibility tree (screen readers ignore them)

**Example:**

```javascript
// Source: W3Schools filter table pattern + localStorage best practices
// Filter state structure
var filterState = {
  hideApplied: false,
  hideRejected: false,
  hideInterviewing: false,
  hideOffer: false
};

// Load filter state from localStorage
function loadFilterState() {
  try {
    var saved = localStorage.getItem('job-radar-filter-state');
    if (saved) {
      filterState = JSON.parse(saved);
    }
  } catch (err) {
    console.warn('[filter] Failed to load state from localStorage:', err);
    // Use default state
  }
}

// Save filter state to localStorage
function saveFilterState() {
  try {
    localStorage.setItem('job-radar-filter-state', JSON.stringify(filterState));
  } catch (err) {
    console.error('[filter] Failed to save state to localStorage:', err);
    notyf.error('Filter state storage quota exceeded');
  }
}

// Apply filter to all job elements (table rows and cards)
function applyFilter() {
  var allJobs = document.querySelectorAll('[data-job-key]');
  var visibleCount = 0;

  for (var i = 0; i < allJobs.length; i++) {
    var job = allJobs[i];
    var jobKey = job.getAttribute('data-job-key');

    // Check status from localStorage status map
    var statusMap = getApplicationStatusMap();
    var status = statusMap[jobKey] ? statusMap[jobKey].status : null;

    var shouldHide = false;
    if (status === 'applied' && filterState.hideApplied) shouldHide = true;
    if (status === 'rejected' && filterState.hideRejected) shouldHide = true;
    if (status === 'interviewing' && filterState.hideInterviewing) shouldHide = true;
    if (status === 'offer' && filterState.hideOffer) shouldHide = true;

    if (shouldHide) {
      job.style.display = 'none';
      job.setAttribute('aria-hidden', 'true');
    } else {
      job.style.display = '';
      job.removeAttribute('aria-hidden');
      visibleCount++;
    }
  }

  // Announce count update to screen readers
  announceFilterCount(visibleCount, allJobs.length);
}

// Announce filter result count via ARIA live region
function announceFilterCount(visible, total) {
  var announcer = document.getElementById('status-announcer');
  if (!announcer) return;

  var message = 'Showing ' + visible + ' of ' + total + ' jobs';
  announcer.textContent = message;

  // Clear after 1 second so repeated filters re-announce
  setTimeout(function() {
    announcer.textContent = '';
  }, 1000);
}

// Initialize filter on page load
document.addEventListener('DOMContentLoaded', function() {
  loadFilterState();
  renderFilterControls();
  applyFilter();
});
```

**Filter control UI:**

```html
<!-- Add to header section, before "All Results" table -->
<div class="mb-3">
  <label class="form-label">Filter by Status:</label>
  <div class="btn-group" role="group" aria-label="Status filters">
    <input type="checkbox" class="btn-check" id="filter-applied" autocomplete="off">
    <label class="btn btn-outline-secondary" for="filter-applied">Hide Applied</label>

    <input type="checkbox" class="btn-check" id="filter-rejected" autocomplete="off">
    <label class="btn btn-outline-secondary" for="filter-rejected">Hide Rejected</label>

    <input type="checkbox" class="btn-check" id="filter-interviewing" autocomplete="off">
    <label class="btn btn-outline-secondary" for="filter-interviewing">Hide Interviewing</label>

    <input type="checkbox" class="btn-check" id="filter-offer" autocomplete="off">
    <label class="btn btn-outline-secondary" for="filter-offer">Hide Offer</label>

    <button class="btn btn-outline-primary" id="clear-filters">Show All</button>
  </div>
</div>
```

**Accessibility notes:**
- Use role="group" with aria-label on filter controls
- ARIA live region already exists in report.py (id="status-announcer")
- display:none is CORRECT (removes from accessibility tree so screen readers don't announce hidden jobs)
- Checkboxes must announce checked state automatically (native HTML behavior)

### Pattern 2: CSV Export with UTF-8 BOM and RFC 4180 Escaping

**What:** Generate CSV file from visible job data with proper UTF-8 encoding, quote escaping, and formula injection protection, then trigger browser download

**When to use:** Client-side data export from single-file HTML with no server, must work in file:// protocol and open correctly in Excel on Windows

**Example:**

```javascript
// Source: RFC 4180 + OWASP CSV injection prevention + GitHub b4stien/js-csv-encoding
// Escape CSV field per RFC 4180
function escapeCSVField(value) {
  if (value == null) return '';
  var str = String(value);

  // Formula injection protection: prefix dangerous characters with single quote
  if (/^[=+\-@]/.test(str)) {
    str = "'" + str;
  }

  // RFC 4180: Fields with commas, quotes, or newlines must be quoted
  if (str.indexOf(',') !== -1 || str.indexOf('"') !== -1 || str.indexOf('\n') !== -1) {
    // Double-quote escaping: " becomes ""
    str = '"' + str.replace(/"/g, '""') + '"';
  }

  return str;
}

// Generate CSV from visible jobs
function generateCSV() {
  // Get all visible job elements (not display:none)
  var allJobs = document.querySelectorAll('[data-job-key]');
  var visibleJobs = [];

  for (var i = 0; i < allJobs.length; i++) {
    var job = allJobs[i];
    if (job.style.display !== 'none') {
      visibleJobs.push(job);
    }
  }

  if (visibleJobs.length === 0) {
    notyf.error('No visible jobs to export');
    announceToScreenReader('CSV export failed: no visible jobs');
    return;
  }

  // CSV header row
  var headers = [
    'Rank', 'Score', 'New', 'Status', 'Title', 'Company',
    'Salary', 'Type', 'Location', 'Snippet', 'URL'
  ];
  var csvRows = [headers.map(escapeCSVField).join(',')];

  // CSV data rows
  for (var i = 0; i < visibleJobs.length; i++) {
    var job = visibleJobs[i];
    var row = extractJobData(job);
    csvRows.push(row.map(escapeCSVField).join(','));
  }

  // Join rows with CRLF (RFC 4180 line ending)
  var csvContent = csvRows.join('\r\n');

  // UTF-8 BOM prefix for Excel compatibility on Windows
  var BOM = '\uFEFF';
  var csvWithBOM = BOM + csvContent;

  // Create blob and trigger download
  var blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' });
  var url = URL.createObjectURL(blob);

  var link = document.createElement('a');
  link.href = url;
  link.download = 'job-radar-export-' + new Date().toISOString().split('T')[0] + '.csv';
  link.click();

  // Clean up blob URL
  URL.revokeObjectURL(url);

  var msg = 'Exported ' + visibleJobs.length + ' job' + (visibleJobs.length > 1 ? 's' : '') + ' to CSV';
  notyf.success(msg);
  announceToScreenReader(msg);
}

// Extract job data from DOM element
function extractJobData(jobElement) {
  var isTableRow = jobElement.tagName === 'TR';

  if (isTableRow) {
    // Extract from table row cells
    var cells = jobElement.querySelectorAll('td, th');
    return [
      cells[0] ? cells[0].textContent.trim() : '', // Rank
      cells[1] ? cells[1].textContent.replace(/\s+/g, ' ').trim() : '', // Score (clean badge text)
      cells[2] ? cells[2].textContent.trim() : '', // New
      cells[3] ? getStatusText(jobElement) : '', // Status
      cells[4] ? cells[4].textContent.trim() : '', // Title
      cells[5] ? cells[5].textContent.trim() : '', // Company
      cells[6] ? cells[6].textContent.trim() : '', // Salary
      cells[7] ? cells[7].textContent.trim() : '', // Type
      cells[8] ? cells[8].textContent.trim() : '', // Location
      cells[9] ? cells[9].textContent.trim() : '', // Snippet
      jobElement.getAttribute('data-job-url') || '' // URL
    ];
  } else {
    // Extract from card element (hero or recommended)
    var title = jobElement.getAttribute('data-job-title') || '';
    var company = jobElement.getAttribute('data-job-company') || '';
    var score = jobElement.getAttribute('data-score') || '';
    var url = jobElement.getAttribute('data-job-url') || '';
    var status = getStatusText(jobElement);

    // Parse additional fields from card body (complex, may need data attributes)
    return [
      '', // Rank (cards don't have numeric rank)
      score,
      '', // New badge (parse from badge element if needed)
      status,
      title,
      company,
      '', // Salary (extract from card body if needed)
      '', // Type
      '', // Location
      '', // Snippet (cards have full details, not snippet)
      url
    ];
  }
}

// Get status text from job element
function getStatusText(jobElement) {
  var statusBadge = jobElement.querySelector('.status-badge');
  if (statusBadge) {
    return statusBadge.textContent.replace('●', '').trim(); // Remove pending dot if present
  }
  return '';
}
```

**CSV export button placement:**

```html
<!-- Add near "Export Status Updates" button in recommended section -->
<button class="btn btn-sm btn-outline-success export-csv-btn no-print"
        onclick="generateCSV()">
  Export Visible Jobs as CSV
</button>
```

**Critical notes:**
- UTF-8 BOM (`\uFEFF`) MUST be first characters for Excel on Windows to detect UTF-8
- RFC 4180 double-quote escaping: `"` becomes `""` inside quoted fields
- Formula injection: prefix `=`, `+`, `-`, `@` with single quote `'`
- CRLF line endings (`\r\n`) per RFC 4180 spec
- URL.revokeObjectURL() after download to free memory
- Blob + download attribute works in file:// protocol (blob: URLs are protocol-independent)

### Pattern 3: localStorage Error Handling

**What:** Wrap all localStorage operations in try/catch to handle quota exceeded, disabled localStorage (private browsing), and JSON.parse errors

**When to use:** Any localStorage read/write operation (filter state, status tracking)

**Example:**

```javascript
// Source: LogRocket localStorage guide + TrackJS error handling patterns
// Safe localStorage write
function safeLocalStorageSet(key, value) {
  try {
    var jsonValue = JSON.stringify(value);
    localStorage.setItem(key, jsonValue);
    return true;
  } catch (err) {
    if (err.name === 'QuotaExceededError') {
      console.error('[storage] localStorage quota exceeded');
      notyf.error('Storage quota exceeded — cannot save filter state');
    } else if (err.name === 'SecurityError') {
      console.warn('[storage] localStorage disabled (private browsing?)');
    } else {
      console.error('[storage] localStorage.setItem failed:', err);
    }
    return false;
  }
}

// Safe localStorage read
function safeLocalStorageGet(key, defaultValue) {
  try {
    var item = localStorage.getItem(key);
    if (item === null) return defaultValue;
    return JSON.parse(item);
  } catch (err) {
    if (err instanceof SyntaxError) {
      console.warn('[storage] Invalid JSON in localStorage key:', key);
    } else {
      console.error('[storage] localStorage.getItem failed:', err);
    }
    return defaultValue;
  }
}
```

**Why this is critical:** Private browsing modes may disable localStorage, quota exceeded errors happen when storing large data, and corrupt JSON in localStorage causes JSON.parse to throw SyntaxError.

### Pattern 4: ARIA Live Region Announcements for Filter Updates

**What:** Update existing ARIA live region with filter count when filters change so screen reader users hear "Showing X of Y jobs"

**When to use:** Any dynamic content update that sighted users see but screen reader users might miss (filtering, status changes)

**Example:**

```javascript
// Source: MDN ARIA live regions + GOV.UK search accessibility pattern
// Announce filter result count
function announceFilterCount(visibleCount, totalCount) {
  var announcer = document.getElementById('status-announcer');
  if (!announcer) return;

  var message;
  if (visibleCount === totalCount) {
    message = 'Showing all ' + totalCount + ' jobs';
  } else {
    message = 'Showing ' + visibleCount + ' of ' + totalCount + ' jobs';
  }

  // Update live region (role="status" has implicit aria-live="polite")
  announcer.textContent = message;

  // Clear after 1 second so repeated filter changes re-announce
  setTimeout(function() {
    announcer.textContent = '';
  }, 1000);
}
```

**Accessibility notes:**
- Existing `<div id="status-announcer" role="status" aria-live="polite" aria-atomic="true" class="visually-hidden">` in report.py
- role="status" has implicit aria-live="polite" (announces when screen reader is idle)
- aria-atomic="true" makes screen reader announce entire message, not just changed portion
- Clear after 1 second so subsequent filter changes re-announce (screen readers ignore duplicate text)
- Don't announce individual status changes (already handled by existing status management code)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV escaping | Custom string replacement logic | RFC 4180 escapeCSVField function | Edge cases like `"quotes"` in `"quoted, fields"` require double-quote doubling inside already-quoted strings |
| Formula injection detection | Regex for all dangerous formulas | Prefix check for `=+-@` characters | OWASP documented pattern, covers all spreadsheet formula prefixes (Excel, Google Sheets, LibreOffice) |
| UTF-8 encoding for Excel | Plain UTF-8 or charset meta tag | UTF-8 BOM prefix `\uFEFF` | Excel on Windows defaults to windows-1252 without BOM, causing character corruption for international names/companies |
| Filter state persistence | Cookies or URL parameters | localStorage JSON object | localStorage is synchronous, simple API, larger quota than cookies, no URL pollution |
| Blob URL memory management | Keep blob URLs indefinitely | URL.revokeObjectURL() after download | Blob URLs keep data in memory until page unload unless explicitly revoked, causes memory leak on repeated exports |
| Filter visibility detection | Check computed styles or offsetHeight | Track display:none directly | Computed styles are slow, offsetHeight fails for hidden parents, display property is reliable |

**Key insight:** CSV generation is deceptively complex (formula injection, quote escaping, UTF-8 BOM) but has well-established solutions. Filtering is simple (CSS display toggling) but requires ARIA live region announcements and localStorage error handling. Both patterns are proven in production across thousands of sites. The report already has 90% of infrastructure (data attributes, localStorage status map, ARIA live region) — Phase 22 just wires it together.

## Common Pitfalls

### Pitfall 1: Forgetting UTF-8 BOM Causes Excel Character Corruption

**What goes wrong:** CSV exports work in Google Sheets and LibreOffice but show garbled characters (□, �, mojibake) for international names/companies when opened in Excel on Windows.

**Why it happens:** Excel on Windows defaults to windows-1252 (ANSI) encoding when opening CSV files. Without a UTF-8 BOM (Byte Order Mark), Excel doesn't detect UTF-8 and misinterprets multi-byte characters.

**How to avoid:** Prefix CSV content with UTF-8 BOM character `\uFEFF` before creating Blob. Verified pattern: `new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" })`

**Warning signs:** CSV opens correctly in text editors and Google Sheets but shows wrong characters in Excel. Names like "François" become "FranÃ§ois".

**Source:** Shield UI JavaScript Unicode CSV export guide, GitHub b4stien/js-csv-encoding showcase

### Pitfall 2: Not Escaping Double Quotes Breaks CSV Parsing

**What goes wrong:** Job titles or companies containing double quotes (e.g., `Senior Engineer - "Best Team"`) break CSV parsing, causing columns to shift or disappear.

**Why it happens:** CSV uses double quotes to wrap fields containing special characters. A double quote INSIDE a quoted field must be escaped as two double quotes (`""`), per RFC 4180 spec.

**How to avoid:** Use escapeCSVField function that replaces `"` with `""` BEFORE wrapping field in quotes. Pattern: `str.replace(/"/g, '""')` then wrap result in quotes if needed.

**Warning signs:** CSV opens with misaligned columns. Fields with quotes appear truncated. Excel shows "Data may have been lost" warning.

**Source:** RFC 4180 section 2.7, InventiveHQ CSV special characters handling guide

### Pitfall 3: Formula Injection Allows Spreadsheet Code Execution

**What goes wrong:** Job title like `=SUM(A1:A999)` or `=cmd|'/c calc'!A1` executes as formula when CSV is opened in Excel, potentially running malicious code or exposing data.

**Why it happens:** Spreadsheet applications treat cells starting with `=`, `+`, `-`, or `@` as formulas. If user-submitted job title starts with these characters, it becomes executable code.

**How to avoid:** Prefix any field starting with `=`, `+`, `-`, or `@` with a single quote character `'`. Excel/Sheets/LibreOffice treat single-quote prefix as literal text indicator.

**Warning signs:** CSV shows calculated values instead of job titles. Excel displays security warnings about external links. Audit logs show unexpected formula execution.

**Source:** OWASP CSV Injection attack documentation, Cyber Chief best-practice prevention guide

### Pitfall 4: display:none Without aria-hidden Confuses Screen Readers

**What goes wrong:** Filtered-out jobs are hidden visually but screen readers still announce them, making filter appear broken to blind users.

**Why it happens:** CSS display:none removes from visual rendering but older screen readers sometimes cache accessibility tree before CSS applies. Adding aria-hidden="true" ensures all AT respects hidden state.

**How to avoid:** When setting `element.style.display = 'none'`, also set `element.setAttribute('aria-hidden', 'true')`. When showing, remove both: `element.style.display = ''` and `element.removeAttribute('aria-hidden')`.

**Warning signs:** Screen reader announces "50 jobs" but only 10 are visible. VoiceOver rotor shows hidden jobs in list. NVDA browse mode includes filtered items.

**Source:** MDN ARIA aria-hidden documentation (NOTE: Primary research shows display:none DOES remove from accessibility tree in modern browsers, but aria-hidden is defensive coding for older AT)

**CORRECTION BASED ON RESEARCH:** Modern browsers (Chrome, Firefox, Safari 17+) remove display:none elements from accessibility tree automatically. The aria-hidden attribute is OPTIONAL — display:none alone is sufficient. However, adding aria-hidden is defensive coding for older assistive technology and has no negative effects.

### Pitfall 5: Not Clearing ARIA Live Region Prevents Re-Announcement

**What goes wrong:** First filter change announces "Showing 10 of 50 jobs" but subsequent filter changes are silent even though count changes to "Showing 5 of 50 jobs".

**Why it happens:** Screen readers ignore duplicate text in ARIA live regions. If live region still contains "Showing X of Y jobs" when you update it with new count, some AT sees it as unchanged content.

**How to avoid:** Clear ARIA live region text after 1 second using setTimeout. Next update will be treated as new content and announced. Pattern: `setTimeout(function() { announcer.textContent = ''; }, 1000);`

**Warning signs:** First filter works perfectly but subsequent filters are silent. Screen reader users report "filter doesn't seem to be working after first use".

**Source:** Sara Soueidan ARIA live regions guide Part 2, Scott O'Hara dynamic search results patterns

### Pitfall 6: localStorage.setItem Throws QuotaExceededError When Full

**What goes wrong:** Filter state or status updates fail silently (or crash script) when localStorage quota is exceeded (typically 5-10MB per origin).

**Why it happens:** localStorage.setItem() throws QuotaExceededError when storage is full. Without try/catch, this crashes JavaScript execution and breaks all filtering.

**How to avoid:** Wrap ALL localStorage.setItem calls in try/catch. Show user-friendly error via notyf.error(). Check error.name === 'QuotaExceededError' for specific quota message.

**Warning signs:** Filter state doesn't persist across sessions. Console shows "Uncaught QuotaExceededError". Private browsing mode breaks feature entirely (localStorage disabled).

**Source:** TrackJS "Failed to execute 'setItem' on 'Storage'" error guide, LogRocket localStorage error handling

### Pitfall 7: JSON.parse Throws on Corrupted localStorage Data

**What goes wrong:** Page crashes on load with "Uncaught SyntaxError: Unexpected token in JSON" when reading filter state from localStorage.

**Why it happens:** localStorage can contain corrupted data (manual editing via DevTools, interrupted write, encoding issues). JSON.parse() throws SyntaxError on invalid JSON.

**How to avoid:** Wrap JSON.parse(localStorage.getItem(key)) in try/catch. On error, return default value instead of crashing. Log warning to console for debugging.

**Warning signs:** Page loads fine first time but crashes after localStorage is written. Error only happens in specific browser/device. Clearing localStorage "fixes" the issue.

**Source:** Refine "Unexpected token in JSON at position 0 error" guide, Bobby Hadz SyntaxError JSON.parse

### Pitfall 8: Forgetting URL.revokeObjectURL Causes Memory Leak

**What goes wrong:** Repeated CSV exports gradually consume memory until browser tab slows down or crashes, especially with large result sets.

**Why it happens:** URL.createObjectURL() creates a blob URL that references data in memory. Without URL.revokeObjectURL(), the blob stays in memory until page unload. Each export creates a new unreleased blob.

**How to avoid:** Call URL.revokeObjectURL(url) immediately after triggering download (after link.click()). Pattern: `link.click(); URL.revokeObjectURL(url);`

**Warning signs:** Browser memory usage grows with each CSV export. DevTools memory profiler shows accumulating blob URLs. Page becomes sluggish after 10+ exports.

**Source:** MDN URL.createObjectURL documentation, Ben Nadel blob download tutorial

## Code Examples

Verified patterns from official sources and current report implementation:

### Complete Filter Implementation with localStorage Persistence

```javascript
// Source: Composite of W3Schools filter pattern + Phase 21 report.py existing status tracking
// Filter state (persisted to localStorage)
var filterState = {
  hideApplied: false,
  hideRejected: false,
  hideInterviewing: false,
  hideOffer: false
};

// Load filter state on page load
function initializeFilters() {
  loadFilterState();
  renderFilterUI();
  applyFilter();
}

// Load from localStorage
function loadFilterState() {
  try {
    var saved = localStorage.getItem('job-radar-filter-state');
    if (saved) {
      var parsed = JSON.parse(saved);
      // Merge with defaults (defensive against partial state)
      filterState = Object.assign({}, filterState, parsed);
    }
  } catch (err) {
    console.warn('[filter] Failed to load filter state:', err);
    // Use default state
  }
}

// Save to localStorage
function saveFilterState() {
  try {
    localStorage.setItem('job-radar-filter-state', JSON.stringify(filterState));
  } catch (err) {
    console.error('[filter] Failed to save filter state:', err);
    if (err.name === 'QuotaExceededError') {
      notyf.error('Storage quota exceeded');
    }
  }
}

// Render filter UI checkboxes with current state
function renderFilterUI() {
  document.getElementById('filter-applied').checked = filterState.hideApplied;
  document.getElementById('filter-rejected').checked = filterState.hideRejected;
  document.getElementById('filter-interviewing').checked = filterState.hideInterviewing;
  document.getElementById('filter-offer').checked = filterState.hideOffer;
}

// Apply filter to all jobs
function applyFilter() {
  var allJobs = document.querySelectorAll('[data-job-key]');
  var visibleCount = 0;

  // Get application status map (already exists in report.py)
  var statusMap = {};
  try {
    var localData = localStorage.getItem('job-radar-application-status');
    statusMap = localData ? JSON.parse(localData) : {};
  } catch (err) {
    console.warn('[filter] Failed to load status map:', err);
  }

  // Filter each job
  for (var i = 0; i < allJobs.length; i++) {
    var job = allJobs[i];
    var jobKey = job.getAttribute('data-job-key');
    var statusEntry = statusMap[jobKey];
    var status = statusEntry ? statusEntry.status : null;

    var shouldHide = false;
    if (status === 'applied' && filterState.hideApplied) shouldHide = true;
    if (status === 'rejected' && filterState.hideRejected) shouldHide = true;
    if (status === 'interviewing' && filterState.hideInterviewing) shouldHide = true;
    if (status === 'offer' && filterState.hideOffer) shouldHide = true;

    if (shouldHide) {
      job.style.display = 'none';
      job.setAttribute('aria-hidden', 'true');
    } else {
      job.style.display = '';
      job.removeAttribute('aria-hidden');
      visibleCount++;
    }
  }

  // Announce to screen readers
  announceFilterCount(visibleCount, allJobs.length);
}

// Handle filter checkbox change
function handleFilterChange(event) {
  var checkbox = event.target;
  var filterType = checkbox.id.replace('filter-', ''); // "applied", "rejected", etc.
  var stateKey = 'hide' + filterType.charAt(0).toUpperCase() + filterType.slice(1);

  filterState[stateKey] = checkbox.checked;
  saveFilterState();
  applyFilter();
}

// Clear all filters
function clearAllFilters() {
  filterState = {
    hideApplied: false,
    hideRejected: false,
    hideInterviewing: false,
    hideOffer: false
  };
  saveFilterState();
  renderFilterUI();
  applyFilter();

  var msg = 'All filters cleared';
  notyf.success(msg);
  announceToScreenReader(msg);
}

// Announce filter count (uses existing ARIA live region)
function announceFilterCount(visibleCount, totalCount) {
  var announcer = document.getElementById('status-announcer');
  if (!announcer) return;

  var message;
  if (visibleCount === totalCount) {
    message = 'Showing all ' + totalCount + ' jobs';
  } else {
    message = 'Showing ' + visibleCount + ' of ' + totalCount + ' jobs';
  }

  announcer.textContent = message;
  setTimeout(function() { announcer.textContent = ''; }, 1000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  initializeFilters();

  // Attach event listeners to filter checkboxes
  document.getElementById('filter-applied').addEventListener('change', handleFilterChange);
  document.getElementById('filter-rejected').addEventListener('change', handleFilterChange);
  document.getElementById('filter-interviewing').addEventListener('change', handleFilterChange);
  document.getElementById('filter-offer').addEventListener('change', handleFilterChange);
  document.getElementById('clear-filters').addEventListener('click', clearAllFilters);

  // Re-apply filter when status changes (integrate with existing status management)
  // NOTE: This would be added to the existing status change handler
});
```

### Complete CSV Export with UTF-8 BOM and Security

```javascript
// Source: RFC 4180 + OWASP CSV injection + Shield UI Unicode CSV + MDN Blob API
// Escape CSV field per RFC 4180 with formula injection protection
function escapeCSVField(value) {
  if (value == null || value === '') return '';
  var str = String(value);

  // Formula injection protection (OWASP pattern)
  if (/^[=+\-@]/.test(str)) {
    str = "'" + str;
  }

  // RFC 4180: Escape if contains comma, quote, or newline
  var needsQuoting = str.indexOf(',') !== -1 ||
                     str.indexOf('"') !== -1 ||
                     str.indexOf('\n') !== -1 ||
                     str.indexOf('\r') !== -1;

  if (needsQuoting) {
    // Double-quote escaping
    str = '"' + str.replace(/"/g, '""') + '"';
  }

  return str;
}

// Extract job data from DOM element
function extractJobDataFromElement(jobElement, rank) {
  var isTableRow = jobElement.tagName === 'TR';

  if (isTableRow) {
    // Extract from table row
    var cells = jobElement.querySelectorAll('td, th');

    // Clean score badge text (remove "Score" prefix and "/5.0" suffix)
    var scoreText = cells[1] ? cells[1].textContent.trim() : '';
    var scoreMatch = scoreText.match(/(\d+\.\d+)/);
    var score = scoreMatch ? scoreMatch[1] : '';

    // Get status badge text or empty
    var statusBadge = jobElement.querySelector('.status-badge');
    var status = statusBadge ? statusBadge.textContent.replace(/●/g, '').trim() : '';

    // Check for NEW badge
    var newBadge = cells[2] ? cells[2].querySelector('.badge.bg-primary') : null;
    var isNew = newBadge ? 'NEW' : '';

    return [
      rank,
      score,
      isNew,
      status,
      cells[4] ? cells[4].textContent.trim() : '', // Title
      cells[5] ? cells[5].textContent.trim() : '', // Company
      cells[6] ? cells[6].textContent.trim() : '', // Salary
      cells[7] ? cells[7].textContent.trim() : '', // Type
      cells[8] ? cells[8].textContent.trim() : '', // Location
      cells[9] ? cells[9].textContent.trim() : '', // Snippet
      jobElement.getAttribute('data-job-url') || ''  // URL
    ];
  } else {
    // Extract from card element (hero or recommended section)
    var title = jobElement.getAttribute('data-job-title') || '';
    var company = jobElement.getAttribute('data-job-company') || '';
    var score = jobElement.getAttribute('data-score') || '';
    var url = jobElement.getAttribute('data-job-url') || '';

    var statusBadge = jobElement.querySelector('.status-badge');
    var status = statusBadge ? statusBadge.textContent.replace(/●/g, '').trim() : '';

    var newBadge = jobElement.querySelector('.badge.bg-primary');
    var isNew = newBadge ? 'NEW' : '';

    // Cards have full details in body, extract key fields
    var cardBody = jobElement.querySelector('.card-body');
    var salary = '';
    var location = '';
    var arrangement = '';

    if (cardBody) {
      var items = cardBody.querySelectorAll('li');
      for (var i = 0; i < items.length; i++) {
        var text = items[i].textContent;
        if (text.indexOf('Rate/Salary:') !== -1) {
          salary = text.replace('Rate/Salary:', '').trim();
        } else if (text.indexOf('Location:') !== -1) {
          location = text.replace('Location:', '').trim();
        }
      }
    }

    return [
      rank,
      score,
      isNew,
      status,
      title,
      company,
      salary,
      arrangement || location, // Type column shows arrangement or location
      location,
      '', // Snippet (cards don't have snippet)
      url
    ];
  }
}

// Generate and download CSV
function exportVisibleJobsToCSV() {
  // Get all visible jobs (not display:none)
  var allJobs = document.querySelectorAll('[data-job-key]');
  var visibleJobs = [];

  for (var i = 0; i < allJobs.length; i++) {
    if (allJobs[i].style.display !== 'none') {
      visibleJobs.push(allJobs[i]);
    }
  }

  if (visibleJobs.length === 0) {
    var msg = 'No visible jobs to export';
    notyf.error(msg);
    announceToScreenReader(msg);
    return;
  }

  // CSV header row
  var headers = [
    'Rank', 'Score', 'New', 'Status', 'Title', 'Company',
    'Salary', 'Type', 'Location', 'Snippet', 'URL'
  ];

  var csvRows = [];
  csvRows.push(headers.map(escapeCSVField).join(','));

  // CSV data rows
  for (var i = 0; i < visibleJobs.length; i++) {
    var jobData = extractJobDataFromElement(visibleJobs[i], i + 1);
    csvRows.push(jobData.map(escapeCSVField).join(','));
  }

  // Join with CRLF per RFC 4180
  var csvContent = csvRows.join('\r\n');

  // Add UTF-8 BOM for Excel compatibility
  var BOM = '\uFEFF';
  var csvWithBOM = BOM + csvContent;

  // Create blob and download
  var blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' });
  var url = URL.createObjectURL(blob);

  var link = document.createElement('a');
  link.href = url;
  link.download = 'job-radar-export-' + new Date().toISOString().split('T')[0] + '.csv';
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Clean up blob URL
  URL.revokeObjectURL(url);

  var msg = 'Exported ' + visibleJobs.length + ' job' + (visibleJobs.length > 1 ? 's' : '') + ' to CSV';
  notyf.success(msg);
  announceToScreenReader(msg);
}
```

### Filter UI HTML (Add to report.py header section)

```html
<!-- Source: Bootstrap 5.3 button group + WCAG accessible forms -->
<!-- Add this before the "All Results" table section -->
<div class="mb-4" role="region" aria-labelledby="filter-heading">
  <h3 id="filter-heading" class="h5">Filter by Status</h3>
  <div class="d-flex align-items-center gap-2 flex-wrap">
    <div class="btn-group" role="group" aria-label="Status filter checkboxes">
      <input type="checkbox" class="btn-check" id="filter-applied" autocomplete="off">
      <label class="btn btn-outline-secondary" for="filter-applied">Hide Applied</label>

      <input type="checkbox" class="btn-check" id="filter-rejected" autocomplete="off">
      <label class="btn btn-outline-secondary" for="filter-rejected">Hide Rejected</label>

      <input type="checkbox" class="btn-check" id="filter-interviewing" autocomplete="off">
      <label class="btn btn-outline-secondary" for="filter-interviewing">Hide Interviewing</label>

      <input type="checkbox" class="btn-check" id="filter-offer" autocomplete="off">
      <label class="btn btn-outline-secondary" for="filter-offer">Hide Offer</label>
    </div>

    <button class="btn btn-outline-primary" id="clear-filters" aria-label="Clear all filters and show all jobs">
      Show All
    </button>

    <button class="btn btn-outline-success export-csv-btn no-print" onclick="exportVisibleJobsToCSV()" aria-label="Export visible jobs to CSV file">
      Export CSV
    </button>
  </div>
  <p class="text-muted small mt-2 mb-0">Filter applies to jobs with status set. Unset jobs are always visible.</p>
</div>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Server-side CSV generation | Client-side Blob + download attribute | ~2015-2018 | Enables CSV export in static sites and file:// protocol, no server required |
| jQuery table filtering plugins | Vanilla JavaScript with querySelectorAll | ~2018-2020 | Zero dependencies, smaller bundle size, native browser performance |
| Plain UTF-8 CSV | UTF-8 with BOM (`\uFEFF`) | ~2016 (Excel 2007+ on Windows) | Fixes character corruption in Excel on Windows for international characters |
| Ignore CSV formula injection | OWASP prefix mitigation (`'=SUM()`) | ~2014-2017 (OWASP documented) | Prevents code execution when CSV opened in Excel/Sheets |
| sessionStorage for filter state | localStorage with persistence | ~2012-2015 | Filter state persists across browser sessions, better UX |
| Manual quote escaping | RFC 4180 double-quote doubling | 2005 (RFC published) | Standard CSV escaping, works across all parsers |
| visibility:hidden for filtering | display:none | ~2014-2018 | Removes from accessibility tree (correct for filtering), screen readers only hear visible results |
| execCommand('copy') fallback | Clipboard API primary | ~2021-2023 | Already used in report.py for URL copying, secure context only |
| data URLs for downloads | Blob URLs with revokeObjectURL | ~2015-2018 | Better memory management, works for large files, cleaner URLs |

**Deprecated/outdated:**

- **jQuery table filter plugins:** Modern vanilla JS with querySelectorAll is faster and has zero dependencies. Bootstrap 5 already provides button styling.
- **Tab character for formula injection:** Single quote prefix is simpler and works across all spreadsheet apps (Excel, Google Sheets, LibreOffice Calc).
- **window.btoa() for CSV encoding:** Blob API with UTF-8 charset is more reliable and handles Unicode correctly without base64 bloat.
- **Inline data URLs:** Blob URLs are more efficient for large CSVs and allow memory cleanup with revokeObjectURL().
- **aria-live="assertive" for filter announcements:** aria-live="polite" (implicit in role="status") is less disruptive and sufficient for non-critical updates.

## Open Questions

1. **Should CSV export include only table jobs or also hero/recommended cards?**
   - What we know: Table has all jobs. Hero and recommended sections duplicate top-scoring jobs with more details.
   - What's unclear: Whether users want full details from cards or consistent table format.
   - Recommendation: Export ALL visible jobs (table rows + cards) to avoid confusion. Cards have richer data (talking points, full details), so include both sections. Add "Section" column to CSV indicating "Hero", "Recommended", or "Other".

2. **Should filters persist across different report files or be per-report?**
   - What we know: localStorage is origin-scoped (same protocol + domain + port).
   - What's unclear: If user opens `jobs_2026-02-11.html` with "Hide Applied" checked, should `jobs_2026-02-12.html` also have that filter?
   - Recommendation: Use SHARED filter state across all reports from same origin (file:// or same directory). This is better UX — user sets preference once. Use localStorage key `job-radar-filter-state` (no timestamp).

3. **Should "Show All" button also clear application statuses or just filters?**
   - What we know: "Show All" clears hideApplied/hideRejected/etc. filters. Application statuses are separate (status dropdown).
   - What's unclear: Whether "Show All" should be "reset all state" or just "reset filters".
   - Recommendation: "Show All" ONLY clears filters, NOT application statuses. Status is persistent job metadata. Filter is temporary view preference. Keep separate. Add tooltip: "Clears filters to show all jobs (statuses remain unchanged)".

4. **Should CSV export respect current sort order or always export rank order?**
   - What we know: Table is sorted by score (descending) in generated HTML. No client-side sorting feature exists.
   - What's unclear: Future phases might add sortable columns. Should CSV export match visual order?
   - Recommendation: Export in DOM order (querySelectorAll returns document order). Add "Rank" column based on position in exported list. If sorting is added later, CSV will export sorted order automatically.

5. **Should filter counts show "10 of 50 jobs" or "10 jobs (40 hidden)"?**
   - What we know: Both convey same information. Screen readers will announce either.
   - What's unclear: Which is clearer for users.
   - Recommendation: Use "Showing X of Y jobs" format. This is standard pattern (see GOV.UK search, Google results). More intuitive than "X hidden" which requires mental math to know how many visible.

## Sources

### Primary (HIGH confidence)

- [RFC 4180: Common Format and MIME Type for Comma-Separated Values (CSV) Files](https://datatracker.ietf.org/doc/html/rfc4180) - Official CSV specification
- [OWASP CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection) - Formula injection attack documentation
- [MDN: ARIA live regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions) - Official ARIA live region specification
- [MDN: URL.createObjectURL()](https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static) - Blob URL creation API
- [MDN: Blob](https://developer.mozilla.org/en-US/docs/Web/API/Blob) - Binary data API
- [MDN: Array.prototype.filter()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/filter) - JavaScript filtering
- [W3C ARIA22: Using role=status](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA22.html) - Screen reader announcements
- [Can I Use: download attribute](https://caniuse.com/download) - Browser support for HTML5 download

### Secondary (MEDIUM confidence)

- [InventiveHQ: Handling Special Characters in CSV Files](https://inventivehq.com/blog/handling-special-characters-in-csv-files) - RFC 4180 practical guide
- [Shield UI: JavaScript CSV Export with Unicode Symbols](https://www.shieldui.com/javascript-unicode-csv-export) - UTF-8 BOM implementation
- [GitHub: b4stien/js-csv-encoding](https://github.com/b4stien/js-csv-encoding) - CSV encoding showcase
- [Cyber Chief: CSV Formula Injection Prevention](https://www.cyberchief.ai/2024/09/csv-formula-injection-attacks.html) - Best-practice methods
- [Sara Soueidan: Accessible Notifications with ARIA Live Regions Part 1](https://www.sarasoueidan.com/blog/accessible-notifications-with-aria-live-regions-part-1/) - ARIA patterns
- [Sara Soueidan: Accessible Notifications with ARIA Live Regions Part 2](https://www.sarasoueidan.com/blog/accessible-notifications-with-aria-live-regions-part-2/) - ARIA implementation
- [GOV.UK: Improving Accessibility on Search](https://technology.blog.gov.uk/2014/08/14/improving-accessibility-on-gov-uk-search/) - Filter accessibility pattern
- [Scott O'Hara: Considering Dynamic Search Results](https://www.scottohara.me/blog/2022/02/05/dynamic-results.html) - Live region best practices
- [LogRocket: Storing and Retrieving JavaScript Objects in localStorage](https://blog.logrocket.com/storing-retrieving-javascript-objects-localstorage/) - Error handling
- [TrackJS: Failed to Execute 'setItem' on 'Storage'](https://trackjs.com/javascript-errors/failed-to-execute-setitem-on-storage/) - Quota errors
- [W3Schools: How To Create a Filter/Search Table](https://www.w3schools.com/howto/howto_js_filter_table.asp) - Basic filtering pattern
- [Ben Nadel: Downloading Text Using Blobs and createObjectURL](https://www.bennadel.com/blog/3472-downloading-text-using-blobs-url-createobjecturl-and-the-anchor-download-attribute-in-javascript.htm) - Download implementation
- [Atomic Accessibility: Select Dropdown WCAG Checklist](https://www.atomica11y.com/accessible-design/select/) - Accessible dropdowns
- [TheWCAG: Accessible Dropdowns & Selects Example 2026](https://www.thewcag.com/examples/dropdowns-selects) - WCAG 2.2 compliance
- [TheAdminBar: Making Search & Filters Accessible](https://theadminbar.com/accessibility-weekly/accessible-search-and-filter/) - Filter accessibility tips

### Tertiary (LOW confidence - verification recommended)

- [CodeHim: Filter Table with Select Option in JavaScript](https://codehim.com/vanilla-javascript/filter-table-with-select-option-in-javascript/) - Community example
- [Bobby Hadz: Filter Array with Multiple Conditions](https://bobbyhadz.com/blog/javascript-filter-array-multiple-conditions) - JavaScript patterns
- [Bobby Hadz: SyntaxError JSON.parse](https://bobbyhadz.com/blog/javascript-syntaxerror-json-parse-unexpected-character) - Error handling
- [Refine: Unexpected Token in JSON](https://refine.dev/blog/unexpected-token-in-json-at-position-0-error/) - JSON errors
- [Sling Academy: Filtering Lists via JavaScript](https://www.slingacademy.com/article/filtering-lists-show-and-hide-items-via-javascript-dom-updates/) - DOM updates
- [Medium: CSV Injection by Sanskar Jain](https://medium.com/@vulnerable19/csv-injection-d1507ff859cf) - Security overview
- [xCloud: Comprehensive Guide On CSV Injection](https://xcloud.host/csv-injection-and-how-to-prevent-it/) - Prevention guide

## Metadata

**Confidence breakdown:**

- **Standard stack:** HIGH - All features are native browser APIs (Blob, localStorage, Array.filter, display:none) with excellent documentation on MDN and W3C specs. No external dependencies.
- **CSV generation:** HIGH - RFC 4180 is official spec. UTF-8 BOM pattern verified across Shield UI guide and GitHub examples. OWASP formula injection is authoritative source.
- **Filtering patterns:** HIGH - W3Schools, MDN, and accessibility guides (Sara Soueidan, Scott O'Hara, GOV.UK) provide consistent patterns. display:none + ARIA live regions is proven approach.
- **ARIA live regions:** HIGH - Existing report.py already has role="status" live region. MDN, W3C, and Sara Soueidan sources are authoritative. Pattern is WCAG 2.2 compliant.
- **Error handling:** MEDIUM - localStorage error patterns from LogRocket and TrackJS are practical but not official spec. Verified across multiple sources.
- **Browser support:** HIGH - All APIs (Blob, localStorage, download attribute) are supported in modern browsers. Can I Use shows 97%+ support for download attribute.

**Research date:** 2026-02-11

**Valid until:** 2026-05-11 (90 days) - JavaScript filtering patterns are stable. CSV standards (RFC 4180, UTF-8 BOM) are unchanging. Browser APIs (Blob, localStorage) are mature. ARIA 1.3 is stable. Main evolution would be new browser APIs (File System Access API) but not needed for this use case.
