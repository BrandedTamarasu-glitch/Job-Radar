# Job Radar Handoff

Date: 2026-05-18

## Current State

- Repo path: `/home/corye/openai-cli/Job-Radar`
- Branch: `main`
- Git status after latest slice: clean, `main...origin/main [ahead 100]`
- Last full validation: `1175 passed, 8 skipped`
- Do not push unless explicitly asked. The 100 local commits after the last push are still local.

## Latest Local Commits

```text
(current) refactor: stop persisting legacy source warnings
9dcb54d refactor: centralize source display names
aa55c8a refactor: centralize source registry construction
c863819 refactor: extract dice scraper
2e49827 refactor: extract hn hiring scraper
331e246 refactor: extract remote scraper fetchers
1c48f54 refactor: extract hiringcafe fetcher
5413885 refactor: extract usajobs fetcher
71f661c refactor: extract jsearch fetcher
30f1587 refactor: extract authentic jobs fetcher
d8f34ad refactor: extract adzuna fetcher
9269f78 refactor: share source location matching
f513733 refactor: extract lightweight api fetchers
d8e56b3 refactor: extract remaining source mappers
454423f refactor: extract usajobs mapper
9372d45 refactor: extract jsearch mapper
594c1ff refactor: extract authentic jobs mapper
a10c258 refactor: extract adzuna mapper
d16ad4a refactor: extract source parsing helpers
e6d656f refactor: extract source job model
7049d4d refactor: extract source config helpers
fe8d098 refactor: group source queries by phase
074e271 refactor: extract source query builder
0d0eabe refactor: extract manual source helpers
ec9433e refactor: extract source registry helpers
98de685 refactor: share search profile preparation
4ffd8e2 refactor: use shared scored filters in cli
fcdec9c refactor: use shared raw filters in cli
30f4428 refactor: use shared scorer in cli
314aa3a refactor: share raw result filtering
e23f5cb refactor: share scored result filtering
905b824 refactor: extract shared search pipeline helpers
74cfb91 refactor: centralize legacy queue handling
6bc8bae refactor: centralize asset queue handling
3a22fd6 refactor: centralize source diagnostics loading
20dde8a refactor: centralize source strategy loading
8817f3d refactor: centralize profile guidance loading
9fd446f refactor: centralize review summary loading
b511736 refactor: centralize search completion content
5e6e0c0 refactor: extract manual update button reset
35fb9dc refactor: centralize download queue results
4985940 refactor: centralize update availability handling
a63f519 refactor: centralize manual update results
5903fed refactor: centralize download worker cleanup
a748f7a refactor: centralize update banner teardown
9f4e71a refactor: remove update status initializer
b4a2275 refactor: centralize api section registration
1ee8106 refactor: centralize search progress updates
aa92d65 refactor: centralize source diagnostics text
9aafa8f refactor: centralize maintenance text
452e22a refactor: remove profile field wrapper
```

## Recently Pushed

Before the current local Sprint 3 commits, the main repo and wiki were pushed successfully using the active `BrandedTamarasu-glitch` GitHub CLI credential.

Main repo docs commit:

```text
0f41166 docs: update report decomposition status
```

Wiki docs commit:

```text
d031627 docs: update report decomposition status
```

## What Was Completed Recently

### Sprint 3: Report Decomposition

`job_radar/report.py` was reduced to 2,149 lines and now delegates to focused modules for:

- report safety
- assets
- text helpers
- filtering
- source warnings
- tiers
- matching
- stats
- profile/tracker summaries
- manual links
- job details
- controls
- job attributes
- result tables
- result rows
- cards/sections
- Markdown sections/results/manual links/profile summaries

README, CHANGELOG, `.planning/AUDIT_REMEDIATION_SPRINTS.md`, and wiki were updated to reflect this work.

### Sprint 3: GUI Architecture Cleanup

Started reducing `job_radar/gui/main_window.py` by moving display formatting into view models/helpers:

- `job_radar/search_pipeline.py`
  - Shared search filter parsing, profile preference, freshness/date resolution, and result filtering helpers for GUI/CLI reuse
  - Shared preset/preferred-skill profile preparation used by CLI and GUI
  - Shared raw-result date/company/skill/location filtering; CLI now uses the shared raw-result filter for date filtering
  - Shared result scoring/dealbreaker sorting and post-score filtering helpers; CLI now uses the shared scorer and composable post-score filters
- `job_radar/source_registry.py`
  - Shared source registry dataclasses and display-name selection helpers
  - Shared selected-query filtering and source phase grouping for fetch orchestration
  - Canonical automated source phase order and registry construction metadata
  - Canonical fallback display-name map for source identifiers
  - `sources.py` now delegates registry/manual display-name selection and registry metadata while retaining query adapters
- `job_radar/manual_sources.py`
  - Manual job-board URL generators, manual source registry, and manual URL generation helpers
  - `sources.py` re-exports the manual-source API for existing CLI/GUI/test imports
- `job_radar/source_queries.py`
  - Automated source query construction and HN Hiring skill-slug mapping
  - `sources.py` re-exports `build_search_queries` for existing CLI/GUI/test imports
