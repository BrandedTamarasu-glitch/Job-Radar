# Phase 21: Responsive Layout - Research

**Researched:** 2026-02-11
**Domain:** CSS responsive design with accessible table-to-card transformations
**Confidence:** HIGH

## Summary

Phase 21 transforms the Job Radar HTML report to adapt across desktop (≥992px), tablet (<992px), and mobile (<768px) viewports. The core technical challenge is converting a 10-column accessible table into a mobile card layout while preserving screen reader semantics — CSS display:block strips native table roles, requiring explicit ARIA restoration.

Modern browsers (Chrome, Firefox, Safari 17+) now support table semantics with display properties when ARIA roles are explicitly added. The safest baseline approach uses horizontal scroll containers, but user requirements demand visual adaptation. Research confirms three proven patterns: (1) column hiding at tablet breakpoints using CSS display:none, (2) table-to-card transformation using display:block with ARIA role restoration, and (3) mobile-first media queries with content-driven breakpoints at 768px (tablet) and 992px (desktop).

Critical finding: As of October 2023, tables with display properties are functional across Chromium, Gecko, and WebKit when ARIA roles (role="table", role="row", role="columnheader", role="cell") are applied via JavaScript on page load. Safari addressed its table semantics bugs in version 17 (2023). Screen reader testing with NVDA + Firefox/Chrome and VoiceOver + Safari is mandatory to verify table navigation remains functional.

**Primary recommendation:** Use mobile-first approach with 768px and 992px breakpoints. Hide low-priority columns using display:none at <992px (maintains accessibility). Transform table to stacked cards using display:block at <768px, restore ARIA roles with JavaScript function on DOMContentLoaded, and test with NVDA table navigation (Ctrl+Alt+Arrows) and VoiceOver rotor to verify semantic preservation.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| CSS Media Queries | CSS3 standard | Responsive breakpoints | Native browser feature, zero dependencies |
| ARIA table roles | WAI-ARIA 1.3 | Semantic restoration | W3C standard for accessibility tree correction |
| CSS Grid | CSS Grid Level 1 | Mobile card layout | Modern layout without float hacks, excellent browser support |
| `prefers-color-scheme` | Already in use | Dark mode support | Carries through to responsive views |
| CSS custom properties | Already in use | Typography/color variables | Phase 19 foundation extends to responsive styles |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `clamp()` function | CSS Values Level 4 | Fluid typography | Optional enhancement for smooth scaling between breakpoints |
| `container queries` | CSS Containment Level 3 | Component-level responsive | Future enhancement, not needed for table/card pattern |
| Viewport meta tag | HTML5 standard | Mobile device rendering | Already present in report.py, verify correct settings |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Media queries | Container queries | Container queries are modern but table isn't nested in container; media queries simpler for page-level breakpoints |
| ARIA role restoration | Scroll container only | Scroll container safest but fails VIS-05 requirement for mobile card layout |
| Mobile-first | Desktop-first | Mobile-first forces essential-content thinking and performs better on slow connections |
| CSS Grid for cards | Flexbox | Grid better for two-dimensional card layout with aligned internal elements |
| JavaScript ARIA injection | Inline HTML ARIA | JS allows single source of truth (table markup) without duplicating roles in Python template |

**Installation:**

No installation required — all features are native CSS3, HTML5, and WAI-ARIA standards supported in modern browsers.

## Architecture Patterns

### Recommended Project Structure

All CSS lives in inline `<style>` block in `job_radar/report.py` `_generate_html_report()` function. JavaScript lives in inline `<script>` block before closing `</body>` tag.

```
job_radar/
└── report.py                   # Contains all HTML template with inline CSS/JS
    ├── <style> block           # Phase 19 variables + Phase 21 responsive rules
    ├── <body> markup           # Semantic table with proper th/td structure
    └── <script> block          # ARIA role injection + existing copy/status JS
```

### Pattern 1: Mobile-First Media Queries with Content-Driven Breakpoints

**What:** Define base styles for mobile (<768px), then progressively enhance for tablet (768px-991px) and desktop (≥992px)

**When to use:** Page-level responsive behavior where content dictates breakpoints (not device categories)

**Example:**

```css
/* Source: Modern responsive design best practices 2026 */
/* Mobile-first: base styles apply to smallest viewport */
table {
  width: 100%;
  border-collapse: collapse;
}

/* Tablet: 768px and up - reveal table with reduced columns */
@media (min-width: 768px) {
  /* Table becomes visible, cards hidden */
  .job-cards-mobile { display: none; }
  table { display: table; }

  /* Hide low-priority columns until desktop */
  .col-arrangement,
  .col-salary,
  .col-posted,
  .col-source { display: none; }
}

/* Desktop: 992px and up - show all columns */
@media (min-width: 992px) {
  .col-arrangement,
  .col-salary,
  .col-posted,
  .col-source { display: table-cell; }
}
```

