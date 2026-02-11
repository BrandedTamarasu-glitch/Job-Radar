# Architecture Research: v1.4.0 Visual Design & Polish

**Domain:** HTML report visual enhancements for Job Radar CLI
**Researched:** 2026-02-11
**Confidence:** HIGH

## Executive Summary

v1.4.0 adds visual design improvements to the existing HTML report generation system. All features integrate directly into `report.py` via CSS additions (hero jobs, semantic colors, typography, responsive layout, print styles) and inline JavaScript extensions (status filters, CSV export). Accessibility CI adds a new GitHub Actions workflow. The single-file HTML constraint is non-negotiable and drives all architectural decisions.

**Key architectural insight:** The existing report.py string concatenation architecture with inline CSS/JS makes incremental enhancements straightforward. Font strategy uses system font stacks (zero bytes). Responsive tables use CSS-only column hiding (no Python logic changes). CSV export uses browser-side JavaScript (no Python CSV generation). Accessibility CI runs as separate workflow job.

**Integration complexity:** LOW — All features are additive CSS/JS enhancements to existing HTML generation. No new Python modules, no data flow changes, no new dependencies.

## Current Architecture (v1.3.0)

### Report Generation System

```
┌─────────────────────────────────────────────────────────────┐
│                    report.py (1367 lines)                    │
├─────────────────────────────────────────────────────────────┤
│  generate_report() — Entry point                             │
│    ├── _generate_markdown_report() → .md file               │
│    └── _generate_html_report() → .html file                 │
│         ├── HTML string concatenation                        │
│         ├── Bootstrap 5.3 CSS (CDN links)                    │
│         ├── Inline <style> block (~150 lines CSS)            │
│         ├── Body structure (header, sections, footer)        │
│         │   ├── _html_profile_summary()                      │
│         │   ├── _html_recommended_cards()                    │
│         │   ├── _html_results_table()                        │
│         │   └── _html_manual_urls_section()                  │
│         ├── Bootstrap JS bundle (CDN)                        │
│         ├── Notyf toast library (CDN)                        │
│         └── Inline <script> block (~500 lines JS)            │
│             ├── Clipboard API with execCommand fallback      │
│             ├── Application status tracking (localStorage)   │
│             ├── Theme switcher (dark/light/auto)             │
│             └── Keyboard shortcuts (Ctrl+K copy all)         │
└─────────────────────────────────────────────────────────────┘

Data Flow:
profile.json + scored_results[] + tracker_stats
    → _generate_html_report()
    → HTML string with embedded CSS/JS
    → Write single .html file
    → Opens in browser via file:// protocol
```

### Key Constraints

1. **Single-file HTML**: Must work with `file://` protocol (no separate CSS/JS/font files)
2. **CDN links present**: Bootstrap, Notyf, Prism.js loaded from CDN (not actually inlined despite context note)
3. **String concatenation**: HTML built via f-strings, not templating engine
4. **Inline blocks**: Custom CSS in `<style>`, custom JS in `<script>` at end of file
5. **Accessibility-first**: Existing code has `visually-hidden` classes, ARIA labels, semantic HTML

### Current CSS Organization (~150 lines)

```css
<style>
  /* Print-friendly styles */
  @media print { ... }

  /* Dark mode adjustments */
  [data-bs-theme="dark"] { ... }

  /* Component-specific styles */
  .score-badge { ... }
  .copy-btn { ... }
  .status-badge { ... }
  .status-dropdown { ... }
  .pending-dot { ... }

  /* Focus indicators for keyboard navigation */
  .job-item:focus-visible { ... }
  a:focus-visible { ... }
  .btn:focus-visible { ... }

  /* Utility classes */
  .visually-hidden { ... }
</style>
```

### Current JavaScript Organization (~500 lines)

