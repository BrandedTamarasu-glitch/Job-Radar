# Feature Research: v2.2.0 Auto-Update & hiring.cafe

**Domain:** Desktop Application Auto-Update & Job Board Integration
**Researched:** 2026-02-15
**Confidence:** MEDIUM

## Feature Landscape

This research covers two distinct feature domains for the Job Radar v2.2.0 milestone:
1. **Auto-update infrastructure** for desktop applications
2. **hiring.cafe integration** as a new job source

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

#### Auto-Update Features

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Launch-time version check | Industry standard for desktop apps; users expect to know about updates when they start the app | MEDIUM | Requires network call to GitHub Releases API, version comparison logic, and error handling for offline scenarios |
| Visual update notification | Silent checks are invisible; users need clear indication that an update exists | LOW | Dialog or banner with version number, release date, and action buttons |
| Download progress indicator | Users expect feedback during long-running operations; downloads can be 30-100MB | MEDIUM | Progress bar with percentage, transfer speed, and cancellation option |
| "Remind me later" option | Forced updates frustrate users; they need control over timing | LOW | Dismiss dialog without disabling future notifications |
| Manual update check | Users want to check for updates on demand, not just at launch | LOW | Menu item or Settings button that triggers version check |
| HTTPS-only downloads | Security baseline for 2026; unencrypted downloads are unacceptable | LOW | GitHub Releases serves over HTTPS by default |
| Release notes display | Users want to know what changed before downloading 50MB | LOW | Fetch and display CHANGELOG.md or release description from GitHub |

#### hiring.cafe Integration Features

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Job title, company, location extraction | Core job listing data; already expected for existing 10 sources | MEDIUM | Requires API endpoint discovery or HTML parsing; hiring.cafe has official API endpoints per scraper evidence |
| Salary data extraction | hiring.cafe's key differentiator is transparent salary info; users will expect Job Radar to surface this | MEDIUM | Salary parsing with min/max range extraction; format varies (hourly vs annual, USD vs other currencies) |
| Remote/hybrid/onsite filtering | Job Radar already filters by arrangement; users expect parity across sources | LOW | hiring.cafe supports this natively per search results |
| Direct apply URL | Job Radar generates "apply" links for all sources; table stakes | LOW | hiring.cafe provides `apply_url` field per scraper data structure |
| Deduplication with existing sources | Job Radar already does cross-source fuzzy dedup; users expect it to work with hiring.cafe | MEDIUM | Reuse existing rapidfuzz deduplication (85% threshold) from v1.2.0 |
| Rate limiting integration | Job Radar has SQLite-backed rate limiting for all API sources; users expect no crashes from API throttling | MEDIUM | Integrate with existing `rate_limits.py` and `.rate_limits/` SQLite database |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

#### Auto-Update Features

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Skip version option | Users can permanently dismiss a specific version if they have compatibility concerns or prefer current version | MEDIUM | Requires persistent storage of skipped versions; check against skip list during version check |
| Changelog preview before download | Informed decision-making; users see what's new before committing to 50MB download | MEDIUM | Fetch CHANGELOG.md or GitHub release notes via API; parse and display in readable format |
| Differential updates (NOT RECOMMENDED) | Reduces download size from 50MB to 5-10MB by downloading only changed files | HIGH | electron-updater supports this, but PyInstaller bundles are not structured for differential updates; would require major refactoring |
| Staged rollouts (NOT RECOMMENDED) | Gradual release to subset of users reduces impact of critical bugs | HIGH | Requires server-side infrastructure or complex manifest editing; overkill for single-developer open-source tool |
| Automatic background downloads | Download happens silently while user works; notify when ready to install | MEDIUM | Threading for background download; risk of consuming bandwidth without user consent |
| Update channels (stable/beta) | Power users can opt into beta releases for early access | MEDIUM | Requires separate release tags (v2.2.0 vs v2.2.0-beta.1) and channel selection in Settings |

