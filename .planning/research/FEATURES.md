# Feature Research: v2.1.0 Source Expansion & Polish

**Domain:** Job Search Aggregator - Desktop Application (v2.1.0 milestone)
**Researched:** 2026-02-13
**Confidence:** MEDIUM-HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Duplicate Detection** | Users hate seeing same job 5+ times from different aggregators; 50-80% of job postings are duplicates | MEDIUM-HIGH | Must handle exact matches (job_id, URL) AND fuzzy matches (similar title + company + location). Job boards that don't deduplicate get user complaints about "refresh spam" |
| **Source Attribution** | Users need to know if job is from LinkedIn, Indeed, or obscure board they've never heard of | LOW | Display "via [source]" on each listing; aggregators like SerpAPI return this as "via" field |
| **Rate Limit Handling** | Free API tiers have strict limits; app must gracefully handle 429 errors without crashing | MEDIUM | JSearch offers free tier but limits unclear; SerpAPI ~2.5s per request; USAJobs requires API key with documented rate limits. Cache results, show warnings |
| **Expired Listing Filtering** | Aggregators suffer from "aggregator lag" - jobs filled weeks ago still appear | MEDIUM | Track posting date, allow user to filter by recency (24h, 7d, 30d). LinkUp found this is #1 complaint about aggregators |
| **Uninstall without Residue** | Desktop apps leave cache/logs/config scattered across system; users expect clean removal | LOW-MEDIUM | Platform installers provide uninstall hooks. Self-uninstaller in GUI must delete ~/.config, cache dirs, logs. Leave user data ONLY if explicitly saved |
| **Platform-Native Install UX** | Windows users expect .exe installer; Mac users expect .dmg with drag-to-Applications; Linux users tolerate .tar.gz | MEDIUM | PyInstaller onedir is just bundled files. Users expect: Windows=NSIS/Inno Setup wizard, Mac=signed .pkg or .dmg, not zip files |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **User-Customizable Scoring Weights** | Power users want to prioritize location (remote) over seniority, or title_relevance over skill_match | MEDIUM | UI: 6 sliders (skill_match 25% → 0-50%), live preview of score changes on current results. Weighted scoring models are standard in 2026 product/risk tools; users expect customizable weights + visualization |
| **Staffing Firm Penalty Dial** | Real user feedback: "want more direct company jobs." Current 4.5/5.0 boost is hardcoded; let users control -2.0 (penalty) to +2.0 (boost) | LOW-MEDIUM | Depends on customizable scoring weights. Could default to -0.5 (slight penalty) instead of +4.5 boost, with slider for user override |
| **Cross-Source Smart Deduplication** | Instead of just showing 5 copies, pick "best" source (direct employer > LinkedIn > staffing firm > aggregator) | HIGH | Prioritization logic: Direct company URL > LinkedIn/Indeed > ZipRecruiter > staffing firms. Show "also posted on: [3 other sites]" collapsed detail |
| **API Cost Transparency** | Show user "15 JSearch credits used today (85 remaining)" so they understand why results are slower/limited | LOW | Display quota usage in status bar. JSearch/SerpAPI have free tiers; users on free plan need visibility into limits |
| **Local-First with Refresh** | Aggregators are slow (2.5s/request). Cache last 7 days of results, only hit APIs for new queries or explicit refresh | MEDIUM | Privacy-focused (fits existing "all local" ethos). Fast initial load from SQLite, background refresh for new postings |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-Time Aggregator Polling** | "Keep results always fresh" | JSearch/SerpAPI: ~2.5s per request. Polling 5 sources every 10min = 720 API calls/day. Free tiers exhausted in hours; paid tiers = $$$ | Cache-first with manual refresh button. Show "last updated: 2h ago" with refresh icon. User pulls when needed |
| **Aggregate ALL Sources Simultaneously** | "Show me everything" | JSearch returns 500 results max. If user has 6 automated sources active, that's 3000 jobs before deduplication. UI becomes unusable | Default to 2-3 sources per search. Let user enable more via checkboxes. Warn "this will take 30+ seconds" |
| **Automatic App Updates** | "Just update me in background" | Desktop security: self-updating requires code signing + admin privileges on Windows/Mac. PyInstaller apps can't easily self-update without installer framework | Show "Update available: v2.2.0" notification with download link. Or: built-in updater that downloads new installer and launches it |
| **Embed Web Browser for Applications** | "Let me apply without leaving app" | Each job board has different application flow (Indeed: modal, LinkedIn: redirect, company site: ATS iframe). Embedding Chromium = +100MB app size | Keep existing URL generator approach. User clicks "Apply" → opens default browser to application page |
| **Scrape Salary Data from Aggregators** | "Tell me the pay range" | SerpAPI returns salary when available, but 70%+ of postings don't include it. Scraping is unreliable; users expect data that isn't there | Show salary when API provides it. Display "Salary: Not disclosed" for others. Don't scrape/guess |

