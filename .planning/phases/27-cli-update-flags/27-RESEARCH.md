# Phase 27: CLI Update Flags - Research

**Researched:** 2026-02-12
**Domain:** Python argparse CLI flag design with custom validation
**Confidence:** HIGH

## Summary

Phase 27 adds direct CLI flags for updating common profile fields (skills, min_score, titles) without entering interactive mode. The implementation requires custom argparse validators, mutually exclusive groups, and early exit patterns. The existing codebase already has robust validation in `profile_manager.py` (Phase 24) and `profile_editor.py` (Phase 26), which can be reused to ensure consistency.

The primary technical challenge is custom type validation in argparse for comma-separated strings and float ranges. Python's argparse provides `ArgumentTypeError` for validation failures and `add_mutually_exclusive_group()` for enforcing one-flag-per-command behavior. The existing `--view-profile` and `--edit-profile` flags demonstrate the early exit pattern (lines 462-568 in search.py).

**Primary recommendation:** Create custom argparse type validators that raise `ArgumentTypeError` with user-friendly messages. Reuse existing validation logic from `profile_manager.py` to ensure CLI flags use identical validation rules as interactive mode. Add mutually exclusive groups to prevent multiple update flags in one command.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Flag Naming & Syntax:**
- Long flags only — no short aliases (--update-skills, --set-min-score, --set-titles)
- Skills format: comma-separated quoted string (--update-skills "python,react,typescript")
- --update-skills replaces the entire list — simple, predictable
- Add --set-titles flag in addition to --update-skills and --set-min-score (titles change often enough)

**Output & Feedback:**
- Success output shows confirmation + diff (e.g., "Skills updated.\n  Old: python, react\n  New: python, react, typescript")
- Same backup message as interactive mode ("Profile backed up") — consistent across all update paths
- Always show output — same messages whether interactive or piped, no TTY detection
- --set-min-score shows context hint ("Min score updated to 3.5 (jobs scoring below 3.5 will be hidden)")

**Error Handling & Exit Codes:**
- Exit code 1 for all errors — simple, conventional
- Errors always suggest valid range (e.g., "min_score must be 0.0-5.0, got 7.0") — matches Phase 24 friendly tone
- No profile exists: error with guidance ("No profile found. Run 'job-radar' first to create one.")
- Allow clearing skills list with empty string — user might want to start fresh

**Flag Scope & Combinations:**
- One update flag per command — error if multiple update flags used, avoids partial-failure
- Update flags always exit without searching — clean separation of concerns
- Update flags and --view-profile are mutually exclusive — avoids order-of-operations confusion
- --help text includes examples for each update flag

### Claude's Discretion
- Exact argparse configuration and help text formatting
- Error message wording beyond the established friendly tone
- How empty string clearing interacts with validation (may need special case)

### Deferred Ideas (OUT OF SCOPE)
- --add-skill / --remove-skill granular flags — deferred per "Replace only for v1.5" decision, add later if users need them
- --run flag to combine update + search — keep exit-only for now, revisit based on usage
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| argparse | stdlib (3.10+) | CLI argument parsing | Built-in, zero dependencies, comprehensive validation support |
| pathlib | stdlib | Path manipulation | Modern path handling, already used throughout codebase |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| profile_manager | v1.1.4 (Phase 24) | Profile validation & save | Reuse validate_profile, save_profile for consistency |
| profile_editor | v1.1.4 (Phase 26) | Validation logic | Reuse CommaSeparatedValidator pattern from wizard.py |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| argparse | click, typer | More features but adds dependency; argparse sufficient for this phase |
| Custom validators | None (inline validation) | Inline is simpler but harder to test and maintain; custom functions better |

**Installation:**
No new dependencies — all functionality available in current stack.

## Architecture Patterns

### Recommended Implementation Structure

Add to existing `search.py`:
```
job_radar/
└── search.py           # Add validators + handlers in existing file
    ├── Validators (new section)
    │   ├── comma_separated_skills()
    │   ├── valid_score_range()
    │   └── comma_separated_titles()
    ├── parse_args()    # Add new flags
    └── main()          # Add early exit handlers
```

### Pattern 1: Custom Type Validators

**What:** Functions that convert and validate argparse string inputs

**When to use:** For any flag that requires validation beyond basic type conversion

