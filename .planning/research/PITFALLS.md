# Pitfalls Research: v1.4.0 Visual Design & Polish

**Domain:** Adding visual design improvements and responsive features to existing Bootstrap 5 HTML report generator
**Researched:** 2026-02-11
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Base64 Font Embedding Bloat & FOUT/FOIT

**What goes wrong:**
Embedding Inter and JetBrains Mono as base64 in the inline CSS creates massive file size bloat (fonts are 7-30x larger than typical images) with an additional 33% overhead from base64 encoding itself. Without subsetting, Inter Regular + JetBrains Mono can easily add 200-400KB to an already 120KB Bootstrap CSS inline bundle, pushing total file size past Google's 2MB crawl limit for search or causing significant performance degradation. Additionally, base64 encoding puts fonts on the critical path, blocking CSS rendering and causing FOIT (Flash of Invisible Text) where text is invisible until fonts load.

**Why it happens:**
Developers assume "single-file HTML = everything must be base64" and embed full font files with all glyphs. The promise of "no FOUT because CSS and fonts arrive together" is misleading — it doesn't speed up font delivery, it just delays the entire CSS from parsing and executing.

**How to avoid:**
1. **Subset fonts to English + basic Latin only** — reduces Inter from ~90KB TTF to ~28KB WOFF2 (70% reduction) using tools like glyphanger or pyftsubset
2. **Convert to WOFF2** (not WOFF or TTF) — Brotli compression provides 30-50% additional reduction
3. **Include only weights actually used** — Inter Regular (400) + Bold (700), JetBrains Mono Regular (400) for code
4. **Add font-display: swap** to @font-face rules — shows fallback text immediately, swaps when custom font loads
5. **Consider fallback-only for print** — print stylesheets can use system fonts (Georgia, Consolas) to avoid bloat

**Warning signs:**
- HTML file size exceeds 500KB
- Lighthouse reports "Ensure text remains visible during webfont load" warning
- Time to First Contentful Paint (FCP) > 2 seconds on 3G
- Users report blank white page on slow connections

**Phase to address:**
Phase 1 (Font System) — Must establish font subsetting and WOFF2 conversion in Python build process before implementing font changes. Should include fallback font stack testing.

---

### Pitfall 2: WCAG Contrast Regression with Custom Semantic Colors

**What goes wrong:**
Replacing Bootstrap's default blue contextual classes (primary, success, warning, danger) with custom semantic colors for job scores breaks WCAG 2.1 Level AA compliance. Bootstrap's own documentation warns that their default palette "may lead to insufficient color contrast (below the recommended WCAG 2.2 text color contrast ratio of 4.5:1 and the WCAG 2.2 non-text color contrast ratio of 3:1)". Custom brand colors often fail even worse — a "nice looking" teal that works on white backgrounds fails contrast ratio on gray table cells, or a "professional" dark blue creates insufficient contrast with black text.

**Why it happens:**
Designers pick colors visually ("looks good to me") without testing contrast ratios, especially across all combinations (text on background, borders on backgrounds, disabled states). Bootstrap's built-in `color-contrast()` Sass function isn't available in runtime CSS customization, so developers manually override CSS variables without verification.

**How to avoid:**
1. **Test ALL color combinations** with WebAIM Contrast Checker before implementation:
   - Normal text: 4.5:1 minimum
   - Large text (18pt+): 3:1 minimum
   - UI components/borders: 3:1 minimum
2. **Test with colorblind simulators** (Protanopia, Deuteranopia) — 8% of men have red-green colorblindness, so red/green for good/bad scores fails without additional visual indicators
3. **Include non-color indicators** — icons (checkmark, warning triangle), patterns, or text labels alongside color coding
4. **Document color values with contrast ratios** in code comments:
   ```css
   /* Success green: #22c55e on white = 3.4:1 (PASS AA Large) */
   ```
5. **Add Colour Contrast Analyser (CCA)** to CI/CD to automatically fail builds below WCAG AA thresholds

**Warning signs:**
- Existing accessibility tests start failing after color changes
- Light-colored warning badges have poor readability
- Color-coded scores look identical in grayscale screenshots
- Lighthouse accessibility score drops below 100

