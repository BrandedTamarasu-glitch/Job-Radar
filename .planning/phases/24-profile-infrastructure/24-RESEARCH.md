# Phase 24: Profile Infrastructure - Research

**Researched:** 2026-02-12
**Domain:** Python file I/O, data validation, backup management
**Confidence:** HIGH

## Summary

Phase 24 builds a centralized profile management module to replace scattered profile I/O logic across the codebase. The wizard already implements atomic writes via `_write_json_atomic()`, but profile loading/validation is duplicated in `search.py` with inconsistent error handling. The phase requires extracting the atomic write pattern, adding automatic timestamped backups with rotation (keep 10 most recent), schema versioning (v1), and centralizing all validation logic.

**Primary recommendation:** Create `profile_manager.py` using Python stdlib only (no Pydantic needed for this simple use case). Extract atomic write from wizard, add backup rotation using pathlib + sorted by mtime, implement schema versioning with migration hooks, and centralize validation using existing wizard validators plus custom exception hierarchy.

## Standard Stack

### Core Libraries

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tempfile (stdlib) | - | Atomic file writes | `mkstemp()` creates temp files in same directory for atomic rename |
| pathlib (stdlib) | - | File operations | Modern, cross-platform path handling; `.replace()` for atomic rename |
| json (stdlib) | - | Profile serialization | Built-in, no dependencies; `indent=2` for human-readable output |
| datetime (stdlib) | - | Timestamp generation | `datetime.utcnow().isoformat()` for ISO8601 backup filenames |
| os (stdlib) | - | Low-level file ops | `os.fsync()` ensures data written to disk before rename |

### Supporting Libraries (Already in Project)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| questionary | latest | Inline validation | Reuse existing validators (NonEmptyValidator, ScoreValidator, etc.) |
| pytest | >=9.0 | Testing | Unit tests for atomic writes, backup rotation, validation |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib only | Pydantic | Pydantic adds 5-50x validation overhead; overkill for simple dict validation with 8 fields |
| Custom exceptions | ValidationError from questionary | questionary's ValidationError is for interactive prompts only; need exception hierarchy for programmatic API |
| Manual timestamp parsing | python-dateutil | Already in dependencies, but stdlib datetime.fromisoformat() handles ISO8601 natively in Python 3.11+ |
| Custom backup rotation | rotate-backups library | Adds dependency for simple "sort by mtime, delete oldest" pattern; 10 lines of pathlib code |

**Installation:**

No new dependencies required - all stdlib.

## Architecture Patterns

### Recommended Module Structure

```
job_radar/
├── profile_manager.py      # NEW: Centralized profile I/O
│   ├── ProfileValidationError (exception hierarchy)
│   ├── load_profile()
│   ├── save_profile()
│   ├── validate_profile()
│   └── _rotate_backups()
├── wizard.py               # MODIFY: Use profile_manager for I/O
├── search.py               # MODIFY: Use profile_manager for loading
└── paths.py                # EXTEND: Add get_backup_dir()
```

### Pattern 1: Atomic File Write with Backup

**What:** Create timestamped backup, write to temp file, fsync, atomic rename, delete old backups
**When to use:** All profile writes (wizard, quick-edit, CLI flags)

**Example:**

```python
# Source: Existing wizard.py _write_json_atomic() pattern + backup rotation
from pathlib import Path
import tempfile
import os
import json
from datetime import datetime

def save_profile(profile_data: dict, profile_path: Path) -> None:
    """Save profile with automatic backup and atomic write.

    Raises ProfileValidationError if validation fails.
    """
    # Validate first - never write invalid data
    validate_profile(profile_data)

    # Add schema version if not present
    if "schema_version" not in profile_data:
        profile_data["schema_version"] = 1

    # Create timestamped backup if profile exists
    if profile_path.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = profile_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"profile_{timestamp}.json"

        # Simple copy for backup (not atomic - backup corruption is recoverable)
        with open(profile_path, "r", encoding="utf-8") as src:
            with open(backup_path, "w", encoding="utf-8") as dst:
                dst.write(src.read())

        # Rotate backups: keep 10 most recent
        _rotate_backups(backup_dir, max_backups=10)

    # Atomic write to temp file + rename (from wizard pattern)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=profile_path.parent,
        prefix=profile_path.name + ".",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk

        Path(tmp_path).replace(profile_path)  # Atomic on POSIX & Windows 3.3+
    except:
        try:
            os.unlink(tmp_path)
        except:
            pass
        raise
```

### Pattern 2: Backup Rotation by Modification Time

**What:** Sort backup files by mtime, delete all but N most recent
**When to use:** After creating new backup, before returning from save_profile()

**Example:**

