# Changelog

## Unreleased

### New Features
- **Adaptive dashboard maintenance guidance** - Profile dashboard recommendations can now surface local maintenance suggestions from Settings state.
- **Adaptive dashboard source quality** - Profile dashboard recommendations can now surface source-quality issues from recent diagnostics.
- **Bounded review-state clearing** - Review-state helpers can clear a limited number of entries by state for safer future bulk actions.
- **Dismissed review cleanup** - Settings can clear a bounded batch of dismissed review items without touching shortlist or maybe-later entries.
- **Daily dashboard foundation** - Added a Profile-tab next-step panel that prioritizes profile readiness, overdue follow-ups, review queue work, and saved/recent search shortcuts from local state.
- **Search insight recap** - Recent and saved searches now show a bounded previous-run comparison for total, new, high-score, and review-state movement.
- **Search run context** - Search completion now highlights source failures, cache behavior, and active filters that may explain result changes.
- **Changed-search prioritization** - Saved searches with meaningful previous-run movement are surfaced first in the Search tab.
- **Dashboard search insight** - The Profile dashboard now calls out saved searches that changed since the previous run.
- **Follow-up focus filters** - Applications can filter the follow-up queue to all, overdue, or due-soon actions.
- **Quick follow-up completion** - Applications next-action queue rows can clear completed follow-ups directly.
- **Follow-up snooze** - Applications next-action queue rows can snooze follow-ups by three days.
- **Follow-up calendar export** - Applications can export dated follow-up tasks as an iCalendar file.
- **Source reliability scoring** - Settings source diagnostics now include coarse reliability scores from recent source history.
- **Source toggle recommendations** - Settings diagnostics now recommend temporarily disabling repeatedly unreliable sources.
- **Source coverage gaps** - Source health history now preserves search context so Settings can call out source/preset combinations with no recent jobs.
- **Preset strategy diagnostics** - Settings now recommends source/preset actions from recent failures and low-yield or high-yield search outcomes.
- **Pre-run source strategy guidance** - Search controls now show recent source reliability and preset-yield guidance before rerunning a search.
- **Source selection strategy** - Settings and Search guidance now recommend specific sources to uncheck, pair with broader coverage, or keep enabled from recent outcomes.
- **Source strategy name clarity** - Source diagnostics normalize saved source keys into user-facing source names so recommendations stay readable.
- **Release readiness tracking** - Added a Product Iteration U-Y release-readiness checklist with source strategy and release support validation checkpoints.
- **Redacted feedback diagnostics** - Settings now shows copyable privacy-safe aggregate diagnostics users can share after release without exposing local profile, search, tracker, or path contents.
- **Windows build script release drift** - Windows local builds now derive the version from package metadata, use release-compatible archive/checksum names, and run release artifact verification.
- **Local maintenance insights** - Settings now summarizes local data size, cache files, tracker history, review state, saved searches, and maintenance suggestions.
- **Bounded dashboard history counts** - Profile dashboard changed-search callouts now stay compact for large saved-search histories.
- **Maintenance documentation** - README, workflow docs, and FAQ now describe local maintenance behavior and privacy boundaries.

### Documentation
- Documented Product Iterations P-T and U-Y across README, roadmap, and project state memory.
- Drafted Product Iteration U-Y release notes with privacy boundaries for local user data.
- Added privacy-safe post-release feedback loop planning for Product Iteration U-Y.

### Validation
- Full automated regression for Sprint X release readiness: 950 passed, 8 skipped.
- Local Linux artifact build verification passed for `job-radar-v2.6.0-linux.tar.gz` with checksum manifest generation.

## v2.6.0 — 2026-05-15

### New Features
- **Editable application workspace** — Applications rows now support direct status, next-action, due-date, notes, and template insertion workflows while preserving tracker timeline history.
- **Search review state** — Search results now support persisted shortlist, maybe-later, and dismissed states across GUI summaries, saved-search comparisons, and HTML reports.
- **Data portability** — Settings can export and validate portable app-data bundles with profile, config, saved searches, review state, tracker data, and manifest checks.