**Example:**
```python
# Source: https://docs.python.org/3/library/argparse.html + project requirements
import argparse

def valid_score_range(value: str) -> float:
    """Validate min_score is a float in range 0.0-5.0.

    Raises argparse.ArgumentTypeError with user-friendly message on failure.
    Used as: parser.add_argument("--set-min-score", type=valid_score_range)
    """
    try:
        score = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"min_score must be a number, got '{value}'"
        )

    if not (0.0 <= score <= 5.0):
        raise argparse.ArgumentTypeError(
            f"min_score must be 0.0-5.0, got {score}"
        )

    return score

def comma_separated_skills(value: str) -> list[str]:
    """Parse comma-separated skill list with whitespace trimming.

    Empty string returns empty list (for clearing).
    Used as: parser.add_argument("--update-skills", type=comma_separated_skills)
    """
    if not value or value.strip() == "":
        return []  # Allow clearing with empty string

    items = [s.strip() for s in value.split(",") if s.strip()]

    if not items:
        raise argparse.ArgumentTypeError(
            "skills list cannot be empty (unless clearing with empty string)"
        )

    return items
```

### Pattern 2: Early Exit Handler

**What:** Handle flags immediately in main(), before loading profile or starting search

**When to use:** For flags that modify state and should not run search

**Example:**
```python
# Source: Existing --view-profile pattern (search.py lines 462-519)
def main():
    config = load_config(pre_args.config)
    args = parse_args(config)

    # Early exit handlers (before profile loading)
    if args.update_skills:
        handle_update_skills(args.update_skills, args.profile)
        sys.exit(0)  # Exit without searching

    if args.set_min_score:
        handle_set_min_score(args.set_min_score, args.profile, config)
        sys.exit(0)

    # ... continue to search flow only if no update flags
```

### Pattern 3: Mutually Exclusive Groups

**What:** Enforce that only one update flag is used per command

**When to use:** When flags should not be combined (avoids partial failure)

**Example:**
```python
# Source: https://docs.python.org/3/library/argparse.html
update_group = parser.add_mutually_exclusive_group()
update_group.add_argument(
    "--update-skills",
    type=comma_separated_skills,
    help="Replace skills list (comma-separated)",
)
update_group.add_argument(
    "--set-min-score",
    type=valid_score_range,
    help="Set minimum score threshold (0.0-5.0)",
)
update_group.add_argument(
    "--set-titles",
    type=comma_separated_titles,
    help="Replace target titles (comma-separated)",
)

# Make update flags and --view-profile mutually exclusive
view_edit_group = parser.add_mutually_exclusive_group()
view_edit_group.add_argument("--view-profile", ...)
view_edit_group.add_argument("--edit-profile", ...)
# Note: Can't nest mutually exclusive groups directly
# Solution: Check manually in main() if both categories used
```

### Pattern 4: Diff Display for CLI Updates

**What:** Show old vs. new values after successful update

**When to use:** For all update operations (consistency with interactive mode)

**Example:**
```python
# Source: profile_editor.py _show_diff_and_confirm() + user requirements
def display_update_diff(field_name: str, old_value, new_value):
    """Display confirmation message with old/new diff.

    Matches interactive mode format from profile_editor.py.
    """
    old_display = format_value(old_value)
    new_display = format_value(new_value)

    print(f"{field_name} updated.")
    print(f"  Old: {old_display}")
    print(f"  New: {C.BOLD}{new_display}{C.RESET}")

def format_value(value) -> str:
    """Format value for display (lists as comma-separated)."""
    if isinstance(value, list):
        return ", ".join(value) if value else "(empty)"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)
```

### Anti-Patterns to Avoid

- **Validating in handler instead of type:** Argparse type validators give automatic error formatting and --help integration
- **Partial updates on failure:** Never write profile if any validation fails; validate first, then save atomically
- **Different validation than interactive mode:** Reuse ScoreValidator logic from wizard.py to ensure CLI and interactive use identical rules
- **TTY-dependent output:** User decision is to always show output, no `sys.stdout.isatty()` checks

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Comma-separated parsing with validation | Custom split + try/catch logic | argparse type function with split() + validation | Automatic error formatting, --help integration, testability |
| Float range validation | if/else chains in handler | Custom type validator raising ArgumentTypeError | Consistent error messages, happens at parse time not runtime |
| Profile path resolution | Duplicate logic | Existing profile path resolution from lines 570-574 in search.py | Consistency with --view-profile, --edit-profile patterns |
| Diff display | Print statements in handler | Extract format_value() helper | Reuse in multiple update handlers |

