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

Status: started. CLI saved search presets already exist; GUI search controls now expose the same presets and the worker applies the selected preset before fetching, scoring, manual URL generation, and report rendering. GUI source checkboxes now allow per-search automated source selection. Include/exclude company filters are available per GUI search and apply before scoring/tracking.

Deliverables:
- [Done] Add saved search presets to GUI search controls.
- [Partial] Add per-search source toggles for automated and manual sources. Automated source toggles are implemented; manual source toggles remain.
- [Done] Add include/exclude company filters.
- Add must-have vs nice-to-have skill controls.
- Add location/remote strictness controls.
- Add freshness controls: 24h, 48h, 7d, custom.

Validation:
- [Done] Tests that GUI preset selection applies the same overlay as CLI presets.
- [Partial] Source-toggle tests ensuring disabled sources are not queried or shown as searched.
- [Partial] Scoring/search tests for must-have skills and company filters. Company filter tests are implemented.
- Full suite after each behavior slice.

Accessibility:
- Preset/source controls must be keyboard reachable.
- Disabled source state must be described in text, not color alone.

## Sprint C: Application Pipeline

Goal: support follow-through after discovery, not only search.

Deliverables:
- Add a dedicated GUI Applications view.
- Surface tracker statuses: Applied, Interviewing, Rejected, Offer.
- Add notes per job.
- Add next-action and date fields.
- Export application pipeline to CSV.
- Add a "hide rejected/skipped" setting for future reports.

Validation:
- Tracker persistence tests for notes and next actions.
- GUI view-model tests for grouped application statuses.
- CSV export tests.

Accessibility:
- Application status controls need labels and keyboard operation.
- Notes and date fields must preserve focus order.

## Sprint D: Performance & Observability

Goal: make performance explainable and tunable as source coverage grows.

Deliverables:
- Add per-source timing to GUI completion summary.
- Add source health history across runs.
- Add cache hit/miss counters.
- Add "slowest sources" diagnostics in Settings.
- Consider per-source cache TTLs.
- Improve cancellation propagation deeper into source fetches where practical.

Validation:
- Tests for timing and cache metric aggregation.
- Cancellation tests for source execution boundaries.
- Full suite and at least one manual slow-source smoke test.

Accessibility:
- Diagnostics should be plain text and not only visual charts.

## Sprint E: Report Review UX Upgrade

Goal: make the generated report faster to work through on desktop and mobile.

Deliverables:
- Add shortlist state separate from application status.
- Add keyboard navigation between job cards.
- Add compact/detail view toggle.
- Improve mobile layout for reviewing jobs on phone.
- Add a concise "why this matched" summary at the top of each card.
- Group missing-skill callouts by must-have and nice-to-have.

Validation:
- Report tests for shortlist persistence and filtering.
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
