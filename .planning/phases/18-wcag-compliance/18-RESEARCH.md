# Phase 18: WCAG 2.1 Level AA Compliance - Research

**Researched:** 2026-02-11
**Domain:** Web accessibility (WCAG 2.1 Level AA) + CLI accessibility
**Confidence:** HIGH for HTML/web standards, MEDIUM for CLI accessibility, LOW for questionary screen reader support

## Summary

WCAG 2.1 Level AA compliance requires implementing both automated-checkable standards (color contrast, semantic HTML, ARIA attributes) and manual-verification features (screen reader announcements, keyboard navigation). For this phase, we must address two distinct accessibility surfaces: **HTML reports** (Bootstrap 5-based) and **CLI wizard** (questionary-based).

**HTML Reports:** Bootstrap 5 provides foundational accessibility (`.visually-hidden`, reduced motion support) but does NOT automatically provide WCAG 2.1 Level AA compliance. Critical gaps include: no semantic landmarks (nav, main, header), no skip navigation link, insufficient color contrast in default palette, missing ARIA labels for dynamic content, and improper table header associations for screen readers. All gaps are fixable with manual additions.

**CLI Wizard:** Terminal accessibility is an emerging domain with significant gaps. The questionary library (built on prompt_toolkit) has no documented screen reader support. CLI accessibility depends on: honoring NO_COLOR environment variable, avoiding animated spinners (or making them optional), providing clear text output that screen readers can parse, and using colorblind-safe terminal color palettes. Screen reader testing with NVDA/JAWS (Windows) and VoiceOver (macOS) is essential but challenging in terminal environments.

**Primary recommendation:** Prioritize HTML report accessibility (achievable to Level AA with known patterns) while implementing basic CLI accessibility best practices (NO_COLOR support, simple output mode). Defer comprehensive CLI screen reader testing to post-v1.3.0 validation phase due to tooling limitations and low confidence in questionary compatibility.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Bootstrap 5 | 5.3.0 | UI framework | Already in use (Phase 16/17); has built-in accessibility helpers but requires manual WCAG implementation |
| axe-core | Latest | Automated accessibility testing | Powers Lighthouse accessibility audits; finds ~57% of WCAG issues automatically with zero false positives |
| Lighthouse | Latest (via Chrome DevTools) | Accessibility scoring/auditing | Official Chrome tool; generates accessibility score 0-100 based on axe-core engine; required for success criterion 10 (score ≥95) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| WebAIM Contrast Checker | Web tool | Color contrast validation | Manual testing for all text/background pairs to meet 4.5:1 minimum (WCAG 1.4.3) |
| NVDA | Latest (2025+) | Windows screen reader testing | Free, open-source; strictness helps catch structural issues; 65.6% market share among screen reader users |
| JAWS | Latest | Windows screen reader testing | Enterprise standard; 60.5% market share; recommended for thorough testing alongside NVDA |
| VoiceOver | macOS built-in | macOS screen reader testing | Native macOS accessibility; required for cross-platform validation |
| questionary | Current (in pyproject.toml) | CLI prompts | Already integrated; no accessibility documentation but follows terminal best practices |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Bootstrap 5 | Custom CSS | Bootstrap already integrated (Phase 16/17); custom CSS would require rewriting existing reports; Bootstrap provides `.visually-hidden` class and focus utilities |
| axe-core (via Lighthouse) | WAVE browser extension | WAVE is excellent but Lighthouse provides required scoring metric (success criterion 10); can use both |
| questionary | Click library prompts | Questionary already integrated and provides richer UI; Click has similar accessibility unknowns for screen readers |

**Installation:**
No new dependencies required for HTML accessibility (manual implementation). Testing tools are browser-based or OS built-in.

```bash
# For NVDA (Windows): Download from https://www.nvaccess.org/download/
# For JAWS (Windows): Commercial license required
# For VoiceOver (macOS): Built-in, enable with Cmd+F5
# For Lighthouse: Built into Chrome DevTools (F12 → Lighthouse tab)
```

## Architecture Patterns

