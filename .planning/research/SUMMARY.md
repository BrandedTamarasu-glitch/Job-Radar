# Project Research Summary

**Project:** Job Radar v2.1.0 - Source Expansion & Polish
**Domain:** Desktop job aggregation application
**Researched:** 2026-02-13
**Confidence:** HIGH

## Executive Summary

Job Radar v2.1.0 is a feature expansion milestone for an existing Python desktop application that aggregates job postings. The research reveals this is a well-architected layered pipeline system (interface → orchestration → processing → infrastructure) that successfully uses PyInstaller, CustomTkinter GUI, and established patterns for API rate limiting and caching. The core architecture is solid and can support the planned enhancements without major refactoring.

The recommended approach is to add job aggregator APIs (JSearch, SerpAPI Google Jobs, USAJobs, Jobicy) alongside user-configurable scoring weights and professional packaging (platform-native installers with GUI uninstall). The existing stack requires minimal additions: `serpapi` SDK for Google Jobs access, `dmgbuild` for macOS DMG creation, and `pynsist` for Windows installers. All other features leverage existing dependencies (`requests`, standard library modules) and established patterns already proven in the codebase.

The primary risks are: (1) schema migration without version bumping will cause KeyError crashes for existing users, (2) macOS code signing using `--deep` flag will create "damaged app" errors, and (3) GUI uninstall attempting to delete the running application binary will fail on Windows. These are all addressable with proper migration logic, correct signing procedures, and two-stage uninstall scripts. The research provides specific prevention strategies for each pitfall with concrete code examples.

## Key Findings

### Recommended Stack

The existing stack (Python 3.10+, PyInstaller, CustomTkinter, requests, pyrate-limiter) requires only targeted additions for v2.1.0. No major dependencies need replacement or major version upgrades.

**Core technologies:**
- `serpapi` (0.1.5+): Official Python SDK for SerpAPI Google Jobs access — returns structured JSON with 40+ data points per job, integrates with existing `requests` + `python-dotenv` pattern
- `dmgbuild` (1.6.7+): macOS DMG creation — actively maintained (Jan 2026 release), requires Python 3.10+ to match project requirements
- `pynsist` (2.8+): Windows NSIS installer creation — bundles Python runtime, better than manual PyInstaller + NSIS workflow
- Standard library modules: `json`, `subprocess`, `platform`, `shutil` for scoring config, uninstall, and OS detection — no new runtime dependencies

**What NOT to use:**
- `cx_Freeze` for MSI: Would require rewriting entire validated build pipeline; marginal startup improvements don't justify migration risk
- ZipRecruiter official API: No confirmed public API exists; third-party scrapers cost $50+/month (defer or use manual URL pattern)
- RapidAPI SDK/wrappers: Adds dependency for minimal benefit; `requests` handles standard HTTP headers natively

**Critical version note:** Python 3.10 reaches EOL October 2026. Project should plan migration to Python 3.11+ by Q4 2026.

### Expected Features

Research identifies clear feature priorities based on user expectations for job aggregators and desktop applications in 2026.

**Must have (table stakes):**
- Duplicate detection (50-80% of aggregator results are dupes) — users hate seeing same job 5+ times
- Source attribution ("via LinkedIn") — users need to know where job came from
- Rate limit handling — free API tiers have strict limits; app must handle 429 errors gracefully
- Platform-native installers — Windows users expect .exe wizard, Mac users expect .dmg, not raw zip files
- Uninstall without residue — desktop apps must clean up cache/logs/config on removal

**Should have (competitive advantage):**
- User-customizable scoring weights (6 sliders for skill_match, response, title, seniority, location, domain) — power users want control over prioritization
- Staffing firm penalty dial — user feedback: "want more direct company jobs" (current +4.5 boost is too high)
- Cross-source smart deduplication — when duplicates found, show "best" source (direct employer > LinkedIn > staffing firm)
- API cost transparency — show "15/100 daily searches used" so users understand limits

**Defer (v2+):**
- Fuzzy duplicate detection (Levenshtein distance) — catches 30% more dupes but high complexity (NLP algorithms)
- Additional aggregators beyond JSearch/SerpAPI — diminishing returns, wait for user demand
- Application tracking — different problem space, requires schema changes
- Auto-refresh background service — complex OS service registration, battery drain concerns

### Architecture Approach

Job Radar follows a proven layered pipeline architecture that cleanly separates concerns and supports the v2.1.0 enhancements without refactoring.

**Major components:**
1. **Interface Layer** (CLI entry, GUI window) — add Settings tab for uninstall button
2. **Orchestration Layer** (search pipeline coordinator: fetch → filter → score → track → report) — remains unchanged
3. **Processing Layer** (sources, scoring, tracker, report) — extend sources with aggregator_sources.py, modify scoring.py to read profile weights
4. **Infrastructure Layer** (HTTP cache, config loader, profile manager, API config, rate limits) — add API keys for new sources, bump profile schema to v2

