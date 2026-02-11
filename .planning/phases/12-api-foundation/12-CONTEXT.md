# Phase 12: API Foundation - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Build secure infrastructure for API credential management and rate limiting. This phase creates the foundation that Phase 13 (Job Source APIs) will use to integrate Adzuna and Authentic Jobs. Scope is infrastructure only — no actual API integrations yet.

</domain>

<decisions>
## Implementation Decisions

### Credential Storage Pattern
- .env file lives in project root (next to job_radar.py)
- .env.example includes key names + signup URLs (e.g., ADZUNA_APP_ID= # Get from https://developer.adzuna.com)
- Missing API keys: Claude's discretion on silent skip vs warning (balance UX and transparency)
- .env loading timing: Claude's discretion on startup vs lazy loading (balance performance and error clarity)

### Rate Limiting Strategy
- Independent rate limits per source (Adzuna has its limit, Authentic Jobs has its own)
- When rate limit hit: Skip that source for current search, show results from other sources
- Rate limit configuration: Hardcoded per provider's official docs (not user-configurable)
- Rate limit state persists to disk (like tracker.json pattern) — remembers windows across runs

### Error Handling Approach
- .env syntax errors: Claude's discretion on fail-fast vs graceful degradation
- Invalid API key (401/403): Show error once in output, skip that source
- API key validation: Claude's discretion on upfront ping vs fail-on-first-request (balance startup time vs error clarity)
- Rate limit warnings include retry time: "Skipped Adzuna: rate limited, retry after 2:35pm"

### Developer Experience
- Include --setup-apis command (interactive setup for API keys)
- --setup-apis behavior: Create .env file with prompts, ask for each key, validate format, write .env
- Include --test-apis command to ping each API and report which keys work
- Rate limit debugging via --verbose flag (shows remaining quota, next reset time per source)

### Claude's Discretion
- .env loading strategy (startup vs lazy)
- Missing key behavior (silent skip vs warning)
- Syntax error handling (crash vs degrade)
- API key validation timing (upfront vs on-demand)
- Exact rate limit persistence format
- Progress indicator design during API setup

</decisions>

<specifics>
## Specific Ideas

- Rate limit state should work "like tracker.json" — persist across runs using similar pattern
- Error messages should be clear and actionable (tell user exactly what to fix)
- --verbose output should help debug rate limit issues without separate debug flag

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 12-api-foundation*
*Context gathered: 2026-02-10*