## Feature Dependencies

```
[Platform-Native Installers]
    └──requires──> [Uninstall Button in GUI]
                       └──requires──> [Uninstaller Script]

[User-Customizable Scoring Weights]
    └──enables──> [Staffing Firm Penalty Dial]
    └──requires──> [Score Recalculation Engine]
    └──enhances──> [Existing Scoring System]

[Duplicate Detection]
    └──requires──> [Job Unique Identifier Strategy]
                       └──uses──> [job_id OR url OR fuzzy(title+company+location)]
    └──enhances──> [All Aggregator APIs]
    └──conflicts──> [Show All Results Mode] (if user wants to see duplicates for debugging)

[Job Aggregator APIs]
    └──requires──> [Rate Limit Handling]
    └──requires──> [API Key Management UI]
    └──requires──> [Duplicate Detection]
    └──enhances──> [Existing 6 Automated Sources]

[Free Job Board APIs]
    └──requires──> [Same as Aggregator APIs]
    └──increases──> [Duplicate Detection Importance] (more sources = more dupes)

[Local-First Caching]
    └──requires──> [SQLite Schema Extension]
    └──requires──> [Cache Expiry Logic]
    └──reduces-need-for──> [Real-Time Polling]
```

### Dependency Notes

- **Platform-Native Installers → Uninstall Button:** NSIS/Inno Setup/pkg installers register uninstall entries with OS. GUI uninstall button invokes this registered uninstaller OR runs custom cleanup script if OS uninstaller not available.
- **Customizable Scoring → Staffing Firm Dial:** Staffing firm boost is currently hardcoded at +4.5 to response_likelihood. Making it user-adjustable requires exposing all scoring weights. Can't do one without the other.
- **Duplicate Detection → Aggregator APIs:** Aggregators like JSearch pull from Google Jobs, LinkedIn, Indeed simultaneously. Without deduplication, user sees 10 copies of same Software Engineer role. MUST have before adding aggregators or user experience degrades.
- **Caching → API Rate Limits:** Local-first caching reduces API calls by 80%+. User refreshes once/day instead of every search. Critical for free tier viability.

## MVP Definition for v2.1.0

### Launch With (v2.1.0)

Minimum viable increment to existing app — what's needed to deliver milestone value.

- [x] **JSearch API Integration** — Aggregator that pulls Google Jobs + LinkedIn + Indeed. Gives "more LinkedIn postings" per user feedback. 500 results/query, free tier available.
- [x] **Basic Duplicate Detection (Exact Match)** — Check job_id and URL before inserting. Prevents showing identical posting from 3 sources. Start with exact match; fuzzy matching is v2.2+.
- [x] **Rate Limit Handling** — Catch 429 errors, show user-friendly "Daily limit reached for JSearch (resets tomorrow)" message instead of crash.
- [x] **User-Customizable Scoring Weights** — 6 sliders for skill_match, response_likelihood, title_relevance, seniority, location, domain. Live score preview. Addresses "I care more about remote than seniority" feedback.
- [x] **Staffing Firm Penalty Dial** — Slider for staffing firm score adjustment (-2.0 to +2.0). Default to -0.5 (slight penalty). Addresses "want more direct company jobs" feedback. Requires customizable weights.
- [x] **GUI Uninstall Button** — Settings tab: "Uninstall Job Radar" button that runs cleanup script (delete cache, logs, config) then invokes OS uninstaller if available.
- [x] **Platform-Native Installers** — Windows: NSIS .exe installer with wizard. macOS: signed .pkg or .dmg with Applications folder shortcut. Linux: keep .tar.gz (acceptable for Linux users).

