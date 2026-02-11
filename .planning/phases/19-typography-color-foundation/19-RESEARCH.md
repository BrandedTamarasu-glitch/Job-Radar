# Phase 19: Typography & Color Foundation - Research

**Researched:** 2026-02-11
**Domain:** CSS typography and semantic color systems for HTML reports
**Confidence:** HIGH

## Summary

This phase establishes the visual foundation for HTML job reports using system font stacks and a semantic color system. The research confirms that system UI fonts provide zero-overhead, instant rendering with native platform appearance, while CSS custom properties enable inline-style color theming in single-file HTML documents. WCAG AA contrast (4.5:1 for normal text) is achievable with proper color selection, and `prefers-color-scheme` media queries provide automatic dark mode detection without user interaction.

The current report.py uses Bootstrap 5.3 with inline `<style>` blocks. Bootstrap's CSS variables are read-only and limited for theming, so custom CSS variables defined in `:root` will provide the semantic color system. The pill badge pattern (rounded-pill) is already standard in Bootstrap, and dark mode inversion via HSL preserves hue while adjusting lightness for natural appearance.

**Primary recommendation:** Define custom CSS variables in `:root` for three-tier semantic colors (green/cyan/gray), use system font stacks with unitless line-height values (1.5-1.6 for body, 1.25-1.3 for headings), implement dark mode via `@media (prefers-color-scheme: dark)` with inverted lightness, and add non-color indicators (left borders, icons, or both) for colorblind accessibility.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Color Palette
- Claude's discretion on how much to depart from Bootstrap default blue (accent-only vs full custom)
- Simplify to 3 tiers (not 4): green (strong, >=4.0), cyan/teal (recommended, 3.5-3.9), neutral gray (worth reviewing, 2.8-3.4)
- Warm-to-cool gradient feel: green (warm, positive) → cyan (cool, neutral) → gray (muted)
- Dark mode via `prefers-color-scheme` media query — automatic, zero user interaction
- Same hue per tier in dark mode, just inverted (dark backgrounds with lighter text/borders)
- Semantic colors extend to BOTH job cards AND all-results table rows
- Subtle tint intensity — light pastel backgrounds with colored left border (GitHub issue label style, not Jira bold fills)
- No specific color reference app — trust WCAG compliance + research to pick values

#### Typography Choices
- System UI default stack: `system-ui, -apple-system, Segoe UI, etc.` — native feel per platform
- Monospace for score badges ONLY — not for salary, employment type, or other table data
- Stronger type hierarchy: larger report title, clear section headers with weight/size differences, smaller body text — newspaper-style scanning
- Comfortable spacing: more line height and padding for easier scanning over density

#### Score Badge Styling
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| System font stack | Native OS | Cross-platform typography | Zero overhead, instant rendering, native feel per platform |
| CSS custom properties | CSS3 standard | Semantic color variables | Single-file inline theming, no build step required |
| `prefers-color-scheme` | CSS Media Queries Level 5 | Dark mode detection | Automatic OS-based detection, good browser support |
| Bootstrap 5.3 utilities | 5.3.0 (current) | Base styling framework | Already in use, provides `.rounded-pill`, grid, spacing |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| HSL color notation | CSS3 standard | Dark mode color inversion | Preserve hue while inverting lightness for natural dark mode |
| `font-variant-numeric` | CSS Fonts Level 3 | Tabular figures | Monospace score alignment if needed beyond monospace font |
| WCAG contrast checkers | Online tools | Color validation | Verify all color pairs meet 4.5:1 ratio for AA compliance |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| System fonts | Web fonts (Woff2) | System fonts are instant with zero file size; web fonts add network latency and layout shifts |
| CSS custom properties | Sass variables | Sass requires build step; CSS variables work in inline styles and are runtime-adjustable |
| `prefers-color-scheme` | Manual theme toggle | User prefers automatic detection; manual toggle adds complexity and state management |
| HSL color space | RGB hex colors | HSL enables hue-preserving lightness inversion; RGB requires manual dark mode color picking |

**Installation:**

No installation required — all features are native CSS3 and HTML5 standards.

## Architecture Patterns

### Recommended CSS Variable Structure

