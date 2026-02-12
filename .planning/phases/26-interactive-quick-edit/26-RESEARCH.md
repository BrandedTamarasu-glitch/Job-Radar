# Phase 26: Interactive Quick-Edit - Research

**Researched:** 2026-02-12
**Domain:** Interactive CLI editing with questionary, profile validation, diff preview
**Confidence:** HIGH

## Summary

Phase 26 implements an interactive quick-edit flow for updating individual profile fields through a guided menu-driven interface. The phase leverages the existing questionary library (already in dependencies at version 2.1.1+), reuses validators from wizard.py, and integrates with profile_manager.py for atomic saves and validation. The technical domain is well-understood with clear patterns already established in the codebase.

Research confirms that questionary's `select()` and `text()` functions support the required `default` parameter for pre-filling values, and the library's styling system works seamlessly with the existing `_Colors` class pattern. The NO_COLOR standard applies only to color output, not text styling like bold - however, the current codebase disables BOLD when NO_COLOR is set, which we should maintain for consistency.

For diff preview, a simple side-by-side "Old: X → New: Y" format using bold styling (respects existing NO_COLOR behavior) is sufficient and clearer than full difflib output for single-field changes.

**Primary recommendation:** Build a loop-based field selector using questionary.select() with category-grouped choices showing current values, reuse all wizard validators unchanged, implement diff as simple f-string comparison, and structure as a loop that returns to menu after each save/cancel for multi-field editing sessions.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Edit Entry & Field Selection**
- Entry via **both** `--edit-profile` CLI flag AND the `--view-profile` edit prompt
- **Questionary select** menu with arrow-key navigation — consistent with existing wizard UX
- Menu **shows current values** next to each field name (e.g., "Name (Cory)")
- Fields **grouped by category** in the menu — Identity, Search, Filters, etc.

**Diff Preview & Confirmation**
- **Side-by-side** diff display (Old: X → New: Y)
- **Bold/plain styling** for changes — bold for new value, plain for old (works without color, respects NO_COLOR)
- Confirmation prompt: **"Apply this change? (y/N)"** — default No for safety
- Cancel message: **"Change discarded — profile unchanged."** — friendly, reassuring

**Input Handling Per Field Type**
- List fields (skills, titles, dealbreakers): **add/remove operations** via submenu for surgical edits on long lists
- List values entered as **comma-separated strings** when adding
- Boolean fields (new_only): **explicit Yes/No choice** menu, no auto-toggle
- Text/number inputs **pre-fill current value** so user can modify rather than retype

**Edit Flow After Save**
- After saving: **return to field menu** — supports editing multiple fields in one session
- After declining change: **return to field menu** — user can pick another field or retry
- Menu includes **explicit "Done — exit editor" option** as the last item
- After exiting editor: **offer to run a search** — "Profile updated. Run search now? (y/N)"

### Claude's Discretion

- Exact category grouping of fields in the menu
- Add/remove submenu design (how add vs remove are presented)
- Validation error re-prompt behavior
- How pre-fill works technically (questionary default parameter)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| questionary | 2.1.1+ | Interactive CLI prompts | Already in dependencies, proven in wizard.py, supports all required features (select, text, confirm, default values, validation) |
| profile_manager | N/A (local) | Profile I/O and validation | Phase 24 module - provides save_profile(), load_profile(), validate_profile(), exception hierarchy |
| tabulate | 0.9.0+ | Table formatting | Already in dependencies, used in profile_display.py for consistent styling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | Path manipulation | Profile path resolution (existing pattern in search.py) |
| json | stdlib | Config serialization | For config.json updates (min_score, new_only) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Simple f-string diff | difflib.unified_diff | Difflib adds complexity for single-field changes; side-by-side "Old → New" is clearer for CLI |
| questionary.checkbox | simple-term-menu | Questionary already in deps and consistent with wizard UX; no need for new dependency |
| Custom loop | inquirer library | Questionary already proven in codebase, team familiar with API |

