# v2.4 Product Iteration Plan

Created: 2026-05-13

## Theme

Make Job Radar easier to adopt, easier to steer, and more useful as a daily job-search workflow.

This round builds on the v2.3 stability work by moving beyond "generate a good report" toward a product loop:

- setup confidence before a user searches
- finer control over search scope and quality
- status and follow-up tracking after discovery
- transparent performance and source health
- faster report review on desktop and mobile

## Sprint A: First-Run & Setup Friction

Goal: make first successful use more predictable for non-technical users.

Deliverables:
- Add a post-profile setup health check that summarizes active sources, missing API keys, and rate-limited sources.
- Add GUI branching for "Run demo search" vs "Run real search" after onboarding.
- Improve PDF resume import review with clear missing-field prompts.
- Add Settings shortcuts to open app data and report folders.
- Document what a healthy setup looks like.

Validation:
- Tests for source health summary construction.
- GUI handler tests for setup shortcuts where practical.
- Manual smoke test for first-run profile creation, demo report, and real search.

Accessibility:
- Health status cannot rely on color alone.
- Folder/action buttons need clear accessible labels.

## Sprint B: Search Quality & Control

Goal: let users steer what gets searched without editing their profile for every run.

Status: started. CLI saved search presets already exist; GUI search controls now expose the same presets and the worker applies the selected preset before fetching, scoring, manual URL generation, and report rendering. GUI source checkboxes now allow per-search automated and manual source selection. Include/exclude company filters, must-have and nice-to-have skill controls, location strictness controls, and freshness presets are available per GUI search and apply before scoring/tracking.

Deliverables:
- [Done] Add saved search presets to GUI search controls.
- [Done] Add per-search source toggles for automated and manual sources.
- [Done] Add include/exclude company filters.
- [Done] Add must-have vs nice-to-have skill controls.
- [Done] Add location/remote strictness controls.
- [Done] Add freshness controls: 24h, 48h, 7d, custom.

Validation:
- [Done] Tests that GUI preset selection applies the same overlay as CLI presets.
- [Done] Source-toggle tests ensuring disabled sources are not queried or shown as searched.
- [Done] Scoring/search tests for must-have skills, nice-to-have skills, company filters, location strictness, and freshness presets.
- Full suite after each behavior slice.

Accessibility:
- Preset/source controls must be keyboard reachable.
- Disabled source state must be described in text, not color alone.

## Sprint C: Application Pipeline

Goal: support follow-through after discovery, not only search.

Status: started. Tracker persistence now supports application notes plus next-action and next-action date metadata while preserving existing status behavior. The GUI now includes a read-only Applications tab backed by status grouping, with CSV export available from the view. Reports can now use a config setting to hide rejected/skipped application statuses from future result lists.

Deliverables:
- [Read-only done] Add a dedicated GUI Applications view.
- [View-model done] Surface tracker statuses: Applied, Interviewing, Rejected, Offer.
- [Backend done] Add notes per job.
- [Backend done] Add next-action and date fields.
- [Backend done] Export application pipeline to CSV.
- [Backend done] Add a "hide rejected/skipped" setting for future reports.

Validation:
- [Done] Tracker persistence tests for notes and next actions.
- [Done] GUI view-model tests for grouped application statuses.
- [Done] CSV export tests.
- [Done] Tracker and GUI worker tests for hiding rejected/skipped report entries.

Accessibility:
- Application status controls need labels and keyboard operation.
- Notes and date fields must preserve focus order.

## Sprint D: Performance & Observability

Goal: make performance explainable and tunable as source coverage grows.

Status: started. GUI search completion summaries now include per-source elapsed timing from the worker progress callback, making slow sources visible after each run. The tracker now persists compact source health history across runs for future diagnostics. Cache hit/miss/write counters are now captured per fetch run and surfaced in GUI/CLI summaries. Settings now includes slowest-source diagnostics built from persisted source health history. Source fetchers now have source-specific cache TTLs. GUI cancellation now propagates into fetch execution boundaries so pending phases and unsubmitted source queries can stop earlier.

Deliverables:
- [Done] Add per-source timing to GUI completion summary.
- [Backend done] Add source health history across runs.
- [Done] Add cache hit/miss counters.
- [View-model/UI done] Add "slowest sources" diagnostics in Settings.
- [Backend done] Consider per-source cache TTLs.
- [Backend done] Improve cancellation propagation deeper into source fetches where practical.

Validation:
- [Done] Tests for GUI source timing summary formatting and worker aggregation.
- [Done] Tracker persistence tests for source health history.
- [Done] Tests for cache metric aggregation.
- [Done] Source diagnostics view-model tests.
- [Done] Cache TTL tests for custom expiry and source-specific values.
- [Done] Cancellation tests for source execution boundaries.
- Full suite and at least one manual slow-source smoke test.

Accessibility:
- Diagnostics should be plain text and not only visual charts.

## Sprint E: Report Review UX Upgrade

Goal: make the generated report faster to work through on desktop and mobile.

Status: started. Reports now include a shortlist state stored separately from application status, with per-job shortlist toggles and a Show Shortlist filter.

Deliverables:
- [Done] Add shortlist state separate from application status.
- Add keyboard navigation between job cards.
- Add compact/detail view toggle.
- Improve mobile layout for reviewing jobs on phone.
- Add a concise "why this matched" summary at the top of each card.
- Group missing-skill callouts by must-have and nice-to-have.

Validation:
- [Done] Report tests for shortlist persistence and filtering.
- Keyboard shortcut tests for navigation behavior.
- Mobile/report layout smoke checks where practical.

Accessibility:
- Preserve skip link, focus indicators, live announcements, and semantic headings.
- Compact/detail toggle must announce state.

## Suggested Order

1. Sprint B: immediate improvement to daily search steering.
2. Sprint A: improve first-run confidence once search controls are clearer.
3. Sprint C: add follow-through workflow after discovery.
4. Sprint D: deepen performance visibility as more controls and history exist.
5. Sprint E: refine the report review surface after workflow shape is clearer.

## Success Criteria

- Users can run common search modes from the GUI without editing their profile.
- Users can choose source scope and freshness from the search screen.
- Users can track application follow-through inside the app.
- Users can understand which sources are slow, failing, cached, or rate-limited.
- Reports are faster to review and easier to use on mobile.
- Full test suite stays green after each sprint.
