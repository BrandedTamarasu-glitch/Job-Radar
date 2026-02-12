# Requirements: Job Radar v1.5.0

**Defined:** 2026-02-11
**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters

## v1.5.0 Requirements

Requirements for Profile Management & Workflow Efficiency milestone.

### Profile Viewing

- [ ] **VIEW-01**: User can see profile preview automatically on search startup showing all current settings
- [ ] **VIEW-02**: User can manually view profile with `job-radar --view-profile` command
- [ ] **VIEW-03**: Profile display uses formatted table layout with clear section headers
- [ ] **VIEW-04**: Profile preview respects `--no-wizard` flag to disable automatic display
- [ ] **VIEW-05**: Help text documents all profile management commands and flags

### Profile Updates

- [ ] **EDIT-01**: User can enter quick-edit mode to update a single profile field interactively
- [ ] **EDIT-02**: User can select which field to edit from a menu (name, skills, titles, experience, location, dealbreakers, min_score, new_only)
- [ ] **EDIT-03**: User sees before/after diff preview for all profile changes before saving
- [ ] **EDIT-04**: User must confirm changes before profile is updated
- [ ] **EDIT-05**: User can update skills list via `--update-skills` CLI flag (comma-separated)
- [ ] **EDIT-06**: User can set minimum score via `--set-min-score` CLI flag (0.0-5.0 range)
- [ ] **EDIT-07**: CLI flag updates exit after update without running search (early exit pattern)
- [ ] **EDIT-08**: All update methods validate input before saving (reuse wizard validators)

### Data Safety & Infrastructure

- [ ] **SAFE-01**: Profile writes use atomic operations (temp file + rename) to prevent corruption
- [ ] **SAFE-02**: System creates automatic timestamped backup before each profile update
- [ ] **SAFE-03**: System maintains last 10 backups and deletes older backups automatically
- [ ] **SAFE-04**: Profile includes `schema_version` field (set to 1 for v1.5.0)
- [ ] **SAFE-05**: Profile validation is shared between wizard, quick-edit, and CLI flags (single source of truth)
- [ ] **SAFE-06**: Profile manager module centralizes all profile I/O operations
- [ ] **SAFE-07**: Invalid profile updates are rejected with clear error messages
- [ ] **SAFE-08**: Profile atomic write pattern is extracted from `wizard._write_json_atomic()` for reuse

## Future Requirements

Deferred to v1.6.0+. Tracked but not in current roadmap.

### Profile Recovery

- **RECOV-01**: User can restore profile from backup with `--restore-profile` command
- **RECOV-02**: User can list available backups before restoring

### Advanced Updates

- **UPDT-01**: User can add dealbreakers via `--add-dealbreaker` CLI flag
- **UPDT-02**: User can remove dealbreakers via `--remove-dealbreaker` CLI flag
- **UPDT-03**: User can toggle new-only mode via `--new-only` flag (already exists, but profile persistence is future)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Multiple profiles support | Context switching pattern unclear for job search use case; wait for user validation |
| Profile export/import | No collaboration use case identified yet; defer until sharing need emerges |
| Undo last change | Complex for v1; wait for actual user mistakes in the wild before investing |
| Profile templates | Premature; need more profile usage data to identify common patterns |
| Cloud sync | Job Radar is privacy-focused and offline-first by design |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SAFE-01 | Phase 24 | Pending |
| SAFE-02 | Phase 24 | Pending |
| SAFE-03 | Phase 24 | Pending |
| SAFE-04 | Phase 24 | Pending |
| SAFE-05 | Phase 24 | Pending |
| SAFE-06 | Phase 24 | Pending |
| SAFE-07 | Phase 24 | Pending |
| SAFE-08 | Phase 24 | Pending |
| VIEW-01 | Phase 25 | Pending |
| VIEW-02 | Phase 25 | Pending |
| VIEW-03 | Phase 25 | Pending |
| VIEW-04 | Phase 25 | Pending |
| VIEW-05 | Phase 25 | Pending |
| EDIT-01 | Phase 26 | Pending |
| EDIT-02 | Phase 26 | Pending |
| EDIT-03 | Phase 26 | Pending |
| EDIT-04 | Phase 26 | Pending |
| EDIT-08 | Phase 26 | Pending |
| EDIT-05 | Phase 27 | Pending |
| EDIT-06 | Phase 27 | Pending |
| EDIT-07 | Phase 27 | Pending |

**Coverage:**
- v1.5.0 requirements: 21 total
- Mapped to phases: 21/21
- Unmapped: 0

---
*Requirements defined: 2026-02-11*
*Last updated: 2026-02-11 after roadmap creation (all requirements mapped)*