- `job_radar/source_config.py`
  - Source fetch parallelism, slow-query threshold, and per-source cache TTL resolution
  - `sources.py` re-exports the config helpers for existing tests/imports
- `job_radar/source_models.py`
  - Shared `JobResult` data model
  - `sources.py` re-exports `JobResult` for existing CLI/GUI/test imports
- `job_radar/source_parsing.py`
  - Shared source text cleanup, location normalization, arrangement parsing, and Dice parsing constants
  - Shared location matching helper for local hiring.cafe filtering
  - `sources.py` re-exports parsing helpers used by existing tests/imports
- `job_radar/source_mappers.py`
  - Adzuna, Authentic Jobs, JSearch, USAJobs, SerpAPI, Jobicy, and hiring.cafe API response mappers
  - hiring.cafe salary normalization/formatting helpers
  - `sources.py` re-exports moved mappers for existing tests/imports
- `job_radar/source_api_fetchers.py`
  - Adzuna, Authentic Jobs, JSearch, USAJobs, SerpAPI, Jobicy, and hiring.cafe API fetchers
  - `sources.py` keeps patch-compatible wrappers/re-exports for existing tests/imports and registry wiring
- `job_radar/source_scrapers.py`
  - Dice, HN Hiring, RemoteOK, and We Work Remotely scraper fetchers
  - `sources.py` keeps patch-compatible wrappers for existing tests/imports and registry wiring
- `job_radar/gui/applications_view_model.py`
  - `format_next_action_due_text`
  - `ApplicationNextActionRow`
  - `application_next_action_row`
  - `ApplicationPipelineDisplayRow`
  - `application_pipeline_display_row`
  - `application_followup_filter_options`
- `job_radar/saved_searches.py`
  - `format_search_history_detail`
  - `recent_search_panel_rows`
  - `saved_search_panel_rows`
  - `load_recent_search_panel_rows`
  - `load_saved_search_panel_rows`
  - `saved_search_success_message`
  - `saved_search_error_message`
- `job_radar/gui/applications_view_model.py`
  - Applications CSV export/import status messages
  - report status import feedback
  - follow-up calendar export feedback
  - Applications edit/follow-up failure feedback
- `job_radar/gui/applications_tab.py`
  - Applications tab construction
  - Applications follow-up queue construction
- `job_radar/gui/update_status_view_model.py`
  - Settings update status text/color formatting
  - relative last-check time formatting
- `job_radar/gui/review_state_view_model.py`
  - Review queue summary formatting and safe loading
- `job_radar/gui/maintenance_view_model.py`
  - Settings cache/app-data maintenance status messages
  - dismissed review cleanup status messages
  - Settings local maintenance and feedback diagnostics text composition
- `job_radar/gui/source_diagnostics_view_model.py`
  - Settings source diagnostics text composition
  - Settings source diagnostics history loading
  - Search-tab pre-run source strategy guidance loading
- `job_radar/gui/search_summary.py`
  - live source progress text helpers
  - source progress counter display text
  - search completion label/block text helpers
  - search completion content block composition
  - search readiness guidance line composition
- `job_radar/gui/search_panel.py`
  - Search state content clearing helper
  - Search source-progress widget updates
  - Search idle controls/action shell construction
  - Search idle profile-readiness guidance panel construction
  - Search success message replacement helper
  - Recent search panel construction
  - Saved search panel construction/status label
  - Search progress panel construction/updatable widget bundle
  - Search completion panel construction
  - Search error panel construction
  - Search cancellation panel construction
- `job_radar/gui/api_status_view_model.py`
  - API credential test status text/color formatting
  - API credential test HTTP response status mapping
- `job_radar/gui/install_status_view_model.py`
  - installer launch prompt/status/error messages
- `job_radar/gui/profile_view_model.py`
  - Profile tab summary row formatting
  - Profile tab readiness summary/guidance formatting
  - Profile tab load error text
  - Profile loading for non-blocking search guidance
- `job_radar/gui/profile_panel.py`
  - Profile tab content clearing helper
  - Profile tab label/value row construction
  - Profile tab readiness/summary/edit panel construction
- `job_radar/gui/dashboard_panel.py`
  - Profile dashboard next-step panel construction
- `job_radar/gui/dialogs.py`
  - Centered modal message dialog construction
- `job_radar/gui/welcome_panel.py`
  - First-run welcome screen construction
- `job_radar/gui/window_shell.py`
  - Top-level content clearing while preserving the header
- `job_radar/gui/tab_shell.py`
  - Main tabview construction and canonical tab names
- `job_radar/gui/main_window.py`
  - Shared lazy tab-build helper for user and programmatic tab navigation
  - Shared available-update queue handling helper
  - Shared manual update-check result helpers
  - Shared manual update-check button reset helper
  - Shared update banner teardown helper
  - Shared download worker reference cleanup helper
  - Shared terminal download queue handling helpers
  - Shared download progress and asset queue handling helpers
  - Shared legacy worker queue handling helpers
  - New source health history writes use canonical `query_failure_details` and `slow_query_warnings` without persisting new ambiguous `source_warnings` aliases
  - Removed redundant Applications due-text wrapper in favor of the view-model helper
  - Removed obsolete Profile field wrapper after Profile row rendering moved to `profile_panel.py`
  - Removed obsolete Settings update-status initializer after update panel extraction
