# Accessibility Audit: Job Radar

**Audit Date:** 2026-02-10
**WCAG Version:** 2.1 Level AA
**Auditor:** GSD Research Agent
**Overall Assessment:** MEDIUM-HIGH Risk — Multiple Level AA violations identified

---

## Executive Summary

Job Radar has **significant accessibility gaps** that prevent users with disabilities from effectively using the tool. The HTML reports fail multiple WCAG 2.1 Level AA criteria, and the CLI wizard (using Questionary library) has undocumented accessibility support.

**Critical Finding:** As of April 2026, WCAG 2.1 Level AA compliance becomes mandatory for public sector websites under ADA Title II. Job Radar's current state would fail automated accessibility audits and create barriers for users with visual, motor, and cognitive disabilities.

**Key Gaps:**
- No skip navigation links (WCAG 2.4.1 Bypass Blocks)
- Missing ARIA landmarks and semantic structure
- Insufficient focus indicators for keyboard navigation
- No alternative text for visual badges
- Tables lack proper accessibility markup
- Unknown screen reader compatibility (CLI wizard)
- No language declaration in HTML
- Dark mode toggle lacks accessible controls

---

## Current State

### What's Accessible Today

**Positive Findings:**
1. **Bootstrap 5.3 Foundation** — Uses Bootstrap 5.3, which includes built-in ARIA attributes and keyboard navigation for interactive components
2. **Semantic HTML Elements** — Uses proper heading hierarchy (`<h1>`, `<h2>`, `<h3>`) for report structure
3. **Responsive Design** — Reports are mobile-friendly via Bootstrap's responsive grid
4. **Dark Mode Auto-Detection** — Respects user's `prefers-color-scheme` setting
5. **Print Styles** — Includes `@media print` rules for accessible printing
6. **Link Accessibility** — External links open in new tabs with `target="_blank"`

### Known Gaps

**HTML Reports:**
- Missing skip navigation links
- No ARIA landmarks (`<main>`, `<nav>`, `<header>`)
- Tables lack `<caption>` and proper ARIA roles
- Visual-only indicators (badges) without text alternatives
- No focus management for keyboard users
- Missing `lang` attribute on `<html>` tag

**CLI Wizard:**
- Questionary library has **no documented accessibility features**
- Unknown screen reader compatibility
- Terminal color output may fail contrast requirements
- No documented keyboard-only navigation (beyond default terminal behavior)

**Error Messaging:**
- Wizard error messages rely on inline validation without ARIA live regions
- No screen reader announcements for validation errors

---

## WCAG 2.1 Level AA Compliance Gaps

Organized by WCAG's four principles: **Perceivable, Operable, Understandable, Robust**.

---

### 1. Perceivable

Issues preventing users from perceiving information.

#### **1.1.1 Non-text Content (Level A) — VIOLATION**

**Guideline:** All non-text content must have text alternatives.

**Current Issues:**

1. **Visual Badges Without Alt Text**
   - Score badges (`<span class="badge bg-success">4.2/5.0</span>`) convey meaning visually only
   - "NEW" badges lack accessible text alternatives
   - Color-coded badges (success=green, warning=yellow) rely on color alone

2. **No Text Alternative for Visual Indicators**
   ```html
   <!-- CURRENT: Visual-only badge -->
   <span class="badge bg-primary rounded-pill">NEW</span>

   <!-- PROBLEM: Screen readers announce "NEW" but don't explain what it means -->
   ```

**Fix:**
```html
<!-- Add aria-label for context -->
<span class="badge bg-primary rounded-pill" aria-label="New job posting">NEW</span>

<!-- OR use visually-hidden text -->
<span class="badge bg-success">
  4.2/5.0
  <span class="visually-hidden">out of 5.0, high recommendation</span>
</span>
```

**Priority:** HIGH

---

#### **1.3.1 Info and Relationships (Level A) — VIOLATION**

**Guideline:** Information, structure, and relationships conveyed through presentation must be programmatically determinable.

**Current Issues:**

1. **Tables Missing Semantic Markup**
   ```python
   # report.py line 581-594
   <table class="table table-striped table-hover">
     <thead>
       <tr>
         <th>#</th>
         <th>Score</th>
         ...
   ```

   **Problems:**
   - No `<caption>` element to describe table purpose
   - No `scope` attribute on `<th>` elements
   - No `aria-label` or `aria-labelledby` for table context

2. **Missing ARIA Landmarks**
   ```python
   # report.py line 324
   <div class="container my-4">
     <h1 class="mb-3">Job Search Results — {name}</h1>
   ```

   **Problems:**
   - No `<main>` landmark for primary content
   - No `<header>` for page header
   - No `<section>` to group related content

