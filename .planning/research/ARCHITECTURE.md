# Architecture Research: Profile Management Integration

**Domain:** CLI Profile Management (subsequent milestone)
**Researched:** 2026-02-11
**Confidence:** HIGH

## Current Architecture (Baseline)

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Entry Point                           │
│                  job_radar/__main__.py                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Banner     │  │   Wizard    │  │   Search    │          │
│  │  Display    │  │   (first    │  │    Main     │          │
│  │             │  │    run)     │  │             │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                 │
├─────────┴────────────────┴────────────────┴─────────────────┤
│                    Argument Parsing                          │
│                     (argparse)                               │
├─────────────────────────────────────────────────────────────┤
│                    Profile I/O Layer                         │
│                   paths.py + wizard.py                       │
├─────────────────────────────────────────────────────────────┤
│                    Data Storage                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  ~/.job-radar/                                       │    │
│  │    ├── profile.json (flat JSON - user profile)      │    │
│  │    └── config.json  (flat JSON - CLI defaults)      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Current Component Boundaries

| Component | Responsibility | File | Interfaces |
|-----------|----------------|------|------------|
| **Entry Point** | Bootstrap, wizard routing, error handling | `__main__.py` | Calls: banner, wizard, search.main() |
| **Banner** | Display ASCII art with profile name | `banner.py` | Reads profile.json for name only |
| **Wizard** | Interactive setup, profile creation/update | `wizard.py` | Writes: profile.json, config.json |
| **Search** | Argument parsing, job search orchestration | `search.py` | Reads: profile.json, config.json |
| **Path Resolution** | Platform-specific paths, frozen app detection | `paths.py` | Returns: data directory, resource paths |

### Current Data Flow

```
Program Start
    ↓
[__main__.py]
    ↓
Extract profile name for banner (read-only peek)
    ↓
Display banner
    ↓
Check --no-wizard flag
    ↓
   NO → Route based on profile existence:
         • First run: run_setup_wizard() → save profile.json, config.json
         • Profile exists: questionary prompt:
           - "Run search" → continue to search
           - "Update profile" → run_setup_wizard()
           - "Create new" → run_setup_wizard()
    ↓
   YES → Skip wizard (dev mode)
    ↓
[search.main()]
    ↓
Parse arguments with argparse
    ↓
Load profile.json via load_profile_with_recovery()
    ↓
Execute search with profile data
```

### Current Profile Schema

**profile.json** (required fields):
```json
{
  "name": "string",
  "years_experience": "int",
  "level": "string (derived: junior|mid|senior|principal)",
  "target_titles": ["string"],
  "core_skills": ["string"],
  "location": "string (optional)",
  "arrangement": ["string (optional)"],
  "domain_expertise": ["string (optional)"],
  "comp_floor": "int (optional)",
  "dealbreakers": ["string (optional)"]
}
```

**config.json** (search defaults):
```json
{
  "min_score": "float (default: 2.8)",
  "new_only": "bool (default: true)",
  "profile_path": "string (path to profile.json)"
}
```

## Integration Architecture for New Features

### Feature 1: Profile Preview on Startup

**What:** Display profile summary before search execution.

**Integration Point:** `__main__.py` between banner display and wizard routing.

**Implementation:**
- Add new function: `display_profile_summary(profile_data: dict)` in new module `profile_manager.py`
- Call after banner, before wizard prompt
- Read profile.json once (already loaded for banner name extraction)

**Data Flow:**
```
Banner Display
    ↓
Load profile.json
    ↓
display_profile_summary(profile) → Pretty-print key fields
    ↓
Continue to wizard prompt or search
```

**No Breaking Changes:** Preview is read-only, doesn't affect existing flow.

---

### Feature 2: Quick-Edit Mode

**What:** Update specific profile fields interactively without full wizard.

**Integration Point:** New questionary choice in `__main__.py` profile prompt + reuse wizard field prompts.

**Architecture Decision: Extend wizard.py vs new module?**

**Recommendation: Extend wizard.py** because:
- Field validators already exist (NonEmptyValidator, CommaSeparatedValidator, etc.)
- Field definitions already centralized in `questions` list
- Atomic file write logic (`_write_json_atomic`) already implemented
- Avoids code duplication

**Implementation:**
- Add function: `quick_edit_field(profile_path: Path, field_key: str) -> bool` in `wizard.py`
- Reuse existing validators and prompts from `questions` list
- Add new questionary choice in `__main__.py`: "Quick-edit a field"

**Data Flow:**
```
Profile exists prompt
    ↓
User selects "Quick-edit a field"
    ↓
quick_edit_field() in wizard.py:
    1. Load current profile.json
    2. questionary.select() field to edit
    3. Re-prompt with current value as default
    4. Validate with existing validator
    5. Show diff (old vs new)
    6. Confirm save
    7. Atomic write with _write_json_atomic()
```