**Integration pattern for new features:**
- Job aggregator APIs plug into existing sources.py pattern (reuse caching, rate limiting, threading)
- Configurable scoring extends profile.json schema with optional `scoring_weights` object (backward compatible with defaults)
- GUI uninstall adds new module (uninstall.py) with platform detection, doesn't touch core pipeline
- Platform installers are post-build step after PyInstaller (no spec file changes needed)

**Suggested build order:** Phase 1 (source expansion) → Phase 2 (configurable scoring) → Phase 3 (GUI uninstall) → Phase 4 (platform installers). This order reuses existing infrastructure first, then touches core profile/scoring coupling, then adds self-contained GUI feature, then addresses packaging last.

### Critical Pitfalls

Research identified 5 critical pitfalls that will break the release if not addressed. Each has concrete prevention strategies.

1. **Scoring weight migration without schema version bump** — Adding configurable weights to profile without bumping `CURRENT_SCHEMA_VERSION` from 1 to 2 causes KeyError crashes when scoring.py expects `profile["scoring_weights"]` but old profiles lack this key. Prevention: Bump to v2, add v1→v2 migration that sets default weights, update _template.json, test with old profiles.

2. **Rate limiter SQLite connection leaks** — Adding 4 new APIs creates 10 total SQLite connections that aren't closed on exit, causing "database is locked" errors. Worse, sources sharing backend API (e.g., JobAPI and JobAPI Premium both hit api.jobapi.com) create separate rate limit databases but hit same pool, burning quota twice as fast. Prevention: Add `atexit` handler to close connections, map sources to shared backend APIs, add dynamic rate limit configs.

3. **macOS code signing with --deep flag** — PyInstaller appends Python bytecode to executable; `--deep` signing breaks Mach-O format causing "app is damaged" errors. Prevention: Sign binaries inside-out (dependencies → executables → bundle), use `--options runtime` with entitlements, notarize with `notarytool`, test on clean macOS machine with Gatekeeper enabled.

4. **GUI uninstall deleting running app** — Windows locks error: "process cannot access file"; macOS allows deletion but leaves zombie process. Prevention: Two-stage uninstall (delete user data + create cleanup script → schedule script to run after exit → exit immediately), wait 2 seconds for process exit, delete app binary, delete cleanup script.

5. **GitHub Actions CI time explosion** — Adding DMG/MSI/DEB installers balloons CI from 15min to 45+ min, with macOS notarization waiting 5-10min for Apple servers. Prevention: Separate signing from building (build → upload unsigned → sign job downloads, signs, uploads), defer optional formats (MSI, DEB), add smoke test before signing to catch PyInstaller issues early.

## Implications for Roadmap

Based on research, the recommended phase structure follows dependency order and risk mitigation strategies.

### Phase 1: API Source Infrastructure
**Rationale:** Foundation work that all new sources depend on. Fixes rate limiter connection leaks and API backend mapping BEFORE adding actual APIs. Low risk because it enhances existing infrastructure without changing user-facing behavior.

**Delivers:**
- SQLite connection cleanup with `atexit` handler
- Shared rate limiters for sources using same backend API
- Dynamic rate limit configs from .env/config.json
- Better error messages for rate limit failures

**Addresses:**
- Pitfall #2 (rate limiter state corruption)
- Table stakes: rate limit handling

**Avoids:** Technical debt pattern of hardcoding rate limits, connection leak performance trap

### Phase 2: Job Aggregator APIs (JSearch, USAJobs)
**Rationale:** Delivers immediate user value (more job sources) by reusing the infrastructure from Phase 1. Start with 2 well-documented APIs (JSearch for LinkedIn/Indeed/Google Jobs, USAJobs for federal jobs) before adding others. This validates the infrastructure changes.

**Delivers:**
- `aggregator_sources.py` with fetch_jsearch() and fetch_usajobs()
- Integration with existing build_search_queries() and fetch_all() orchestration
- API key management in .env for RAPIDAPI_KEY, USAJOBS_API_KEY, USAJOBS_EMAIL
- Basic duplicate detection (exact match by job_id/URL)

**Addresses:**
- Must-have: source attribution (APIs return "via" field)
- Must-have: duplicate detection (50-80% of aggregator results)
- Should-have: API cost transparency (display quota usage)

**Uses:** serpapi SDK, requests library, existing cache.py and rate_limits.py patterns