**Phase to address:**
Phase 1 (Semantic Colors) — Before implementing any color changes, establish WCAG testing protocol. Phase 3 (Accessibility CI) should catch regressions automatically.

---

### Pitfall 3: Responsive Table Display Block Losing Table Semantics

**What goes wrong:**
Converting Bootstrap tables to `display: block` or `display: flex` for mobile stacking completely removes native table semantics. Screen readers treat the table as a `<div>` soup, announcing cells as unrelated text chunks with no structural relationships. A table showing "Company | Position | Score" becomes "Company ABC Position Senior Developer Score 87 Company XYZ..." with no indication of column headers or row groupings. Even worse, if using `display: grid` or `display: flex` on Safari (pre-2024 versions), table semantics are completely dropped and assistive technology users lose all context.

**Why it happens:**
Popular CSS patterns for responsive tables use `display: block` + floats to stack rows vertically, which works visually but destroys accessibility. Developers test with visual inspection only, not with screen readers.

**How to avoid:**
1. **Never use `display: block/flex/grid` on `<table>` without ARIA restoration**
2. **When changing display properties, add explicit ARIA roles**:
   ```css
   @media (max-width: 768px) {
     table { display: block; }
   }
   ```
   ```html
   <table role="table">
     <thead role="rowgroup">
       <tr role="row">
         <th role="columnheader">Company</th>
   ```
3. **Better approach: Keep table semantics, hide non-critical columns**:
   - Use `visibility: hidden` on less important columns (not `display: none` on parent)
   - Show only critical data (company name, score) on mobile
   - Provide "View Details" expandable row or link to full data
4. **Card layout pattern**: Convert to actual cards with `<dl>` (definition list) structure:
   ```html
   <div role="article" aria-label="Job posting">
     <dl>
       <dt>Company:</dt><dd>ABC Corp</dd>
       <dt>Score:</dt><dd>87</dd>
     </dl>
   </div>
   ```
5. **Test with actual screen readers** (NVDA on Windows, VoiceOver on Mac/iOS) at mobile viewport widths

**Warning signs:**
- Screen reader announces table content as plain text paragraph
- NVDA/JAWS doesn't announce "Table with X rows" when entering table
- axe DevTools reports "Elements must have their visible text as part of their accessible name"
- Table navigation shortcuts (T to jump tables, Ctrl+Alt+arrows to navigate cells) don't work

**Phase to address:**
Phase 2 (Mobile Responsive) — Critical to address during initial mobile layout implementation. Should include screen reader testing as acceptance criteria.

---

### Pitfall 4: Bootstrap Print Stylesheet Stripping Backgrounds with !important

**What goes wrong:**
Bootstrap's built-in print stylesheet includes `background-color: transparent !important` and forces table cells to `background-color: white !important` globally, completely overriding custom score-based color coding. Attempting to add print rules like `.score-high { background-color: #d4edda !important; }` fails because Bootstrap's print reset has higher specificity or loads after custom CSS. Even if backgrounds do print, users' browsers default to "omit background graphics" in print settings, so color-coded cells print as white regardless of CSS. This destroys the visual hierarchy that was the entire point of the color system upgrade.

**Why it happens:**
Developers add print styles but don't realize Bootstrap's print CSS is already in the inline bundle fighting them. Testing print preview with default browser settings (background graphics off) doesn't reveal the issue, but users printing with that setting see broken layouts.

**How to avoid:**
1. **Override Bootstrap's print reset with higher specificity AFTER Bootstrap CSS**:
   ```css
   @media print {
     /* Override Bootstrap's transparent backgrounds */
     .table > tbody > tr > td.score-high,
     .table > tbody > tr > th.score-high {
       background-color: #d4edda !important;
       -webkit-print-color-adjust: exact !important;
       print-color-adjust: exact !important;
     }
   }
   ```
2. **Use `print-color-adjust: exact`** (and `-webkit-` prefix) to request browsers honor background colors — note this is a HINT, not a guarantee
3. **Provide non-color fallback for prints**:
   - Add borders/patterns to score ranges
   - Include score numbers explicitly ("Score: 87/100")
   - Add icons/symbols: ★★★★☆ for ratings
