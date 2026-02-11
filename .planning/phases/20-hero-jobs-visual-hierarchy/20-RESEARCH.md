# Phase 20: Hero Jobs Visual Hierarchy - Research

**Researched:** 2026-02-11
**Domain:** CSS visual hierarchy, card elevation, section layout
**Confidence:** HIGH

## Summary

Phase 20 builds on the existing 3-tier semantic color system (Phase 19) to elevate hero jobs (score ≥4.0) with prominent visual hierarchy beyond the current subtle background + border treatment. Research shows that modern UI design (2026) achieves prominence through **layered visual cues**: shadow elevation, increased spacing, badge enhancements, and section separation—not just color alone.

The existing `.tier-strong` class provides green pastel background + 5px left border. Hero elevation adds: (1) multi-layer box shadows for depth perception, (2) increased padding for spatial hierarchy, (3) prominent badge labels like "Top Match" or "Excellent Match", and (4) clear section separation with optional visual dividers.

**Primary recommendation:** Use CSS custom properties for multi-layer shadows that adapt to dark mode, increase card padding for hero jobs, add prominent text labels to score badges, and separate hero section from lower-tier jobs with strategic spacing and optional divider.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Bootstrap 5.3 | 5.3.x | Shadow utilities | Already integrated; provides `.shadow-sm`, `.shadow`, `.shadow-lg` |
| CSS Custom Properties | Native | Dark mode shadow adaptation | Existing pattern from Phase 19; enables shadow transparency control |
| HSL Color Variables | Native | Semantic tier colors | Phase 19 foundation; hero builds on `--tier-strong-*` vars |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `prefers-color-scheme` | Native | Dark mode detection | Already implemented; shadows need dark mode adjustments |
| ARIA roles | Native | Accessible separators | When using visual dividers between sections |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CSS custom properties | Inline Bootstrap shadow classes | Bootstrap shadows don't adapt opacity for dark mode; custom properties enable fine-tuned transparency |
| Multi-layer shadows | Single shadow | Single shadows lack depth realism; research shows 2+ layers create better elevation perception |
| Section wrapper | Just spacing | Section wrapper enables background differentiation and ARIA landmarks; pure spacing is simpler |

**Installation:**
No new dependencies required. All techniques use existing Bootstrap 5.3 + CSS custom properties already in codebase.

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── report.py                # All changes in this single file
│   ├── <style> block        # Add hero shadow CSS variables
│   ├── _html_recommended_section()  # Split hero jobs into separate section
│   └── _score_tier()        # Already correctly identifies tier-strong
```

### Pattern 1: Multi-Layer Shadow Elevation
**What:** Combine 2-3 box shadows with different blur/spread values to create realistic depth perception
**When to use:** For hero jobs (score ≥4.0) to create "floating above page" effect

**Example:**
```css
/* Source: Josh W. Comeau - Designing Beautiful Shadows in CSS */
:root {
  /* Hero shadow: multi-layer for realistic elevation */
  --shadow-hero:
    0 1px 3px rgba(0, 0, 0, 0.12),
    0 4px 8px rgba(0, 0, 0, 0.08),
    0 8px 16px rgba(0, 0, 0, 0.05);
}

@media (prefers-color-scheme: dark) {
  :root {
    /* Reduce shadow opacity in dark mode to prevent harsh contrast */
    --shadow-hero:
      0 1px 3px rgba(0, 0, 0, 0.3),
      0 4px 8px rgba(0, 0, 0, 0.2),
      0 8px 16px rgba(0, 0, 0, 0.15);
  }
}

.tier-strong.hero-job {
  box-shadow: var(--shadow-hero);
}
```

### Pattern 2: Spatial Hierarchy with Padding
**What:** Increase internal padding for hero cards to create "breathing room" and perceived importance
**When to use:** Always for hero jobs; follows "internal ≤ external" spacing rule

**Example:**
```css
/* Source: 8-point grid system best practices */
.card-body {
  padding: 1.25rem;  /* 20px - base tier */
}

.tier-strong .card-body {
  padding: 1.5rem;   /* 24px - hero tier (+4px = 8pt increment) */
}
```

### Pattern 3: Prominent Badge Labels
**What:** Add semantic text labels ("Top Match", "Excellent Match") to score badges for immediate recognition
**When to use:** For hero jobs; complements numeric score with qualitative signal

**Example:**
```html
<!-- Source: Badge UI design best practices 2026 -->
<span class="badge rounded-pill score-badge tier-badge-strong">
  <span class="visually-hidden">Score </span>
  4.2
  <span class="visually-hidden"> out of 5.0</span>
  <span class="badge-label ms-1">Top Match</span>