**Key insight:** argparse type validators catch errors at parse time with professional formatting. Manual validation in handlers duplicates effort and gives inconsistent UX.

## Common Pitfalls

### Pitfall 1: Mutually Exclusive Groups with Multiple Categories

**What goes wrong:** argparse doesn't support nested mutually exclusive groups. You can't enforce "only one update flag AND not with --view-profile" in a single group.

**Why it happens:** Mutually exclusive groups are flat — can't nest one group inside another.

**How to avoid:** Create one mutually exclusive group for update flags only. Then manually check in main() if any update flag is present with --view-profile or --edit-profile:

```python
if args.view_profile and any([args.update_skills, args.set_min_score, args.set_titles]):
    parser.error("update flags cannot be used with --view-profile")
```

**Warning signs:** Error message "argument --view-profile: not allowed with argument --update-skills" doesn't appear when both are used.

### Pitfall 2: Empty String Validation Edge Case

**What goes wrong:** User decision allows clearing skills with empty string, but how should validation handle `--update-skills ""`?

**Why it happens:** Empty string is different from omitted flag. Comma parsing returns empty list for "", but should that be valid?

**How to avoid:** Special-case empty string in validator:

```python
def comma_separated_skills(value: str) -> list[str]:
    # Empty string means "clear the list" — valid operation
    if value == "":
        return []

    items = [s.strip() for s in value.split(",") if s.strip()]

    # But comma-only strings like ",,," are invalid
    if not items:
        raise argparse.ArgumentTypeError("skills list cannot be empty")

    return items
```

**Warning signs:** Test case `--update-skills ""` raises validation error instead of clearing list.

### Pitfall 3: Profile Not Found Handling

**What goes wrong:** Update flags fail with cryptic error if profile doesn't exist. Should they trigger wizard like main search does?

**Why it happens:** User decision says "error with guidance" not "trigger wizard" for CLI flags.

**How to avoid:** Load profile with try/except and give helpful error:

```python
def handle_update_skills(skills: list[str], profile_path_arg: str):
    profile_path = resolve_profile_path(profile_path_arg)

    if not profile_path.exists():
        print(f"{C.RED}Error: No profile found.{C.RESET}")
        print(f"\n{C.YELLOW}Tip:{C.RESET} Run 'job-radar' first to create one.")
        sys.exit(1)

    profile = load_profile(profile_path)
    # ... rest of update logic
```

**Warning signs:** Running `job-radar --update-skills "python"` with no profile shows ProfileNotFoundError traceback instead of friendly message.

### Pitfall 4: Exit Code Inconsistency

**What goes wrong:** Some errors exit with 0, others with 1, making shell scripts unpredictable.

**Why it happens:** Forgetting to sys.exit(1) after error messages, or using return instead of sys.exit in main().

**How to avoid:** Always pair error messages with `sys.exit(1)`:

```python
if not profile_path.exists():
    print("Error: No profile found.")
    sys.exit(1)  # MUST be explicit

# Success cases
print("Profile updated.")
sys.exit(0)  # Explicit exit after update
```

**Warning signs:** Shell script with `job-radar --set-min-score abc || echo "failed"` doesn't print "failed".

### Pitfall 5: Forgetting to Show Backup Message

**What goes wrong:** CLI updates don't show "Profile backed up" message that interactive mode shows.

**Why it happens:** `save_profile()` prints the message via profile_manager.py line 240, but only if backup succeeds. Might not trigger on first save.

**How to avoid:** Trust save_profile() to handle the message. Don't duplicate it in handler:

```python
# Good: Let save_profile() handle backup message
save_profile(profile, profile_path)
display_update_diff("Skills", old_skills, new_skills)

# Bad: Manually printing "Profile backed up" — duplicates profile_manager logic
```

**Warning signs:** "Profile backed up" appears twice, or doesn't appear when it should.

## Code Examples

Verified patterns from official sources and existing codebase:

### Complete --update-skills Implementation