4. **Test print preview with "background graphics: OFF"** (the default) — verify borders/text make visual hierarchy clear
5. **Consider print-specific layout**: Simplified table with bold/italic instead of colors, or pre-computed summary section

**Warning signs:**
- Print preview shows all-white table cells
- Color-coded scores visible on screen disappear in print
- PDF exports from browser show no background colors
- User bug reports: "Printed report loses all formatting"

**Phase to address:**
Phase 2 (Print Stylesheet) — Address immediately when adding print support. Include print testing with backgrounds off in QA checklist.

---

### Pitfall 5: CSV Export Missing UTF-8 BOM Breaks Excel Special Characters

**What goes wrong:**
JavaScript Blob-based CSV export creates files that display correctly in text editors but show corrupted characters in Microsoft Excel when job titles, companies, or descriptions contain non-ASCII characters (é, ñ, ™, curly quotes, em-dashes). A job title like "Développeur Senior—Full Stack" appears as "DÃ©veloppeur Seniorâ€"Full Stack" when opened directly in Excel. Additionally, commas in company names ("Acme, Inc.") or job titles break CSV column structure, shifting data into wrong columns.

**Why it happens:**
CSV exports specify UTF-8 encoding (`charset=utf-8`) but omit the BOM (Byte Order Mark) that Excel requires to detect UTF-8. Without BOM bytes `\xEF\xBB\xBF` at the file start, Excel assumes Windows-1252 encoding. Developers test with simple ASCII data or open CSVs in text editors (which handle UTF-8 correctly) rather than Excel.

**How to avoid:**
1. **Add UTF-8 BOM prefix** to CSV content before creating Blob:
   ```javascript
   const BOM = "\uFEFF";
   const csvContent = BOM + csvData;
   const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
   ```
2. **Escape special characters** properly:
   - Wrap all fields in double quotes: `"Acme, Inc.","Senior Dev—FT","Score: 87"`
   - Escape embedded quotes by doubling: `"Company ""Quoted"" Name"` → `Company "Quoted" Name`
   - Preserve newlines in multi-line descriptions: `"Line 1\nLine 2"` works in Excel
3. **Test in actual Excel** (not Google Sheets or LibreOffice) on Windows with non-ASCII data:
   - Test company names: Citroën, Nestlé, SAP®
   - Test special chars: em-dash (—), curly quotes (" "), trademark (™)
   - Test commas in values
4. **Provide UTF-8 BOM as default**, document how to import if user manually changes encoding

**Warning signs:**
- Excel shows "DÃ©veloppeur" instead of "Développeur"
- Commas in company names cause data to shift columns
- Special characters like em-dashes (—) display as â€"
- User bug reports: "CSV file is corrupted" (but only from Excel users)

**Phase to address:**
Phase 2 (CSV Export) — Must implement BOM and proper escaping from the start. Add test suite with non-ASCII sample data.

---

### Pitfall 6: Lighthouse CI Flakiness from Dynamic Content & Timing Issues

**What goes wrong:**
Lighthouse accessibility scores fluctuate between runs (98, 100, 95, 100) in GitHub Actions CI despite identical code, causing builds to randomly fail. The HTML report loads application status from localStorage, updates counts dynamically with JavaScript, and applies filters — all of which execute at unpredictable times relative to Lighthouse's scan. Lighthouse may scan before JavaScript finishes, catching the page in an intermediate state with missing ARIA labels on filter buttons or dynamic count badges showing "0" (failing "button must have discernible text" rule). Multiple consecutive runs on the same code produce different accessibility scores, making the CI gate unreliable.

**Why it happens:**
Lighthouse's default configuration doesn't wait for JavaScript execution to complete before auditing. Dynamic content loading (localStorage reads), DOM manipulation (updating counts), and async operations create race conditions. Running Lighthouse once per commit amplifies variance — single runs are inherently flaky for performance/timing-dependent audits.

**How to avoid:**
1. **Configure multiple Lighthouse runs** (minimum 3-5) and use median score:
   ```yaml
   # .lighthouserc.json
   {
     "ci": {
       "collect": {
         "numberOfRuns": 5
       },
       "assert": {
         "preset": "lighthouse:recommended",
         "assertions": {
           "categories:accessibility": ["error", {"minScore": 0.95}]
         }
       }
     }
   }
   ```