**Rationale:** 768px is established tablet threshold, 992px is "large device" standard. Mobile-first reduces CSS override complexity and improves performance on slower connections.

### Pattern 2: Table-to-Card Transformation with ARIA Restoration

**What:** Convert table to stacked cards at mobile breakpoint using display:block, restore semantics with ARIA roles

**When to use:** Mobile viewport (<768px) where horizontal scrolling creates poor UX

**Example:**

```css
/* Source: Adrian Roselli responsive accessible tables + ADG examples */
/* Mobile only: <768px */
@media (max-width: 767px) {
  /* Hide table headers (visually) but keep in DOM for data-* attributes */
  thead {
    position: absolute;
    clip: rect(0 0 0 0);
    height: 1px;
    width: 1px;
    overflow: hidden;
  }

  /* Convert table elements to block stacking */
  table, tbody, tr, td, th {
    display: block;
    width: 100%;
  }

  /* Each row becomes a card */
  tbody tr {
    margin-bottom: 1rem;
    padding: 1rem;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    background: white;
  }

  /* Each cell shows label + value using ::before with data attributes */
  td {
    display: grid;
    grid-template-columns: 8em auto;
    gap: 0.5rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #e9ecef;
  }

  td:last-child {
    border-bottom: none;
  }

  td::before {
    content: attr(data-label) ": ";
    font-weight: 600;
    color: #495057;
  }
}
```

**JavaScript ARIA restoration:**

```javascript
// Source: Adrian Roselli's AddTableARIA function (2018, updated 2023)
function AddTableARIA() {
  try {
    // Only apply to tables that need semantic restoration
    var allTables = document.querySelectorAll('table');
    for (var i = 0; i < allTables.length; i++) {
      allTables[i].setAttribute('role','table');
    }

    var allCaptions = document.querySelectorAll('caption');
    for (var i = 0; i < allCaptions.length; i++) {
      allCaptions[i].setAttribute('role','caption');
    }

    var allRowGroups = document.querySelectorAll('thead, tbody, tfoot');
    for (var i = 0; i < allRowGroups.length; i++) {
      allRowGroups[i].setAttribute('role','rowgroup');
    }

    var allRows = document.querySelectorAll('tr');
    for (var i = 0; i < allRows.length; i++) {
      allRows[i].setAttribute('role','row');
    }

    var allCells = document.querySelectorAll('td');
    for (var i = 0; i < allCells.length; i++) {
      allCells[i].setAttribute('role','cell');
    }

    var allHeaders = document.querySelectorAll('th');
    for (var i = 0; i < allHeaders.length; i++) {
      allHeaders[i].setAttribute('role','columnheader');
    }

    // Handle row headers if present
    var allRowHeaders = document.querySelectorAll('th[scope=row]');
    for (var i = 0; i < allRowHeaders.length; i++) {
      allRowHeaders[i].setAttribute('role','rowheader');
    }
  } catch (e) {
    console.log("AddTableARIA(): " + e);
  }
}

// Run on page load
document.addEventListener('DOMContentLoaded', AddTableARIA);
```

**Critical notes:**
- ARIA injection must run BEFORE screen readers parse the page (DOMContentLoaded is correct timing)
- `data-label` attributes must be added to every `<td>` in Python template generation
- Test with NVDA (Ctrl+Alt+Arrow keys) and VoiceOver (VO+arrow navigation) to verify table semantics preserved

### Pattern 3: Column Hiding with Preserved Accessibility

**What:** Hide low-priority table columns at tablet breakpoint using display:none (maintains screen reader access)

**When to use:** Tablet viewport (768px-991px) where 10 columns cause overflow but full table structure still fits

**Example:**

```css
/* Source: WCAG-compliant responsive table patterns */
/* Apply to specific column classes */
@media (max-width: 991px) {
  /* Hide columns by class, not nth-child (more maintainable) */
  .col-arrangement,
  .col-salary,
  .col-posted,
  .col-source {
    display: none;
  }
}

/* Desktop: reveal all columns */
@media (min-width: 992px) {
  .col-arrangement,
  .col-salary,
  .col-posted,
  .col-source {
    display: table-cell;
  }
}
```

**HTML structure requirement:**

