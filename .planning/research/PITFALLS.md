# Pitfalls Research: Profile Management Features

**Domain:** CLI Profile Management (Update, Preview, Quick-Edit)
**Researched:** 2026-02-11
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Partial Update File Corruption

**What goes wrong:**
Profile JSON becomes corrupted (truncated, invalid JSON) when update operation is interrupted mid-write by crash, Ctrl+C, disk-full, or power loss. User loses entire profile, not just failed update.

**Why it happens:**
Direct file writes (`open(path, 'w') → json.dump()`) are not atomic. If Python process is killed between truncating file and completing write, profile.json contains partial content. JSON parser then fails on next read, making profile unrecoverable without backup.

**Consequences:**
- Total profile data loss (wizard re-run required)
- Search breaks silently if profile read fails
- User loses trust in CLI update features
- No recovery path without backup

**How to avoid:**
Implement atomic write pattern:
```python
import os
import json
import tempfile

def atomic_write_json(path, data):
    """Write JSON atomically using temp + rename."""
    dir_path = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=dir_path,
        delete=False,
        suffix='.tmp'
    ) as tmp_file:
        tmp_path = tmp_file.name
        json.dump(data, tmp_file, indent=2)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())  # Force to disk

    # Atomic rename (same filesystem)
    os.replace(tmp_path, path)  # os.replace is atomic on POSIX/Windows
```

**Warning signs:**
- Profile corruption reports from users
- "JSON decode error" in error logs
- Empty or truncated profile.json files
- No temp file usage in update code

**Phase to address:**
Phase 1 (Foundation) - Must be in place before ANY profile update features ship. Non-negotiable for data integrity.