```python
# Source: Synthesized from argparse docs + profile_manager.py patterns
def comma_separated_skills(value: str) -> list[str]:
    """Parse and validate comma-separated skills list.

    Empty string returns empty list (allows clearing).
    Raises ArgumentTypeError for invalid input.
    """
    if value == "":
        return []

    items = [s.strip() for s in value.split(",") if s.strip()]

    if not items:
        raise argparse.ArgumentTypeError(
            "skills list cannot be empty (use \"\" to clear)"
        )

    return items

def handle_update_skills(skills: list[str], profile_path_arg: str | None):
    """Update core_skills field and exit."""
    from pathlib import Path

    # Resolve profile path (same logic as main flow)
    if profile_path_arg:
        profile_path = Path(profile_path_arg).expanduser()
    else:
        from .paths import get_data_dir
        profile_path = get_data_dir() / "profile.json"

    # Check profile exists
    if not profile_path.exists():
        print(f"{C.RED}Error: No profile found.{C.RESET}")
        print(f"\n{C.YELLOW}Tip:{C.RESET} Run 'job-radar' first to create one.")
        sys.exit(1)

    # Load current profile
    try:
        profile = load_profile(profile_path)
    except ProfileValidationError as e:
        print(f"{C.RED}Error: {e.message}{C.RESET}")
        sys.exit(1)

    # Store old value for diff
    old_skills = profile.get("core_skills", [])

    # Update and save
    profile["core_skills"] = skills

    try:
        save_profile(profile, profile_path)
    except ProfileValidationError as e:
        print(f"{C.RED}Error: {e.message}{C.RESET}")
        sys.exit(1)

    # Display confirmation with diff
    print(f"\n{C.GREEN}Skills updated.{C.RESET}")
    print(f"  Old: {', '.join(old_skills) if old_skills else '(empty)'}")
    print(f"  New: {C.BOLD}{', '.join(skills) if skills else '(empty)'}{C.RESET}")
    print()

# Add to parse_args():
update_group = parser.add_mutually_exclusive_group()
update_group.add_argument(
    "--update-skills",
    type=comma_separated_skills,
    metavar="SKILLS",
    help='Replace skills list (comma-separated). Example: --update-skills "python,react,typescript"',
)

# Add to main() (before profile loading):
if args.update_skills is not None:
    handle_update_skills(args.update_skills, args.profile)
    sys.exit(0)
```

### Complete --set-min-score Implementation

```python
# Source: Synthesized from argparse docs + profile_manager validation patterns
def valid_score_range(value: str) -> float:
    """Validate min_score is a float in range 0.0-5.0."""
    try:
        score = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"min_score must be a number, got '{value}'"
        )

    if not (0.0 <= score <= 5.0):
        raise argparse.ArgumentTypeError(
            f"min_score must be 0.0-5.0, got {score}"
        )

    return score

def handle_set_min_score(score: float, profile_path_arg: str | None, config_dict: dict):
    """Update min_score in config and exit."""
    from pathlib import Path

    # Resolve config path (same logic as main flow)
    if config_dict.get("config_path"):
        config_path = Path(config_dict["config_path"]).expanduser()
    else:
        from .paths import get_data_dir
        config_path = get_data_dir() / "config.json"

    # Load current config
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    # Store old value for diff
    old_score = config.get("min_score", 2.8)

    # Update and save
    config["min_score"] = score

    from .profile_manager import _write_json_atomic
    _write_json_atomic(config_path, config)

    # Display confirmation with diff and context hint
    print(f"\n{C.GREEN}Min score updated to {score:.1f}{C.RESET}")
    print(f"  Old: {old_score:.1f}")
    print(f"  New: {C.BOLD}{score:.1f}{C.RESET}")
    print(f"\n{C.DIM}Jobs scoring below {score:.1f} will be hidden.{C.RESET}")
    print()

# Add to parse_args():
update_group.add_argument(
    "--set-min-score",
    type=valid_score_range,
    metavar="SCORE",
    help="Set minimum score threshold (0.0-5.0). Example: --set-min-score 3.5",
)

# Add to main():
if args.set_min_score is not None:
    handle_set_min_score(args.set_min_score, args.profile, config)
    sys.exit(0)
```

### Mutual Exclusion Check for Update Flags + View/Edit