```html
<!-- Python template must add column classes to th and td -->
<thead>
  <tr>
    <th scope="col">#</th>
    <th scope="col">Score</th>
    <th scope="col">Title</th>
    <th scope="col">Company</th>
    <th scope="col">Location</th>
    <th scope="col" class="col-arrangement">Arrangement</th>
    <th scope="col" class="col-salary">Salary</th>
    <th scope="col" class="col-posted">Posted</th>
    <th scope="col" class="col-source">Source</th>
    <th scope="col">Status</th>
    <th scope="col">Link</th>
  </tr>
</thead>
<tbody>
  <tr class="tier-strong">
    <td>1</td>
    <td><span class="badge">4.2</span></td>
    <td>Senior Engineer</td>
    <td>Acme Corp</td>
    <td>Remote</td>
    <td class="col-arrangement">Remote</td>
    <td class="col-salary">$120k-$160k</td>
    <td class="col-posted">2 days ago</td>
    <td class="col-source">Dice</td>
    <td><select>...</select></td>
    <td><button>Copy</button></td>
  </tr>
</tbody>
```

**Why this works:** CSS display:none hides elements visually AND from screen readers, but since columns are duplicated (mobile shows ALL data in card format), accessibility is maintained — users get complete data in appropriate format for their viewport.

### Pattern 4: Fluid Typography with clamp()

**What:** Use clamp() for smooth font size scaling between breakpoints without jarring media query jumps

**When to use:** Optional enhancement for Phase 19 typography system to improve readability across viewports

**Example:**

```css
/* Source: Smashing Magazine Modern Fluid Typography (2022) */
:root {
  /* Combines rem (respects user zoom) with viewport units (scales with width) */
  --font-size-title: clamp(1.5rem, 2vw + 1rem, 2rem);
  --font-size-section: clamp(1.25rem, 1.5vw + 0.75rem, 1.5rem);
  --font-size-body: clamp(0.875rem, 1vw + 0.5rem, 1rem);
}

h1 { font-size: var(--font-size-title); }
h2 { font-size: var(--font-size-section); }
body { font-size: var(--font-size-body); }
```

**Accessibility consideration:** The `vw` unit alone doesn't respond to browser zoom, but combining with `rem` ensures zoom accessibility while allowing viewport scaling.

**Recommendation:** Optional for Phase 21. Phase 19 already uses fixed rem values which work well. Add clamp() only if user testing shows readability issues at intermediate viewport widths.

### Pattern 5: Mobile Card Layout with CSS Grid

**What:** Use CSS Grid for internal card structure to align labels and values cleanly

**When to use:** Mobile card layout (<768px) where each table row becomes a stacked card

**Example:**

```css
/* Source: MDN CSS Grid patterns + responsive card best practices */
@media (max-width: 767px) {
  tbody tr {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.75rem;
    padding: 1rem;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    margin-bottom: 1rem;
  }

  /* Each cell is a grid with label column + value column */
  td {
    display: grid;
    grid-template-columns: 8em 1fr; /* Fixed label width, fluid value */
    gap: 0.5rem;
    align-items: start;
  }

  /* Label from data-label attribute */
  td::before {
    content: attr(data-label);
    font-weight: 600;
    color: #6c757d;
    text-align: right;
  }

  /* Score badge cell: special layout */
  td.score-cell {
    grid-template-columns: auto 1fr; /* Badge auto-sizes */
    justify-items: start;
  }

  /* Interactive elements maintain touch targets (44x44px minimum) */
  td button, td select {
    min-height: 44px;
    min-width: 44px;
  }
}
```

### Anti-Patterns to Avoid

- **Using nth-child() for column hiding:** Brittle when column order changes. Use semantic class names instead.
- **Forgetting viewport meta tag:** Mobile browsers won't respect media queries without `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- **ARIA roles in HTML markup:** Duplication and maintenance burden. Inject via JavaScript for single source of truth.
- **Hiding table headers completely:** Screen readers lose context. Use visually-hidden pattern (absolute positioning, 1px dimensions) or data-label attributes.
- **display:contents on table elements:** Known to break accessibility across browsers as of 2024. Avoid.
- **Desktop-first media queries:** Requires more overrides and delivers more CSS to mobile devices.
- **Color-only indicators in cards:** Phase 19 tier borders must carry through to mobile cards for colorblind users.
- **Touch targets smaller than 44x44px:** WCAG 2.5.5 Level AAA (2.1) requires minimum target sizes for mobile interaction.
- **Relying on hover states:** Mobile has no hover. Ensure all interactive feedback works via tap/focus.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ARIA role injection | Manual role attributes in Python template | JavaScript AddTableARIA function | Single source of truth, tested pattern, easier maintenance |
| Breakpoint values | Custom pixel values based on popular devices | Standard 768px/992px breakpoints | Content-driven and industry-standard |
| Responsive testing | Browser resize only | Browser DevTools device emulation + real devices | Emulators catch touch target issues, font rendering differences |
| Viewport detection | JavaScript window.innerWidth checks | CSS media queries | CSS is faster, works without JS, handles resize automatically |
| Card label generation | Hardcoded labels in CSS ::before | data-label attributes from Python template | Maintainable when column names change |
| Scroll container shadows | Custom JavaScript scroll listeners | CSS background gradients with background-attachment | Pure CSS solution, better performance |