**Key Pattern:** Git-style "show diff before commit" prevents accidental overwrites.

---

### Feature 3: CLI Update Flags

**What:** Non-interactive profile updates via CLI flags (e.g., `--update-skills`, `--set-min-score`).

**Integration Point:** `search.py` argument parser + early exit handlers.

**Architecture Decision: Modify profile in search.py vs new module?**

**Recommendation: New module `profile_manager.py`** because:
- Keeps `search.py` focused on search orchestration
- Profile modification is distinct from search execution
- Enables reuse across wizard.py and search.py

**Implementation:**
- Add flags to argparse in `search.py`:
  ```python
  profile_group.add_argument("--update-skills", metavar="SKILLS", help="Update skills list (comma-separated)")
  profile_group.add_argument("--set-min-score", type=float, help="Update min_score in config.json")
  profile_group.add_argument("--add-dealbreaker", metavar="TEXT", help="Add dealbreaker to profile")
  ```
- Add early exit handler in `search.main()` before search execution:
  ```python
  if args.update_skills or args.set_min_score or args.add_dealbreaker:
      from .profile_manager import update_profile_from_flags
      update_profile_from_flags(args, profile_path_str)
      sys.exit(0)
  ```

**Data Flow:**
```
search.main()
    ↓
Parse args with argparse
    ↓
Check for update flags (--update-skills, --set-min-score, etc.)
    ↓
   YES → Call update_profile_from_flags():
         1. Load current profile.json/config.json
         2. Apply changes
         3. Validate with wizard validators
         4. Show diff (old → new)
         5. Confirm or --yes flag for non-interactive
         6. Atomic write
         7. Exit
    ↓
   NO → Continue to search execution
```

---

### New Component: profile_manager.py

**Responsibility:** Profile CRUD operations, diff display, validation reuse.

**Functions:**
```python
def load_profile(path: Path) -> dict:
    """Load and validate profile.json."""

def save_profile(path: Path, data: dict, show_diff: bool = True) -> bool:
    """Save profile with optional diff preview and confirmation."""

def display_profile_summary(profile: dict):
    """Pretty-print profile for preview on startup."""

def update_profile_from_flags(args: Namespace, profile_path: str):
    """Apply CLI flag updates to profile/config with validation."""

def diff_profile(old: dict, new: dict) -> str:
    """Generate human-readable diff using difflib.unified_diff."""

def validate_profile_field(key: str, value: Any) -> bool:
    """Reuse wizard validators for individual fields."""
```

**Why a new module?**
- Centralizes profile I/O logic (currently scattered across wizard.py, search.py, __main__.py)
- Enables reuse across wizard, CLI flags, and future features (e.g., profile export/import)
- Maintains single responsibility: profile_manager = profile data, wizard = interactive flows

---

## Recommended Project Structure (Updated)

```
job_radar/
├── __main__.py           # Entry point - routing only (no profile I/O)
├── wizard.py             # Interactive flows (setup, quick-edit)
├── search.py             # Search orchestration + argparse
├── profile_manager.py    # NEW: Profile CRUD, validation, diff display
├── banner.py             # ASCII art display
├── paths.py              # Path resolution
├── config.py             # Config loading (existing)
└── ... (other modules)
```

### Structure Rationale

- **profile_manager.py:** Centralized profile operations avoid duplication across wizard.py and search.py
- **wizard.py remains interactive:** Keeps questionary flows separate from data operations
- **search.py stays lean:** Argument parsing + orchestration, delegates profile ops to profile_manager

---

## Architectural Patterns

### Pattern 1: Git-Style Diff Before Save

**What:** Show old vs new values before writing profile changes, require confirmation.

**When to use:** Any profile modification (quick-edit, CLI flags).

**Trade-offs:**
- PRO: Prevents accidental overwrites, user trust
- PRO: Familiar pattern (git commit, terraform apply)
- CON: Extra step (mitigated with --yes flag for automation)

**Example:**
```python
def save_profile(path: Path, data: dict, show_diff: bool = True) -> bool:
    if show_diff and path.exists():
        old_data = json.loads(path.read_text())
        diff = diff_profile(old_data, data)
        print("\nChanges to be saved:")
        print(diff)
        if not questionary.confirm("Save these changes?").ask():
            return False
    _write_json_atomic(path, data)
    return True
```

---

### Pattern 2: Validator Reuse from Wizard

**What:** Extract wizard validators into reusable functions for CLI flag validation.

**When to use:** CLI flags that update the same fields as wizard prompts.

**Trade-offs:**
- PRO: Single source of truth for validation rules
- PRO: Consistent error messages across interactive and non-interactive modes
- CON: Requires refactoring wizard.py to export validators

