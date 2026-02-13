# Architecture Research — v2.1.0 Source Expansion & Polish

**Domain:** Desktop job aggregator enhancement — adding new sources, configurable scoring, GUI uninstall, platform-native installers
**Researched:** 2026-02-13
**Confidence:** HIGH

## System Overview — Existing Architecture

Job Radar follows a **layered pipeline architecture** with these key characteristics:

```
┌─────────────────────────────────────────────────────────────┐
│                     INTERFACE LAYER                          │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ CLI Entry    │  │ GUI Window   │                         │
│  │ (search.py)  │  │ (main_window)│                         │
│  └──────┬───────┘  └──────┬───────┘                         │
├─────────┴──────────────────┴─────────────────────────────────┤
│                     ORCHESTRATION LAYER                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Search Pipeline Coordinator                  │    │
│  │  (fetch → filter → score → track → report)          │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                     PROCESSING LAYER                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Sources │  │ Scoring │  │ Tracker │  │ Report  │        │
│  │ (fetch) │  │ Engine  │  │ (dedup) │  │ (MD/TXT)│        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
├───────┴────────────┴────────────┴────────────┴──────────────┤
│                     INFRASTRUCTURE LAYER                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  HTTP    │  │  Config  │  │ Profile  │  │   API    │    │
│  │  Cache   │  │  Loader  │  │ Manager  │  │  Config  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Current Component Boundaries

| Component | Responsibility | Integration Points |
|-----------|----------------|-------------------|
| **sources.py** | Job source fetchers, URL generators, query builders | Uses cache.py, api_config.py, rate_limits.py, deduplication.py |
| **scoring.py** | 6-component weighted scoring engine | Uses staffing_firms.py, profile data |
| **tracker.py** | Cross-run deduplication, seen jobs tracking | JSON persistence at ~/.job-radar/tracker.json |
| **report.py** | Markdown/HTML report generation | Consumes scored results, manual URLs |
| **config.py** | CLI defaults persistence | JSON at ~/.job-radar/config.json |
| **profile_manager.py** | Profile I/O with atomic writes, validation | JSON at ~/.job-radar/profile.json |
| **api_config.py** | API key loading from .env | Uses python-dotenv |
| **rate_limits.py** | SQLite-backed rate limiter | Uses pyrate-limiter |
| **cache.py** | HTTP response caching (4hr TTL) | Filesystem cache |
| **gui/** | CustomTkinter GUI (profile form, search controls, progress) | Uses worker_thread.py for async search |

## Integration Points for v2.1.0 Features

### Feature 1: Job Aggregator APIs

**What it is:** Add free job aggregator APIs (JobApis, Arbeitnow, Remotive) to expand job source coverage beyond current scrapers and premium APIs.

**Where it plugs in:**
- **New file:** `job_radar/aggregator_sources.py` — follows same pattern as existing sources.py
- **Modified:** `sources.py` — add aggregator queries to build_search_queries(), add calls to fetch_all()
- **Modified:** `api_config.py` — add aggregator API keys to .env.example template
- **Modified:** `rate_limits.py` — add rate limit configs for new APIs (JobApis: 100/month free tier)

**Complexity:** Low — replicates existing API pattern (Adzuna/Authentic Jobs). Rate limiting, caching, error handling already built.

### Feature 2: New Free Job Boards (Scrapers)

**What it is:** Add scraper support for more free job boards beyond Dice/HN/RemoteOK/WWR.

**Where it plugs in:**
- **Modified:** `sources.py` — add new fetch_[source]() functions following existing pattern
- **Modified:** `sources.py` — add to build_search_queries() and fetch_all() orchestration
- **No new files needed** — existing scraper infrastructure handles it

**Complexity:** Medium — scraper stability depends on site structure. Sites using heavy JS (LinkedIn) require Selenium, increasing complexity. Recommend starting with static-HTML sites (Indeed, Glassdoor).

**Pitfall:** Cloudflare/bot detection (already encountered with WWR). Mitigation: graceful degradation (log warning, return empty list, continue pipeline).

### Feature 3: User-Configurable Staffing Firm Scoring

**What it is:** Allow users to customize staffing firm scoring weight (currently hardcoded +1.5 boost in _score_response_likelihood()).

**Where it integrates:**
- **Modified:** profile.json schema — add "scoring_config": {"staffing_firm_weight": 1.5} (optional field)
- **Modified:** scoring.py — read config from profile, apply dynamic weight
- **Modified:** gui/profile_form.py — add "Advanced Scoring" section with slider/input
- **Modified:** profile_manager.py — update CURRENT_SCHEMA_VERSION to 2, add migration logic

**Complexity:** Low — config plumbing already exists (profile → scoring), just needs UI surface.

**Schema migration:** Use profile_manager.py versioning system (bump to v2, add defaults on load).

### Feature 4: GUI Uninstall Button

**What it is:** Add "Uninstall Job Radar" button to GUI settings that runs platform-specific uninstall commands.

**Where it integrates:**
- **Modified:** gui/main_window.py — add "Settings" tab to tabview
- **New file:** job_radar/uninstall.py — platform detection, uninstall logic
- **Modified:** job-radar.spec — ensure uninstaller script is bundled (no changes needed, subprocess calls platform tools)

**Complexity:** Medium — platform detection straightforward, but proper uninstall requires:
- **macOS:** Remove .app from /Applications (requires admin privileges via osascript)
- **Windows:** Requires installer to create registry entries + uninstaller (Inno Setup handles this)
- **Linux:** Remove extracted dir from /opt or ~/.local (depends on install method)

**Critical pitfall:** Button only works if app was installed properly (not running from extracted zip). Need to detect install method and disable button if unsupported.

### Feature 5: Platform-Native Installers

**What it is:** Create DMG (macOS), MSI/EXE installer (Windows), DEB/RPM (Linux) instead of raw zip archives.

**Where it integrates:**
- **Modified:** .github/workflows/release.yml — add installer build steps after PyInstaller
- **New files:**
  - macos/create-dmg.sh — script to build DMG with create-dmg tool
  - windows/installer.iss — Inno Setup script for Windows installer
  - linux/build-deb.sh — dpkg-deb wrapper for Debian package
- **Modified:** job-radar.spec — no changes (PyInstaller output is input to installers)

**Complexity:** Medium-High
- **macOS:** Low complexity — create-dmg tool is straightforward, already have .app bundle
- **Windows:** Medium complexity — Inno Setup script is declarative, generates uninstaller automatically
- **Linux:** High complexity — DEB/RPM packaging has many rules, dependencies, post-install scripts. Recommend starting with AppImage (simpler).

**Recommended build order:** macOS DMG → Windows Inno Setup → Linux AppImage (skip DEB/RPM initially).

## Data Flow Changes

### Current Data Flow (Simplified)
```
Profile JSON → build_search_queries() → fetch_all() [4-6 threads]
    → deduplicate_cross_source()
    → score_job() [uses profile, staffing_firms.py]
    → filter (--new-only, --min-score)
    → generate_report() → Markdown file