```python
# Source: https://docs.python.org/3/library/argparse.html + manual checking pattern
# In main(), after parse_args():

# Check if any update flag is used with --view-profile or --edit-profile
update_flags = [
    args.update_skills is not None,
    args.set_min_score is not None,
    args.set_titles is not None,
]
view_edit_flags = [args.view_profile, args.edit_profile]

if any(update_flags) and any(view_edit_flags):
    print(f"{C.RED}Error: Update flags cannot be used with --view-profile or --edit-profile{C.RESET}")
    print(f"\n{C.YELLOW}Tip:{C.RESET} Use update flags alone to modify profile, or use --edit-profile for interactive editing.")
    sys.exit(1)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual validation in handlers | argparse type validators with ArgumentTypeError | argparse 3.2+ (2011) | Automatic error formatting, better --help text |
| sys.exit() after parser.parse_args() | Early return patterns with exit codes | Modern Python 3.10+ | Testable, cleaner separation |
| String concatenation for help text | textwrap.dedent() for multiline help | Python 3.0+ | Better formatting, readable code |

**Deprecated/outdated:**
- `optparse` module: Deprecated since Python 3.2, replaced by argparse
- Raising SystemExit(code) in validators: Use ArgumentTypeError for type validation failures

## Open Questions

1. **Should --set-titles allow empty string clearing like --update-skills?**
   - What we know: User decision allows clearing skills with empty string
   - What's unclear: Whether titles should have same behavior (validation requires at least one title)
   - Recommendation: Disallow empty string for titles (validator raises error) since target_titles is required field in profile validation

2. **Should CLI updates trigger profile display before exiting?**
   - What we know: User decision says "exit after update without running search"
   - What's unclear: Whether to display full profile after update (like --view-profile does)
   - Recommendation: No — just show diff and exit. User can run `job-radar --view-profile` separately if desired

3. **How should --set-min-score interact with profile.json min_score field?**
   - What we know: min_score can be in both profile.json (per-profile default) and config.json (global default)
   - What's unclear: Should --set-min-score update profile.json or config.json?
   - Recommendation: Update config.json (global default) like interactive editor does. Per user decision from Phase 26, min_score lives in config.json

## Sources

### Primary (HIGH confidence)
- [Python argparse official documentation](https://docs.python.org/3/library/argparse.html) - ArgumentTypeError, add_mutually_exclusive_group(), type parameter
- Existing codebase:
  - `/home/corye/Claude/Job-Radar/job_radar/search.py` - Early exit patterns (--view-profile, --edit-profile)
  - `/home/corye/Claude/Job-Radar/job_radar/profile_manager.py` - save_profile(), load_profile(), validate_profile()
  - `/home/corye/Claude/Job-Radar/job_radar/profile_editor.py` - Diff display patterns, validator reuse
  - `/home/corye/Claude/Job-Radar/tests/test_profile_manager.py` - Validation test patterns

### Secondary (MEDIUM confidence)
- [CheckRange class for argparse - GitHub Gist](https://gist.github.com/dmitriykovalev/2ab1aa33a8099ef2d514925d84aa89e7) - Float range validation patterns
- [Python argparse comma-separated lists - DevRescue](https://devrescue.com/python-argparse-comma-separated-list/) - Comma-separated validation
- [Testing sys.exit() with pytest - Medium](https://medium.com/python-pandemonium/testing-sys-exit-with-pytest-10c6e5f7726f) - Exit code testing patterns
- [Testing argparse with pytest - Simon Willison TIL](https://til.simonwillison.net/pytest/pytest-argparse) - CLI testing best practices
- [How to handle invalid arguments with argparse - GeeksforGeeks](https://www.geeksforgeeks.org/python/how-to-handle-invalid-arguments-with-argparse-in-python/) - ArgumentTypeError usage

### Tertiary (LOW confidence)
- None - all findings verified with official docs or existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - argparse is stdlib, existing validation code proven in Phase 24/26
- Architecture: HIGH - Early exit pattern already implemented for --view-profile, --edit-profile
- Pitfalls: MEDIUM - Edge cases (empty string, mutual exclusion) identified but need testing to confirm

**Research date:** 2026-02-12
**Valid until:** 2026-03-15 (30 days - stable stdlib domain)