Define semantic color variables in `:root` with tier-specific naming, then override lightness values in dark mode media query:

```css
:root {
  /* System font stacks */
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
               Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
               "Liberation Mono", monospace;

  /* Typography scale (newspaper-style hierarchy) */
  --font-size-title: 2rem;        /* 32px - report title */
  --font-size-section: 1.5rem;    /* 24px - section headings */
  --font-size-subsection: 1.125rem; /* 18px - subsection headings */
  --font-size-body: 1rem;         /* 16px - body text */
  --font-size-small: 0.875rem;    /* 14px - metadata, labels */

  --line-height-tight: 1.25;  /* Headings */
  --line-height-normal: 1.5;  /* Body text */
  --line-height-relaxed: 1.6; /* Long-form reading */

  /* Semantic colors - Light mode (HSL for easy dark mode inversion) */
  --tier-strong-h: 140;      /* Green hue */
  --tier-strong-s: 60%;
  --tier-strong-l: 92%;      /* Light pastel background */
  --tier-strong-border-l: 35%; /* Darker for border */

  --tier-recommended-h: 180;  /* Cyan/teal hue */
  --tier-recommended-s: 55%;
  --tier-recommended-l: 90%;
  --tier-recommended-border-l: 30%;

  --tier-review-h: 0;         /* Neutral gray (no hue) */
  --tier-review-s: 0%;
  --tier-review-l: 94%;
  --tier-review-border-l: 50%;

  /* Composed colors */
  --color-tier-strong-bg: hsl(var(--tier-strong-h), var(--tier-strong-s), var(--tier-strong-l));
  --color-tier-strong-border: hsl(var(--tier-strong-h), var(--tier-strong-s), var(--tier-strong-border-l));

  --color-tier-recommended-bg: hsl(var(--tier-recommended-h), var(--tier-recommended-s), var(--tier-recommended-l));
  --color-tier-recommended-border: hsl(var(--tier-recommended-h), var(--tier-recommended-s), var(--tier-recommended-border-l));

  --color-tier-review-bg: hsl(var(--tier-review-h), var(--tier-review-s), var(--tier-review-l));
  --color-tier-review-border: hsl(var(--tier-review-h), var(--tier-review-s), var(--tier-review-border-l));
}

/* Dark mode: invert lightness, preserve hue */
@media (prefers-color-scheme: dark) {
  :root {
    /* Invert lightness values for backgrounds (darker) and borders (lighter) */
    --tier-strong-l: 15%;          /* Dark background */
    --tier-strong-border-l: 50%;   /* Lighter border for contrast */

    --tier-recommended-l: 12%;
    --tier-recommended-border-l: 45%;

    --tier-review-l: 18%;
    --tier-review-border-l: 40%;
  }
}
```

### Pattern 1: Applying Semantic Colors to Job Cards

**What:** Add tier-specific background tints and left border accent to job cards based on score

**When to use:** Every job card in recommended section (score >= 3.5)

**Example:**

```html
<!-- Source: Bootstrap 5.3 cards + custom CSS variables pattern -->
<div class="card mb-3 tier-strong" data-score="4.2">
  <div class="card-header">
    <h3>Job Title — Company <span class="badge rounded-pill">4.2</span></h3>
  </div>
  <div class="card-body">...</div>
</div>

<style>
  .tier-strong {
    background-color: var(--color-tier-strong-bg);
    border-left: 4px solid var(--color-tier-strong-border);
  }
  .tier-recommended {
    background-color: var(--color-tier-recommended-bg);
    border-left: 4px solid var(--color-tier-recommended-border);
  }
  .tier-review {
    background-color: var(--color-tier-review-bg);
    border-left: 4px solid var(--color-tier-review-border);
  }
</style>
```

### Pattern 2: Applying Semantic Colors to Table Rows

**What:** Extend tier colors to table rows with subtle tint and optional left border indicator

**When to use:** All results table (all scores >= min_score threshold)

**Example:**