```

### New Data Flow (v2.1.0)
```
Profile JSON [with scoring_config]
    → build_search_queries() [+aggregator APIs, +new scrapers]
    → fetch_all() [8-10 threads now]
        → fetch_jobapis() [new]
        → fetch_arbeitnow() [new]
        → fetch_remotive() [new]
        → [existing sources]
    → deduplicate_cross_source()
    → score_job() [reads scoring_config from profile]
    → filter (--new-only, --min-score)
    → generate_report() → Markdown file
    → [GUI uninstall button available in settings]

[CI/CD Pipeline]
PyInstaller build → [macOS: create-dmg] [Windows: Inno Setup] → Release artifacts
```

**Key change:** Profile now drives scoring behavior (not just job matching). This makes scoring_config first-class citizen, needs validation/migration support.

## Suggested Build Order

### Phase 1: Source Expansion (Low Risk, High Value)
1. **Job aggregator APIs** — add aggregator_sources.py, integrate with existing API pattern
2. **New scraper sources** — add to sources.py following Dice/RemoteOK pattern
3. **Testing** — verify deduplication handles new sources, check rate limits

**Rationale:** Reuses existing infrastructure (caching, rate limiting, threading), minimal architectural changes. Gets more job coverage quickly.

### Phase 2: Configurable Scoring (Medium Risk, High User Value)
4. **Profile schema v2** — add scoring_config field, update profile_manager.py validation
5. **Scoring engine updates** — read config, apply dynamic weights
6. **GUI scoring settings** — add sliders/toggles to profile_form.py
7. **Migration testing** — ensure v1 profiles upgrade cleanly

**Rationale:** Touches core profile/scoring coupling, needs careful validation. Do after sources are working to avoid conflating bugs.

### Phase 3: GUI Uninstall (Low Risk, Nice-to-Have)
8. **Uninstall module** — uninstall.py with platform detection
9. **Settings tab** — add to main_window.py
10. **Testing** — verify button is disabled when install type unsupported

**Rationale:** Self-contained feature, doesn't affect core pipeline. Can be done in parallel with Phase 2.

### Phase 4: Platform Installers (High Effort, External Dependencies)
11. **macOS DMG** — create-dmg script, update release.yml
12. **Windows Inno Setup** — installer.iss script, add choco install step to CI
13. **Linux AppImage** — defer DEB/RPM (high complexity, low adoption for CLI tools)

**Rationale:** Build on working app, needs CI/CD tooling setup. macOS is easiest (create-dmg), Windows medium (Inno Setup), Linux hardest (packaging rules). Do last to avoid blocking core features.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Mixing Scraper and API Concerns

**What people do:** Put API key logic in scraper functions, or scraper retry logic in API functions.

**Why it's wrong:** Makes sources.py harder to maintain. Scraper stability (parse errors, rate limits) is different from API stability (auth, quotas).

**Do this instead:** Keep aggregator_sources.py separate for API sources, use shared primitives (fetch_with_retry, check_rate_limit) but don't mix parsing logic.

### Anti-Pattern 2: Hardcoding Uninstall Paths

**What people do:** Assume standard install location, run rm -rf without checking if path exists or is correct.

**Why it's wrong:** User may have installed to custom location, or running from extracted zip. Deletes wrong app or fails silently.

**Do this instead:** Detect install method (check if running from .app bundle, from /Applications, from exe installer). Disable uninstall button if unsupported.

### Anti-Pattern 3: Blocking GUI Thread for Uninstall

**What people do:** Call subprocess.run() directly in button click handler.

**Why it's wrong:** GUI freezes during admin privilege prompts, no progress feedback, can't cancel.

**Do this instead:** Run uninstall in background thread (like search worker), show progress dialog, allow cancel.

### Anti-Pattern 4: Not Versioning Scoring Config Schema

**What people do:** Add scoring_config to profile without migration logic.

**Why it's wrong:** Old profiles crash on load when scoring.py expects the field.

**Do this instead:** Use profile_manager.py schema versioning (already built), add v1→v2 migration that adds defaults.

## New Module Structure

```
job_radar/
├── aggregator_sources.py     # NEW: JobApis, Arbeitnow, Remotive fetchers
├── uninstall.py               # NEW: Platform-specific uninstall logic
├── sources.py                 # MODIFIED: add new scrapers, integrate aggregators
├── scoring.py                 # MODIFIED: read scoring_config from profile
├── profile_manager.py         # MODIFIED: bump schema to v2, add migration
├── api_config.py              # MODIFIED: add aggregator API keys to template
├── rate_limits.py             # MODIFIED: add aggregator rate limit configs
├── gui/
│   ├── main_window.py         # MODIFIED: add Settings tab with uninstall button
│   └── profile_form.py        # MODIFIED: add Advanced Scoring section
└── ...

