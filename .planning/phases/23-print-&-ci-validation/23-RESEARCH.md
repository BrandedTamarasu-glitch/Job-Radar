# Phase 23: Print & CI Validation - Research

**Researched:** 2026-02-11
**Domain:** CSS Print Stylesheets + GitHub Actions CI (Lighthouse + axe-core)
**Confidence:** HIGH

## Summary

Phase 23 has two distinct sub-domains: (1) a CSS print stylesheet enhancement in `report.py` and (2) a new GitHub Actions workflow for accessibility CI. Both are well-understood domains with established patterns.

The print stylesheet work is straightforward CSS -- expanding the existing `@media print` block (currently 4 lines at line 417 in report.py) to hide interactive elements (copy buttons, status dropdowns, filter controls, keyboard hints), preserve tier score colors with `print-color-adjust: exact`, and add `break-inside: avoid` rules to prevent job entries from splitting across pages. Bootstrap 5 strips background colors in print by default; overriding this requires higher specificity via `!important` combined with `print-color-adjust`.

The CI work requires a new `.github/workflows/accessibility.yml` workflow that runs on PRs. It uses `treosh/lighthouse-ci-action@v12` (community-maintained GitHub Action wrapping `@lhci/cli`) for Lighthouse audits, and `@axe-core/cli` for WCAG violation scanning. Both tools need the HTML served over HTTP (not file://), so the workflow must generate a sample report and serve it via Python's `http.server` or Lighthouse CI's `staticDistDir`. The prior decision from STATE.md locks in: Lighthouse CI with 5 runs for median score + axe-core as primary tool.

**Primary recommendation:** Two-part implementation -- (1) expand the existing `@media print` CSS block in report.py with ~30 lines of print rules, (2) create a new `accessibility.yml` workflow with Lighthouse CI (5 runs, median >=0.95 accessibility score) + axe-core (WCAG 2.1 AA, `--exit` flag), both using `staticDistDir` or a local Python HTTP server for the generated report.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@lhci/cli` | 0.15.x | Lighthouse CI runner | Google's official CLI for automating Lighthouse in CI |
| `treosh/lighthouse-ci-action` | v12 | GitHub Action wrapper for LHCI | Community standard, Lighthouse v12.6, 1s init, handles Chrome setup |
| `@axe-core/cli` | 4.11.x | axe-core command-line runner | Deque's official CLI, active (not deprecated), WCAG 2.1 AA |
| CSS `print-color-adjust` | Baseline 2025+ | Preserve background colors in print | W3C standard property, supported in all modern browsers |
| CSS `break-inside` | Baseline | Prevent page breaks inside elements | Modern replacement for `page-break-inside` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `actions/upload-artifact` | v4 | Upload CI artifacts | Upload Lighthouse HTML reports + axe JSON results |
| `actions/setup-node` | v4 | Install Node.js in CI | Required for @lhci/cli and @axe-core/cli |
| `actions/setup-python` | v5 | Install Python in CI | Required to generate sample HTML report |
| `python3 -m http.server` | stdlib | Serve static HTML locally | Serve generated report for axe-core testing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `treosh/lighthouse-ci-action` | Raw `@lhci/cli` npm install | Action handles Chrome setup automatically, less config |
| `@axe-core/cli` | `pa11y-ci` with axe runner | axe-core/cli is simpler, aligns with prior STATE.md decision |
| `python3 -m http.server` | `staticDistDir` in Lighthouse CI | staticDistDir only works for Lighthouse; axe-core still needs a server |
| `break-inside: avoid` | `page-break-inside: avoid` | `break-inside` is the modern standard; include both for max compat |

**Installation (CI only -- no local deps):**
```bash
# In GitHub Actions workflow:
npm install -g @lhci/cli@0.15.x
npm install -g @axe-core/cli
```

## Architecture Patterns

### Recommended Project Structure
```
.github/
  workflows/
    release.yml          # Existing: build + release on tags
    accessibility.yml    # NEW: Lighthouse + axe-core on PRs
lighthouserc.js          # NEW: LHCI configuration (collect, assert, upload)
job_radar/
  report.py              # MODIFIED: expanded @media print block
tests/
  test_report.py         # MODIFIED: add print CSS tests
```

### Pattern 1: Print Stylesheet as Additive CSS Block
**What:** Expand the existing `@media print` block in report.py (line 417) with comprehensive print rules
**When to use:** Single-file HTML reports where all CSS is inline
**Example:**
```css
/* Source: MDN print-color-adjust docs + Bootstrap 5 print override pattern */
@media print {
  /* Hide interactive elements */
  .no-print,
  .copy-btn,
  .copy-all-btn,
  .dropdown,
  .shortcut-hint,
  .export-status-btn,
  .btn-check,
  #clear-filters,
  #export-csv-btn { display: none !important; }

  /* Preserve score colors (override Bootstrap stripping) */
  .tier-strong,
  .tier-rec,
  .tier-review,
  .tier-badge-strong,
  .tier-badge-rec,
  .tier-badge-review,
  .badge {
    print-color-adjust: exact !important;
    -webkit-print-color-adjust: exact !important;
  }

  /* Prevent job entries from splitting across pages */
  .card, .hero-job, tr {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  /* Clean up print layout */
  body { background: white !important; }
  .card { border: 1px solid #ddd !important; box-shadow: none !important; }
  .badge { border: 1px solid currentColor; }
}
```

### Pattern 2: Lighthouse CI Configuration File
**What:** `lighthouserc.js` at project root configuring collect, assert, and upload
**When to use:** Any project using `@lhci/cli` or `treosh/lighthouse-ci-action`
**Example:**
```javascript
// Source: Lighthouse CI configuration docs
module.exports = {
  ci: {
    collect: {
      numberOfRuns: 5,
      staticDistDir: './ci-report',
      settings: {
        chromeFlags: '--no-sandbox --disable-gpu',
        // Prevent clearing localStorage (needed for status hydration)
        disableStorageReset: true
      }
    },
    assert: {
      assertions: {
        'categories:accessibility': ['error', { minScore: 0.95 }]
      }
    },
    upload: {
      target: 'filesystem',
      outputDir: './lhci-results'
    }
  }
};
```

### Pattern 3: GitHub Actions Workflow with Dual Tools
**What:** Single workflow running both Lighthouse and axe-core on a generated HTML report
**When to use:** Projects needing both score-based and violation-based accessibility checks
**Example:**
```yaml
# Source: treosh/lighthouse-ci-action docs + axe-core/cli docs
name: Accessibility CI
on:
  pull_request:
    branches: [main]

jobs:
  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install project
        run: pip install -e .

      - name: Generate sample report
        run: python -c "from job_radar.report import ...; ..."

      - name: Lighthouse CI
        uses: treosh/lighthouse-ci-action@v12
        with:
          configPath: ./lighthouserc.js
          uploadArtifacts: true

      - name: Install axe-core CLI
        run: npm install -g @axe-core/cli

      - name: Start HTTP server
        run: python3 -m http.server 8080 --directory ./ci-report &

      - name: Run axe-core
        run: axe http://localhost:8080/report.html --tags wcag2a,wcag2aa,wcag21a,wcag21aa --exit --save axe-results.json --dir ./axe-results

      - name: Upload axe results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: axe-results
          path: ./axe-results/
```

### Anti-Patterns to Avoid
- **Testing file:// URLs:** axe-core and Lighthouse both need HTTP-served pages; file:// causes CORS issues and lacks localStorage support
- **Skipping `-webkit-print-color-adjust`:** Safari requires the prefixed version even though the unprefixed `print-color-adjust` is standard
- **Using `page-break-inside` alone:** Modern browsers prefer `break-inside`, but including both ensures maximum compatibility
- **Running fewer than 5 Lighthouse runs:** Scores can vary 5-10 points between runs; 5 runs with median gives stable results
- **Not using `--exit` with axe-core:** Without `--exit`, axe-core returns exit code 0 even with violations, making CI useless

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Lighthouse CI automation | Custom Puppeteer+Lighthouse script | `treosh/lighthouse-ci-action@v12` | Handles Chrome setup, artifact upload, score assertions, 1s init |
| WCAG violation scanning | Custom axe-core injection via Puppeteer | `@axe-core/cli` | Handles browser launch, rule configuration, JSON output, exit codes |
| HTTP server for CI | Custom Express/Flask server | `python3 -m http.server` | Zero dependencies, one-liner, stdlib |
| Print color preservation | JavaScript-based print formatting | CSS `print-color-adjust: exact` | Browser-native, no JS needed, works offline |
| Page break control | Manual page counting logic | CSS `break-inside: avoid` | Browser handles pagination automatically |

**Key insight:** Both the print stylesheet and CI tools are "configure, don't code" problems. The print work is ~30 lines of CSS rules added to an existing media query. The CI work is a workflow YAML + config file. No custom code is needed beyond generating a sample HTML report for the CI tests.

## Common Pitfalls

### Pitfall 1: Bootstrap 5 Strips Print Backgrounds
**What goes wrong:** Tier score colors (green/cyan/gray backgrounds) disappear when printing because Bootstrap's CSS sets `background: transparent !important` on elements in print
**Why it happens:** Bootstrap's print normalization intentionally strips backgrounds to save ink by default
**How to avoid:** Use `print-color-adjust: exact !important` AND `-webkit-print-color-adjust: exact !important` on all tier-colored elements, with higher specificity than Bootstrap's rules (use specific class selectors)
**Warning signs:** Score badges appear as plain text without colored backgrounds in print preview

### Pitfall 2: Lighthouse Score Flakiness
**What goes wrong:** CI fails intermittently because Lighthouse accessibility score drops to 0.93 on some runs
**Why it happens:** Lighthouse scores vary 5-10 points between runs due to resource loading timing and rendering differences
**How to avoid:** Use `numberOfRuns: 5` in lighthouserc.js; LHCI uses the median of all runs automatically
**Warning signs:** CI passes sometimes, fails other times with similar code changes

### Pitfall 3: axe-core Exits 0 on Violations
**What goes wrong:** CI pipeline passes even when WCAG violations exist
**Why it happens:** By default, `@axe-core/cli` returns exit code 0 regardless of violations found
**How to avoid:** Always use the `--exit` flag: `axe http://localhost:8080/report.html --exit`
**Warning signs:** Violations listed in output but workflow shows green check

### Pitfall 4: localStorage Not Available in CI
**What goes wrong:** Status hydration JavaScript throws errors because localStorage is not available or empty in CI headless Chrome
**Why it happens:** CI runs in a clean browser context with no stored state
**How to avoid:** The existing code already handles this gracefully (try/catch around localStorage access, falls back to empty object). Use `disableStorageReset: true` in Lighthouse config to preserve any state set during page load. The `hydrateApplicationStatus()` function tolerates empty localStorage.
**Warning signs:** Console errors about localStorage in CI logs

### Pitfall 5: DOMContentLoaded Timing for Dynamic Content
**What goes wrong:** Lighthouse/axe-core audits fire before status badges are rendered because they depend on DOMContentLoaded
**Why it happens:** `hydrateApplicationStatus()` and `initializeFilters()` run on DOMContentLoaded, which may complete after Lighthouse's initial scan
**How to avoid:** Use `--load-delay=2000` with axe-core to wait for DOM hydration. For Lighthouse, the `disableStorageReset: true` setting + natural DOMContentLoaded timing is sufficient since Lighthouse waits for the page to be interactive. Status badges are non-critical for accessibility scoring (they appear via JavaScript, but the base HTML is already accessible).
**Warning signs:** axe-core reports violations on elements that haven't been rendered yet

### Pitfall 6: Interactive Elements Visible in Print
**What goes wrong:** Copy buttons, status dropdowns, filter checkboxes, and keyboard hints appear in printed output
**Why it happens:** The existing `@media print` block only hides `.no-print` class, but many interactive elements don't have this class
**How to avoid:** Add specific selectors for `.copy-btn`, `.copy-all-btn`, `.dropdown`, `.shortcut-hint`, `.btn-check`, `#clear-filters`, `#export-csv-btn` to the print hide rules
**Warning signs:** Printed report shows clickable buttons and dropdown menus

### Pitfall 7: Hero Card Shadows in Print
**What goes wrong:** Box shadows render as weird artifacts or colored outlines in print output
**Why it happens:** `box-shadow` doesn't translate well to print media
**How to avoid:** Set `box-shadow: none !important` on `.hero-job` and `.card` in the print media query
**Warning signs:** Dark borders or smudges around hero cards in print preview

## Code Examples

### Print Stylesheet Enhancement (report.py)
```python
# Source: Verified via MDN docs + Bootstrap 5 print behavior
# Replace the existing @media print block (line 417-422 in report.py) with:

@media print {{
  /* Hide all interactive/navigation chrome */
  .no-print,
  .copy-btn,
  .copy-all-btn,
  .dropdown,
  .shortcut-hint,
  .export-status-btn,
  .btn-check + label,
  .btn-check,
  #clear-filters,
  #export-csv-btn,
  #filter-heading,
  [role="region"][aria-labelledby="filter-heading"] {{
    display: none !important;
  }}

  /* Override Bootstrap background stripping with higher specificity */
  .tier-strong,
  .tier-rec,
  .tier-review {{
    print-color-adjust: exact !important;
    -webkit-print-color-adjust: exact !important;
    background-color: var(--color-tier-strong-bg) !important; /* each uses own var */
  }}

  .tier-badge-strong,
  .tier-badge-rec,
  .tier-badge-review,
  .badge.bg-primary,
  .badge.bg-success,
  .badge.bg-danger,
  .badge.bg-warning {{
    print-color-adjust: exact !important;
    -webkit-print-color-adjust: exact !important;
  }}

  /* Prevent job entries from splitting across pages */
  .card,
  .hero-job,
  tr {{
    break-inside: avoid;
    page-break-inside: avoid;
  }}

  /* Remove shadows and simplify borders for print */
  body {{ background: white !important; }}
  .card {{ border: 1px solid #ddd !important; box-shadow: none !important; }}
  .hero-job {{ box-shadow: none !important; }}
  .badge {{ border: 1px solid currentColor; }}
}}
```

### lighthouserc.js Configuration
```javascript
// Source: Lighthouse CI docs (configuration.html)
module.exports = {
  ci: {
    collect: {
      numberOfRuns: 5,
      staticDistDir: './ci-report',
      settings: {
        chromeFlags: '--no-sandbox --disable-gpu',
        disableStorageReset: true
      }
    },
    assert: {
      assertions: {
        'categories:accessibility': ['error', { minScore: 0.95 }]
      }
    },
    upload: {
      target: 'filesystem',
      outputDir: './lhci-results'
    }
  }
};
```

### GitHub Actions Workflow (accessibility.yml)
```yaml
# Source: treosh/lighthouse-ci-action docs + axe-core/cli docs
name: Accessibility

on:
  pull_request:
    branches: [main]

jobs:
  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Python dependencies
        run: pip install -e .

      - name: Generate sample report
        run: |
          mkdir -p ci-report
          python -c "
          from job_radar.report import generate_report
          from job_radar.sources import JobResult
          # ... generate sample report to ci-report/
          "

      - name: Lighthouse CI
        uses: treosh/lighthouse-ci-action@v12
        with:
          configPath: ./lighthouserc.js
          uploadArtifacts: true

      - name: Install axe-core CLI
        run: npm install -g @axe-core/cli

      - name: Start local server
        run: python3 -m http.server 8080 --directory ./ci-report &

      - name: Wait for server
        run: sleep 2

      - name: Run axe-core WCAG audit
        run: |
          axe http://localhost:8080/index.html \
            --tags wcag2a,wcag2aa,wcag21a,wcag21aa \
            --exit \
            --save axe-results.json \
            --dir ./axe-results

      - name: Upload axe results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: axe-accessibility-results
          path: ./axe-results/
```

### Sample Report Generator Script (for CI)
```python
# Source: Existing test_report.py fixtures pattern
# Generate a minimal but realistic HTML report for CI testing
from job_radar.report import generate_report
from job_radar.sources import JobResult

profile = {
    "name": "CI Test User",
    "target_titles": ["Senior Developer"],
    "core_skills": ["Python", "FastAPI"],
    "level": "senior",
    "years_experience": 5,
    "location": "Remote",
    "arrangement": ["remote"],
}

scored_results = [
    {
        "job": JobResult(
            title="Senior Python Engineer",
            company="TestCorp",
            location="Remote",
            arrangement="remote",
            salary="$140k",
            date_posted="2026-01-01",
            description="Build Python services",
            url="https://example.com/job/1",
            source="Test",
            employment_type="Full-time",
        ),
        "score": {
            "overall": 4.2,
            "recommendation": "Strong match",
            "components": {
                "skill_match": {"ratio": "2/2", "matched_core": ["Python", "FastAPI"], "matched_secondary": []},
                "title_relevance": {"reason": "Match"},
                "seniority": {"reason": "Matches"},
                "response": {"likelihood": "High", "reason": "Good fit"},
            },
        },
        "is_new": True,
    },
    # ... include at least one job per tier (strong, rec, review)
]

result = generate_report(
    profile=profile,
    scored_results=scored_results,
    manual_urls=[],
    sources_searched=["Test"],
    from_date="2026-01-01",
    to_date="2026-01-02",
    output_dir="./ci-report",
)
```

### Python Tests for Print CSS (test_report.py)
```python
# Source: Existing test patterns in test_report.py
def test_html_report_print_hides_interactive_elements(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Print stylesheet hides copy buttons, dropdowns, and filter controls."""
    result = generate_report(...)
    html_content = Path(result["html"]).read_text()

    # Verify print media query hides interactive elements
    assert ".copy-btn" in html_content  # selector exists in print block
    assert ".dropdown" in html_content
    assert "display: none !important" in html_content

def test_html_report_print_color_adjust(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Print stylesheet preserves tier score colors."""
    result = generate_report(...)
    html_content = Path(result["html"]).read_text()

    assert "print-color-adjust: exact" in html_content
    assert "-webkit-print-color-adjust: exact" in html_content

def test_html_report_print_page_break_control(sample_profile, sample_scored_results, sample_manual_urls, tmp_path):
    """Print stylesheet prevents job entries from splitting across pages."""
    result = generate_report(...)
    html_content = Path(result["html"]).read_text()

    assert "break-inside: avoid" in html_content
    assert "page-break-inside: avoid" in html_content
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `page-break-inside: avoid` | `break-inside: avoid` (+ legacy fallback) | CSS Fragmentation Level 3 | Use both for max compat |
| `-webkit-print-color-adjust` only | `print-color-adjust: exact` (standard) | Baseline 2025 | Unprefixed now standard; still include `-webkit-` prefix |
| `axe-cli` (deprecated package) | `@axe-core/cli` (scoped package) | 2022 | Old `axe-cli` npm package is deprecated, use `@axe-core/cli` |
| Manual Lighthouse runs | `treosh/lighthouse-ci-action@v12` | v12 (Lighthouse 12.6) | Wraps @lhci/cli, handles Chrome, artifacts, 1s startup |
| Single Lighthouse run | 5 runs with median (numberOfRuns: 5) | Best practice | Eliminates score flakiness from single-run variability |

**Deprecated/outdated:**
- `axe-cli` npm package: Deprecated, replaced by `@axe-core/cli`
- `page-break-inside`: Legacy, replaced by `break-inside` (include both for compat)
- `treosh/lighthouse-ci-action@v9`: Older version, current is v12

## Open Questions

1. **Sample Report Generation in CI**
   - What we know: CI needs to generate a realistic HTML report to test. The test fixtures in `test_report.py` provide the pattern. The `generate_report()` function requires a `tracker.get_all_application_statuses()` call (imported inside `_generate_html_report`).
   - What's unclear: Whether the tracker module works cleanly in CI without a tracker.json file present. Need to verify the fallback behavior.
   - Recommendation: Check if `tracker.get_all_application_statuses()` returns `{}` gracefully when no tracker.json exists. If not, mock it or pre-create an empty file. The existing test fixtures already work with `generate_report()` in pytest, so this should be fine.

2. **axe-core Testing file:// vs HTTP**
   - What we know: `@axe-core/cli` works with HTTP URLs. It launches headless Chrome. The docs don't explicitly discuss `file://` protocol testing.
   - What's unclear: Whether `@axe-core/cli` supports `file://` URLs directly. Most references suggest using HTTP.
   - Recommendation: Use `python3 -m http.server` to serve the generated report. This is reliable and avoids potential `file://` CORS issues. A one-liner background process in the workflow.

3. **Lighthouse CI `staticDistDir` vs Explicit URL**
   - What we know: `staticDistDir` tells Lighthouse CI to spin up its own server and audit all HTML files in the directory. `url` lets you specify explicit URLs.
   - What's unclear: Whether `staticDistDir` auto-discovers HTML files in subdirectories or only the root. Also whether the HTML filename matters (it generates timestamped filenames like `jobs_2026-02-11_14-30.html`).
   - Recommendation: Use `staticDistDir` pointed at the CI output directory. If the timestamped filename causes issues, rename it to `index.html` in the CI script. Lighthouse CI hosts files locally on a random port and corrects URLs automatically.

## Sources

### Primary (HIGH confidence)
- [MDN: print-color-adjust](https://developer.mozilla.org/en-US/docs/Web/CSS/print-color-adjust) - Property values, syntax, browser support (Baseline 2025)
- [Lighthouse CI Configuration docs](https://googlechrome.github.io/lighthouse-ci/docs/configuration.html) - collect, assert, upload options
- [Lighthouse CI Getting Started](https://googlechrome.github.io/lighthouse-ci/docs/getting-started.html) - Setup guide
- [treosh/lighthouse-ci-action GitHub](https://github.com/treosh/lighthouse-ci-action) - v12 docs, workflow examples, staticDistDir, uploadArtifacts
- [@axe-core/cli README (GitHub)](https://github.com/dequelabs/axe-core-npm/blob/develop/packages/cli/README.md) - --exit, --tags, --save, Chrome flags
- [axe-core GitHub](https://github.com/dequelabs/axe-core) - WCAG coverage, rule types

### Secondary (MEDIUM confidence)
- [CSS-Tricks: print-color-adjust](https://css-tricks.com/almanac/properties/p/print-color-adjust/) - Usage patterns
- [Bootstrap #16420: Print background color](https://github.com/twbs/bootstrap/issues/16420) - Bootstrap print stripping behavior
- [web.dev: Lighthouse CI](https://web.dev/articles/lighthouse-ci) - Best practices for numberOfRuns and assertions
- [Can I Use: print-color-adjust](https://caniuse.com/css-color-adjust) - Browser support matrix

### Tertiary (LOW confidence)
- [Various Medium articles on Lighthouse CI + GitHub Actions](https://pradappandiyan.medium.com/setting-up-lighthouse-ci-from-scratch-with-github-actions-integration-1f7be5567e7f) - Community patterns
- [CivicActions: pa11y-ci with axe](https://accessibility.civicactions.com/posts/automated-accessibility-testing-leveraging-github-actions-and-pa11y-ci-with-axe) - Alternative approaches

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools verified via official docs and npm; versions confirmed
- Architecture: HIGH - Well-established patterns; existing codebase structure is clear
- Pitfalls: HIGH - Bootstrap print behavior and Lighthouse flakiness are well-documented issues
- Print CSS: HIGH - `print-color-adjust` is a standard CSS property documented by MDN (Baseline 2025)
- CI workflow: HIGH - treosh/lighthouse-ci-action v12 is mature; @axe-core/cli 4.11.x is actively maintained

**Research date:** 2026-02-11
**Valid until:** 2026-03-11 (stable domain, tools are mature)