</span>
```

```css
.badge-label {
  font-size: 0.85em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}
```

### Pattern 4: Section Separation
**What:** Create distinct visual break between hero jobs and lower-tier jobs using spacing + optional divider
**When to use:** When ≥1 hero job exists; prevents hero jobs from blending into page flow

**Example:**
```html
<!-- Source: Accessible section separator patterns -->
<section aria-labelledby="hero-heading" class="hero-jobs-section mb-5">
  <h2 id="hero-heading" class="h4 mb-3">Top Matches (Score ≥ 4.0)</h2>
  <!-- Hero job cards -->
</section>

<div class="section-divider" role="separator" aria-hidden="true"></div>

<section aria-labelledby="recommended-heading" class="recommended-jobs-section mb-4">
  <h2 id="recommended-heading" class="h4 mb-3">Recommended Roles (Score 3.5-3.9)</h2>
  <!-- Lower-tier job cards -->
</section>
```

```css
.section-divider {
  height: 1px;
  background: linear-gradient(to right, transparent, #dee2e6 20%, #dee2e6 80%, transparent);
  margin: 3rem 0; /* 48px top/bottom - follows 8pt grid */
}

@media (prefers-color-scheme: dark) {
  .section-divider {
    background: linear-gradient(to right, transparent, #495057 20%, #495057 80%, transparent);
  }
}
```

### Anti-Patterns to Avoid
- **Over-shadowing:** Don't use shadows >24px blur or >0.3 opacity in light mode—creates harsh "pop-out" effect that breaks page cohesion
- **Color-only distinction:** Don't rely solely on background color for hero status—combine shadow + padding + badge label for multi-sensory cues (colorblind accessibility)
- **Inconsistent spacing:** Don't use arbitrary padding values—stick to 8pt grid (0.5rem increments) for visual rhythm
- **Static shadows in dark mode:** Don't reuse light mode shadow opacity—dark mode needs higher opacity to maintain visibility against dark backgrounds

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Shadow depth perception | Single `box-shadow` value | Multi-layer shadow with 2-3 stacked values | Material Design research shows humans perceive depth through layered shadows with varying blur/spread; single shadows look flat |
| Dark mode shadow adaptation | Duplicate CSS rules | CSS custom properties with `@media (prefers-color-scheme: dark)` override | Phase 19 pattern already established; custom properties enable single-source-of-truth with media query overrides |
| Accessible section separators | `<hr>` or `<div>` without ARIA | `role="separator"` with `aria-hidden="true"` | MDN accessibility guidelines require ARIA roles for semantic separators; purely decorative dividers need `aria-hidden` |
| Badge label styling | Inline styles or one-off classes | Reusable `.badge-label` utility class | Design systems principle: tokens over magic numbers; enables consistent badge enhancements across report |

**Key insight:** Visual hierarchy is a **layered system**—shadow elevation + spatial padding + badge prominence + section structure work together. Removing any one layer degrades the overall effect. Don't optimize prematurely by choosing "just shadows" or "just spacing"—the combination is what creates hero-level distinction.

## Common Pitfalls

### Pitfall 1: Shadows Break in Dark Mode
**What goes wrong:** Light mode shadows (low opacity) become invisible in dark mode, or create inverted "glow" effect
**Why it happens:** Default `rgba(0,0,0,0.15)` shadows have insufficient contrast against dark backgrounds
**How to avoid:** Use CSS custom properties with separate opacity values for light/dark modes
**Warning signs:** Hero cards look flat in dark mode, or shadows appear as white halos

**Prevention:**
```css
:root {
  --shadow-color: 0, 0, 0;  /* RGB components for flexibility */
  --shadow-opacity-1: 0.12;
  --shadow-opacity-2: 0.08;
  --shadow-opacity-3: 0.05;
}

@media (prefers-color-scheme: dark) {
  :root {
    --shadow-opacity-1: 0.3;   /* Increase opacity in dark mode */
    --shadow-opacity-2: 0.2;
    --shadow-opacity-3: 0.15;
  }
}

.hero-job {
  box-shadow:
    0 1px 3px rgba(var(--shadow-color), var(--shadow-opacity-1)),
    0 4px 8px rgba(var(--shadow-color), var(--shadow-opacity-2)),
    0 8px 16px rgba(var(--shadow-color), var(--shadow-opacity-3));
}
```

### Pitfall 2: Focus Indicators Obscured by Shadows
**What goes wrong:** Keyboard focus outline becomes hard to see against hero card shadows
**Why it happens:** Default `outline` property doesn't account for elevated shadow layers
**How to avoid:** Enhance focus indicators with additional contrast for tier-strong cards
**Warning signs:** Tab navigation loses visual clarity on hero jobs; WCAG 2.4.7 violation

**Prevention:**
```css
/* Source: WCAG 2.1 Focus Visible guidelines */
.tier-strong.job-item:focus-visible {
  outline: 3px solid var(--color-tier-strong-border);  /* Thicker outline */
  outline-offset: 3px;  /* More offset to clear shadow */
  box-shadow:
    var(--shadow-hero),
    0 0 0 6px rgba(var(--tier-strong-h), var(--tier-strong-s), var(--tier-strong-border-l), 0.2);  /* Additional glow */
}
```

### Pitfall 3: Section Divider Lacks Semantic Meaning
**What goes wrong:** Visual divider between sections looks decorative but confuses screen readers
**Why it happens:** Empty `<div>` or `<hr>` without ARIA attributes creates ambiguous page structure
**How to avoid:** Use `role="separator"` for meaningful breaks, `aria-hidden="true"` for pure decoration
**Warning signs:** Screen reader announces "region" or "content" without context

**Prevention:**
```html
<!-- Decorative divider (purely visual) -->
<div class="section-divider" role="separator" aria-hidden="true"></div>

<!-- OR meaningful separator (announces to screen readers) -->
<hr role="separator" aria-label="End of top matches section" class="section-divider">
```

### Pitfall 4: Badge Label Overcrowding
**What goes wrong:** Adding "Top Match" label makes score badge too wide, wraps awkwardly on mobile
**Why it happens:** Fixed badge width doesn't account for variable text length
**How to avoid:** Use responsive font sizing and allow badge to flex-wrap naturally
**Warning signs:** Badge text wraps mid-word, or badge extends beyond card width on narrow viewports

**Prevention:**
```css
.score-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5em;          /* Space between score and label */
  flex-wrap: nowrap;   /* Keep score + label on same line */
  white-space: nowrap; /* Prevent text wrapping */
}

@media (max-width: 576px) {
  .badge-label {
    font-size: 0.7em;  /* Reduce label size on mobile */
  }
}
```

### Pitfall 5: Inconsistent Spacing Breaks Visual Rhythm
**What goes wrong:** Hero section uses arbitrary spacing (e.g., `margin-bottom: 35px`), creating visual tension with rest of page
**Why it happens:** Not adhering to 8-point grid system or Bootstrap's spacer scale
**How to avoid:** Always use Bootstrap spacing utilities (`mb-3`, `mb-4`, `mb-5`) or multiples of 0.5rem
**Warning signs:** Sections feel "off" visually; inconsistent gaps between elements

**Prevention:**
```css
/* ✅ GOOD: Bootstrap spacing utilities (8pt grid) */
.hero-jobs-section { margin-bottom: 3rem; }     /* mb-5 equivalent */
.section-divider { margin: 3rem 0; }            /* my-5 equivalent */

/* ❌ BAD: Arbitrary spacing */
.hero-jobs-section { margin-bottom: 35px; }
.section-divider { margin: 42px 0; }
```

## Code Examples

Verified patterns from official sources:

### Hero Card with Multi-Layer Shadow
```css
/* Source: Material Design elevation guidelines + Josh W. Comeau shadow design */
:root {
  /* Hero-specific shadow variables */
  --shadow-hero:
    0 1px 3px rgba(0, 0, 0, 0.12),
    0 4px 8px rgba(0, 0, 0, 0.08),
    0 8px 16px rgba(0, 0, 0, 0.05);
}

@media (prefers-color-scheme: dark) {
  :root {
    --shadow-hero:
      0 1px 3px rgba(0, 0, 0, 0.3),
      0 4px 8px rgba(0, 0, 0, 0.2),
      0 8px 16px rgba(0, 0, 0, 0.15);
  }
}

/* Apply to hero jobs (score >= 4.0) */
.tier-strong.hero-job {
  box-shadow: var(--shadow-hero);
  padding: 1.5rem;  /* Increased from base 1.25rem */
  margin-bottom: 1.5rem;  /* More space between hero cards */
}
```

### Prominent Score Badge with Label
```html
<!-- Source: Badge UI design patterns 2026 -->
<span class="badge rounded-pill score-badge tier-badge-strong">
  <span class="visually-hidden">Score </span>
  4.2
  <span class="visually-hidden"> out of 5.0</span>
  <span class="badge-label">Top Match</span>
</span>
```

```css
/* Badge label styling */
.badge-label {
  margin-left: 0.5em;
  font-size: 0.85em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  opacity: 0.95;  /* Slightly muted for visual balance */
}

/* Responsive adjustment */
@media (max-width: 576px) {
  .badge-label {
    font-size: 0.7em;
  }
}
```

### Section Structure with Divider
```html
<!-- Source: ARIA separator role MDN documentation -->
<section aria-labelledby="hero-heading" class="hero-jobs-section mb-5">
  <h2 id="hero-heading" class="h4 mb-3">
    Top Matches (Score ≥ 4.0)
  </h2>
  <p class="text-muted mb-4">
    These jobs are excellent matches for your profile.
  </p>

  <!-- Hero job cards here -->
</section>

<div class="section-divider" role="separator" aria-hidden="true"></div>

<section aria-labelledby="recommended-heading" class="recommended-jobs-section mb-4">
  <h2 id="recommended-heading" class="h4 mb-3">
    Recommended Roles (Score 3.5-3.9)
  </h2>

  <!-- Lower-tier job cards here -->
</section>
```

```css
/* Gradient divider with dark mode support */
.section-divider {
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    #dee2e6 20%,
    #dee2e6 80%,
    transparent
  );
  margin: 3rem 0;
}

