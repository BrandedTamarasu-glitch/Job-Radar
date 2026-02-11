# Phase 13 Context: Job Source APIs

**Created:** 2026-02-10
**Phase Goal:** Users receive job listings from Adzuna and Authentic Jobs in their search results

This document captures implementation decisions from user discussion. It guides what the researcher investigates and what the planner implements.

---

## Decisions (LOCKED)

These choices are finalized. Researcher: investigate THESE approaches deeply. Planner: implement exactly as specified.

### Error Presentation

**API Failures (network, 500, timeout):**
- Silent skip - no terminal message shown to user
- Source is absent from results
- Logged for debugging only

**Rate Limiting:**
- Show rate limit notice to user
- Display format: "Skipped {source}: rate limited, retry after {time}"
- Time format: 12-hour with lowercase am/pm (e.g., "2:35pm")
- Don't wait or block - skip immediately

**Empty Results:**
- Merge silently - no special message
- Source contributed 0 jobs, results from other sources shown normally

**Total Failure:**
- Distinguish causes in error messages
- "All sources failed" (network/API errors) vs "All sources returned zero matches" (legitimate empty)
- Different messages for different failure modes

### Data Quality Handling

**Missing Required Fields:**
- Skip the job entirely - don't show jobs without title or company
- Log the invalid job for debugging
- Required fields: title, company, url (minimum to be useful)

**Text Cleanup:**
- Strip all HTML tags from descriptions
- Normalize whitespace (collapse multiple spaces/newlines to single spaces)
- Decode HTML entities

**Salary Data:**
- Store as-is with type flag (hourly/annual/range)
- Don't normalize to single format
- Scoring logic adapts per type
- New JobResult fields: salary_min, salary_max, salary_currency (optional)

**Deduplication:**
- Cross-source fuzzy matching
- Detect same job posted to multiple sources
- Match criteria: title + company + location similarity
- Not just source+job_id (would miss cross-source duplicates)

### Search Flow Integration

**Fetch Timing:**
- Scrapers first, then APIs (sequential)
- Run existing scrapers, wait for completion, then supplement with API data
- User sees initial scraper results faster

**Progress UI:**
- Single progress bar for all sources
- Generic message: "Fetching jobs from N sources..."
- Show percentage complete
- Less verbose than per-source status

**Result Streaming:**
- Wait for all sources to complete before showing results
- Collect all results, then score/rank once
- User sees complete picture, no partial results

**Credential Checking:**
- Lazy check during fetch (no upfront validation)
- Attempt API call, handle missing credentials as "source unavailable"
- Fail gracefully when credentials missing

### Field Mapping Strategy

**Mapping Strictness:**
- Strict validation - required fields must exist with valid data types
- Invalid jobs are skipped and logged
- No lenient defaults for required fields

**Location Normalization:**
- Parse to 'City, State' format
- Extract city and state/province from API responses
- Standardize to format like "San Francisco, CA"
- Handle 'Remote' as special case (pass through as-is)

**Schema Extension:**
- Extend JobResult dataclass with optional fields
- Add: salary_min (float), salary_max (float), salary_currency (str)
- Available for API sources, None for scraper sources
- Backward compatible with existing code

**Mapping Logic:**
- Per-source mapper functions
- Each API source has its own map_to_job_result() function
- Clear separation of concerns
- Easy to debug and maintain per-source

---

## Claude's Discretion

Areas where Claude can make implementation choices:

### Technical Implementation
- HTTP library choice (requests, httpx, aiohttp)
- Timeout values for API calls
- Retry logic for transient failures (how many retries, backoff strategy)
- Logging levels and verbosity
- Test coverage approach

### Architecture
- Module structure (one file per source, or shared utils)
- Where fuzzy matching logic lives (new module, extend existing)
- How to integrate with existing search.py fetch flow
- Error handling patterns and exception hierarchy

### Performance
- Whether to cache parsed/cleaned API responses
- Batch size for API requests (if pagination supported)
- Concurrency approach within API fetching (if applicable)

### Patterns
- How to structure per-source mapper functions (class-based, function-based)
- Validation approach (Pydantic, dataclasses, manual checks)
- Location parsing strategy (regex, split/strip, library)

---

## Deferred Ideas

Captured for future milestones - DO NOT implement in this phase:

### Future Enhancements
- Geocoding locations to lat/long for distance filtering
- Caching API responses with source-specific TTL (phase-specific, deferred to future)
- Salary filtering in UI (show only jobs above $X)
- Auto-retry rate-limited sources in background
- Parallel scraper + API fetching (chose sequential for v1.2)
- Pre-flight API key validation before search starts
- Streaming results as sources complete (chose wait-for-all)

---

## Research Guidance

**For gsd-phase-researcher:**

Focus research on:
1. **Cross-source fuzzy matching algorithms** - how to detect duplicates across APIs
   - String similarity libraries (fuzzywuzzy, rapidfuzz, difflib)
   - Matching thresholds for title/company/location
   - Performance implications of N×M comparisons
2. **Location parsing patterns** - extracting "City, State" from diverse formats
   - Common API location formats to handle
   - Edge cases: Remote, international, multi-location
   - Libraries vs regex approaches
3. **Adzuna API specifics** - salary data structure, pagination, response format
   - Actual field names and types
   - Rate limit headers (if any)
   - Error response formats
4. **Authentic Jobs API specifics** - response structure, job categories
   - Field names and data types
   - How design/creative roles are identified
   - Error response formats
5. **JobResult schema extension** - how to add optional fields to existing dataclass
   - Backward compatibility patterns
   - How existing code (scoring, tracking, reporting) handles new fields

Do NOT research:
- Alternative API sources beyond Adzuna and Authentic Jobs
- Async/concurrent execution patterns (sequential is decided)
- Caching strategies (deferred to future)
- Progress bar implementation details (generic pattern decided)

---

## Planning Guidance

**For gsd-planner:**

When creating PLAN.md files:
1. Honor ALL decisions in "Decisions (LOCKED)" section above
2. Use "Claude's Discretion" areas to make technical choices
3. Do NOT include "Deferred Ideas" in this phase
4. Create per-source mapper functions (one for Adzuna, one for Authentic Jobs)
5. Extend JobResult dataclass with optional salary fields
6. Implement cross-source fuzzy deduplication
7. Update search flow to run scrapers first, then APIs sequentially
8. Add single progress bar (not per-source status)
9. Implement strict validation with skip-invalid-jobs behavior
10. Parse locations to "City, State" format

Test coverage must verify:
- Missing required fields → job skipped
- HTML stripped from descriptions
- Cross-source deduplication works
- Rate limit notices shown correctly
- Silent skips for API failures/empty results
- Location parsing handles common formats
- Salary fields populated from Adzuna
- Sequential fetch order (scrapers then APIs)

---

## Acceptance Criteria

Phase 13 is complete when:
- [ ] Adzuna jobs appear in search results with title, company, location, URL, salary data
- [ ] Authentic Jobs listings appear in search results
- [ ] API failures skip silently (logged only)
- [ ] Rate limits show notice with retry time
- [ ] Cross-source fuzzy deduplication prevents duplicate jobs
- [ ] Locations normalized to "City, State" format
- [ ] Jobs with missing required fields are skipped
- [ ] HTML stripped from descriptions
- [ ] JobResult has optional salary_min, salary_max, salary_currency fields
- [ ] Scrapers run first, then APIs supplement results
- [ ] Single progress bar shown during fetching
- [ ] All sources complete before results displayed

---

*Generated from /gsd:discuss-phase 13*