```python
# Source: pathlib glob + sorted by mtime pattern
def _rotate_backups(backup_dir: Path, max_backups: int = 10) -> None:
    """Keep only the N most recent backup files."""
    backups = sorted(
        backup_dir.glob("profile_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True  # Newest first
    )

    # Delete all but max_backups
    for old_backup in backups[max_backups:]:
        old_backup.unlink()
```

### Pattern 3: Schema Versioning with Migration Hooks

**What:** Store schema_version in profile, provide migration path for future versions
**When to use:** On every profile save and load

**Example:**

```python
# Source: JSON schema versioning best practices
def load_profile(profile_path: Path) -> dict:
    """Load and validate profile with schema migration support."""
    if not profile_path.exists():
        raise ProfileNotFoundError(f"Profile not found: {profile_path}")

    try:
        with open(profile_path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        raise ProfileValidationError(f"Invalid JSON: {e.msg} (line {e.lineno})")

    # Handle missing schema_version (pre-v1.5.0 profiles)
    schema_version = profile.get("schema_version", 0)

    if schema_version == 0:
        # Migrate v0 -> v1: add schema_version field
        profile["schema_version"] = 1
        # Auto-save migrated profile
        save_profile(profile, profile_path)
    elif schema_version > 1:
        raise ProfileValidationError(
            f"Profile schema version {schema_version} is newer than supported (max: 1). "
            "Please update Job Radar."
        )

    validate_profile(profile)
    return profile
```

### Pattern 4: Centralized Validation with Custom Exceptions

**What:** Single validation function called by all entry points (wizard, load, CLI)
**When to use:** Before any profile write, after any profile load

**Example:**

```python
# Source: Custom exception hierarchy best practices + existing search.py validation
class ProfileValidationError(Exception):
    """Base exception for profile validation errors."""
    pass

class MissingFieldError(ProfileValidationError):
    """Required field is missing."""
    def __init__(self, field: str):
        super().__init__(f"Missing required field: '{field}'")
        self.field = field

class InvalidTypeError(ProfileValidationError):
    """Field has wrong type."""
    def __init__(self, field: str, expected: str, got: type):
        super().__init__(
            f"Field '{field}' must be {expected}, got {got.__name__}"
        )
        self.field = field

def validate_profile(profile: dict) -> None:
    """Validate profile structure and field constraints.

    Raises ProfileValidationError subclass on validation failure.
    """
    if not isinstance(profile, dict):
        raise InvalidTypeError("profile", "dict", type(profile))

    # Required fields
    required = ["name", "target_titles", "core_skills"]
    for field in required:
        if field not in profile:
            raise MissingFieldError(field)

    # Type validation
    if not isinstance(profile["target_titles"], list) or not profile["target_titles"]:
        raise InvalidTypeError("target_titles", "non-empty list", type(profile["target_titles"]))

    if not isinstance(profile["core_skills"], list) or not profile["core_skills"]:
        raise InvalidTypeError("core_skills", "non-empty list", type(profile["core_skills"]))

    # Range validation for optional fields
    if "years_experience" in profile:
        years = profile["years_experience"]
        if not isinstance(years, int) or years < 0 or years > 50:
            raise ProfileValidationError(
                f"years_experience must be integer 0-50, got {years}"
            )

    if "comp_floor" in profile:
        comp = profile["comp_floor"]
        if not isinstance(comp, (int, float)) or comp < 0 or comp > 1_000_000:
            raise ProfileValidationError(
                f"comp_floor must be number 0-1000000, got {comp}"
            )
```

### Anti-Patterns to Avoid

- **Direct json.dump() to target path:** Crash during write corrupts file. Always use temp + rename.
- **Validating after file write:** Write invalid data on disk. Always validate before write.
- **Backup without rotation:** Fills disk with infinite backups. Always limit backup count.
- **Generic Exception raising:** Caller can't distinguish error types. Use exception hierarchy.
- **Validation logic in multiple places:** Inconsistent behavior. Single validate_profile() function.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic writes | Custom locking/transactions | tempfile.mkstemp() + Path.replace() | OS-level atomic rename; cross-platform; battle-tested |
| Timestamp formatting | Custom date parsers | datetime.isoformat() / fromisoformat() | ISO8601 standard; sortable filenames; stdlib |
| File sorting by mtime | Manual stat() loops | sorted(paths, key=lambda p: p.stat().st_mtime) | Pythonic one-liner; pathlib handles cross-platform stat |
| JSON validation | String parsing for types | isinstance() checks + exception hierarchy | Clear error messages; Python native; no regex fragility |

**Key insight:** Python stdlib provides robust file I/O primitives. The complexity is in the *pattern* (temp + fsync + rename + backup + rotate), not the individual operations. Don't add dependencies for simple operations.

## Common Pitfalls

