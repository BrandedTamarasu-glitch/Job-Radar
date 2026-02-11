# Phase 14: Wellfound URLs - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate manual search URLs for Wellfound (formerly AngelList Talent) that users can click to browse startup jobs. This supplements automated sources (API integrations) with a manual browsing option, similar to existing Indeed/LinkedIn URL patterns. No scraping, no API integration — just smart URL generation.

</domain>

<decisions>
## Implementation Decisions

### URL Construction
- **Base URL pattern:** Research and decide (Claude investigates Wellfound's current URL structure during research phase)
- **Search filters:** Include job title/role (required), location, and remote filter
- **Special character handling:** URL encode everything using urllib.parse.quote (standard approach)
- **URL validation:** Test with HEAD request to verify URL returns 200, but don't let failures block output (recommended safety check)

### User Presentation
- **Placement:** Top of search results — show prominently before job listings: "Manual sources: Wellfound | Indeed | LinkedIn"
- **Terminal format:** Clickable URL with emoji: 🔗 Wellfound: https://wellfound.com/... (terminal auto-links if supported)
- **HTML format:** Bootstrap button/badge styled to match existing report aesthetic, with Wellfound logo/icon
- **Manual explanation:** Yes, include brief explanation like "(Manual - no public API)" in both terminal and HTML

### Query Mapping
- **Multiple target_titles:** Use first title only — take profile['target_titles'][0] for the Wellfound URL
- **Location mapping:** Use target_market as-is (e.g., "San Francisco, CA") — pass directly to URL without transformation
- **Remote detection:** Check target_market for 'Remote' (case-insensitive) — if found, add remote filter to URL
- **Core skills influence:** Research and decide — Claude investigates if Wellfound search benefits from including skills in query string

### Documentation and Guidance
- **Instructions style:** Usage tips — provide actionable guidance like "Create a free account to save searches and get alerts"
- **When to show:** Always show Wellfound URL in every search report alongside other manual sources (no conditional hiding)
- **Manual source grouping:** Yes, show all manual sources together (Wellfound | Indeed | LinkedIn) in unified presentation
- **Medium differences:** Claude decides best presentation per medium (terminal vs HTML) — likely more detailed in HTML with tooltips/expandable sections

### Claude's Discretion
- Exact Wellfound URL structure and parameter names (research phase will determine)
- Whether to include skills in query (research-informed decision)
- Terminal vs HTML documentation depth and formatting details
- Fallback behavior if HEAD request fails
- Exact wording of usage tips

</decisions>

<specifics>
## Specific Ideas

- Format similar to existing Indeed/LinkedIn pattern (if they exist in current codebase)
- Wellfound specializes in startup jobs, early-stage companies, equity-heavy roles
- Should integrate seamlessly with Phase 13 API sources (Adzuna, Authentic Jobs)
- Keep it simple — this is a URL generator, not a scraper

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope (URL generation for manual browsing).

</deferred>

---

*Phase: 14-wellfound-urls*
*Context gathered: 2026-02-10*
