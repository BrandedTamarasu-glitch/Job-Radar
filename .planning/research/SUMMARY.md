# Project Research Summary

**Project:** Job Radar v1.4.0 Visual Design & Polish
**Domain:** HTML report enhancement for CLI job search tool
**Researched:** 2026-02-11
**Confidence:** HIGH

## Executive Summary

v1.4.0 enhances Job Radar's single-file HTML report with modern visual design, responsive layout, and accessibility improvements. Research reveals a fundamental tension: Stack research recommends WOFF2 base64 font embedding (150-200KB overhead) while Architecture research strongly advocates system font stacks (zero bytes, instant rendering). **Architecture wins** — base64 embedding violates performance best practices, blocks rendering, prevents caching, and contradicts the single-file constraint's spirit (portability, not bloat). System fonts like `-apple-system, Segoe UI, Roboto` provide excellent readability across platforms with zero file size impact.

The recommended approach is **CSS-first, additive integration**. All features integrate as inline CSS/JavaScript enhancements to existing `report.py` HTML generation with zero changes to Python data structures. Typography uses system fonts. Semantic colors leverage Bootstrap 5's existing CSS variables. Responsive tables transform via CSS media queries (no Python logic duplication). Status filters and CSV export use browser-side JavaScript (no server dependencies). Accessibility CI runs as separate GitHub Actions job.

Key risks center on **accessibility regression** (WCAG contrast failures with custom colors, table semantics loss from `display: block`, missing screen reader announcements) and **implementation shortcuts** (skipping font subsetting if base64 used, omitting UTF-8 BOM in CSV, single Lighthouse run causing flaky CI). Mitigation: test color contrast with WebAIM Checker before implementation, preserve table ARIA roles explicitly, add live regions for dynamic content, configure 5 Lighthouse runs with axe-core as primary tool.

## Key Findings

### Recommended Stack

Stack research focuses on **technology additions** for v1.4.0 features. Critical finding: single-file HTML constraint eliminates CDN fonts and requires either base64 embedding or CSS-only solutions.

**Core technologies:**
- **System font stacks** (overrides base64 recommendation): Zero bytes, instant rendering, native feel — Modern Font Stacks patterns for sans-serif UI and monospace code
- **fonttools + Brotli** (if base64 used): Font subsetting with pyftsubset reduces Inter from 300KB to 40KB; WOFF2 compression provides 30% better compression than WOFF — Only needed if rejecting system fonts
- **Blob API** (native browser): CSV generation client-side with no Python dependencies — Creates CSV from table DOM, triggers download via `URL.createObjectURL()`
- **Lighthouse CI + pa11y-ci**: GitHub Actions accessibility auditing with 90+ score threshold — Lighthouse for comprehensive metrics, pa11y with axe-core for deeper checks
- **Bootstrap 5.3.8** (existing): Continue using inline CSS — Semantic color variables (`--bs-success-bg-subtle`) perfect for score-based system

**Font strategy resolution:** Architecture research conclusively debunks base64 embedding — adds 150-200KB, blocks rendering, prevents browser caching, worse performance than system fonts. Use system font stacks exclusively.

### Expected Features

Feature research defines **table stakes** (users expect these) vs. **differentiators** (competitive advantage) for job dashboard design.

**Must have (table stakes):**
- **Visual hierarchy for top jobs** (≥4.0 scores) — Hero sections standard in job boards; larger cards, elevated position, visual prominence
- **Semantic color coding** — Dashboard users rely on color for at-a-glance status; 3 tiers max with accessible patterns + icons
- **Mobile responsive layout** — 60%+ traffic is mobile; 768px breakpoint for card stacking
- **Status filtering** — ATS dashboards universally provide hide/show by status; always-accessible controls
- **Print functionality** — Reports shared/archived; @media print with simplified layout
- **CSV export** — Data portability expected in analytics tools; client-side via Blob API

**Should have (competitive):**
- **Enhanced typography** — Professional feel with system font stacks; improves readability
- **Responsive table column hiding** — Maintains desktop density while supporting tablet (10→6 columns)
- **Accessibility CI automation** — Lighthouse + axe-core in GitHub Actions; catches regressions before users
- **Granular status filters** — Multi-select beyond basic hide/show
- **Mobile card layout** — Superior UX vs. squeezed tables at <768px