### Improvements
- **Source health clarity** — Settings now prioritizes unhealthy sources, shows cache freshness, and provides clearer recommended actions for failed, slow, warning-heavy, and healthy sources.
- **Large workflow stability** — Large HTML reports skip rendering omitted lower-score rows after the visible/collapsed caps, and search cancellation now stops final report preparation before source-health writes or report generation.
- **Release trust** — Release verification now diagnoses filename and installer-directory drift, validates executable permissions, suppresses noisy virtualenv matches, returns clean CLI failures, and publishes checksum manifests for release artifacts.

### Documentation
- Updated README installation guidance for checksum verification and refreshed roadmap/planning docs for the completed K-O iteration.

### Validation
- 910 automated tests collected: 902 passed, 8 skipped.

## v2.5.0 — 2026-05-13

### New Features
- **GUI search steering** — Added GUI presets, source toggles, company filters, must-have and nice-to-have skill controls, location strictness, and freshness presets for per-search control without editing the profile.
- **Application pipeline** — Added a GUI Applications tab, application notes, next actions, next-action dates, CSV export, and a config-backed option to hide rejected/skipped jobs from future reports.
- **Performance and source diagnostics** — Added per-source timing, source health history, cache hit/miss/write counters, slowest-source diagnostics in Settings, source-specific cache TTLs, and better GUI cancellation propagation into source fetch boundaries.
- **Report review workflow** — Added shortlist state separate from application status, keyboard navigation between visible jobs, compact/detail view, improved mobile report layout, concise "why this matched" summaries, and grouped must-have/nice-to-have skill callouts.

### Documentation
- Updated README and workflow docs for the v2.5.0 product iteration, expanded feature coverage, and refreshed test counts.

### Validation
- 781 automated tests collected: 773 passed, 8 skipped.

## v2.4.0 — 2026-05-13

### New Features
- **GUI search controls** — Added GUI presets, automated/manual source toggles, company include/exclude filters, must-have and nice-to-have skill controls, location strictness, and freshness presets.
- **Application pipeline foundation** — Added tracker persistence for notes, next actions, and next-action dates; added an Applications view-model; added application pipeline CSV export helpers.

### Fixes
- **Release test compatibility** — Metadata tests now support Python 3.10 via `tomli` fallback, fixing the failed release workflow collection error on macOS.

### Validation
- 754 automated tests collected: 746 passed, 8 skipped.

## v2.3.0 — 2026-05-13

### New Features
- **GUI search outcome clarity** — Completion screens now show source warnings, per-source job counts, zero-result next actions, and clearer cancelled/error states.
- **Runtime stability controls** — Added documented controls for fetch parallelism, request timeout, and slow-source warning thresholds.
- **Cache maintenance controls** — Added stale cache pruning plus visible cache clearing in both CLI (`--clear-cache`) and GUI Settings.

### Improvements
- **Report responsiveness** — Removed unused report assets, added a payload-size guard, collapsed lower-score rows in large reports, and centralized external asset tags.
- **Long-running data maintenance** — Added conservative tracker pruning for old seen jobs while preserving application status and legacy records.
- **Storage consistency** — Tracker data now defaults to app data `results/tracker.json`, with legacy launch-directory tracker fallback.
- **Uninstall clarity** — Runtime data locations, cleanup behavior, and profile/config-only backup scope are documented consistently across README, workflow docs, and FAQ.

### Validation
- 727 automated tests collected: 719 passed, 8 skipped.

## v2.2.0 — 2026-02-16

### New Features
- **In-app auto-update** — Detect new releases, preview changelog, download with progress bar, SHA256 verification, launch installer, and skip-version support
- **hiring.cafe integration** — New free job source (tech job aggregator, rate limited: 60/hour, no API key required)
- **Cross-source dedup richness scoring** — When duplicate listings are found across sources, the richest version (most complete data) is kept instead of first-seen

### Improvements
- 9 Windows CI test fixes for cross-platform reliability
- 664 automated tests across 21 test files (was 566 across 19)

## v2.1.7 — 2026-02-14

### Critical Bug Fix
- **Tab buttons now work reliably** - Fixed invisible welcome screen frame blocking tab button clicks
- **Root cause** - `grid_slaves()` didn't clear `place()`-managed widgets, leaving invisible overlay
- **Impact** - Eliminated random tab switching delays and click blocking

## v2.1.6 — 2026-02-14