**Installation:**
No new dependencies required - all tools already in pyproject.toml.

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── profile_editor.py    # New - Phase 26 interactive editor
├── wizard.py            # Existing - validators REUSED here
├── profile_manager.py   # Existing - save/load/validate
├── profile_display.py   # Existing - display functions
└── search.py            # Modified - add --edit-profile handler, update --view-profile edit prompt
```

### Pattern 1: Loop-Based Field Selector with Category Grouping
**What:** Main editor function runs a while True loop presenting a field selection menu, processes edits, and returns to menu until user selects "Done"
**When to use:** For multi-field editing sessions where users may want to change several fields sequentially
**Example:**
```python
def run_profile_editor(profile_path: Path, config_path: Path) -> bool:
    """Interactive profile editor - returns True if any changes saved."""
    changed = False

    while True:
        profile = load_profile(profile_path)
        config = load_config(config_path)

        # Build menu with category separators and current values
        choices = _build_field_choices(profile, config)

        field = questionary.select(
            "Which field would you like to edit?",
            choices=choices,
            style=custom_style
        ).ask()

        if field == "Done — exit editor":
            break

        # Edit selected field
        if _edit_field(field, profile, config, profile_path, config_path):
            changed = True
            # Loop continues - returns to menu

    return changed
```

### Pattern 2: Field Type Dispatching
**What:** Route each field to appropriate input handler based on type (text, list, boolean, number)
**When to use:** When different fields need different input patterns (single value vs add/remove list operations)
**Example:**
```python
def _edit_field(field_name: str, profile: dict, config: dict,
                profile_path: Path, config_path: Path) -> bool:
    """Edit single field - returns True if saved."""

    # Determine field type and current value
    if field_name in LIST_FIELDS:
        return _edit_list_field(field_name, profile, profile_path)
    elif field_name in BOOLEAN_FIELDS:
        return _edit_boolean_field(field_name, config, config_path)
    elif field_name in NUMBER_FIELDS:
        return _edit_number_field(field_name, profile, config, profile_path, config_path)
    else:
        return _edit_text_field(field_name, profile, profile_path)
```

### Pattern 3: List Field Add/Remove Submenu
**What:** For list fields, present submenu: "Add items", "Remove items", "Replace all", "Back"
**When to use:** For surgical edits to long lists without forcing user to retype entire list
**Example:**
```python
def _edit_list_field(field_name: str, profile: dict, profile_path: Path) -> bool:
    """Edit list field via add/remove submenu."""
    current_items = profile.get(field_name, [])

    action = questionary.select(
        f"How would you like to edit {field_name}?",
        choices=[
            "Add items",
            "Remove items",
            "Replace all",
            "Back"
        ]
    ).ask()

    if action == "Add items":
        new_items_str = questionary.text(
            f"Enter items to add (comma-separated):",
            validate=CommaSeparatedValidator(min_items=1)
        ).ask()
        new_items = [s.strip() for s in new_items_str.split(',') if s.strip()]
        updated = current_items + new_items
        return _save_with_confirmation(field_name, current_items, updated, profile, profile_path)

    elif action == "Remove items":
        if not current_items:
            print("No items to remove")
            return False
        to_remove = questionary.checkbox(
            f"Select items to remove:",
            choices=[questionary.Choice(item) for item in current_items]
        ).ask()
        updated = [item for item in current_items if item not in to_remove]
        return _save_with_confirmation(field_name, current_items, updated, profile, profile_path)

    # ... handle Replace all and Back
```

### Pattern 4: Diff Preview with Confirmation
**What:** Show before/after comparison using bold for new value, plain for old, then prompt for confirmation
**When to use:** Before every save operation to give user final review
**Example:**
```python
def _show_diff_and_confirm(field_name: str, old_value, new_value) -> bool:
    """Display side-by-side diff and ask for confirmation."""
    # Format values for display
    old_display = _format_value_for_diff(old_value)
    new_display = _format_value_for_diff(new_value)

    print(f"\n{field_name}:")
    print(f"  Old: {old_display}")
    print(f"  New: {C.BOLD}{new_display}{C.RESET}")

    confirmed = questionary.confirm(
        "Apply this change?",
        default=False,  # Safety: default to No
        style=custom_style
    ).ask()

    if confirmed:
        return True
    else:
        print("Change discarded — profile unchanged.")
        return False
```

### Pattern 5: Validator Reuse from wizard.py
**What:** Import all validators from wizard.py unchanged, apply same validation logic in editor
**When to use:** Always - ensures consistency between wizard and editor, DRY principle
**Example:**
```python
# In profile_editor.py
from .wizard import (
    NonEmptyValidator,
    CommaSeparatedValidator,
    ScoreValidator,
    YearsExperienceValidator,
    CompensationValidator,
    custom_style
)