**Defer (v2+):**
- Dynamic font loading from CDN (breaks offline/file:// usage)
- Animated transitions (print issues, accessibility concerns)
- Real-time status sync (requires backend, breaks self-contained model)
- Complex multi-tier color schemes (5+ colors indistinguishable, accessibility issues)

### Architecture Approach

Architecture research confirms **zero data flow changes** — all features are presentation-layer CSS/JavaScript enhancements to existing `report.py` HTML generation.

**Integration pattern:** All modifications target 4 sections of `report.py`:
1. `<style>` block: +150 lines (system fonts, semantic colors, responsive media queries, print optimizations)
2. `_generate_html_report()`: +50 lines (add CSS classes, data attributes, filter UI HTML)
3. `_html_recommended_cards()`: +15 lines (hero job conditional class)
4. `<script>` block: +100 lines (status filter logic, CSV export function)

**Total estimated addition:** ~325 lines in `report.py`, +45 lines in `.github/workflows/release.yml`

**Major components:**
1. **System Font Stack** — CSS variables in `:root` with `-apple-system, Segoe UI, Roboto` fallback chain; zero file size, instant rendering
2. **Semantic Color System** — CSS custom properties with dark mode variants; leverages Bootstrap 5 variables, maintains WCAG AA contrast
3. **CSS-Only Responsive Table** — Media queries + data attributes; desktop shows 10 columns, tablet hides 4, mobile converts to cards via `display: block` + ARIA restoration
4. **Browser-Side Interactivity** — JavaScript for status filters (localStorage + URL params) and CSV export (Blob API from table DOM)
5. **Accessibility CI** — Separate GitHub Actions job; generates test report, runs Lighthouse (5 runs for median score) + axe-core, fails if accessibility <90

**File size impact:** Current ~150KB + ~10KB additions = **160KB total** (well under 200KB threshold)

### Critical Pitfalls

Research identified 7 critical pitfalls with phase-specific prevention strategies.

1. **Base64 Font Embedding Bloat & FOUT** — Full fonts add 200-400KB, block CSS rendering, cause Flash of Invisible Text. **Avoid:** Use system font stacks (zero bytes) or subset to Latin-only WOFF2 with `font-display: swap`

2. **WCAG Contrast Regression** — Custom colors often fail 4.5:1 text / 3:1 UI ratios. **Avoid:** Test ALL combinations with WebAIM Contrast Checker before implementation, include non-color indicators (icons), add CCA to CI

3. **Table Semantics Loss** — `display: block` on tables destroys screen reader navigation. **Avoid:** Add explicit ARIA roles (`role="table"`) when changing display, or use card layout with `<dl>` structure, test with NVDA/VoiceOver

4. **Bootstrap Print Override** — Bootstrap's `background-color: transparent !important` strips score colors in print. **Avoid:** Override with higher specificity AFTER Bootstrap, use `print-color-adjust: exact`, add borders as fallback, test with backgrounds OFF

5. **CSV UTF-8 BOM Missing** — Excel shows corrupted characters (DÃ©veloppeur). **Avoid:** Prepend `\uFEFF` BOM to CSV, escape commas/quotes properly, test in Excel on Windows with non-ASCII data

6. **Lighthouse CI Flakiness** — Scores fluctuate due to dynamic content timing. **Avoid:** Configure 5 runs for median, add explicit waits for localStorage/dynamic content, use axe-core as primary tool

7. **Filter State Loss** — Filters reset on reload, no screen reader announcements. **Avoid:** Persist in localStorage AND URL query params, add ARIA live regions for count updates, test with screen readers

## Implications for Roadmap

Based on research, v1.4.0 should follow a **7-phase build order** driven by dependencies and risk mitigation.

### Phase 1: Foundation (Typography & Colors)
**Rationale:** Typography and semantic colors are foundational — hero jobs, responsive layout, and filters all depend on these base styles.
**Delivers:** System font stack CSS, semantic color variables (3 tiers: Strong/Recommend/Review), dark mode support
**Addresses:** Table stakes (semantic color coding), differentiator (enhanced typography)
**Avoids:** Pitfall 1 (font bloat — using system fonts), Pitfall 2 (contrast regression — test before implementation)
**Research flag:** Standard patterns (Modern Font Stacks, Bootstrap color variables) — skip phase research

### Phase 2: Hero Jobs Visual Hierarchy
**Rationale:** Depends on semantic colors for visual reinforcement; establishes score-based prioritization before responsive work.
**Delivers:** Hero job styling (top 3 with ≥4.0 scores), "Top Match" badge, elevated card design
**Addresses:** Table stakes (visual hierarchy for top jobs)
**Uses:** Semantic colors from Phase 1, existing recommended cards structure
**Avoids:** Accessibility pitfall (must include keyboard focus indicators, color + icon)
**Research flag:** Standard job board pattern — skip phase research

### Phase 3: Responsive Layout (Table & Mobile Cards)
**Rationale:** Core usability for mobile users; more complex than hero jobs due to table semantics preservation.
**Delivers:** Responsive table column hiding (10→6 columns at 768px), mobile card layout (<768px), ARIA role restoration
**Addresses:** Table stakes (mobile responsive layout), differentiator (responsive column hiding, mobile cards)
**Implements:** CSS-only transformation with data attributes, media queries
**Avoids:** Pitfall 3 (table semantics loss — explicit ARIA roles required)
**Research flag:** **Needs research** — complex accessibility requirements, must verify ARIA patterns for display: block tables

### Phase 4: Status Filters
**Rationale:** Depends on responsive layout (reuses data attributes from table rows); enables decluttering large reports.
**Delivers:** Status filter dropdown (All/Applied/Interviewing/Rejected/Offer), localStorage + URL param persistence, ARIA live announcements
**Addresses:** Table stakes (status filtering)
**Uses:** Existing status tracking (localStorage), data-status attributes from responsive table
**Avoids:** Pitfall 7 (state loss + no announcements — localStorage + URL + live regions required)
**Research flag:** Standard filter pattern — skip phase research

### Phase 5: CSV Export
**Rationale:** Depends on status filters (can export filtered view); pure browser-side, no Python changes.
**Delivers:** "Export CSV" button, Blob API generation from table DOM, UTF-8 BOM prefix, proper escaping
**Addresses:** Table stakes (CSV export)
**Uses:** Browser Blob API, existing table structure
**Avoids:** Pitfall 5 (UTF-8 BOM missing — must prepend `\uFEFF`)
**Research flag:** Standard Blob API pattern — skip phase research

### Phase 6: Print Stylesheet
**Rationale:** Optimizes all previous features for print; must come after visual features are stable.
**Delivers:** Enhanced @media print rules, Bootstrap override with `print-color-adjust: exact`, hide interactive elements, page break control
**Addresses:** Table stakes (print functionality)
**Extends:** Existing print CSS in report.py
**Avoids:** Pitfall 4 (Bootstrap stripping backgrounds — higher specificity + borders fallback)
**Research flag:** Standard print CSS — skip phase research

### Phase 7: Accessibility CI
**Rationale:** Validates all features after implementation; enforces quality gate.
**Delivers:** GitHub Actions workflow with Lighthouse CI (5 runs, median score ≥90), axe-core integration, artifact uploads
**Addresses:** Differentiator (accessibility CI automation)
**Validates:** All visual features for WCAG AA compliance
**Avoids:** Pitfall 6 (Lighthouse flakiness — 5 runs + explicit waits + axe-core primary)
**Research flag:** **Needs research** — CI configuration, Lighthouse config for dynamic content, axe-core integration details

### Phase Ordering Rationale

- **Phases 1-2 (Foundation → Hero Jobs):** Typography and colors must exist before hero jobs can use them; low-risk, no dependencies
- **Phase 3 (Responsive Layout):** Complex due to accessibility; blocking for Phase 4 (filters need data attributes)
- **Phases 4-5 (Filters → CSV):** Sequential — CSV export can respect filter state; both browser-side JavaScript
- **Phase 6 (Print):** Optimizes previous features; must come after visual design stable
- **Phase 7 (CI):** Validates everything; acts as quality gate, not blocking for feature work

**Dependency chain:**
```
Phase 1 (Foundation) → Phase 2 (Hero Jobs)
                    ↓
                  Phase 3 (Responsive) → Phase 4 (Filters) → Phase 5 (CSV)
                                                            ↓
                                                          Phase 6 (Print)
                                                            ↓
                                                          Phase 7 (CI)
```

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 3 (Responsive Layout):** Complex accessibility patterns for `display: block` on tables — need ARIA role restoration patterns, screen reader testing guidelines, Bootstrap 5 responsive utilities compatibility
- **Phase 7 (Accessibility CI):** Lighthouse CI configuration for file:// protocol, dynamic content waits (localStorage hydration), axe-core GitHub Actions integration, multiple run configuration

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Foundation):** Modern Font Stacks + Bootstrap color variables — well-documented
- **Phase 2 (Hero Jobs):** Standard job board hero section — established pattern
- **Phase 4 (Filters):** JavaScript filtering with localStorage — existing codebase pattern
- **Phase 5 (CSV):** Blob API CSV export — well-documented browser API
- **Phase 6 (Print):** CSS @media print — standard web development

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | System fonts verified as best practice; fonttools/Blob API official docs; Architecture conclusively debunks base64 embedding |
| Features | **HIGH** | Feature research verified against competitor analysis (LinkedIn, Indeed, Glassdoor); patterns validated with UX best practices, WCAG guidelines |
| Architecture | **HIGH** | Integration patterns verified against existing codebase; all modifications additive (no breaking changes); file size impact calculated |
| Pitfalls | **HIGH** | All 7 critical pitfalls sourced from authoritative references (MDN, WebAIM, Adrian Roselli, Smashing Magazine, official tool docs) |