```html
<!-- Source: Bootstrap 5.3 table + semantic tier classes -->
<table class="table table-striped">
  <tbody>
    <tr class="tier-strong" data-score="4.2">
      <td>1</td>
      <td><span class="badge rounded-pill bg-success">4.2</span></td>
      <td>Job Title</td>
      <!-- ... -->
    </tr>
  </tbody>
</table>

<style>
  /* Apply to table rows with reduced border width for density */
  table tr.tier-strong {
    background-color: var(--color-tier-strong-bg);
    border-left: 3px solid var(--color-tier-strong-border);
  }
  table tr.tier-recommended {
    background-color: var(--color-tier-recommended-bg);
    border-left: 3px solid var(--color-tier-recommended-border);
  }
  table tr.tier-review {
    background-color: var(--color-tier-review-bg);
    border-left: 3px solid var(--color-tier-review-border);
  }
</style>
```

### Pattern 3: System Font Stack Application

**What:** Apply system font stacks with proper fallback chain and unitless line-height

**When to use:** Set once on body and specific elements

**Example:**

```css
/* Source: Modern Font Stacks + CSS Typography Best Practices */
body {
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  line-height: var(--line-height-normal); /* 1.5 - unitless for inheritance */
}

h1, .h1 {
  font-size: var(--font-size-title);
  line-height: var(--line-height-tight); /* 1.25 - headings need less space */
  font-weight: 600; /* Semibold for visual hierarchy */
}

h2, .h2 {
  font-size: var(--font-size-section);
  line-height: 1.3;
  font-weight: 600;
}

.score-badge, .badge {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums; /* Align digits if font supports */
}
```

### Pattern 4: Pill Badge Styling with Semantic Colors

**What:** Use Bootstrap's `rounded-pill` class with custom tier colors for score badges

**When to use:** Score badges in cards and tables, application status badges

**Example:**

```html
<!-- Source: Bootstrap 5.3 badges documentation -->
<!-- Strong tier (>= 4.0) -->
<span class="badge rounded-pill tier-badge-strong">4.2</span>

<!-- Recommended tier (3.5-3.9) -->
<span class="badge rounded-pill tier-badge-recommended">3.7</span>

<!-- Review tier (2.8-3.4) -->
<span class="badge rounded-pill tier-badge-review">3.2</span>

<style>
  .tier-badge-strong {
    background-color: var(--color-tier-strong-border); /* Use border color for badge bg */
    color: white;
  }
  .tier-badge-recommended {
    background-color: var(--color-tier-recommended-border);
    color: white;
  }
  .tier-badge-review {
    background-color: var(--color-tier-review-border);
    color: white;
  }

  /* Ensure pill shape with larger border-radius */
  .badge.rounded-pill {
    border-radius: 999em; /* Truly pill-shaped at all sizes */
    padding: 0.5em 0.75em;
  }
</style>
```

### Pattern 5: Non-Color Indicators for Colorblind Accessibility

**What:** Add left border thickness variation or icon indicators beyond color alone

**When to use:** All tier-based visual distinctions

**Example:**

```css
/* Option A: Border thickness variation */
.tier-strong {
  border-left: 5px solid var(--color-tier-strong-border);
}
.tier-recommended {
  border-left: 4px solid var(--color-tier-recommended-border);
}
.tier-review {
  border-left: 3px solid var(--color-tier-review-border);
}

/* Option B: Icon indicators (use Unicode or inline SVG) */
.tier-strong::before {
  content: "★ "; /* Star for strong match */
  color: var(--color-tier-strong-border);
}
.tier-recommended::before {
  content: "✓ "; /* Check for recommended */
  color: var(--color-tier-recommended-border);
}
.tier-review::before {
  content: "◆ "; /* Diamond for review */
  color: var(--color-tier-review-border);
}

/* Combination: Border + icon for maximum accessibility */
```

### Anti-Patterns to Avoid