2. **Add explicit waits** for dynamic content in Lighthouse config:
   ```javascript
   // Wait for specific elements to appear
   await page.waitForSelector('[data-status-count]', { visible: true });
   await page.waitForFunction(() => {
     const count = document.querySelector('[data-status-count]');
     return count && count.textContent !== '0';
   });
   ```
3. **Separate static vs. dynamic audits**:
   - Static audits (HTML structure, contrast, ARIA) run on every commit
   - Dynamic audits (interactive elements, localStorage state) run only on main/release branches
4. **Use axe-core directly** for more reliable accessibility testing — axe has zero false positives philosophy and better handles dynamic content
5. **Add data-* attributes** for test stability:
   ```html
   <button data-filter="applied" aria-label="Filter: Applied (5)">
     Applied <span data-testid="applied-count">5</span>
   </button>
   ```
6. **Review failed audits manually** — if Lighthouse catches an issue 1 out of 5 runs, it's likely a real race condition

**Warning signs:**
- Lighthouse accessibility scores vary by >3 points between identical runs
- CI failures for "Elements must have discernible text" that pass locally
- Intermittent failures on dynamic filter buttons or count badges
- Lighthouse reports different number of accessibility issues on consecutive runs
- GitHub Actions logs show timing differences in JavaScript execution

**Phase to address:**
Phase 3 (Accessibility CI) — Essential to configure multiple runs and waits from the start. Consider axe-core as primary tool with Lighthouse as secondary validation.

---

### Pitfall 7: JavaScript Filter State Loss & Missing Accessibility Announcements

**What goes wrong:**
Implementing status filters (Applied, Interview, Rejected) with JavaScript filtering creates two critical issues: (1) Filter state is lost on page reload — users apply filters, reload the page (F5), and all jobs reappear without filter state persisted, and (2) Screen reader users have no indication that content changed after clicking a filter button. Sighted users see jobs disappear/reappear, but screen reader users hear "Filter: Applied, button" with no announcement that "Showing 5 of 47 jobs". Additionally, using URL fragments for state (`#filter=applied`) breaks accessibility because screen readers don't announce URL changes, and fragment-based routing isn't indexed by search engines.

**Why it happens:**
Developers implement filtering as in-memory JavaScript state without persistence or live region announcements. URL fragment routing seems like an easy solution for state persistence, but it's a client-side-only approach that assistive technology doesn't recognize. Testing with mouse clicks doesn't reveal the lack of screen reader announcements.

**How to avoid:**
1. **Persist filter state in localStorage** AND URL query params (not fragments):
   ```javascript
   // Good: Query params are crawlable and can be announced
   const params = new URLSearchParams(window.location.search);
   params.set('filter', 'applied');
   window.history.replaceState({}, '', `?${params}`);
   localStorage.setItem('jobFilter', 'applied');
   ```
2. **Add ARIA live region** for filter results announcements:
   ```html
   <div aria-live="polite" aria-atomic="true" class="sr-only" id="filter-status">
     <!-- JavaScript updates this -->
   </div>
   ```
   ```javascript
   function applyFilter(status) {
     const count = filterJobs(status);
     const statusEl = document.getElementById('filter-status');
     statusEl.textContent = `Showing ${count} ${status} jobs out of ${totalJobs} total`;
   }
   ```
3. **Use aria-pressed** on filter toggle buttons to indicate active state:
   ```html
   <button aria-pressed="true" data-filter="applied">
     Applied (5)
   </button>
   ```
4. **Sync state on load**:
   ```javascript
   window.addEventListener('DOMContentLoaded', () => {
     const params = new URLSearchParams(window.location.search);
     const savedFilter = params.get('filter') || localStorage.getItem('jobFilter');
     if (savedFilter) applyFilter(savedFilter);
   });
   ```
5. **Test with screen reader** (NVDA/VoiceOver) — verify announcements after filter clicks