.github/workflows/
└── release.yml                # MODIFIED: add installer build steps

macos/
└── create-dmg.sh              # NEW: DMG builder script

windows/
└── installer.iss              # NEW: Inno Setup script

linux/
└── build-appimage.sh          # NEW: AppImage builder (defer DEB/RPM)
```

## Sources

**Job Aggregator APIs:**
- [Public APIs Jobs Category](https://publicapis.dev/category/jobs)
- [Best Jobs APIs 2026](https://publicapis.io/best/jobs)
- [Arbeitnow Job Board API](https://www.arbeitnow.com/blog/job-board-api)
- [JobApis GitHub](https://jobapis.github.io/)

**macOS Installers:**
- [create-dmg GitHub](https://github.com/sindresorhus/create-dmg)
- [How to create DMG installer](https://gist.github.com/jadeatucker/5382343)
- [Packaging PyQt5 apps with PyInstaller macOS](https://www.pythonguis.com/tutorials/packaging-pyqt5-applications-pyinstaller-macos-dmg/)

**Windows Installers:**
- [Inno Setup Official](https://jrsoftware.org/isinfo.php)
- [Creating Professional Installers with Inno Setup 2026](https://ahmedsyntax.com/creating-professional-installers-inno-setup/)
- [Create Installer with Inno Setup Tutorial](https://manaj.hashnode.dev/create-installer-of-python-program-for-windows-os-using-inno-setup)

**GUI Framework:**
- [CustomTkinter GitHub](https://github.com/TomSchimansky/CustomTkinter)
- [CustomTkinter Official Docs](https://customtkinter.tomschimansky.com/)

---

*Architecture research for: Job Radar v2.1.0 Source Expansion & Polish*
*Researched: 2026-02-13*