**Key insight:** Responsive table patterns are well-researched with documented accessibility pitfalls. Adrian Roselli's ARIA restoration pattern has been tested since 2018 and updated through 2023 as browser support evolved. Browser DevTools and screen readers are essential testing tools — visual inspection alone misses semantic breakage.

## Common Pitfalls

### Pitfall 1: display:block Strips Table Semantics Without ARIA

**What goes wrong:** Applying `display: block` to table elements makes screen readers lose table navigation (NVDA table mode, VoiceOver rotor), row/column context, and header associations.

**Why it happens:** CSS display properties override the browser's accessibility tree. When a `<table>` has `display: block`, browsers remove the "table" role from the accessibility tree and no longer map th/td relationships.

**How to avoid:** Add explicit ARIA roles (`role="table"`, `role="row"`, `role="columnheader"`, `role="cell"`) via JavaScript on page load. Test with screen readers to verify table navigation still works.

**Warning signs:** NVDA doesn't announce "table with X rows and Y columns" when entering the table. VoiceOver rotor doesn't show table navigation option. Arrow key table navigation doesn't work.

**Source:** Adrian Roselli's "Tables, CSS Display Properties, and ARIA" (2018, updated October 2023), TPGi browser compatibility notes

### Pitfall 2: Safari Pre-17 Drops Table Semantics Even With ARIA

**What goes wrong:** Older Safari versions (pre-2024) strip table semantics when display properties change, even with ARIA roles present.

**Why it happens:** WebKit had bugs in accessibility tree construction when CSS display overrides native semantics. Fixed in Safari 17 after 5.75 years of bug reports.

**How to avoid:** Test on Safari 17+ (current as of 2024). Provide scroll container fallback for older browsers if analytics show significant Safari 16 usage. Document minimum browser requirements in README.

**Warning signs:** Table works in Chrome/Firefox but fails VoiceOver testing on Safari 16 or older.

**Source:** Adrian Roselli's "It's Mid-2022 and Browsers (Mostly Safari) Still Break Accessibility via Display Properties", GitHub browser-compat-data issue #19994

### Pitfall 3: Missing data-label Attributes Break Mobile Context

**What goes wrong:** Mobile card layout shows values without labels because table headers are hidden and no data-label attributes exist on `<td>` elements.

**Why it happens:** CSS ::before content uses `attr(data-label)` to generate labels, but Python template doesn't add these attributes.

**How to avoid:** Add `data-label="Column Name"` attribute to every `<td>` element during template generation in report.py. Match labels to `<th>` text exactly.

**Warning signs:** Mobile cards show raw data with no labels (e.g., "4.2 Acme Corp Remote" instead of "Score: 4.2, Company: Acme Corp, Location: Remote").

**Example fix:**

```python
# In report.py _generate_html_report()
f'<td data-label="Score">{score}</td>'
f'<td data-label="Company">{company}</td>'
```

### Pitfall 4: Column Hiding Causes Screen Reader Confusion

**What goes wrong:** Using `display: none` on columns at tablet breakpoint hides data from screen readers, but users expect full table access.

**Why it happens:** CSS `display: none` removes elements from both visual rendering AND accessibility tree.

**How to avoid:** This is ACCEPTABLE for responsive tables where mobile view shows ALL data in card format. Users get complete information in format optimized for their viewport. Document this behavior as intentional design decision.

**Alternative:** Use `visibility: hidden` with `position: absolute` to keep in accessibility tree while hiding visually, but this creates layout issues with table structure.

**Warning signs:** Screen reader users on tablet complain about missing columns. This is only a pitfall if mobile view ALSO hides those columns — in this design, mobile shows everything, so it's safe.

**Source:** Accessibility Developer Guide responsive tables documentation

### Pitfall 5: Touch Targets Smaller Than 44x44px

**What goes wrong:** Copy buttons, status dropdowns, and links are too small to tap accurately on mobile devices, causing user frustration and accessibility failures.

**Why it happens:** Desktop button sizes (typically 32x32px) are optimized for mouse precision, not finger touch. WCAG 2.5.5 (Level AAA) requires 44x44px minimum.