**Warning signs:**
- Filters reset to "All" on page reload despite user setting filter
- Screen reader testing reveals no announcement after clicking filter button
- URL shows `#filter=applied` instead of `?filter=applied`
- Users report "Filters don't stay applied when I refresh"
- axe DevTools warns "aria-live region not updated"

**Phase to address:**
Phase 2 (Status Filters) — Must implement localStorage + query param sync and ARIA live regions from the start. Include screen reader testing in acceptance criteria.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Embed full font files without subsetting | No build tooling needed, works immediately | +300KB file size, slow page loads, poor mobile UX | Never — subsetting is one-time 10min Python script |
| Use Bootstrap default colors without testing | No design work, ships faster | WCAG AA failures, accessibility lawsuit risk, user complaints | Never on WCAG-compliant products |
| `display: block` on tables without ARIA | Responsive layout works visually in 20 lines CSS | Screen reader users can't navigate data, ADA compliance fails | Never — ARIA restoration takes 5 minutes |
| Skip UTF-8 BOM in CSV export | Works in Google Sheets and text editors | Excel users see corrupted data, support tickets, reputation damage | Never — BOM is 1 line of code (`const BOM = "\uFEFF"`) |
| Single Lighthouse run in CI | Faster CI builds (30s vs. 2min) | Flaky tests, false positives/negatives, eroded trust in CI | Only for non-critical static sites; Never for accessibility compliance |
| URL fragments instead of query params for filters | Easier JavaScript, no backend needed | Breaks accessibility, SEO, shareability; localStorage alone loses state on new device | Never — query params are equally easy |
| Skip print testing with backgrounds OFF | Works in developer's print preview | Users print blank white tables, lose score context | Never — default browser setting, must test both modes |
| Base64 embed fonts as TTF/WOFF instead of WOFF2 | Simpler conversion (no pyftsubset needed) | 3-5x larger file size (WOFF2 Brotli compression is crucial) | Never — WOFF2 support is 95%+ browsers since 2018 |

## Integration Gotchas