### Recommended HTML Structure
```
HTML Report Structure (Accessibility-Enhanced):
<!DOCTYPE html>
<html lang="en">
  <head>
    <!-- Existing meta tags, Bootstrap CSS -->
  </head>
  <body>
    <!-- NEW: Skip navigation link (first focusable element) -->
    <a href="#main-content" class="visually-hidden-focusable">Skip to main content</a>

    <!-- NEW: Semantic header with navigation role -->
    <header role="banner">
      <div class="container">
        <h1>Job Search Results</h1>
      </div>
    </header>

    <!-- NEW: Semantic main landmark -->
    <main id="main-content" role="main">
      <div class="container">
        <!-- Profile summary section -->
        <section aria-labelledby="profile-heading">
          <h2 id="profile-heading">Candidate Profile Summary</h2>
          <!-- Content -->
        </section>

        <!-- Jobs table with proper headers -->
        <section aria-labelledby="jobs-heading">
          <h2 id="jobs-heading">Job Listings</h2>
          <table class="table" aria-describedby="table-description">
            <caption id="table-description">
              Job search results sorted by score
            </caption>
            <thead>
              <tr>
                <th scope="col">Score</th>
                <th scope="col">Title</th>
                <!-- Other columns -->
              </tr>
            </thead>
            <tbody>
              <!-- Data rows -->
            </tbody>
          </table>
        </section>
      </div>
    </main>

    <!-- NEW: Semantic footer -->
    <footer role="contentinfo">
      <!-- Footer content -->
    </footer>

    <!-- NEW: ARIA live region for dynamic status updates -->
    <div id="status-announcer"
         role="status"
         aria-live="polite"
         aria-atomic="true"
         class="visually-hidden">
      <!-- Populated by JavaScript when status changes -->
    </div>
  </body>
</html>
```

### Pattern 1: Skip Navigation Link
**What:** First focusable element allowing keyboard users to bypass repeated content and jump directly to main content.

**When to use:** Required for WCAG 2.4.1 (Bypass Blocks) Level A; becomes visible when focused via keyboard (Tab key).

**Example:**
```html
<!-- Source: https://webaim.org/techniques/skipnav/ -->
<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: white;
  padding: 8px;
  text-decoration: none;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
</style>

<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Later in document -->
<main id="main-content">
  <!-- Main content starts here -->
</main>
```

**Bootstrap 5 shortcut:**
```html
<!-- Use Bootstrap's built-in class -->
<a class="visually-hidden-focusable" href="#main-content">
  Skip to main content
</a>
```

### Pattern 2: ARIA Landmarks with Semantic HTML
**What:** Combining HTML5 semantic elements (`<header>`, `<main>`, `<nav>`, `<footer>`) with explicit ARIA roles for maximum compatibility.

**When to use:** Required for WCAG success criterion A11Y-02 (screen reader announces semantic page structure).

**Example:**
```html
<!-- Source: W3C ARIA best practices -->
<header role="banner">
  <!-- Site header/branding -->
</header>

<nav role="navigation" aria-label="Main navigation">
  <!-- Navigation links -->
</nav>

<main role="main" id="main-content">
  <!-- Primary page content -->
</main>

<aside role="complementary" aria-label="Related resources">
  <!-- Sidebar content -->
</aside>

<footer role="contentinfo">
  <!-- Footer content -->
</footer>
```

**Why explicit roles:** Some older screen readers don't recognize HTML5 semantic elements; explicit `role` attributes ensure compatibility.

### Pattern 3: Accessible Data Tables
**What:** Using `<th>` with `scope` attribute to associate header cells with data cells for screen reader navigation.

**When to use:** Required for A11Y-03 (screen reader can navigate job listing table with proper header/cell associations).

**Example:**
```html
<!-- Source: https://webaim.org/techniques/tables/data -->
<table class="table table-striped" aria-describedby="jobs-caption">
  <caption id="jobs-caption">
    Job search results for [Profile Name], sorted by relevance score
  </caption>
  <thead>
    <tr>
      <th scope="col">#</th>
      <th scope="col">Score</th>
      <th scope="col">Status</th>
      <th scope="col">Title</th>
      <th scope="col">Company</th>
      <th scope="col">Location</th>
      <th scope="col">Link</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">1</th>
      <td>
        <span class="visually-hidden">Score </span>
        4.2
        <span class="visually-hidden"> out of 5.0</span>
      </td>
      <td>
        <span class="badge bg-primary">
          <span class="visually-hidden">New listing, not seen in previous searches</span>
          NEW
        </span>
      </td>
      <td>Senior Software Engineer</td>
      <td>Acme Corp</td>
      <td>Remote</td>
      <td><a href="..." target="_blank" aria-label="View job at Acme Corp (opens in new tab)">View</a></td>
    </tr>
  </tbody>
</table>
```

**Screen reader behavior:** When navigating to score cell "4.2", announces "Score 4.2 out of 5.0" (full context).

### Pattern 4: Contextual Screen Reader Text
**What:** Using Bootstrap's `.visually-hidden` class to add context for screen reader users without cluttering visual display.

**When to use:** Required for A11Y-04 (score badges with context) and A11Y-05 (NEW badges with context).

