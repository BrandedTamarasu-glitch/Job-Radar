# Roadmap: Job Radar

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2024-10-15)
- ✅ **v1.1 Desktop App** - Phases 5-11 (shipped 2024-11-20)
- ✅ **v1.2 API & Dedup** - Phases 12-18 (shipped 2024-12-10)
- ✅ **v1.3 Accessibility** - Phases 19-23 (shipped 2025-01-15)
- ✅ **v1.4 Polish** - Phases 24-27 (shipped 2025-01-30)
- ✅ **v1.5 Profile Management** - Phases 28-30 (shipped 2025-02-05)
- ✅ **v2.0 Desktop GUI** - Phases 31-33 (shipped 2025-12-15)
- ✅ **v2.1 Sources & Installers** - Phases 34-37 (shipped 2026-01-31)
- 🚧 **v2.2.0 Auto-Update & Source Expansion** - Phases 38-42 (in progress)

## Phases

<details>
<summary>✅ v1.0-v2.1 (Phases 1-37) - SHIPPED</summary>

Milestones v1.0 through v2.1 completed with 18 plans total across 37 phases.

Phase details available in git history.

</details>

### 🚧 v2.2.0 Auto-Update & Source Expansion (In Progress)

**Milestone Goal:** Enable automatic updates and expand job source coverage with hiring.cafe

#### Phase 38: Auto-Update Foundation (Version Detection)
**Goal**: Users can discover and manually download new versions via GitHub Releases
**Depends on**: Phase 37 (v2.1 shipped)
**Requirements**: UPDATE-01, UPDATE-02, UPDATE-03, UPDATE-04, UPDATE-05, UPDATE-14
**Success Criteria** (what must be TRUE):
  1. User sees update notification banner on launch when newer version available
  2. User can dismiss notification with "Remind Later" button (persists across restarts until new version)
  3. User can manually check for updates via Settings tab button
  4. User sees correct version comparison (1.10 > 1.9, not string sorting)
  5. User sees graceful error message when update check fails due to network issues
**Plans:** 2 plans

Plans:
- [x] 38-01-PLAN.md — TDD: UpdateChecker backend (version comparison, throttling, suppress tracking, GitHub API)
- [x] 38-02-PLAN.md — UpdateBanner widget, main_window integration, Settings Updates section

#### Phase 39: Auto-Update Download
**Goal**: Users can download installers automatically with visual progress feedback
**Depends on**: Phase 38
**Requirements**: UPDATE-06, UPDATE-10, UPDATE-13
**Success Criteria** (what must be TRUE):
  1. User can click "Download Now" button and installer downloads in background
  2. User sees download progress bar with percentage and transfer speed
  3. User can cancel download without app hanging or leaving partial files
  4. User sees retry option when download fails midway
  5. Downloaded installer appears in system temp directory and cleans up on app exit
**Plans:** 2 plans

Plans:
- [x] 39-01-PLAN.md — DownloadWorker backend, UpdateChecker asset fetching, platform detection, SHA256 verification
- [x] 39-02-PLAN.md — UpdateBanner multi-state transformation, confirmation dialog, MainWindow download lifecycle

#### Phase 40: Auto-Update Installation
**Goal**: Users can launch platform-specific installers securely from within app
**Depends on**: Phase 39
**Requirements**: UPDATE-07, UPDATE-08, UPDATE-09
**Success Criteria** (what must be TRUE):
  1. User can click "Install Now" after download completes and installer opens
  2. macOS user sees DMG open without Gatekeeper quarantine blocking it
  3. Windows user sees NSIS installer with UAC elevation prompt
  4. Linux user sees clear instructions to extract tar.gz manually
  5. User sees error message if installer fails integrity verification (SHA256 mismatch)
**Plans:** 2 plans

Plans:
- [x] 40-01-PLAN.md — Installer launch backend, dialogs (InstallConfirmDialog, LinuxInstallInstructionsDialog), cleanup
- [x] 40-02-PLAN.md — Wire install flow into UpdateBanner and MainWindow (confirmation, launch, exit, error handling)

#### Phase 41: Auto-Update Polish
**Goal**: Update experience feels polished with version skipping and changelog preview
**Depends on**: Phase 40
**Requirements**: UPDATE-11, UPDATE-12
**Success Criteria** (what must be TRUE):
  1. User can click "Skip This Version" and never sees notification for that version again
  2. User sees "What's new?" section in update dialog with changelog preview
  3. User sees formatted release notes from GitHub Releases API
  4. Skipped versions persist across app restarts in update state file
**Plans**: TBD

Plans:
- [ ] 41-01-PLAN.md: TBD

#### Phase 42: hiring.cafe Integration
**Goal**: Users receive job listings from hiring.cafe with salary data and location filtering
**Depends on**: Phase 37 (independent of auto-update phases)
**Requirements**: HIRE-01, HIRE-02, HIRE-03, HIRE-04, HIRE-05, HIRE-06, HIRE-07, HIRE-08, HIRE-09, HIRE-10
**Success Criteria** (what must be TRUE):
  1. User sees hiring.cafe jobs in search results alongside existing 10 sources
  2. User sees salary data extracted from hiring.cafe listings in report
  3. User sees hiring.cafe jobs filtered by their profile's location preferences
  4. User sees hiring.cafe jobs deduplicated with existing sources (no duplicate titles/companies)
  5. User sees graceful continuation when hiring.cafe API fails (other 10 sources still work)
  6. User sees up to 1,000 jobs from hiring.cafe when search criteria match broadly
**Plans**: TBD

Plans:
- [ ] 42-01-PLAN.md: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 38 → 39 → 40 → 41 → 42

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 38. Auto-Update Foundation | v2.2.0 | 2/2 | ✓ Complete | 2026-02-16 |
| 39. Auto-Update Download | v2.2.0 | 2/2 | ✓ Complete | 2026-02-16 |
| 40. Auto-Update Installation | v2.2.0 | 2/2 | ✓ Complete | 2026-02-16 |
| 41. Auto-Update Polish | v2.2.0 | 0/TBD | Not started | - |
| 42. hiring.cafe Integration | v2.2.0 | 0/TBD | Not started | - |

---
*Last updated: 2026-02-16*
