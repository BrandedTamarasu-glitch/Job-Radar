# Release Readiness: Product Iteration U-Y

Created: 2026-05-15

## Scope

This checklist tracks the release-readiness sweep for Product Iteration U-Y after the adaptive dashboard, workflow shortcuts, and source strategy work.

## Checkpoints

- [x] Sprint W source strategy validation
  - Command: `rtk .venv/bin/python -m pytest tests/test_source_diagnostics_view_model.py tests/test_gui_onboarding.py tests/test_gui_search_summary.py -q`
  - Result: 81 passed
  - Coverage: source/preset diagnostics, source-selection recommendations, Search tab pre-run guidance, source-name normalization, GUI onboarding wiring, and GUI search summary context.

- [x] Release support validation
  - Command: `rtk .venv/bin/python -m pytest tests/test_release_verification.py tests/test_release_notes.py tests/test_metadata.py -q`
  - Result: 19 passed
  - Coverage: release artifact expectations, release-note generation, clean release-note CLI failures, runtime/package version sync, and build metadata derivation.

- [x] Combined focused release checkpoint
  - Command: `rtk .venv/bin/python -m pytest tests/test_source_diagnostics_view_model.py tests/test_gui_onboarding.py tests/test_gui_search_summary.py tests/test_release_verification.py tests/test_release_notes.py tests/test_metadata.py -q`
  - Result: 100 passed
  - Coverage: Sprint W user-facing source strategy plus Sprint X release support checks in one pass.

- [x] Broader regression sweep
  - Command: `rtk .venv/bin/python -m pytest -q`
  - Result: 950 passed, 8 skipped
  - Coverage: full automated suite before packaging or tagging.

- [x] Documentation refresh
  - Confirm README, changelog, roadmap, and project state reflect the final U-Y scope.
  - Confirm release notes summarize user-facing changes without exposing local private data.
  - Draft: `.planning/RELEASE_NOTES_DRAFT_U_Y.md`

- [x] Build verification
  - [x] Build script metadata check
    - Command: `rtk .venv/bin/python -m pytest tests/test_metadata.py tests/test_release_verification.py -q`
    - Result: 13 passed
    - Additional check: `bash -n scripts/build.sh`
    - Result: passed
    - Coverage: Unix and Windows build scripts derive versions from package metadata, emit expected release artifact/checksum names, and call release artifact verification.
  - [x] Artifact build check
    - Command: `PYTHON_BIN=.venv/bin/python bash scripts/build.sh`
    - Result: passed; release verification accepted `dist/job-radar/job-radar` and `job-radar-v2.7.0-linux.tar.gz`
    - Binary check: `./dist/job-radar/job-radar --version` returned `job-radar 2.7.0`
    - Checksum manifest: `job-radar-v2.7.0-linux.sha256`
    - Note: PyInstaller emitted non-fatal CustomTkinter font-copy warnings from a read-only home font directory, then completed successfully.

## Current Status

Sprint X is complete. Focused release support validation, full regression, documentation refresh, build-script metadata verification, and local Linux artifact build verification have passed.
