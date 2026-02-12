"""Interactive profile editor for quick field updates.

Provides a loop-based field selection menu with field-type dispatching,
diff preview with confirmation, and reuse of all wizard validators.
Accessible via --edit-profile flag and the --view-profile edit prompt.
"""

from pathlib import Path

import questionary
from questionary import Choice, Separator

from .config import load_config
from .profile_manager import (
    ProfileValidationError,
    _write_json_atomic,
    load_profile,
    save_profile,
)
from .search import _Colors as C
from .wizard import (
    CommaSeparatedValidator,
    CompensationValidator,
    NonEmptyValidator,
    ScoreValidator,
    YearsExperienceValidator,
    custom_style,
)

# ---------------------------------------------------------------------------
# Field metadata
# ---------------------------------------------------------------------------

# Fields stored in profile.json
PROFILE_FIELDS = {
    "name": {"display": "Name", "type": "text", "category": "IDENTITY"},
    "years_experience": {
        "display": "Experience",
        "type": "number",
        "category": "IDENTITY",
    },
    "location": {
        "display": "Location",
        "type": "text",
        "category": "IDENTITY",
        "optional": True,
    },
    "core_skills": {"display": "Core Skills", "type": "list", "category": "SKILLS"},
    "target_titles": {
        "display": "Target Titles",
        "type": "list",
        "category": "SKILLS",
    },
    "dealbreakers": {
        "display": "Dealbreakers",
        "type": "list",
        "category": "FILTERS",
        "optional": True,
    },
}

# Fields stored in config.json
CONFIG_FIELDS = {
    "min_score": {"display": "Min Score", "type": "number", "category": "PREFERENCES"},
    "new_only": {
        "display": "New Jobs Only",
        "type": "boolean",
        "category": "PREFERENCES",
    },
}

# Validators reused from wizard.py (zero duplication)
FIELD_VALIDATORS = {
    "name": NonEmptyValidator(),
    "years_experience": YearsExperienceValidator(),
    "core_skills": CommaSeparatedValidator(min_items=1, field_name="skill"),
    "target_titles": CommaSeparatedValidator(min_items=1, field_name="title"),
    "min_score": ScoreValidator(),
}

# Categories in display order
_CATEGORIES = ["IDENTITY", "SKILLS", "FILTERS", "PREFERENCES"]


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------


def _format_value_for_diff(value) -> str:
    """Format any value type for diff display."""
    if isinstance(value, list):
        return ", ".join(value) if value else "(empty)"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None or value == "":
        return "(not set)"
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)


# ---------------------------------------------------------------------------
# Diff preview and confirmation
# ---------------------------------------------------------------------------


def _show_diff_and_confirm(field_key: str, old_value, new_value) -> bool:
    """Display side-by-side diff and ask for confirmation.

    Uses bold styling for the new value (respects NO_COLOR via _Colors).
    Confirmation defaults to No for safety.
    """
    old_display = _format_value_for_diff(old_value)
    new_display = _format_value_for_diff(new_value)

    # Get display name from field metadata
    if field_key in PROFILE_FIELDS:
        display_name = PROFILE_FIELDS[field_key]["display"]
    elif field_key in CONFIG_FIELDS:
        display_name = CONFIG_FIELDS[field_key]["display"]
    else:
        display_name = field_key

    print(f"\n{display_name}:")
    print(f"  Old: {old_display}")
    print(f"  New: {C.BOLD}{new_display}{C.RESET}")

    confirmed = questionary.confirm(
        "Apply this change?",
        default=False,
        style=custom_style,
    ).ask()

    if confirmed is None:
        # Ctrl+C -- treat as decline
        print("Change discarded -- profile unchanged.")
        return False

    if not confirmed:
        print("Change discarded -- profile unchanged.")

    return confirmed


# ---------------------------------------------------------------------------
# Field menu builder
# ---------------------------------------------------------------------------


def _build_field_choices(profile: dict, config: dict) -> list:
    """Build categorized menu choices showing current values.

    Returns a list of Choice and Separator objects suitable for
    questionary.select().
    """
    choices: list = []

    # Group fields by category
    for category in _CATEGORIES:
        # Collect fields for this category
        fields_in_cat: list[tuple[str, dict, dict]] = []

        for key, meta in PROFILE_FIELDS.items():
            if meta["category"] == category:
                fields_in_cat.append((key, meta, profile))

        for key, meta in CONFIG_FIELDS.items():
            if meta["category"] == category:
                fields_in_cat.append((key, meta, config))

        if not fields_in_cat:
            continue

        choices.append(Separator(f"--- {category} ---"))

        for key, meta, data in fields_in_cat:
            value = data.get(key)
            field_type = meta["type"]

            if field_type == "list":
                items = value if isinstance(value, list) else []
                display_val = f"{len(items)} items"
            elif field_type == "boolean":
                display_val = "Yes" if value else "No"
            elif field_type == "number" and key == "years_experience":
                display_val = f"{value} years" if value is not None else "(not set)"
            elif value is not None and value != "":
                display_val = str(value)
            else:
                display_val = "(not set)"

            title = f"{meta['display']} ({display_val})"
            choices.append(Choice(title=title, value=key))

    # Exit option
    choices.append(Separator())
    choices.append(Choice(title="Done -- exit editor", value="done"))

    return choices


