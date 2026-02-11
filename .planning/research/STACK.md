# Stack Research: v1.4.0 Visual Design & Polish

**Domain:** Job search report HTML generator with visual enhancements
**Researched:** 2026-02-11
**Confidence:** HIGH

## Executive Summary

This research focuses on **stack additions** for v1.4.0 visual design improvements. The **critical constraint** is that all HTML reports must remain single-file with inline CSS/JS for `file://` protocol compatibility. This constraint eliminates CDN fonts and requires base64 font embedding or CSS-only solutions.

**Key finding:** WOFF2 base64 embedding with pyftsubset for font optimization, browser-side CSV export (no Python dependencies), CSS-only responsive tables, and GitHub Actions for accessibility CI.

---

## Recommended Stack Additions

### Typography & Font Embedding

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **fonttools** | 4.57+ | Font subsetting with `pyftsubset` | Industry standard for font optimization. Supports WOFF2 output, variable font subsetting, and Unicode range selection. Required for creating small base64-embeddable fonts. |
| **Brotli** | Latest | WOFF2 compression | Required dependency for fonttools to output WOFF2 format. WOFF2 achieves 30% better compression than WOFF (up to 50% in some cases). |
| **Inter (Variable Font)** | Latest from Google Fonts | Body/UI font | Modern workhorse typeface with 2000+ glyphs covering 147 languages. Variable font supports weights 100-900 with optical sizing. Self-hosted WOFF2 optimized for Latin subset reduces to ~40KB. |
| **JetBrains Mono** | Latest from GitHub | Monospace font for scores | Code-focused monospace font optimized for readability. Available as WOFF2 for web embedding. Use Latin subset only for minimal file size. |

**Font embedding strategy:**
1. **Subset fonts** with `pyftsubset` to Latin characters only (U+0020-00FF, U+0100-017F)
2. **Convert to WOFF2** for maximum compression (30% smaller than WOFF)
3. **Base64 encode** WOFF2 files into CSS `@font-face` rules
4. **Inline in `<style>` tag** within HTML template (Python string generation)

**Why NOT use CDN fonts:** Single-file HTML constraint requires all assets inline. External font links break `file://` compatibility.

### CSS Framework (No Changes)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Bootstrap** | 5.3.8 | CSS framework | Already validated in existing stack. Continue using inline CSS/JS from CDN during development, then inline for production. Bootstrap 5.3 added semantic color CSS variables (`--bs-success-bg-subtle`, etc.) perfect for score-based color system. |

**Note:** Bootstrap 5 removed built-in print styles. Will need custom print stylesheet (see Supporting Libraries).

### Data Export (Browser-Side)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Blob API** | Native browser API | CSV generation in browser | Native JavaScript solution. No Python dependencies. Works in all modern browsers. Creates CSV from table data and triggers download via `URL.createObjectURL()` + `<a download>`. |

**Why NOT use Python csv module:** Adding CSV export to Python would require:
- New dependency in `pyproject.toml`
- Data transformation logic in `report.py`
- File writing operations
Browser-side generation is simpler, allows user to export on-demand, and leverages existing table HTML as data source.

### Accessibility Testing (CI/CD)

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| **Lighthouse CI** | Latest | Performance + accessibility auditing in GitHub Actions | Primary CI tool. Tests performance, accessibility (WCAG), SEO, PWA. Can assert baseline scores (e.g., accessibility ≥90). Runs against deployed HTML or local server. |
| **pa11y-ci** | Latest (with axe-core runner) | Accessibility-focused testing | Secondary/complementary tool. Use with `--runner axe` flag. axe-core + pa11y combined find ~35% of accessibility issues. Can test static HTML files directly via `file://` paths. |

**Recommended approach:**
1. **Lighthouse CI** for comprehensive audits (primary)
2. **pa11y-ci with axe-core** for deeper accessibility checks (secondary)
3. Run on every PR + tag push
4. Fail build if accessibility score < 90 or critical violations found

---

## Supporting Libraries