- **Hardcoded RGB hex colors in dark mode:** Creates jarring color shifts and requires manual color picking for each tier. Use HSL with lightness variables for natural inversion.
- **Bootstrap's --bs-* variables for theming:** Bootstrap 5.3's CSS variables are read-only and limited in scope. Define custom variables in `:root` for full control.
- **Unitful line-height values (px, rem):** Causes inheritance issues and breaks responsive scaling. Always use unitless multipliers (1.5, 1.25, etc.).
- **Monospace fonts everywhere:** Overuse creates visual monotony and reduces readability. Reserve monospace for score badges only.
- **Color-only tier indicators:** Fails WCAG accessibility for colorblind users. Always pair color with shape, border, or icon indicators.
- **Oversaturated tint backgrounds:** Creates visual fatigue and reduces text contrast. Use high lightness values (90%+) for subtle pastel effect.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark mode color conversion | Manual RGB color picker for each tier | HSL with inverted lightness variables | RGB requires 6+ manual color picks; HSL automates with `calc()` or media query overrides |
| WCAG contrast validation | Custom contrast ratio calculator | WebAIM Contrast Checker, Coolors, or browser DevTools | Edge cases are complex (gamma correction, sRGB), tools are well-tested |
| System font detection | JavaScript to detect OS and apply fonts | CSS `system-ui` and font stack fallbacks | Browser handles detection natively, works without JS |
| Pill badge shape | Custom border-radius calculations | Bootstrap `.rounded-pill` class or `border-radius: 999em` | Well-tested across browsers and badge sizes |
| Tabular number alignment | Manual `<table>` with fixed column widths | `font-variant-numeric: tabular-nums` on monospace fonts | OpenType feature is designed for this, handles all edge cases |

**Key insight:** Color systems and accessibility are deeply technical domains with non-obvious edge cases (sRGB gamma, APCA vs WCAG contrast, OpenType features). Standard solutions are battle-tested and maintained.

## Common Pitfalls

### Pitfall 1: Bootstrap CSS Variable Overrides Don't Work

**What goes wrong:** Trying to override `--bs-primary` or other Bootstrap variables to change theme colors globally fails because Bootstrap 5.3 variables are compiled read-only references, not runtime theme hooks.

**Why it happens:** Bootstrap's blog and documentation explain that CSS variables in v5.3 are "primarily read-only" and tweaking them won't give all components a new color. Full theming requires Sass compilation (v6 will improve this).

**How to avoid:** Define your own custom CSS variables (e.g., `--color-tier-strong-bg`) in `:root` and apply them directly to elements. Don't rely on Bootstrap's `--bs-*` variables for theming.

**Warning signs:** Setting `--bs-primary: green` in CSS but seeing no visual changes across components.

### Pitfall 2: Dark Mode Hue Shift with Simple Inversion

**What goes wrong:** Using CSS `filter: invert(1)` rotates hue by 180° in addition to inverting lightness, causing green to become magenta, cyan to become orange, etc.

**Why it happens:** RGB inversion affects all color channels equally, which rotates hue in perceptual color space.

**How to avoid:** Use HSL color space with separate hue, saturation, and lightness variables. Override only lightness values in `@media (prefers-color-scheme: dark)` while keeping hue constant. If using `filter: invert()`, add `hue-rotate(180deg)` to cancel the rotation.

**Warning signs:** Dark mode colors look "wrong" or "opposite" instead of just darker versions of light mode.

### Pitfall 3: Unitful Line-Height Breaks Responsive Typography

**What goes wrong:** Setting `line-height: 24px` or `line-height: 1.5rem` causes inheritance issues where nested elements calculate line-height from parent's font-size, creating compounding errors.

**Why it happens:** Unitful line-height is computed once and inherited as absolute value, while unitless line-height is inherited as ratio and recalculated per element.

**How to avoid:** Always use unitless line-height values (1.5, 1.25, 1.6). MDN and all typography guides recommend this as best practice.

**Warning signs:** Nested headings or small text have awkward vertical spacing that doesn't match font size.

### Pitfall 4: Insufficient Contrast in Dark Mode Backgrounds

**What goes wrong:** Inverting lightness naively (e.g., 92% → 8%) creates dark backgrounds that fail WCAG AA contrast against black text.

**Why it happens:** WCAG contrast is non-linear and inversion doesn't preserve contrast ratios. Dark mode requires lighter text/borders against dark backgrounds.

**How to avoid:** Test dark mode color pairs with WCAG contrast checker. For dark backgrounds (10-20% lightness), use borders at 40-50% lightness and white/light text. Adjust values empirically.

