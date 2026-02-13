# Phase 33: Scoring Configuration Backend - Context

**Gathered:** 2026-02-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Add user-customizable scoring weights to the profile schema with backward-compatible v1→v2 migration. Existing profiles auto-migrate without data loss. Scoring engine accepts optional weights parameter. No GUI changes (Phase 34). No new source scoring (Phase 35).

</domain>

<decisions>
## Implementation Decisions

### Weight Defaults & Ranges
- All 6 scoring components are user-adjustable
- Weights must sum to 1.0 (normalized percentages)
- Minimum weight per component: 0.05 (prevents accidentally disabling a component)
- Default weights must reproduce identical scores to current hardcoded behavior — score stability is critical on upgrade
- Users can later adjust to equal weights if they want, but migration must not change scores

### Migration Behavior
- Migration triggers automatically on first profile load — user doesn't notice
- Always create a backup of the v1 profile before migrating (e.g., profile_v1_backup.json)
- Score stability is CRITICAL: default v2 weights must exactly reproduce current hardcoded scoring behavior — no score changes on upgrade
- On corrupted/unexpected profile structure: add default scoring_weights, log warning, keep running — don't block the user (graceful fallback)

### Staffing Firm Preference Model
- Three fixed presets: Boost, Neutral, Penalize (specific point values — not user-adjustable beyond these three)
- NEW default is Neutral (0) — staffing firms treated same as direct employers by default (changed from current +4.5 boost)
- Note: This is a deliberate default change — new installs and migrated profiles get neutral, not the old boost

### Schema Structure
- Add explicit schema version field: "schema_version": 2 (enables future migrations)
- Detect v1 profiles by absence of schema_version field
- Add scoring weight questions to CLI wizard (not GUI-only — terminal users need access too)

### Claude's Discretion
- Whether scoring_weights is a nested object or flat keys in profile JSON
- Whether staffing_preference lives inside scoring_weights or as a separate top-level field
- Whether staffing firm preference is part of the 6 weights (making it 7) or a separate post-scoring adjustment
- Whether changing staffing preference recomputes from cache or requires re-run
- Exact numeric values for Boost/Neutral/Penalize presets
- How to determine current hardcoded weights to use as migration defaults
- Migration implementation details (profile_manager.py changes)

</decisions>

<specifics>
## Specific Ideas

- Score stability on migration is the #1 priority — if a user upgrades and their scores change, that's a trust-breaking bug
- The shift from +4.5 staffing boost to neutral (0) is intentional — most users reported staffing firms ranking too high
- Minimum weight of 0.05 prevents users from accidentally creating a scoring system that ignores important signals

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 33-scoring-configuration-backend*
*Context gathered: 2026-02-13*