**How to avoid:** Apply `min-height: 44px; min-width: 44px;` to all interactive elements in mobile breakpoint. Increase padding around buttons. Ensure adequate spacing between adjacent interactive elements.

**Warning signs:** Users miss buttons and trigger adjacent controls. Lighthouse flags "tap target" issues. Manual mobile testing shows difficulty hitting small targets.

**Source:** WCAG 2.1 Success Criterion 2.5.5, BrowserStack mobile accessibility guide

### Pitfall 6: Viewport Meta Tag Missing or Misconfigured

**What goes wrong:** Mobile browsers render desktop layout at 980px viewport width and scale down, making text unreadably small and defeating responsive design.

**Why it happens:** Without viewport meta tag, mobile browsers assume desktop layout. Without `initial-scale=1`, browsers apply default zoom that breaks media query behavior.

**How to avoid:** Verify `<meta name="viewport" content="width=device-width, initial-scale=1">` exists in report.py HTML template. This should already be present from Bootstrap integration.

**Warning signs:** Media queries don't trigger on mobile devices. Report loads at desktop size and requires pinch-zoom to read.

**Source:** MDN viewport meta tag documentation, mobile web best practices

### Pitfall 7: Forgetting Dark Mode in Responsive Styles

**What goes wrong:** Mobile card layout looks correct in light mode but breaks contrast/readability in dark mode due to missing dark mode overrides for new card styles.

**Why it happens:** Phase 19 dark mode styles target existing elements. New mobile card borders, backgrounds, and labels need dark mode color variables.

**How to avoid:** Extend existing `@media (prefers-color-scheme: dark)` block with mobile card styles. Use Phase 19 CSS custom properties for consistency.

**Warning signs:** Mobile cards have white backgrounds in dark mode. Card borders disappear. Label text has poor contrast.

**Example fix:**

```css
@media (prefers-color-scheme: dark) {
  @media (max-width: 767px) {
    tbody tr {
      background: #212529;
      border-color: #495057;
    }
    td::before {
      color: #adb5bd;
    }
  }
}
```

### Pitfall 8: Testing Only in Browser Resize, Not Real Devices

**What goes wrong:** Layout looks perfect in Chrome DevTools responsive mode but breaks on actual mobile devices due to browser chrome, address bar collapse, touch event differences, or font rendering.

**Why it happens:** Desktop browser emulation is approximate. Real devices have viewport height changes (address bar hide/show), different default fonts, actual touch input vs mouse simulation.

**How to avoid:** Test on real iOS (iPhone Safari) and Android (Chrome) devices or use cloud device labs (BrowserStack, Sauce Labs). Check viewport height issues with address bar behavior.

**Warning signs:** Users report layout issues that don't reproduce in DevTools. Interactive elements don't respond to touch. Fonts render at unexpected sizes.

**Source:** BrowserStack mobile testing guide, responsive design pitfalls 2026

## Code Examples

Verified patterns from official sources:

### Complete Responsive Table with ARIA Restoration