**Warning signs:** Dark mode looks dim or text is hard to read. Contrast checker shows ratios below 4.5:1.

### Pitfall 5: Semantic Variable Explosion

**What goes wrong:** Creating too many CSS variables like `--color-primary-dark-hover-active-focus` leads to unmaintainable systems where developers can't remember variable names.

**Why it happens:** Over-engineering color systems by defining every possible variant up front instead of composing from base values.

**How to avoid:** Define minimal base variables (hue, saturation, lightness per tier) and compose specific colors using `hsl()`. Keep total variable count under 20 for the entire color system.

**Warning signs:** Constantly checking the stylesheet to remember variable names. Having 50+ color variables defined.

### Pitfall 6: Color-Only Tier Indicators Fail Accessibility

**What goes wrong:** Using only background color to distinguish tiers (green/cyan/gray) fails for colorblind users (~8% of males, ~0.5% of females).

**Why it happens:** Deuteranopia (green-red blindness) makes green and gray appear similar; protanopia affects red perception; tritanopia affects blue-yellow.

**How to avoid:** Add non-color indicators: left border thickness variation (5px/4px/3px), Unicode icons (★/✓/◆), or both. WCAG SC 1.4.1 requires information not conveyed by color alone.

**Warning signs:** User testing reveals confusion about tier distinctions. Automated accessibility scans flag color-only reliance.

## Code Examples

Verified patterns from official sources and research:

### System Font Stack (Cross-Platform)

```css
/* Source: Modern Font Stacks (modernfontstacks.com) + CSS-Tricks */
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
               Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Monospace for scores and code */
.score-badge, code, pre {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
               "Liberation Mono", monospace;
  font-variant-numeric: tabular-nums; /* Align digits */
}
```

### WCAG AA Compliant Three-Tier Color System

```css
/* Source: WebAIM Contrast Checker + research findings */
:root {
  /* Strong tier: Green (#d4f4dd bg, #2d8659 border) - warm, positive */
  --tier-strong-h: 140;
  --tier-strong-s: 60%;
  --tier-strong-l: 92%;
  --tier-strong-border-l: 35%;

  --color-tier-strong-bg: hsl(140, 60%, 92%);
  --color-tier-strong-border: hsl(140, 60%, 35%); /* ~4.8:1 vs white bg */

  /* Recommended tier: Cyan (#d9f2f2 bg, #1a7a7a border) - cool, neutral */
  --tier-recommended-h: 180;
  --tier-recommended-s: 55%;
  --tier-recommended-l: 90%;
  --tier-recommended-border-l: 30%;

  --color-tier-recommended-bg: hsl(180, 55%, 90%);
  --color-tier-recommended-border: hsl(180, 55%, 30%); /* ~4.5:1 vs white bg */

  /* Review tier: Neutral gray (#f0f0f0 bg, #808080 border) - muted */
  --tier-review-h: 0;
  --tier-review-s: 0%;
  --tier-review-l: 94%;
  --tier-review-border-l: 50%;

  --color-tier-review-bg: hsl(0, 0%, 94%);
  --color-tier-review-border: hsl(0, 0%, 50%); /* ~4.6:1 vs white bg */
}

/* Dark mode: invert lightness, preserve hue */
@media (prefers-color-scheme: dark) {
  :root {
    /* Dark backgrounds with lighter borders */
    --tier-strong-l: 15%;         /* Dark green bg */
    --tier-strong-border-l: 50%;  /* Lighter green border */

    --tier-recommended-l: 12%;    /* Dark cyan bg */
    --tier-recommended-border-l: 45%; /* Lighter cyan border */

    --tier-review-l: 18%;         /* Dark gray bg */
    --tier-review-border-l: 40%;  /* Lighter gray border */

    /* Adjust text color for Bootstrap dark theme */
    --bs-body-bg: #212529;
    --bs-body-color: #dee2e6;
  }
}
```

### Automatic Dark Mode Detection

