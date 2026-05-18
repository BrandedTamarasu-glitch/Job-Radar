# Audit Remediation Sprints

Last updated: 2026-05-16

This plan converts the Review Squad top-to-bottom quality, security, UX, and rebase audit into executable sprints. The current release line is blocked until Sprint 0 is complete and validated.

## Sprint 0 - Release Blockers

Goal: remove the runtime trust and privacy defects that should not ship in the next production release.

- Harden auto-update downloads:
  - Fail closed when a release asset has no SHA256 digest/checksum.
  - Download installers into a private per-run temp directory instead of a predictable shared temp filename.
  - Only surface installer launch when verification succeeds.
- Make generated reports local-first:
  - Remove remote CDN JS/CSS from local reports or vendor the assets.
  - Keep report interactivity working offline.
  - Reduce embedded tracker/review/application payloads after remote assets are removed.
- Move credentials out of cwd `.env` flows:
  - Resolve one credential store under app data or OS credential storage.
  - Migrate legacy cwd `.env` once where safe.
  - Replace `sys.exit` library behavior with typed credential/config errors.
  - Redact or avoid credential-bearing URLs in cache/log material.

Validation:
- `pytest tests/test_download_worker.py tests/test_update_checker.py`
- `pytest tests/test_report.py tests/test_api_config.py tests/test_cache.py`
- Full `pytest tests/`

## Sprint 1 - Must-Fix Trust, State, And Release Hygiene

Goal: close high-priority user trust gaps and make the next release process defensible.

- Add URL scheme allowlisting for job links and manual report URLs.
- Implement a real report-to-app status import/sync path, or revise docs until the sync exists.
- Harden release workflow:
  - Default to read-only permissions.
  - Grant `contents: write` only to the release publishing job.
  - Pin actions and release tools deliberately.
  - Lock or constrain build dependencies.
- Clean rebase identity drift in shipped metadata and docs, including installer URLs.
- Add `.review-squad/` to ignored local tooling paths.

Validation:
- `pytest tests/test_report.py tests/test_tracker.py tests/test_metadata.py`
- Release workflow dry-run review and release verification tests.

## Sprint 2 - Persistence And Schema Consolidation

Goal: make user state resilient and easier to evolve without data loss.

- Centralize atomic JSON writes and recovery behavior for tracker/cache/review/saved-search state.
- Add explicit schema versions and migrations for tracker, review state, saved searches, and app-data bundles.
- Validate portability restore payload sizes and JSON schemas before mutating live app data.
- Keep legacy reads non-destructive during migrations.

Validation:
- `pytest tests/test_tracker.py tests/test_review_state.py tests/test_saved_searches.py tests/test_data_portability.py tests/test_cache.py`
- Corrupt-file and interrupted-write regression tests.

## Sprint 3 - Rebase-Nimble Architecture

Goal: reduce merge hotspots and duplicated behavior after the trust fixes are stable.

- Extract a shared search pipeline service used by CLI and GUI adapters.
- Split `main_window.py` into tab/presenter modules with behavior-oriented tests.
- Move source adapters out of the single `sources.py` hotspot behind a small registry/interface.
- Split report rendering into data shaping, template/assets, and export modules.
- Consolidate profile schema construction and validation across CLI and GUI.
- Rename source-health fields to distinguish source failures from slow-query warnings, with migration.

Current progress:
- Report rendering has been split into focused HTML and Markdown modules while preserving compatibility wrappers in `job_radar/report.py`.
- Extracted modules now cover report safety, assets, text helpers, filtering, source warnings, tiers, matching, stats, profile/tracker summaries, manual links, job details, controls, job attributes, result tables, result rows, cards, and Markdown sections.
- GUI display formatting cleanup has started by moving saved-search panel loading/rows/feedback, Applications pipeline rows, follow-up queue rows, filters, and Applications export/import/edit feedback into view-model helpers.
- Applications tab construction now lives in a focused `job_radar/gui/applications_tab.py` helper while `MainWindow` retains behavior callbacks.
- Settings update status formatting now lives in `job_radar/gui/update_status_view_model.py`.
- Settings maintenance cache/app-data/dismissed-review feedback now lives in `job_radar/gui/maintenance_view_model.py`.
- Live source progress text now lives in `job_radar/gui/search_summary.py`, and GUI progress handlers normalize counters before updating progress bars.
- Search completion label/block text now lives in `job_radar/gui/search_summary.py`.
- Search idle profile-readiness guidance, recent/saved search panels, search progress, and search completion panel construction now live in `job_radar/gui/search_panel.py`.
- API credential test status formatting and HTTP response mapping now live in `job_radar/gui/api_status_view_model.py`.
- Installer launch prompt/status/error messages now live in `job_radar/gui/install_status_view_model.py`.
- Profile tab summary and readiness formatting now live in `job_radar/gui/profile_view_model.py`.
- Profile tab label/value row construction now lives in `job_radar/gui/profile_panel.py`.
- Profile dashboard next-step panel construction now lives in `job_radar/gui/dashboard_panel.py`.
- Latest validation: `1087 passed, 8 skipped`.

Validation:
- Full `pytest tests/`
- Focused behavior tests replacing brittle source-string assertions where possible.

## Sprint 4 - UX, Accessibility, And Product Polish

Goal: improve usability once trust, state, and architecture risks are under control.

- Make welcome/search/progress/completion/error views scroll-safe at minimum window size and OS text scaling.
- Rework Applications row actions so status, edits, and templates do not clip.
- Improve report offline status feedback and status-sync messaging.
- Review copy for macOS portable install paths, source counts, and feature claims.

Validation:
- GUI view-model tests.
- Targeted screenshot/manual checks at minimum and default window sizes.
- Documentation review against implemented behavior.
