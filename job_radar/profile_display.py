"""Formatted profile preview display using tabulate.

Prints a bordered, sectioned table showing non-empty profile fields
with a branded header line. Respects NO_COLOR via the existing
_Colors class from search.py.
"""

from __future__ import annotations

from tabulate import tabulate

from .search import _Colors as C


def _format_comp_floor(value: int | float) -> str:
    """Format compensation floor as dollar amount with comma separator."""
    return f"${int(value):,}"


def _format_experience(profile: dict) -> str:
    """Format years_experience with optional level suffix."""
    years = profile["years_experience"]
    level = profile.get("level")
    if level:
        return f"{years} years ({level} level)"
    return f"{years} years"


def _section_rows(label: str, fields: list[tuple[str, str]]) -> list[list[str]]:
    """Build rows for a section, returning empty list if all fields are empty."""
    if not fields:
        return []
    return [[f"{C.BOLD}{label}{C.RESET}", ""]] + [[k, v] for k, v in fields]


def display_profile(profile: dict, config: dict | None = None) -> None:
    """Display formatted profile preview with sections and borders.

    Parameters
    ----------
    profile : dict
        Validated profile dict from profile_manager.load_profile().
    config : dict | None
        Config dict from config.load_config() for preferences display.

    Notes
    -----
    - Filters out None/empty fields (only shows set fields).
    - Uses tabulate with simple_grid format for bordered output.
    - Respects NO_COLOR via _Colors class from search.py.
    - Groups fields into sections: Identity, Skills, Preferences, Filters.
    """
    if config is None:
        config = {}

    # --- Branded header ---
    header_text = " Job Radar Profile "
    pad_total = 60 - len(header_text)
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left
    header_line = f"{'=' * pad_left}{header_text}{'=' * pad_right}"
    print(f"\n{C.CYAN}{header_line}{C.RESET}")

    # --- Build section rows ---
    all_rows: list[list[str]] = []

    # IDENTITY section
    identity_fields: list[tuple[str, str]] = []
    if profile.get("name"):
        identity_fields.append(("Name", profile["name"]))
    if profile.get("years_experience") is not None:
        identity_fields.append(("Experience", _format_experience(profile)))
    if profile.get("location"):
        identity_fields.append(("Location", profile["location"]))
    if profile.get("arrangement"):
        identity_fields.append(("Arrangement", ", ".join(profile["arrangement"])))

    all_rows.extend(_section_rows("IDENTITY", identity_fields))

    # SKILLS section
    skills_fields: list[tuple[str, str]] = []
    if profile.get("core_skills"):
        skills_fields.append(("Core Skills", ", ".join(profile["core_skills"])))
    if profile.get("secondary_skills"):
        skills_fields.append(("Secondary Skills", ", ".join(profile["secondary_skills"])))
    if profile.get("certifications"):
        skills_fields.append(("Certifications", ", ".join(profile["certifications"])))
    if profile.get("domain_expertise"):
        skills_fields.append(("Domain Expertise", ", ".join(profile["domain_expertise"])))

    all_rows.extend(_section_rows("SKILLS", skills_fields))

    # PREFERENCES section (from config dict)
    pref_fields: list[tuple[str, str]] = []
    if config.get("min_score") is not None:
        pref_fields.append(("Min Score", str(config["min_score"])))
    if "new_only" in config:
        pref_fields.append(("New Jobs Only", "Yes" if config["new_only"] else "No"))

    all_rows.extend(_section_rows("PREFERENCES", pref_fields))

    # FILTERS section
    filter_fields: list[tuple[str, str]] = []
    if profile.get("dealbreakers"):
        filter_fields.append(("Dealbreakers", ", ".join(profile["dealbreakers"])))
    if profile.get("comp_floor") is not None:
        filter_fields.append(("Min Compensation", _format_comp_floor(profile["comp_floor"])))
    if profile.get("target_titles"):
        filter_fields.append(("Target Titles", ", ".join(profile["target_titles"])))

    all_rows.extend(_section_rows("FILTERS", filter_fields))

    # --- Render table ---
    if all_rows:
        table = tabulate(all_rows, tablefmt="simple_grid", colalign=("left", "left"))
        print(table)

    # --- Separator line ---
    print(f"{C.DIM}{'─' * 60}{C.RESET}\n")
