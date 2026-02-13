# Requirements: Job Radar v2.1.0

**Defined:** 2026-02-13
**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters.

## v2.1.0 Requirements

Requirements for v2.1.0 Source Expansion & Polish. Each maps to roadmap phases.

### Source Expansion

- [ ] **SRC-01**: User can receive job results from JSearch (Google Jobs aggregator) covering LinkedIn, Indeed, Glassdoor, and company career pages
- [ ] **SRC-02**: User can receive job results from USAJobs federal job listings
- [ ] **SRC-03**: User can receive job results from SerpAPI Google Jobs as an alternative aggregator
- [ ] **SRC-04**: User can receive job results from Jobicy remote job listings
- [ ] **SRC-05**: User can see which original source each job came from (source attribution label)
- [ ] **SRC-06**: User sees deduplicated results across all sources (exact-match by URL/job ID)
- [ ] **SRC-07**: User can see API quota usage in the GUI (e.g., "15/100 daily searches used")
- [ ] **SRC-08**: User can configure API keys for new sources via `--setup-apis` wizard

### Scoring Configuration

- [ ] **SCORE-01**: User can adjust the 6 scoring component weights via GUI sliders
- [ ] **SCORE-02**: User can set staffing firm preference to boost, neutral, or penalize
- [ ] **SCORE-03**: Profile schema auto-migrates from v1 to v2 preserving all existing data
- [ ] **SCORE-04**: User can see live score preview when adjusting weights in the GUI
- [ ] **SCORE-05**: User can reset scoring weights to defaults with one click

### Uninstall & Packaging

- [ ] **PKG-01**: User can uninstall via GUI button that removes all app data (config, cache, rate limits)
- [ ] **PKG-02**: GUI uninstall shows confirmation dialog listing exact paths to be deleted
- [ ] **PKG-03**: User can create a backup of profile/config before uninstalling
- [ ] **PKG-04**: macOS users get a DMG installer with Applications folder drag-drop
- [ ] **PKG-05**: Windows users get an NSIS installer with setup wizard and Add/Remove Programs entry
- [ ] **PKG-06**: Uninstall works even while the app is running (two-stage cleanup)

### Infrastructure

- [ ] **INFRA-01**: Rate limiter connections are cleaned up on app exit (atexit handler)
- [ ] **INFRA-02**: Sources sharing the same backend API use shared rate limiters
- [ ] **INFRA-03**: Rate limit configs are loadable from config file (not hardcoded)

## Future Requirements

Deferred to v2.2+. Tracked but not in current roadmap.

### Enhanced Deduplication

- **DEDUP-01**: Fuzzy duplicate detection using Levenshtein distance for similar (non-exact) job listings
- **DEDUP-02**: Smart source selection showing "best" source when duplicates found (direct employer > aggregator > staffing)

### Additional Sources

- **SRC-09**: ZipRecruiter integration (pending public API availability)
- **SRC-10**: Additional job aggregator APIs beyond JSearch/SerpAPI

### Platform Packaging

- **PKG-07**: Linux DEB/RPM packages for package manager installation
- **PKG-08**: Windows code signing certificate for SmartScreen bypass
- **PKG-09**: macOS code signing certificate for Gatekeeper bypass

## Out of Scope

| Feature | Reason |
|---------|--------|
| LinkedIn/Indeed direct scraping | Both sites aggressively block automation; unreliable long-term |
| ZipRecruiter API | No confirmed public API; third-party scrapers cost $50+/month |
| Fuzzy duplicate detection | High complexity (NLP algorithms); defer after exact-match ships |
| Auto-refresh background service | Complex OS service registration, battery drain concerns |
| Linux native packaging (DEB/RPM) | High packaging complexity; tar.gz acceptable for Linux users |
| Live score recalculation on slider drag | Performance risk with thousands of jobs; use Apply button instead |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 31 | Pending |
| INFRA-02 | Phase 31 | Pending |
| INFRA-03 | Phase 31 | Pending |
| SRC-01 | Phase 32 | Pending |
| SRC-02 | Phase 32 | Pending |
| SRC-05 | Phase 32 | Pending |
| SRC-06 | Phase 32 | Pending |
| SRC-08 | Phase 32 | Pending |
| SCORE-03 | Phase 33 | Pending |
| SCORE-01 | Phase 34 | Pending |
| SCORE-02 | Phase 34 | Pending |
| SCORE-04 | Phase 34 | Pending |
| SCORE-05 | Phase 34 | Pending |
| SRC-03 | Phase 35 | Pending |
| SRC-04 | Phase 35 | Pending |
| SRC-07 | Phase 35 | Pending |
| PKG-01 | Phase 36 | Pending |
| PKG-02 | Phase 36 | Pending |
| PKG-03 | Phase 36 | Pending |
| PKG-06 | Phase 36 | Pending |
| PKG-04 | Phase 37 | Pending |
| PKG-05 | Phase 37 | Pending |

**Coverage:**
- v2.1.0 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-13*
*Last updated: 2026-02-13 after roadmap creation (100% coverage achieved)*