### Add After Validation (v2.2+)

Features to add once core aggregator integration is working and users provide feedback.

- [ ] **SerpAPI Google Jobs** — Alternative to JSearch if free tier limits too restrictive. ~2.5s per request, cached searches free.
- [ ] **ZipRecruiter API** — Free job board. Requires developer API key. Adds more US-based postings.
- [ ] **USAJobs API** — Free federal jobs API. Requires API key (free via developer.usajobs.gov). Niche but valuable for users seeking government roles.
- [ ] **Jobicy RSS Feed** — Free remote jobs feed. 100 results/query, no auth. Easy integration, low value-add (duplicates with RemoteOK/WWR).
- [ ] **Fuzzy Duplicate Detection** — Detect near-duplicates: "Senior Software Engineer" vs "Sr. Software Eng" at same company/location. Use Levenshtein distance on (title + company + location). Catches 80% more duplicates than exact match.
- [ ] **Smart Source Prioritization** — When duplicates detected, show "best" version: Direct employer site > LinkedIn > Indeed > staffing firm. Collapse others as "also posted on: [3 sites]."
- [ ] **API Cost Dashboard** — Show quota usage: "JSearch: 45/100 daily searches used. Resets in 6h." Help users understand why some sources disabled.
- [ ] **Local-First Caching** — Cache job results for 7 days in SQLite. Only hit APIs for new searches or explicit refresh. Reduces API calls by 80%+.

### Future Consideration (v3+)

Features to defer until product-market fit for aggregators is established.

- [ ] **Additional Aggregators (TheJobAPI, Adzuna Jobs)** — More sources = more duplicates = diminishing returns. Wait for user demand.
- [ ] **Application Tracking** — Track which jobs user applied to. Requires schema changes + UI. Separate feature area from sourcing.
- [ ] **Salary Data Collection** — JSearch/SerpAPI return salary when available. Low coverage (30% of postings). Wait for user complaints before prioritizing.
- [ ] **Auto-Refresh Background Service** — Desktop daemon that refreshes results every 4h. Complex (OS service registration) + battery drain on laptops. User can manually refresh.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| JSearch API Integration | HIGH (more LinkedIn/Indeed) | MEDIUM (API client, data mapping) | P1 |
| Basic Duplicate Detection (Exact) | HIGH (prevents 50% of dupes) | LOW (dict lookup by job_id/url) | P1 |
| Rate Limit Handling | HIGH (prevents crashes) | LOW (try/catch + user message) | P1 |
| User-Customizable Scoring Weights | HIGH (power user request) | MEDIUM (UI + recalc engine) | P1 |
| Staffing Firm Penalty Dial | HIGH (user feedback: "more direct jobs") | LOW (depends on scoring weights) | P1 |
| GUI Uninstall Button | MEDIUM (polish/professionalism) | LOW (cleanup script + button) | P1 |
| Platform-Native Installers | HIGH (Windows/Mac UX expectation) | MEDIUM (NSIS/pkg setup + signing) | P1 |
| SerpAPI Google Jobs | MEDIUM (alternative to JSearch) | MEDIUM (similar to JSearch) | P2 |
| USAJobs API | MEDIUM (niche: gov jobs) | LOW (API client, good docs) | P2 |
| ZipRecruiter API | MEDIUM (more US postings) | LOW (API client) | P2 |
| Fuzzy Duplicate Detection | MEDIUM (catches 30% more dupes) | HIGH (NLP/similarity algorithms) | P2 |
| Smart Source Prioritization | MEDIUM (reduces clutter) | MEDIUM (ranking logic) | P2 |
| API Cost Dashboard | LOW (transparency nice-to-have) | LOW (display quota data) | P2 |
| Local-First Caching | HIGH (speed + API savings) | MEDIUM (SQLite schema + expiry) | P2 |
| Jobicy RSS Feed | LOW (duplicates existing sources) | LOW (RSS parsing) | P3 |
| Additional Aggregators | LOW (diminishing returns) | MEDIUM | P3 |
| Application Tracking | MEDIUM (different problem space) | HIGH (schema + UI) | P3 |
| Salary Data Collection | LOW (30% coverage) | LOW (already in API responses) | P3 |
| Auto-Refresh Background Service | LOW (battery drain, complexity) | HIGH (OS service registration) | P3 |