Common mistakes when connecting to external services or existing systems.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Bootstrap 5 existing inline CSS | Appending new CSS causes Bootstrap print reset to override colors | Place custom print CSS AFTER Bootstrap in concatenation order, use higher specificity selectors |
| localStorage for filter state | Storing state but not syncing URL, breaks shareable links | Store in BOTH localStorage (persistence) AND URL query params (shareability) |
| WCAG 2.1 AA existing compliance | Assuming new color scheme maintains compliance without testing | Test every color combination with WebAIM Contrast Checker, add automated contrast checks to CI |
| Existing score color coding (Bootstrap contextual classes) | Direct replacement breaks semantics (.bg-success → .score-high) | Keep Bootstrap classes for base styling, layer custom colors via CSS variables, maintain non-color indicators |
| file:// protocol requirement | Assuming `fetch()` or external resource loading works | Everything must be inline — no external font files, no CDN links, no XHR; test by opening file:// directly |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Base64 embedding all fonts without subsetting | HTML file 800KB+, 4s load on 3G, browser hangs on open | Subset to 50-100KB total, use WOFF2, consider system font fallbacks for print | >200KB embedded fonts (Inter + JetBrains full = 400KB+) |
| Inline CSS exceeding browser parser limits | Browser refuses to render, white screen, "file too large" errors | Keep total inline CSS <500KB, minify, remove unused Bootstrap components | Total HTML >2MB (Google crawl limit), CSS >1MB (parser stress) |
| JavaScript filtering 1000+ jobs in DOM | Filter button clicks lag 500ms+, UI freezes, poor mobile performance | Virtual scrolling, pagination, or limit visible results to 200 | >500 table rows with complex filtering |
| Inline JavaScript for filters/export without minification | Page load slows, Time to Interactive increases | Minify JavaScript, defer non-critical scripts with `<!-- defer -->` comments | >50KB inline JavaScript unminified |
| Multiple font weights embedded (100-900) | 100-200KB per font family, unused weights waste bandwidth | Only embed weights actually used (400 regular + 700 bold), remove 100/200/300/500/600/800/900 | >3 font weights per family |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| CSV export not escaping formulas (=, +, @, -) | CSV injection — Excel executes formulas, potential remote code execution if user opens CSV | Prefix values starting with `=+-@` with single quote: `'=SUM(A1:A10)` or tab character |
| localStorage containing sensitive job application data | Data persists indefinitely, accessible to XSS, survives across sessions | Store only non-sensitive state (filter selections, sort order), never API keys or personal notes |
| Missing Content-Security-Policy in inline HTML | XSS risk from user-generated content (job descriptions, company names) | Add CSP meta tag: `<meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline'">` |
| Base64 encoded fonts from untrusted sources | Malicious font files can exploit rendering engine vulnerabilities | Only embed fonts from official sources (Google Fonts, JetBrains GitHub), verify checksums |
| Print CSS exposing hidden data | Hidden columns (`display: none`) may print if print stylesheet isn't comprehensive | Explicitly set `display: none !important` on sensitive fields in print media query |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Hero jobs visually distinct but not sortable | Users can't filter to "show only hero jobs" or sort by hero status | Add hero status as filterable/sortable column, include in CSV export |
| Mobile hides columns without indication | Users don't know data exists, assume fields are missing | Show "View Details" link/button to expand full row data, or tooltip "Tap for more" |
| Responsive breakpoint at 768px only | Layout breaks on iPad Pro (1024px) in portrait, large phones (≥768px) | Test at 375px, 768px, 1024px, 1280px, use fluid layouts with clamp() |
| Color-only score indicators | Colorblind users can't distinguish scores, fails WCAG 1.4.1 | Combine color + icon (★ rating) + text label ("Excellent: 87/100") |
| Print opens new tab instead of print dialog | Users confused, have to manually File → Print, extra step | Use `window.print()` JavaScript to trigger print dialog directly |
| CSV filename generic "export.csv" | Users download multiple reports, can't distinguish them | Include date + filter state: `job-radar-applied-2026-02-11.csv` |
| No loading indicator during filter | Appears broken if filtering >200 jobs takes 200ms | Add spinner or "Filtering..." text during processing, use debounce for search inputs |
| Font changes break pre-existing user zoom | Users with 150% browser zoom get clipped text or broken layouts | Test at 100%, 150%, 200% zoom, use relative units (rem, em), avoid fixed heights |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Font embedding:** Often missing subsetting — verify file size <150KB total for Inter + JetBrains Mono, check WOFF2 format, test FOUT with throttled network
- [ ] **Semantic colors:** Often missing contrast verification — run WebAIM Contrast Checker on ALL combinations, test with Deuteranopia/Protanopia simulator, verify non-color indicators exist
- [ ] **Responsive tables:** Often missing ARIA roles — test with NVDA/VoiceOver, verify table semantics preserved, check that hidden columns have `aria-hidden="true"`
- [ ] **Print stylesheet:** Often missing background color preservation — test with "background graphics: OFF" in print settings, verify borders/text-based hierarchy exists
- [ ] **CSV export:** Often missing UTF-8 BOM — open in Excel on Windows (not Mac, not Google Sheets), test with é, ñ, ™, —, verify commas in values don't break columns
- [ ] **Accessibility CI:** Often missing multiple Lighthouse runs — verify 3-5 runs configured, check for explicit waits on dynamic content, confirm axe-core as primary tool
- [ ] **Status filters:** Often missing ARIA live regions — test with screen reader, verify announcements on filter change, check localStorage + URL query param sync
- [ ] **Mobile card layout:** Often missing semantic structure — verify `<dl>` or proper ARIA roles, test skip navigation, check expandable details work with keyboard
- [ ] **Hero job visual hierarchy:** Often missing keyboard focus indicators — verify visible focus ring at 200% zoom, check color contrast on focus state ≥3:1
- [ ] **Font rendering:** Often missing cross-platform testing — test on Windows (ClearType), macOS (retina), Linux, verify fallback stack works when custom fonts fail

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Base64 fonts too large (>500KB) | LOW | 1. Generate font subset with pyftsubset/glyphanger 2. Convert to WOFF2 3. Test file size reduction 4. Re-inline into CSS |
| WCAG contrast failures post-launch | MEDIUM | 1. Audit all color combinations with CCA 2. Adjust failing colors by +10% lightness/darkness 3. Add AAA-compliant borders as fallback 4. Re-run accessibility tests |
| Table semantics lost on mobile | HIGH | 1. Add ARIA roles to ALL table elements 2. Consider card layout rewrite with `<dl>` 3. Add comprehensive screen reader testing 4. May require UX redesign |
| Bootstrap print CSS stripping backgrounds | LOW | 1. Add print CSS overrides with `!important` after Bootstrap 2. Include `print-color-adjust: exact` 3. Add border-based visual hierarchy 4. Document print-with-backgrounds instructions |
| CSV export breaks Excel | LOW | 1. Prepend UTF-8 BOM `\uFEFF` 2. Escape all values with quotes 3. Handle formula injection (prefix =, +, -, @) 4. Test with Excel on Windows |
| Lighthouse CI too flaky | MEDIUM | 1. Configure 5 runs + median scoring 2. Add explicit waits for dynamic content 3. Switch to axe-core for reliability 4. Separate static vs. dynamic audit jobs |
| Filter state lost on reload | MEDIUM | 1. Add URL query param sync 2. Implement localStorage fallback 3. Add ARIA live regions for announcements 4. Test reload scenarios |
| Mobile layout breaks at unusual widths | MEDIUM | 1. Add intermediate breakpoints (375px, 1024px, 1280px) 2. Use `clamp()` for fluid typography 3. Test on real devices (iPhone SE, iPad Pro) 4. Use container queries if complex |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Base64 font bloat & FOUT/FOIT | Phase 1: Font System | File size <150KB for fonts, Lighthouse FCP <2s, font-display: swap present |
| WCAG contrast regression | Phase 1: Semantic Colors | WebAIM Contrast Checker all combinations ≥4.5:1 text / ≥3:1 UI, colorblind simulator testing |
| Table semantics lost (display: block) | Phase 2: Mobile Responsive | NVDA announces "table with X rows", ARIA roles verified, axe-core clean scan |
| Bootstrap print CSS override | Phase 2: Print Stylesheet | Print preview with backgrounds OFF shows borders/hierarchy, color-adjust: exact confirmed |
| CSV UTF-8 BOM missing | Phase 2: CSV Export | Excel on Windows opens with é, ñ, — correct, commas in values don't break columns |
| Lighthouse CI flakiness | Phase 3: Accessibility CI | 5 Lighthouse runs with <3 point variance, axe-core zero failures, wait conditions documented |
| Filter state loss & no SR announcements | Phase 2: Status Filters | localStorage + URL param sync works, ARIA live region announces filter results, NVDA testing passes |
| Hero job accessibility | Phase 1: Hero Visual Hierarchy | Focus indicators visible at 200% zoom, ARIA labels present, keyboard navigation works |
| Responsive breakpoint gaps | Phase 2: Mobile Responsive | Test at 375px, 768px, 1024px, 1280px, no horizontal scroll, text readable at 150% zoom |
| Font rendering cross-platform | Phase 1: Font System | Visual test Windows/Mac/Linux, fallback stack tested (Georgia, Consolas), FOUT acceptable |