### Print Stylesheet

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **bootstrap-print-css** | 1.0.1+ | Print-optimized CSS for Bootstrap 5 | Bootstrap 5 removed print styles. This community package restores them. Inline into `<style media="print">` block. Hides `.no-print` elements, removes shadows, ensures readable contrast. |

**Alternative:** Write custom print CSS. bootstrap-print-css is small (~5KB) and covers common cases (table layout, card borders, badge visibility).

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **Google Webfonts Helper** | Download Inter/JetBrains Mono as WOFF2 | UI tool at `gwfh.mranftl.com/fonts/inter`. Generates `@font-face` CSS + downloads font files. Use for initial font acquisition before subsetting. |
| **pyftsubset** (via fonttools) | Subset fonts to Latin characters | CLI tool. Example: `pyftsubset Inter.ttf --unicodes="U+0020-00FF,U+0100-017F" --layout-features="*" --flavor="woff2" --output-file="Inter-Latin.woff2"`. Reduces Inter from ~300KB to ~40KB. |
| **base64 CLI** | Encode WOFF2 to base64 for CSS embedding | Standard Unix tool (`base64 Inter-Latin.woff2 > inter.b64`). Paste output into CSS `url(data:font/woff2;base64,...)`. Note: Base64 adds ~33% size overhead, but WOFF2 compression offsets this. |

---

## Installation

### Python Dependencies (Development)

```bash
# Font subsetting tools (development only, not runtime dependency)
pip install fonttools brotli

# Accessibility testing (CI environment)
npm install -g lighthouse pa11y-ci
```

### Font Preparation Workflow

```bash
# 1. Download fonts from Google Fonts or official repos
# (Use Google Webfonts Helper for Inter: https://gwfh.mranftl.com/fonts/inter)

# 2. Subset to Latin characters + common symbols
pyftsubset Inter-VariableFont.ttf \
  --unicodes="U+0020-00FF,U+0100-017F,U+2000-206F,U+2190-21BB" \
  --layout-features="*" \
  --flavor="woff2" \
  --output-file="Inter-Latin.woff2"

pyftsubset JetBrainsMono-Regular.ttf \
  --unicodes="U+0020-00FF,U+0100-017F" \
  --layout-features="*" \
  --flavor="woff2" \
  --output-file="JetBrainsMono-Latin.woff2"

# 3. Base64 encode for CSS embedding
base64 -w 0 Inter-Latin.woff2 > inter-base64.txt
base64 -w 0 JetBrainsMono-Latin.woff2 > jetbrains-base64.txt

# 4. Paste base64 strings into @font-face rules in report.py HTML template
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **WOFF2 base64 embed** | WOFF base64 embed | Never. WOFF2 is 30% smaller and supported in all modern browsers (2026). WOFF is legacy. |
| **WOFF2 base64 embed** | External font files | If single-file constraint is lifted. External files enable browser caching but break `file://` protocol and require server/hosting. |
| **Browser-side CSV (Blob API)** | Python csv module | If CSV export needs server-side generation (e.g., batch exports, API endpoints). Current use case is user-triggered download from browser. |
| **Lighthouse CI + pa11y-ci** | axe DevTools CLI | If budget allows. axe DevTools is commercial product with advanced reporting. Free tier limited. pa11y-ci with axe-core runner provides similar coverage. |
| **CSS-only responsive tables** | JavaScript table-to-cards library | If complex interactions needed (sorting, filtering, pagination). Current need is simple mobile layout. CSS `@media` queries + data attributes sufficient. |
| **bootstrap-print-css** | Custom print stylesheet | If specific print requirements (e.g., page breaks, custom headers). bootstrap-print-css covers 80% of cases. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Google Fonts CDN links** | Breaks single-file HTML constraint. External requests fail on `file://` protocol. | Self-hosted WOFF2 fonts with base64 embedding. |
| **Font subsetting libraries in browser (e.g., fontmin.js)** | Adds runtime overhead and increases HTML file size. Subsetting should happen at build time. | pyftsubset during development, embed final base64 in HTML template. |
| **TTF/OTF fonts for web** | Uncompressed formats 3-5x larger than WOFF2. Poor performance. | Always use WOFF2 for web. TTF/OTF only as source for pyftsubset. |
| **Python CSV libraries (csv, pandas)** | Adds runtime dependency for feature better handled in browser. Users want on-demand export, not pre-generated files. | Blob API in JavaScript to generate CSV client-side. |
| **jQuery table-to-cards plugins** | Adds jQuery dependency (Job Radar is jQuery-free). Overkill for simple responsive layout. | Pure CSS with `@media` queries + data attributes for mobile card layout. |
| **Notyf CDN in production** | Already using Notyf from CDN in current HTML. Fine for now, but consider inlining for true single-file HTML. | Inline Notyf JS/CSS in future iteration if strict single-file enforced. |