### Pitfall 1: Non-Atomic Replace on Different Filesystems

**What goes wrong:** `Path.replace()` is not atomic if temp file and target are on different filesystems (e.g., temp in `/tmp`, target in `/home`).

**Why it happens:** Atomic rename requires same filesystem; cross-filesystem requires copy+delete.

**How to avoid:** Create temp file in same directory as target using `tempfile.mkstemp(dir=target.parent)`.

**Warning signs:** Tests pass locally but fail in Docker/CI with different filesystem layouts.

### Pitfall 2: Forgetting fsync() Before Rename

**What goes wrong:** OS crash between write and rename loses data; file is renamed but empty.

**Why it happens:** OS buffers writes; rename happens before buffer flush.

**How to avoid:** Call `os.fsync(fd)` after write, before close/rename.

**Warning signs:** Rare corruption on power loss; hard to reproduce.

### Pitfall 3: Schema Version Comparison as String

**What goes wrong:** `"10" < "2"` is True in string comparison; schema version 10 treated as older than 2.

**Why it happens:** JSON stores numbers as numbers, but comparison might use str if not careful.

**How to avoid:** Always compare schema_version as int: `int(profile.get("schema_version", 0))`.

**Warning signs:** Migration logic breaks at version 10+.

### Pitfall 4: Backup Timestamp Collision

**What goes wrong:** Two saves within same second overwrite each other's backups.

**Why it happens:** Timestamp format `%Y%m%d_%H%M%S` has 1-second granularity.

**How to avoid:** Add microseconds to timestamp or use UUID suffix for uniqueness.

**Warning signs:** Test failures in fast loops; backup count less than save count.

### Pitfall 5: Validation After Partial Migration

**What goes wrong:** Migrate schema_version field but forget to migrate actual data structure; validation fails on old format.

**Why it happens:** Schema version incremented before data transformed.

**How to avoid:** Migrate data first, then set schema_version, then validate.

**Warning signs:** `load_profile()` raises validation errors on previously valid files after schema migration.

### Pitfall 6: Silent Backup Failure

**What goes wrong:** Backup creation fails (permissions, disk full) but save continues; no backup exists.

**Why it happens:** Backup is "nice to have" so errors are caught and ignored.

**How to avoid:** Let backup errors propagate; backup failure should abort save.

**Warning signs:** Users report "no backups" but saves succeed.

## Code Examples

Verified patterns from existing codebase:

### Atomic Write Pattern (from wizard.py)

```python
# Source: /home/corye/Claude/Job-Radar/job_radar/wizard.py lines 145-186
def _write_json_atomic(path: Path, data: dict):
    """Write JSON file atomically with temp file + rename to prevent corruption.

    Uses temp file in same directory + atomic rename to prevent partial writes
    on crash/interrupt. Ensures parent directory exists before writing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Critical: ensure written to disk

        Path(tmp_path).replace(path)  # Atomic on Unix and Windows Python 3.3+
    except:
        try:
            os.unlink(tmp_path)
        except:
            pass
        raise
```

### Profile Validation Pattern (from search.py)

```python
# Source: /home/corye/Claude/Job-Radar/job_radar/search.py lines 237-295
# Consolidated validation logic to be extracted into profile_manager.py

def validate_profile(profile: dict) -> None:
    """Validate profile structure and constraints."""
    if not isinstance(profile, dict):
        raise ProfileValidationError(
            f"Profile must be a JSON object, got {type(profile).__name__}"
        )

    # Required fields
    required = ["name", "target_titles", "core_skills"]
    missing = [f for f in required if f not in profile]
    if missing:
        raise MissingFieldError(', '.join(missing))

    # Type and non-empty validation
    if not isinstance(profile.get("target_titles"), list) or not profile["target_titles"]:
        raise InvalidTypeError("target_titles", "non-empty list", type(profile.get("target_titles")))

    if not isinstance(profile.get("core_skills"), list) or not profile["core_skills"]:
        raise InvalidTypeError("core_skills", "non-empty list", type(profile.get("core_skills")))

    # Optional field validation
    if "years_experience" in profile:
        years = profile["years_experience"]
        if not isinstance(years, int):
            raise InvalidTypeError("years_experience", "integer", type(years))
        if not (0 <= years <= 50):
            raise ProfileValidationError(
                f"years_experience must be 0-50, got {years}"
            )

    if "comp_floor" in profile:
        comp = profile["comp_floor"]
        if not isinstance(comp, (int, float)):
            raise InvalidTypeError("comp_floor", "number", type(comp))
        if not (0 <= comp <= 1_000_000):
            raise ProfileValidationError(
                f"comp_floor must be 0-1000000, got {comp}"
            )

    if "arrangement" in profile:
        arr = profile["arrangement"]
        if not isinstance(arr, list):
            raise InvalidTypeError("arrangement", "list", type(arr))
```

