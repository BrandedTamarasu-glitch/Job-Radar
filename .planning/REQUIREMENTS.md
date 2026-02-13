# Requirements: Job Radar

**Defined:** 2026-02-12
**Core Value:** Accurate job-candidate scoring -- if the scoring is wrong, nothing else matters.

## v2.0.0 Requirements

Requirements for desktop GUI launcher. Each maps to roadmap phases.

### GUI Foundation

- [x] **GUI-01**: Double-clicking the executable opens a desktop window (not a terminal)
- [x] **GUI-02**: Running with CLI flags (e.g., `job-radar --min-score 3.5`) uses the existing CLI path
- [x] **GUI-03**: Search execution does not freeze the GUI window (non-blocking threading)
- [x] **GUI-04**: GUI updates (progress, errors) are thread-safe via main thread callbacks

### Profile Setup

- [x] **PROF-01**: User can create a new profile via GUI form fields (name, skills, titles, experience, location, arrangement)
- [x] **PROF-02**: User can upload a PDF resume via file dialog to pre-fill profile fields
- [x] **PROF-03**: Profile form validates input and shows error messages for invalid fields
- [x] **PROF-04**: User can edit an existing profile through the same GUI form (pre-filled with current values)

### Search Controls

- [x] **SRCH-01**: User can click a "Run Search" button to start a job search
- [x] **SRCH-02**: User can set date range (from/to) for job postings
- [x] **SRCH-03**: User can set minimum score threshold
- [x] **SRCH-04**: User can toggle "new only" mode
- [x] **SRCH-05**: Search completion shows results count and "Open Report" button to open HTML report in browser

### Progress & Feedback

- [x] **PROG-01**: User sees a visual progress indicator while search is running
- [x] **PROG-02**: User sees error messages when search fails (network errors, source failures)

### Packaging

- [x] **PKG-01**: PyInstaller builds produce a GUI executable for Windows, macOS, and Linux
- [x] **PKG-02**: GUI executable is separate from CLI executable (both included in distribution)
- [x] **PKG-03**: CustomTkinter theme files are bundled correctly via --add-data

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Search Controls (Differentiators)

- **SRCH-06**: Date range presets (Last 24h, Last 48h, Last week)
- **SRCH-07**: Quick re-run button for repeating last search

### Profile Setup (Differentiators)

- **PROF-05**: Visual sections grouping related fields (Identity, Skills, Preferences, Filters)
- **PROF-06**: Pre-fill form from existing profile on subsequent launches

### Progress & Feedback (Differentiators)

- **PROG-03**: Per-source progress display (e.g., "Fetching Dice... 3/6 sources")
- **PROG-04**: Completion summary showing results count before opening report

### Packaging (Differentiators)

- **PKG-04**: macOS code signing and notarization for Gatekeeper bypass
- **PKG-05**: Linux AppImage or Flatpak distribution format

## Out of Scope

| Feature | Reason |
|---------|--------|
| Inline results display in GUI | HTML report already handles display, filtering, and interaction |
| Real-time filtering in GUI | HTML report has status filtering, CSV export, and keyboard shortcuts |
| Custom browser selection | OS default browser is sufficient |
| Multi-profile switching | Context switching unclear for job search (deferred from v1.x) |
| Settings/preferences panel | Config file + CLI flags handle this adequately |
| System tray / background mode | Batch daily search workflow is intentional design |
| Dark/light theme toggle | CustomTkinter follows system theme automatically |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GUI-01 | Phase 28 | Complete |
| GUI-02 | Phase 28 | Complete |
| GUI-03 | Phase 28 | Complete |
| GUI-04 | Phase 28 | Complete |
| PROF-01 | Phase 29 | Complete |
| PROF-02 | Phase 29 | Complete |
| PROF-03 | Phase 29 | Complete |
| PROF-04 | Phase 29 | Complete |
| SRCH-01 | Phase 29 | Complete |
| SRCH-02 | Phase 29 | Complete |
| SRCH-03 | Phase 29 | Complete |
| SRCH-04 | Phase 29 | Complete |
| SRCH-05 | Phase 29 | Complete |
| PROG-01 | Phase 29 | Complete |
| PROG-02 | Phase 29 | Complete |
| PKG-01 | Phase 30 | Complete |
| PKG-02 | Phase 30 | Complete |
| PKG-03 | Phase 30 | Complete |

**Coverage:**
- v2.0.0 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

**Coverage validation:** 18/18 requirements mapped (100%)

---
*Requirements defined: 2026-02-12*
*Last updated: 2026-02-13 after Phase 30 completion — all v2.0.0 requirements complete*