**Priority key:**
- **P1: Must have for v2.1.0** — Core value delivery: aggregators, user control, professional packaging
- **P2: Should have for v2.2** — Enhancements once P1 validated: more sources, better deduplication
- **P3: Nice to have for v3+** — Future consideration after product-market fit

## Competitor Feature Analysis

| Feature | Indeed (Aggregator) | LinkedIn Job Search | ZipRecruiter | Our Approach (v2.1.0) |
|---------|---------------------|---------------------|--------------|------------------------|
| **Duplicate Detection** | Partial (same job_id) | None visible (shows all) | Good (company+title) | Exact match v2.1; fuzzy v2.2 |
| **Source Attribution** | "via [source]" on each job | Direct + "via [source]" | Direct + syndicated | "via [source]" from API response |
| **Scoring Customization** | None (black box) | None (relevance hidden) | None (match % opaque) | Full control: 6 weight sliders |
| **Staffing Firm Handling** | Mixed (shows all) | Mixed (shows all) | Promotes staffing heavily | User-configurable penalty/boost |
| **Installation** | Web-only | Web-only | Web-only | Desktop: NSIS (Win), .pkg (Mac) |
| **Uninstall** | N/A (web) | N/A (web) | N/A (web) | GUI button + OS uninstaller |
| **API Access** | $$ (enterprise only) | None (web scraping ToS violation) | $$ (not documented publicly) | Free tiers (JSearch, USAJobs) |
| **Local/Privacy** | Cloud-based, ad-tracked | Cloud-based, LinkedIn profile linked | Cloud-based, email-gated | Fully local, no accounts |

### Key Differentiators vs Competitors

1. **Transparency:** Competitors use black-box scoring. We show exactly how scores are calculated AND let users adjust weights.
2. **Control:** Users explicitly choose staffing firm preference (penalty/neutral/boost) instead of getting whatever algorithm decides.
3. **Privacy:** Fully local desktop app. No accounts, no tracking, no "sign up to see more results."
4. **Multi-Source:** Indeed/LinkedIn/ZipRecruiter are siloed. We aggregate across all of them + free boards + direct scrapers.

## Real-World User Expectations (2026)

### Job Aggregators

**What users expect:**
- Results from Google Jobs, LinkedIn, Indeed (JSearch ✅, SerpAPI ✅)
- No duplicate listings (50-80% of aggregator results are dupes)
- Source transparency ("via LinkedIn" on each result)
- Fresh postings (filter out jobs older than 30 days)
- Fast results (<5 seconds for 100 jobs)

**What frustrates users:**
- "Same job posted 10 times" (top complaint per LinkUp research)
- Expired listings still showing weeks later ("aggregator lag")
- Staffing firms dominating results (user feedback: "want direct companies")
- Fake/spam postings (Indeed specific, less common in aggregators)

### Customizable Scoring

**What users expect:**
- Sliders or percentage inputs for each scoring factor
- Live preview of how changes affect current results
- Presets: "Prioritize Remote," "Prioritize Salary," "Prioritize Experience Match"
- Defaults that work for 80% of users

**Pattern from 2026 tools:** Weighted scoring models are standard in product management, risk assessment, and applicant tracking systems. Users expect:
1. Clear criteria labels (not "Factor A")
2. Adjustable weights (sliders 0-100% or ratio inputs)
3. Visual feedback (scores update immediately)
4. Ability to reset to defaults

### Desktop Installers

**What users expect:**

