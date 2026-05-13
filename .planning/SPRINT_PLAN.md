# Job Radar Refinement Sprint Plan

Created: 2026-05-13

## Goal

Refine Job Radar after the v2.2.0 release by first restoring project hygiene and reliability, then aligning documentation, and finally improving maintainability and product quality.

## Sprint 0: Baseline & Hygiene

Goal: make the repo coherent before changing behavior.

- Set up or confirm a local development environment.
- Install development dependencies with `pip install -e .[dev]`.
- Run `pytest tests/` and capture the baseline.
- Sync release metadata across `pyproject.toml`, `job_radar/__init__.py`, docs, and CLI output.
- Replace stale repository links with `BrandedTamarasu-glitch/Job-Radar`.
- Add a lightweight guard so version drift is caught by tests.

Deliverable: tests run locally, version metadata is consistent, and stale links are removed.

## Sprint 1: Reliability Fixes

Goal: remove obvious runtime hazards and environment-sensitive behavior.

- Fix the CLI source-progress callback mismatch so it accepts the same callback contract as the GUI.
- Reduce broad silent startup exception swallowing in `job_radar/__main__.py` by logging recoverable failures.
- Move HTTP response cache storage away from the current working directory and into the existing app data path.
- Add focused tests for callback compatibility, startup logging where practical, and cache path behavior.

Deliverable: safer CLI/GUI execution and cache behavior that works consistently in packaged desktop use.

## Sprint 2: Documentation Accuracy

Goal: make user-facing and maintainer docs match the application.

- Correct the FAQ scoring table to match the actual six scoring components and weights.
- Align source lists, version references, update behavior, and repository links across README, FAQ, WORKFLOW, installer docs, and CLI help.
- Add a concise developer validation section with setup, test, smoke-test, and release-check commands.

Deliverable: docs accurately describe v2.2.0 behavior and give maintainers a clear validation path.

## Sprint 3: Source Integration Cleanup

Goal: make job sources easier to maintain and debug.

- Introduce a source registry or lightweight `JobSource` interface.
- Replace long source dispatch branches in `fetch_all` while preserving behavior.
- Normalize source display names and progress accounting.
- Surface per-source failures in CLI, GUI, and reports without failing the whole search.

Status: in progress. The source registry is in place, `fetch_all()` no longer uses long dispatch branches, source display/progress accounting is normalized, and query failures are summarized for CLI/reporting consumers. Remaining work: deeper module extraction and richer GUI/report surfacing for partial source failures.

Deliverable: same search behavior with cleaner source architecture and better diagnostics.

## Sprint 4: Match Quality & Transparency

Goal: help job seekers understand and tune ranking decisions.

- Expand score explanations in reports.
- Show matched skills, missing important skills, title rationale, compensation uncertainty, and parse confidence notes.
- Improve dealbreaker matching with phrase and word-boundary handling.
- Add scoring regression fixtures with expected score bands.

Status: in progress. Skill scoring now reports missing core skills, and detailed Markdown/HTML reports show those missing skills so users can see why a role ranked lower without changing score math. Remaining work: richer title/compensation explanations, dealbreaker boundary handling, and scoring regression fixtures.

Deliverable: users can understand why a job ranked where it did.

## Sprint 5: Maintainability Refactor

Goal: reduce future change cost without rewriting the app.

- Split `gui/main_window.py` into focused GUI modules.
- Split `report.py` into Markdown, HTML, template, CSV, and status helpers.
- Split `sources.py` into API sources, scraper sources, and shared parsing utilities.
- Keep behavior stable with focused tests around each extraction.

Status: in progress. HTML report card detail rendering has been extracted into a shared helper used by both hero and recommended sections, reducing duplicated markup while preserving report output. Remaining work: broader report module extraction and GUI/source module splits.

Deliverable: smaller modules with the same external behavior.

## Sprint 6: Product Polish

Goal: improve first-run and daily-use value.

- Add a sample/demo mode so users can see a report without API keys.
- Improve zero-results explanations and suggested next actions.
- Add saved search presets for common target role/market combinations.

Status: in progress. Zero-result CLI output and generated reports now include concrete next actions for lowering thresholds, broadening titles/skills/location, and using manual check URLs. `--demo-report` now generates a sample report without profile setup, API keys, or live fetching. Remaining work: saved search presets.

Deliverable: smoother onboarding and better daily search workflow.

## Execution Order

Complete Sprint 0, Sprint 1, and Sprint 2 first. Those are low-risk and remove concrete inconsistencies. Sprint 3 and Sprint 4 should follow because they directly improve the core search and matching value. Sprint 5 and Sprint 6 are larger refinements once the foundation is stable.
