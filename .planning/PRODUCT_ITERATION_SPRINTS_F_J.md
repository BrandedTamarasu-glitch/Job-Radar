# Product Iteration Sprints F-J

Created: 2026-05-14

## Goal

Continue the post-v2.5.0 product iteration by making Job Radar easier to start, easier to reuse, more transparent in its ranking decisions, and sturdier under regular desktop use.

## Sprint F: Onboarding & First-Run Experience

Goal: help a new job seeker understand value quickly and create a useful first profile without trial and error.

- Add GUI access to the existing no-network demo report experience from both first-run onboarding and the Search tab.
- Add profile readiness checks for fields that strongly affect match quality.
- Ensure GUI-created profiles get the same default scoring and staffing settings as CLI wizard profiles.
- Surface profile-readiness guidance in the Search tab with a direct path back to Profile.
- Add profile-form field hints for titles, skills, location, compensation, and dealbreakers.
- Tailor GUI zero-result next actions with profile-readiness recommendations.
- Surface first-search guidance without requiring users to read docs first.
- Improve empty and incomplete profile states with concrete next actions.

Deliverable: a first-time user can preview a realistic report, create a stronger profile, and understand what to fix before running their first real search.

Status: complete. GUI onboarding now includes first-run demo report access, shared demo-report generation, profile readiness checks, Search tab readiness guidance, profile-form hints, GUI profile scoring defaults, and profile-aware zero-result next actions.

## Sprint G: Saved Searches & Search History

Goal: make repeated job searching fast and comparable.

- Add saved/recent search storage in the app data directory.
- Save named GUI searches with presets, source selections, filters, and freshness settings.
- Show recent searches and one-click rerun from the GUI.
- Track "new since last run" for saved searches.
- Add lightweight comparison between the last two runs for a saved search.

Deliverable: daily users can rerun targeted searches and immediately see what changed.

Status: in progress. Backend storage for recent search configs has started, successful GUI searches now record recent search configs without blocking search execution, the Search tab can reapply the latest recent searches, named saved-search storage is available, the Search tab can save/reapply named searches, GUI search completion records result metadata, and saved/recent searches display last-run summaries.

## Sprint H: Match Tuning & Explainability

Goal: give users practical control over ranking behavior without making them tune raw internals.

- Add GUI match-calibration presets such as broader, balanced, and strict.
- Explain lower-ranked and rejected jobs with concise reason summaries.
- Add profile quality checks tied to scoring signals.
- Expand regression fixtures for expected score bands across common role patterns.

Deliverable: users can understand and tune why jobs appear, rank, or get filtered.

## Sprint I: Application Workflow Upgrade

Goal: make the application pipeline useful after the search is complete.

- Add a stronger next-action queue across application statuses.
- Add application timeline details for status changes, notes, and follow-ups.
- Improve import/export behavior for application status portability.
- Add optional note templates for follow-up, recruiter response, and cover letter prep.

Deliverable: users can manage follow-through inside Job Radar instead of treating reports as one-off artifacts.

## Sprint J: Performance & Packaging Hardening

Goal: keep the app fast and trustworthy as usage and result volume grow.

- Tighten background-worker cancellation and progress boundaries.
- Improve report rendering for large result sets.
- Tune source timeouts, retries, and cache TTL defaults based on diagnostics.
- Add release artifact verification and clearer release-build failure diagnostics.

Deliverable: faster large searches, clearer build health, and fewer surprises in packaged desktop releases.

## Execution Order

Start with Sprint F because it improves first impression and lowers support burden. Then move to Sprint G to improve daily reuse, Sprint H to improve trust in matching, Sprint I to deepen follow-through value, and Sprint J to harden the product as usage grows.