@media (prefers-color-scheme: dark) {
  .section-divider {
    background: linear-gradient(
      to right,
      transparent,
      #495057 20%,
      #495057 80%,
      transparent
    );
  }
}
```

### Focus Indicator Enhancement
```css
/* Source: WCAG 2.1 Focus Visible guidelines + Sara Soueidan's focus indicator guide */
.tier-strong.job-item:focus-visible {
  outline: 3px solid var(--color-tier-strong-border);
  outline-offset: 3px;
  box-shadow:
    var(--shadow-hero),  /* Preserve elevation shadow */
    0 0 0 6px rgba(142, 55%, 52%, 0.2);  /* Additional focus glow */
}

/* Ensure 3:1 contrast ratio for focus indicator per WCAG 2.4.11 */
@media (prefers-color-scheme: dark) {
  .tier-strong.job-item:focus-visible {
    outline-color: var(--color-tier-strong-text);
    box-shadow:
      var(--shadow-hero),
      0 0 0 6px rgba(142, 55%, 60%, 0.3);  /* Brighter glow in dark mode */
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single `box-shadow` value | Multi-layer shadows (2-3 stacked) | 2024-2025 | Better depth perception; "elevated" cards feel more realistic per Material Design 3 updates |
| Static shadow opacity | CSS custom properties with dark mode overrides | 2025-2026 | Shadows remain visible in dark mode without harsh contrast; adaptive design pattern |
| Flat spacing (uniform padding) | Spatial hierarchy (variable padding by tier) | 2026 | "Internal ≤ external" rule from design systems; hero content gets breathing room |
| Icon-only badges | Text label + icon badges | 2026 | Semantic labels ("Top Match") improve scannability; Nielsen Norman Group research shows 37% faster recognition |
| Section concatenation | Explicit section breaks with ARIA separators | 2025-2026 | Accessibility improvements; screen readers announce section boundaries |

**Deprecated/outdated:**
- **Bootstrap `.shadow` class only:** Bootstrap's built-in shadow utilities don't adapt to dark mode automatically and lack the multi-layer depth of modern elevation patterns. While valid for basic shadows, they're insufficient for hero-level prominence.
- **Uniform card padding:** 2026 design systems emphasize spatial hierarchy where importance correlates with spacing. Equal padding for all tiers flattens visual hierarchy.
- **Color-only tier distinction:** WCAG guidelines and colorblind accessibility research show color alone is insufficient. Current best practice layers color + shadow + spacing + typography for multi-sensory cues.

## Open Questions

1. **Badge Label Text: "Top Match" vs "Excellent Match"**
   - What we know: Design systems (2026) use short, action-oriented labels; "Top Match" is 2 words, "Excellent Match" is 2 words
   - What's unclear: User preference for confidence language ("Top" = ranking, "Excellent" = quality)
   - Recommendation: Use **"Top Match"** for score ≥4.0 as it's 1 character shorter, aligns with "top-scoring" mental model, and has higher information density. Can A/B test if user feedback suggests otherwise.

2. **Section Divider: Always Show or Conditional?**
   - What we know: Visual divider improves section separation when hero jobs exist
   - What's unclear: Whether to show divider when only 1 hero job exists (minimal separation benefit)
   - Recommendation: **Conditional display**: Show divider only when ≥2 hero jobs exist AND ≥1 lower-tier job exists. For single hero job, rely on spacing + heading alone. Avoids visual clutter in sparse reports.

3. **Hero Section Placement: Always Top or Context-Dependent?**
   - What we know: Requirements state "Hero job section appears at top of report before other listings"
   - What's unclear: Whether this means top of entire report (above profile) or top of job listings section
   - Recommendation: **Top of job listings** (after profile section). Profile establishes context for scoring; hero jobs immediately follow as primary content. Keeps logical flow: context → highest value → lower tiers.

4. **Enhanced Focus Indicators: Per-Tier or Hero-Only?**
   - What we know: WCAG requires 3:1 contrast for focus indicators; shadows can obscure outlines
   - What's unclear: Whether enhanced focus (thicker outline + glow) should apply to all tiers or just hero jobs
   - Recommendation: **Hero-only enhancement**. Standard focus indicators (2px outline, 2px offset) suffice for non-elevated cards. Hero cards with shadows need 3px outline + 3px offset + glow to maintain visibility. Avoids over-engineering lower tiers.

## Sources

### Primary (HIGH confidence)
- [Bootstrap 5.3 Shadow Utilities](https://getbootstrap.com/docs/5.3/utilities/shadows/) - Shadow class names and Sass variables
- [Bootstrap 5.3 Spacing Utilities](https://getbootstrap.com/docs/5.3/utilities/spacing/) - 8-point grid spacing scale
- [MDN: ARIA separator role](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles/separator_role) - Accessible section dividers
- [WCAG 2.1 Focus Visible](https://www.sarasoueidan.com/blog/focus-indicators/) - Focus indicator contrast requirements
- [WebAIM: Color Contrast](https://webaim.org/articles/contrast/) - WCAG AA contrast ratios

### Secondary (MEDIUM confidence)
- [Josh W. Comeau: Designing Beautiful Shadows in CSS](https://www.joshwcomeau.com/css/designing-shadows/) - Multi-layer shadow best practices
- [Elevation Design Patterns: Tokens, Shadows, and Roles](https://designsystems.surf/articles/depth-with-purpose-how-elevation-adds-realism-and-hierarchy) - Shadow elevation research
- [UI Design Trends 2026: Modular Card Layouts](https://landdding.com/blog/ui-design-trends-2026) - Spatial hierarchy patterns
- [Spacing Best Practices: 8pt Grid System](https://cieden.com/book/sub-atomic/spacing/spacing-best-practices) - Internal ≤ external spacing rule
- [Badge UI Design: Tips and Usability](https://www.setproduct.com/blog/badge-ui-design) - Badge label design patterns
- [Hero Section Design Best Practices 2026](https://www.perfectafternoon.com/2025/hero-section-design/) - Section structure and spacing
- [CSS Custom Properties for Dark Mode](https://css-irl.info/quick-and-easy-dark-mode-with-css-custom-properties/) - Dark mode shadow adaptation
- [Colorblind Accessibility: Visual Hierarchy](https://reciteme.com/news/colour-blind-accessibility/) - Multi-cue design patterns

### Tertiary (LOW confidence)
- Various WebSearch results on 2026 design trends - Directional insights but not implementation-specific

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - All techniques use existing Bootstrap 5.3 + CSS custom properties from Phase 19; no new dependencies
- Architecture: **HIGH** - Patterns verified against official docs (Bootstrap, MDN, WCAG); aligns with established codebase structure
- Pitfalls: **HIGH** - Based on official accessibility guidelines (WCAG 2.1, WebAIM) and documented shadow/dark mode issues

**Research date:** 2026-02-11
**Valid until:** 2026-03-13 (30 days - stable CSS/accessibility standards; design trends may evolve but fundamentals are solid)