**Example:**
```html
<!-- Source: https://getbootstrap.com/docs/5.3/getting-started/accessibility/ -->
<!-- Score badge -->
<span class="badge bg-success">
  <span class="visually-hidden">Score </span>
  4.2
  <span class="visually-hidden"> out of 5.0</span>
</span>
<!-- Screen reader hears: "Score 4.2 out of 5.0" -->
<!-- Sighted users see: "4.2" -->

<!-- NEW badge -->
<span class="badge bg-primary">
  <span class="visually-hidden">New listing, not seen in previous searches</span>
  NEW
</span>
<!-- Screen reader hears: "New listing, not seen in previous searches" -->
<!-- Sighted users see: "NEW" -->
```

**CSS for `.visually-hidden` (Bootstrap 5 built-in):**
```css
.visually-hidden {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
```

### Pattern 5: ARIA Live Regions for Dynamic Content
**What:** Using `aria-live` to announce status changes (e.g., dropdown status updates) to screen readers without page reload.

**When to use:** When JavaScript updates content dynamically (status dropdown changes, toast notifications).

**Example:**
```html
<!-- Source: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions -->
<!-- Create empty live region in initial HTML -->
<div id="status-announcer"
     role="status"
     aria-live="polite"
     aria-atomic="true"
     class="visually-hidden">
</div>

<!-- JavaScript updates status -->
<script>
function announceStatusChange(jobTitle, newStatus) {
  const announcer = document.getElementById('status-announcer');
  // Update text content to trigger announcement
  announcer.textContent = `Status for ${jobTitle} changed to ${newStatus}`;

  // Clear after announcement (optional)
  setTimeout(() => {
    announcer.textContent = '';
  }, 1000);
}

// Example: Status dropdown change
document.querySelector('.status-dropdown').addEventListener('click', (e) => {
  const status = e.target.dataset.status;
  const jobTitle = e.target.closest('.card').dataset.jobTitle;
  announceStatusChange(jobTitle, status);
});
</script>
```

**Key principles:**
- Live region MUST exist in DOM before content updates (create empty on page load)
- Use `aria-live="polite"` (waits for user to be idle) for status updates
- Use `aria-live="assertive"` (interrupts) only for critical errors
- Use `aria-atomic="true"` to announce full message, not just changed text
- Bootstrap's Notyf toast library may need ARIA live region wrapper for accessibility

### Pattern 6: Focus Indicators
**What:** Visible outlines/borders when interactive elements receive keyboard focus.

**When to use:** Required for WCAG 2.4.7 (Focus Visible) Level AA and A11Y-06 (keyboard user can see visible focus indicators).

**Example:**
```css
/* Source: Phase 16 implementation + WCAG 2.4.7 best practices */
/* Bootstrap provides default focus styles, but can enhance */

.job-item:focus-visible {
  outline: 3px solid #0d6efd;  /* Bootstrap primary blue */
  outline-offset: 2px;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

/* Ensure dropdown items show focus */
.dropdown-item:focus {
  background-color: #e9ecef;
  color: #000;
  outline: 2px solid #0d6efd;
  outline-offset: -2px;
}

/* Table links */
a:focus-visible {
  outline: 2px solid #0d6efd;
  outline-offset: 2px;
  text-decoration: underline;
}
```

**Note:** Use `:focus-visible` (not `:focus`) to show indicators only for keyboard navigation, not mouse clicks (modern browser support).

### Anti-Patterns to Avoid

- **DON'T use `<div>` with styling instead of `<th>`**: Screen readers rely on `<th>` elements to identify headers; styled `<td>` or `<div>` won't be announced as headers.

- **DON'T use `display: none` or `visibility: hidden` for skip links**: These remove elements from keyboard navigation entirely; use off-screen positioning or `.visually-hidden-focusable` instead.

- **DON'T assume Bootstrap's default colors meet contrast requirements**: Bootstrap's info/warning colors often fall below 4.5:1 ratio; always test with WebAIM Contrast Checker.

- **DON'T add ARIA live regions with content already populated**: Screen readers ignore pre-populated live regions; create empty and update via JavaScript.

- **DON'T use `placeholder` as a label substitute**: Placeholders disappear on input; always use `<label>` or `aria-label` for form fields.