**Overall confidence:** **HIGH**

### Gaps to Address

**Font strategy resolved:** Stack research recommended base64 WOFF2 embedding, but Architecture research provided conclusive evidence for system fonts (performance, file size, rendering). **Decision: System fonts exclusively.** If custom fonts absolutely required later, use external WOFF2 files with aggressive subsetting (not base64).

**Total HTML file size impact:** 160KB final size is conservative estimate. Must monitor during implementation:
- Current: ~150KB (Bootstrap + inline CSS/JS)
- Phase 1-6 additions: ~10KB (CSS/JS additions)
- **If base64 fonts used:** +150-200KB (UNACCEPTABLE — reject this approach)
- Safe threshold: <200KB total

**Responsive table accessibility:** Phase 3 requires careful ARIA role restoration when using `display: block`. Adrian Roselli's research indicates Safari pre-2024 completely drops table semantics with display changes. **Mitigation:** Test on Safari 2023+, consider card-only layout if ARIA restoration insufficient, include NVDA/VoiceOver testing in acceptance criteria.

**Lighthouse CI dynamic content:** Phase 7 must handle localStorage hydration timing (status tracking loads application state on DOMContentLoaded). **Mitigation:** Configure Lighthouse to wait for `[data-status-hydrated]` attribute after JavaScript completes, or use axe-core as primary tool (zero false positives, better dynamic content handling).

