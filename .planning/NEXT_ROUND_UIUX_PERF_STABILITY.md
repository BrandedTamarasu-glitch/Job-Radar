# Next Round Plan: UI/UX and Performance/Stability

Created: 2026-05-13

## Theme

Focus the next implementation round on making Job Radar feel more trustworthy under real daily use:

- clearer GUI feedback during slow, partial, cancelled, and empty searches
- bounded runtime behavior for slow or flaky sources
- easier-to-maintain report UI code
- long-term data maintenance for cache, tracker, and rate-limit state

## Sprint A: GUI Search Feedback & Recovery

Goal: make the desktop app explain what happened without requiring logs or report inspection.

Status: started. Worker completion messages now include a per-source run summary and source-warning metadata. The GUI completion state now renders partial source warnings, source job counts, and zero-result next actions. Cancelled and failed searches now have persistent states that explain whether a report was generated and offer clear retry/navigation controls.

- Show source warnings in the GUI completion state.
- Add a compact per-source run summary: attempted, succeeded, failed, job count.
- Improve cancel/error states so the user knows whether a report was generated, skipped, or partially generated.
- Add a no-results GUI state with the same next-action guidance used by CLI/report output.

Validation:
- Worker queue message tests for warning/summary payloads.
- GUI handler tests where practical.
- Manual smoke test for success, partial failure, cancellation, and zero results.

Accessibility:
- Do not rely on color alone.
- Keep status text screen-reader meaningful.
- Ensure dialogs/buttons are keyboard reachable and clearly labeled.

## Sprint B: Runtime Controls & Stability

Goal: prevent slow or flaky sources from making the app feel frozen.

Status: started. Fetch parallelism is centralized behind a validated `JOB_RADAR_MAX_WORKERS` runtime control while preserving the existing default. Request timeout propagation is available through a validated `JOB_RADAR_REQUEST_TIMEOUT` control in `fetch_with_retry`. Rate-limit SQLite state now lives under the platform app data path instead of the launch directory. Slow query warnings are recorded with `JOB_RADAR_SLOW_QUERY_SECONDS` and surfaced in generated reports.

- Add configurable fetch parallelism with a conservative default.
- Add configurable request timeout and propagate it into source fetches.
- Record slow query/source warnings in run stats and reports.
- Move persistent rate-limit SQLite state from the working directory to the platform app data path.

Validation:
- Tests for default/configured worker count.
- Tests for timeout propagation into `fetch_with_retry`.
- Tests for rate-limit storage path resolution.
- Full suite after storage-path changes.

Risks:
- Worker and timeout settings touch CLI, GUI, and source fetchers.
- Existing `.rate_limits` files may remain in old locations; avoid destructive migration in this sprint.

## Sprint C: Report UI Payload & Responsiveness

Goal: preserve current report features while reducing payload and maintenance risk.

Status: started. Unused Prism syntax-highlighting CSS/JS assets are removed from generated reports while preserving Bootstrap, Notyf, clipboard, status, filter, CSV, keyboard, and print behavior. A payload-size guard now catches unexpected growth for small reports. Large result tables now keep the first 20 rows visible and collapse lower-score rows behind a keyboard-operable disclosure. External report asset tags are centralized in focused helpers for easier payload review.

- Extract CSS/JS report generation into focused helper modules or template sections.
- Remove unused CDN assets if they are not required by report features.
- Add optional collapsed sections for lower-score results when result count is high.
- Add a report payload-size guard to catch accidental growth.

Validation:
- Existing report tests remain green.
- Targeted tests for extracted helpers.
- Browser smoke test for copy, status, filters, CSV export, keyboard shortcuts, and print.

Accessibility:
- Preserve skip link, focus states, aria labels, live announcements, and keyboard shortcuts.
- Collapsed sections must be keyboard operable.

## Sprint D: Tracker & Cache Maintenance

Goal: avoid hidden performance degradation for long-running users.

- [Done] Add conservative tracker pruning for old seen jobs.
- [Done] Add cache maintenance hooks for stale files.
- [Done] Add a visible cache clear path in CLI/GUI.
- [Done] Document storage locations for cache, tracker, and rate-limit data.

Validation:
- [Done] Tracker pruning boundary tests.
- [Done] Cache clear tests for missing and populated directories.
- [Done] Smoke test that old tracker data does not break report status hydration.

## Suggested Order

1. Sprint A: immediate user-trust improvement and reuses source-warning metadata already added.
2. Sprint B: bounds runtime behavior before broader report/UI refactors.
3. Sprint C: improves maintainability after behavior is clearer.
4. Sprint D: handles long-term performance once search-time behavior is stable.

## Success Criteria

- Users can see partial-search outcomes in the GUI.
- Slow/flaky sources are bounded by documented controls.
- Generated reports keep existing features while becoming easier to maintain.
- Long-term use does not steadily degrade from unbounded state files.
- Full test suite stays green after each sprint.