- **DON'T rely solely on color to convey information**: Use icons, text, or patterns alongside color for colorblind users.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Visually hidden text | Custom CSS for screen-reader-only content | Bootstrap's `.visually-hidden` class | Handles edge cases (Safari focus, VoiceOver bugs, magnification users); tested across screen readers; 1px dimensions prevent removal from accessibility tree |
| Color contrast checking | Manual eyeball comparison | WebAIM Contrast Checker tool | Calculates exact ratios per WCAG formula; accounts for font size/weight variations; prevents subjective judgment errors |
| Skip link implementation | Custom positioning/focus logic | Bootstrap's `.visually-hidden-focusable` | Ensures link is keyboard accessible but hidden until focused; compatible with all browsers; avoids `display:none` trap |
| Accessibility auditing | Manual checklist verification | Lighthouse + axe-core | Automates ~57% of WCAG checks; provides specific WCAG criterion mapping; generates reproducible scores; free and integrated into Chrome DevTools |
| ARIA live region timing | Manual setTimeout/polling | `role="status"` or `role="alert"` with proper setup | Browsers handle announcement timing automatically; avoids race conditions with screen reader buffer; respects user's screen reader settings |
| Table header associations | Complex `id`/`headers` mapping | Simple `scope="col"` or `scope="row"` | Sufficient for 99% of tables; simpler markup; better screen reader support; `id`/`headers` only needed for multi-level headers |

**Key insight:** Accessibility involves subtle cross-browser and assistive technology bugs that have been solved by standards and established libraries. Reinventing patterns (especially `.visually-hidden` CSS or ARIA timing) leads to failures in edge cases (Safari focus bugs, VoiceOver race conditions, JAWS parsing differences).

## Common Pitfalls

### Pitfall 1: Bootstrap Default Colors Fail Contrast Requirements
**What goes wrong:** Using Bootstrap's default `.text-muted`, `.btn-outline-secondary`, or custom brand colors without testing produces text below 4.5:1 contrast ratio, failing WCAG 1.4.3 (Level AA).

**Why it happens:** Bootstrap prioritizes aesthetic appeal over WCAG compliance; documentation explicitly warns colors "may produce insufficient contrast."