def _edit_text_field(field_name: str, profile: dict, profile_path: Path) -> bool:
    """Edit simple text field with validation."""
    current = profile.get(field_name, "")

    new_value = questionary.text(
        f"Enter new value for {field_name}:",
        default=str(current),  # Pre-fill current value
        validate=FIELD_VALIDATORS[field_name],  # Reuse wizard validators
        style=custom_style
    ).ask()

    if new_value is None:  # Cancelled
        return False

    return _save_with_confirmation(field_name, current, new_value, profile, profile_path)
```

### Pattern 6: Category Separators in Menu
**What:** Use questionary.Separator() to create visual groupings in field selection menu
**When to use:** To organize fields into Identity, Search, Filters, etc. sections
**Example:**
```python
from questionary import Separator

def _build_field_choices(profile: dict, config: dict) -> list:
    """Build categorized menu choices showing current values."""
    choices = []

    # IDENTITY section
    choices.append(Separator("=== IDENTITY ==="))
    choices.append(f"Name ({profile.get('name', 'not set')})")
    choices.append(f"Experience ({profile.get('years_experience', 0)} years)")
    choices.append(f"Location ({profile.get('location', 'not set')})")

    # SKILLS section
    choices.append(Separator("=== SKILLS ==="))
    choices.append(f"Core Skills ({len(profile.get('core_skills', []))} items)")
    choices.append(f"Target Titles ({len(profile.get('target_titles', []))} items)")

    # FILTERS section
    choices.append(Separator("=== FILTERS ==="))
    choices.append(f"Dealbreakers ({len(profile.get('dealbreakers', []))} items)")
    choices.append(f"Min Score ({config.get('min_score', 2.8)})")

    # Exit option
    choices.append(Separator())
    choices.append("Done — exit editor")

    return choices
```

### Anti-Patterns to Avoid
- **Modifying profile dict in-place before confirmation:** Always work with copies, only call save_profile() after user confirms change
- **Skipping validation on edits:** Every edit MUST pass through same validators as wizard - no shortcuts
- **Using difflib for single-field diffs:** Overkill and harder to read than simple "Old: X → New: Y" format
- **Auto-toggling boolean fields:** User must explicitly choose Yes/No via questionary.confirm() - no silent toggles
- **Assuming NO_COLOR only affects color:** Current codebase disables BOLD when NO_COLOR is set - maintain this behavior for consistency

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Interactive menus | Custom curses-based menu system | questionary.select() | Already in deps, handles all edge cases (terminal size, colors, keyboard nav), proven in wizard.py |
| Input validation | New validation logic | wizard.py validators | DRY principle, ensures consistency, already tested |
| Diff display | difflib.unified_diff or HtmlDiff | Simple f-string "Old → New" format | Single-field changes don't need full diff algorithms; simpler is clearer |
| Atomic file writes | Manual temp file handling | profile_manager._write_json_atomic() | Already handles fsync, permissions, cleanup, cross-platform |
| Profile validation | Duplicate validation checks | profile_manager.validate_profile() | Central validation ensures no partial/invalid states saved |
| Value formatting | Custom formatters per field | Reuse _format_* helpers from profile_display.py | Consistency with display output (e.g., compensation as $X,XXX) |

**Key insight:** The codebase already has 90% of what this phase needs. Success comes from assembling existing pieces (questionary + validators + profile_manager + styling) into a new flow, not building new infrastructure.

## Common Pitfalls

### Pitfall 1: Breaking Validator Reuse
**What goes wrong:** Copying validator code into profile_editor.py instead of importing, leading to validation drift
**Why it happens:** Seems easier than managing imports, especially if validators need slight modifications
**How to avoid:** Import validators from wizard.py unchanged. If editor needs different behavior, create wrapper that calls wizard validator
**Warning signs:** Duplicate validator class definitions, divergent error messages between wizard and editor

### Pitfall 2: NO_COLOR and Bold Styling Confusion
**What goes wrong:** Applying bold styling when NO_COLOR is set, breaking user's explicit preference
**Why it happens:** Misunderstanding NO_COLOR spec - it technically only affects color, not other styling
**How to avoid:** Follow existing _Colors pattern in search.py which disables BOLD when NO_COLOR is set, even though spec doesn't require it
**Warning signs:** Bold text appearing in NO_COLOR=1 output, inconsistency with existing codebase styling

### Pitfall 3: Profile/Config Split Confusion
**What goes wrong:** Trying to save min_score and new_only to profile.json instead of config.json
**Why it happens:** Editor deals with "profile settings" conceptually, but they're split across two files
**How to avoid:** Clear field routing - profile fields go to profile_path, config fields (min_score, new_only) go to config_path
**Warning signs:** Validation errors about unexpected fields, config preferences not persisting

### Pitfall 4: Missing Validation Before Save
**What goes wrong:** Saving profile without calling validate_profile(), allowing invalid state
**Why it happens:** save_profile() validates internally, so seems redundant to validate in caller
**How to avoid:** Let save_profile() handle validation - it will raise ProfileValidationError on first issue (per Phase 24 decision 24-01)
**Warning signs:** Partial profile updates, confusing error messages about missing fields

### Pitfall 5: Category Separator Handling in Menu
**What goes wrong:** Treating Separator items as selectable choices, causing crashes when user somehow selects them
**Why it happens:** Not understanding questionary.Separator() vs regular choices
**How to avoid:** Use questionary.Separator() for category headers - they're automatically non-selectable
**Warning signs:** KeyError when mapping choice back to field name, unexpected crashes on menu selection

### Pitfall 6: List Edit Without Diff Preview
**What goes wrong:** Adding/removing list items without showing full before/after state
**Why it happens:** Add/remove operations feel incremental, so diff seems unnecessary
**How to avoid:** Always show full list diff (entire old list → entire new list) before saving, even for add/remove
**Warning signs:** User surprised by what was saved, no chance to review final list state

### Pitfall 7: Forgetting Search Offer After Exit
**What goes wrong:** User edits profile, exits editor, and has to manually run search
**Why it happens:** Editor function returns True/False for "changed", but caller doesn't act on it
**How to avoid:** In search.py --edit-profile and --view-profile handlers, check return value and offer "Run search now?" if True
**Warning signs:** User requests to "save and search" feature, poor UX for profile-then-search workflow

## Code Examples

Verified patterns from existing codebase and official documentation:

### Pre-filling Text Input with Current Value
```python
# Source: questionary documentation + wizard.py pattern (lines 399-401)
current_value = profile.get('name', '')