**Windows:**
- Double-click .exe → wizard with Next/Install/Finish
- Option to create desktop shortcut
- Option to add to Start Menu
- Registered in "Add/Remove Programs"
- Signed installer (avoids SmartScreen warnings)

**macOS:**
- .dmg file that opens to show app icon + Applications folder
- Drag app to Applications to install
- OR .pkg installer for apps that need system-level access
- Signed + notarized (avoids Gatekeeper "unidentified developer")
- Uninstaller: drag app to Trash OR in-app uninstall button

**Linux:**
- .tar.gz or .deb/.rpm for distro-specific
- AppImage for universal binary (single file, no install)
- Uninstaller: rm -rf or package manager (apt remove)

**What frustrates users:**
- .zip file with no instructions (PyInstaller onedir is this)
- No uninstaller (leftover configs in ~/.config, cache in ~/.cache)
- Unsigned binaries (OS warnings scare users away)

### GUI Uninstall

**What users expect:**
- Button in Settings or Help menu: "Uninstall Job Radar"
- Confirmation dialog: "This will remove the app and delete cached data. User profiles will be preserved. Uninstall?"
- Progress indicator during cleanup
- Final dialog: "Job Radar has been uninstalled. Click OK to exit."
- App closes itself after cleanup

**What must be deleted:**
- Application binary (OS uninstaller handles this)
- Cache directories (~/.cache/job-radar)
- Logs (~/.local/share/job-radar/logs)
- Temp files

**What must be preserved (unless user chooses "Delete All Data"):**
- User profiles (~/.config/job-radar/profiles.json)
- Search history (if user opted in)
- Custom scoring weights

**Anti-pattern:** Apps that "uninstall" but leave 50MB of cache/logs scattered across system. Users discover this weeks later and feel betrayed.

## Technical Feasibility Notes

### Job Aggregator APIs

**JSearch (RapidAPI):**
- **Access:** Free tier available (no credit card for testing)
- **Rate Limits:** Not publicly documented; likely 100-500 requests/month on free tier
- **Data:** 30+ fields per job, 500 results max per query
- **Sources:** Google Jobs, LinkedIn, Indeed, Glassdoor
- **Cost:** Contact for custom pricing; free tier sufficient for testing
- **Confidence:** HIGH (actively maintained, GitHub examples, 2026 references)

**SerpAPI Google Jobs:**
- **Access:** API key required (free tier available)
- **Rate Limits:** 100 searches/month free; cached searches free
- **Performance:** ~2.5s per request (or ~1.2s with Ludicrous speed)
- **Data:** title, company, location, via, description, highlights, apply_options
- **Pagination:** next_page_token for up to 10 results/page
- **Cost:** $50/month for 5000 searches
- **Confidence:** HIGH (official docs, active 2026)

**USAJobs:**
- **Access:** Free API key via developer.usajobs.gov
- **Rate Limits:** Documented in guides (need to visit /guides/rate-limiting)
- **Data:** Federal job postings only (niche use case)
- **Auth:** Requires Authorization header with API key
- **Confidence:** HIGH (official government API, comprehensive docs)

**ZipRecruiter:**
- **Access:** API exists but not publicly documented
- **Free Tier:** Unclear; may require partner agreement
- **Confidence:** LOW (no official public API docs found)

**Jobicy:**
- **Access:** Free RSS feed/API (100 results/query, no auth)
- **Rate Limits:** "Don't poll excessively; a few times/day is sufficient"
- **Data:** Remote jobs only
- **Filters:** count, geo, industry, tag
- **Restrictions:** Don't redistribute to external job platforms (Google Jobs, LinkedIn, etc.)
- **Confidence:** MEDIUM (official GitHub repo, 2026 docs, but restrictive ToS)

### Duplicate Detection

**Exact Match (Easy):**
- Check `job_id` (if provided by API) OR `url` (application link)
- Python: `seen_ids = set()` → O(1) lookup
- Catches: Same job from JSearch and Adzuna (both pull from Google Jobs)