**How to avoid:**
1. Test ALL color combinations with WebAIM Contrast Checker (https://webaim.org/resources/contrastchecker/)
2. Target 4.5:1 minimum for normal text, 3:1 for large text (18pt+)
3. Override Bootstrap colors in custom CSS if needed
4. Pay special attention to: link colors on light backgrounds, badge colors, button text colors, disabled state colors

**Warning signs:** Lighthouse accessibility score flags contrast issues; light gray text on white background; pastel colors for critical information.

### Pitfall 2: ARIA Live Regions Not Working
**What goes wrong:** Adding `aria-live="polite"` to an element with content already present, or creating the element dynamically with content, results in screen readers never announcing updates.

**Why it happens:** Screen readers only monitor regions that exist in the DOM before content changes occur; dynamically created regions or pre-populated regions are ignored.

**How to avoid:**
1. Create empty live region in initial HTML: `<div id="announcer" aria-live="polite"></div>`
2. Update content via JavaScript: `document.getElementById('announcer').textContent = 'New message';`
3. Never create live region and populate it in same script execution
4. For dynamic creation, insert empty region, wait 2 seconds (for accessibility API detection), then populate

**Warning signs:** Testing with NVDA/JAWS/VoiceOver produces no announcements when content updates; checking DOM shows `aria-live` attribute is present but announcements don't occur.

### Pitfall 3: Forgetting `scope` Attribute on Table Headers
**What goes wrong:** Using `<th>` elements without `scope` attribute means screen readers may not properly associate headers with data cells, especially in complex tables.

**Why it happens:** Browsers visually render `<th>` as bold/centered regardless of `scope`; developers assume visual header equals accessible header.

**How to avoid:**
1. Always add `scope="col"` to column headers in `<thead>`
2. Always add `scope="row"` to row headers (first cell in each row if acting as header)
3. Test with screen reader: navigate to data cell and verify it announces associated headers
4. Add `<caption>` element to describe table purpose

**Warning signs:** Screen reader announces cell content but not associated headers when navigating table; Lighthouse flags "Cells in a `<table>` element that use the `headers` attribute refer to an element id not found within the same table."

### Pitfall 4: No Keyboard Focus Indicators
**What goes wrong:** Phase 16 added `:focus-visible` to `.job-item` but may have missed other interactive elements (dropdowns, buttons, links); keyboard users can't track focus position.

**Why it happens:** CSS resets often remove default outlines with `outline: none`; developers forget to add replacements for all interactive elements.

**How to avoid:**
1. Never use `outline: none` or `outline: 0` without replacement
2. Use `:focus-visible` pseudo-class (not `:focus`) to show indicators only for keyboard navigation
3. Test by tabbing through page without mouse; ensure every interactive element shows visible indicator
4. Use browser DevTools to force `:focus-visible` state and inspect all elements
5. Ensure contrast ratio of focus indicator against background meets 3:1 (WCAG 2.4.11 for Level AA in WCAG 2.2, but good practice for 2.1)

**Warning signs:** Tabbing through page with keyboard shows no visible change in appearance; focus "disappears" when reaching certain elements; dropdown items don't show which is focused.

### Pitfall 5: Terminal Colors Invisible to Colorblind Users
**What goes wrong:** Using red/green for status indicators (success/error) in terminal output means deuteranopia users (most common colorblindness, ~6% of males) cannot distinguish states.

**Why it happens:** Developers test with default vision; ANSI colors seem distinct on their screen.

**How to avoid:**
1. Pair color with text indicators: ✓/✗ symbols, SUCCESS/ERROR labels, or icons
2. Use colorblind-safe palettes: blue/orange instead of red/green
3. Test with colorblind simulation tools (Chrome DevTools has built-in vision deficiency emulator)
4. Honor `NO_COLOR` environment variable to disable all colors
5. Provide `--no-color` or `--plain` CLI flag for accessible output mode

**Warning signs:** Relying solely on color without text; using red/green for pass/fail; no option to disable colored output.

### Pitfall 6: Questionary Prompts Unreadable with Screen Readers
**What goes wrong:** Screen readers may not announce prompt questions, selection options, or confirmation of user choices in questionary interactive prompts.

**Why it happens:** Terminal UI libraries like prompt_toolkit (which questionary uses) render prompts as live-updating text in terminal buffer; screen readers designed for GUI applications may not parse terminal updates correctly.

**How to avoid:**
1. Test with NVDA on Windows terminal (Windows Terminal or Command Prompt)
2. Test with VoiceOver on macOS terminal (Terminal.app or iTerm2)
3. Provide alternative non-interactive mode: accept all inputs via CLI flags (e.g., `--profile resume.pdf --sources indeed --date-range 7`)
4. Document screen reader compatibility status in README
5. Consider echo/confirmation output: "Using profile: resume.pdf" after each selection

**Warning signs:** Manual testing with screen reader produces no audio; prompt appears visually but screen reader remains silent; user can type but gets no feedback on what they're entering.

### Pitfall 7: Notyf Toast Notifications Not Announced
**What goes wrong:** Notyf toast library (integrated in Phase 17) displays visual notifications for status changes, but screen readers don't announce them.

**Why it happens:** Notyf creates DOM elements dynamically for toasts; without proper ARIA live region wrapper, screen readers ignore them.

**How to avoid:**
1. Verify if Notyf includes `aria-live` attributes on toast container (check generated DOM)
2. If not, create custom ARIA live region and populate it when Notyf shows toast:
   ```javascript
   notyf.success('Status updated');
   document.getElementById('status-announcer').textContent = 'Status updated';
   ```
3. Or configure Notyf to use custom container with pre-existing `aria-live="polite"`
4. Test with screen reader: trigger toast and verify announcement

**Warning signs:** Visual toast appears but screen reader testing produces no announcement; checking DOM shows toast element lacks `aria-live` or `role="alert"`.

## Code Examples

Verified patterns from official sources:

### Skip Navigation Link (WebAIM Standard)
```html
<!-- Source: https://webaim.org/techniques/skipnav/ -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Job Search Results</title>
  <style>
    .skip-link {
      position: absolute;
      top: -40px;
      left: 0;
      background: #000;
      color: white;
      padding: 8px;
      text-decoration: none;
      z-index: 100;
    }
    .skip-link:focus {
      top: 0;
    }
  </style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <header role="banner">
    <h1>Job Search Results</h1>
  </header>

  <main id="main-content" role="main">
    <h2>Results for John Doe</h2>
    <!-- Content -->
  </main>
</body>
</html>
```

### Accessible Table with Contextual Badges
```html
<!-- Source: https://webaim.org/techniques/tables/data + Bootstrap 5 -->
<table class="table table-striped table-hover" aria-describedby="jobs-caption">
  <caption id="jobs-caption" class="visually-hidden">
    Job search results sorted by relevance score descending
  </caption>
  <thead>
    <tr>
      <th scope="col">#</th>
      <th scope="col">Score</th>
      <th scope="col">New</th>
      <th scope="col">Title</th>
      <th scope="col">Company</th>
      <th scope="col">Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">1</th>
      <td>
        <span class="visually-hidden">Score </span>
        4.2
        <span class="visually-hidden"> out of 5.0</span>
      </td>
      <td>
        <span class="badge bg-primary">
          <span class="visually-hidden">New listing, not seen in previous searches</span>
          NEW
        </span>
      </td>
      <td>Senior Software Engineer</td>
      <td>Acme Corp</td>
      <td>
        <a href="https://example.com/job/123"
           target="_blank"
           aria-label="View Senior Software Engineer at Acme Corp, opens in new tab">
          View
        </a>
      </td>
    </tr>
  </tbody>
</table>
```

### ARIA Live Region for Status Updates
```html
<!-- Source: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions -->
<!-- HTML: Create empty live region on page load -->
<div id="status-announcer"
     role="status"
     aria-live="polite"
     aria-atomic="true"
     class="visually-hidden">
</div>

<!-- JavaScript: Update status when dropdown changes -->
<script>
// Assuming existing Phase 17 status dropdown functionality
document.querySelectorAll('.status-dropdown .dropdown-item').forEach(item => {
  item.addEventListener('click', function(e) {
    e.preventDefault();

    const newStatus = this.dataset.status;
    const card = this.closest('.card');
    const jobTitle = card.dataset.jobTitle;
    const jobKey = card.dataset.jobKey;

    // Update visual dropdown (existing Phase 17 logic)
    updateStatusDropdown(card, newStatus);

    // NEW: Announce to screen reader
    const announcer = document.getElementById('status-announcer');
    if (newStatus) {
      announcer.textContent = `Status for ${jobTitle} changed to ${newStatus}`;
    } else {
      announcer.textContent = `Status cleared for ${jobTitle}`;
    }

    // Clear announcement after 1 second (optional)
    setTimeout(() => {
      announcer.textContent = '';
    }, 1000);
  });
});
</script>
```

### Focus Indicators for All Interactive Elements
```css
/* Source: WCAG 2.4.7 + Phase 16 implementation */

/* Job cards (already in Phase 16) */
.job-item:focus-visible {
  outline: 3px solid #0d6efd;
  outline-offset: 2px;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

/* Links */
a:focus-visible {
  outline: 2px solid #0d6efd;
  outline-offset: 2px;
  text-decoration: underline;
}

/* Buttons */
.btn:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

/* Dropdown items */
.dropdown-item:focus {
  background-color: #e9ecef;
  outline: 2px solid #0d6efd;
  outline-offset: -2px;
}

/* Dropdown toggle button */
.dropdown-toggle:focus-visible {
  outline: 2px solid #0d6efd;
  outline-offset: 2px;
}

/* Skip link (visible on focus) */
.skip-link:focus {
  top: 0;
  outline: 2px solid #fff;
  outline-offset: 2px;
}
```

### Semantic HTML Structure with ARIA Landmarks
```html
<!-- Source: W3C ARIA best practices + Bootstrap 5 -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Search Results — John Doe</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <!-- Skip link (first focusable element) -->
  <a href="#main-content" class="visually-hidden-focusable">Skip to main content</a>

  <!-- Semantic header with banner role -->
  <header role="banner" class="bg-primary text-white py-3">
    <div class="container">
      <h1 class="h3 mb-0">Job Search Results</h1>
    </div>
  </header>

  <!-- Main content area -->
  <main id="main-content" role="main">
    <div class="container my-4">

      <!-- Profile summary section -->
      <section aria-labelledby="profile-heading">
        <div class="card mb-4">
          <div class="card-header">
            <h2 id="profile-heading" class="h4 mb-0">Candidate Profile Summary</h2>
          </div>
          <div class="card-body">
            <ul class="list-unstyled mb-0">
              <li><strong>Name:</strong> John Doe</li>
              <li><strong>Role:</strong> Senior Software Engineer</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Jobs table section -->
      <section aria-labelledby="jobs-heading">
        <h2 id="jobs-heading" class="h4 mb-3">Job Listings</h2>
        <table class="table table-striped" aria-describedby="jobs-caption">
          <caption id="jobs-caption" class="visually-hidden">
            Job search results sorted by score
          </caption>
          <thead>
            <tr>
              <th scope="col">Score</th>
              <th scope="col">Title</th>
            </tr>
          </thead>
          <tbody>
            <!-- Job rows -->
          </tbody>
        </table>
      </section>

    </div>
  </main>

  <!-- Footer -->
  <footer role="contentinfo" class="bg-light py-3 mt-5">
    <div class="container">
      <p class="text-muted mb-0">Generated by Job Radar v1.3.0</p>
    </div>
  </footer>

  <!-- ARIA live region for announcements (hidden visually) -->
  <div id="status-announcer"
       role="status"
       aria-live="polite"
       aria-atomic="true"
       class="visually-hidden">
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WCAG 2.0 (2008) | WCAG 2.1 (2018, updated 2023) | June 2018 | Added 17 new success criteria focused on mobile, low vision, and cognitive disabilities; Level AA now includes 50 criteria total |
| `role` attributes only | Semantic HTML5 + explicit `role` | ~2015 | `<header role="banner">` provides maximum compatibility; older screen readers need explicit roles despite HTML5 semantics |
| Skip links always visible | Hidden until focused (`.visually-hidden-focusable`) | Bootstrap 4+ (2018) | Reduces visual clutter while maintaining accessibility; focus makes link appear for keyboard users |
| Complex `id`/`headers` for all tables | Simple `scope` attribute | WCAG 2.0 era | `scope="col"` sufficient for 99% of tables; simpler markup, better screen reader support; `headers` only for multi-level spanning |
| `aria-live` with timeouts | Create empty, populate via JS | ~2016 (MDN docs) | Live regions must exist before content updates; eliminates race conditions with screen reader buffer |
| Display colors only | NO_COLOR environment variable | 2020+ standard | Community standard; respects user preference to disable all ANSI colors in terminal output |
| Manual contrast checking | Automated tools (Lighthouse/axe-core) | 2019+ | Lighthouse detects ~57% of WCAG issues automatically; axe-core provides zero false positives |
| NVDA + JAWS only | Add VoiceOver, mobile screen readers | 2020+ | VoiceOver 10.5% market share; mobile screen readers growing; cross-platform testing now essential |

**Deprecated/outdated:**
- `summary` attribute on `<table>`: Deprecated in HTML5; use `<caption>` instead
- `aria-describedby` pointing to non-existent IDs: Common error; always verify ID exists
- Positioning skip links off-screen with negative `left` values: Breaks screen magnifiers; use `.visually-hidden-focusable` or absolute positioning with negative `top` instead
- Using `display:none` for visually hidden content: Removes from accessibility tree; use `.visually-hidden` pattern
- Bootstrap 4's `.sr-only`: Renamed to `.visually-hidden` in Bootstrap 5 (2021) for clarity

## Open Questions

### 1. Does questionary library support screen readers (NVDA/JAWS/VoiceOver)?
- **What we know:** Questionary uses prompt_toolkit for terminal UI; prompt_toolkit has Unicode support and cross-platform terminal handling; no documentation exists on screen reader compatibility for either library.
- **What's unclear:** Whether terminal screen readers (NVDA with terminal, VoiceOver with Terminal.app) can parse and announce questionary's interactive prompts (selection menus, confirmations); whether user input is echoed audibly; whether arrow key navigation of options is announced.
- **Recommendation:** LOW confidence in questionary screen reader support. Mitigation strategies:
  1. Implement CLI flag-based alternative: `job-radar --profile resume.pdf --sources indeed linkedin --min-score 2.8` (bypasses interactive wizard)
  2. Test manually with NVDA (Windows) and VoiceOver (macOS) in terminal environment
  3. Document findings in README accessibility section
  4. Consider post-v1.3.0 investigation of alternative CLI libraries (Click with simple prompts, argparse with confirmation flags)
  5. For v1.3.0, prioritize HTML report accessibility (achievable) over CLI wizard accessibility (uncertain)

### 2. Do terminal colors (colorama/rich) meet contrast requirements for colorblind users?
- **What we know:** Project uses colorama (in pyproject.toml); modern terminals support ANSI 4-bit colors; colorblind accessibility requires avoiding red/green for critical distinctions; NO_COLOR environment variable is community standard.
- **What's unclear:** Which specific colors are used in current CLI output; whether red/green are used for status indicators; whether contrast ratios meet WCAG standards on default terminal backgrounds (black/white).
- **Recommendation:** MEDIUM confidence that colorama output can be made accessible. Actions:
  1. Audit current CLI output: identify all color usage (info, warnings, errors, success)
  2. Test with Chrome DevTools colorblind simulator (protanopia, deuteranopia, tritanopia)
  3. Ensure colors are paired with text indicators (✓/✗ symbols, SUCCESS/ERROR labels)
  4. Implement NO_COLOR support: `if os.getenv('NO_COLOR'): disable_colors()`
  5. Provide `--no-color` CLI flag as explicit alternative
  6. Use colorblind-safe palette: blue for info, orange/amber for warnings, keep red for errors (but pair with "ERROR:" text)

### 3. How to test Lighthouse accessibility score for file:// protocol reports?
- **What we know:** HTML reports are opened via `file://` protocol (local filesystem); Lighthouse in Chrome DevTools works on `file://` URLs; target score is ≥95 for success criterion A11Y-10.
- **What's unclear:** Whether all Lighthouse checks work on `file://` (some require HTTP headers); whether CDN resources (Bootstrap) cause warnings; whether score is reproducible across environments.
- **Recommendation:** HIGH confidence Lighthouse works for this use case. Test procedure:
  1. Generate HTML report
  2. Open in Chrome: `chrome file:///path/to/report.html` (or drag into browser)
  3. Open DevTools (F12) → Lighthouse tab
  4. Select "Accessibility" category, "Desktop" device, click "Analyze page load"
  5. Review score and flagged issues
  6. Iterate: fix issues, regenerate report, re-test until score ≥95
  7. Document score in verification results (Phase 18 verification plan)

### 4. Should we test with WCAG 2.2 or stick to 2.1 Level AA?
- **What we know:** Phase scope specifies WCAG 2.1 Level AA; WCAG 2.2 was published August 2023 (newer); WCAG 2.2 is backward compatible (all 2.1 criteria remain, 9 new criteria added at Level A/AA).
- **What's unclear:** Whether targeting 2.2 adds significant implementation effort; whether 2.2 tools/documentation are mature.
- **Recommendation:** MEDIUM confidence to stay with 2.1 for v1.3.0. Rationale:
  1. Phase explicitly scopes to WCAG 2.1 Level AA
  2. WCAG 2.2 Level AA adds criteria like 2.4.11 Focus Appearance (more stringent than 2.4.7 Focus Visible), 2.4.13 Focus Not Obscured, 3.2.6 Consistent Help, 3.3.7 Redundant Entry, 3.3.8 Accessible Authentication
  3. Most new 2.2 criteria apply to complex web apps (authentication flows, help systems); Job Radar reports are static read-only HTML
  4. Lighthouse currently tests against WCAG 2.1 + some 2.2 criteria
  5. Post-v1.3.0: Evaluate WCAG 2.2 adoption if reports become interactive (e.g., filters, search)

## Sources

### Primary (HIGH confidence)
- [WCAG 2.1 Official Specification](https://www.w3.org/TR/WCAG21/) - Complete success criteria
- [Bootstrap 5.3 Accessibility Documentation](https://getbootstrap.com/docs/5.3/getting-started/accessibility/) - Built-in features and limitations
- [WebAIM: Skip Navigation Links](https://webaim.org/techniques/skipnav/) - Implementation patterns
- [WebAIM: Creating Accessible Tables](https://webaim.org/techniques/tables/data) - Scope attribute usage
- [MDN: ARIA Live Regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions) - Complete implementation guide
- [WebAIM: CSS Invisible Content](https://webaim.org/techniques/css/invisiblecontent/) - Visually hidden pattern
- [W3C: Understanding WCAG 2.4.7 Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) - Focus indicator requirements
- [Lighthouse Accessibility Scoring](https://developer.chrome.com/docs/lighthouse/accessibility/scoring) - How scores are calculated
- [Deque axe-core](https://github.com/dequelabs/axe-core) - Automated testing engine

### Secondary (MEDIUM confidence)
- [GitHub CLI Accessible Experiences](https://github.com/orgs/community/discussions/158037) - Terminal CLI best practices (2026)
- [Choosing readable ANSI colors for CLIs](https://trentm.com/2024/09/choosing-readable-ansi-colors-for-clis.html) - Colorblind accessibility
- [Screen Reader Testing Guide](https://testparty.ai/blog/screen-reader-testing-guide) - NVDA/JAWS/VoiceOver methodology
- [NVDA vs JAWS Comparison](https://www.uxpin.com/studio/blog/nvda-vs-jaws-screen-reader-testing-comparison/) - Screen reader testing approach
- [The A11Y Collective: ARIA Live](https://www.a11y-collective.com/blog/aria-live/) - Best practices guide
- [Sara Soueidan: Accessible Notifications](https://www.sarasoueidan.com/blog/accessible-notifications-with-aria-live-regions-part-1/) - Live region patterns

### Tertiary (LOW confidence)
- [Questionary PyPI](https://pypi.org/project/questionary/) - Library overview (no accessibility docs)
- [prompt_toolkit GitHub](https://github.com/prompt-toolkit/python-prompt-toolkit) - Terminal library (no screen reader info)
- [Rich library documentation](https://rich.readthedocs.io/) - Terminal colors (no accessibility features documented)
- Web searches for "questionary screen reader" - No results found; needs manual testing
- Web searches for "prompt_toolkit accessibility" - No dedicated documentation; LOW confidence

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Bootstrap 5, Lighthouse, axe-core are industry standards with extensive documentation
- HTML architecture patterns: HIGH - All patterns sourced from W3C, WebAIM, MDN with verified code examples
- CLI accessibility: MEDIUM - General best practices documented (NO_COLOR, colorblind colors) but questionary-specific support unknown
- Questionary screen reader support: LOW - No documentation found; requires manual testing with NVDA/JAWS/VoiceOver
- Testing methodology: HIGH - Lighthouse, NVDA, JAWS, VoiceOver are standard tools with clear usage docs

**Research date:** 2026-02-11
**Valid until:** 2026-04-11 (60 days for stable WCAG 2.1 standards; WCAG 2.2 adoption may accelerate, re-check quarterly)