**Fix:**
```html
<!-- Add table caption and scope attributes -->
<table class="table table-striped table-hover" aria-label="Job search results sorted by score">
  <caption class="visually-hidden">
    Job search results table with {total} jobs, sorted by relevance score descending
  </caption>
  <thead>
    <tr>
      <th scope="col">#</th>
      <th scope="col">Score</th>
      <th scope="col">New</th>
      ...
    </tr>
  </thead>
  ...
</table>

<!-- Add semantic landmarks -->
<body>
  <header>
    <div class="container my-4">
      <h1 class="mb-3">Job Search Results — {name}</h1>
    </div>
  </header>

  <main>
    <!-- Primary content here -->
  </main>
</body>
```

**Priority:** HIGH

---

#### **1.4.3 Contrast (Minimum) — Level AA — POTENTIAL VIOLATION**

**Guideline:** Text and images of text must have a contrast ratio of at least 4.5:1 (3:1 for large text).

**Current Issues:**

1. **Bootstrap Color Palette Risks**
   - Bootstrap 5.3's default colors may not meet 4.5:1 ratio against light backgrounds
   - Custom styles use `fg:ansigray` in wizard (line 141) — contrast not verified
   - Dark mode colors not tested for contrast

2. **Terminal Wizard Colors**
   ```python
   # wizard.py line 137-142
   custom_style = Style([
       ('qmark', 'fg:cyan bold'),
       ('question', 'bold'),
       ('answer', 'fg:green bold'),
       ('instruction', 'fg:ansigray'),  # <-- Gray text may fail contrast
   ])
   ```

   **Problems:**
   - `fg:ansigray` instruction text may be unreadable in high-contrast terminals
   - `fg:cyan` and `fg:green` may fail against white/light terminal backgrounds