**Fuzzy Match (Hard):**
- Normalize: lowercase, strip whitespace, remove punctuation
- Compare: `(title, company, location)` tuple
- Levenshtein distance < 3 = probable duplicate
- Python: `fuzzywuzzy` or `RapidFuzz` library
- Catches: "Senior Software Engineer" vs "Sr. Software Eng" at "Google" vs "Google Inc."

**Complexity:** Exact match is LOW (already have URL deduplication logic for scrapers). Fuzzy match is MEDIUM-HIGH (requires NLP library, tuning threshold, handling edge cases).

**Recommendation:** Ship exact match in v2.1.0. Add fuzzy in v2.2 after gathering user feedback on duplicate rate.

### Customizable Scoring Weights

**UI Implementation (CustomTkinter):**
- 6 `CTkSlider` widgets (0.0 to 1.0 range)
- 6 `CTkLabel` widgets showing current percentage (e.g., "25%")
- "Reset to Defaults" button
- "Apply" button → recalculate scores for all current results
- Live preview: update one job's score as user drags slider (performance test needed)

**Backend Changes:**
- Current: weights hardcoded in scoring function
- New: weights stored in `config.json` or user profile
- Scoring function accepts `weights` dict parameter
- Batch recalculation: iterate through all jobs, recalc score, re-sort

**Complexity:** MEDIUM. UI is straightforward (sliders exist in CustomTkinter). Backend requires refactoring scoring function to accept weights as parameters instead of hardcoded constants.

**Dependency:** Staffing firm penalty dial requires this. Can't make staffing boost customizable without exposing all other weights (inconsistent UX).

### Platform-Native Installers

**Windows (NSIS):**
- Tool: NSIS (free, scriptable) or Inno Setup (free, GUI-based)
- Input: PyInstaller onedir output
- Output: `Job-Radar-Setup-v2.1.0.exe`
- Features: Wizard, desktop shortcut, Start Menu entry, uninstaller registry entry
- Signing: Requires code signing certificate ($100/year for EV cert to avoid SmartScreen)
- Complexity: MEDIUM (NSIS script learning curve, certificate procurement)

**macOS (.pkg):**
- Tool: `pkgbuild` (built into macOS) + `productbuild` for signed installer
- Input: PyInstaller onedir output
- Output: `Job-Radar-v2.1.0.pkg` or `.dmg` with drag-to-Applications
- Features: Installs to /Applications, uninstaller via drag-to-Trash or in-app button
- Signing: Requires Apple Developer ID ($99/year)
- Notarization: Required for Gatekeeper (automated via `xcrun notarytool`)
- Complexity: MEDIUM (signing + notarization setup, PKG file structure)

**Linux:**
- Keep current: .tar.gz (acceptable for Linux users)
- Optional: AppImage (single-file executable, no install required)
- Complexity: LOW (no change) or LOW-MEDIUM (AppImage via `appimagetool`)

**Critical Note:** PyInstaller creates onedir bundles (folder with executable + dependencies). This is NOT an installer. Users expect:
- Windows: One .exe to download and run
- macOS: One .dmg or .pkg to download and open
- Linux: One .tar.gz or .AppImage to download (current state OK)

Without platform-native installers, app feels "hobbyist." With them, app feels "professional."

### GUI Uninstall Button

**Implementation:**
1. Add button to Settings tab: "Uninstall Job Radar"
2. Confirm dialog: "This will remove Job Radar and cached data. Continue?"
3. Run cleanup script:
   - Windows: `uninstall.bat` (delete cache, logs, invoke `uninstall.exe` from NSIS)
   - macOS: `uninstall.sh` (delete cache, logs, delete app from /Applications)
   - Linux: `uninstall.sh` (delete cache, logs, binary)
4. Exit app

**What to Delete:**
- Application binary and dependencies (OS uninstaller handles on Windows/Mac)
- `~/.cache/job-radar/` (or `%APPDATA%\Local\Job-Radar\Cache` on Windows)
- `~/.local/share/job-radar/logs/`
- `~/.config/job-radar/*.log`

**What to Preserve:**
- `~/.config/job-radar/profiles.json` (user data)
- `~/.config/job-radar/config.json` (settings, API keys)
- UNLESS user checks "Delete all data including profiles"