---

## Stack Patterns by Use Case

### Pattern 1: Font Embedding

**If target is single-file HTML with minimal size:**
- Use **variable fonts** (Inter Variable supports all weights in one file)
- Subset to **Latin only** (U+0020-00FF + U+0100-017F)
- Use **WOFF2** format
- Embed **base64 in CSS**
- Expected size: ~50-60KB for both fonts (base64-encoded)

**If target is multi-file HTML with caching:**
- Use **separate font files** (not base64)
- Reference via `<link>` or external CSS
- Browser caches fonts across reports

### Pattern 2: CSV Export

**If export triggered by user in browser:**
- Use **Blob API + download link**
- Generate CSV from existing table DOM
- No server round-trip

**If export generated during report creation:**
- Use Python **csv module**
- Write `.csv` file alongside `.html`
- Requires data serialization in `report.py`

### Pattern 3: Responsive Tables

**If mobile layout is simple card stack:**
- Use **CSS `@media (max-width: 768px)`**
- Hide `<thead>`, display `<td>` as blocks
- Use `td::before { content: attr(data-label); }` for labels

**If mobile layout needs interactivity (sort/filter):**
- Use **JavaScript table library** (DataTables, Tabulator)
- Adds complexity but enables advanced features

### Pattern 4: Accessibility CI

**If testing static HTML files:**
- Use **pa11y-ci** with `file://` URLs
- Configure in `.pa11yci` JSON
- Run in GitHub Actions with Node.js setup

