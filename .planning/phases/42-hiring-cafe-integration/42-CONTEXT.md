# Phase 42: hiring.cafe Integration - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Add hiring.cafe as an 11th job source. Fetch listings via their API, extract salary data, filter by location, deduplicate against existing sources, and handle failures gracefully. Jobs appear in search results and reports alongside the current 10 sources.

</domain>

<decisions>
## Implementation Decisions

### Search & filtering
- Use job titles from the user's profile as the search query to hiring.cafe
- Location filtering: use server-side filtering first (if API supports), then refine locally for edge cases
- Remote jobs always included regardless of location preference
- Request volume: match existing sources (~50-100 per query), not the full 1000 maximum

### Salary data handling
- Standardized range format: normalize to "$120K-$160K" annual range, consistent across sources
- Missing salary: show "Not listed" as explicit placeholder
- Salary included in scoring — jobs with salary in the user's desired range score higher
- Non-standard formats (hourly, monthly) converted to annual equivalent

### Deduplication strategy
- Title + Company exact match for dedup (same title AND same company = duplicate)
- When duplicate found, keep the listing with more data (salary, full description, more metadata)
- Dedup happens before scoring — remove duplicates first, score unique jobs only
- Source label ("hiring.cafe") shown in report — each job shows its source

### Failure & graceful degradation
- Silent skip on API failure — other 10 sources continue, no error message to user
- No retry — fail fast, one attempt only, move on to other sources
- Timeout: match existing source timeout values
- Malformed data: skip individual bad entries but keep good ones from same response

### Claude's Discretion
- Exact API endpoint discovery and query parameter mapping
- How to detect and handle hiring.cafe pagination
- Salary normalization formulas (hourly × 2080, monthly × 12, etc.)
- How to integrate into existing source pipeline (adapter pattern, etc.)
- Field mapping from hiring.cafe response to Job Radar schema
- Rate limiting implementation (60 req/hour per requirements)

</decisions>

<specifics>
## Specific Ideas

- Matching existing source volume (~50-100) keeps the experience consistent and avoids overwhelming the report
- Title + Company exact match is simple and reliable — avoids false positive dedup that would hide legitimate different jobs
- Keeping the listing with more data ensures users get the best information regardless of which source found it first
- Silent skip on failure is user-friendly — if one of 11 sources fails, the user still gets 10 sources of results

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 42-hiring-cafe-integration*
*Context gathered: 2026-02-16*
