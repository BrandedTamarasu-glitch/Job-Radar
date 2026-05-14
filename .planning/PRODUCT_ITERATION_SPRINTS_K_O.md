# Product Iteration Sprints K-O

Created: 2026-05-14

## Goal

Continue improving Job Radar as a daily job-search workspace: make common actions editable from the GUI, reduce repeated setup, improve search review, expose source health clearly, and keep release/update trust high as the product grows.

## Sprint K: Application Editing & Templates

Goal: make the application tracker feel editable and useful directly from the desktop app.

- Add GUI controls for updating application status, next action, due date, and notes without leaving the Applications tab.
- Add template insertion for follow-up, recruiter response, and cover-letter prep notes.
- Preserve timeline history for every GUI edit.
- Keep CSV import/export compatible with the richer tracker data.

Deliverable: users can manage follow-up details from the GUI with fewer manual file edits.

Status: in progress.

## Sprint L: Search Review Workspace

Goal: make search results easier to triage after a run.

- Add shortlist, dismiss, and maybe-later review states to search results.
- Carry review state into reports and saved-search comparisons.
- Add bulk actions for visible result groups.
- Keep report payloads bounded for large searches.

Deliverable: users can quickly turn a search result list into a practical review queue.

Status: pending.

## Sprint M: Source Health Controls

Goal: give users clearer control over unreliable or slow job sources.

- Show per-source health and last-error summaries in the GUI.
- Add temporary disable and retry controls for noisy sources.
- Surface cache age and freshness decisions near search controls.
- Keep diagnostics useful for support and release validation.

Deliverable: users can understand source failures and keep searching without restarting or editing config files.

Status: pending.

## Sprint N: Data Portability & Recovery

Goal: make local data safer and easier to move between machines.

- Add GUI import/export flows for profiles, application tracker data, saved searches, and settings.
- Add backup restore affordances for profile and tracker data.
- Validate imports before mutating local state.
- Document recovery paths for common support cases.

Deliverable: users can back up, migrate, and recover Job Radar data confidently.

Status: pending.

## Sprint O: Performance & Release Trust

Goal: keep large daily workflows responsive and make releases easier to verify.

- Profile the largest GUI/report paths and reduce avoidable work.
- Add focused regression tests for long-running search cancellation and large report rendering.
- Expand release notes and artifact verification docs around supported platforms.
- Improve build-failure diagnostics when artifact names, permissions, or installer outputs drift.

Deliverable: the app remains responsive under larger local datasets and release failures are easier to diagnose.

Status: pending.

## Execution Order

Start with Sprint K because application editing builds directly on the completed tracker queue, timeline, import/export, and templates. Then move to Sprint L to improve daily review workflows, Sprint M to make source reliability visible, Sprint N to protect user data, and Sprint O to harden performance and release operations after the next set of product surfaces lands.