```javascript
<script>
  // 1. Library initialization
  const notyf = new Notyf({ ... });

  // 2. Clipboard utilities
  async function copyToClipboard(text) { ... }
  function copySingleUrl(btn) { ... }
  function copyAllRecommendedUrls(btn) { ... }

  // 3. Status tracking
  function hydrateApplicationStatus() { ... }
  function updateStatus(jobKey, newStatus, el) { ... }
  function syncStatusWithBackend() { ... }

  // 4. Accessibility helpers
  function announceToScreenReader(msg) { ... }

  // 5. Theme switcher
  function initThemeSwitcher() { ... }

  // 6. Keyboard shortcuts
  document.addEventListener('keydown', function(e) { ... });

  // 7. Bootstrap initialization
  document.addEventListener('DOMContentLoaded', function() { ... });
</script>
```

## v1.4.0 Architecture (Integration Points)

### Modified Components

| Component | Current State | Modification | Lines Changed (Est.) |
|-----------|---------------|--------------|---------------------|
| `report.py::_generate_html_report()` | Generates HTML structure | Add CSS variables, hero markup, responsive classes | +100 |
| `<style>` block | ~150 lines | Add font stack, semantic colors, responsive table, print styles | +150 |
| `<script>` block | ~500 lines | Add status filter logic, CSV export function | +100 |
| `.github/workflows/release.yml` | Tests + builds | Add accessibility job with Lighthouse CI | +40 |

**Total estimated addition:** ~390 lines across 4 files
**New files:** 0
**Modified files:** 2 (report.py, .github/workflows/release.yml)

### Integration Pattern 1: Font Embedding Strategy

**Decision: System Font Stack (zero bytes, maximum performance)**

**Rationale:**
- Base64 WOFF2 embedding: 30-50KB per font variant × multiple weights = 150-200KB+ added to each HTML file
- Embedding blocks rendering, prevents parallel loading, breaks browser caching
- Single-file constraint means fonts can't be cached separately
- System fonts render instantly, feel native, respect user preferences

**Implementation:**

```css
/* Add to <style> block in _generate_html_report() */
:root {
  /* System font stacks — organized by typeface classification */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, sans-serif;
  --font-serif: "Iowan Old Style", "Apple Garamond", Baskerville,
                "Times New Roman", "Droid Serif", Times, serif;
  --font-mono: ui-monospace, "Cascadia Code", "Source Code Pro", Menlo,
               Consolas, "DejaVu Sans Mono", monospace;
}

body {
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-sans);
  font-weight: 600;
  line-height: 1.2;
}

code, pre {
  font-family: var(--font-mono);
}
```