```html
<!-- Source: Adrian Roselli + Accessibility Developer Guide composite pattern -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <style>
    /* Phase 19 variables already defined in :root */

    /* Desktop: all columns visible */
    table {
      width: 100%;
      border-collapse: collapse;
    }

    th, td {
      padding: 0.75rem;
      text-align: left;
      border-bottom: 1px solid #dee2e6;
    }

    /* Tablet: hide low-priority columns */
    @media (max-width: 991px) {
      .col-arrangement,
      .col-salary,
      .col-posted,
      .col-source {
        display: none;
      }
    }

    /* Mobile: card layout */
    @media (max-width: 767px) {
      /* Hide table headers visually (keep in DOM for ARIA) */
      thead {
        position: absolute;
        clip: rect(0 0 0 0);
        height: 1px;
        width: 1px;
        overflow: hidden;
      }

      /* Stack table elements */
      table, tbody, tr, td {
        display: block;
        width: 100%;
      }

      /* Each row becomes a card */
      tbody tr {
        margin-bottom: 1rem;
        padding: 1rem;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        background: white;
      }

      /* Preserve tier borders from Phase 19 */
      tbody tr.tier-strong {
        border-left: 5px solid var(--color-tier-strong-border);
      }
      tbody tr.tier-rec {
        border-left: 4px solid var(--color-tier-rec-border);
      }
      tbody tr.tier-review {
        border-left: 3px solid var(--color-tier-review-border);
      }

      /* Grid layout for cells: label + value */
      td {
        display: grid;
        grid-template-columns: 8em auto;
        gap: 0.5rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e9ecef;
      }

      td:last-child {
        border-bottom: none;
      }

      /* Label from data-label attribute */
      td::before {
        content: attr(data-label) ": ";
        font-weight: 600;
        color: #6c757d;
      }

      /* Hide label for cells that don't need it */
      td.no-label::before {
        display: none;
      }

      /* Touch targets */
      td button, td select {
        min-height: 44px;
        min-width: 44px;
      }
    }

    /* Dark mode overrides */
    @media (prefers-color-scheme: dark) {
      @media (max-width: 767px) {
        tbody tr {
          background: #212529;
          border-color: #495057;
        }
        td {
          border-bottom-color: #343a40;
        }
        td::before {
          color: #adb5bd;
        }
      }
    }
  </style>
</head>
<body>
  <table>
    <caption>Job Results</caption>
    <thead>
      <tr>
        <th scope="col">#</th>
        <th scope="col">Score</th>
        <th scope="col">Title</th>
        <th scope="col">Company</th>
        <th scope="col">Location</th>
        <th scope="col" class="col-arrangement">Arrangement</th>
        <th scope="col" class="col-salary">Salary</th>
        <th scope="col" class="col-posted">Posted</th>
        <th scope="col" class="col-source">Source</th>
        <th scope="col">Status</th>
        <th scope="col">Link</th>
      </tr>
    </thead>
    <tbody>
      <tr class="tier-strong">
        <td data-label="#">1</td>
        <td data-label="Score"><span class="badge rounded-pill">4.2</span></td>
        <td data-label="Title">Senior Python Engineer</td>
        <td data-label="Company">Acme Corp</td>
        <td data-label="Location">Remote</td>
        <td data-label="Arrangement" class="col-arrangement">Remote</td>
        <td data-label="Salary" class="col-salary">$120k-$160k</td>
        <td data-label="Posted" class="col-posted">2 days ago</td>
        <td data-label="Source" class="col-source">Dice</td>
        <td data-label="Status"><select><option>Not Applied</option></select></td>
        <td data-label="Link" class="no-label"><button>Copy URL</button></td>
      </tr>
    </tbody>
  </table>

  <script>
    // ARIA role restoration for table semantics with display:block
    function AddTableARIA() {
      try {
        var allTables = document.querySelectorAll('table');
        for (var i = 0; i < allTables.length; i++) {
          allTables[i].setAttribute('role','table');
        }

        var allCaptions = document.querySelectorAll('caption');
        for (var i = 0; i < allCaptions.length; i++) {
          allCaptions[i].setAttribute('role','caption');
        }

        var allRowGroups = document.querySelectorAll('thead, tbody, tfoot');
        for (var i = 0; i < allRowGroups.length; i++) {
          allRowGroups[i].setAttribute('role','rowgroup');
        }

        var allRows = document.querySelectorAll('tr');
        for (var i = 0; i < allRows.length; i++) {
          allRows[i].setAttribute('role','row');
        }

        var allCells = document.querySelectorAll('td');
        for (var i = 0; i < allCells.length; i++) {
          allCells[i].setAttribute('role','cell');
        }

        var allHeaders = document.querySelectorAll('th');
        for (var i = 0; i < allHeaders.length; i++) {
          allHeaders[i].setAttribute('role','columnheader');
        }

        var allRowHeaders = document.querySelectorAll('th[scope=row]');
        for (var i = 0; i < allRowHeaders.length; i++) {
          allRowHeaders[i].setAttribute('role','rowheader');
        }
      } catch (e) {
        console.log("AddTableARIA(): " + e);
      }
    }

    // Run on page load
    document.addEventListener('DOMContentLoaded', AddTableARIA);
  </script>
</body>
</html>
```

### Mobile-First Breakpoint Structure

```css
/* Source: BrowserStack media query guide + mobile-first best practices 2026 */

/* Base: Mobile styles (<768px) */
body {
  padding: 0.5rem;
  font-size: 0.875rem;
}

h1 {
  font-size: 1.5rem;
}

/* Tablet: 768px and up */
@media (min-width: 768px) {
  body {
    padding: 1rem;
    font-size: 1rem;
  }

  h1 {
    font-size: 1.75rem;
  }

  /* Reveal table, hide mobile cards */
  .mobile-cards { display: none; }
  table { display: table; }
}

/* Desktop: 992px and up */
@media (min-width: 992px) {
  body {
    padding: 2rem;
  }

  h1 {
    font-size: 2rem;
  }

  /* Show all table columns */
  .col-arrangement,
  .col-salary,
  .col-posted,
  .col-source {
    display: table-cell;
  }
}

/* Large desktop: 1200px and up (optional enhancement) */
@media (min-width: 1200px) {
  body {
    max-width: 1140px;
    margin: 0 auto;
  }
}
```