**Example:**
```python
# wizard.py - refactor
VALIDATORS = {
    'skills': CommaSeparatedValidator(min_items=1, field_name="skill"),
    'min_score': ScoreValidator(),
}

# profile_manager.py - reuse
from .wizard import VALIDATORS

def update_skills(profile: dict, skills_str: str) -> dict:
    validator = VALIDATORS['skills']
    # Apply validation...
    profile['core_skills'] = [s.strip() for s in skills_str.split(',')]
    return profile
```

---

### Pattern 3: Early Exit Handlers for Update Flags

**What:** Check for update flags before search execution, exit after update.

**When to use:** CLI flags that modify state but don't trigger search (e.g., `--update-skills`).

**Trade-offs:**
- PRO: Clear separation: update OR search, not both
- PRO: Avoids unexpected side effects (user expects update, not search)
- CON: Can't combine update + search in one command (acceptable: profile updates are infrequent)

**Example:**
```python
def main():
    args = parse_args()

    # Early exit: API setup
    if args.setup_apis:
        setup_apis()
        sys.exit(0)

    # Early exit: Profile updates
    if args.update_skills or args.set_min_score:
        update_profile_from_flags(args, profile_path)
        sys.exit(0)

    # Continue to search...
```

---

## Data Flow for New Features

### Request Flow: Profile Preview

```
Program Start
    ↓
[__main__.py] load profile for banner
    ↓
display_banner(profile_name)
    ↓
[NEW] display_profile_summary(profile)  ← Read-only, no state change
    ↓
Continue to wizard prompt or search
```

---

### Request Flow: Quick-Edit

```
User selects "Quick-edit a field"
    ↓
[wizard.py] quick_edit_field(profile_path, field_key)
    ↓
Load profile.json → old_data
    ↓
Prompt with questionary (reuse validator)
    ↓
Apply change → new_data
    ↓
diff_profile(old_data, new_data) → display diff
    ↓
Confirm save
    ↓
   YES → _write_json_atomic(profile_path, new_data)
    ↓
   NO → Discard changes
```

---

### Request Flow: CLI Update Flags

```
job-radar --update-skills "Python, Go, Rust"
    ↓
[search.py] parse_args() → args.update_skills = "Python, Go, Rust"
    ↓
Check args.update_skills is not None
    ↓
   YES → [profile_manager.py] update_profile_from_flags()
         1. Load profile.json
         2. Validate skills string with CommaSeparatedValidator
         3. Apply change: profile['core_skills'] = ["Python", "Go", "Rust"]
         4. Show diff
         5. Confirm (or --yes flag)
         6. Save with _write_json_atomic()
         7. sys.exit(0)
    ↓
   NO → Continue to search
```

---

## Integration Points Summary

| Feature | Modifies | Entry Point | New Functions | Reuses |
|---------|----------|-------------|---------------|--------|
| **Profile Preview** | None (read-only) | `__main__.py` | `profile_manager.display_profile_summary()` | Existing profile load |
| **Quick-Edit** | `profile.json` | `__main__.py` → `wizard.py` | `wizard.quick_edit_field()` | Validators, `_write_json_atomic()` |
| **CLI Update Flags** | `profile.json`, `config.json` | `search.py` (early exit) | `profile_manager.update_profile_from_flags()`, `diff_profile()` | Validators from wizard |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Silent Profile Updates

**What people do:** Update profile.json without showing changes or confirmation.

**Why it's wrong:** User loses trust, can't audit changes, accidental overwrites.

**Do this instead:** Always show diff before save, require confirmation (or --yes flag for automation).

---

### Anti-Pattern 2: Duplicate Validators

**What people do:** Copy-paste validation logic from wizard.py into profile_manager.py.

**Why it's wrong:** Rules drift apart, maintenance burden, inconsistent error messages.

**Do this instead:** Extract validators into shared constants/functions, import where needed.

---

### Anti-Pattern 3: Mixing Update + Search in One Command

**What people do:** Allow `job-radar --update-skills "X,Y" --min-score 3.0` to update profile AND run search.

**Why it's wrong:** Unexpected side effects, unclear intent (is this an update or a search?), harder to test.

**Do this instead:** Update flags exit early (after update), search flags continue to search. Mutually exclusive.

---

### Anti-Pattern 4: Profile I/O Scattered Everywhere

**What people do:** Load/save profile.json directly in `__main__.py`, `wizard.py`, `search.py` with inline logic.

**Why it's wrong:** Inconsistent validation, error handling, diff display. Hard to add features (e.g., profile backup).

**Do this instead:** Centralize in `profile_manager.py`, expose clean API (`load_profile()`, `save_profile()`).

---

## Backward Compatibility

### Existing Behavior Preserved