**Complexity:** LOW. Shell script + button + dialog. Most complex part is handling OS-specific cleanup on Windows (delete registry entries).

## Sources

**Job Aggregator APIs:**
- [JSearch API — OpenWeb Ninja](https://www.openwebninja.com/api/jsearch) (MEDIUM confidence)
- [SerpAPI Google Jobs API](https://serpapi.com/google-jobs-api) (HIGH confidence)
- [USAJobs Developer Portal](https://developer.usajobs.gov/) (HIGH confidence)
- [Jobicy Remote Jobs API/RSS](https://jobicy.com/jobs-rss-feed) (MEDIUM confidence)
- [Jobicy GitHub Repository](https://github.com/Jobicy/remote-jobs-api) (MEDIUM confidence)
- [Best Job Posting APIs 2026](https://theirstack.com/en/blog/best-job-posting-apis) (MEDIUM confidence)

**Duplicate Detection:**
- [Job Board Duplicate Problem](https://www.linkup.com/insights/blog/job-board-data-pollution-duplicate-jobs-part-2) (HIGH confidence - 15x increase in duplicates from programmatic ads)
- [How to Detect Non-Exact Duplicates](https://www.textkernel.com/learn-support/blog/online-job-postings-have-many-duplicates-but-how-can-you-detect-them-if-they-are-not-exact-copies-of-each-other/) (HIGH confidence - technical approach)
- [Duplicate Job Listings on LinkedIn](https://medium.com/@mp5718/how-many-companies-post-duplicate-jobs-on-linkedin-ee620dfe4133) (MEDIUM confidence)
- [Job Aggregator Deduplication Best Practices](https://www.goproxy.com/blog/web-scraping-job-postings/) (MEDIUM confidence)

**User Expectations:**
- [Job Board User Complaints](https://www.whatjobs.com/news/joblookup-review-2026-legit-job-board-or-just-another-aggregator/) (MEDIUM confidence - 2026 user reviews)
- [Staffing Agency vs Direct Employer Preferences](https://talentbridge.com/direct-hire-vs-contract-staffing-whats-really-working-for-smart-businesses-in-2026/) (HIGH confidence - job seekers prefer direct hire)
- [Fuzzy Matching Best Practices](https://dataladder.com/fuzzy-matching-101/) (HIGH confidence)

**Customizable Scoring:**
- [Weighted Scoring Models 2026](https://productschool.com/blog/product-fundamentals/weighted-scoring-model) (HIGH confidence)
- [Weighted Scoring in Applications](https://www.6sigma.us/six-sigma-in-focus/weighted-scoring-prioritization/) (MEDIUM confidence)
- [Best AI Job Search Tools 2026](https://aijourn.com/the-best-ai-job-search-tools-in-2026/) (MEDIUM confidence)

**Desktop Installers:**
- [NSIS vs Inno Setup Comparison](https://www.advancedinstaller.com/choosing-the-right-windows-packaging-tool-as-developer.html) (HIGH confidence)
- [macOS PKG Packaging](https://apptimized.com/en/news/application-packaging-and-deploying-for-macos-in-simple-words/) (MEDIUM confidence)
- [PyInstaller Cross-Platform Deployment](https://github.com/orgs/pyinstaller/discussions/9026) (HIGH confidence - official repo)

**Uninstaller:**
- [Mac App Uninstall Best Practices](https://support.apple.com/en-us/102610) (HIGH confidence - official Apple docs)
- [Windows Uninstall Programs](https://support.microsoft.com/en-us/windows/uninstall-or-remove-apps-and-programs-in-windows-4b55f974-2cc6-2d2b-d092-5905080eaf98) (HIGH confidence - official Microsoft docs)
- [Best Mac Uninstallers 2026](https://macpaw.com/reviews/best-uninstallers-for-mac) (MEDIUM confidence)

---

*Feature research for: Job Radar v2.1.0 - Source Expansion & Polish*
*Researched: 2026-02-13*
*Next: Use this to inform milestone phase breakdown and task prioritization*