### Fluid Typography with clamp() (Optional Enhancement)

```css
/* Source: Smashing Magazine Modern Fluid Typography (2022) */
:root {
  /* Smooth scaling between mobile and desktop without media query jumps */
  --font-size-title: clamp(1.5rem, 2vw + 1rem, 2rem);
  --font-size-section: clamp(1.25rem, 1.5vw + 0.75rem, 1.5rem);
  --font-size-body: clamp(0.875rem, 1vw + 0.5rem, 1rem);

  /* Combines rem (respects zoom) with vw (scales with viewport) */
  /* Format: clamp(min, preferred, max) */
}

h1 { font-size: var(--font-size-title); }
h2 { font-size: var(--font-size-section); }
body { font-size: var(--font-size-body); }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Device-specific breakpoints (iPhone 6, iPad) | Content-driven breakpoints (768px, 992px) | ~2016-2018 | Future-proof for new devices, focuses on layout needs |
| Desktop-first media queries | Mobile-first with min-width | ~2015-2017 | Better performance on mobile, forces essential-content thinking |
| JavaScript viewport detection | CSS media queries | ~2014-2016 | Faster, works without JS, handles resize automatically |
| Table scroll containers only | ARIA-enabled table-to-card | ~2020-2023 (browser fixes) | Better mobile UX while maintaining accessibility |
| display:contents workaround | Explicit ARIA roles | ~2023-2024 | display:contents remains buggy, ARIA roles proven stable |
| Separate mobile/desktop templates | Single responsive template | ~2012-2015 | Easier maintenance, consistent data, faster updates |
| Fixed breakpoints in pixels | Container queries (emerging) | 2022-2026 | Component-level responsive, but media queries still better for tables |
| Manual ARIA in markup | JavaScript injection | ~2018-2023 | Single source of truth, less duplication |

**Deprecated/outdated:**

- **Safari 16 and earlier for table semantics:** Safari 17 (2023) fixed 5.75-year-old bug. Minimum browser requirement should be Safari 17+ for full accessibility.
- **display:contents on tables:** Remains problematic across browsers as of 2024. Use display:block with ARIA instead.
- **Hover-only interactions:** Mobile has no hover. All functionality must work via tap/focus.
- **Viewport width alone for responsive typography:** Breaks user zoom. Use clamp() with rem + vw combination.
- **nth-child() for column selection:** Brittle when order changes. Use semantic class names.

## Open Questions

1. **Should hero job cards (Phase 20) also transform to mobile stacked layout?**
   - What we know: Hero jobs currently use Bootstrap card structure. Phase 20 added shadows and borders.
   - What's unclear: Whether hero cards already stack responsively via Bootstrap's default grid behavior or need explicit mobile styles.
   - Recommendation: Test hero section at <768px. Bootstrap cards stack by default, but verify tier borders and shadows render correctly. Add mobile-specific padding/margin if needed.

2. **Should mobile view preserve column hiding from tablet view or show all 10 columns?**
   - What we know: Tablet hides 4 columns. Mobile transforms table to cards.
   - What's unclear: Whether mobile cards should show all 10 data points or also hide the 4 low-priority columns.
   - Recommendation: Show ALL 10 columns in mobile cards. Users on small screens need complete data, and card format has unlimited vertical space. Only hide columns in constrained table layouts (tablet).

3. **Should data-label attributes match exact <th> text or use abbreviated labels?**
   - What we know: CSS ::before uses attr(data-label) to generate labels in mobile cards.
   - What's unclear: Whether to use full header text ("Posted Date") or shorter mobile-friendly labels ("Posted").
   - Recommendation: Use abbreviated labels optimized for mobile (8em label column width). Map headers: # → "#", Score → "Score", Title → "Job", Company → "Company", Location → "Location", Arrangement → "Type", Salary → "Salary", Posted → "Posted", Source → "Source", Status → "Status", Link → no label (copy button is self-explanatory).

4. **Should ARIA injection run conditionally only on mobile or always?**
   - What we know: display:block only applies at <768px, but ARIA roles don't harm desktop table rendering.
   - What's unclear: Performance/maintenance tradeoff of conditional vs unconditional ARIA injection.
   - Recommendation: Apply ARIA roles unconditionally. Simpler code, no viewport detection needed, negligible performance impact, ensures semantics in all cases. Modern browsers handle redundant ARIA gracefully.

5. **Should copy buttons in mobile cards use text labels or remain icon-only?**
   - What we know: Desktop uses button with "Copy" text. Mobile has limited horizontal space.
   - What's unclear: Whether mobile buttons should be icon-only with aria-label or keep text for clarity.
   - Recommendation: Keep text labels for clarity and accessibility. Use flexbox to stack button content vertically if needed. Ensure 44x44px touch target regardless of label style.

## Sources

### Primary (HIGH confidence)

- [Adrian Roselli: Tables, CSS Display Properties, and ARIA](https://adrianroselli.com/2018/02/tables-css-display-properties-and-aria.html) - ARIA restoration pattern, updated October 2023
- [Adrian Roselli: A Responsive Accessible Table](https://adrianroselli.com/2017/11/a-responsive-accessible-table.html) - Complete implementation with screen reader testing
- [Accessibility Developer Guide: Responsive Tables](https://www.accessibility-developer-guide.com/examples/tables/responsive/) - Tested patterns with NVDA/JAWS verification (May 2024)
- [TPGi: CSS Display Properties and Table Semantics](https://www.tpgi.com/short-note-on-what-css-display-properties-do-to-table-semantics/) - Browser compatibility status
- [W3C: ARIA Table Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/table/) - Official specification
- [MDN: Responsive Design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design) - Media queries and breakpoints
- [BrowserStack: CSS Media Query Breakpoints Guide](https://www.browserstack.com/guide/what-are-css-and-media-query-breakpoints) - Standard breakpoint values 2026

### Secondary (MEDIUM confidence)

- [Smashing Magazine: Accessible Front-End Patterns For Responsive Tables](https://www.smashingmagazine.com/2022/12/accessible-front-end-patterns-responsive-tables-part1/) - 2022 patterns with scroll shadows
- [Smashing Magazine: Modern Fluid Typography Using CSS Clamp](https://www.smashingmagazine.com/2022/01/modern-fluid-typography-css-clamp/) - clamp() implementation
- [LogRocket: Fluid vs Responsive Typography with CSS Clamp](https://blog.logrocket.com/fluid-vs-responsive-typography-css-clamp/) - Accessibility considerations
- [MDN: CSS Grid Layout Common Patterns](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Common_grid_layouts) - Card layout examples
- [TestMu AI: CSS Grid Best Practices](https://www.testmu.ai/blog/css-grid-best-practices/) - 2026 patterns
- [WebAIM: CSS Invisible Content for Screen Readers](https://webaim.org/techniques/css/invisiblecontent/) - Visually-hidden pattern
- [BrowserStack: Screen Reader Testing Guide](https://www.browserstack.com/guide/media-query-for-desktop-tablet-mobile) - NVDA/VoiceOver testing

### Tertiary (LOW confidence - verification recommended)

- [Adrian Roselli: It's Mid-2022 and Browsers (Mostly Safari) Still Break Accessibility](https://adrianroselli.com/2022/07/its-mid-2022-and-browsers-mostly-safari-still-break-accessibility-via-display-properties.html) - Safari historical bugs (resolved in Safari 17)
- [GitHub: r-lib/pkgdown #2140](https://github.com/r-lib/pkgdown/issues/2140) - Community report of display:block issue
- [Responsive Design Mistakes 2026](https://parachutedesign.ca/blog/responsive-web-design-mistakes/) - Pitfall catalog
- [Keel Info: Responsive Web Design Trends 2026](https://www.keelis.com/blog/responsive-web-design-in-2026:-trends-and-best-practices) - Industry trends

## Metadata

**Confidence breakdown:**

- **Standard stack:** HIGH - CSS media queries, ARIA roles, and CSS Grid are stable standards with excellent browser support and comprehensive MDN documentation.
- **Architecture patterns:** HIGH - Adrian Roselli's ARIA restoration pattern tested since 2018, updated 2023. Accessibility Developer Guide patterns verified with screen readers in May 2024. Breakpoints 768px/992px are industry standard.
- **ARIA implementation:** HIGH - W3C official pattern, multiple authoritative sources (Roselli, TPGi, ADG) confirm browser support as of October 2023 across Chromium/Gecko/WebKit.
- **Pitfalls:** HIGH - Safari 17 table bug fix documented. Touch target requirements from WCAG 2.5.5. Viewport meta tag critical for mobile rendering.
- **Mobile card layout:** MEDIUM - CSS Grid patterns well-documented but specific application to 10-column job table with tier borders requires implementation testing.

**Research date:** 2026-02-11

**Valid until:** 2026-05-11 (90 days) - CSS standards stable. Browser versions evolve (Safari 17+ requirement). WCAG 2.2 adopted, 3.0 still draft. Container queries gaining adoption but not needed for this phase.