- `job_radar/gui/demo_report_view_model.py`
  - Demo report success/error feedback text
- `job_radar/gui/settings_panel.py`
  - Settings update controls/status panel construction
  - Settings section separator construction
  - Settings storage maintenance and diagnostics panel construction
  - Settings Jobicy public-source status and JSearch setup tip construction
  - Settings API credential section construction
  - Settings API credential widget registration
  - Settings API credential panel orchestration
  - Settings scoring configuration panel construction
  - Settings danger-zone construction

Current line counts:

```text
2149 job_radar/report.py
1138 job_radar/search.py
 261 job_radar/search_pipeline.py
 505 job_radar/source_scrapers.py
 487 job_radar/source_api_fetchers.py
 488 job_radar/source_mappers.py
 120 job_radar/source_parsing.py
  27 job_radar/source_models.py
 117 job_radar/source_config.py
 122 job_radar/source_queries.py
 117 job_radar/manual_sources.py
 142 job_radar/source_registry.py
 440 job_radar/sources.py
 627 job_radar/gui/worker_thread.py
2320 job_radar/gui/main_window.py
  14 job_radar/gui/demo_report_view_model.py
  44 job_radar/gui/dialogs.py
  70 job_radar/gui/welcome_panel.py
  11 job_radar/gui/window_shell.py
  17 job_radar/gui/tab_shell.py
 581 job_radar/gui/settings_panel.py
 507 job_radar/gui/search_panel.py
  82 job_radar/gui/profile_panel.py
  62 job_radar/gui/dashboard_panel.py
  75 job_radar/gui/api_status_view_model.py
  31 job_radar/gui/install_status_view_model.py
  88 job_radar/gui/profile_view_model.py
 287 job_radar/gui/applications_tab.py
 297 job_radar/gui/applications_view_model.py
 287 job_radar/gui/maintenance_view_model.py
 477 job_radar/gui/source_diagnostics_view_model.py
 258 job_radar/gui/search_summary.py
  78 job_radar/gui/update_status_view_model.py
  32 job_radar/gui/review_state_view_model.py
 478 job_radar/saved_searches.py
```

## Validation Commands Used

Focused tests for latest GUI slices:

```bash
rtk .venv/bin/python -m pytest tests/test_applications_view_model.py tests/test_gui_onboarding.py
rtk .venv/bin/python -m pytest tests/test_saved_searches.py tests/test_gui_onboarding.py
```

Full regression:

```bash
rtk .venv/bin/python -m pytest tests/
```

Latest result:

```text
1175 passed, 8 skipped
```

## Active Plan

Continue `.planning/AUDIT_REMEDIATION_SPRINTS.md`.

Completed or mostly handled:

- Sprint 0: release blockers
- Sprint 1: trust/state/release hygiene
- Sprint 2: persistence/schema consolidation
- Sprint 3 report renderer decomposition

Still planned in Sprint 3:

- Extract a shared search pipeline service used by CLI and GUI adapters.
- Continue splitting `gui/main_window.py` into tab/presenter/view-model modules.
- Source adapter implementations have moved out of the single `sources.py` hotspot; `sources.py` still carries compatibility imports, wrappers, and registry wiring.
- Consolidate profile schema construction/validation across CLI and GUI.
- Continue source-health compatibility cleanup where it is safe; new tracker writes now distinguish source failures from slow-query warnings, while legacy `source_warnings` reads remain supported.

Still planned in Sprint 4:

- Make welcome/search/progress/completion/error views scroll-safe at minimum window size and OS text scaling.
- Rework Applications row actions so status, edits, and templates do not clip.
- Improve report offline status feedback and status-sync messaging.
- Review copy for macOS portable install paths, source counts, and feature claims.

## Recommended Next Slice

Continue with small, low-risk compatibility cleanup or return to `MainWindow` extractions before attempting larger tab splitting:

1. Trim `sources.py` compatibility imports only where tests and downstream imports prove they are not part of the public surface.
2. Move more search-panel state loading and empty-state text out of `MainWindow` if source compatibility cleanup looks risky.
3. Continue extracting tab construction only where callbacks stay simple and tests remain behavior-oriented.

Suggested validation for the next GUI slice:

```bash
rtk .venv/bin/python -m pytest tests/test_applications_view_model.py tests/test_saved_searches.py tests/test_gui_onboarding.py
rtk .venv/bin/python -m pytest tests/
```

## Notes

- Use `apply_patch` for edits.
- Use `rtk git` for git operations.
- `.review-squad/` should remain untracked/ignored.
- Use `env -u GH_TOKEN rtk git push ...` if pushing is requested, so Git uses the active `BrandedTamarasu-glitch` keyring credential.