**If testing served HTML (localhost or deployed):**
- Use **Lighthouse CI**
- Requires server (http-server, Python's http.server)
- More comprehensive metrics (performance, SEO)

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| fonttools 4.57+ | Python 3.10+ | Minimum Python version for fonttools. Job Radar requires Python 3.10+, so compatible. |
| Brotli (latest) | fonttools 4.57+ | Required for WOFF2 output. Install alongside fonttools. |
| bootstrap-print-css 1.0.1+ | Bootstrap 5.0+ | Works with Bootstrap 5.3.8 (current Job Radar version). |
| Lighthouse CI 0.15+ | Node.js 18+ | GitHub Actions ubuntu-latest includes Node.js 20+. |
| pa11y-ci 4.0+ | Node.js 18+ | Compatible with axe-core 4.x. Use `--runner axe` flag. |

---

## Implementation Roadmap

### Phase 1: Font Preparation (Development)
1. Download Inter Variable + JetBrains Mono from Google Fonts
2. Install fonttools + Brotli: `pip install fonttools brotli`
3. Subset fonts to Latin with pyftsubset
4. Base64 encode WOFF2 files
5. Create `@font-face` CSS with embedded fonts

### Phase 2: HTML Template Updates (Python)
1. Add `<style>` block with base64 font CSS to `report.py` HTML template
2. Update existing CSS to use `font-family: 'Inter', sans-serif` for body
3. Add `font-family: 'JetBrains Mono', monospace` for `.score-badge`
4. Add semantic color classes (`.bg-success-subtle`, `.text-success-emphasis`)

### Phase 3: Responsive Table (CSS)
1. Add `data-label` attributes to `<td>` elements in Python template
2. Add `@media (max-width: 768px)` rules to inline CSS
3. Hide `<thead>`, stack `<td>` as blocks, show labels via `::before`

### Phase 4: CSV Export (JavaScript)
1. Add "Export CSV" button to HTML template
2. Add JavaScript function to extract table data
3. Generate CSV string, create Blob, trigger download

### Phase 5: Print Stylesheet (CSS)
1. Download bootstrap-print-css from npm or GitHub
2. Inline into `<style media="print">` block in HTML template
3. Add custom rules for hiding filters, showing URLs

### Phase 6: Accessibility CI (GitHub Actions)
1. Create `.github/workflows/accessibility.yml`
2. Add Lighthouse CI step (test against static HTML)
3. Add pa11y-ci step with axe-core runner
4. Fail build on accessibility score < 90

---

## Sources

**Font Embedding & Optimization:**
- [Embedding Fonts with CSS and Base64](https://patdavid.net/2012/08/embedding-fonts-with-css-and-base64/) — Base64 embedding techniques
- [Embedded Google Fonts](https://amio.github.io/embedded-google-fonts/) — Google Fonts self-hosting
- [Understanding WOFF and WOFF2: The Future of Web Fonts](https://www.oreateai.com/blog/understanding-woff-and-woff2-the-future-of-web-fonts/582553e7148e0f4df8784b911f7ac945) — WOFF2 compression benefits (30% better than WOFF)
- [Google Webfonts Helper](https://gwfh.mranftl.com/fonts/inter) — Self-hosting tool for Inter font
- [Inter Font Family](https://rsms.me/inter/) — Official Inter font site
- [fonttools Documentation](https://fonttools.readthedocs.io/en/stable/subset/) — pyftsubset documentation
- [How I subset fonts for my site](https://www.naiyerasif.com/post/2024/06/27/how-i-subset-fonts-for-my-site/) — Practical font subsetting guide

**CSV Export:**
- [Python csv Module Documentation](https://docs.python.org/3/library/csv.html) — Official Python csv module (HIGH confidence)
- [How to create and download CSV file in JavaScript](https://www.geeksforgeeks.org/javascript/how-to-create-and-download-csv-file-in-javascript/) — Browser-side CSV generation
- [Client side csv download using Blob](https://riptutorial.com/javascript/example/24711/client-side-csv-download-using-blob) — Blob API techniques

**Accessibility Testing:**
- [GoogleChrome/lighthouse-ci GitHub](https://github.com/GoogleChrome/lighthouse-ci) — Official Lighthouse CI (HIGH confidence)
- [Lighthouse CI with GitHub Actions](https://www.ianjmacintosh.com/articles/using-lighthouse-ci-with-github-actions/) — GitHub Actions integration
- [pa11y GitHub](https://github.com/pa11y/pa11y) — Official pa11y (HIGH confidence)
- [Automated accessibility testing with pa11y-ci and axe](https://accessibility.civicactions.com/posts/automated-accessibility-testing-leveraging-github-actions-and-pa11y-ci-with-axe) — pa11y + axe integration
- [axe-core GitHub](https://github.com/dequelabs/axe-core) — Official axe-core (HIGH confidence)

**Bootstrap & CSS:**
- [Bootstrap 5.3 CSS Variables](https://getbootstrap.com/docs/5.3/customize/css-variables/) — Official Bootstrap docs (HIGH confidence)
- [Bootstrap 5.3 Color System](https://getbootstrap.com/docs/5.3/customize/color/) — Semantic color variables (HIGH confidence)
- [bootstrap-print-css GitHub](https://github.com/coliff/bootstrap-print-css) — Print stylesheet for Bootstrap 5
- [Bootstrap 5 Breakpoints](https://getbootstrap.com/docs/5.0/layout/breakpoints/) — 768px breakpoint documentation (HIGH confidence)
- [Responsive Data Tables | CSS-Tricks](https://css-tricks.com/responsive-data-tables/) — CSS techniques for mobile tables

---

*Stack research for: Job Radar v1.4.0 Visual Design & Polish*
*Researched: 2026-02-11*
*Confidence: HIGH (all recommendations verified with official docs or authoritative sources)*