new_value = questionary.text(
    "What's your name?",
    default=current_value,  # Pre-fills with current value for editing
    validate=NonEmptyValidator(),
    style=custom_style
).ask()
```

### Select Menu with Category Separators and Current Values
```python
# Source: questionary documentation + wizard.py custom_style (lines 141-146)
from questionary import Separator

choices = [
    Separator("=== IDENTITY ==="),
    f"Name ({profile.get('name', 'not set')})",
    f"Location ({profile.get('location', 'not set')})",
    Separator("=== SKILLS ==="),
    f"Core Skills ({len(profile.get('core_skills', []))} items)",
    Separator(),
    "Done — exit editor"
]

field = questionary.select(
    "Which field would you like to edit?",
    choices=choices,
    style=custom_style  # Reuse wizard style
).ask()
```

### Checkbox for Multi-Select (Remove Items from List)
```python
# Source: questionary documentation - checkbox with Choice objects
current_skills = profile.get('core_skills', [])

to_remove = questionary.checkbox(
    "Select skills to remove:",
    choices=[questionary.Choice(skill) for skill in current_skills],
    style=custom_style
).ask()

if to_remove:
    updated_skills = [s for s in current_skills if s not in to_remove]
```

### Boolean Field Explicit Yes/No Menu
```python
# Source: wizard.py pattern (lines 427, 744-750)
current_new_only = config.get('new_only', True)

new_value = questionary.confirm(
    "Show only new jobs (not previously seen)?",
    default=current_new_only,  # Pre-fill current setting
    style=custom_style
).ask()

if new_value is not None:  # Not cancelled
    config['new_only'] = new_value
```

### Side-by-Side Diff with Bold Styling
```python
# Source: profile_display.py _Colors usage + user CONTEXT decision
from .search import _Colors as C

def _show_diff_and_confirm(field_name: str, old_value, new_value) -> bool:
    """Show side-by-side diff and confirm - respects NO_COLOR."""
    # Format values (handle lists, numbers, etc.)
    old_display = _format_value_for_diff(old_value)
    new_display = _format_value_for_diff(new_value)

    print(f"\n{field_name}:")
    print(f"  Old: {old_display}")  # Plain text
    print(f"  New: {C.BOLD}{new_display}{C.RESET}")  # Bold for new value

    confirmed = questionary.confirm(
        "Apply this change?",
        default=False,  # User decision: default No for safety
        style=custom_style
    ).ask()

    if not confirmed:
        print("Change discarded — profile unchanged.")  # User decision: friendly message

    return confirmed