**CSV formula injection:** Phase 5 must prevent CSV injection attacks. If job titles/descriptions contain `=SUM()` or similar, Excel executes formulas. **Mitigation:** Prefix values starting with `=+-@` with single quote or tab character.

## Sources

### Primary (HIGH confidence)
- **STACK.md** — fonttools (official docs), Modern Font Stacks (authoritative CSS patterns), Lighthouse CI (official Google repo), Bootstrap 5.3 (official docs)
- **FEATURES.md** — Smashing Magazine (accessible responsive tables), MDN (print CSS), GeeksforGeeks (CSV export), Job board competitor analysis (LinkedIn, Indeed, Glassdoor)
- **ARCHITECTURE.md** — CSS-Tricks (responsive tables, system fonts), Modern Font Stacks (official), Google Lighthouse CI (official), HTML Tables in Responsive Design 2026 (current best practices)
- **PITFALLS.md** — Zach Leate (web font performance authority), WebAIM (WCAG official resource), Adrian Roselli (table accessibility authority), Smashing Magazine (responsive patterns), MDN (@media print)

### Secondary (MEDIUM confidence)
- Accessible Color Tokens for Enterprise Design Systems (WCAG token patterns)
- Hero Section Design 2026 (visual priority patterns)
- Setting Up Lighthouse CI From Scratch (practical CI examples)
- GeeksforGeeks (CSV export patterns — verified against MDN)

### Tertiary (LOW confidence)
- None — all architectural decisions verified against official sources or existing Job Radar codebase patterns

---
*Research completed: 2026-02-11*
*Ready for roadmap: yes*
*Total research files: 4 (STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md)*
