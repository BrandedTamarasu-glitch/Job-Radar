# Job Radar Handoff

Date: 2026-05-20

## Current State

- Repo path: `/home/corye/openai-cli/Job-Radar`
- Branch: `main`
- Git status after release: local branch synced with origin except preserved untracked `.forgeflow/`
- Current release: `v2.9.0`
- Current release URL: https://github.com/BrandedTamarasu-glitch/Job-Radar/releases/tag/v2.9.0
- Last local full validation: `1205 passed, 8 skipped`
- Release workflow validation: GitHub Actions Release run `26164927148` passed tests, platform builds, installer builds, and release publishing.

## Latest Commits

```text
95a28de ui: wrap follow-up queue actions
1c585f5 docs: complete sprint 4 copy review
c4c885d ux: clarify report status sync
21960f5 ui: wrap applications row actions
6b430bd ui: make search states scroll-safe
```

## Recently Shipped

### v2.8.0 Release

The `v2.8.0` tag points at `828b19f` and the release is published with Linux, macOS, Windows, installer, and checksum assets.

Release/docs updates included:

- `pyproject.toml` and `job_radar/__init__.py` version bump to `2.8.0`
- `CHANGELOG.md`, `README.md`, and `README-dist.txt` release updates
- Wiki updates for `Home.md`, `For-Developers.md`, and `Refinement-Sprint-Plan.md`

Release validation completed:

```text
rtk .venv/bin/python -m pytest tests/test_metadata.py tests/test_release_verification.py tests/test_release_notes.py
21 passed

rtk .venv/bin/python -m pytest tests/
1180 passed, 8 skipped

rtk env PYTHON_BIN=.venv/bin/python bash scripts/build.sh
OK: dist/job-radar/job-radar
OK: job-radar-v2.8.0-linux.tar.gz
OK: wrote checksums to job-radar-v2.8.0-linux.sha256
```

The first tag-triggered release run failed on Windows CI. The fix in `828b19f` made private credential writes tolerate platforms without `os.fchmod`, made an installer-message assertion platform-aware, and relaxed the report payload-size guard for Windows line endings. The tag was then force-updated with user approval and the rerun passed.

### v2.8.1 Release

The `v2.8.1` tag is published with Linux, macOS, Windows, installer, and checksum assets.

Validation completed:

```text
rtk .venv/bin/python -m pytest tests/test_metadata.py tests/test_release_verification.py tests/test_release_notes.py
21 passed

rtk .venv/bin/python -m pytest tests/
1201 passed, 8 skipped

rtk env PYTHON_BIN=.venv/bin/python bash scripts/build.sh
OK: dist/job-radar/job-radar
OK: job-radar-v2.8.1-linux.tar.gz
OK: wrote checksums to job-radar-v2.8.1-linux.sha256

./dist/job-radar/job-radar --version
job-radar 2.8.1
```

### v2.9.0 Release

The `v2.9.0` release packages Sprint 4 UX polish, GitHub Actions runtime maintenance, report status-sync copy, and public documentation truth-sweep updates. The tag is published with Linux, macOS, Windows, installer, and checksum assets.

Validation completed:

```text
rtk .venv/bin/python -m pytest tests/test_metadata.py tests/test_release_verification.py tests/test_release_notes.py
23 passed

rtk .venv/bin/python -m pytest tests/
1205 passed, 8 skipped

rtk env PYTHON_BIN=.venv/bin/python bash scripts/build.sh
OK: dist/job-radar/job-radar
OK: job-radar-v2.9.0-linux.tar.gz
OK: wrote checksums to job-radar-v2.9.0-linux.sha256

./dist/job-radar/job-radar --version
job-radar 2.9.0
```

The tag-triggered GitHub Actions Release workflow passed:

```text
Run: 26164927148
Release: https://github.com/BrandedTamarasu-glitch/Job-Radar/releases/tag/v2.9.0
```

## Sprint 3 Completed Work

The v2.8.0 line includes the audit-remediation architecture work completed so far:

- Report rendering split into focused HTML and Markdown modules while preserving compatibility wrappers in `job_radar/report.py`
- Shared search-pipeline helpers for profile preparation, raw filtering, scoring, sorting, and post-score filtering
- Source architecture split across registry, manual-source, query, config, model, parsing, mapper, API-fetcher, and scraper modules while `job_radar/sources.py` preserves compatibility imports/wrappers
- GUI helper extraction across settings, search, profile, dashboard, applications, update, diagnostics, dialogs, welcome, tab shell, and window shell modules
- Source health writes now distinguish `query_failure_details` from `slow_query_warnings`; legacy `source_warnings` reads remain supported
- Post-release Settings update status cleanup moved skipped-version and manual update-result status formatting into `job_radar/gui/update_status_view_model.py`
- Post-release API quota display cleanup moved quota label text/color formatting into `job_radar/gui/api_status_view_model.py`
- GUI Open Report now uses the shared browser helper instead of direct `webbrowser` calls.
- Uninstall partial-failure and completion message formatting now lives in `job_radar/gui/uninstall_view_model.py`.
- Profile years parsing, compensation-floor parsing, range constants, and level derivation now live in `job_radar/profile_schema.py` for CLI wizard, quick editor, GUI form, and profile validation reuse.
- Temporary Search-tab success message replacement and auto-hide timing now live in `job_radar/gui/search_panel.py`.
- Search-tab saved-search feedback label updates now live in `job_radar/gui/search_panel.py`.
- Applications-tab export/import/edit feedback label updates now live in `job_radar/gui/applications_tab.py`.
- Settings maintenance feedback label updates now live in `job_radar/gui/settings_panel.py`.
- API credential status label application now lives in `job_radar/gui/api_status_view_model.py`.
- Release and accessibility workflows now use current Node 24 GitHub Actions majors, and release Windows jobs use the explicit `windows-2025-vs2026` runner label.

## Active Plan

Continue `.planning/AUDIT_REMEDIATION_SPRINTS.md`.

Completed or mostly handled:

- Sprint 0: release blockers
- Sprint 1: trust/state/release hygiene
- Sprint 2: persistence/schema consolidation
- Sprint 3: report, source, search-pipeline, profile schema, and broad GUI architecture cleanup
- Post-release workflow maintenance for GitHub Actions Node 24 runtime migration

Still planned in Sprint 3:

- Continue reducing `job_radar/gui/main_window.py` where helpers can own construction or state formatting without taking behavior callbacks away from `MainWindow`
- Trim `job_radar/sources.py` compatibility wrappers only where tests and downstream imports prove they are not public surface

Sprint 4 completed locally:

- First-run welcome content and Search tab idle/progress/completion/error/cancel states now render in scrollable containers for minimum-window and OS text-scaling resilience.
- Applications header actions, follow-up queue actions, and per-row status/edit/template controls now use grid-based wrapped rows to reduce clipping at narrow widths and larger text settings.
- Report controls and status-change feedback now explain that generated reports work offline and browser-local status edits require JSON export plus Applications-tab import.
- README, FAQ, and distribution README now use current macOS portable paths, source counts, status export/import behavior, and source-extension architecture.

## Recommended Next Slice

Start the next post-release planning slice: monitor v2.9.0 for installer/download feedback, then choose the next low-risk backlog item from the post-release feedback candidates or remaining compatibility-focused audit cleanup.

Latest validation:

```bash
rtk .venv/bin/python -m pytest tests/test_metadata.py tests/test_release_verification.py tests/test_release_notes.py
22 passed

rtk .venv/bin/python -m pytest tests/
1202 passed, 8 skipped
```

Sprint 4 latest validation:

```bash
rtk .venv/bin/python -m pytest tests/test_gui_onboarding.py
68 passed

rtk .venv/bin/python -m pytest tests/
1202 passed, 8 skipped

rtk .venv/bin/python -m pytest tests/test_applications_view_model.py tests/test_gui_onboarding.py
86 passed

rtk .venv/bin/python -m pytest tests/
1203 passed, 8 skipped

rtk .venv/bin/python -m pytest tests/test_report.py tests/test_report_controls.py tests/test_demo_report_view_model.py tests/test_applications_view_model.py
130 passed

rtk .venv/bin/python -m pytest tests/
1203 passed, 8 skipped

rtk .venv/bin/python -m pytest tests/test_metadata.py tests/test_release_notes.py tests/test_install_status_view_model.py tests/test_demo_report_view_model.py
17 passed

rtk .venv/bin/python -m pytest tests/
1204 passed, 8 skipped

rtk .venv/bin/python -m pytest tests/test_gui_onboarding.py tests/test_applications_view_model.py
87 passed

rtk .venv/bin/python -c '<CustomTkinter construction smoke for welcome/search/applications at 700x500, 900x600, and widget scales 1.0/1.25>'
gui smoke ok: 700x500, 900x600, scales 1.0 and 1.25

rtk .venv/bin/python -m pytest tests/
1205 passed, 8 skipped
```

## Notes

- Use `apply_patch` for edits.
- Use `rtk git` for git operations.
- Keep `.forgeflow/` untracked unless explicitly asked otherwise.
- Use `env -u GH_TOKEN rtk git push ...` if pushing is requested, so Git uses the active `BrandedTamarasu-glitch` keyring credential.