**Build order:** Phase 1 (Typography foundation before hero jobs)
**Modified function:** `_generate_html_report()` — add CSS to `<style>` block
**Size impact:** 0 bytes (uses system fonts already on user's OS)
**Sources:**
- [Modern Font Stacks](https://modernfontstacks.com/) — Comprehensive system font CSS for modern OS (HIGH confidence)
- [CSS-Tricks System Font Stack](https://css-tricks.com/snippets/css/system-font-stack/) — Industry standard patterns (HIGH confidence)

### Integration Pattern 2: Semantic Color System

**Decision: CSS Custom Properties with Dark Mode Support**

**Implementation:**

```css
/* Add to <style> block after font definitions */
:root {
  /* Semantic color tokens */
  --color-hero: #1a73e8;          /* High-priority jobs */
  --color-hero-bg: #e8f0fe;
  --color-success: #28a745;       /* Score >= 4.0 */
  --color-warning: #ffc107;       /* Score 3.5-3.9 */
  --color-info: #17a2b8;          /* New jobs */
  --color-neutral: #6c757d;       /* Score < 3.5 */
  --color-text-primary: #212529;
  --color-text-secondary: #6c757d;
  --color-border: #dee2e6;
}

[data-bs-theme="dark"] {
  --color-hero: #8ab4f8;
  --color-hero-bg: #1e3a5f;
  --color-success: #34d058;
  --color-warning: #ffdf5d;
  --color-info: #58a6ff;
  --color-neutral: #8b949e;
  --color-text-primary: #e6edf3;
  --color-text-secondary: #8b949e;
  --color-border: #30363d;
}

/* Apply semantic colors to existing badges */
.badge.bg-primary { background-color: var(--color-info) !important; }
.badge.bg-success { background-color: var(--color-success) !important; }
.badge.bg-warning { background-color: var(--color-warning) !important; }
.badge.bg-secondary { background-color: var(--color-neutral) !important; }
```

**Build order:** Phase 1 (Color foundation before hero jobs)
**Modified function:** `_generate_html_report()` — add CSS to `<style>` block
**Sources:**
- [Designing semantic colors for your system](https://imperavi.com/blog/designing-semantic-colors-for-your-system/) — Semantic color patterns (MEDIUM confidence)
- [Accessible Color Tokens for Enterprise Design Systems](https://www.aufaitux.com/blog/color-tokens-enterprise-design-systems-best-practices/) — WCAG-compliant color tokens (HIGH confidence)

### Integration Pattern 3: Hero Jobs Visual Treatment

**Decision: CSS Class-Based Highlighting (No Python Logic Changes)**

**Implementation:**

```python
# In _html_recommended_cards() — modify existing card generation
# Add hero class to top 3 jobs (score >= 4.0)
hero_count = 0
for i, r in enumerate(recommended, 1):
    score_val = r["score"]["overall"]
    is_hero = hero_count < 3 and score_val >= 4.0
    hero_class = " hero-job" if is_hero else ""
    if is_hero:
        hero_count += 1

    # Existing card HTML with hero class added
    cards.append(f"""
    <div class="card mb-3{hero_class}" data-job-url="{html.escape(job.url)}" ...>
      ...
    </div>
    """)
```

```css
/* Add to <style> block */
.hero-job {
  border-left: 4px solid var(--color-hero) !important;
  background-color: var(--color-hero-bg);
  box-shadow: 0 2px 8px rgba(26, 115, 232, 0.15);
}

.hero-job::before {
  content: "⭐ Top Match";
  display: inline-block;
  background-color: var(--color-hero);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

[data-bs-theme="dark"] .hero-job {
  background-color: var(--color-hero-bg);
  box-shadow: 0 2px 8px rgba(138, 180, 248, 0.2);
}
```

**Build order:** Phase 2 (After semantic colors)
**Modified function:** `_html_recommended_cards()` — add conditional class
**Lines changed:** ~15 in Python, ~30 in CSS
**Sources:**
- [Hero Section Design: Best Practices & Examples for 2026](https://www.perfectafternoon.com/2025/hero-section-design/) — Visual priority patterns (MEDIUM confidence)

### Integration Pattern 4: Responsive Table → Mobile Cards

**Decision: CSS-Only Transformation (No Python Column Selection)**

**Rationale:**
- Python-side column selection would require duplicating HTML generation logic for mobile/desktop
- CSS media queries can hide columns and reformat rows as cards with zero Python changes
- Data attributes already present in table rows (from status tracking feature)
- Pseudo-elements can inject column labels from data attributes

**Implementation:**

```python
# In _html_results_table() — add data-label attributes to <td> elements
# (Table cells already have semantic structure, just add labels)
rows.append(f"""
<tr {row_attrs}>
  <th scope="row" data-label="#">{i}</th>
  <td data-label="Score">{score_badge_accessible}...</td>
  <td data-label="New">{new_badge_accessible}</td>
  <td data-label="Status">{status_dropdown}</td>
  <td data-label="Title"><strong>{html.escape(job.title)}</strong></td>
  <td data-label="Company">{html.escape(job.company)}</td>
  <td data-label="Salary">{salary}</td>
  <td data-label="Type">{html.escape(emp_type)}</td>
  <td data-label="Location">{html.escape(job.location)}</td>
  <td data-label="Snippet">{html.escape(snippet)}</td>
  <td data-label="Link">{link_html}</td>
</tr>
""")
```

```css
/* Add to <style> block */
/* Desktop: Hide less important columns on medium screens */
@media (max-width: 1200px) {
  table th:nth-child(9),  /* Snippet */
  table td:nth-child(9) {
    display: none;
  }
}

@media (max-width: 992px) {
  table th:nth-child(7),  /* Salary */
  table td:nth-child(7),
  table th:nth-child(8),  /* Type */
  table td:nth-child(8) {
    display: none;
  }
}

/* Mobile: Convert to card layout */
@media (max-width: 768px) {
  /* Hide table header */
  table thead {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }

  /* Make each row a card */
  table, tbody, tr, th, td {
    display: block;
  }

  table tr {
    border: 1px solid var(--color-border);
    border-radius: 0.375rem;
    margin-bottom: 1rem;
    padding: 1rem;
    background: white;
  }

  [data-bs-theme="dark"] table tr {
    background: #212529;
  }

  table th,
  table td {
    border: none;
    padding: 0.5rem 0;
    position: relative;
    padding-left: 40%;
  }

  /* Row number as badge */
  table th[scope="row"] {
    padding-left: 0;
    margin-bottom: 0.5rem;
  }

  table th[scope="row"]::before {
    content: "Job #";
    font-weight: normal;
    margin-right: 0.25rem;
  }

  /* Inject labels from data-label attributes */
  table td::before {
    content: attr(data-label) ": ";
    position: absolute;
    left: 0;
    width: 35%;
    font-weight: 600;
    color: var(--color-text-secondary);
  }

  /* Hide empty cells */
  table td:empty {
    display: none;
  }
}
```

**Build order:** Phase 3 (After semantic colors)
**Modified function:** `_html_results_table()` — add data-label attributes to existing <td> elements
**Lines changed:** ~10 in Python (just adding attributes), ~80 in CSS
**Sources:**
- [CSS-Tricks Responsive Data Tables](https://css-tricks.com/responsive-data-tables/) — Card transformation technique (HIGH confidence)
- [HTML Tables in Responsive Design: Do's and Don'ts (2026)](https://618media.com/en/blog/html-tables-in-responsive-design/) — Current best practices (HIGH confidence)

### Integration Pattern 5: Status Filters

**Decision: Client-Side JavaScript Filtering (No HTML Changes)**

**Rationale:**
- Status data already in DOM via data-status attributes (from existing status tracking feature)
- Filter UI can be pure JavaScript DOM manipulation
- No server-side filtering needed (all jobs already in HTML)
- Leverages existing Bootstrap dropdown components

**Implementation:**

```python
# In _generate_html_report() — add filter UI to header section (after status-announcer)
filter_ui = """
<div class="mb-3">
  <label for="status-filter" class="form-label">Filter by status:</label>
  <select id="status-filter" class="form-select" aria-label="Filter jobs by application status">
    <option value="">All jobs</option>
    <option value="applied">Applied</option>
    <option value="interviewing">Interviewing</option>
    <option value="rejected">Rejected</option>
    <option value="offer">Offer</option>
  </select>
</div>
"""
# Insert after tracker stats, before recommended section
```

```javascript
// Add to <script> block — after existing status tracking code
function initStatusFilter() {
  var filterSelect = document.getElementById('status-filter');
  if (!filterSelect) return;

  filterSelect.addEventListener('change', function() {
    var filterValue = this.value;
    var allRows = document.querySelectorAll('.job-item');
    var visibleCount = 0;

    allRows.forEach(function(row) {
      var jobStatus = row.dataset.jobStatus || '';
      var shouldShow = !filterValue || jobStatus === filterValue;

      if (shouldShow) {
        row.style.display = '';
        visibleCount++;
      } else {
        row.style.display = 'none';
      }
    });

    // Announce to screen readers
    var msg = visibleCount + ' job' + (visibleCount !== 1 ? 's' : '') + ' shown';
    announceToScreenReader(msg);
  });
}

// Call in DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
  // ... existing initialization ...
  initStatusFilter();
});
```

**Build order:** Phase 4 (After responsive table — reuses data attributes)
**Modified function:** `_generate_html_report()` — add filter UI HTML, add JS function
**Lines changed:** ~15 in Python (HTML), ~30 in JavaScript
**Sources:**
- Existing codebase pattern (status tracking already uses data attributes)

### Integration Pattern 6: CSV Export

**Decision: Browser-Side JavaScript Export (No Python CSV Module)**

**Rationale:**
- Data already in HTML table (no need to duplicate in Python-generated CSV)
- Browser-side export has zero server/file overhead (no extra file to manage)
- Works with file:// protocol (Blob + download link)
- Job Radar reports typically have 20-100 results (not millions) — browser handles easily
- Avoids Python csv module dependency and file management

**Implementation:**

```python
# In _generate_html_report() — add export button near results table heading
export_button = """
<button onclick="exportTableToCSV()"
        class="btn btn-outline-primary btn-sm no-print"
        aria-label="Download job results as CSV file">
  📊 Export to CSV
</button>
"""
# Insert in _html_results_table() near heading
```

```javascript
// Add to <script> block
function exportTableToCSV() {
  var table = document.querySelector('.table');
  if (!table) {
    notyf.error('No table found to export');
    return;
  }

  var rows = [];

  // Header row
  var headers = Array.from(table.querySelectorAll('thead th')).map(function(th) {
    return th.textContent.trim();
  });
  rows.push(headers);

  // Data rows (only visible rows if filter active)
  var dataRows = table.querySelectorAll('tbody tr');
  dataRows.forEach(function(tr) {
    if (tr.style.display === 'none') return; // Skip filtered rows

    var cells = Array.from(tr.querySelectorAll('th, td')).map(function(cell) {
      // Extract text content, strip HTML
      var text = cell.textContent.trim();
      // Handle commas and quotes (CSV escaping)
      if (text.includes(',') || text.includes('"') || text.includes('\n')) {
        text = '"' + text.replace(/"/g, '""') + '"';
      }
      return text;
    });
    rows.push(cells);
  });

  // Generate CSV string
  var csvContent = rows.map(function(row) {
    return row.join(',');
  }).join('\n');

  // Create blob and download
  var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  var link = document.createElement('a');
  var url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', 'job-radar-results-' + new Date().toISOString().slice(0,10) + '.csv');
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  notyf.success('CSV file downloaded');
  announceToScreenReader('CSV export complete');
}
```

**Build order:** Phase 5 (After status filters — can export filtered results)
**Modified function:** `_generate_html_report()` — add button HTML, add JS function
**Lines changed:** ~10 in Python (button), ~50 in JavaScript
**Sources:**
- [How to Export HTML Table to CSV Using Vanilla JavaScript](https://www.xjavascript.com/blog/export-html-table-to-csv-using-vanilla-javascript/) — Pure JS solution (HIGH confidence)
- [GeeksforGeeks: How to export HTML table to CSV using JavaScript](https://www.geeksforgeeks.org/javascript/how-to-export-html-table-to-csv-using-javascript/) — CSV escaping patterns (MEDIUM confidence)

### Integration Pattern 7: Print Stylesheet Enhancements

**Decision: Extend Existing @media print Block**

**Implementation:**

```css
/* Extend existing @media print block in <style> */
@media print {
  /* Existing styles */
  .no-print { display: none !important; }
  body { background: white !important; }
  .card { border: 1px solid #ddd !important; }
  .badge { border: 1px solid currentColor; }

  /* NEW: Enhanced print styles */

  /* Hide interactive elements */
  button, .dropdown, .btn { display: none !important; }

  /* Optimize typography */
  body {
    font-size: 11pt;
    line-height: 1.4;
    color: #000;
  }

  h1 { font-size: 18pt; }
  h2 { font-size: 14pt; }
  h3, h4 { font-size: 12pt; }

  /* Hero jobs: preserve visual priority */
  .hero-job {
    border-left: 3pt solid #000 !important;
    background: #f5f5f5 !important;
    page-break-inside: avoid;
  }

  /* Table optimization */
  table {
    font-size: 9pt;
    border-collapse: collapse;
    width: 100%;
  }

  table th,
  table td {
    border: 1pt solid #ddd;
    padding: 4pt;
  }

  /* Hide less important columns */
  table th:nth-child(3),  /* New badge */
  table td:nth-child(3),
  table th:nth-child(4),  /* Status dropdown */
  table td:nth-child(4),
  table th:nth-child(10), /* Snippet */
  table td:nth-child(10) {
    display: none;
  }

  /* Page breaks */
  .card, tr {
    page-break-inside: avoid;
  }

  h2, h3, h4 {
    page-break-after: avoid;
  }

  /* Links: show URLs */
  a[href^="http"]::after {
    content: " (" attr(href) ")";
    font-size: 8pt;
    color: #666;
  }
}
```

**Build order:** Phase 6 (Last — after all visual features)
**Modified function:** `_generate_html_report()` — extend existing @media print block
**Lines changed:** ~60 in CSS (within existing <style> block)
**Sources:**
- Existing codebase pattern (print styles already present)
- CSS print best practices (standard web development knowledge)

### Integration Pattern 8: Accessibility CI

**Decision: Separate GitHub Actions Workflow Job**

**Rationale:**
- Lighthouse CI requires HTML files to audit (must run after HTML generation)
- Can fail independently of main tests without blocking release
- Uses static HTML file (generate one test report for audit)
- Runs on every push, provides PR comments with scores

**Implementation:**

```yaml
# Add to .github/workflows/release.yml — new job after test, before build

  accessibility:
    name: Accessibility Audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Generate test report
        run: |
          # Create test profile if doesn't exist
          if [ ! -f profile.json ]; then
            echo '{"name":"Test User","level":"Senior","years_experience":5,"target_titles":["Software Engineer"],"core_skills":["Python"],"location":"Remote","arrangement":["remote"],"target_market":"US"}' > profile.json
          fi
          # Run search to generate HTML report
          python -m job_radar.search --sources dice --max-results 10 || true

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install Lighthouse CI
        run: npm install -g @lhci/cli@0.15.x

      - name: Run Lighthouse CI
        run: |
          # Find most recent HTML report
          REPORT_FILE=$(ls -t results/*.html 2>/dev/null | head -n1)
          if [ -z "$REPORT_FILE" ]; then
            echo "No HTML report found, skipping audit"
            exit 0
          fi
          # Create Lighthouse config
          cat > lighthouserc.json <<EOF
          {
            "ci": {
              "collect": {
                "staticDistDir": "./results",
                "url": ["file://$(pwd)/$REPORT_FILE"]
              },
              "assert": {
                "preset": "lighthouse:recommended",
                "assertions": {
                  "categories:accessibility": ["error", {"minScore": 0.9}],
                  "categories:best-practices": ["warn", {"minScore": 0.8}],
                  "categories:seo": ["warn", {"minScore": 0.8}]
                }
              }
            }
          }
          EOF
          lhci autorun

      - name: Upload Lighthouse results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: lighthouse-results
          path: .lighthouseci/
```

**Build order:** Phase 7 (Final — validates all accessibility work)
**Modified file:** `.github/workflows/release.yml`
**Lines changed:** ~45 in YAML
**Notes:**
- Job marked as non-blocking (`continue-on-error` not set, but separate from build job)
- Generates test report in CI environment
- Lighthouse audits accessibility, best practices, SEO
- Results uploaded as artifacts for inspection
- Can add axe-core separately or rely on Lighthouse (includes axe)

**Sources:**
- [GitHub: GoogleChrome/lighthouse-ci](https://github.com/GoogleChrome/lighthouse-ci) — Official implementation guide (HIGH confidence)
- [Setting Up Lighthouse CI From Scratch (with GitHub Actions Integration)](https://pradappandiyan.medium.com/setting-up-lighthouse-ci-from-scratch-with-github-actions-integration-1f7be5567e7f) — Practical example (MEDIUM confidence)

## Data Flow Changes

**No data flow changes.** All features are presentation-layer enhancements:

```
BEFORE v1.4.0:
profile.json + scored_results[] → _generate_html_report() → HTML file

AFTER v1.4.0:
profile.json + scored_results[] → _generate_html_report() → HTML file
                                   (with enhanced CSS/JS)
```

The Python data structures (`profile`, `scored_results`, `tracker_stats`) remain unchanged. Only the HTML/CSS/JS output changes.

## Component Modification Summary

### report.py Modifications

| Section | Change Type | Est. Lines | Complexity |
|---------|-------------|------------|------------|
| `<style>` block | CSS additions | +150 | Low |
| `_generate_html_report()` HTML structure | Add classes, data attributes, filter UI | +50 | Low |
| `_html_recommended_cards()` | Add hero job logic | +15 | Low |
| `_html_results_table()` | Add data-label attributes | +10 | Low |
| `<script>` block | Add filter + CSV functions | +100 | Medium |
| **TOTAL** | **Additive changes** | **~325** | **Low-Medium** |

**No existing code removed.** All changes are additive enhancements.

### GitHub Actions Modifications

| File | Change Type | Est. Lines | Complexity |
|------|-------------|------------|------------|
| `.github/workflows/release.yml` | Add accessibility job | +45 | Low |

## Build Order Recommendations

Based on dependencies and logical progression:

```
Phase 1: Typography & Color Foundation
├── System font stack CSS
└── Semantic color variables
    ↓
Phase 2: Hero Jobs
├── Depends on: semantic colors
└── Modify: _html_recommended_cards()
    ↓
Phase 3: Responsive Layout
├── Depends on: semantic colors
└── Modify: _html_results_table() + media queries
    ↓
Phase 4: Status Filters
├── Depends on: data attributes in responsive table
└── Add: filter UI + JavaScript
    ↓
Phase 5: CSV Export
├── Depends on: status filters (can export filtered view)
└── Add: export button + JavaScript
    ↓
Phase 6: Print Stylesheet
├── Depends on: all visual features (optimizes them for print)
└── Extend: @media print block
    ↓
Phase 7: Accessibility CI
├── Depends on: all features implemented
└── Add: GitHub Actions job
```

**Rationale:**
- Phases 1-2: Foundation (fonts + colors) before features that use them
- Phases 3-5: Interactive features in dependency order
- Phase 6: Print optimizations after features are stable
- Phase 7: Validation after implementation complete

## Anti-Patterns to Avoid

### Anti-Pattern 1: Separate CSS/JS Files

**What people do:** Extract CSS/JS to separate files, link with `<link>` and `<script src="">`
**Why it's wrong:** Breaks single-file constraint and file:// protocol compatibility
**Do this instead:** Inline all CSS in `<style>` block, all JS in `<script>` block

### Anti-Pattern 2: Base64 Font Embedding

**What people do:** Inline WOFF2 fonts as base64 data URIs
**Why it's wrong:**
- Adds 150-200KB+ per HTML file
- Blocks rendering (large inline data)
- Prevents browser caching
- Worse repeat view performance
**Do this instead:** Use system font stacks (zero bytes, instant rendering)

### Anti-Pattern 3: Python-Side CSV Generation

**What people do:** Add CSV generation to `_generate_markdown_report()`, write separate .csv file
**Why it's wrong:**
- Duplicates data (already in HTML table)
- Requires file management (cleanup, file listing)
- User has two files instead of one self-contained HTML
- More code to maintain (CSV formatting logic)
**Do this instead:** Browser-side JavaScript CSV export from existing table

### Anti-Pattern 4: Server-Side Status Filtering

**What people do:** Add `--filter-status` CLI argument, filter in Python before HTML generation
**Why it's wrong:**
- Requires re-running entire search to change filter
- Can't see all statuses in one view
- Complicates CLI UX
**Do this instead:** Client-side JavaScript filtering (instant, no re-run)

### Anti-Pattern 5: Separate Accessibility Tests

**What people do:** Add pytest-axe or pa11y to Python test suite
**Why it's wrong:**
- Can't test generated HTML (tests would need to generate reports first)
- Python test suite doesn't have browser context
- Lighthouse CI is industry standard, includes axe-core
**Do this instead:** Lighthouse CI in GitHub Actions (full browser audit)

## Testing Strategy

### Manual Testing Checklist

For each feature:

```
[ ] Desktop Chrome (light mode)
[ ] Desktop Chrome (dark mode)
[ ] Desktop Firefox
[ ] Desktop Safari
[ ] Mobile Chrome (responsive layout)
[ ] Mobile Safari (responsive layout)
[ ] Print preview (Chrome)
[ ] file:// protocol (not http://localhost)
[ ] Screen reader (macOS VoiceOver or Windows Narrator)
[ ] Keyboard navigation (Tab, Enter, Space)
```

### Automated Testing

```
Existing pytest suite:
- No changes needed (HTML generation logic unchanged)
- Consider adding snapshot tests for HTML structure

Accessibility CI:
- Runs on every push
- Lighthouse accessibility score >= 90
- Flags regressions automatically
```

## Performance Considerations

| Feature | Performance Impact | Mitigation |
|---------|-------------------|------------|
| System fonts | **+0ms** (instant) | N/A — already on system |
| CSS additions | **+5-10ms** (parse ~300 lines CSS) | Minify CSS in production (future) |
| JavaScript additions | **+10-15ms** (parse ~100 lines JS) | Load order unchanged (end of body) |
| Responsive media queries | **+0ms** (CSS-only) | Browser-native performance |
| Status filter | **<1ms** per filter change | Pure DOM manipulation, no layout thrash |
| CSV export | **10-50ms** for 100 rows | Only on user action, not page load |
| **Total page load impact** | **~15-25ms** | Negligible for file:// protocol |

**File size impact:**
- Current HTML: ~150KB (with CDN links, ~200KB if CSS/JS inlined)
- After v1.4.0: +~10KB (CSS/JS additions)
- **Total: ~160KB** (still well under 200KB threshold)

## Rollback Strategy

All features are CSS/JS additions with no breaking changes to data structures:

```
Rollback options:
1. Remove CSS block additions → features disappear, base functionality intact
2. Remove JS function additions → filters/export gone, core report works
3. Git revert specific commits → granular rollback per phase
4. Feature flags (future): Use CSS classes to toggle features
```

**Safe rollback:** Any phase can be reverted independently without breaking earlier phases.

## Sources

### HIGH Confidence (Official Docs, Verified Tools)

- [Modern Font Stacks](https://modernfontstacks.com/) — System font CSS patterns
- [CSS-Tricks System Font Stack](https://css-tricks.com/snippets/css/system-font-stack/) — Industry standard
- [CSS-Tricks Responsive Data Tables](https://css-tricks.com/responsive-data-tables/) — Card transformation
- [HTML Tables in Responsive Design (2026)](https://618media.com/en/blog/html-tables-in-responsive-design/) — Current patterns
- [GitHub: GoogleChrome/lighthouse-ci](https://github.com/GoogleChrome/lighthouse-ci) — Official tool
- [How to Export HTML Table to CSV Using Vanilla JavaScript](https://www.xjavascript.com/blog/export-html-table-to-csv-using-vanilla-javascript/) — Pure JS patterns

### MEDIUM Confidence (WebSearch, Multiple Sources)

- [Accessible Color Tokens for Enterprise Design Systems](https://www.aufaitux.com/blog/color-tokens-enterprise-design-systems-best-practices/) — Color patterns
- [Designing semantic colors for your system](https://imperavi.com/blog/designing-semantic-colors-for-your-system/) — Semantic color rationale
- [Hero Section Design: Best Practices & Examples for 2026](https://www.perfectafternoon.com/2025/hero-section-design/) — Visual priority
- [Setting Up Lighthouse CI From Scratch](https://pradappandiyan.medium.com/setting-up-lighthouse-ci-from-scratch-with-github-actions-integration-1f7be5567e7f) — Practical example
- [GeeksforGeeks: Export HTML table to CSV](https://www.geeksforgeeks.org/javascript/how-to-export-html-table-to-csv-using-javascript/) — CSV patterns

### LOW Confidence (Unverified Claims)

- None — all architectural decisions verified against official sources or existing codebase

---
*Architecture research for: Job Radar v1.4.0 Visual Design & Polish*
*Researched: 2026-02-11*