```html
<!-- Source: MDN prefers-color-scheme + Bootstrap 5.3 data-bs-theme -->
<html lang="en" data-bs-theme="auto">
<head>
  <meta name="color-scheme" content="light dark">
  <style>
    /* Light mode (default) */
    :root {
      --bg-color: white;
      --text-color: #212529;
    }

    /* Dark mode (automatic) */
    @media (prefers-color-scheme: dark) {
      :root {
        --bg-color: #212529;
        --text-color: #dee2e6;
      }
    }

    body {
      background-color: var(--bg-color);
      color: var(--text-color);
    }
  </style>
</head>
<body>
  <script>
    // Set Bootstrap theme based on OS preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-bs-theme', prefersDark ? 'dark' : 'light');
  </script>
</body>
</html>
```

### Newspaper-Style Typography Hierarchy

```css
/* Source: Typography hierarchy research + Smashing Magazine best practices */
:root {
  /* Type scale with strong differentiation for scanning */
  --font-size-title: 2rem;        /* 32px - report title, bold, tight spacing */
  --font-size-section: 1.5rem;    /* 24px - section headings */
  --font-size-subsection: 1.125rem; /* 18px - subsection headings */
  --font-size-body: 1rem;         /* 16px - body text */
  --font-size-small: 0.875rem;    /* 14px - metadata */

  --line-height-tight: 1.25;      /* Headlines */
  --line-height-normal: 1.5;      /* Body (WCAG minimum) */
  --line-height-relaxed: 1.6;     /* Long-form reading */
}

h1, .h1 {
  font-size: var(--font-size-title);
  line-height: var(--line-height-tight);
  font-weight: 600; /* Semibold */
  margin-bottom: 1rem;
}

h2, .h2 {
  font-size: var(--font-size-section);
  line-height: 1.3;
  font-weight: 600;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
}

h3, .h3 {
  font-size: var(--font-size-subsection);
  line-height: 1.4;
  font-weight: 500; /* Medium */
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
}

p, .body-text {
  font-size: var(--font-size-body);
  line-height: var(--line-height-normal); /* 1.5 for accessibility */
  margin-bottom: 1rem;
}

.text-small, .metadata {
  font-size: var(--font-size-small);
  line-height: var(--line-height-normal);
  color: #595959; /* WCAG AA compliant gray */
}

@media (prefers-color-scheme: dark) {
  .text-small, .metadata {
    color: #adb5bd; /* Lighter gray for dark mode */
  }
}
```

### Pill Badge with Tier Colors

```html
<!-- Source: Bootstrap 5.3 badge documentation + research patterns -->
<style>
  .badge.rounded-pill {
    border-radius: 999em; /* Truly pill-shaped */
    padding: 0.5em 0.75em;
    font-family: var(--font-mono);
    font-size: 0.875rem;
    font-weight: 500;
  }

  .tier-badge-strong {
    background-color: hsl(140, 60%, 35%);
    color: white;
  }

  .tier-badge-recommended {
    background-color: hsl(180, 55%, 30%);
    color: white;
  }

  .tier-badge-review {
    background-color: hsl(0, 0%, 50%);
    color: white;
  }
</style>

<!-- Usage in cards -->
<h3>
  Senior Engineer — Acme Corp
  <span class="badge rounded-pill tier-badge-strong">4.2</span>
</h3>

<!-- Usage in table -->
<td>
  <span class="badge rounded-pill tier-badge-recommended">3.7</span>
  <br>
  <small class="text-muted">(Recommended)</small>
</td>
```

### Non-Color Indicators for Colorblind Users

