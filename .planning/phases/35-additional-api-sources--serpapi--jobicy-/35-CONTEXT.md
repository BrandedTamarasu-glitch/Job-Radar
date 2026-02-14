# Phase 35: Additional API Sources (SerpAPI, Jobicy) - Context

**Gathered:** 2026-02-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Add two new job API integrations: SerpAPI Google Jobs (alternative aggregator) and Jobicy (remote-focused job board). Include GUI quota tracking display for all rate-limited sources.

This phase adds these specific sources. Additional job boards are separate phases.

</domain>

<decisions>
## Implementation Decisions

### API Integration Approach
- Follow same pattern as JSearch/USAJobs for consistency
- Reuse existing API fetcher structure, rate limiter setup, response mapping
- Fail gracefully on API errors - continue search with other sources, show partial results
- Include "Test API" buttons for each source in GUI (like existing APIs)
- Optional dependencies - users choose which sources to enable (tiered approach continues)

### Quota/Rate Limit Display
- Display location: Settings tab with API keys (e.g., "JSearch: 15/100 searches today")
- Detail level: Simple count ("15/100 today") without progress bars or detailed breakdowns
- Update timing: Real-time after each search that uses the API
- Warning behavior: Visual warning (yellow/orange) when >80% used, auto-disable source when quota exhausted

### Source Configuration & Control
- Enable/disable: Checkboxes in Settings tab for each source
- CLI wizard: Prompt for SerpAPI and Jobicy keys during setup alongside other APIs
- Search order: SerpAPI and Jobicy come after other APIs (scrapers → primary APIs → these)
- Quota exhaustion: Show in-search notification ("SerpAPI quota exhausted, using other sources")

### Results Quality & Attribution
- Attribution: Simple source label ("via SerpAPI", "via Jobicy") like current "via LinkedIn" approach
- Scoring: All jobs scored equally regardless of source (no quality multipliers)
- Duplicate detection: Same as existing - exact URL/ID match deduplication
- Incomplete data: Skip jobs missing required fields (title, description) before scoring

### Claude's Discretion
- Exact API request/response structure for each source
- Rate limiter configuration specifics
- Error message wording
- Quota tracking implementation details

</decisions>

<specifics>
## Specific Ideas

- Quota display should update immediately after searches so users know their remaining quota
- Notification for quota exhaustion should be non-intrusive but visible during search progress
- Test buttons validate API keys work before user tries to search

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 35-additional-api-sources--serpapi--jobicy-*
*Context gathered: 2026-02-14*