# ---------------------------------------------------------------------------
# Field editors
# ---------------------------------------------------------------------------


def _edit_text_field(field_key: str, data: dict, save_path: Path) -> bool:
    """Edit a simple text field (name, location)."""
    current = data.get(field_key, "")
    meta = PROFILE_FIELDS[field_key]
    validator = FIELD_VALIDATORS.get(field_key)

    result = questionary.text(
        f"Enter new value for {meta['display']}:",
        default=str(current) if current else "",
        validate=validator,
        style=custom_style,
    ).ask()

    if result is None:
        return False

    new_value = result.strip()

    # For optional fields: empty string means clear the field
    if meta.get("optional") and not new_value:
        if field_key in data:
            if not _show_diff_and_confirm(field_key, current, None):
                return False
            del data[field_key]
            try:
                save_profile(data, save_path)
                print(f"{C.GREEN}Profile updated.{C.RESET}")
                return True
            except ProfileValidationError as e:
                print(f"{C.RED}Error: {e.message}{C.RESET}")
                return False
        return False

    if new_value == current:
        print("No change.")
        return False

    if not _show_diff_and_confirm(field_key, current, new_value):
        return False

    data[field_key] = new_value
    try:
        save_profile(data, save_path)
        print(f"{C.GREEN}Profile updated.{C.RESET}")
        return True
    except ProfileValidationError as e:
        print(f"{C.RED}Error: {e.message}{C.RESET}")
        return False


def _edit_number_field(
    field_key: str, data: dict, save_path: Path, *, is_config: bool
) -> bool:
    """Edit a numeric field (years_experience, min_score)."""
    current = data.get(field_key, 0)
    validator = FIELD_VALIDATORS.get(field_key)

    if field_key in CONFIG_FIELDS:
        display_name = CONFIG_FIELDS[field_key]["display"]
    else:
        display_name = PROFILE_FIELDS[field_key]["display"]

    result = questionary.text(
        f"Enter new value for {display_name}:",
        default=str(current),
        validate=validator,
        style=custom_style,
    ).ask()

    if result is None:
        return False

    # Parse the value
    if field_key == "min_score":
        new_value = float(result.strip())
    else:
        new_value = int(result.strip())

    if new_value == current:
        print("No change.")
        return False

    if not _show_diff_and_confirm(field_key, current, new_value):
        return False

    data[field_key] = new_value

    # Recalculate level when years_experience changes
    if field_key == "years_experience":
        if new_value < 2:
            data["level"] = "junior"
        elif new_value < 5:
            data["level"] = "mid"
        elif new_value < 10:
            data["level"] = "senior"
        else:
            data["level"] = "principal"

    try:
        if is_config:
            _write_json_atomic(save_path, data)
        else:
            save_profile(data, save_path)
        print(f"{C.GREEN}{'Config' if is_config else 'Profile'} updated.{C.RESET}")
        return True
    except ProfileValidationError as e:
        print(f"{C.RED}Error: {e.message}{C.RESET}")
        return False


def _edit_boolean_field(
    field_key: str, config: dict, config_path: Path
) -> bool:
    """Edit a boolean field (new_only) with explicit Yes/No choice."""
    current_value = config.get(field_key, True)
    display_name = CONFIG_FIELDS[field_key]["display"]

    result = questionary.confirm(
        f"{display_name} -- show only new jobs?",
        default=current_value,
        style=custom_style,
    ).ask()

    if result is None:
        return False

    if result == current_value:
        print("No change.")
        return False

    old_display = "Yes" if current_value else "No"
    new_display = "Yes" if result else "No"

    if not _show_diff_and_confirm(field_key, old_display, new_display):
        return False

    config[field_key] = result
    _write_json_atomic(config_path, config)
    print(f"{C.GREEN}Config updated.{C.RESET}")
    return True


def _edit_list_field(
    field_key: str, profile: dict, profile_path: Path
) -> bool:
    """Edit a list field via add/remove/replace submenu."""
    current_items = profile.get(field_key, [])
    display_name = PROFILE_FIELDS[field_key]["display"]

    action = questionary.select(
        f"Edit {display_name} ({len(current_items)} items):",
        choices=[
            "Add items",
            "Remove items",
            "Replace all",
            "Back to field menu",
        ],
        style=custom_style,
    ).ask()

    if action is None or action == "Back to field menu":
        return False

    if action == "Add items":
        return _list_add(field_key, current_items, profile, profile_path)
    elif action == "Remove items":
        return _list_remove(field_key, current_items, profile, profile_path)
    elif action == "Replace all":
        return _list_replace(field_key, current_items, profile, profile_path)

    return False