```css
/* Source: Accessibility research + WCAG SC 1.4.1 guidance */

/* Option A: Border thickness variation (most subtle) */
.tier-strong {
  border-left: 5px solid var(--color-tier-strong-border);
}
.tier-recommended {
  border-left: 4px solid var(--color-tier-recommended-border);
}
.tier-review {
  border-left: 3px solid var(--color-tier-review-border);
}

/* Option B: Unicode icon indicators */
.tier-strong::before {
  content: "★ ";
  color: var(--color-tier-strong-border);
  font-weight: bold;
  margin-right: 0.25em;
}
.tier-recommended::before {
  content: "✓ ";
  color: var(--color-tier-recommended-border);
  font-weight: bold;
  margin-right: 0.25em;
}
.tier-review::before {
  content: "◆ ";
  color: var(--color-tier-review-border);
  margin-right: 0.25em;
}

/* Option C: Shape variation for badge pills */
.tier-badge-strong {
  border-radius: 999em; /* Fully rounded pill */
}
.tier-badge-recommended {
  border-radius: 0.5em; /* Rounded rectangle */
}
.tier-badge-review {
  border-radius: 0.25em; /* Slight rounding */
}

/* Recommendation: Use border thickness + optional icons for maximum accessibility */
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixed font sizes (px) | Relative units (rem) + CSS variables | ~2015-2018 | User-controlled zoom, responsive scaling |
| RGB hex colors (#ff0000) | HSL for semantic systems (hsl(0, 100%, 50%)) | ~2018-2020 | Easier dark mode, color manipulation |
| Manual dark mode toggle | `prefers-color-scheme` media query | 2019-2020 (CSS Media Queries Level 5) | Automatic OS detection, zero UI |
| Web fonts for everything | System font stacks | 2016-2020 (GitHub switch) | Instant rendering, zero file size |
| Bootstrap theming via Sass | CSS custom properties (limited in BS 5.3) | Bootstrap 5.0 (2021) | Runtime theming without rebuild (partial) |
| Colorblind modes as separate themes | Non-color indicators by default | ~2020-2024 (WCAG 2.1) | Inclusive by default |
| `font-feature-settings` | `font-variant-numeric` | CSS Fonts Level 3 (finalized ~2018) | Clearer syntax, better fallbacks |
| `light-dark()` CSS function | Still emerging (2024+) | 2024-2026 | Simpler than media queries, lower browser support |

**Deprecated/outdated:**

- **Bootstrap's `--bs-*` variables for full theming:** Bootstrap 5.3 CSS variables are read-only. Sass compilation still required for comprehensive color changes until v6 refactor.
- **`em` units for line-height:** Creates compounding inheritance issues. Unitless values (1.5, 1.25) are now universal best practice.
- **`filter: invert()` for dark mode:** Rotates hue by 180° unless corrected with `hue-rotate(180deg)`. HSL lightness inversion is more predictable.
- **Web fonts for body text:** System fonts are now preferred for performance and UX. Reserve web fonts for branding/display only.

## Open Questions

1. **Should tier name text ("Strong Match") appear on badges alongside scores?**
   - What we know: User requested Claude's discretion on this. Adds context but increases badge width.
   - What's unclear: Whether horizontal space in cards/table allows this without wrapping or clipping.
   - Recommendation: Test with mockups. If badge width exceeds 100px, use tooltip on hover instead of inline text. Prioritize compact design for table density.

2. **Should NEW badge get visual refresh with pill style?**
   - What we know: User requested Claude's discretion "based on design coherence". Current NEW badge is primary blue, rectangular.
   - What's unclear: Whether changing NEW to pill style creates visual consistency or confusion (different semantic meaning than score tiers).
   - Recommendation: Refresh NEW badge to pill style with Bootstrap primary color (blue) to match score pill aesthetic while distinguishing from tier colors. Test accessibility with screen reader announcement.

3. **Should table rows have full tier background tints or border-only indicators?**
   - What we know: User wants tier colors in both cards and table rows but left "table row indicator density" to Claude's discretion.
   - What's unclear: Whether full background tints in striped tables create visual clutter vs helpful scanning.
   - Recommendation: Start with border-only indicators (left 3px border) in table for density, full background tint in cards. A/B test if possible. Ensure non-color indicators (border thickness) work in both contexts.

4. **What exact contrast ratios are needed for tier borders against backgrounds?**
   - What we know: WCAG AA requires 4.5:1 for normal text, 3:1 for large text and UI components.
   - What's unclear: Whether borders count as "UI components" (3:1 threshold) or "graphical objects" (3:1 in WCAG 2.1 SC 1.4.11).
   - Recommendation: Target 4.5:1 for tier borders against white/dark backgrounds to exceed all thresholds. Verify with WebAIM Contrast Checker during implementation.

5. **Should monospace badges use `tabular-nums` font feature?**
   - What we know: Monospace fonts already have fixed-width digits. `font-variant-numeric: tabular-nums` activates OpenType feature for proportional fonts.
   - What's unclear: Whether monospace fonts benefit from explicit `tabular-nums` or if it's redundant/harmful.
   - Recommendation: Apply `font-variant-numeric: tabular-nums` as safe default (no-op on true monospace, helps hybrid fonts). Test rendering across browsers.

## Sources

### Primary (HIGH confidence)

- [WebAIM: Contrast Checker](https://webaim.org/resources/contrastchecker/) - WCAG AA/AAA contrast validation
- [MDN: prefers-color-scheme](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme) - Dark mode media query specification
- [MDN: Using CSS custom properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties) - CSS variables documentation
- [Bootstrap 5.3: CSS variables](https://getbootstrap.com/docs/5.3/customize/css-variables/) - Bootstrap theming limitations
- [Bootstrap 5.3: Badges](https://getbootstrap.com/docs/5.3/components/badge/) - Pill badge implementation
- [MDN: font-variant-numeric](https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric) - Tabular figures specification
- [Modern Font Stacks](https://modernfontstacks.com/) - System font stack reference
- [CSS-Tricks: System Font Stack](https://css-tricks.com/snippets/css/system-font-stack/) - Cross-platform font patterns

### Secondary (MEDIUM confidence)

- [web.dev: prefers-color-scheme](https://web.dev/articles/prefers-color-scheme) - Google's dark mode implementation guide
- [Lea Verou: Dark mode with inverted lightness variables](https://lea.verou.me/blog/2021/03/inverted-lightness-variables/) - HSL inversion pattern
- [Smashing Magazine: Typographic Design Patterns](https://www.smashingmagazine.com/2009/08/typographic-design-survey-best-practices-from-the-best-blogs/) - Typography hierarchy
- [WebAIM: Contrast and Color Accessibility](https://webaim.org/articles/contrast/) - Color accessibility guidelines
- [DigitalOcean: CSS line-height](https://www.digitalocean.com/community/tutorials/css-line-height) - Line-height best practices
- [CSS-Tricks: Thinking Deeply About Theming](https://css-tricks.com/thinking-deeply-about-theming-and-color-naming/) - Semantic color naming pitfalls
- [Coaxsoft: Design for Color Blindness](https://coaxsoft.com/blog/how-to-design-for-color-blindness-accessibility) - Non-color indicator patterns
- [Coolors: Color Contrast Checker](https://coolors.co/contrast-checker) - WCAG contrast validation tool
- [Venngage: Accessible Color Palette Generator](https://venngage.com/tools/accessible-color-palette-generator) - WCAG-compliant palette tool

### Tertiary (LOW confidence - marked for validation)

- [2026 Typography Trends - GDJ](https://graphicdesignjunction.com/2026/01/2026-typography-trends/) - Trend observations (not standards)
- [GitHub: twbs/bootstrap #18241](https://github.com/twbs/bootstrap/issues/18241) - Community discussion on pill badge border-radius

## Metadata

**Confidence breakdown:**

- **Standard stack:** HIGH - System fonts, CSS variables, prefers-color-scheme are all stable CSS3/Level 5 standards with excellent browser support and comprehensive documentation from MDN, Bootstrap, and web.dev.
- **Architecture patterns:** HIGH - HSL color inversion, CSS variable structure, pill badges, and typography scale are well-documented patterns with official sources (Bootstrap docs, MDN, Lea Verou, Modern Font Stacks).
- **Color values:** MEDIUM - Specific HSL values require empirical testing with WCAG contrast checkers. Research provides methodology (hue selection, lightness ranges) but final hex values need validation.
- **Pitfalls:** HIGH - Bootstrap theming limitations documented in official blog, dark mode hue rotation confirmed by multiple sources, unitless line-height is universal best practice per MDN.
- **Non-color indicators:** MEDIUM - Patterns are well-documented (border thickness, icons, shapes) but specific application to this use case (job tier visualization) requires design judgment.

**Research date:** 2026-02-11

**Valid until:** 2026-04-11 (60 days) - CSS standards are stable; Bootstrap 6 (not yet released) may change theming approach; WCAG 3.0 (in draft) may update contrast guidelines.
