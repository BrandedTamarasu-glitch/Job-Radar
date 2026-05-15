# Product Iteration Sprints U-Y

Created: 2026-05-15

## Goal

Make Job Radar feel more like an adaptive job-search workspace: the app should prioritize the user's next move, reduce repeated manual cleanup, improve confidence in source choices, and prepare the completed product iteration for a release-quality checkpoint.

## Sprint U: Adaptive Command Center

Goal: make the opening dashboard respond to search, follow-up, source, and maintenance signals.

- Surface maintenance suggestions and source-quality issues in the Profile dashboard when they need attention.
- Keep dashboard recommendations bounded and actionable.
- Preserve no-network startup behavior.
- Keep navigation targets clear for each recommendation.

Deliverable: returning users can see operational issues and next actions from the first authenticated screen.

Status: complete. Profile dashboard recommendations surface local maintenance suggestions and source-quality issues that need attention.

## Sprint V: Workflow Shortcuts & Bulk Actions

Goal: reduce repeated manual work in search review and applications.

- Add bounded bulk actions for recurring review decisions.
- Add safer shortcuts for common application follow-up updates.
- Keep destructive or broad actions reversible or clearly scoped.
- Preserve tracker and review-state history.

Deliverable: users can process repeated workflow updates faster without losing control.

Status: complete. Review-state helpers now support bounded clearing by state, and Settings exposes a bounded dismissed-review cleanup shortcut.

## Sprint W: Source Strategy & Preset Intelligence

Goal: help users choose source coverage and presets based on recent outcomes.

- Recommend source/preset combinations from reliability, coverage, and result quality signals.
- Highlight stale or low-yield source choices before a run.
- Keep source recommendations understandable without requiring logs.
- Avoid disabling sources automatically.

Deliverable: users can choose better source coverage before spending time on a search.

Status: complete. Settings source diagnostics now include preset strategy recommendations from recent failures and low-yield or high-yield search outcomes, Search controls surface bounded pre-run source strategy guidance before reruns, both surfaces recommend specific sources to uncheck, broaden, or keep enabled, and source keys are normalized into readable names.

## Sprint X: Release Readiness & Regression Sweep

Goal: harden the accumulated product work before a release.

- Run broader automated validation and resolve regressions.
- Refresh release notes, README, workflow docs, and planning state.
- Verify build metadata, artifact expectations, and release scripts.
- Keep release checklist reproducible.

Deliverable: the next release candidate is documented, validated, and ready to package.

Status: complete. Release support validation passed for release artifact expectations, release notes, and metadata tests; full automated regression passed with 950 tests and 8 skips; Windows build script version/artifact drift was fixed; release notes were drafted in `.planning/RELEASE_NOTES_DRAFT_U_Y.md`; local Linux artifact build verification passed; `.planning/RELEASE_READINESS_U_Y.md` tracks the completed release-readiness checklist.

## Sprint Y: Post-Release Feedback Loop

Goal: make the next iteration easier to steer from real usage.

- Add lightweight feedback prompts or exported diagnostics users can share safely.
- Summarize completed iteration outcomes and remaining risks.
- Plan the next product slice from observed workflow gaps.
- Keep private local data out of exported diagnostics unless explicitly included by the user.

Deliverable: the project has a clean loop from release, feedback, and next planning.

Status: in progress. Sprint X release readiness is complete, and `.planning/POST_RELEASE_FEEDBACK_U_Y.md` now captures privacy-safe feedback fields, intake template, and next-iteration input buckets.

## Execution Order

Start with Sprint U because it turns the completed P-T maintenance/source work into daily guidance. Sprint V then accelerates repeated workflows. Sprint W improves source strategy before release hardening. Sprint X prepares the release candidate, and Sprint Y closes the loop for the next iteration.