def _list_add(
    field_key: str,
    current_items: list,
    profile: dict,
    profile_path: Path,
) -> bool:
    """Add items to a list field."""
    result = questionary.text(
        "Enter items to add (comma-separated):",
        validate=CommaSeparatedValidator(min_items=1, field_name="item"),
        style=custom_style,
    ).ask()

    if result is None:
        return False

    new_items = [s.strip() for s in result.split(",") if s.strip()]
    updated = current_items + new_items

    if not _show_diff_and_confirm(field_key, current_items, updated):
        return False

    profile[field_key] = updated
    try:
        save_profile(profile, profile_path)
        print(f"{C.GREEN}Profile updated.{C.RESET}")
        return True
    except ProfileValidationError as e:
        print(f"{C.RED}Error: {e.message}{C.RESET}")
        return False


def _list_remove(
    field_key: str,
    current_items: list,
    profile: dict,
    profile_path: Path,
) -> bool:
    """Remove items from a list field."""
    if not current_items:
        print("No items to remove.")
        return False

    to_remove = questionary.checkbox(
        "Select items to remove:",
        choices=[Choice(title=item, value=item) for item in current_items],
        style=custom_style,
    ).ask()

    if not to_remove:
        return False

    updated = [item for item in current_items if item not in to_remove]

    if not _show_diff_and_confirm(field_key, current_items, updated):
        return False

    profile[field_key] = updated
    try:
        save_profile(profile, profile_path)
        print(f"{C.GREEN}Profile updated.{C.RESET}")
        return True
    except ProfileValidationError as e:
        print(f"{C.RED}Error: {e.message}{C.RESET}")
        return False


def _list_replace(
    field_key: str,
    current_items: list,
    profile: dict,
    profile_path: Path,
) -> bool:
    """Replace all items in a list field."""
    current_str = ", ".join(current_items)
    validator = FIELD_VALIDATORS.get(field_key, CommaSeparatedValidator(min_items=1, field_name="item"))

    result = questionary.text(
        f"Enter all items (comma-separated):",
        default=current_str,
        validate=validator,
        style=custom_style,
    ).ask()

    if result is None:
        return False

    updated = [s.strip() for s in result.split(",") if s.strip()]

    if updated == current_items:
        print("No change.")
        return False

    if not _show_diff_and_confirm(field_key, current_items, updated):
        return False

    profile[field_key] = updated
    try:
        save_profile(profile, profile_path)
        print(f"{C.GREEN}Profile updated.{C.RESET}")
        return True
    except ProfileValidationError as e:
        print(f"{C.RED}Error: {e.message}{C.RESET}")
        return False


# ---------------------------------------------------------------------------
# Field dispatcher
# ---------------------------------------------------------------------------


def _edit_field(
    field_key: str,
    profile: dict,
    config: dict,
    profile_path: Path,
    config_path: Path,
) -> bool:
    """Dispatch to appropriate editor based on field type. Returns True if saved."""
    if field_key in CONFIG_FIELDS:
        field_meta = CONFIG_FIELDS[field_key]
    else:
        field_meta = PROFILE_FIELDS[field_key]

    field_type = field_meta["type"]

    if field_type == "list":
        return _edit_list_field(field_key, profile, profile_path)
    elif field_type == "boolean":
        return _edit_boolean_field(field_key, config, config_path)
    elif field_type == "number":
        if field_key in CONFIG_FIELDS:
            return _edit_number_field(field_key, config, config_path, is_config=True)
        else:
            return _edit_number_field(field_key, profile, profile_path, is_config=False)
    else:  # text
        return _edit_text_field(field_key, profile, profile_path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_profile_editor(profile_path: Path, config_path: Path) -> bool:
    """Run interactive profile editor. Returns True if any changes were saved.

    Main editor loop: presents a categorized field menu, dispatches to
    appropriate field editor, shows diff preview with confirmation,
    and loops until user selects "Done".

    Parameters
    ----------
    profile_path : Path
        Path to profile.json file.
    config_path : Path
        Path to config.json file.

    Returns
    -------
    bool
        True if any changes were saved during the session.
    """
    any_changes = False

    while True:
        # Reload each iteration so menu shows latest values after edits
        profile = load_profile(profile_path)
        config = load_config(str(config_path))

        choices = _build_field_choices(profile, config)

        field_key = questionary.select(
            "Which field would you like to edit?",
            choices=choices,
            style=custom_style,
        ).ask()

        if field_key is None:
            # Ctrl+C -- exit editor
            break

        if field_key == "done":
            break

        if _edit_field(field_key, profile, config, profile_path, config_path):
            any_changes = True

    return any_changes
