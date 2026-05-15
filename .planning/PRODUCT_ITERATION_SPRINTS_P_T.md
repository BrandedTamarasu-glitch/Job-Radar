# Product Iteration Sprints P-T

Created: 2026-05-15

## Goal

Make Job Radar easier to use as a daily command center: give users a clear next step when they open the app, deepen search and follow-up workflows, improve source trust, and keep larger local histories fast and explainable.

## Sprint P: Daily Dashboard & Next Steps

Goal: make the first authenticated screen answer "what should I do next?"

- Add a compact next-step panel driven by profile readiness, review queue counts, application follow-ups, and saved-search history.
- Link each recommendation to the relevant tab or workflow.
- Keep the panel useful with partial or missing local data.
- Avoid adding startup network work.

Deliverable: returning users can immediately see the highest-value next action without inspecting every tab.

Status: complete. Profile now includes a local next-step panel that prioritizes profile readiness, application follow-ups, review queue work, and saved/recent search shortcuts with tab navigation.

## Sprint Q: Search Comparison & Insight Recap

Goal: help users understand how the latest run changed their opportunity landscape.

- Show last-run deltas for total, new, high-score, and review-state counts.
- Highlight saved searches that have changed meaningfully since the previous run.
- Add clearer "why this search changed" copy for source failures, filters, and cache freshness.
- Keep summaries bounded for large histories.

Deliverable: users can decide whether a search needs attention before opening a full report.

Status: in progress. Saved searches now surface a bounded previous-run comparison line for total, new, high-score, and review-state movement.

## Sprint R: Follow-Up Workflow Automation

Goal: make application follow-up easier to run consistently.

- Add due-soon and overdue filters for the Applications tab.
- Add quick complete/snooze actions for next-action rows.
- Add optional calendar-friendly export for follow-up tasks.
- Preserve tracker timeline history for every automation action.

Deliverable: users can maintain follow-ups from a focused queue instead of scanning every application.

Status: planned.

## Sprint S: Source Quality & Coverage Controls

Goal: turn source diagnostics into practical search decisions.

- Add source reliability scoring over recent runs.
- Recommend source toggles when repeated failures or stale caches are detected.
- Expose coverage gaps by source and search preset.
- Keep diagnostics actionable without requiring logs.

Deliverable: users can tune source coverage confidently when job boards are noisy or degraded.

Status: planned.

## Sprint T: Local Performance & Maintenance Insights

Goal: keep large long-running installs predictable.

- Add visible local data size and history counts.
- Surface stale cache, tracker, review-state, and saved-search maintenance suggestions.
- Add focused tests for bounded dashboard summaries over large local datasets.
- Document maintenance behavior and privacy boundaries.

Deliverable: users understand what local state exists, how large it is, and when maintenance is useful.

Status: planned.

## Execution Order

Start with Sprint P because it improves the opening workflow and creates a reusable summary layer. Sprint Q builds on that summary layer for search history insights. Sprint R expands daily follow-up execution. Sprint S improves source trust once daily workflows are clearer. Sprint T closes the iteration with performance and maintenance visibility.
