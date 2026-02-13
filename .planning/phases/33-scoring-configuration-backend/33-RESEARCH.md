# Phase 33: Scoring Configuration Backend - Research

**Researched:** 2026-02-13
**Domain:** JSON schema migration, profile data versioning, backward compatibility
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Weight Defaults & Ranges**
- All 6 scoring components are user-adjustable
- Weights must sum to 1.0 (normalized percentages)
- Minimum weight per component: 0.05 (prevents accidentally disabling a component)
- Default weights must reproduce identical scores to current hardcoded behavior — score stability is critical on upgrade
- Users can later adjust to equal weights if they want, but migration must not change scores

**Migration Behavior**
- Migration triggers automatically on first profile load — user doesn't notice
- Always create a backup of the v1 profile before migrating (e.g., profile_v1_backup.json)
- Score stability is CRITICAL: default v2 weights must exactly reproduce current hardcoded scoring behavior — no score changes on upgrade
- On corrupted/unexpected profile structure: add default scoring_weights, log warning, keep running — don't block the user (graceful fallback)

**Staffing Firm Preference Model**
- Three fixed presets: Boost, Neutral, Penalize (specific point values — not user-adjustable beyond these three)
- NEW default is Neutral (0) — staffing firms treated same as direct employers by default (changed from current +4.5 boost)
- Note: This is a deliberate default change — new installs and migrated profiles get neutral, not the old boost

**Schema Structure**
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

## Summary

Phase 33 adds user-customizable scoring weights to the profile schema with backward-compatible v1→v2 migration. The existing profile infrastructure (profile_manager.py) already handles schema versioning (v0→v1 for pre-1.5.0 profiles), atomic writes, automatic backups, and validation. This phase extends that pattern to v1→v2 migration, adding scoring_weights and staffing_preference fields while maintaining score stability for existing users.

**Critical constraint:** Default v2 weights MUST exactly reproduce current hardcoded scoring behavior. The current weights from scoring.py lines 47-54 are: skill_match(0.25), title_relevance(0.15), seniority(0.15), location(0.15), domain(0.10), response_likelihood(0.20). These sum to 1.0 and must be preserved byte-for-byte in the migration.

**Staffing firm handling:** Currently hardcoded at +4.5 boost (scoring.py line 502). The new default is Neutral (0), representing a deliberate product change. This is NOT score-stability-breaking because it's a new optional feature with documented behavior change.

