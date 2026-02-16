# Project Research Summary

**Project:** Job Radar v2.2.0 - Auto-Update & hiring.cafe Integration
**Domain:** Desktop Application Auto-Update Infrastructure + Job Board Integration
**Researched:** 2026-02-15
**Confidence:** HIGH

## Executive Summary

This research covers two independent feature domains for Job Radar v2.2.0: auto-update infrastructure for desktop applications and integration with hiring.cafe as a new job source. The recommended approach leverages Job Radar's existing Python stack with minimal new dependencies—only `packaging>=26.0` is required for semantic version comparison, with optional `tqdm` for download progress UX. No external dependencies are needed for hiring.cafe integration; the existing requests + BeautifulSoup stack handles the unofficial API endpoints.

The auto-update implementation should prioritize user control over automation. Instead of silent installs (which introduce security risks with unsigned binaries and UAC/Gatekeeper complexity), the MVP should implement version checking with user-initiated downloads. GitHub Releases API provides the version manifest, Python stdlib handles downloads and installer launching, and existing CustomTkinter GUI shows notifications. This "progressive enhancement" approach validates user demand before investing in automated download workflows.

Critical risks center on platform-specific installer handling and unofficial API brittleness. macOS Gatekeeper requires notarization for downloaded DMGs (not just code signing), Windows NSIS installers need proper UAC elevation via `os.startfile()` rather than subprocess, and version comparison must use semantic versioning to avoid "1.10 < 1.9" bugs. For hiring.cafe, the unofficial API may change without notice, requiring graceful degradation, conservative rate limiting (start at 60 requests/hour), and robust salary/location parsing with fallback to raw text when structured extraction fails.

## Key Findings

### Recommended Stack

Job Radar's existing stack handles 95% of requirements with zero new dependencies. The only required addition is `packaging>=26.0` for PEP 440-compliant semantic version comparison—3x faster than alternatives and handles edge cases (pre-releases, epochs) that naive string comparison misses. Optional `tqdm>=4.67.3` provides download progress visualization with 60ns overhead.

**Core technologies:**
- **packaging 26.0**: Semantic version comparison for update detection—Python stdlib-adjacent (PyPA official), prevents "1.10 < 1.9" lexicographic comparison bugs
- **urllib.request (stdlib)**: Download installers from GitHub Releases with progress hooks—no extra dependencies needed
- **subprocess + platform (stdlib)**: Cross-platform installer launching—macOS `open`, Windows `start`, Linux `xdg-open`
- **requests (existing)**: GitHub Releases API calls and hiring.cafe POST requests with JSON payloads
- **pyrate-limiter (existing)**: Rate limiting for hiring.cafe using SQLiteBucket infrastructure
- **beautifulsoup4 (existing)**: Fallback if hiring.cafe API changes to HTML rendering

**Critical stack decision:** Avoid PyUpdater, Esky, and tufup libraries—all are either unmaintained, Python 2-only, or overkill for "download installer and launch" workflow. Python stdlib + requests handles everything with greater simplicity and maintainability.

### Expected Features

Auto-update and hiring.cafe have distinct feature expectations based on industry standards and competitor analysis.