### Phase 3: Configurable Scoring Architecture
**Rationale:** Requires careful profile schema migration (Pitfall #1). Do after sources are working to avoid conflating bugs. Touches core profile/scoring coupling which needs thorough validation.

**Delivers:**
- Profile schema v2 with optional `scoring_weights` object
- v1→v2 migration logic with default weights
- scoring.py refactored to accept weights parameter
- Backward compatibility: old profiles auto-migrate, new profiles have weights in _template.json

**Addresses:**
- Should-have: user-customizable scoring weights (power user request)
- Should-have: staffing firm penalty dial (depends on weight customization)
- Pitfall #1: schema migration without version bump

**Implements:** Profile manager schema versioning (already built), atomic write pattern (already built)

### Phase 4: GUI Scoring Configuration
**Rationale:** UI surface for Phase 3 backend. Can be done after backend is proven to work. Self-contained GUI work that doesn't affect CLI or core pipeline.

**Delivers:**
- Advanced Scoring section in profile form with 6 sliders (CTkSlider widgets)
- Real-time validation (weights sum to 1.0)
- Live preview of score changes on current results
- Reset to defaults button

**Addresses:**
- Should-have: user-customizable scoring weights (GUI completion)
- UX pitfall: no feedback on validation failure

**Uses:** Existing CustomTkinter widgets, profile_manager.py validation

### Phase 5: Additional API Sources (SerpAPI, Jobicy)
**Rationale:** Expand source coverage after core aggregator pattern validated. SerpAPI provides alternative to JSearch if rate limits problematic; Jobicy adds remote-specific jobs with no auth required.

**Delivers:**
- fetch_serpapi_google_jobs() with serpapi SDK
- fetch_jobicy() with requests (RSS/JSON API)
- Updated rate limit configs (SerpAPI: 100/month free, Jobicy: 1/hour recommended)

**Addresses:**
- Should-have: more source coverage
- Must-have: rate limit handling (Jobicy has usage guidelines)

**Defers:** ZipRecruiter (no public API), fuzzy duplicate detection (complex NLP)

### Phase 6: GUI Uninstall Feature
**Rationale:** Self-contained feature that doesn't affect core pipeline. Can be done in parallel with Phase 4/5. Requires platform-specific testing but low risk to existing functionality.

**Delivers:**
- Settings tab in main_window.py
- uninstall.py module with platform detection (subprocess, platform, shutil)
- Two-stage uninstall: delete data → schedule cleanup script → exit
- Confirmation dialog with exact paths that will be deleted
- Backup option (create .job-radar-backup.zip before deletion)

**Addresses:**
- Must-have: uninstall without residue
- Pitfall #4: GUI uninstall deleting running app

**Avoids:** Anti-pattern of hardcoding uninstall paths, blocking GUI thread, no confirmation

### Phase 7: Platform-Native Installers
**Rationale:** Build on working app (all features complete and tested). Needs CI/CD tooling setup and signing/notarization which has external dependencies (Apple servers, certificate procurement). macOS easiest, Windows medium, Linux defer.

**Delivers:**
- macOS: create-dmg script → .dmg file with Applications folder shortcut
- Windows: pynsist config → .exe NSIS installer with wizard
- CI: Separate build job from signing job for faster failures
- Smoke test before signing to catch PyInstaller issues early

**Addresses:**
- Must-have: platform-native installers (professional UX)
- Pitfall #3: macOS code signing with --deep
- Pitfall #5: GitHub Actions CI time explosion

**Defers:** Linux DEB/RPM (high complexity, .tar.gz acceptable), Windows code signing certificate ($400/year)

### Phase Ordering Rationale

- **Phase 1 before Phase 2:** Infrastructure fixes must be in place before adding APIs that depend on rate limiting and connection management
- **Phase 2 before Phase 3:** Validate source expansion works before touching core scoring logic; avoid conflating bugs across two major systems
- **Phase 3 before Phase 4:** Backend schema migration must be proven before adding GUI that reads/writes new schema
- **Phase 5 after Phase 2:** Additional sources use same pattern as initial sources; do after pattern validated
- **Phase 6 parallel with Phase 4/5:** Uninstall is self-contained, can proceed in parallel without dependencies
- **Phase 7 last:** Installers are packaging concern, don't block feature development; requires external dependencies (Apple notarization, certificate procurement)

**Dependency grouping:** Phases 1-2 are tightly coupled (infrastructure → usage). Phases 3-4 are tightly coupled (backend → frontend). Phases 5-7 are loosely coupled and can overlap.

**Pitfall avoidance:** This ordering directly addresses all 5 critical pitfalls by ensuring prerequisites are met before dependent work begins (schema migration before GUI, infrastructure before APIs, features before installers).

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 7 (Platform Installers):** macOS notarization process changes frequently, code signing certificate procurement varies by region, Windows SmartScreen bypass documentation for unsigned apps
- **Phase 2 (Job Aggregator APIs):** JSearch free tier limits not publicly documented (may hit quota faster than expected), USAJobs rate limits documented but need to verify actual enforcement

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (API Source Infrastructure):** SQLite cleanup, atexit handlers, connection pooling are well-documented Python patterns
- **Phase 3 (Configurable Scoring Architecture):** JSON schema migration already implemented for v0→v1, same pattern applies
- **Phase 4 (GUI Scoring Configuration):** CustomTkinter sliders and validation are straightforward GUI work with official docs
- **Phase 6 (GUI Uninstall):** Platform detection and subprocess cleanup are standard patterns covered in research

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official docs verified for serpapi, dmgbuild, pynsist; PyInstaller already in use; version compatibility confirmed |
| Features | HIGH | Table stakes derived from LinkUp research (duplicate problem), user feedback documented (staffing firm preference), competitor analysis clear |
| Architecture | HIGH | Existing codebase analysis shows layered pipeline with clean integration points; pattern reuse reduces risk |
| Pitfalls | HIGH | All critical pitfalls have concrete reproduction steps, prevention strategies, and recovery plans from official sources (PyInstaller wiki, Apple docs) |

**Overall confidence:** HIGH

The research is based on verified official sources (SerpAPI PyPI, PyInstaller wiki, Apple developer docs, USAJobs developer portal) and direct codebase analysis. The existing architecture provides proven patterns that new features can follow. The pitfalls identified are well-documented with specific prevention strategies.

### Gaps to Address

**During planning:**
- **JSearch rate limits:** Free tier documentation is sparse. Plan to add cost tracking and quota warnings early in Phase 2 to detect limits empirically.
- **macOS notarization timing:** Apple server response times vary (5-10min typical, but can timeout). Phase 7 should budget time for notarization retries and have fallback plan (ship unsigned ZIP if notarization repeatedly fails).
- **Windows SmartScreen:** Unsigned installer shows "Windows protected your PC" warning. Phase 7 needs user documentation on bypass procedure OR defer code signing certificate to v2.2.

**During implementation:**
- **Fuzzy duplicate detection algorithm tuning:** Research shows Levenshtein distance < 3 works for job titles, but threshold may need adjustment based on real data. Plan for A/B testing in Phase 5 if time allows, otherwise defer to v2.2.
- **Profile migration testing at scale:** Research covers v1→v2 migration logic, but needs validation with diverse real profiles (100+ skills, complex dealbreakers). Add property-based test in Phase 3.

**Long-term considerations:**
- **Python 3.10 EOL (Oct 2026):** Migration to Python 3.11+ should be planned for Q4 2026 before security patches end. Not blocking for v2.1.0 but needs roadmap attention.

## Sources

### Primary (HIGH confidence)
- [SerpAPI Python SDK - PyPI](https://pypi.org/project/serpapi/) — Package version, Google Jobs engine capabilities
- [USAJobs Developer Portal](https://developer.usajobs.gov/) — Official API authentication, rate limits, federal job data structure
- [PyInstaller macOS Code Signing Wiki](https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OSX-Code-Signing) — Correct signing procedure (no --deep), notarization steps
- [PyInstaller Issue #7937](https://github.com/pyinstaller/pyinstaller/issues/7937) — Signing failure modes, LINKEDIT segment explanation
- [dmgbuild PyPI](https://pypi.org/project/dmgbuild/) — Version 1.6.7 (Jan 2026 release), Python 3.10+ requirement
- [pynsist PyPI and docs](https://pynsist.readthedocs.io/) — Version 2.8, NSIS installer workflow

### Secondary (MEDIUM confidence)
- [JSearch API on RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) — API capabilities (500 results/query), free tier existence (exact limits unclear)
- [Jobicy Remote Jobs API GitHub](https://github.com/Jobicy/remote-jobs-api) — Usage guidelines (1/hour recommended), API parameters
- [LinkUp Duplicate Job Research](https://www.linkup.com/insights/blog/job-board-data-pollution-duplicate-jobs-part-2) — 15x increase in duplicates from programmatic ads
- [Textkernel Fuzzy Duplicate Detection](https://www.textkernel.com/learn-support/blog/online-job-postings-have-many-duplicates-but-how-can-you-detect-them-if-they-are-not-exact-copies-of-each-other/) — Levenshtein distance approach for title+company+location
- [Product School Weighted Scoring](https://productschool.com/blog/product-fundamentals/weighted-scoring-model) — User expectations for customizable weights in 2026 tools

### Tertiary (LOW confidence)
- [ZipRecruiter APIs on RapidAPI](https://rapidapi.com/collection/ziprecruiter-api) — Third-party options only, no confirmed official public API
- [PyInstaller vs cx_Freeze 2026 comparison](https://ahmedsyntax.com/2026-comparison-pyinstaller-vs-cx-freeze-vs-nui/) — Performance benchmarks (startup time differences)

---
*Research completed: 2026-02-13*
*Ready for roadmap: yes*
