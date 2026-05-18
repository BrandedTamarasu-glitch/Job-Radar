# Job Radar Handoff

Date: 2026-05-18

## Current State

- Repo path: `/home/corye/openai-cli/Job-Radar`
- Branch: `main`
- Git status after release: clean and synced with `origin/main`, except preserved untracked `.forgeflow/`
- Current release: `v2.8.0`
- Release URL: https://github.com/BrandedTamarasu-glitch/Job-Radar/releases/tag/v2.8.0
- Last local full validation: `1181 passed, 8 skipped`
- Release workflow validation: GitHub Actions Release run `26061938202` passed tests, platform builds, installer builds, and release creation.

## Latest Commits

```text
828b19f ci: fix windows release tests
f21eb34 docs: prepare v2.8.0 release
cc3ba06 refactor: centralize app data status
3e88566 refactor: centralize cache clear status
e83496e refactor: centralize dismissed review cleanup
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

## Sprint 3 Completed Work

The v2.8.0 line includes the audit-remediation architecture work completed so far:

- Report rendering split into focused HTML and Markdown modules while preserving compatibility wrappers in `job_radar/report.py`
- Shared search-pipeline helpers for profile preparation, raw filtering, scoring, sorting, and post-score filtering
- Source architecture split across registry, manual-source, query, config, model, parsing, mapper, API-fetcher, and scraper modules while `job_radar/sources.py` preserves compatibility imports/wrappers
- GUI helper extraction across settings, search, profile, dashboard, applications, update, diagnostics, dialogs, welcome, tab shell, and window shell modules
- Source health writes now distinguish `query_failure_details` from `slow_query_warnings`; legacy `source_warnings` reads remain supported
- Post-release Settings update status cleanup moved skipped-version status formatting into `job_radar/gui/update_status_view_model.py`

## Active Plan

Continue `.planning/AUDIT_REMEDIATION_SPRINTS.md`.

Completed or mostly handled:

- Sprint 0: release blockers
- Sprint 1: trust/state/release hygiene
- Sprint 2: persistence/schema consolidation
- Sprint 3: report, source, search-pipeline, and broad GUI architecture cleanup

Still planned in Sprint 3:

- Continue reducing `job_radar/gui/main_window.py` where helpers can own construction or state formatting without taking behavior callbacks away from `MainWindow`
- Consolidate profile schema construction and validation across CLI and GUI
- Trim `job_radar/sources.py` compatibility wrappers only where tests and downstream imports prove they are not public surface

Still planned in Sprint 4:

- Make welcome/search/progress/completion/error views scroll-safe at minimum window size and OS text scaling
- Rework Applications row actions so status, edits, and templates do not clip
- Improve report offline status feedback and status-sync messaging
- Review copy for macOS portable install paths, source counts, and feature claims

## Recommended Next Slice

Continue with another small post-release Sprint 3 slice:

1. Inspect `job_radar/gui/main_window.py` for remaining text/state helpers that can move into existing view-model modules.
2. Prefer one narrow extraction with behavior-oriented tests.
3. Run focused GUI/view-model tests, then full `rtk .venv/bin/python -m pytest tests/`.
4. Commit after validation.

Suggested focused validation:

```bash
rtk .venv/bin/python -m pytest tests/test_gui_onboarding.py tests/test_gui_search_summary.py tests/test_profile_view_model.py
rtk .venv/bin/python -m pytest tests/
```

## Notes

- Use `apply_patch` for edits.
- Use `rtk git` for git operations.
- Keep `.forgeflow/` untracked unless explicitly asked otherwise.
- Use `env -u GH_TOKEN rtk git push ...` if pushing is requested, so Git uses the active `BrandedTamarasu-glitch` keyring credential.