### Timestamp for Backup Filenames

```python
# Source: Python datetime stdlib best practices
from datetime import datetime

def create_backup_filename(base_name: str = "profile") -> str:
    """Generate sortable, unique backup filename with timestamp."""
    # UTC for consistency across timezones
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.json"

# Example output: "profile_20260212_143022.json"
# Sorts lexicographically in chronological order
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| os.rename() | Path.replace() | Python 3.3 | Path.replace() is atomic on Windows; os.rename() was not |
| Manual JSON parsing | json.load() with error handling | Always | json.load() provides line numbers in JSONDecodeError |
| Global exception handlers | Exception hierarchy | 2020+ | Callers can catch specific errors (e.g., MissingFieldError vs InvalidTypeError) |
| Pydantic for everything | Dataclasses/stdlib for simple cases | Pydantic v2 (2023) | Pydantic faster but still overkill for 8-field dict validation |

**Deprecated/outdated:**

- **os.rename()**: Use `Path.replace()` for cross-platform atomic rename (Python 3.3+)
- **Manual fsync via system calls**: Use `os.fsync(file_descriptor)` stdlib method
- **String-based path handling**: Use pathlib for all path operations (Python 3.4+)

## Open Questions

1. **Should backup rotation be synchronous or async?**
   - What we know: Backup rotation deletes old files (I/O operation)
   - What's unclear: Impact on wizard/CLI responsiveness for 10-file deletion
   - Recommendation: Keep synchronous for v1.5.0 (simpler, 10 deletes is <10ms); add async if users report slowness

2. **Should schema migration auto-save or require explicit save?**
   - What we know: load_profile() can detect schema_version=0 and migrate to v1
   - What's unclear: Should migration write to disk immediately or only on next save?
   - Recommendation: Auto-save on migration (expand-contract pattern) to prevent re-migration on every load

3. **Should backup creation failures abort the save?**
   - What we know: Backup protects against bad updates
   - What's unclear: If backup fails (permissions, disk full), should save proceed?
   - Recommendation: Abort save on backup failure (safety first); user can fix permissions and retry

## Sources

### Primary (HIGH confidence)

- Python 3 datetime module documentation - https://docs.python.org/3/library/datetime.html
- Python 3 tempfile module (official docs) - https://docs.python.org/3/library/tempfile.html
- Python 3 pathlib module (official docs) - https://docs.python.org/3/library/pathlib.html
- Existing Job Radar codebase - /home/corye/Claude/Job-Radar/job_radar/wizard.py (atomic write pattern)
- Existing Job Radar codebase - /home/corye/Claude/Job-Radar/job_radar/search.py (validation logic)

### Secondary (MEDIUM confidence)

- [Better File Writing in Python: Embrace Atomic Updates](https://sahmanish20.medium.com/better-file-writing-in-python-embrace-atomic-updates-593843bfab4f) - Medium article on atomic write patterns
- [Get a list of files sorted by modified date in Python](https://medium.com/@makerhacks/get-a-list-of-files-sorted-by-modified-date-in-python-44bac04c14d9) - pathlib sorting by mtime
- [Sort files after glob in Pathlib](https://madflex.de/sort-files-after-glob-in-pathlib/) - pathlib glob + sort pattern
- [Best Practices for Evolving Schemas in Schema Registry](https://docs.solace.com/Schema-Registry/schema-registry-best-practices.htm) - Schema versioning strategies
- [Couchbase Tutorial - Schema Versioning](https://developer.couchbase.com/tutorial-schema-versioning?learningPath=learn/json-document-management-guide) - JSON schema migration patterns
- [How to Create Custom Exceptions in Python](https://oneuptime.com/blog/post/2026-01-22-create-custom-exceptions-python/view) - 2026 exception hierarchy patterns
- [Define Custom Exceptions in Python - GeeksforGeeks](https://www.geeksforgeeks.org/python/define-custom-exceptions-in-python/) - Exception best practices
- [Pydantic vs Dataclasses: Python Data Validation Comparison](https://softwarelogic.co/en/blog/pydantic-vs-dataclasses-which-excels-at-python-data-validation) - When to use stdlib vs Pydantic

### Tertiary (LOW confidence)

- None - all findings verified with official docs or existing codebase

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - All stdlib, verified in existing wizard.py atomic write implementation
- Architecture: HIGH - Patterns extracted from existing codebase (wizard.py, search.py) and stdlib docs
- Pitfalls: MEDIUM-HIGH - fsync/filesystem issues verified in docs; backup collision is logical inference (not observed in wild)

**Research date:** 2026-02-12
**Valid until:** ~60 days (stable domain - file I/O patterns change slowly; schema versioning is architectural)