**Real-world examples:**
- [Docker config.json corruption on crashes](https://github.com/moby/moby/discussions/48529)
- [OpenCode storage corruption mid-write](https://github.com/anomalyco/opencode/issues/7733)
- [GitLens removed git remotes silently](https://github.com/gitkraken/vscode-gitlens/issues/4851)

---

### Pitfall 2: Validation Inconsistency Between Wizard and CLI Flags

**What goes wrong:**
Wizard validates profile fields strictly (type checking, range validation), but `--update-skills` or `--set-min-score` flags accept invalid values that corrupt profile. Example: `--set-min-score 99` succeeds even though scoring system uses 0.0-5.0 scale.

**Why it happens:**
Developers implement wizard validation once, then add CLI flags later without extracting/reusing validation logic. Each update path has separate validation (or none for CLI flags), leading to divergence.

**Consequences:**
- Invalid profile values break scoring engine
- Wizard-created profiles work, CLI-updated profiles fail
- Silent data corruption (no error, but scoring wrong)
- User confusion ("worked yesterday, broken today")

**How to avoid:**
1. Extract validation to shared schema module:
```python
# profile_schema.py
from typing import Literal, List
from pydantic import BaseModel, Field, validator

class ProfileSchema(BaseModel):
    name: str = Field(min_length=1)
    level: Literal["entry", "mid", "senior", "lead"]
    years_experience: int = Field(ge=0, le=50)
    core_skills: List[str] = Field(min_items=1, max_items=20)
    comp_floor: float | None = Field(ge=0)

    @validator('core_skills')
    def no_empty_skills(cls, v):
        if any(not s.strip() for s in v):
            raise ValueError("Skills cannot be empty strings")
        return v
```

2. Use in wizard AND CLI flags:
```python
# Wizard
profile = ProfileSchema(**wizard_answers)

# CLI flag
profile = ProfileSchema.parse_file(profile_path)
profile.core_skills = args.update_skills.split(',')
profile = ProfileSchema(**profile.dict())  # Re-validate
```

**Warning signs:**
- Scoring errors after CLI updates
- Invalid values in profile.json
- Different behavior wizard vs. CLI
- No shared validation module

**Phase to address:**
Phase 1 (Foundation) - Validation schema must exist BEFORE implementing CLI flags. Add CLI flags in Phase 2 only after validation is unified.

**Real-world examples:**
- [npm config validation conflicts](https://github.com/npm/cli/issues/8353) - strict validation caused friction with other tools
- [Git config manual edits break](https://teamtreehouse.com/community/git-stopped-working-fatal-bad-config-line-1-in-file-usersusernamegitconfig)

---

### Pitfall 3: No Confirmation for Destructive CLI Flag Updates

**What goes wrong:**
User runs `job-radar --update-skills "Python,JavaScript"` expecting to ADD skills, but flag REPLACES entire skills list. No confirmation prompt, no undo, original skills gone.

**Why it happens:**
CLI flags are designed for non-interactive use (scripts, CI/CD), so confirmation prompts break automation. But users expect CLI flags to behave like interactive commands with safety guardrails.

**Consequences:**
- Accidental data loss (skills, certifications)
- User frustration with "destructive" CLI
- Support requests for recovery
- Hesitation to use CLI flags

**How to avoid:**
1. **Default to append mode**, require explicit replacement:
```bash
# Safe (append)
job-radar --add-skills "Docker,Kubernetes"

# Explicit destructive (replace)
job-radar --set-skills "Python,JavaScript" --confirm

# Error without confirmation
job-radar --set-skills "..."
# Error: --set-skills is destructive. Add --confirm or use --add-skills
```

2. **Show before/after diff** when confirmation required:
```python
if args.set_skills and not args.confirm:
    print("🚨 DESTRUCTIVE CHANGE:")
    print(f"  Current: {', '.join(profile.core_skills)}")
    print(f"  New:     {', '.join(new_skills)}")
    print("\nAdd --confirm to proceed, or use --add-skills to append")
    sys.exit(1)
```

3. **Dry-run mode** for preview:
```bash
job-radar --set-min-score 3.5 --dry-run
# Would update min_score: 2.0 → 3.5
```

**Warning signs:**
- User complaints about lost data
- Support requests for "undo" or recovery
- Hesitation to use CLI flags in docs/issues
- No --dry-run or --confirm flags

**Phase to address:**
Phase 2 (CLI Flags) - Before implementing ANY destructive flags, decide on safety model (append vs. replace, confirmation, dry-run).

**Real-world examples:**
- [Gemini CLI safe mode confirmation](https://addyosmani.com/blog/gemini-cli/) - default requires approval
- [Salesforce CLI validation without args](https://github.com/forcedotcom/cli/issues/2246) - no confirmation for destructive deploys

---

### Pitfall 4: Profile Schema Evolution Without Migration Path

**What goes wrong:**
v1.6.0 adds `preferred_languages` field to profile. Old profiles (v1.5.0) don't have this field. Code expects field to exist, crashes on profile load with `KeyError: 'preferred_languages'`.

**Why it happens:**
No version tracking in profile JSON. No migration system to upgrade old profiles. Code assumes current schema, fails when loading profiles created by older versions.

**Consequences:**
- App crashes on version upgrade
- Users forced to re-run wizard (lose profile)
- Breaking change in "minor" version
- Backward compatibility broken

**How to avoid:**
1. **Add schema version** to profile:
```json
{
  "schema_version": 2,
  "name": "...",
  ...
}
```

2. **Implement migration system**:
```python
CURRENT_SCHEMA = 2

def migrate_profile(profile_data):
    version = profile_data.get('schema_version', 1)

    if version == 1:
        # Add preferred_languages (default to languages)
        profile_data['preferred_languages'] = profile_data.get('languages', ['English'])
        profile_data['schema_version'] = 2

    if version == 2:
        # Future migration
        pass

    return profile_data

def load_profile(path):
    with open(path) as f:
        data = json.load(f)

    # Auto-migrate and save
    data = migrate_profile(data)
    if data['schema_version'] != CURRENT_SCHEMA:
        atomic_write_json(path, data)  # Persist migration

    return ProfileSchema(**data)
```

3. **Test migrations**:
```python
def test_migration_v1_to_v2():
    v1_profile = {"name": "Test", "languages": ["Spanish"]}
    migrated = migrate_profile(v1_profile)
    assert migrated['schema_version'] == 2
    assert migrated['preferred_languages'] == ["Spanish"]
```

**Warning signs:**
- No `schema_version` field in profile
- KeyError on profile load after updates
- No migration tests
- Breaking changes in minor versions

**Phase to address:**
Phase 1 (Foundation) - Add schema versioning IMMEDIATELY, before v1.5.0 ships. Migrations can be added incrementally, but version field must exist from start.

**Real-world examples:**
- [JSON schema compatibility checker](https://github.com/json-schema-org/community/issues/984) - detecting breaking changes
- [ORS config migration tool](https://github.com/GIScience/ors-config-migration) - JSON to YAML with schema changes
- [Native image metadata upgrades](https://github.com/oracle/graal/issues/8534)

---

### Pitfall 5: No Backup Before Profile Updates

**What goes wrong:**
User runs `--update-skills` with typo. Realizes mistake immediately, but no undo. Previous profile state lost. Must manually reconstruct skills list from memory or re-run wizard.

**Why it happens:**
Backup considered "extra complexity" for initial implementation. Developers assume atomic writes prevent corruption, but atomic writes don't prevent USER ERRORS.

**Consequences:**
- No recovery from user mistakes
- Anxiety about using CLI flags
- Feature abandonment (users stick to wizard)
- Support burden for recovery requests

**How to avoid:**
1. **Automatic timestamped backups**:
```python
from datetime import datetime
import shutil

def backup_profile(profile_path):
    """Create timestamped backup before update."""
    if not os.path.exists(profile_path):
        return None

    backup_dir = os.path.join(os.path.dirname(profile_path), '.backups')
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'profile_{timestamp}.json')

    shutil.copy2(profile_path, backup_path)

    # Cleanup: keep last 10 backups
    backups = sorted(glob.glob(os.path.join(backup_dir, 'profile_*.json')))
    for old_backup in backups[:-10]:
        os.remove(old_backup)

    return backup_path

def update_profile(profile_path, updates):
    backup_path = backup_profile(profile_path)
    print(f"💾 Backup saved: {backup_path}")

    # ... perform update with atomic write ...

    return backup_path
```

2. **Easy restore command**:
```bash
job-radar --restore-profile
# Lists recent backups with preview
# User selects which to restore
```

3. **Post-update summary**:
```
✓ Profile updated successfully
  Updated: core_skills
  Backup: ~/.job-radar/.backups/profile_20260211_143052.json
  Restore: job-radar --restore-profile
```

**Warning signs:**
- No backup directory or mechanism
- User complaints about irreversible changes
- Support requests for manual recovery
- Feature usage drops over time

**Phase to address:**
Phase 2 (CLI Flags) - Implement before shipping CLI update flags. Backup is table-stakes for any destructive operation.

**Real-world examples:**
- [Git config backup best practices](https://labex.io/tutorials/git-how-to-fix-fatal-unable-to-read-config-file-error-in-git-417550) - "create regular backups"
- [Network config backup automation](https://www.manageengine.com/network-configuration-manager/best-practices-for-backing-up-network-configurations.html)
- [Fortinet config backup](https://docs.fortinet.com/document/fortigate/7.6.5/administration-guide/702257/configuration-backups-and-reset) - before firmware updates

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip atomic writes, use direct `open('w')` | 5 fewer lines of code | Profile corruption on crashes, user data loss, support burden | **Never** - atomic writes are non-negotiable |
| Duplicate validation (wizard vs. CLI) | Faster initial implementation | Validation divergence, silent corruption, test explosion | **Never** - extract validation from day 1 |
| No schema versioning | Simpler initial design | Breaking changes on every schema update, forced wizard re-runs | **Never** - add version field immediately |
| Skip backups ("atomic writes are enough") | Less disk I/O, simpler code | No recovery from user errors, feature anxiety | **Never** for destructive operations |
| CLI flags default to REPLACE instead of APPEND | Simpler flag parsing | User data loss, confusion, support requests | Only with `--confirm` flag requirement |
| String-based skill parsing (`"Python,JS"`) instead of JSON | Easier CLI usage | Can't handle commas in skill names, quote escaping issues | Acceptable for MVP; migrate to JSON in later versions |
| No dry-run mode | Fewer code paths to test | Users afraid to use CLI flags without preview | Only if confirmation prompts show diffs |

---

## Integration Gotchas

Common mistakes when integrating profile updates with existing system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **Wizard → CLI flag validation** | Wizard uses Questionary validation, CLI flags use argparse types. Different validation rules. | Extract to shared Pydantic schema. Both paths validate through schema. |
| **Profile load in search.py** | Assumes profile.json always valid, crashes on corruption. | Try/except with helpful error: "Profile corrupted. Restore backup with --restore-profile or re-run wizard." |
| **Preview display** | Dumps entire JSON to console, overwhelming and unreadable. | Format as human-readable table with sections (Personal Info, Skills, Preferences). |
| **CLI flag parsing** | `--update-skills "Python, JavaScript"` splits on comma WITHOUT trimming whitespace → skills: `["Python", " JavaScript"]` | Strip whitespace: `[s.strip() for s in args.update_skills.split(',')]` |
| **Backup cleanup** | Never delete old backups → fills disk over months. | Keep last 10-20 backups, delete older. Or size-based limit (e.g., 1 MB total). |
| **Profile path resolution** | Hardcode `~/.job-radar/profile.json`, breaks on Windows if `~` not expanded. | Use `os.path.expanduser('~/.job-radar/profile.json')` |
| **Schema migration timing** | Migrate on every profile read → unnecessary I/O. | Migrate once, persist updated profile. Track current schema version. |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading entire backup directory to list backups | CLI hangs when listing restore options | Use `os.scandir()` with `stat()`, don't read file contents | >100 backups (months of daily updates) |
| Validating profile on every scorer instantiation | Scoring becomes slow, test suite timeout | Validate once at load, cache validated object | >1000 job listings per search |
| Re-parsing JSON skills normalization on every match | CPU spike during scoring | Pre-normalize skills on profile load, cache normalized lookup | Already resolved in v1.0 (normalize at lookup) |
| Keeping all schema versions in migration chain | Migration code grows forever, slow startup | Archive migrations: support N-1 and N-2 versions, force wizard for older | Schema version >10 |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| **Path traversal in `--restore-profile <path>`** | User provides `../../etc/passwd`, app tries to load it | Validate path is within `~/.job-radar/.backups/`, reject `..` segments |
| **Arbitrary code execution via JSON** | Attacker modifies profile.json to inject code (e.g., `__import__` in deserializer) | Use `json.load()` NOT `pickle` or `eval()`. Never execute profile values. |
| **No validation on restored backups** | User restores old backup with invalid schema, app crashes | Validate + migrate restored profiles before saving |
| **World-readable profile.json** | Profile contains PII (name, location, email in highlights) | Set restrictive permissions: `os.chmod(profile_path, 0o600)` (owner read/write only) |
| **Command injection via skill names** | Skill name `"; rm -rf /"` executed if passed to shell | Never pass profile values to shell commands. No `os.system()` or `subprocess.shell=True`. |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| **Profile preview dumps raw JSON** | Overwhelming, hard to read, looks broken | Format as sections with labels: `Personal Info`, `Skills` (with counts), `Preferences` |
| **No indication which fields quick-edit can change** | User guesses, gets errors, gives up | `job-radar --help` shows: "Editable fields: skills, min_score, target_titles, location" |
| **CLI flag updates with zero feedback** | "Did it work? Let me check the file..." | Print confirmation: "✓ Updated core_skills (5 skills)" |
| **No diff shown before destructive change** | User confirms without knowing what's changing | Show before/after: `core_skills: ["Python", "JS"] → ["Go", "Rust"]` |
| **Error messages reference internal field names** | "ValidationError: comp_floor must be >= 0" → user doesn't know what comp_floor is | "Error: Minimum salary must be a positive number (or leave blank)" |
| **Quick-edit mode shows ALL fields** | Overwhelms user with 15 fields, most unchanged | Show only common fields (skills, location, min_score). Advanced flag for full edit. |
| **Preview runs before EVERY search** | Adds 2-3 seconds to startup, annoying for daily use | Preview only on `--profile-preview` flag, or first run each day |
| **Restore command doesn't show backup contents** | User picks wrong backup, restores old version | Show first few fields + timestamp: `20260211_1430: John Doe, Python/JS, 5 skills` |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Profile update**: Atomic write implemented — verify `os.replace()` used (not `os.rename()` which fails cross-filesystem)
- [ ] **Profile update**: Backup created — verify backup timestamp in output
- [ ] **Profile update**: Old backups cleaned up — verify only N most recent kept
- [ ] **Validation**: Same rules wizard and CLI — verify shared schema module used
- [ ] **Validation**: Profile validated after restore — verify restore path calls schema validation
- [ ] **CLI flags**: Confirmation for destructive changes — verify `--set-*` flags error without `--confirm`
- [ ] **CLI flags**: Helpful error messages — verify field names translated to user language
- [ ] **Preview**: Formatted output, not raw JSON — verify sections, labels, readable layout
- [ ] **Preview**: Performance acceptable — verify preview takes <100ms
- [ ] **Schema migration**: Version field in profile — verify all profiles have `schema_version`
- [ ] **Schema migration**: Migration tests — verify test for each schema version upgrade
- [ ] **Error handling**: Corrupted profile helpful error — verify suggests restore or wizard
- [ ] **Error handling**: Invalid flag value helpful error — verify shows valid range/options
- [ ] **Security**: File permissions set — verify profile.json is 0o600 (owner only)
- [ ] **Security**: Backup permissions set — verify backup files are 0o600
- [ ] **Security**: Path traversal prevented — verify restore path validated

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| **Corrupted profile (no backup)** | HIGH | 1. Check `.backups/` for automatic backups<br>2. If none, attempt manual JSON repair with `jq` or text editor<br>3. Last resort: re-run wizard (`job-radar --wizard`) |
| **Corrupted profile (with backup)** | LOW | 1. `job-radar --restore-profile`<br>2. Select most recent backup<br>3. Verify with `--profile-preview` |
| **Invalid value from CLI flag** | LOW | 1. Validation should prevent this (fail fast)<br>2. If persisted: load profile, fix value, save with atomic write<br>3. Add test for this validation case |
| **Lost skills from REPLACE instead of APPEND** | MEDIUM | 1. `job-radar --restore-profile`<br>2. Select backup before destructive change<br>3. Use `--add-skills` instead of `--set-skills` |
| **Schema migration failed** | MEDIUM | 1. Check migration error message for version<br>2. Manual migration: load JSON, add missing fields, increment version<br>3. Report bug with profile structure (anonymized) |
| **Backup directory full** | LOW | 1. Manual cleanup: `rm ~/.job-radar/.backups/profile_2026011*` (old month)<br>2. Or increase retention limit in code |
| **Permissions error (can't write profile)** | LOW | 1. Check ownership: `ls -l ~/.job-radar/profile.json`<br>2. Fix: `chmod 600 ~/.job-radar/profile.json`<br>3. Check parent directory permissions |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| **Partial update corruption** | Phase 1: Foundation (atomic writes) | Test: kill process mid-write, profile still valid (old or new, never corrupted) |
| **Validation inconsistency** | Phase 1: Foundation (schema) | Test: same invalid value rejected by wizard AND CLI flags with same error |
| **No confirmation for destructive changes** | Phase 2: CLI Flags | Test: `--set-skills` without `--confirm` exits with error + diff |
| **Schema evolution without migration** | Phase 1: Foundation (versioning) | Test: load v1 profile, migrates to v2, saves v2 |
| **No backup before updates** | Phase 2: CLI Flags | Test: update creates backup, backup listed in `--restore-profile` |
| **Preview dumps raw JSON** | Phase 3: Preview & Quick-Edit | Manual test: preview output is human-readable with sections |
| **No diff before confirmation** | Phase 2: CLI Flags | Manual test: confirmation prompt shows before/after diff |
| **Path traversal in restore** | Phase 2: CLI Flags | Test: `--restore-profile ../../../etc/passwd` rejected |
| **World-readable profile** | Phase 1: Foundation | Test: new profile has 0o600 permissions on Unix |
| **Command injection via skills** | N/A (not applicable) | Code review: no `subprocess` or `os.system` with profile values |

---

## Sources

### File Corruption & Atomic Writes
- [Storage resilience: atomic writes, safer temp cleanup](https://github.com/anomalyco/opencode/issues/7733) - OpenCode corruption prevention strategies
- [Docker config.json rewrite on every run](https://github.com/moby/moby/discussions/48529) - Docker's atomic write approach
- [Registry corruption after crash during atomic rename](https://github.com/openclaw/openclaw/issues/1469) - Real-world atomic write failure
- [Better File Writing in Python: Embrace Atomic Updates](https://sahmanish20.medium.com/better-file-writing-in-python-embrace-atomic-updates-593843bfab4f) - Python atomic write patterns

### Validation Consistency
- [npm config validation warnings](https://github.com/npm/cli/issues/8353) - Strict validation friction with other tools
- [Testing CLI the way people use it](https://www.smashingmagazine.com/2022/04/testing-cli-way-people-use-it/) - Independence and validation testing
- [CLI flags force interactive mode discussion](https://github.com/serverless/serverless/discussions/11275) - Consistency between modes

### Confirmation & Safety
- [Gemini CLI safe mode confirmation](https://addyosmani.com/blog/gemini-cli/) - Default approval requirements
- [CLI Tools with previews, dry runs](https://nickjanetakis.com/blog/cli-tools-that-support-previews-dry-runs-or-non-destructive-actions) - Safety patterns
- [Salesforce CLI validation without args](https://github.com/forcedotcom/cli/issues/2246) - Destructive change confirmation

### Schema Evolution & Migration
- [JSON Schema Compatibility Checker](https://github.com/json-schema-org/community/issues/984) - Detecting breaking changes
- [JSON Metadata Versioning, Backwards Compatibility](https://github.com/oracle/graal/issues/8534) - Native image metadata upgrades
- [ORS config migration tool](https://github.com/GIScience/ors-config-migration) - JSON schema migration patterns
- [Migrations.Json.Net](https://github.com/Weingartner/Migrations.Json.Net) - Framework for data migrations

### Git Config Corruption Examples
- [Git config corruption: fatal bad config line](https://github.com/orgs/community/discussions/22483)
- [GitLens removed git remotes silently](https://github.com/gitkraken/vscode-gitlens/issues/4851)
- [Super long branch names corrupt config](https://github.com/git/git-scm.com/issues/188)
- [How to fix fatal unable to read config file](https://labex.io/tutorials/git-how-to-fix-fatal-unable-to-read-config-file-error-in-git-417550)

### Backup Best Practices
- [Configuration backups and reset](https://docs.fortinet.com/document/fortigate/7.6.5/administration-guide/702257/configuration-backups-and-reset)
- [Best practices for backing up network configurations](https://www.manageengine.com/network-configuration-manager/best-practices-for-backing-up-network-configurations.html)
- [Performing a configuration backup](https://docs.fortinet.com/document/fortigate/6.2.0/best-practices/262994/performing-a-configuration-backup)

### Transaction Rollback & Error Handling
- [How to Fix transaction aborted Errors in PostgreSQL](https://oneuptime.com/blog/post/2026-01-25-fix-transaction-aborted-postgresql/view) - Savepoint patterns
- [Handling UnexpectedRollbackException in Spring](https://www.baeldung.com/spring-unexpected-rollback-exception)
- [Transaction rollback performs partial rollback](https://github.com/sequelize/sequelize/issues/9105)

### UX Patterns
- [UX patterns for CLI tools](https://www.lucasfcosta.com/blog/ux-patterns-cli-tools) - CLI documentation and examples
- [CLI UX best practices: progress displays](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays)
- [20 profile page design examples with expert UX advice](https://www.eleken.co/blog-posts/profile-page-design) - Edit mode patterns

### Validation Approaches
- [How Zod Changed TypeScript Validation Forever](https://iamshadi.medium.com/how-zod-changed-typescript-validation-forever-the-power-of-runtime-and-compile-time-validation-531cd63799cf)
- [AJV CLI: Command-line interface for Ajv JSON Validator](https://github.com/ajv-validator/ajv-cli)
- [Standalone validation code with Ajv](https://ajv.js.org/standalone.html)

---
*Pitfalls research for: Job Radar v1.5.0 Profile Management*
*Researched: 2026-02-11*
*Confidence: HIGH - based on verified sources (GitHub issues, official docs, real-world examples)*