def _format_value_for_diff(value) -> str:
    """Format value for diff display."""
    if isinstance(value, list):
        return ", ".join(value) if value else "(empty)"
    elif isinstance(value, (int, float)):
        return str(value)
    elif value is None or value == "":
        return "(not set)"
    else:
        return str(value)
```

### Atomic Save with Validation (Reuse from profile_manager)
```python
# Source: profile_manager.py save_profile() (lines 222-245)
from .profile_manager import save_profile, ProfileValidationError

try:
    # save_profile() validates internally and raises on first error (24-01)
    save_profile(profile_data, profile_path)
    print(f"{C.GREEN}Profile updated{C.RESET}")
    return True
except ProfileValidationError as e:
    print(f"{C.RED}Error: {e.message}{C.RESET}")
    # Per user decision: re-prompt on validation error
    return False
```

### Main Editor Loop with Multi-Field Support
```python
# Source: wizard.py post-summary edit loop pattern (lines 519-751)
def run_profile_editor(profile_path: Path, config_path: Path) -> bool:
    """Run interactive profile editor - returns True if any changes saved."""
    any_changes = False

    while True:
        # Reload profile/config each iteration to show latest values
        profile = load_profile(profile_path)
        config = load_config(config_path)

        choices = _build_field_choices(profile, config)

        field = questionary.select(
            "Which field would you like to edit?",
            choices=choices,
            style=custom_style
        ).ask()

        if field is None:  # Ctrl+C
            break

        if "Done" in field:  # User decision: explicit exit option
            break

        # Parse field name from "FieldName (current_value)" format
        field_name = field.split("(")[0].strip()

        # Edit field - returns True if saved
        if _edit_field(field_name, profile, config, profile_path, config_path):
            any_changes = True
            # User decision: return to menu after save
        # User decision: return to menu after decline too

    return any_changes
```

### Integration with --view-profile (Replace Placeholder)
```python
# Source: search.py lines 479-486 (replace placeholder)
# In search.py main():

if args.view_profile:
    # ... existing display logic ...

    # Replace placeholder with actual editor call
    try:
        edit = input("\nWant to edit? (y/N) ").strip().lower()
        if edit == 'y':
            from .profile_editor import run_profile_editor
            from .paths import get_data_dir

            data_dir = get_data_dir()
            profile_path = data_dir / "profile.json"
            config_path = data_dir / "config.json"

            if run_profile_editor(profile_path, config_path):
                # User decision: offer to run search after edit
                search = questionary.confirm(
                    "Profile updated. Run search now?",
                    default=False,
                    style=custom_style
                ).ask()
                if search:
                    # Fall through to normal search flow
                    pass  # TODO: refactor to avoid sys.exit(0) blocking search
    except (EOFError, KeyboardInterrupt):
        pass

    sys.exit(0)
```

### Add/Remove Submenu for List Fields
```python
# Source: User decision - surgical edits via submenu
def _edit_list_field(field_name: str, profile: dict, profile_path: Path) -> bool:
    """Edit list field with add/remove/replace submenu."""
    current_items = profile.get(field_name, [])

    while True:  # Allow multiple operations before confirming
        action = questionary.select(
            f"Edit {field_name} ({len(current_items)} items):",
            choices=[
                "Add items",
                "Remove items",
                "Replace all",
                "Back to field menu"
            ],
            style=custom_style
        ).ask()

        if action is None or "Back" in action:
            return False  # No changes

        if "Add" in action:
            # User decision: comma-separated input when adding
            new_items = questionary.text(
                f"Enter items to add (comma-separated):",
                validate=CommaSeparatedValidator(min_items=1, field_name="item"),
                style=custom_style
            ).ask()

            if new_items:
                items_list = [s.strip() for s in new_items.split(',') if s.strip()]
                updated = current_items + items_list

                # User decision: show diff even for add operation
                if _show_diff_and_confirm(field_name, current_items, updated):
                    profile[field_name] = updated
                    save_profile(profile, profile_path)
                    return True  # Changed and saved

        elif "Remove" in action:
            if not current_items:
                print(f"No {field_name} to remove")
                continue

            to_remove = questionary.checkbox(
                f"Select {field_name} to remove:",
                choices=[questionary.Choice(item) for item in current_items],
                style=custom_style
            ).ask()

            if to_remove:
                updated = [item for item in current_items if item not in to_remove]

                if _show_diff_and_confirm(field_name, current_items, updated):
                    profile[field_name] = updated
                    save_profile(profile, profile_path)
                    return True

        elif "Replace" in action:
            current_str = ", ".join(current_items)
            new_items = questionary.text(
                f"Enter all {field_name} (comma-separated):",
                default=current_str,  # Pre-fill for editing
                validate=CommaSeparatedValidator(min_items=1, field_name="item"),
                style=custom_style
            ).ask()

            if new_items:
                updated = [s.strip() for s in new_items.split(',') if s.strip()]

                if _show_diff_and_confirm(field_name, current_items, updated):
                    profile[field_name] = updated
                    save_profile(profile, profile_path)
                    return True
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON editing | Interactive CLI wizards | ~2020+ | Questionary and similar libraries made CLI UX competitive with web forms |
| difflib for all diffs | Contextual diff strategies | Ongoing | Complex diffs (code, multi-line) still use difflib; simple field changes use "Old → New" format |
| Color-only accessibility | NO_COLOR standard | 2021+ (spec) | Universal standard for disabling color, but implementations vary on bold/style handling |
| Auto-save on edit | Explicit confirmation | UX best practice | User control and review before destructive actions |