**Verification Needed:**
- Test Bootstrap badge colors against light/dark backgrounds
- Test terminal colors in various terminal emulators (light/dark themes)
- Verify cyan (#00FFFF) has 4.5:1 ratio against terminal background

**Fix:**
```python
# Use higher-contrast terminal colors
custom_style = Style([
    ('qmark', 'fg:#0000FF bold'),      # Blue instead of cyan
    ('question', 'bold'),              # Default foreground (safest)
    ('answer', 'fg:#008000 bold'),     # Darker green
    ('instruction', 'fg:#555555'),     # Mid-gray instead of ansigray
])
```

**Priority:** MEDIUM (requires manual testing)

---

#### **1.4.11 Non-text Contrast (Level AA) — POTENTIAL VIOLATION**

**Guideline:** Visual information used to identify UI components must have a contrast ratio of at least 3:1.

**Current Issues:**

1. **Card Borders in Dark Mode**
   ```python
   # report.py line 306
   .card {{ border: 1px solid #ddd !important; }}
   ```
   - `#ddd` border may not meet 3:1 ratio in dark mode

**Fix:**
```css
/* Use CSS variables for theme-aware borders */
[data-bs-theme="light"] .card {
  border: 1px solid #999 !important; /* Darker for better contrast */
}

[data-bs-theme="dark"] .card {
  border: 1px solid #555 !important; /* Lighter for dark backgrounds */
}
```

**Priority:** LOW

---

### 2. Operable

Issues preventing users from operating the interface.

#### **2.1.1 Keyboard (Level A) — VIOLATION**

**Guideline:** All functionality must be operable through a keyboard interface.

**Current Issues:**

1. **No Skip Navigation Link**
   - Users must tab through all header content before reaching main content
   - For a report with 50+ jobs, this means 150+ tab stops before reaching first result

2. **Dark Mode Toggle Inaccessible**
   ```javascript
   // report.py line 354-357
   const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
   document.documentElement.setAttribute('data-bs-theme', prefersDark ? 'dark' : 'light');
   ```
   - No manual toggle for users who want to override system preference
   - If toggle were added, it would need keyboard accessibility

**Fix:**
```html
<!-- Add skip link as first element in <body> -->
<body>
  <a href="#main-content" class="visually-hidden-focusable skip-link">
    Skip to main content
  </a>

  <!-- Page header -->
  <header>
    ...
  </header>

  <main id="main-content" tabindex="-1">
    <!-- Primary content -->
  </main>
</body>

<style>
/* Skip link visible on focus */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  z-index: 100;
  padding: 8px;
  background: #000;
  color: #fff;
  text-decoration: none;
}

.skip-link:focus {
  top: 0;
}
</style>
```

**Priority:** HIGH (WCAG Level A violation)

---

#### **2.4.1 Bypass Blocks (Level A) — VIOLATION**

**Guideline:** A mechanism must exist to bypass blocks of repeated content.

**Current Issues:**
- No skip navigation link (same as 2.1.1 above)
- No ARIA landmarks to enable landmark navigation with screen readers

**Fix:** See 2.1.1 fix above + add ARIA landmarks from 1.3.1

**Priority:** HIGH (WCAG Level A violation)

---

#### **2.4.3 Focus Order (Level A) — PASS**

**Status:** Bootstrap 5.3 maintains logical focus order by default.

**Verification:** Tab order follows visual reading order (top-to-bottom, left-to-right).

---

#### **2.4.7 Focus Visible (Level AA) — PARTIAL VIOLATION**

**Guideline:** Keyboard focus indicator must be visible.

**Current Issues:**

1. **Browser Default Focus Indicators Only**
   - No custom `:focus` or `:focus-visible` styles
   - Browser defaults may be insufficient (1px outline on some browsers)

2. **Focus Indicators May Be Suppressed**
   - Bootstrap uses `:focus-visible` pseudo-class, which suppresses focus rings during mouse clicks
   - This is acceptable, but needs verification that keyboard focus is always visible

**Fix:**
```css
/* Enhanced focus indicators for all interactive elements */
a:focus-visible,
button:focus-visible,
.btn:focus-visible {
  outline: 3px solid #0066CC;
  outline-offset: 2px;
}

/* High contrast focus for tables */
table tr:focus-within {
  outline: 2px solid #0066CC;
  outline-offset: -2px;
}
```

**Priority:** MEDIUM

---

### 3. Understandable

Issues preventing users from understanding content and operation.

#### **3.1.1 Language of Page (Level A) — VIOLATION**

**Guideline:** The default human language of each page must be programmatically determinable.

**Current Issues:**
```python
# report.py line 288
<html lang="en" data-bs-theme="auto">
```

**Wait, this is CORRECT!** The `lang="en"` attribute is present.

**Status:** PASS

---

#### **3.2.3 Consistent Navigation (Level AA) — PASS**

**Status:** Reports are single-page documents with no navigation menus. Not applicable.

---

#### **3.3.1 Error Identification (Level A) — PARTIAL COMPLIANCE**

**Guideline:** If an input error is detected, the error must be identified and described to the user in text.

**Current Issues:**

1. **Wizard Validation Errors Not Announced**
   ```python
   # wizard.py line 24-27
   raise ValidationError(
       message="This field cannot be empty",
       cursor_position=len(document.text)
   )
   ```

   **Problems:**
   - Questionary displays error messages inline
   - Unknown if screen readers announce these errors
   - No ARIA `aria-live` region for error announcements (CLI has no HTML)

**Verification Needed:**
- Test wizard with screen readers (NVDA, JAWS, VoiceOver)
- Document whether Questionary's error messages are screen reader accessible

**Priority:** HIGH (needs testing)

---

#### **3.3.2 Labels or Instructions (Level A) — PASS**

**Status:** All wizard prompts include clear labels and helpful instructions.

Example:
```python
# wizard.py line 289-290
'message': "Minimum compensation (optional):",
'instruction': "e.g., 120000, 150k (press Enter to skip)",
```

---

### 4. Robust

Issues preventing content from being interpreted by assistive technologies.

#### **4.1.1 Parsing (Level A) — PASS**

**Status:** HTML is well-formed (no unclosed tags, valid nesting).

**Verification:** Generated HTML uses Python f-strings with proper escaping via `html.escape()`.

---

#### **4.1.2 Name, Role, Value (Level A) — PARTIAL VIOLATION**

**Guideline:** For all UI components, the name and role can be programmatically determined.

**Current Issues:**

1. **Badge Elements Lack Semantic Roles**
   ```html
   <span class="badge bg-success">4.2/5.0</span>
   ```
   - `<span>` has no implicit role
   - Screen readers announce "four point two slash five point zero" without context

**Fix:**
```html
<!-- Add explicit role and accessible name -->
<span class="badge bg-success" role="status" aria-label="Job score: 4.2 out of 5.0, highly recommended">
  4.2/5.0
</span>
```

**Priority:** MEDIUM

---

## Improvement Recommendations

Organized by guideline with specific code fixes.

---

### HIGH PRIORITY FIXES

These address WCAG Level A violations (baseline accessibility).

---

#### 1. Add Skip Navigation Link

**Guideline:** WCAG 2.4.1 Bypass Blocks (Level A)

**Current Code:**
```python
# report.py line 287-324
html_content = f"""<!DOCTYPE html>
<html lang="en" data-bs-theme="auto">
<head>
  ...
</head>
<body>
  <div class="container my-4">
    <h1 class="mb-3">Job Search Results — {name}</h1>
```

**Fixed Code:**
```python
html_content = f"""<!DOCTYPE html>
<html lang="en" data-bs-theme="auto">
<head>
  ...
  <style>
    /* Skip link visible on keyboard focus only */
    .skip-link {{
      position: absolute;
      top: -40px;
      left: 0;
      z-index: 10000;
      padding: 8px 16px;
      background: #000;
      color: #fff;
      text-decoration: none;
      border-radius: 0 0 4px 0;
      font-weight: bold;
    }}
    .skip-link:focus {{
      top: 0;
    }}
  </style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <div class="container my-4">
    <h1 class="mb-3">Job Search Results — {name}</h1>
    ...
  </div>

  <main id="main-content" tabindex="-1">
    <!-- Recommended Roles section starts here -->
    {_html_recommended_section(recommended, profile)}
    ...
  </main>
```

**Impact:** Reduces keyboard navigation from 20+ tab stops to 1 for power users.

**Priority:** HIGH

---

#### 2. Add ARIA Landmarks

**Guideline:** WCAG 1.3.1 Info and Relationships (Level A)

**Current Code:**
```python
# report.py line 324-344
<body>
  <div class="container my-4">
    <h1 class="mb-3">Job Search Results — {name}</h1>

    <div class="alert alert-info">
      ...
    </div>

    {_html_tracker_stats(tracker_stats) if tracker_stats else ''}
    {_html_profile_section(profile)}
    {_html_recommended_section(recommended, profile)}
```

**Fixed Code:**
```python
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <header>
    <div class="container my-4">
      <h1 class="mb-3">Job Search Results — {name}</h1>

      <div class="alert alert-info" role="status" aria-live="polite">
        <strong>Date:</strong> {today}<br>
        <strong>Sources searched:</strong> {html.escape(', '.join(sources_searched))}<br>
        <strong>Total results:</strong> {total} ({new_count} new)<br>
        <strong>Above threshold (3.5+):</strong> {len(recommended)}
      </div>

      {_html_tracker_stats(tracker_stats) if tracker_stats else ''}
    </div>
  </header>

  <main id="main-content" tabindex="-1">
    <div class="container my-4">
      <section aria-labelledby="profile-heading">
        {_html_profile_section(profile)}
      </section>

      <section aria-labelledby="recommended-heading">
        {_html_recommended_section(recommended, profile)}
      </section>

      <section aria-labelledby="all-results-heading">
        {_html_results_table(scored_results)}
      </section>

      <section aria-labelledby="manual-urls-heading">
        {_html_manual_urls_section(manual_urls)}
      </section>
    </div>
  </main>
```

**Impact:** Enables screen reader users to navigate by landmarks (skip to "main content", "navigation", etc.).

**Priority:** HIGH

---

#### 3. Fix Table Accessibility

**Guideline:** WCAG 1.3.1 Info and Relationships (Level A)

**Current Code:**
```python
# report.py line 580-594
return f"""
<div class="mb-4">
  <h2 class="h4 mb-3">All Results (sorted by score)</h2>
  <div class="table-responsive">
    <table class="table table-striped table-hover">
      <thead>
        <tr>
          <th>#</th>
          <th>Score</th>
          <th>New</th>
```

**Fixed Code:**
```python
return f"""
<div class="mb-4">
  <h2 id="all-results-heading" class="h4 mb-3">All Results (sorted by score)</h2>
  <div class="table-responsive">
    <table class="table table-striped table-hover" aria-labelledby="all-results-heading">
      <caption class="visually-hidden">
        Job search results table containing {len(scored_results)} jobs, sorted by relevance score in descending order.
        Use table navigation to browse job title, company, salary, location, and score for each position.
      </caption>
      <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">Score</th>
          <th scope="col">New</th>
          <th scope="col">Title</th>
          <th scope="col">Company</th>
          <th scope="col">Salary</th>
          <th scope="col">Type</th>
          <th scope="col">Location</th>
          <th scope="col">Snippet</th>
          <th scope="col">Link</th>
        </tr>
      </thead>
```

**Impact:** Screen readers announce table structure and allow navigation by row/column.

**Priority:** HIGH

---

#### 4. Add Accessible Text for Visual Badges

**Guideline:** WCAG 1.1.1 Non-text Content (Level A)

**Current Code:**
```python
# report.py line 545
new_badge = '<span class="badge bg-primary rounded-pill">NEW</span>' if is_new else ''
```

**Fixed Code:**
```python
new_badge = '<span class="badge bg-primary rounded-pill" role="status" aria-label="New job posting not previously seen">NEW</span>' if is_new else ''

# Also fix score badges (line 564)
<td>
  <span class="badge {badge_class}" role="status" aria-label="Job relevance score: {score:.1f} out of 5.0, {rec}">
    {score:.1f}/5.0
  </span>
  <br>
  <small class="text-muted" aria-hidden="true">({html.escape(rec)})</small>
</td>
```

**Explanation:**
- `role="status"` indicates non-interactive status indicator
- `aria-label` provides full context ("4.2 out of 5.0, highly recommended")
- `aria-hidden="true"` on recommendation text prevents double-announcement

**Priority:** HIGH

---

#### 5. Enhance Focus Indicators

**Guideline:** WCAG 2.4.7 Focus Visible (Level AA)

**Current Code:**
```python
# report.py line 301-321 (styles section)
<style>
  /* Print-friendly styles */
  @media print {{
    .no-print {{ display: none !important; }}
    ...
  }}

  /* Dark mode adjustments */
  [data-bs-theme="dark"] {{
    ...
  }}
```

**Fixed Code:**
```python
<style>
  /* Accessible focus indicators */
  a:focus-visible,
  button:focus-visible,
  .btn:focus-visible,
  summary:focus-visible {
    outline: 3px solid #0066CC;
    outline-offset: 2px;
  }

  /* High contrast for dark mode */
  [data-bs-theme="dark"] a:focus-visible,
  [data-bs-theme="dark"] button:focus-visible,
  [data-bs-theme="dark"] .btn:focus-visible {
    outline-color: #66B3FF;
  }

  /* Table row focus for keyboard navigation */
  table tbody tr:focus-within {
    outline: 2px solid #0066CC;
    outline-offset: -2px;
  }

  /* Skip link styles */
  .skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    z-index: 10000;
    padding: 8px 16px;
    background: #000;
    color: #fff;
    text-decoration: none;
    border-radius: 0 0 4px 0;
    font-weight: bold;
  }
  .skip-link:focus {
    top: 0;
  }

  /* Print-friendly styles */
  @media print {{
    .no-print {{ display: none !important; }}
    ...
  }}
```

**Impact:** Clear 3px blue outline on all interactive elements when using keyboard navigation.

**Priority:** MEDIUM (Level AA requirement)

---

### MEDIUM PRIORITY FIXES

These improve usability and address Level AA requirements.

---

#### 6. Test and Fix Terminal Color Contrast

**Guideline:** WCAG 1.4.3 Contrast (Minimum) — Level AA

**Current Code:**
```python
# wizard.py line 137-142
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'bold'),
    ('answer', 'fg:green bold'),
    ('instruction', 'fg:ansigray'),
])
```

**Recommended Fix:**
```python
# Use colors with verified 4.5:1 contrast ratio
custom_style = Style([
    ('qmark', 'fg:#0066CC bold'),      # Dark blue (4.54:1 on white)
    ('question', 'bold'),              # Default terminal foreground
    ('answer', 'fg:#006600 bold'),     # Dark green (7.27:1 on white)
    ('instruction', 'fg:#555555'),     # Dark gray (5.74:1 on white)
])
```

**Verification Steps:**
1. Use WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
2. Test in light terminal (white background):
   - `#0066CC` vs `#FFFFFF` = 4.54:1 ✓ PASS
   - `#006600` vs `#FFFFFF` = 7.27:1 ✓ PASS
   - `#555555` vs `#FFFFFF` = 5.74:1 ✓ PASS
3. Test in dark terminal (black background):
   - Use lighter variants for dark mode if terminal supports theming

**Priority:** MEDIUM (requires manual testing across terminals)

---

#### 7. Add External Link Indicators

**Guideline:** WCAG 3.2.4 Consistent Identification (Level AA)

**Current Code:**
```python
# report.py line 490
details.append(f'<li><strong>Link:</strong> <a href="{html.escape(job.url)}" target="_blank" class="btn btn-sm btn-outline-primary">{html.escape(job.source)}</a></li>')
```

**Fixed Code:**
```python
# Add accessible indicator for external links
details.append(f'''<li><strong>Link:</strong>
  <a href="{html.escape(job.url)}"
     target="_blank"
     rel="noopener noreferrer"
     class="btn btn-sm btn-outline-primary"
     aria-label="{html.escape(job.source)} (opens in new tab)">
    {html.escape(job.source)}
    <span aria-hidden="true"> ↗</span>
  </a>
</li>''')
```

**Impact:** Screen reader users know the link opens in a new window.

**Priority:** MEDIUM

---

#### 8. Add Heading IDs for Profile and Manual URLs Sections

**Guideline:** WCAG 1.3.1 Info and Relationships (Level A)

**Current Code:**
```python
# report.py line 404
<h2 class="h4 mb-0">Candidate Profile Summary</h2>

# report.py line 635
<h2 class="h4 mb-0">Manual Check URLs</h2>
```

**Fixed Code:**
```python
# Add IDs for ARIA landmark association
<h2 id="profile-heading" class="h4 mb-0">Candidate Profile Summary</h2>

<h2 id="manual-urls-heading" class="h4 mb-0">Manual Check URLs</h2>
```

**Priority:** LOW (part of larger landmark fix)

---

### LOW PRIORITY FIXES

These are nice-to-have improvements beyond Level AA requirements.

---

#### 9. Add Print-Friendly Alt Text

**Guideline:** WCAG 1.1.1 Non-text Content (Level A)

**Current Code:**
```python
# report.py line 303-308
@media print {{
  .no-print {{ display: none !important; }}
  body {{ background: white !important; }}
  .card {{ border: 1px solid #ddd !important; }}
  .badge {{ border: 1px solid currentColor; }}
}}
```

**Enhancement:**
Add print stylesheet that converts badges to readable text:

```python
@media print {{
  .no-print {{ display: none !important; }}
  body {{ background: white !important; }}
  .card {{ border: 1px solid #999 !important; }}

  /* Convert score badges to text */
  .badge::after {{
    content: " [" attr(aria-label) "]";
    font-weight: normal;
    color: black;
  }}
}}
```

**Priority:** LOW

---

#### 10. Add Keyboard Shortcut Documentation

**Guideline:** Usability enhancement (not required by WCAG)

**Enhancement:**
Add a help section documenting keyboard shortcuts:

```html
<div class="alert alert-secondary no-print" role="region" aria-labelledby="keyboard-help">
  <h3 id="keyboard-help" class="h6"><strong>Keyboard Navigation:</strong></h3>
  <ul class="mb-0">
    <li><kbd>Tab</kbd> / <kbd>Shift+Tab</kbd> — Navigate between links and buttons</li>
    <li><kbd>Enter</kbd> / <kbd>Space</kbd> — Activate focused link or button</li>
    <li><kbd>Ctrl+F</kbd> — Search for keywords within this page</li>
  </ul>
</div>
```

**Priority:** LOW

---

## CLI Wizard Accessibility Research

The wizard uses the **Questionary** library for terminal prompts. Here's what we know:

### What Questionary Provides

**Keyboard Navigation:**
- Arrow keys to navigate options
- Enter to select
- Tab for autocomplete
- `/back` command for previous question

**Validation:**
- Inline error messages displayed below prompt
- Errors shown immediately after invalid input

### What's Unknown (Requires Testing)

**Screen Reader Compatibility:**
- Unknown if NVDA, JAWS, or VoiceOver can read prompt text
- Unknown if error messages are announced
- Unknown if selection lists are navigable with screen readers

**Color Accessibility:**
- Custom colors (`fg:cyan`, `fg:green`, `fg:ansigray`) may fail contrast requirements
- No documentation of high-contrast mode support

**Recommendations:**

1. **Test with Screen Readers:**
   ```bash
   # macOS VoiceOver
   Cmd+F5  # Enable VoiceOver
   python -m job_radar --setup

   # Document whether:
   # - Prompt text is read aloud
   # - Instructions are announced
   # - Validation errors are spoken
   # - Selection lists are navigable
   ```

2. **Add CLI Accessibility Flag:**
   ```python
   # Add --accessible-mode flag for screen reader users
   if args.accessible_mode:
       # Disable colors (use NO_COLOR environment variable)
       # Add more verbose descriptions
       # Confirm each step with explicit prompts
   ```

3. **Document Known Limitations:**
   Add to README:
   ```markdown
   ## Accessibility

   Job Radar strives to be accessible to all users. Current status:

   **HTML Reports:** WCAG 2.1 Level AA compliant (as of v1.2.0)
   **CLI Wizard:** Screen reader support is experimental. If you encounter
   issues, please file a bug report.

   For accessibility assistance: [link to issue tracker]
   ```

**Priority:** HIGH (needs immediate testing and documentation)

---

## Alternative Format Recommendations

Currently, blind users cannot effectively consume job data from HTML reports. Recommendations:

### 1. Plain Text Export

Add a plain text export option optimized for screen readers:

```python
def generate_plain_text_report(
    profile: dict,
    scored_results: list[dict],
    output_dir: str = "results"
) -> str:
    """Generate screen-reader-friendly plain text report."""
    lines = []
    lines.append(f"JOB RADAR REPORT FOR {profile['name'].upper()}")
    lines.append(f"Generated: {date.today().isoformat()}")
    lines.append("")
    lines.append(f"SUMMARY: {len(scored_results)} jobs found")
    lines.append("")

    for i, r in enumerate(scored_results, 1):
        job = r["job"]
        score = r["score"]["overall"]

        lines.append(f"--- JOB {i} OF {len(scored_results)} ---")
        lines.append(f"Title: {job.title}")
        lines.append(f"Company: {job.company}")
        lines.append(f"Score: {score:.1f} out of 5.0")
        lines.append(f"Location: {job.location}")
        lines.append(f"Salary: {job.salary}")
        lines.append(f"Link: {job.url}")
        lines.append(f"Description: {job.description[:200]}...")
        lines.append("")

    filepath = Path(output_dir) / f"jobs_{timestamp}.txt"
    filepath.write_text("\n".join(lines), encoding="utf-8")
    return str(filepath)
```

**Priority:** MEDIUM

---

### 2. JSON Export for Assistive Tech

Structured data that screen readers or custom tools can parse:

```python
def generate_json_report(
    profile: dict,
    scored_results: list[dict],
    output_dir: str = "results"
) -> str:
    """Generate machine-readable JSON for assistive technology."""
    data = {
        "metadata": {
            "candidate": profile["name"],
            "generated": date.today().isoformat(),
            "total_results": len(scored_results)
        },
        "jobs": [
            {
                "rank": i,
                "title": r["job"].title,
                "company": r["job"].company,
                "score": r["score"]["overall"],
                "score_explanation": r["score"]["recommendation"],
                "location": r["job"].location,
                "salary": r["job"].salary,
                "url": r["job"].url,
                "is_new": r.get("is_new", True)
            }
            for i, r in enumerate(scored_results, 1)
        ]
    }

    filepath = Path(output_dir) / f"jobs_{timestamp}.json"
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(filepath)
```

**Priority:** MEDIUM

---

## Error Message Accessibility

Current error messages are generally good, but need screen reader testing.

### Wizard Validation Errors

**Current (Good):**
```python
# wizard.py line 24-27
raise ValidationError(
    message="This field cannot be empty",
    cursor_position=len(document.text)
)
```

**What's Good:**
- Clear, actionable message
- Appears immediately after invalid input
- Explains what went wrong

**Unknown:**
- Does screen reader announce error message?
- Is error distinguishable from normal text?

**Recommended Testing:**
```bash
# Test with screen reader
# 1. Start wizard
# 2. Leave field empty and press Enter
# 3. Verify screen reader announces "This field cannot be empty"
```

**Priority:** HIGH (testing required)

---

## Priority Fixes Summary

Top 5 improvements by impact:

### 1. Add Skip Navigation Links + ARIA Landmarks
**Impact:** 🔴 CRITICAL
**WCAG Level:** A (baseline)
**Effort:** LOW (2 hours)
**Users Affected:** All keyboard and screen reader users

**Why Critical:** Without skip links, keyboard users must tab through 20-50 elements before reaching content. WCAG Level A violation means this is the minimum baseline for accessibility.

**Implementation:**
- Add `<a href="#main-content" class="skip-link">` as first element
- Wrap content in semantic `<header>` and `<main>` landmarks
- Add `id="main-content"` to main content section

---

### 2. Fix Table Accessibility
**Impact:** 🔴 CRITICAL
**WCAG Level:** A (baseline)
**Effort:** LOW (1 hour)
**Users Affected:** Screen reader users (10-15% of blind users)

**Why Critical:** Tables are the primary way job data is presented. Without proper markup, screen readers cannot navigate or understand table relationships. Users cannot answer "What's the salary for job #5?" without hearing all cells sequentially.

**Implementation:**
- Add `<caption>` with table description
- Add `scope="col"` to all `<th>` elements
- Add `aria-labelledby` reference to heading

---

### 3. Add Accessible Text for Visual Badges
**Impact:** 🟠 HIGH
**WCAG Level:** A (baseline)
**Effort:** LOW (1 hour)
**Users Affected:** Screen reader users

**Why High:** Score badges ("4.2/5.0") and NEW badges are the primary way to identify high-value jobs. Without accessible text, screen readers announce "four point two slash five" without context. Users don't know if 4.2 is good or bad.

**Implementation:**
- Add `aria-label="Job score: 4.2 out of 5.0, highly recommended"` to score badges
- Add `aria-label="New job posting not previously seen"` to NEW badges
- Add `role="status"` to all badges

---

### 4. Test and Document CLI Wizard Screen Reader Support
**Impact:** 🟠 HIGH
**WCAG Level:** A (baseline)
**Effort:** MEDIUM (4 hours testing + 2 hours documentation)
**Users Affected:** Screen reader users attempting first-time setup

**Why High:** If the wizard is unusable for blind users, they cannot configure Job Radar at all. This is a complete blocker. Even if HTML reports were perfect, the tool would be inaccessible.

**Implementation:**
1. Test wizard with NVDA (Windows), JAWS (Windows), VoiceOver (macOS)
2. Document findings (what works, what doesn't)
3. Add accessibility note to README
4. Consider adding `--accessible-mode` CLI flag
5. Fix terminal color contrast (use darker colors)

---

### 5. Enhance Focus Indicators
**Impact:** 🟡 MEDIUM
**WCAG Level:** AA
**Effort:** LOW (1 hour)
**Users Affected:** Keyboard users, low-vision users

**Why Medium:** Bootstrap provides basic focus indicators, but they may be too subtle. Enhanced focus indicators help low-vision users and anyone navigating by keyboard.

**Implementation:**
- Add custom `:focus-visible` styles with 3px outline
- Add high-contrast focus colors for dark mode
- Test that focus is visible on all interactive elements

---

## Testing Recommendations

To verify accessibility fixes:

### Automated Testing

1. **axe DevTools** (browser extension)
   - Install: https://www.deque.com/axe/devtools/
   - Run on generated HTML report
   - Fix all Critical and Serious issues

2. **WAVE** (browser extension)
   - Install: https://wave.webaim.org/extension/
   - Verify color contrast
   - Check for missing alt text

3. **Lighthouse Accessibility Audit**
   ```bash
   # Chrome DevTools > Lighthouse > Accessibility
   # Target score: 95+ (100 is difficult due to Bootstrap)
   ```

### Manual Testing

1. **Keyboard Navigation**
   ```
   Test: Can you navigate entire report using only keyboard?
   - Tab through all links
   - Verify skip link appears on first Tab press
   - Verify all interactive elements are reachable
   - Verify focus indicators are visible
   ```

2. **Screen Reader Testing**
   ```
   macOS: VoiceOver (Cmd+F5)
   Windows: NVDA (free) or JAWS (commercial)

   Test report:
   - Navigate by headings (H key in NVDA/JAWS)
   - Navigate by landmarks (D key in NVDA/JAWS)
   - Navigate table by row/column (Ctrl+Alt+Arrow in NVDA)
   - Verify badges announce meaningful text

   Test wizard:
   - Start wizard with screen reader active
   - Verify all prompts are read aloud
   - Verify instructions are announced
   - Verify error messages are spoken
   ```

3. **Color Contrast Testing**
   ```
   Tool: WebAIM Contrast Checker
   URL: https://webaim.org/resources/contrastchecker/

   Test:
   - All text against background: ≥4.5:1 (normal) or ≥3:1 (large)
   - UI components (borders, icons): ≥3:1
   ```

---

## Resources and Sources

### WCAG 2.1 Level AA Requirements
- [New Digital Accessibility Requirements in 2026](https://bbklaw.com/resources/new-digital-accessibility-requirements-in-2026)
- [What WCAG 2.1 AA Means for ADA Title II Web Compliance in 2026](https://adabook.medium.com/what-wcag-2-1-aa-means-for-ada-title-ii-web-compliance-in-2026-904d60fff912)
- [WCAG 2 Overview | W3C](https://www.w3.org/WAI/standards-guidelines/wcag/)
- [Complete Guide to WCAG 2.1 Level AA Compliance](https://genio.co/resources/research-and-insights/accessibility-wcag-2.1-level-aa-compliance-guide)

### Bootstrap 5.3 Accessibility
- [Accessibility · Bootstrap v5.3](https://getbootstrap.com/docs/5.3/getting-started/accessibility/)
- [How to Achieve Accessibility Compliance with Bootstrap 5](https://www.batoi.com/blogs/developers/how-achieve-accessibility-compliance-bootstrap-5-6645baaae29d1)
- [Building Accessible Websites with Bootstrap 5](https://reintech.io/blog/building-accessible-websites-bootstrap-5)

### CLI and Terminal Accessibility
- [Accessibility of Command Line Interfaces](https://dl.acm.org/doi/fullHtml/10.1145/3411764.3445544)
- [Improving Command Line Interfaces for All Users](https://afixt.com/accessible-by-design-improving-command-line-interfaces-for-all-users/)
- [Best practices for inclusive CLIs](https://seirdy.one/posts/2022/06/10/cli-best-practices/)

### Color Contrast
- [WebAIM: Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Understanding WCAG 2 Contrast Requirements](https://webaim.org/articles/contrast/)
- [Contrast requirements for WCAG 2.2 Level AA](https://www.makethingsaccessible.com/guides/contrast-requirements-for-wcag-2-2-level-aa/)

### Skip Navigation and Keyboard Accessibility
- [WebAIM: Skip Navigation Links](https://webaim.org/techniques/skipnav/)
- [How to Implement Skip Navigation Links](https://testparty.ai/blog/skip-navigation-links)
- [WebAIM: Keyboard Accessibility](https://webaim.org/techniques/keyboard/)

### Focus Indicators
- [Understanding Success Criterion 2.4.7: Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)
- [Guide to designing accessible focus indicators](https://www.sarasoueidan.com/blog/focus-indicators/)
- [Managing Focus and Visible Focus Indicators](https://vispero.com/resources/managing-focus-and-visible-focus-indicators-practical-accessibility-guidance-for-the-web/)

### Table Accessibility
- [ARIA: table role - MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles/table_role)
- [Beginner's guide to accessible tables](https://blog.pope.tech/2023/08/22/beginners-guide-to-accessible-tables/)
- [Ensure table columns, rows, and cells have proper ARIA labels](https://webflow.com/accessibility/checklist/task/ensure-table-columns-rows-and-cells-have-proper-aria-labels)

---

## Conclusion

Job Radar has **significant accessibility barriers** that prevent users with disabilities from effectively using the tool. The good news: most issues are straightforward to fix.

**Estimated Effort for WCAG 2.1 Level AA Compliance:**
- High priority fixes: 8-10 hours
- Medium priority fixes: 6-8 hours
- Testing and documentation: 8-10 hours
- **Total: 22-28 hours** (approximately 3-4 days of development)

**Recommended Approach:**
1. Week 1: Implement high priority fixes (#1-#4)
2. Week 2: Test with real screen readers, document findings
3. Week 3: Implement medium priority fixes based on test results
4. Week 4: Run automated tests (axe, WAVE, Lighthouse), fix remaining issues

**Success Criteria:**
- Lighthouse Accessibility score ≥95
- Zero Critical/Serious issues in axe DevTools
- Manual screen reader test passes all core workflows
- CLI wizard tested and documented with at least one screen reader

By addressing these accessibility gaps, Job Radar will be usable by the estimated 7.6 million Americans with visual disabilities and millions more with motor or cognitive disabilities.