#### hiring.cafe Integration Features

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Engagement metrics (views/applied/saved) | hiring.cafe tracks `viewed_count`, `applied_count`, `saved_count`, `hidden_count`; unique insight into job popularity | LOW | Exposed in API per scraper data structure; display in report as social proof |
| Pagination support for large result sets | hiring.cafe API supports pagination with page size up to 1,000 jobs per request | LOW | Implement pagination loop to fetch all results for broad searches |
| Education/company size filters | Scraper evidence shows these fields are available; Job Radar doesn't currently filter by these | MEDIUM | Extend search form with optional filters; integrate into hiring.cafe API query |
| Geolocation coordinates | hiring.cafe exposes lat/long for map-based visualization | HIGH | Would require map UI component; defer unless user requests geographic analysis |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Silent auto-install | "Just update automatically, I trust you" - users want zero-friction updates | **Security risk:** Silent installs bypass user review of changes; installer requires elevated permissions on macOS/Windows; user loses control. **UX risk:** Breaking changes or bugs surprise users mid-workflow. **Best practice violation:** [Desktop app best practices 2026](https://www.todesktop.com/features/auto-updates) emphasize user control | **Download + notify:** Download installer in background, show notification "Update ready. Restart to install" with "Install Now" button. User clicks through native installer wizard. |
| Force update (no dismiss) | Developers want to ensure users are on latest version for support purposes | **User hostile:** Blocks access to app until update completes; frustrating if user has urgent task. **Backfire risk:** User may uninstall entirely rather than wait for forced update. | **Persistent reminder:** Show notification on every launch until updated. For critical security patches, use prominent red banner instead of dismissible dialog. |
| Auto-update ON by default | "Most users want updates, make it opt-out" | **Bandwidth concerns:** Users on metered connections or slow internet don't want surprise 50MB downloads. **Regression risk:** Auto-updates can introduce bugs; users lose ability to stay on known-good version. **Trust issue:** First-run auto-update feels invasive for privacy-focused tool. | **Opt-in on first launch:** Wizard asks "Check for updates automatically?" with default to YES but user makes explicit choice. Manual "Check for updates" always available. |
| Multiple concurrent downloads | "Download all platform installers so user can share with friends" | **Storage waste:** Job Radar users only need one platform installer. 3 installers = 150MB+ wasted disk space. **Bandwidth waste:** Downloading unused installers consumes user's bandwidth quota. | **Single platform detection:** Auto-detect user's OS (macOS/Windows/Linux) and download only relevant installer. |
| Web-based updater UI | "Modern apps use web UI for rich update experience" | **Complexity:** Requires embedding web view or launching browser; breaks single-file portability. **Security:** Opens attack vector via web content injection. **Overkill:** Update notifications don't need rich UI; native dialogs are clearer. | **Native CustomTkinter dialog:** Reuse existing GUI framework for update notifications. Simple, secure, consistent with Job Radar's desktop-native philosophy. |
| Rollback to previous version | "What if update breaks something? Let user go back." | **Storage cost:** Requires keeping old versions on disk; 50MB per version adds up. **Complexity:** Version management, cleanup logic, testing matrix expands. **Low value:** Job Radar has 566 tests and careful release process; regression risk is low. If update breaks, users can download previous release from GitHub. | **GitHub Releases history:** All versions remain available at https://github.com/.../releases. Users can manually download and reinstall previous version if needed. Document this in FAQ. |
| Scrape hiring.cafe HTML | "Why use unofficial API? Just parse the website." | **Fragility:** Website HTML changes break scraper; hiring.cafe could restructure anytime. **Rate limiting:** Aggressive scraping gets IP banned. **Ethical:** hiring.cafe likely doesn't want bots; unofficial API is reverse-engineered but at least uses their endpoints. **Legal risk:** ToS may prohibit scraping. | **Use hiring.cafe API endpoints:** Scrapers on GitHub/Apify demonstrate official API exists. Use structured JSON endpoints, respect rate limits, and monitor for API changes. |
| Real-time hiring.cafe sync | "Check hiring.cafe every hour for new jobs" | **Bandwidth waste:** Job Radar is a batch daily search tool, not real-time monitoring. Polling hiring.cafe hourly consumes API quota unnecessarily. **UX mismatch:** Users don't want interruptions; they want one comprehensive report per day. | **Single search per run:** Include hiring.cafe in normal search workflow. User clicks "Run Search" once daily, gets all sources including hiring.cafe in one report. |

## Feature Dependencies

```
Auto-Update Flow:
[Launch-time version check]
    └──requires──> [GitHub Releases API integration]
    └──triggers──> [Update notification dialog]
                       ├──user clicks "Download"──> [Download progress indicator]
                       │                                └──on complete──> [Install notification]
                       ├──user clicks "Remind me later"──> [Dismiss, check again next launch]
                       └──user clicks "Skip this version"──> [Persistent skip list]

hiring.cafe Flow:
[API endpoint discovery]
    └──requires──> [Unofficial API documentation research]
    └──enables──> [Job fetching]
                      ├──requires──> [Rate limiting integration]
                      ├──requires──> [Salary parsing]
                      ├──requires──> [Location filtering]
                      └──feeds──> [Deduplication with existing sources]
                                     └──feeds──> [Scoring & report generation]
```

### Dependency Notes

- **Auto-update depends on GitHub Releases:** Job Radar already publishes releases to GitHub with DMG/NSIS installers. Auto-update reuses this infrastructure; no new hosting needed.
- **hiring.cafe requires unofficial API reverse-engineering:** No official public API documentation found. Must reverse-engineer endpoints from [hiring-cafe-job-scraper](https://github.com/umur957/hiring-cafe-job-scraper) and [Apify scrapers](https://apify.com/memo23/apify-hiring-cafe-scraper/api).
- **Salary parsing enhances scoring:** Job Radar's scoring weights include salary range matching. hiring.cafe's transparent salary data improves scoring accuracy.
- **Download progress conflicts with GUI thread blocking:** CustomTkinter GUI must use worker threads for downloads to avoid freezing UI. Job Radar already has `worker_thread.py` pattern from v2.0.0.
- **Skip version list conflicts with update channels:** If user skips v2.3.0 but wants v2.4.0, skip list must be version-specific, not binary on/off flag.

## MVP Definition for v2.2.0

### Launch With (v2.2.0)

Minimum viable auto-update and hiring.cafe integration.

**Auto-Update:**
- [ ] Launch-time version check against GitHub Releases API
- [ ] Update notification dialog (CustomTkinter) with version number, release date, and action buttons
- [ ] "Download Now" button opens browser to GitHub Releases page (user downloads manually)
- [ ] "Remind Me Later" button dismisses dialog; check again next launch
- [ ] Manual "Check for Updates" in Settings tab
- [ ] Store last-checked timestamp to avoid redundant API calls on rapid restarts

**Rationale:** This is the **simplest viable auto-update**. No download automation, no installer launching, no background threads. User sees notification, clicks through to GitHub, downloads installer, runs it. Familiar workflow (same as initial install), zero risk of silent installs or permission escalation bugs.

**hiring.cafe:**
- [ ] API endpoint integration using endpoints from [hiring-cafe-job-scraper](https://github.com/umur957/hiring-cafe-job-scraper)
- [ ] Extract job title, company, location, arrangement (remote/hybrid/onsite), salary, apply URL
- [ ] Salary parsing with min/max range extraction (annual and hourly formats)
- [ ] Location filtering (US states, remote)
- [ ] Rate limiting with SQLite integration (reuse existing `rate_limits.py`)
- [ ] Deduplication with existing 10 sources (reuse rapidfuzz 85% threshold)
- [ ] Pagination support (fetch up to 1,000 jobs per request, loop for more if needed)

**Rationale:** Brings hiring.cafe to parity with existing Job Radar sources. Salary data is key differentiator; must parse correctly. Rate limiting prevents bans. Deduplication avoids duplicate jobs from JSearch/Indeed overlap with hiring.cafe.

### Add After Validation (v2.3+)

Features to add once core is working.

**Auto-Update:**
- [ ] **Automated installer download** — Download DMG/NSIS/tar.gz in background using `requests` with progress callback; save to `~/Downloads/`. Show "Download complete. Open installer?" dialog.
  - **Trigger:** User feedback requests fewer clicks. If 80%+ users click "Download Now" within a week of notification, automate the download step.
- [ ] **Skip version option** — "Don't remind me about v2.3.0" checkbox in update dialog. Store skipped versions in `config.json`.
  - **Trigger:** User feedback about notification fatigue for minor updates they don't want.
- [ ] **Changelog preview in dialog** — Fetch GitHub release notes via API, display in scrollable text area below version info.
  - **Trigger:** User feedback asking "What's new?" before downloading.

**hiring.cafe:**
- [ ] **Engagement metrics display** — Show `viewed_count`, `applied_count`, `saved_count` in HTML report as badge next to job title ("500 applied").
  - **Trigger:** User feedback that this data would be useful for prioritization.
- [ ] **Education requirement filtering** — Add optional "Education" filter to search form; pass to hiring.cafe API.
  - **Trigger:** User feedback requesting education-based filtering (unlikely for Job Radar's audience of experienced developers).

### Future Consideration (v3+)

Features to defer until product-market fit is established.

**Auto-Update:**
- [ ] **Update channels (stable/beta)** — Opt into beta releases via Settings toggle.
  - **Why defer:** No beta program exists yet. Single-developer project doesn't have bandwidth for parallel release tracks.
- [ ] **Staged rollouts** — Release to 10% of users, monitor for crashes, then 100%.
  - **Why defer:** Requires server-side infrastructure or complex GitHub Releases manifest editing. Overkill for open-source tool with 566-test suite.
- [ ] **Differential updates** — Download only changed files instead of full installer.
  - **Why defer:** PyInstaller onedir bundles are not structured for differential updates. Would require switching to Electron (huge tech stack change) or custom update format.

**hiring.cafe:**
- [ ] **Geolocation-based search** — Map UI showing jobs by location.
  - **Why defer:** Job Radar is report-focused, not map-focused. Geographic analysis is out of scope.
- [ ] **hiring.cafe-specific filters** — Company size, industry, tech stack tags.
  - **Why defer:** Requires understanding hiring.cafe's full filter taxonomy. Wait for user requests for specific filters.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Launch-time version check | HIGH | MEDIUM | P1 |
| Update notification dialog | HIGH | LOW | P1 |
| "Remind me later" button | HIGH | LOW | P1 |
| Manual update check | MEDIUM | LOW | P1 |
| hiring.cafe job fetching | HIGH | MEDIUM | P1 |
| hiring.cafe salary extraction | HIGH | MEDIUM | P1 |
| hiring.cafe rate limiting | HIGH | MEDIUM | P1 |
| Automated installer download | MEDIUM | MEDIUM | P2 |
| Skip version option | MEDIUM | LOW | P2 |
| Changelog preview | MEDIUM | LOW | P2 |
| hiring.cafe engagement metrics | LOW | LOW | P2 |
| Update channels (beta) | LOW | HIGH | P3 |
| Staged rollouts | LOW | HIGH | P3 |
| Differential updates | MEDIUM | HIGH | P3 |
| Geolocation search | LOW | HIGH | P3 |

**Priority key:**
- **P1:** Must have for v2.2.0 launch (table stakes)
- **P2:** Should have, add when user feedback validates need
- **P3:** Nice to have, future consideration

## Competitor Feature Analysis

| Feature | VS Code Updates | Electron Apps (Slack, Discord) | Job Radar v2.2.0 |
|---------|----------------|-------------------------------|------------------|
| Launch-time check | Yes, every startup | Yes, background check every 4hrs | Yes, every startup |
| Auto-download | Yes, silent in background | Yes, silent in background | No (P2 future), user clicks to GitHub |
| Progress indicator | Yes, status bar | Yes, notification | Yes (P2 future), CustomTkinter progress bar |
| "Remind me later" | Yes | Yes | Yes |
| "Skip version" | No (auto-updates are forced) | No | Yes (P2 future) |
| Staged rollouts | Yes (Insiders ring) | Yes (via electron-updater) | No (P3, overkill) |
| Differential updates | Yes (reduces 50MB to 5MB) | Yes (electron-updater feature) | No (P3, PyInstaller limitation) |
| Update channels | Yes (Stable/Insiders) | Yes (Stable/Canary/PTB) | No (P3, single-dev project) |

**Our Approach:**
- **Start simpler than competitors:** "Click to download" workflow for v2.2.0. Competitors have dedicated teams and infrastructure for auto-updates; Job Radar is single-developer open-source.
- **Progressive enhancement:** If 80%+ users click "Download Now" immediately, automate it in v2.3. Let user behavior guide feature investment.
- **Platform-native installers already exist:** v2.1.0 ships DMG (macOS) and NSIS (Windows). Auto-update reuses this; no new build pipeline needed.

## Confidence Assessment

### Auto-Update Features: MEDIUM-HIGH Confidence

**HIGH confidence (verified with official docs):**
- [Launch-time version check patterns](https://www.electronjs.org/docs/latest/api/auto-updater) — Electron auto-updater checks on launch and every 10 minutes
- [Download progress UX](https://www.electron.build/auto-update.html) — `download-progress` event with bytesPerSecond, percent, total, transferred
- [GitHub Releases API structure](https://github.com/VioletGiraffe/github-releases-autoupdater) — Standard JSON with tag_name, assets[], browser_download_url

**MEDIUM confidence (verified with community sources):**
- Skip version behavior — [Android update patterns](https://forums.androidcentral.com/threads/can-i-skip-an-apps-update-on-an-app-with-auto-update-disabled.1056866/) and [Windows update skip](https://www.tenforums.com/windows-updates-activation/200189-how-disable-updates-available-popup.html) show user demand
- "Remind me later" as table stakes — [Desktop app best practices](https://www.todesktop.com/features/auto-updates) emphasize user control
- PyUpdater and Updater4pyi libraries — [PyUpdater](https://github.com/Digital-Sapphire/PyUpdater) and [Updater4pyi](https://updater4pyi.readthedocs.io/en/latest/quickstart/) exist but both appear unmaintained (last commit 2-3 years ago); rolling custom solution with `requests` + GitHub API is safer

**LOW confidence (need validation):**
- Update frequency (every launch vs every 4 hours vs daily) — Varies widely across apps; will A/B test based on user feedback
- Changelog format preferences — Don't know if users want full CHANGELOG.md or just bullet points; start with GitHub release description

### hiring.cafe Integration: MEDIUM Confidence

**MEDIUM confidence (verified with scraper source code):**
- [Job data structure](https://github.com/umur957/hiring-cafe-job-scraper) — `id`, `board_token`, `source`, `apply_url`, `title`, `description_clean`, `description_raw`, `viewed_count`, `applied_count`, `saved_count`, `hidden_count`
- [Pagination support](https://apify.com/memo23/apify-hiring-cafe-scraper/api) — "Automatically handles multiple pages of results" with page size up to 1,000 jobs per request
- [Unofficial API endpoints](https://github.com/umur957/hiring-cafe-job-scraper) — Scraper uses "hiring.cafe's official API endpoints" (not HTML scraping)

**LOW confidence (need validation):**
- **Rate limiting policy** — No official documentation found. Will implement conservative rate limiting (10 requests/minute) and monitor for 429 errors.
- **API stability** — Unofficial API; hiring.cafe could change endpoints anytime. Will add error handling and fallback to scraping if API breaks.
- **Salary format variations** — Scraper shows salary data exists, but format examples not in documentation. Will parse common patterns ($100k-$150k, $50/hr) and log unparseable formats for improvement.
- **Location filter parameters** — Assume standard filters (remote, US states) but need to test API to confirm parameter names and values.
- **Education/company size field reliability** — [Scraper docs](https://automatio.ai/templates/en/hiringcafe-web-scraper) mention these fields, but unclear if they're always populated. Will make them optional.

### Open Questions (Require Implementation Research)

1. **hiring.cafe API authentication** — Do endpoints require API key? Or open like RemoteOK? Scraper code will reveal.
2. **hiring.cafe request headers** — Does API check User-Agent? Scraper uses custom headers; may need to match.
3. **hiring.cafe job freshness** — Are jobs timestamped? Can we filter by date_posted to avoid re-processing old jobs?
4. **Installer download security** — Should we verify SHA256 checksum of downloaded installer? GitHub Releases doesn't auto-generate checksums; would need to add to release workflow.
5. **Update frequency configuration** — Should users be able to disable auto-check? Or just skip individual versions?

## Sources

### Auto-Update Research

**Official Documentation (HIGH confidence):**
- [Electron autoUpdater API](https://www.electronjs.org/docs/latest/api/auto-updater) — Update checking patterns
- [electron-builder Auto Update](https://www.electron.build/auto-update.html) — Download progress, notifications
- [Updating Applications | Electron](https://www.electronjs.org/docs/latest/tutorial/updates) — Update strategies
- [Updater4pyi Quickstart](https://updater4pyi.readthedocs.io/en/latest/quickstart/) — Python update library

**Community Resources (MEDIUM confidence):**
- [ToDesktop Auto-Updates Feature](https://www.todesktop.com/features/auto-updates) — Best practices
- [Auto-Updates in Electron Guide](https://www.emadibrahim.com/electron-guide/auto-updates) — UX patterns
- [PyUpdater GitHub](https://github.com/Digital-Sapphire/PyUpdater) — PyInstaller auto-update library (unmaintained)
- [GitHub Releases Auto-Updater (C++)](https://github.com/VioletGiraffe/github-releases-autoupdater) — Version checking patterns
- [Desktop App Update Best Practices | PDQ](https://www.pdq.com/blog/deploying-software-best-practices/) — Testing, rollout strategies
- [Code Signing Best Practices | DigiCert](https://www.digicert.com/faq/code-signing-trust/what-are-code-signing-best-practices) — Security considerations

**User Behavior Research (MEDIUM confidence):**
- [Skip version patterns | Android Central](https://forums.androidcentral.com/threads/can-i-skip-an-apps-update-on-an-app-with-auto-update-disabled.1056866/)
- [Windows update notification disable | TenForums](https://www.tenforums.com/windows-updates-activation/200189-how-disable-updates-available-popup.html)
- [Update cancellation | EaseUS](https://www.easeus.com/computer-instruction/how-to-stop-windows-10-update-in-progress.html)

### hiring.cafe Research

**Scraper Source Code (MEDIUM-HIGH confidence):**
- [hiring-cafe-job-scraper GitHub](https://github.com/umur957/hiring-cafe-job-scraper) — Python scraper using official API endpoints
- [Apify hiring.cafe Scraper API](https://apify.com/memo23/apify-hiring-cafe-scraper/api) — Pagination support, data structure
- [HiringCafe Web Scraper | Automatio.ai](https://automatio.ai/templates/en/hiringcafe-web-scraper) — Education, company size fields

**Platform Reviews (MEDIUM confidence):**
- [HiringCafe Review 2026 | Jobright](https://jobright.ai/blog/hiringcafe-review-2026-features-pros-cons-and-alternatives/) — Features, filters, pros/cons
- [HiringCafe: The Latest in Job Search | Bridged](https://www.getbridged.co/resource/hiringcafe-the-latest-in-job-search) — Overview, differentiators
- [Is HiringCafe Legit? | Remote100k](https://remote100k.com/blog/is-hiringcafe-legit) — Safety, legitimacy

---
*Feature research for: Job Radar v2.2.0 Auto-Update & hiring.cafe Integration*
*Researched: 2026-02-15*
*Confidence: MEDIUM — Auto-update patterns verified with official docs; hiring.cafe API reverse-engineered from scrapers (no official docs)*
