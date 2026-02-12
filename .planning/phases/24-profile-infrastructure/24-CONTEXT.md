# Phase 24: Profile Infrastructure - Context

**Gathered:** 2026-02-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Centralize all profile read/write operations into a single `profile_manager.py` module with atomic writes, automatic timestamped backups, shared validation, and schema versioning. Wizard, quick-edit, and CLI flags all route through this module. No new user-facing features — this is internal infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Backup Storage & Naming
- Backups stored in a **subdirectory** next to the profile (e.g., `profiles/backups/`)
- Filenames use **human-readable timestamps** (e.g., `profile_2026-02-12_14-30-22.json`) so users can browse and find a specific backup by date
- User sees a **brief "Profile backed up" message** when a backup is created during save
- Backup rotation (deleting beyond 10) happens **silently** — no notification to user

### Validation Strictness
- **Unknown fields are preserved silently** — forward-compatible, won't break custom or future fields
- When validation fails on an existing profile during load, **warn and offer to re-run the setup wizard** to fix it
- Claude's Discretion: minimum required fields (based on what scoring engine needs) and whether to catch "probably wrong" vs "definitely wrong" values

### Error Messaging & Recovery
- Error messages use a **friendly, guiding tone** (e.g., "Your min_score of 7.0 is too high — it must be between 0.0 and 5.0.")
- If backup creation fails, **warn but continue with the save** — don't block the user's profile update
- Error messages **always include the file path** where the problem occurred for debugging
- Claude's Discretion: whether to show all validation errors at once or stop at the first one

### Migration Behavior
- Pre-v1.5.0 profiles (no schema_version) are **auto-saved after migration** so they're only migrated once
- Migration is **silent** — no notification to the user, it's an implementation detail
- Older versions of Job Radar **ignore unknown schema_version fields** — best-effort backward compatibility, don't error on newer schemas
- Normal auto-backup before save is sufficient for migration safety — **no extra migration-specific backup** needed

### Claude's Discretion
- Minimum required fields for a valid profile
- Strictness level (definitely wrong only vs probably wrong)
- Error grouping strategy (all errors vs first error)
- Exact backup message wording
- Exception hierarchy design (how many exception subclasses)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The existing `wizard._write_json_atomic()` pattern should be extracted and reused.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 24-profile-infrastructure*
*Context gathered: 2026-02-12*