**Primary recommendation:** Extend profile_manager.py with v1→v2 migration following the existing v0→v1 pattern. Add nested scoring_weights object (cleaner than flat keys, groups related config). Keep staffing_preference separate (it's a post-scoring adjustment, not a weight). Implement fallback defaults in scoring.py for graceful degradation. Add CLI wizard questions for new profiles only (migration uses defaults).

## Standard Stack

### Core (Already in Project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib json | - | Profile serialization | Already used; profile_manager.py line 4 |
| Python stdlib pathlib | - | File operations | Already used; profile_manager.py line 8 |
| Python stdlib logging | - | Migration warnings | Already used; profile_manager.py line 12 |
| questionary | latest | CLI wizard prompts | Already used; wizard.py imports |

### Supporting (No New Dependencies)

All required functionality exists in current codebase. No new dependencies needed.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Nested scoring_weights object | Flat profile keys (skill_match_weight, etc.) | Nested groups related config, easier to validate "sum to 1.0", cleaner JSON structure |
| Separate staffing_preference field | Add as 7th weight | Staffing preference is post-scoring adjustment (add/subtract points), not a weighted component — mixing concerns |
| Auto-migrate on load | Require manual migration | Auto-migration already proven pattern (v0→v1 works well), user doesn't notice upgrade |
| Store weights in config.json | Store in profile.json | Weights are profile-specific (user may want different weights for different job searches), not global config |

**Installation:**

No new dependencies required.

## Architecture Patterns

### Pattern 1: Schema Version Bump with Migration Function

**What:** Increment CURRENT_SCHEMA_VERSION from 1 to 2, add migration case in load_profile()

**When to use:** Any breaking schema change (adding required structure, changing defaults)

**Example:**
```python
# Source: Existing profile_manager.py lines 267-273 + PITFALLS.md lines 17-34
# In profile_manager.py:

CURRENT_SCHEMA_VERSION = 2  # Was 1, bump to 2

def load_profile(profile_path: Path) -> dict:
    """Load, migrate, validate, and return a profile dict."""
    if not profile_path.exists():
        raise ProfileNotFoundError(profile_path)

    try:
        with open(profile_path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        raise ProfileCorruptedError(profile_path, str(e)) from e

    # Schema migration
    schema_version = profile.get("schema_version", 0)

    if schema_version == 0:
        # Pre-v1.5.0 profile -- add schema_version and auto-save
        profile["schema_version"] = CURRENT_SCHEMA_VERSION
        save_profile(profile, profile_path)
    elif schema_version == 1:
        # v1 → v2: Add scoring weights with defaults matching current hardcoded behavior
        profile["scoring_weights"] = {
            "skill_match": 0.25,
            "title_relevance": 0.15,
            "seniority": 0.15,
            "location": 0.15,
            "domain": 0.10,
            "response_likelihood": 0.20,
        }
        # NEW default: neutral staffing preference (changed from +4.5)
        profile["staffing_preference"] = "neutral"
        profile["schema_version"] = 2
        save_profile(profile, profile_path)
    # schema_version > CURRENT_SCHEMA_VERSION: ignore silently (best-effort)

    validate_profile(profile)
    return profile
```

### Pattern 2: Graceful Fallback in Scoring Engine

**What:** Use .get() with defaults instead of assuming fields exist

**When to use:** When consuming migrated fields (defense-in-depth)

**Example:**
```python
# Source: Existing scoring.py pattern + PITFALLS.md lines 273-276
# In scoring.py score_job():

def score_job(job, profile: dict) -> dict:
    """Score a job result against a candidate profile.

    Returns a dict with overall score (1.0-5.0) and component breakdowns.
    """
    # Check dealbreakers first
    dealbreaker_hit = _check_dealbreakers(job, profile)
    if dealbreaker_hit:
        return {
            "overall": 0.0,
            "components": {},
            "recommendation": "Dealbreaker",
            "dealbreaker": dealbreaker_hit,
        }

    scores = {}

    # 1. Skill match
    scores["skill_match"] = _score_skill_match(job, profile)
    # ... other components ...

    # Get weights with fallback to hardcoded defaults (defense-in-depth)
    weights = profile.get("scoring_weights", {
        "skill_match": 0.25,
        "title_relevance": 0.15,
        "seniority": 0.15,
        "location": 0.15,
        "domain": 0.10,
        "response_likelihood": 0.20,
    })

    # Weighted total using configurable weights
    overall = (
        scores["skill_match"]["score"] * weights["skill_match"]
        + scores["title_relevance"]["score"] * weights["title_relevance"]
        + scores["seniority"]["score"] * weights["seniority"]
        + scores["location"]["score"] * weights["location"]
        + scores["domain"]["score"] * weights["domain"]
        + scores["response"]["score"] * weights["response_likelihood"]
    )

    # Apply staffing firm preference (post-scoring adjustment)
    staffing_pref = profile.get("staffing_preference", "neutral")
    if is_staffing_firm(job.company):
        if staffing_pref == "boost":
            overall = min(5.0, overall + 0.5)  # +0.5 boost
            scores["staffing_note"] = "Staffing firm (boosted)"
        elif staffing_pref == "penalize":
            overall = max(1.0, overall - 1.0)  # -1.0 penalty
            scores["staffing_note"] = "Staffing firm (penalized)"
        # "neutral" = no adjustment

    # ... rest of scoring logic (comp penalty, parse confidence) ...

    return {
        "overall": round(overall, 1),
        "components": scores,
        "recommendation": _recommendation(overall),
    }
```

### Pattern 3: Validation with Sum-to-1.0 Check

**What:** Extend validate_profile() to check scoring_weights structure and sum

**When to use:** Before saving profile (catch user errors early)

**Example:**
```python
# Source: Existing profile_manager.py validate_profile() + user constraints
# In profile_manager.py:

def validate_profile(profile: dict) -> None:
    """Validate profile structure and field constraints.

    Checks required fields, types, and value ranges. Raises a
    ProfileValidationError subclass on the first problem found.
    """
    # ... existing validation (lines 78-141) ...

    # Scoring weights validation (v2+ profiles)
    if "scoring_weights" in profile:
        weights = profile["scoring_weights"]
        if not isinstance(weights, dict):
            raise InvalidTypeError("scoring_weights", "dict", type(weights))

        # Check all 6 components present
        required_components = [
            "skill_match", "title_relevance", "seniority",
            "location", "domain", "response_likelihood"
        ]
        missing = [c for c in required_components if c not in weights]
        if missing:
            raise MissingFieldError([f"scoring_weights.{c}" for c in missing])

        # Check each weight is valid number in range [0.05, 1.0]
        for component, weight in weights.items():
            if not isinstance(weight, (int, float)):
                raise InvalidTypeError(
                    f"scoring_weights.{component}", "number", type(weight)
                )
            if not (0.05 <= weight <= 1.0):
                raise ProfileValidationError(
                    f"Weight '{component}' must be between 0.05 and 1.0, got {weight}"
                )

        # Check weights sum to 1.0 (allow 0.01 tolerance for float precision)
        total = sum(weights.values())
        if not (0.99 <= total <= 1.01):
            raise ProfileValidationError(
                f"Scoring weights must sum to 1.0, got {total:.3f}. "
                f"Current: {weights}"
            )

    # Staffing preference validation (v2+ profiles)
    if "staffing_preference" in profile:
        pref = profile["staffing_preference"]
        valid_prefs = ["boost", "neutral", "penalize"]
        if pref not in valid_prefs:
            raise ProfileValidationError(
                f"staffing_preference must be one of {valid_prefs}, got '{pref}'"
            )
```

### Pattern 4: Wizard Questions for New Profiles

**What:** Add scoring weight questions to CLI wizard (default to standard weights)

**When to use:** First-run setup wizard only (migrations use defaults)

**Example:**
```python
# Source: Existing wizard.py questions pattern (lines 189-281)
# Add to wizard.py questions list (after dealbreakers, before min_score):

questions = [
    # ... existing questions ...
    {
        'key': 'scoring_weights_custom',
        'type': 'confirm',
        'message': "Customize scoring component weights?",
        'instruction': "Advanced: adjust how much each factor (skills, title, etc.) affects job scores",
        'validator': None,
        'required': True,
        'default': False,  # Most users use defaults
    },
    # If user says yes, ask for each weight
    # If no, skip and use defaults in profile_data construction
]

# In profile_data construction (after dealbreakers):
if answers.get('scoring_weights_custom'):
    # Prompt for 6 weights, validate sum to 1.0
    # (Implementation deferred to planning phase)
    pass
else:
    # Use defaults matching current hardcoded behavior
    profile_data["scoring_weights"] = {
        "skill_match": 0.25,
        "title_relevance": 0.15,
        "seniority": 0.15,
        "location": 0.15,
        "domain": 0.10,
        "response_likelihood": 0.20,
    }

# Staffing preference (always ask, simpler than weights)
staffing_choice = questionary.select(
    "How should staffing firms be scored?",
    choices=[
        "Neutral (treat same as direct employers)",
        "Boost (prefer staffing firms)",
        "Penalize (avoid staffing firms)",
    ],
    default="Neutral (treat same as direct employers)",
    style=custom_style
).ask()

if "Boost" in staffing_choice:
    profile_data["staffing_preference"] = "boost"
elif "Penalize" in staffing_choice:
    profile_data["staffing_preference"] = "penalize"
else:
    profile_data["staffing_preference"] = "neutral"
```

### Anti-Patterns to Avoid

- **Skip schema version bump:** Adding scoring_weights without bumping CURRENT_SCHEMA_VERSION from 1 to 2 causes KeyError crashes when scoring.py expects the new structure (PITFALLS.md lines 9-41)
- **Change default weights from current behavior:** Using different default values (e.g., equal 0.167 for all 6) breaks score stability — users see different scores after upgrade with no explanation (user constraints mandate reproduction of current hardcoded values)
- **Store weights in config.json instead of profile.json:** Breaks multi-profile workflows where user wants different weights for different job searches (weights are profile-specific, not global config)
- **Make staffing preference a 7th weight:** Staffing preference is a post-scoring adjustment (add/subtract points after weighted sum), not a component weight — mixing concerns makes sum-to-1.0 validation confusing

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON schema migration | Custom migration framework with version mappings | Direct if/elif chain by schema_version | Only 3 versions (0, 1, 2) — framework overhead not justified. Existing v0→v1 works well. |
| Backup file rotation | Cron job or separate cleanup script | Inline rotation after backup creation | Already implemented in profile_manager.py (lines 170-186). Keep it simple. |
| Weight validation | Regex or custom parser | isinstance() + range checks | Weights are simple floats. stdlib validation sufficient. |
| Atomic file writes | Manual open/write/rename | tempfile.mkstemp() + os.fsync() + Path.replace() | Already proven in wizard.py. Don't reinvent. |

**Key insight:** The codebase already has robust patterns for profile I/O, schema migration, and validation. Phase 33 extends existing patterns, not replaces them. Don't introduce new libraries or frameworks.

## Common Pitfalls

### Pitfall 1: Forgetting to Bump Schema Version

**What goes wrong:** Adding scoring_weights to profile without changing CURRENT_SCHEMA_VERSION from 1 to 2. Old profiles load without migration, scoring.py crashes with KeyError when accessing profile["scoring_weights"].

**Why it happens:** Developers think "it's just adding optional fields" and skip version bump. But scoring.py changes from hardcoded weights to reading profile weights — this IS a breaking change.

**How to avoid:**
1. ALWAYS bump CURRENT_SCHEMA_VERSION when adding new profile structure
2. Add migration case in load_profile() before releasing
3. Use .get() with defaults in scoring.py as defense-in-depth
4. Test: Load v1 profile, verify auto-migration, verify scores unchanged

**Warning signs:**
- Tests pass but app crashes with KeyError on real profiles
- User reports "worked fine before update, now crashes on search"
- Old profiles load but scores are all wrong

**Source:** PITFALLS.md lines 9-41

### Pitfall 2: Default Weights Don't Match Current Behavior

**What goes wrong:** Migration uses different default weights than current hardcoded values (e.g., equal 0.167 for all 6 components). Users upgrade to v2.1, suddenly all their scores change. Reports become incomparable across versions.

**Why it happens:** Developer thinks "equal weights are simpler/fairer" and doesn't check current hardcoded values in scoring.py lines 47-54.

**How to avoid:**
1. Extract current weights from scoring.py into named constant
2. Use SAME values in migration and scoring.py fallback
3. Document: "Default weights preserve current behavior"
4. Test: Score same job with v1 profile vs freshly-migrated v2 profile, assert scores identical

**Warning signs:**
- User reports "all my scores dropped after update"
- Reports show different scores for same job across runs
- No code changes to scoring logic but scores change

**Source:** User constraints + scoring.py lines 47-54

### Pitfall 3: Not Creating Backup Before Migration

**What goes wrong:** Auto-migration fails partway through (write error, validation failure). Original v1 profile corrupted. User loses data.

**Why it happens:** Migration calls save_profile() which creates backup, but only if profile_path.exists() (profile_manager.py line 236). If profile loaded from non-standard location, backup fails silently.

**How to avoid:**
1. Verify backup creation in migration test
2. Log backup path: "Profile backed up to {backup_path}"
3. On backup failure, log warning but continue migration (user decision)
4. Test: Simulate disk full during migration, verify graceful handling

**Warning signs:**
- Migration logs show "Could not create backup" warnings
- User reports "profile reset after update"
- Backup directory empty after migration

**Source:** profile_manager.py lines 147-167 + user constraints

### Pitfall 4: Staffing Firm Preference Breaks Existing Logic

**What goes wrong:** Adding staffing_preference field conflicts with existing is_staffing_firm() boost in _score_response_likelihood() (scoring.py line 502). Users get DOUBLE boost (+4.5 from old code, +0.5 from new preference).

**Why it happens:** Old hardcoded boost not removed when adding configurable preference. Both code paths execute.

**How to avoid:**
1. Remove hardcoded +4.5 boost from _score_response_likelihood()
2. Move staffing adjustment to score_job() after weighted sum
3. Document: "Staffing preference replaces old +4.5 boost"
4. Test: Score staffing firm job with neutral preference, verify NO boost

**Warning signs:**
- Staffing firms score impossibly high (>5.0)
- "Neutral" preference still shows boost in scores
- Tests for _score_response_likelihood fail after changes

**Source:** scoring.py line 502 + user constraints

## Code Examples

Verified patterns from official sources and existing codebase:

### Extracting Current Hardcoded Weights

```python
# Source: scoring.py lines 47-54 (current hardcoded behavior)
# Place in profile_manager.py as constant:

DEFAULT_SCORING_WEIGHTS = {
    "skill_match": 0.25,          # 25% - Core skills match
    "title_relevance": 0.15,      # 15% - Job title alignment
    "seniority": 0.15,            # 15% - Experience level fit
    "location": 0.15,             # 15% - Location/arrangement match
    "domain": 0.10,               # 10% - Industry expertise
    "response_likelihood": 0.20,  # 20% - Chance of getting response
}

# Use in migration AND scoring.py fallback to ensure consistency
```

### Profile v2 JSON Structure

```python
# Source: User constraints + existing profile structure
# Example migrated v2 profile:

{
  "schema_version": 2,
  "name": "Jane Doe",
  "years_experience": 7,
  "level": "senior",
  "target_titles": ["Python Engineer", "Backend Engineer"],
  "core_skills": ["Python", "PostgreSQL", "AWS"],
  "secondary_skills": ["Docker", "Kubernetes"],
  "location": "San Francisco, CA",
  "arrangement": ["remote", "hybrid"],
  "domain_expertise": ["fintech", "healthcare"],
  "comp_floor": 120000,
  "dealbreakers": ["relocation required"],
  "scoring_weights": {
    "skill_match": 0.25,
    "title_relevance": 0.15,
    "seniority": 0.15,
    "location": 0.15,
    "domain": 0.10,
    "response_likelihood": 0.20
  },
  "staffing_preference": "neutral"
}
```

### Staffing Preference Application

```python
# Source: User constraints + scoring.py pattern
# In score_job() AFTER weighted sum calculation:

# Apply staffing firm preference (post-scoring adjustment)
staffing_pref = profile.get("staffing_preference", "neutral")
if is_staffing_firm(job.company):
    if staffing_pref == "boost":
        overall = min(5.0, overall + 0.5)
        scores["staffing_note"] = "Staffing firm (boosted +0.5)"
    elif staffing_pref == "penalize":
        overall = max(1.0, overall - 1.0)
        scores["staffing_note"] = "Staffing firm (penalized -1.0)"
    # "neutral" = no adjustment, treat same as direct employers
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded scoring weights in scoring.py | Configurable weights in profile | This phase (v2.1.0) | Users can adjust scoring to preferences |
| Staffing firms always boosted +4.5 | User choice: boost/neutral/penalize | This phase (v2.1.0) | Users who dislike staffing firms can penalize them |
| Manual profile editing in JSON | GUI sliders (Phase 34) | Next phase | Easier weight adjustment, live preview |
| No schema versioning | Explicit schema_version field | v1.5.0 | Enables future migrations |

**Deprecated/outdated:**
- Hardcoded +4.5 staffing boost (scoring.py line 502): Replace with configurable staffing_preference in this phase
- Direct profile.json editing: Will be supplemented (not replaced) by GUI in Phase 34

## Open Questions

1. **Exact numeric values for staffing preference presets**
   - What we know: Three presets (boost, neutral, penalize), user chose neutral as new default
   - What's unclear: Exact point values for boost and penalize
   - Recommendation: Boost = +0.5 (subtle), Penalize = -1.0 (significant but not dealbreaker). Test with real data to tune.

2. **Whether to make scoring_weights optional or required in v2 schema**
   - What we know: Migration always adds it, validation checks it if present
   - What's unclear: Should validate_profile() REQUIRE it for schema_version=2?
   - Recommendation: Make it required for v2 — clearer contract, easier to debug. Fallback .get() in scoring.py handles edge cases.

3. **How to handle profiles edited by future versions (schema_version > 2)**
   - What we know: Current code ignores silently (profile_manager.py line 273)
   - What's unclear: Is silent degradation acceptable, or warn user?
   - Recommendation: Keep silent for now (forward compatibility). Add warning in Phase 34 GUI.

4. **Whether to log migration or keep it silent**
   - What we know: User shouldn't notice upgrade per constraints
   - What's unclear: Should debug logs show "Migrated profile from v1 to v2"?
   - Recommendation: Log at DEBUG level (developers see it, users don't). Helps troubleshooting.

## Sources

### Primary (HIGH confidence)

- `/home/corye/Claude/Job-Radar/job_radar/scoring.py` - Current hardcoded weights (lines 47-54), staffing boost (line 502)
- `/home/corye/Claude/Job-Radar/job_radar/profile_manager.py` - Existing schema migration pattern (lines 267-273), validation (lines 78-141)
- `/home/corye/Claude/Job-Radar/job_radar/wizard.py` - Atomic write pattern (lines 752-757), question structure (lines 189-281)
- `/home/corye/Claude/Job-Radar/.planning/phases/33-scoring-configuration-backend/33-CONTEXT.md` - User decisions and constraints
- `/home/corye/Claude/Job-Radar/.planning/research/PITFALLS.md` - Schema migration pitfalls (lines 9-41)

### Secondary (MEDIUM confidence)

- `/home/corye/Claude/Job-Radar/.planning/phases/24-profile-infrastructure/24-RESEARCH.md` - Profile I/O patterns (lines 62-125)
- `/home/corye/Claude/Job-Radar/.planning/REQUIREMENTS.md` - SCORE-03 requirement definition

### Tertiary (LOW confidence)

None — all research grounded in existing codebase patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, all stdlib + existing libraries
- Architecture: HIGH - Extends proven v0→v1 migration pattern already in production
- Pitfalls: HIGH - Documented from existing codebase issues and user constraints

**Research date:** 2026-02-13
**Valid until:** 2026-03-13 (30 days — stable Python stdlib patterns, no fast-moving dependencies)

**Key findings:**
1. Current scoring weights from scoring.py: skill(0.25), title(0.15), seniority(0.15), location(0.15), domain(0.10), response(0.20)
2. Existing migration pattern (v0→v1) in profile_manager.py lines 267-273 is template for v1→v2
3. Nested scoring_weights object recommended over flat keys (cleaner JSON, easier validation)
4. Staffing preference is post-scoring adjustment, NOT a 7th weight component
5. Score stability is CRITICAL — default weights must match current hardcoded behavior exactly
