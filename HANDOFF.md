# Job Radar Handoff

Date: 2026-05-16

## Current State

- Repo path: `/home/corye/openai-cli/Job-Radar`
- Branch: `main`
- Git status before latest slice: clean, `main...origin/main [ahead 47]`
- Last full validation: `1108 passed, 8 skipped`
- Do not push unless explicitly asked. The 47 local commits after the last push are still local.

## Latest Local Commits

```text
0442575 refactor: centralize demo report feedback
5a2a8b8 refactor: extract search content clearing
3e70a0c refactor: centralize search readiness guidance
3e6cd0a refactor: extract settings separator helper
d414df8 refactor: centralize lazy tab building
d5a4a43 refactor: reuse search success flow
3ba8423 refactor: extract main tab shell
fb8f391 refactor: extract settings scoring panel
```

## Recently Pushed

Before the current 6 local commits, the main repo and wiki were pushed successfully using the active `BrandedTamarasu-glitch` GitHub CLI credential.

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
- `job_radar/gui/maintenance_view_model.py`
  - Settings cache/app-data maintenance status messages
  - dismissed review cleanup status messages
- `job_radar/gui/search_summary.py`
  - live source progress text helpers
  - source progress counter display text
  - search completion label/block text helpers
  - search readiness guidance line composition
- `job_radar/gui/search_panel.py`
  - Search state content clearing helper
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
- `job_radar/gui/profile_panel.py`
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
  - Removed redundant Applications due-text wrapper in favor of the view-model helper
- `job_radar/gui/demo_report_view_model.py`
  - Demo report success/error feedback text
- `job_radar/gui/settings_panel.py`
  - Settings update controls/status panel construction
  - Settings section separator construction
  - Settings storage maintenance and diagnostics panel construction
  - Settings Jobicy public-source status and JSearch setup tip construction
  - Settings API credential section construction
  - Settings API credential panel orchestration
  - Settings scoring configuration panel construction
  - Settings danger-zone construction

Current line counts:

```text
2149 job_radar/report.py
2357 job_radar/gui/main_window.py
  14 job_radar/gui/demo_report_view_model.py
  44 job_radar/gui/dialogs.py
  70 job_radar/gui/welcome_panel.py
  11 job_radar/gui/window_shell.py
  17 job_radar/gui/tab_shell.py
 557 job_radar/gui/settings_panel.py
 486 job_radar/gui/search_panel.py
  76 job_radar/gui/profile_panel.py
  62 job_radar/gui/dashboard_panel.py
  75 job_radar/gui/api_status_view_model.py
  31 job_radar/gui/install_status_view_model.py
  77 job_radar/gui/profile_view_model.py
 287 job_radar/gui/applications_tab.py
 297 job_radar/gui/applications_view_model.py
 275 job_radar/gui/maintenance_view_model.py
 222 job_radar/gui/search_summary.py
  78 job_radar/gui/update_status_view_model.py
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
1108 passed, 8 skipped
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
- Move source adapters out of the single `sources.py` hotspot behind a small registry/interface.
- Consolidate profile schema construction/validation across CLI and GUI.
- Rename source-health fields to distinguish source failures from slow-query warnings, with migration.

Still planned in Sprint 4:

- Make welcome/search/progress/completion/error views scroll-safe at minimum window size and OS text scaling.
- Rework Applications row actions so status, edits, and templates do not clip.
- Improve report offline status feedback and status-sync messaging.
- Review copy for macOS portable install paths, source counts, and feature claims.

## Recommended Next Slice

Continue with small, low-risk `MainWindow` extractions before attempting larger tab splitting:

1. Move more search-panel state loading and empty-state text out of `MainWindow` if it stays low-risk.
2. Continue extracting tab construction only where callbacks stay simple and tests remain behavior-oriented.
3. After a few more GUI slices, commit the GUI architecture cleanup docs and code.

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
