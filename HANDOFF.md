# Job Radar Handoff

Date: 2026-05-16

## Current State

- Repo path: `/home/corye/openai-cli/Job-Radar`
- Branch: `main`
- Git status before reboot: clean, `main...origin/main [ahead 6]`
- Last full validation: `1059 passed, 8 skipped`
- Do not push unless explicitly asked. The 6 local commits after the last push are still local.

## Latest Local Commits

```text
45c1d50 refactor: centralize saved search status copy
ba01044 refactor: centralize search history detail text
e888f85 refactor: move application filter options to view model
5368e5e refactor: move application row display to view model
34954ac refactor: move follow-up queue display to view model
c41e4d7 refactor: move follow-up due labels to view model
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
  - `saved_search_success_message`
  - `saved_search_error_message`
- `job_radar/gui/applications_view_model.py`
  - Applications CSV export/import status messages
  - report status import feedback
  - follow-up calendar export feedback

Current line counts:

```text
2149 job_radar/report.py
3624 job_radar/gui/main_window.py
 272 job_radar/gui/applications_view_model.py
 462 job_radar/saved_searches.py
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
1062 passed, 8 skipped
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

1. Continue moving Applications edit/follow-up failure messages into `applications_view_model.py`.
2. Extract Applications tab building into a focused helper only after view-model formatting is stable.
3. Move more search-panel state loading and empty-state text out of `MainWindow` if it stays low-risk.
4. After a few more GUI slices, commit the GUI architecture cleanup docs and code.

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