## Sources

**Font Embedding & Performance:**
- [Web Font Anti-pattern: Data URIs—zachleat.com](https://www.zachleat.com/web/web-font-data-uris/)
- [Base64 Encoding & Performance, Part 1 – CSS Wizardry](https://csswizardry.com/2017/02/base64-encoding-and-performance/)
- [Performance Anti-Patterns: Base64 Encoding](https://calendar.perfplanet.com/2018/performance-anti-patterns-base64-encoding/)
- [Font Subsetting: How to Optimize Font File Size - Rovity](https://rovity.io/reduce-web-font-size/)
- [Optimize web fonts | web.dev](https://web.dev/learn/performance/optimize-web-fonts)

**WCAG Color Contrast:**
- [Accessibility · Bootstrap v5.3](https://getbootstrap.com/docs/5.3/getting-started/accessibility/)
- [WebAIM: Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Colour Contrast Analyser (CCA) - Vispero](https://vispero.com/color-contrast-checker/)
- [Color Contrast for Accessibility: WCAG Guide (2026)](https://www.webability.io/blog/color-contrast-for-accessibility)

**Responsive Tables & Accessibility:**
- [Accessible Front-End Patterns For Responsive Tables (Part 1) — Smashing Magazine](https://www.smashingmagazine.com/2022/12/accessible-front-end-patterns-responsive-tables-part1/)
- [Tables, CSS Display Properties, and ARIA — Adrian Roselli](https://adrianroselli.com/2018/02/tables-css-display-properties-and-aria.html)
- [Responsive tables - ADG](https://www.accessibility-developer-guide.com/examples/tables/responsive/)
- [A Responsive Accessible Table — Adrian Roselli](https://adrianroselli.com/2017/11/a-responsive-accessible-table.html)

**Print Stylesheets:**
- [Print Styles Gone Wrong: Avoiding Pitfalls in Media Print CSS](https://blog.pixelfreestudio.com/print-styles-gone-wrong-avoiding-pitfalls-in-media-print-css/)
- [Don't Rely on Background Colors Printing | CSS-Tricks](https://css-tricks.com/dont-rely-on-background-colors-printing/)
- [Bootstrap striped table not printing to PDF | API2PDF](https://www.api2pdf.com/solved-bootstrap-striped-table-not-printing-to-pdf)
- [Tables are not printing correctly · Issue #25453 · twbs/bootstrap](https://github.com/twbs/bootstrap/issues/25453)

**CSV Export:**
- [Quick Fix for UTF-8 CSV files in Microsoft Excel — Edmundo Fuentes' Blog](https://www.edmundofuentes.com/blog/2020/06/13/excel-utf8-csv-bom-string/)
- [Opening CSV UTF-8 files correctly in Excel - Microsoft Support](https://support.microsoft.com/en-us/office/opening-csv-utf-8-files-correctly-in-excel-8a935af5-3416-4edd-ba7e-3dfd2bc4a032)
- [JavaScript CSV Download – Excel + Umlaute - DevAndy](https://devandy.de/javascript-csv-download-excel-umlaute/)
- [JavaScript CSV Export with Unicode Symbols | Shield UI](https://www.shieldui.com/javascript-unicode-csv-export)

**Lighthouse CI & Accessibility Testing:**
- [GitHub - GoogleChrome/lighthouse-ci](https://github.com/GoogleChrome/lighthouse-ci)
- [Lighthouse meets GitHub Actions - LogRocket Blog](https://blog.logrocket.com/lighthouse-meets-github-actions-use-lighthouse-ci/)
- [GitHub - dequelabs/axe-core](https://github.com/dequelabs/axe-core)
- [Axe-core by Deque | open source accessibility engine](https://www.deque.com/axe/axe-core/)

**State Management & Accessibility:**
- [Why URL state matters: A guide to useSearchParams in React - LogRocket Blog](https://blog.logrocket.com/url-state-usesearchparams/)
- [Chapter 5: Convey changes of state to screen-readers](https://accessible-vue.com/chapter/5/)
- [When a screen reader needs to announce content - VA.gov Design System](https://design.va.gov/accessibility/when-a-screen-reader-needs-to-announce-content)

**Performance & File Size:**
- [Inlining literally everything for better performance | Go Make Things](https://gomakethings.com/inlining-literally-everything-for-better-performance/)
- [Inline vs. external .js and .css — Mathias Bynens](https://mathiasbynens.be/notes/inline-vs-separate-file)
- [HTML, CSS, and JavaScript in One File: A Complete 2026 Guide](https://copyprogramming.com/howto/how-to-put-html-css-and-js-in-one-single-file)

**Font Rendering Cross-Platform:**
- [Why fonts look better on macOS than on Windows | UX Collective](https://uxdesign.cc/why-fonts-look-better-on-macos-than-on-windows-51a2b7c57975)
- [Font rendering philosophies of Windows & Mac OS X - DamienG](https://damieng.com/blog/2007/06/13/font-rendering-philosophies-of-windows-and-mac-os-x/)
- [The sad state of font rendering on Linux | Infosec scribbles](https://pandasauce.org/post/linux-fonts/)

---

*Pitfalls research for: v1.4.0 Visual Design & Polish*
*Researched: 2026-02-11*
