# Phase 9: Report Enhancement - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Enhance job search report output to automatically open in browser with improved formatting. Generate both HTML (for browser viewing) and Markdown (for text-based workflows). Focus on output/display experience for non-technical users - NOT changing what data is reported or adding new search features.

</domain>

<decisions>
## Implementation Decisions

### Report format
- **Dual output**: Generate both HTML and Markdown files for each search
- **Primary format**: HTML opens in browser (user-facing), Markdown saved alongside (for text/version control)
- **File naming**: Single files with timestamps: `jobs_YYYY-MM-DD_HH-MM.html` and `jobs_YYYY-MM-DD_HH-MM.md`
- **Generation approach**: Write HTML and Markdown separately from job data (no conversion step)

### Browser opening behavior
- **Auto-open trigger**: Only when jobs found (skip if zero matching jobs)
- **Failure handling**: Silent fallback - if browser fails to open, just print file path (non-critical)
- **Headless detection**: Detect headless/server/CI environments and skip browser opening automatically
- **User control**: Both CLI flag (`--no-open`) and config option (`auto_open_browser`) for disabling auto-open

### HTML styling and formatting
- **CSS framework**: Bootstrap 5 via CDN link (online use, smaller bundle)
- **Visual improvements** (all required):
  - Responsive layout (mobile-friendly)
  - Dark mode support (respect browser/system preference)
  - Print-friendly styles (clean printing without backgrounds)
  - Syntax highlighting for job descriptions (code snippets in job posts)

### User feedback and messaging
- **Display timing**: Show report save location AFTER generation (not before search)
- **Information shown**: All of these:
  - HTML file path
  - Markdown file path
  - Report statistics (e.g., "5 jobs found, 3 high matches")
  - Browser opening status (confirm opened or explain why not)
- **Message tone**: Friendly - brief success message + paths + stats, formatted nicely (not minimal, not excessive)
- **Error handling**: Report generation failures are critical - show error and exit with non-zero code

### Claude's Discretion
- Exact Bootstrap component choices (cards, tables, badges, etc.)
- Dark mode implementation approach (CSS variables, media queries)
- Print stylesheet specifics
- Syntax highlighting library choice and configuration
- Headless environment detection method
- Message formatting and color scheme

</decisions>

<specifics>
## Specific Ideas

- HTML should feel professional and modern (Bootstrap framework supports this)
- Reports need to work offline once opened (CDN will load when online, cached after)
- Non-technical users are the target - prioritize clarity over technical details in output
- Phase 8 established wizard flow - reports should feel consistent with that polished UX

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 09-report-enhancement*
*Context gathered: 2026-02-09*