**Must have (table stakes):**
- **Auto-update:** Launch-time version check, visual update notification with version number, "Remind me later" dismissal, manual update check in Settings, HTTPS-only downloads, release notes display
- **hiring.cafe:** Job title/company/location extraction, salary data extraction (hiring.cafe's key differentiator), remote/hybrid/onsite filtering, direct apply URLs, deduplication with existing 10 sources, rate limiting integration

**Should have (competitive):**
- **Auto-update:** Skip version option (persistent dismissal of specific versions), changelog preview before download, automated installer download with progress bar (after MVP validation)
- **hiring.cafe:** Engagement metrics display (viewed_count, applied_count, saved_count as social proof), pagination support for large result sets (API supports up to 1,000 jobs/request)

**Defer (v2+):**
- **Auto-update:** Update channels (stable/beta)—no beta program exists yet; differential updates—PyInstaller bundles not structured for this; staged rollouts—requires server infrastructure
- **hiring.cafe:** Geolocation-based map UI, education/company size filters (wait for user requests)

**Anti-features (commonly requested but problematic):**
- Silent auto-install: Security risk with unsigned binaries, bypasses user consent, requires elevated permissions
- Force update (no dismiss): User hostile, blocks app access, backfires with uninstalls
- Auto-update ON by default: Bandwidth concerns on metered connections, regression risk
- Scrape hiring.cafe HTML: Fragile to site changes, rate limiting risks, ethical concerns—use API endpoints instead

### Architecture Approach

Both features integrate cleanly into existing Job Radar architecture with minimal refactoring. Auto-update adds a new `updater.py` module and `UpdateBanner` widget that reuses the proven worker thread pattern from `SearchWorker`. hiring.cafe follows the existing source registry pattern—same function signature (`fetch_hiringcafe(query, location, verbose)`), returns `list[JobResult]`, integrates with existing rate limiting and deduplication.

**Major components:**

1. **updater.py module** — Version checking (GitHub Releases API), installer download (urllib with progress callbacks), platform-specific launching (subprocess + platform detection)

2. **UpdateBanner GUI widget** — Non-blocking notification between header and tabs, dismissible per session, Download/Remind Later buttons, progress bar during download using queue-based messaging

3. **DownloadWorker thread** — Background installer download following existing `SearchWorker` pattern, cooperative cancellation via threading.Event, queue-based progress updates to avoid GUI thread blocking

4. **hiring.cafe source** — New `fetch_hiringcafe()` function in sources.py, structured salary fields (min/max/currency), rate limiting via existing SQLiteBucket, mapper function for API response to JobResult schema

**Key patterns:**
- Threaded operations with queue messaging (prevent GUI blocking)
- Source registry with unified interface (hiring.cafe is another source)
- Graceful API failures (missing keys, rate limits return empty list, no crashes)

**Integration points:**
- Main window startup: Check for updates in background thread, show banner if available
- Settings tab: Manual "Check for Updates" button, optional API key for hiring.cafe if needed
- Rate limits: Add hiring.cafe configuration to existing RATE_LIMITS dict and BACKEND_API_MAP
- Deduplication: hiring.cafe jobs flow through existing rapidfuzz 85% threshold logic

### Critical Pitfalls

1. **Version comparison with string sorting** — Lexicographic comparison causes "1.10 < 1.9" bug, breaking update detection entirely. **Solution:** Use `packaging.version.Version` for all comparisons, test explicitly with 1.9 vs 1.10.

2. **macOS Gatekeeper quarantine blocks downloaded installers** — Downloaded DMGs receive `com.apple.quarantine` attribute, Gatekeeper blocks unsigned/unnotarized apps. Ad-hoc signing insufficient. **Solution:** Submit DMG to Apple notarization service in CI/CD, test with actual downloads (not local files), verify with `spctl --assess`.

3. **Race condition during app shutdown** — Download thread continues after main app exits, leaving partial installers or blocking shutdown. **Solution:** Cooperative cancellation with threading.Event, check flag per-chunk during streaming download, atexit handler to cleanup, atomic downloads to .tmp + rename on completion.

4. **Update loop from bad manifest or failed installs** — App re-downloads same version after failure, hits GitHub rate limits, notification won't dismiss. **Solution:** State machine tracking "pending_download", "downloaded", "user_dismissed", exponential backoff (1h → 6h → 24h), manifest validation with try/except, never retry on 4xx errors.

5. **Certificate validation failures behind corporate proxies** — SSL-intercepting proxies cause "certificate verify failed" errors, silent failures confuse users. **Solution:** Use system certs on Windows (Python 3.10+), provide `JOBRADAR_NO_SSL_VERIFY=1` escape hatch (documented as insecure), informative error messages, test with mitmproxy.

6. **Installer launch permissions on Windows (UAC)** — NSIS requires admin privileges, subprocess doesn't auto-elevate, silent installs write to wrong registry hive. **Solution:** Use `os.startfile()` on Windows (triggers UAC automatically), let user click through wizard (no silent installs), verify installer manifest has `RequestExecutionLevel admin`.

7. **hiring.cafe unofficial API brittleness** — HTML structure or API schema changes break parsing without warning. **Solution:** Validate required fields before parsing, graceful degradation (log warning, return empty list), monitor success rate per source, fallback selectors for HTML scraping if needed.

8. **Inconsistent salary data from hiring.cafe** — Different formats ("$100k-$120k", "$100000", "Competitive", null) break parsing and display. **Solution:** Regex patterns for common formats, normalize to standard range, handle null gracefully (display "Not specified"), log unparseable formats for iteration, test against real scraped data.

## Implications for Roadmap

Based on research, suggested phase structure prioritizes independence and risk mitigation:

### Phase 1: Auto-Update Infrastructure (Version Detection)
**Rationale:** Independent of hiring.cafe, establishes foundation, immediate user value. Version checking is low-risk and can be shipped quickly to validate demand.

**Delivers:** Launch-time version check against GitHub Releases API, update notification banner in GUI with version number and release date, "Download Now" button opens browser to GitHub Releases page (manual download), "Remind Me Later" dismissal, manual "Check for Updates" in Settings tab, last-checked timestamp caching (avoid redundant API calls).

**Addresses Features:**
- Must-have: Launch-time check, visual notification, "Remind me later", manual check, HTTPS downloads
- Stack: packaging.version for semantic comparison, requests for GitHub API, CustomTkinter for banner widget

**Avoids Pitfalls:**
- Version string comparison: Implement packaging.version from start, test 1.9 vs 1.10
- Update loop: State machine with user_dismissed tracking, exponential backoff on failures
- Certificate validation: Handle SSLError gracefully, show informative messages

**Research Flag:** Standard pattern—no additional research needed. GitHub Releases API is well-documented.

---

### Phase 2: Auto-Update Infrastructure (Automated Download)
**Rationale:** Builds on Phase 1 after validating user demand. If 80%+ users click "Download Now" immediately, automate the download step. More complex due to threading and platform differences.

**Delivers:** Automated installer download in background thread using urllib with progress callbacks, UpdateBanner shows download progress (percentage, transfer speed), DownloadWorker thread with cooperative cancellation, downloaded installer saved to temp directory with atomic rename, progress bar integration with CustomTkinter.

**Uses Stack:**
- urllib.request (stdlib) with reporthook for progress
- Optional tqdm for progress visualization
- threading.Event for cancellation
- tempfile for secure download location

**Avoids Pitfalls:**
- Race condition on shutdown: Cooperative cancellation, check flag per chunk, cleanup on exit
- Certificate failures: Test with mitmproxy, handle SSL errors gracefully
- GUI blocking: Worker thread pattern, queue-based messaging

**Research Flag:** Standard pattern—reuse existing SearchWorker threading approach.

---

### Phase 3: Auto-Update Infrastructure (Installer Launch)
**Rationale:** Depends on Phase 2, highest platform-specific complexity, requires careful security testing.

**Delivers:** Cross-platform installer launching (macOS `open`, Windows `os.startfile()`, Linux instructions), UAC elevation on Windows, Gatekeeper handling on macOS, downloaded installer verification (size, magic bytes), "Install Now" confirmation dialog after download completes, app exit after launching installer.

**Implements Architecture:**
- Platform detection via platform.system()
- subprocess for macOS/Linux
- os.startfile() for Windows (triggers UAC)
- Notarization verification for macOS

**Avoids Pitfalls:**
- Gatekeeper quarantine: Notarize DMG in CI/CD, test with actual downloads, verify spctl
- UAC elevation: Use os.startfile() not subprocess, test as non-admin user, no silent installs
- Installer verification: Check magic bytes (MZ for EXE, EDFE for Mach-O), verify size matches manifest

**Research Flag:** Needs deeper research—macOS notarization workflow, Windows code signing, NSIS installer manifest configuration.

---

### Phase 4: Auto-Update Polish
**Rationale:** After core functionality works, add UX improvements based on user feedback.

**Delivers:** "Skip this version" persistent dismissal, changelog preview in update dialog (fetch GitHub release notes via API), update check failure handling with retry button, configurable update frequency (Settings toggle).

**Addresses Features:**
- Should-have: Skip version option, changelog preview
- Deferred anti-features avoided: No forced updates, no auto-update by default, no silent installs

**Research Flag:** Standard pattern—no additional research needed.

---

### Phase 5: hiring.cafe Integration
**Rationale:** Independent of auto-update, can proceed in parallel. Deferred to allow auto-update validation first. Requires API research upfront.

**Delivers:** API endpoint integration using reverse-engineered endpoints from hiring-cafe-job-scraper, job fetching with title/company/location/arrangement/salary/URL extraction, structured salary parsing (min/max/currency fields), location parsing with remote/hybrid detection, rate limiting via pyrate-limiter SQLiteBucket (60 req/hour initial), deduplication with existing sources using rapidfuzz 85% threshold, pagination support (up to 1,000 jobs/request), graceful degradation if API unavailable.

**Uses Stack:**
- requests (existing) for POST API calls with JSON payload
- pyrate-limiter (existing) for conservative rate limiting
- BeautifulSoup (existing) as fallback if API changes to HTML
- Existing deduplication and scoring logic

**Avoids Pitfalls:**
- API brittleness: Validate required fields, log parsing failures, graceful fallback
- Salary inconsistency: Regex patterns for formats, handle null/unparseable, test against real data
- Location edge cases: Structured parsing with remote/hybrid detection, fallback to raw text
- Deduplication failures: Normalize titles before comparison, multi-field dedup (title+company+location)
- Rate limiting: Conservative 60/hour start, exponential backoff on 429, respect robots.txt

**Research Flag:** Needs phase-specific research—API endpoint URL, authentication method, exact field names, query parameters, rate limit policy. Execute `/gsd:research-phase` before implementation.

---

### Phase Ordering Rationale

**Auto-update phases (1-4) before hiring.cafe (5):**
- Auto-update has immediate user value (existing users want updates)
- Phases 1-2 are low-risk, well-documented patterns
- Phase 3 has highest complexity but is independent—can be tested in isolation
- hiring.cafe requires API research upfront and has higher brittleness risk
- Parallel development possible: one developer on auto-update, another researching hiring.cafe API

**Progressive auto-update approach (3 phases instead of 1):**
- Phase 1 validates demand with minimal investment (version check + manual download)
- Phase 2 adds automation only if users want it (avoid premature optimization)
- Phase 3 tackles platform-specific complexity after core proven
- Phased deployment reduces risk of shipping broken installer launch logic

**hiring.cafe as single phase:**
- All integration work is tightly coupled (can't ship partial API integration)
- API research happens upfront, implementation follows standard source pattern
- Deduplication, rate limiting, parsing are all needed for MVP

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 3 (Installer Launch):** macOS notarization workflow with CI/CD, Windows Authenticode signing, NSIS manifest configuration for UAC, Gatekeeper testing on clean macOS VMs
- **Phase 5 (hiring.cafe Integration):** API endpoint discovery (inspect network traffic or scraper source), authentication requirements (API key vs public), exact JSON field names, rate limit policy, test scraping 100 jobs for salary/location format analysis

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Version Detection):** GitHub Releases API well-documented, packaging.version standard, CustomTkinter banner is existing pattern
- **Phase 2 (Automated Download):** urllib with reporthook is stdlib pattern, threading.Event is existing pattern from SearchWorker
- **Phase 4 (Auto-Update Polish):** All UX improvements follow established GUI patterns, changelog fetch uses same GitHub API as version check

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations verified against official documentation (packaging, urllib, GitHub API) or existing Job Radar codebase (pyrate-limiter, requests). No new external dependencies beyond packaging. |
| Features | MEDIUM-HIGH | Auto-update features verified with official Electron/desktop app docs (ToDesktop, electron-builder). hiring.cafe features extrapolated from scraper source code and competitor analysis (no official API docs). |
| Architecture | HIGH | Integration points map cleanly to existing Job Radar architecture. Threading pattern, source registry, rate limiting all proven. Platform-specific installer launch is standard subprocess pattern. |
| Pitfalls | MEDIUM | Auto-update pitfalls verified with documented issues (Electron, PyUpdater, Gatekeeper, UAC). hiring.cafe pitfalls extrapolated from general job scraping challenges and aggregator brittleness patterns. |

**Overall confidence:** HIGH

Research provides strong foundation for roadmap creation. Auto-update has clear implementation path with stdlib + GitHub Releases. hiring.cafe requires phase-specific API research but integration pattern is proven. Critical pitfalls are identified with concrete prevention strategies.

### Gaps to Address

**Auto-update gaps:**
- **macOS notarization workflow:** Research identified need but not exact CI/CD integration steps. Address during Phase 3 planning with Apple Developer documentation.
- **Windows code signing:** Ad-hoc signing insufficient for production, but Authenticode certificate acquisition process unclear. Address during Phase 3 with Windows Dev Center docs.
- **GitHub rate limit optimization:** 60 req/hour may be tight for high-usage scenarios. Consider adding optional GITHUB_TOKEN env var for 5,000/hour authenticated limit.

**hiring.cafe gaps:**
- **Exact API endpoint URL:** Scraper code references "official API" but URL not confirmed. Inspect hiring.cafe network traffic or scraper source code during Phase 5 research.
- **Authentication requirements:** Unknown if API key required or public endpoint. Test during Phase 5 research.
- **Field name mapping:** Scraper shows fields like `viewed_count`, `apply_url`, but exact JSON schema needs verification. Document during Phase 5 API testing.
- **Rate limit policy:** No official docs found. Start conservative (60/hour), monitor for 429 errors, adjust based on testing.
- **Salary format diversity:** Research shows inconsistent formats across aggregators. Collect 100 real hiring.cafe jobs during Phase 5 to build regex patterns.

**Mitigation strategies:**
- All gaps are "discover during implementation" rather than blockers
- Auto-update gaps are platform integration details, not architectural unknowns
- hiring.cafe gaps are API specifics that require hands-on testing
- Conservative defaults (manual download in Phase 1, 60 req/hour for hiring.cafe) allow shipping while gaps are resolved

## Sources

### Primary (HIGH confidence)
- **STACK.md** — Verified Python stdlib modules (urllib, subprocess, platform), packaging library PEP 440 compliance, GitHub Releases API structure, existing Job Radar stack analysis
- **FEATURES.md** — Auto-update feature expectations from Electron docs (ToDesktop, electron-builder), hiring.cafe data structure from scraper source code analysis
- **ARCHITECTURE.md** — Job Radar codebase patterns (worker_thread.py, sources.py, rate_limits.py), GitHub Releases integration approach
- **PITFALLS.md** — Documented issues from Electron auto-updater (GitHub issues #1488, #1625), macOS Gatekeeper docs, Windows UAC/NSIS documentation, hiring.cafe scraper brittleness patterns

### Secondary (MEDIUM confidence)
- GitHub Releases API documentation — Version manifest structure, asset download URLs, rate limits
- PyPA packaging library docs — Semantic versioning, PEP 440 compliance, version comparison performance
- macOS Gatekeeper security guide — Quarantine attributes, notarization requirements, spctl verification
- Windows NSIS UAC plug-in docs — Elevation manifest, registry hive behavior, silent install risks
- hiring.cafe scraper projects — Unofficial API endpoints, data structure (umur957/hiring-cafe-job-scraper, jinijinjaney/hiringcafe-job-scraper)

### Tertiary (LOW confidence)
- Community auto-update patterns — PyUpdater, Updater4pyi (both appear unmaintained)
- Job scraping best practices — ScrapingBee, Oxylabs guides (general patterns, not hiring.cafe-specific)
- Salary data reliability — Ravio blog on survey unreliability (validates need for robust parsing)

---
*Research completed: 2026-02-15*
*Ready for roadmap: yes*