**Deprecated/outdated:**
- **Questionary < 2.0:** Version 1.x had different API for some prompt types - current 2.1.1 is stable
- **prompt_toolkit 2.x:** Questionary 2.1.1 uses prompt_toolkit 3.x internally (transparent to us, but good to know)
- **Global NO_COLOR disabling all styles:** Spec clarified that NO_COLOR is color-only, but we maintain existing behavior (disables BOLD) for consistency

## Open Questions

1. **Should editor support bulk operations (edit multiple fields without returning to menu)?**
   - What we know: User decision says "return to field menu" after each save/decline
   - What's unclear: Whether power users would benefit from "edit name, titles, skills, then review all diffs and save once"
   - Recommendation: Implement as specified (one field at a time) - can add bulk mode in Phase 27+ if requested

2. **How to handle validation errors that suggest re-running wizard?**
   - What we know: profile_manager.validate_profile() can raise ProfileValidationError
   - What's unclear: If editor breaks required field (e.g., deletes all skills), should we force wizard or allow empty list temporarily?
   - Recommendation: Let save_profile() validation catch it and display error, re-prompt for that field (same as wizard /back behavior)

3. **Should config.json also use save_profile() pattern (backup, atomic write)?**
   - What we know: Config doesn't have backup/validation like profile (wizard.py line 757 uses _write_json directly)
   - What's unclear: Whether config changes justify backup overhead
   - Recommendation: Follow wizard pattern - use _write_json_atomic for config (no backup), save_profile for profile (with backup)

4. **Exit editor vs exit application Ctrl+C handling?**
   - What we know: Questionary.ask() returns None on Ctrl+C
   - What's unclear: Should Ctrl+C in field selection exit editor cleanly or bubble up to application exit?
   - Recommendation: Treat None as "back to menu" in field selector, continue loop - only "Done" option exits editor

## Sources

### Primary (HIGH confidence)
- Questionary 2.1.1 official documentation: https://questionary.readthedocs.io/en/stable/pages/types.html
- Questionary PyPI page (version verification): https://pypi.org/project/questionary/
- NO_COLOR standard specification: https://no-color.org/
- Job Radar codebase: wizard.py, profile_manager.py, profile_display.py, search.py (Phase 24-25 implementations)

### Secondary (MEDIUM confidence)
- [Question Types — Questionary 2.0.1 documentation](https://questionary.readthedocs.io/en/stable/pages/types.html) - Question type parameters and features
- [Questionary GitHub repository](https://github.com/tmbo/questionary) - Examples and issue discussions
- [CLI Design Best Practices](https://codyaray.com/2020/07/cli-design-best-practices) - Field grouping and help organization
- [ANSI escape code - Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code) - Bold styling codes and terminal support

### Tertiary (LOW confidence)
- [simple-term-menu PyPI](https://pypi.org/project/simple-term-menu/) - Alternative menu library (not used, mentioned for completeness)
- [difflib Python stdlib](https://docs.python.org/3/library/difflib.html) - Considered but not used for single-field diffs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Questionary already in deps at 2.1.1, all features verified in official docs, proven in wizard.py
- Architecture: HIGH - Clear patterns from wizard.py reuse, profile_manager integration points documented, loop-based menu is standard Python
- Pitfalls: MEDIUM-HIGH - Identified from codebase analysis and common questionary gotchas, NO_COLOR behavior verified against spec

**Research date:** 2026-02-12
**Valid until:** ~2026-04-12 (60 days - stable domain, questionary 2.x API unlikely to change)
