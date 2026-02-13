# Phase 32: Job Aggregator APIs (JSearch, USAJobs) - Context

**Gathered:** 2026-02-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Add JSearch (Google Jobs aggregator) and USAJobs (federal jobs) as automated sources. Users receive listings with original source attribution, deduplication across all sources, and API key configuration. Extends existing --setup-apis wizard and GUI settings. No new scoring changes (Phase 33-34). No SerpAPI/Jobicy (Phase 35).

</domain>

<decisions>
## Implementation Decisions

### Source Attribution Display
- Show original board name, not aggregator name — JSearch results appear as "LinkedIn", "Indeed", "Glassdoor" (individual sources, like native integrations)
- USAJobs results display as "USAJobs (Federal)"
- GUI per-source progress shows individual lines: "LinkedIn: 5 jobs", "Indeed: 7 jobs", "Glassdoor: 3 jobs" (even though JSearch is one API call, split results by origin for progress display)

### API Key Setup Flow
- Extend existing --setup-apis wizard to include JSearch and USAJobs alongside Adzuna/Authentic Jobs
- Validate API keys during setup by making a test API call — instant feedback that key works before saving
- Add API key configuration fields to the GUI (Settings section) so non-technical users never need the terminal
- When API keys aren't configured, show a suggestion: "Tip: Set up JSearch API key to search LinkedIn, Indeed, and Glassdoor" — always show, not just first run

### Dedup Behavior
- Use existing rapidfuzz fuzzy matching (85% similarity) — same dedup engine that works across Dice/HN/RemoteOK/WWR
- When duplicate found, original source wins over aggregator copy (Dice listing kept over JSearch copy of same job)
- Show multi-source badge on merged listings: "Found on 3 sources" — signals the job is widely posted
- Show dedup stats in both CLI progress output AND report summary (e.g., "12 duplicates removed across 4 sources")

### Search Query Mapping
- JSearch: Use first 4 profile titles (same pattern as Dice), each as separate query
- JSearch location: Match user's profile location_preference — remote if they prefer remote, city if they specified a city
- USAJobs: Search by titles + location (same pattern as other sources)
- USAJobs optional federal fields: Add GS grade range (min/max), preferred agencies list, and security clearance level (None/Secret/Top Secret) as optional profile fields
- Federal fields are optional — blank means no filtering on those parameters

### Claude's Discretion
- Exact JSearch API query parameter mapping (search_terms, location, date_posted, etc.)
- USAJobs API authentication header format
- How to split JSearch results into individual source buckets for progress display
- Error handling for API failures (timeout, 429, invalid key)
- Where federal profile fields appear in GUI form and CLI wizard

</decisions>

<specifics>
## Specific Ideas

- JSearch results should feel like the user has LinkedIn, Indeed, and Glassdoor as native sources — the aggregator layer should be invisible
- USAJobs "(Federal)" label helps users quickly identify government positions which have different application processes
- Multi-source badge gives confidence a job is real (not a ghost listing) when it appears across multiple boards

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 32-job-aggregator-apis*
*Context gathered: 2026-02-13*
