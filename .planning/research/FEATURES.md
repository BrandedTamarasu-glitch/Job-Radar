# Feature Research: Visual Design & Polish (v1.4.0)

**Domain:** Job Board HTML Report Dashboard
**Researched:** 2026-02-11
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in modern job board dashboards. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Visual hierarchy for top jobs | Users expect important items to stand out; universal UX principle across all dashboards | LOW | Hero sections are standard in job boards; larger cards, elevated position, visual prominence expected for ≥4.0 scores |
| Semantic color coding | Dashboard users rely on color to interpret status/severity at a glance; traffic light patterns ubiquitous | LOW | Red/yellow/green or warm/cool spectrum; must avoid 5+ color variations (users can't distinguish); requires accessible patterns + icons |
| Mobile responsive layout | 60%+ web traffic is mobile; non-responsive = broken experience | MEDIUM | 768px breakpoint standard; card stacking on mobile is expected pattern for data-heavy interfaces |
| Status filtering | ATS/recruitment dashboards universally provide hide/show by status; users expect control over noise | LOW | "Hide applied", "Hide rejected" are table stakes; always-accessible filters via fixed header or persistent controls |
| Print functionality | Reports are shared/archived; print-to-PDF is standard browser workflow | LOW | @media print with simplified layout; remove interactive elements, linearize, optimize ink/color |
| CSV export | Data portability is expected in any dashboard with tabular data; universal feature in analytics/reporting tools | LOW-MEDIUM | Client-side via Blob API is modern standard; no server required for static HTML reports |

### Differentiators (Competitive Advantage)

Features that set Job Radar apart. Not required, but valuable for user experience.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Enhanced typography (Inter + JetBrains Mono) | Professional, modern feel; improves readability and data scanning | LOW | Inter for UI/body (small size readability), JetBrains Mono for technical data (job IDs, dates); established pairing pattern |
| Responsive table with smart column hiding | Maintains data density on desktop while gracefully degrading to essentials on mobile | MEDIUM | Priority column pattern: hide supplementary data at breakpoints; Bootstrap d-none d-md-table-cell or data-priority attributes |
| Accessibility CI automation | Proactive quality assurance; catches regressions before users encounter them | MEDIUM | Lighthouse + axe-core in GitHub Actions is established 2026 pattern; runs on PR, prevents merge if fails |
| Granular status filters | Go beyond hide/show to filter by specific status (Applied, Interviewing, Rejected, Offer) | LOW | ATS dashboards provide multi-select or dropdown status filters; enhances existing localStorage-based status tracking |
| Mobile card layout (<768px) | Superior mobile UX compared to squeezed table; optimized for touch targets and thumb zones | MEDIUM | Cards show critical info (title, company, score, status); "View details" expands; standard mobile-first pattern |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems in the single-file HTML context.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Server-side CSV generation | "Python should handle export" | Breaks file:// workflow; requires running server or CLI command; defeats self-contained report model | Client-side Blob API export from browser; works offline, no dependencies, instant download |
| Complex multi-tier color schemes | "More colors = more information" | Studies show 5+ color variations are indistinguishable; creates accessibility issues; increases cognitive load | Stick to 3 semantic tiers (Strong/Recommend/Review); use patterns/icons for additional distinction |
| Dynamic font loading from CDN | "Faster than embedding fonts" | Breaks offline/file:// usage; privacy concerns (Google Fonts tracking); external dependency | Embed WOFF2 fonts in CSS (modern compression); single-file remains portable and works offline |
| Animated transitions/micro-interactions | "Modern dashboards have smooth animations" | Print issues; accessibility concerns (prefers-reduced-motion); unnecessary complexity for static report | Focus on solid information hierarchy and clear visual design; static = fast, accessible, printable |
| Real-time status sync across devices | "Status should sync between computers" | Requires backend/sync service; breaks self-contained model; scope creep for CLI tool | Keep localStorage-based status tracking; provide JSON export/import for manual sync if needed |

## Feature Dependencies

```
[Enhanced Typography]
    └──requires──> Font embedding in CSS (WOFF2 format)
    └──enhances──> Visual hierarchy for hero jobs (better readability)

[Semantic Color Coding]
    └──requires──> Existing score tiers (4.0+, 3.5-3.9, 2.8-3.4)
    └──enhances──> Visual hierarchy for hero jobs (color reinforces importance)
    └──requires──> Accessible patterns/icons (WCAG compliance)

[Hero Jobs Visual Hierarchy]
    └──requires──> Score filtering (≥4.0 threshold already exists)
    └──enhanced-by──> Semantic color coding
    └──enhanced-by──> Enhanced typography

[Responsive Table Column Hiding]
    └──requires──> Bootstrap 5 responsive utilities (already present)
    └──conflicts──> Mobile card layout (both solve same problem; use card layout <768px, hide columns ≥768px)

[Mobile Card Layout]
    └──requires──> 768px breakpoint CSS
    └──requires──> Existing job card structure (already exists for recommended section)
    └──replaces──> Responsive table at mobile sizes (<768px)

[Status Filters]
    └──requires──> Existing status tracking (localStorage, already built)
    └──enhances──> Application status workflow (makes large reports more manageable)

[CSV Export (Client-side)]
    └──requires──> All-results table data (already present)
    └──requires──> Blob API + download attribute (browser standard)
    └──independent──> No server dependencies

[Print-friendly Stylesheet]
    └──requires──> @media print CSS rules
    └──requires──> Existing HTML structure
    └──conflicts──> Interactive elements (hide filters, buttons, navigation in print)

[Accessibility CI]
    └──requires──> GitHub Actions workflow (.github/workflows/)
    └──requires──> Lighthouse CLI + axe-core packages
    └──validates──> All visual features (color contrast, semantic HTML, ARIA)
```

### Dependency Notes

- **Hero jobs requires score filtering:** Already have ≥4.0 threshold logic; just need visual differentiation
- **Semantic color coding requires accessible patterns:** Color alone insufficient for WCAG; need icons or patterns + sufficient contrast ratios
- **Responsive table conflicts with mobile card layout:** Use card layout <768px (superior mobile UX), use column hiding ≥768px (maintain data density on larger screens)
- **Status filters enhance existing status tracking:** Builds on v1.3.0's localStorage-based status management; no new data model needed
- **CSV export is independent:** Pure client-side; no server dependencies; works with existing table structure
- **Print stylesheet conflicts with interactive elements:** Hide status filters, copy buttons, navigation in @media print; show content only
- **Accessibility CI validates all features:** Acts as quality gate; ensures color contrast, focus indicators, semantic HTML maintained

## MVP Definition (v1.4.0 Scope)

### Launch With (v1.4.0)

Core visual improvements that make the report professional and usable.

- [x] **Hero jobs visual hierarchy (≥4.0)** — Table stakes; users expect top matches to stand out
- [x] **Semantic color coding by score tier** — Table stakes; enables at-a-glance interpretation of results
- [x] **Enhanced typography (Inter + JetBrains Mono)** — Differentiator; professional appearance, improved readability
- [x] **Responsive table column hiding (10→6 columns)** — Table stakes; maintains desktop usability while supporting tablet/smaller screens
- [x] **Mobile card layout (<768px breakpoint)** — Differentiator; superior mobile UX compared to squeezed tables
- [x] **Status filters (hide/filter by status)** — Table stakes in ATS/job dashboards; leverages existing status tracking
- [x] **Print-friendly stylesheet** — Table stakes; reports are archived/shared as PDFs
- [x] **CSV export (client-side)** — Table stakes; data portability expected in dashboards
- [x] **Accessibility CI (Lighthouse + axe)** — Differentiator; proactive quality assurance, prevents regressions

### Rationale

All features are either table stakes (users expect them) or low-to-medium complexity differentiators that significantly improve UX. No feature requires server-side changes or breaks the self-contained HTML model. All features build on existing structure (Bootstrap 5, status tracking, job cards, score tiers).

### Deferred (Future Consideration)

Features mentioned in research but out of scope for v1.4.0:

- **Advanced analytics dashboard** — Beyond scope of simple report; would require persistent data store
- **Real-time collaboration features** — Requires backend; breaks self-contained model
- **Custom color theme editor** — Low value for CLI tool; adds complexity for minimal benefit
- **Drag-and-drop column reordering** — Nice-to-have; table is already optimized with priority column strategy
- **Saved filter presets** — Could use localStorage but adds UI complexity; "Hide applied/rejected" covers 90% of use cases

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Hero jobs visual hierarchy | HIGH | LOW | P1 |
| Semantic color coding | HIGH | LOW | P1 |
| Enhanced typography | MEDIUM | LOW | P1 |
| Mobile card layout | HIGH | MEDIUM | P1 |
| Status filters | HIGH | LOW | P1 |
| Print-friendly stylesheet | MEDIUM | LOW | P1 |
| CSV export (client-side) | HIGH | LOW-MEDIUM | P1 |
| Responsive table column hiding | MEDIUM | MEDIUM | P2 |
| Accessibility CI | MEDIUM | MEDIUM | P2 |

**Priority key:**
- P1: Must have for v1.4.0 launch (core visual polish)
- P2: Should have for v1.4.0, but could slip to v1.4.1 if needed (quality assurance)

**Note:** Responsive table column hiding is P2 because mobile card layout (<768px) is higher priority for mobile users, and desktop users already have functional 10-column table. Column hiding is optimization, not blocker.

## Expected Behaviors & UX Patterns

### Hero Jobs Visual Hierarchy (≥4.0 Score)

**Standard pattern:** Featured/hero sections in job boards use larger cards, elevated position (top of results), visual prominence (borders, shadows, backgrounds).

**Expected behaviors:**
- Distinct section header ("Top Matches" or "Highly Recommended")
- Larger card size (1.2-1.5x normal) or full-width treatment
- Visual elevation (shadow, border, background color different from standard cards)
- Positioned above main results table
- Limited quantity (only ≥4.0 scores; typically 3-8 jobs in practice)

**Reference:** Job boards like Indeed, LinkedIn, Glassdoor use hero/featured job sections at top of search results.

**Complexity:** LOW — Existing recommended section already uses cards; just need to emphasize ≥4.0 subset with distinct styling.

### Semantic Color Coding by Score Tier

**Standard pattern:** Dashboard color semantics use warm colors (red/orange) for warnings/low scores, cool colors (green/blue) for positive/high scores, or traffic light pattern (red/yellow/green).

**Expected behaviors:**
- 3 tiers max (studies show 5+ variations are indistinguishable)
  - Strong (≥4.0): Green or success color
  - Recommend (3.5-3.9): Blue or info color
  - Worth Reviewing (2.8-3.4): Yellow/orange or warning color
- Color PLUS pattern/icon (WCAG requires non-color indicators)
- Consistent across score badges, hero cards, table rows
- Sufficient contrast ratios (4.5:1 text, 3:1 UI components)

**Accessibility requirement:** Cannot rely on color alone; must use icons, patterns, or text labels in addition to color.

**Reference:** DataCamp dashboard design best practices, semantic color systems in Carbon Design.

**Complexity:** LOW — Bootstrap 5 already provides semantic color classes (bg-success, bg-info, bg-warning); need to apply consistently + add accessible icons.

### Enhanced Typography (Inter + JetBrains Mono)

**Standard pattern:** Modern dashboards use sans-serif for UI/body (readability at small sizes) + monospace for technical data (numbers, codes, dates).

**Expected behaviors:**
- Inter for headings, body text, UI labels (optimized for small sizes, clean geometric forms)
- JetBrains Mono for job IDs, dates, technical fields (consistent character width, distinguishable characters like 0/O, 1/l/I)
- Font embedding via @font-face with WOFF2 format (modern compression, wide browser support)
- Fonts embedded in CSS (no CDN dependencies; maintains offline/file:// compatibility)

**Implementation note:** Inter + JetBrains Mono is established pairing pattern used in dev tools and dashboards.

**Reference:** JetBrains Mono font pairing resources, modern web typography 2026 trends.

**Complexity:** LOW — Embed WOFF2 fonts in CSS, apply font-family to relevant selectors.

### Responsive Table Column Hiding (10→6 Columns)

**Standard pattern:** Priority column pattern hides non-essential columns at breakpoints using CSS media queries or Bootstrap responsive utilities.

**Expected behaviors:**
- Desktop (≥992px): All 10 columns visible
- Tablet (768-991px): Hide 4 least important columns (show 6 core: Title, Company, Score, Location, Date, Status)
- Mobile (<768px): Replace table with card layout (separate feature)
- Bootstrap approach: `<th class="d-none d-lg-table-cell">` hides column except on large screens
- Column priority hierarchy (always show → sometimes show → hide on small screens):
  - P1 (always): Job Title, Company, Match Score, Status
  - P2 (tablet+): Location, Posted Date
  - P3 (desktop only): Source, Skills, Description excerpt, Action buttons

**Optional enhancement:** Column chooser menu (user can override defaults), but out of scope for v1.4.0.

**Reference:** Accessible front-end patterns for responsive tables (Smashing Magazine), Bootstrap responsive utilities.

**Complexity:** MEDIUM — Need to determine column priority hierarchy, apply responsive classes, test across breakpoints.

### Mobile Card Layout (<768px Breakpoint)

**Standard pattern:** Mobile-first approach uses card grid for data-heavy interfaces; stacks vertically on mobile, 2-column grid on tablet.

**Expected behaviors:**
- <768px: Single column card stack (full width)
- Each card shows critical info (title, company, score badge, status, posted date)
- Expandable/collapsible for full details (or link to details)
- Large touch targets (44x44px minimum per WCAG)
- Card design mirrors existing recommended jobs cards (consistency)
- Replaces table entirely on mobile (table hidden, cards shown)

**CSS approach:** Use `@media (max-width: 767px)` to hide table, show cards; CSS Grid with 1 column on mobile, 2 columns on tablet (768-991px).

**Reference:** CSS Grid mobile-first patterns, responsive card layouts, Bootstrap card components.

**Complexity:** MEDIUM — Need to duplicate table data into card markup (or generate dynamically with JS), ensure accessibility (semantic HTML, focus management).

### Status Filters (Hide Applied/Rejected, Filter by Status)

**Standard pattern:** ATS and recruitment dashboards provide always-accessible filters to show/hide by status; often checkbox toggles or multi-select dropdowns.

**Expected behaviors:**
- Quick toggles: "Hide Applied", "Hide Rejected" (most common use case: declutter already-processed jobs)
- Advanced filter: Dropdown or checkbox group to show only specific statuses (Applied, Interviewing, Rejected, Offer, or Not Applied)
- Filters always accessible (fixed header, or persistent controls above results)
- Filter state saved in localStorage (persistence across page reloads)
- Clear visual feedback when filters active ("X jobs hidden" indicator)
- "Clear filters" button to reset

**Implementation approach:** JavaScript to toggle visibility (add/remove CSS class on filtered rows/cards), localStorage to persist filter state.

**Reference:** Filter UX best practices (Smashing Magazine, Pencil & Paper), ATS dashboard patterns.

**Complexity:** LOW — Build on existing status tracking (localStorage), use JS to show/hide elements based on data-status attribute.

### CSV Export (Client-Side)

**Standard pattern:** Modern dashboards use Blob API + download attribute for client-side CSV generation; no server required.

**Expected behaviors:**
- "Export to CSV" button in report header or above table
- Exports all-results table data (all columns, all rows, respecting current filter state is optional)
- CSV includes headers (column names) in first row
- Filename includes date/context (e.g., "job-radar-results-2026-02-11.csv")
- Instant download (no server round-trip)
- Works offline (file:// protocol compatible)

**Implementation approach:**
```javascript
// Create CSV string from table data
const csv = tableToCSV(tableElement);
// Create Blob
const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
// Generate object URL
const url = URL.createObjectURL(blob);
// Trigger download via anchor element
const link = document.createElement('a');
link.href = url;
link.download = filename;
link.click();
// Clean up object URL
URL.revokeObjectURL(url);
```

**Browser support:** Blob API supported in all modern browsers; legacy IE 10+ support via `navigator.msSaveBlob`.

**Reference:** GeeksforGeeks JavaScript CSV creation, client-side file download tutorials.

**Complexity:** LOW-MEDIUM — Straightforward Blob API usage; complexity in parsing table to CSV (handle quotes, commas, newlines in cell data).

### Print-Friendly Stylesheet

**Standard pattern:** @media print rules remove interactive elements, simplify layout, optimize for ink/paper.

**Expected behaviors:**
- Hide interactive elements: navigation, buttons (copy, status buttons, export), filters
- Hide supplementary content: manual search URL links (not essential for printed record)
- Simplify header: Job count summary, date generated, key filters applied
- Preserve content: Job cards/table, scores, statuses, company names, dates
- Optimize colors: Light backgrounds (save ink), sufficient contrast for black-and-white printing
- Page breaks: Avoid breaking job cards across pages (`page-break-inside: avoid`)
- Margins: Set @page margins for consistent printout
- Font sizes: Ensure readable at print scale (12pt minimum for body text)

**CSS approach:**
```css
@media print {
  .no-print { display: none; }
  body { font-size: 12pt; color: #000; background: #fff; }
  .job-card { page-break-inside: avoid; }
  @page { margin: 1in; }
}
```

**Reference:** MDN @media print guide, SitePoint print-friendly CSS, print stylesheet best practices 2026.

**Complexity:** LOW — Standard CSS; main work is identifying what to hide vs. preserve.

### Accessibility CI (Lighthouse + axe-core in GitHub Actions)

**Standard pattern:** Automated accessibility testing in CI/CD with Lighthouse and axe-core; fails PR if violations found.

**Expected behaviors:**
- GitHub Actions workflow runs on pull requests
- Lighthouse CI generates accessibility score (target: 90+)
- axe-core scans for WCAG 2.1 Level AA violations
- Workflow fails if accessibility score drops or new violations introduced
- Prevents merge if checks fail (enforces quality gate)
- Reports include details of violations (which elements, which rules)

**Implementation approach:**
- `.github/workflows/accessibility.yml` defines workflow
- Workflow installs Lighthouse CLI + axe-core packages
- Runs against generated HTML report (need to generate report in CI, or test against static fixture)
- Parses results, fails build if thresholds not met

**Tools:**
- `@lhci/cli` (Lighthouse CI)
- `axe-core` or `pa11y-ci` (axe-core wrapper for CI)
- GitHub Actions for automation

**Reference:** Automating accessibility tests with GitHub Actions (bolonio.medium.com), Lighthouse CI GitHub repo.

**Complexity:** MEDIUM — Requires CI configuration, understanding of Lighthouse/axe output formats, deciding on thresholds. Maintenance as rules evolve.

## Feature Interaction Matrix

| Feature A | Feature B | Relationship | Notes |
|-----------|-----------|--------------|-------|
| Hero jobs hierarchy | Semantic color coding | Synergistic | Color reinforces visual hierarchy for ≥4.0 jobs |
| Semantic color coding | Accessibility CI | Required | CI enforces color contrast ratios, non-color indicators |
| Responsive table | Mobile card layout | Complementary | Table ≥768px, cards <768px; solve same problem at different breakpoints |
| Status filters | Mobile card layout | Synergistic | Filters work on both table (desktop) and cards (mobile) |
| Status filters | CSV export | Independent | Export can respect or ignore filter state (design decision) |
| Print stylesheet | Status filters | Conflict | Hide filters in print; show filtered content only |
| Print stylesheet | CSV export | Conflict | Hide export button in print (not functional on paper) |
| Enhanced typography | All features | Foundation | Improves readability across all visual features |
| Accessibility CI | All features | Validation | Ensures all features meet WCAG standards |

## Competitor Feature Analysis

| Feature | LinkedIn Jobs | Indeed | Glassdoor | Job Radar Approach |
|---------|---------------|--------|-----------|---------------------|
| Hero/featured jobs | Premium feature (paid) | Sponsored listings (ads) | Featured employer jobs (paid) | Algorithmic (≥4.0 score); free, based on match quality |
| Color coding | None (uniform cards) | Minimal (sponsored badge) | Employer branding colors | Semantic tiers for match score; universal, not employer-specific |
| Mobile layout | Card grid (all sizes) | Card grid (all sizes) | Card grid (all sizes) | Cards <768px, table ≥768px; optimizes for each form factor |
| Status tracking | Applied/Saved (account req) | Applied (account req) | Applied (account req) | localStorage (no account); JSON export for portability |
| CSV export | Not available | Not available | Not available | Client-side export; differentiator for offline/analysis workflows |
| Print-friendly | Basic browser print | Basic browser print | Basic browser print | Optimized @media print; removes clutter, preserves key data |
| Accessibility | WCAG compliant (large co.) | WCAG compliant (large co.) | WCAG compliant (large co.) | WCAG AA + CI enforcement; proactive quality assurance |

**Key differentiators:**
- **Algorithmic hero jobs** (not pay-to-play): Job Radar's ≥4.0 hero section is based on match quality, not advertiser dollars
- **Offline-first with CSV export**: Competitors require accounts, online access; Job Radar is portable, exportable, works offline
- **Optimized hybrid layout**: Competitors use cards everywhere; Job Radar uses data-dense table on desktop (10 columns), cards on mobile (superior UX for each form factor)

## Sources

### Visual Hierarchy & Design Patterns
- [15 Easy-to-Use Job Board Templates in 2026 - JBoard](https://jboard.io/blog/job-board-templates)
- [2025's Modern Job Portal Dashboard – Clean UI Design](https://multipurposethemes.com/blog/2025s-modern-job-portal-dashboard-clean-ui-design/)
- [Stunning hero sections for 2026: Layouts, patterns, and examples](https://lexingtonthemes.com/blog/stunning-hero-sections-2026)
- [Visual Hierarchy in Web Design 2026: Guide to User Attention](https://theorangebyte.com/visual-hierarchy-web-design/)
- [25 Job Board Website Design Examples For Inspiration](https://www.subframe.com/tips/job-board-website-design-examples)

### Responsive Tables & Mobile Patterns
- [Accessible Front-End Patterns For Responsive Tables (Part 1) — Smashing Magazine](https://www.smashingmagazine.com/2022/12/accessible-front-end-patterns-responsive-tables-part1/)
- [HTML Tables in Responsive Design: Do's and Don'ts (2026)](https://618media.com/en/blog/html-tables-in-responsive-design/)
- [CSS Grid Responsive Design: The Mobile-First Approach That Actually Works](https://medium.com/codetodeploy/css-grid-responsive-design-the-mobile-first-approach-that-actually-works-194bdab9bc52)
- [Breakpoint: Responsive Design Breakpoints in 2025 | BrowserStack](https://www.browserstack.com/guide/responsive-design-breakpoints)

### CSV Export
- [How to create and download CSV file in JavaScript - GeeksforGeeks](https://www.geeksforgeeks.org/javascript/how-to-create-and-download-csv-file-in-javascript/)
- [Create and download data in CSV format using plain JavaScript](https://code-maven.com/create-and-download-csv-with-javascript)
- [JavaScript File Download: Browser-Side Solutions for Saving Files](https://sqlpey.com/javascript/javascript-file-download-solutions/)

### Print Stylesheets
- [Printing - CSS | MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing)
- [How to Create Printer-friendly Pages with CSS — SitePoint](https://www.sitepoint.com/css-printer-friendly-pages/)
- [Designing for Print with CSS Tips (2025)](https://618media.com/en/blog/designing-for-print-with-css-tips/)
- [CSS Print Padding on Every Page: Complete Guide with 2026 Best Practices](https://copyprogramming.com/howto/css-css-print-padding-on-every-page)

### Semantic Color Coding
- [The Color-Coded Dashboard: Techniques for Improved Data Interpretation](https://medium.com/@grow.com/the-color-coded-dashboard-techniques-for-improved-data-interpretation-047f4bfec4b4)
- [Semantic Colors in UI/UX Design: A beginner's Guide to Functional Color Systems](https://medium.com/@zaimasri92/semantic-colors-in-ui-ux-design-a-beginners-guide-to-functional-color-systems-cc51cf79ac5a)
- [Dashboard UX design: best practices & real-world examples](https://www.lazarev.agency/articles/dashboard-ux-design)

### Typography
- [JetBrains Mono font pairing with Inter](https://maxibestof.one/typefaces/jetbrains-mono/pairing/inter)
- [JetBrains Mono: A free and open source typeface for developers](https://www.jetbrains.com/lp/mono/)
- [Best Fonts for Web Design in 2025 | Modern Web Typography Trends](https://shakuro.com/blog/best-fonts-for-web-design)

### Status Filters & Dashboard UX
- [Filter UX Design Patterns & Best Practices - Pencil & Paper](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-filtering)
- [Hidden vs. Disabled In UX — Smashing Magazine](https://www.smashingmagazine.com/2024/05/hidden-vs-disabled-ux/)
- [Recruiting Dashboard— a UX/UI Design Challenge](https://meganxyxx.medium.com/scoutible-a-ux-ui-design-challenge-c25295255335)
- [How to Boost Your Hiring with Right Applicant Tracking System Design](https://www.eleken.co/blog-posts/applicant-tracking-system-design-how-to-make-recruitment-better-for-everyone)

### Accessibility CI
- [Automating the accessibility tests of your source code with GitHub Actions](https://bolonio.medium.com/automating-the-accessibility-tests-of-your-source-code-with-github-actions-63590cdc6860)
- [Automated accessibility testing: Leveraging GitHub Actions and pa11y-ci with axe](https://accessibility.civicactions.com/posts/automated-accessibility-testing-leveraging-github-actions-and-pa11y-ci-with-axe)
- [From Theory to Automation: WCAG compliance using axe-core, next.js, and GitHub actions](https://medium.com/@SkorekM/from-theory-to-automation-wcag-compliance-using-axe-core-next-js-and-github-actions-b9f63af8e155)
- [GitHub - GoogleChrome/lighthouse-ci: Automate running Lighthouse](https://github.com/GoogleChrome/lighthouse-ci)

---
*Feature research for: Job Radar v1.4.0 — Visual Design & Polish*
*Researched: 2026-02-11*
*Confidence: HIGH*