| Current Feature | Impact | Notes |
|-----------------|--------|-------|
| `--profile` flag | **None** | Still loads custom profile path |
| `--no-wizard` flag | **None** | Skips wizard, skips preview |
| Wizard on first run | **Enhanced** | Now shows preview after creation |
| questionary prompt | **Extended** | Adds "Quick-edit a field" option |
| `load_profile_with_recovery()` | **None** | Still auto-launches wizard on corrupt profile |

### Breaking Changes: NONE

All new features are additive:
- Profile preview is automatic (can be disabled with `--no-wizard`)
- Quick-edit is opt-in (new menu choice)
- CLI update flags are new arguments (don't conflict with existing)

---

## Suggested Build Order

### Phase 1: Foundation (profile_manager.py)

**Why first:** Centralizes profile I/O, enables all other features.

**Tasks:**
1. Create `profile_manager.py`
2. Move `load_profile()` from `search.py` to `profile_manager.py`
3. Refactor `_write_json_atomic()` from `wizard.py` to `profile_manager.py`
4. Add `diff_profile()` using Python's `difflib.unified_diff`
5. Add `display_profile_summary()` for pretty-printing

**Tests:**
- Load profile from valid/invalid/missing paths
- Diff detection (added fields, removed fields, changed values)
- Pretty-print formatting (all field types)

---

### Phase 2: Profile Preview

**Why second:** Simplest feature, validates profile_manager.py works.

**Tasks:**
1. Update `__main__.py` to call `display_profile_summary()` after banner
2. Add `--no-preview` flag to disable (or reuse `--no-wizard`)
3. Test with full profiles, minimal profiles, optional fields

**Tests:**
- Preview displays all fields correctly
- Preview skips when `--no-wizard` is set
- Preview handles missing optional fields gracefully

---

### Phase 3: Quick-Edit Mode

**Why third:** Reuses wizard validators, tests diff display interactively.

**Tasks:**
1. Extract validators from `wizard.py` into shared constants
2. Add `quick_edit_field()` function in `wizard.py`
3. Add "Quick-edit a field" to questionary menu in `__main__.py`
4. Integrate `diff_profile()` before save confirmation

**Tests:**
- Edit each field type (text, list, number, optional)
- Diff display shows correct changes
- Cancel without saving preserves original
- Validation rejects invalid inputs

---

### Phase 4: CLI Update Flags

**Why last:** Builds on all previous work (diff, validation, profile_manager).

**Tasks:**
1. Add argparse flags to `search.py`:
   - `--update-skills`
   - `--set-min-score`
   - `--add-dealbreaker`
   - `--yes` (skip confirmation)
2. Add early exit handler in `search.main()`
3. Implement `update_profile_from_flags()` in `profile_manager.py`
4. Reuse validators from Phase 3

**Tests:**
- Each flag updates correct field
- Diff shows before confirmation
- `--yes` skips confirmation
- Invalid values rejected with clear errors
- Early exit prevents search execution

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 profiles | Current flat JSON is fine. Single profile per user is typical. |
| 10-100 profiles | Consider profile name-based organization: `~/.job-radar/profiles/{name}.json`. Current design assumes one default profile + custom via `--profile`. |
| 100+ profiles | Add profile listing/switching UI. Not expected for CLI tool (personal use). |

### Scaling Priorities

1. **First bottleneck:** Profile schema evolution (adding/removing fields breaks old profiles).
   - **Fix:** Add schema version field, migration logic in `profile_manager.load_profile()`.

2. **Second bottleneck:** Diff display for large profiles (e.g., 100+ skills).
   - **Fix:** Use `difflib.context_diff` instead of `unified_diff`, or paginate output.

---

## Sources

### Codebase Analysis (HIGH Confidence)
- Analyzed existing architecture from:
  - `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/job_radar/__main__.py`
  - `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/job_radar/wizard.py`
  - `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/job_radar/search.py`
  - `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/job_radar/paths.py`

### CLI Patterns (MEDIUM Confidence)
- [argparse — Parser for command-line options, arguments and subcommands](https://docs.python.org/3/library/argparse.html) — Official argparse documentation
- [Build Command-Line Interfaces With Python's argparse – Real Python](https://realpython.com/command-line-interfaces-python-argparse/) — Comprehensive tutorial on argparse patterns
- [Git - git-config Documentation](https://git-scm.com/docs/git-config) — Git config architecture patterns (get, set, unset commands)
- [Creating a Git-Like Diff Viewer in Python Using Difflib](https://www.timsanteford.com/posts/creating-a-git-like-diff-viewer-in-python-using-difflib/) — Diff display implementation
- [Comparing Sequences in Python with difflib](https://thelinuxcode.com/comparing-sequences-in-python-with-difflib-often-misread-as-dfflib-practical-patterns-for-2026/) — Modern difflib usage patterns

---

*Architecture research for: Job Radar Profile Management Integration*
*Researched: 2026-02-11*
*Confidence: HIGH (codebase analysis) + MEDIUM (external patterns)*
