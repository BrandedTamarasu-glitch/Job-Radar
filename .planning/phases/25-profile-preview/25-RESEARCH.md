# Phase 25: Profile Preview - Research

**Researched:** 2026-02-12
**Domain:** CLI profile display with tabulate, startup flow integration
**Confidence:** HIGH

## Summary

Phase 25 implements read-only profile preview functionality that displays on every startup (after wizard check, before search) and on demand via `--view-profile`. The core technology is tabulate 0.9.0 for table formatting, integrated into the existing color infrastructure (NO_COLOR support). The implementation fits naturally into Job Radar's existing flow: `load_profile_with_recovery()` → `display_profile()` → search begins.

Key architectural decisions from CONTEXT.md: sectioned table layout with borders, only show set fields, `--no-wizard` suppresses both wizard and preview, `--view-profile` displays then offers to edit (forward-looking to Phase 26). The profile manager already provides validated profile data; this phase adds the display layer only.

**Primary recommendation:** Create a standalone `profile_display.py` module with a `display_profile(profile: dict, config: dict | None) -> None` function that uses tabulate with `rounded_grid` or `simple_grid` format, filters out None/empty fields, and respects the existing `_Colors` class for NO_COLOR compliance. Integrate into `search.py` main() flow after profile load, with conditional suppression via `--no-wizard`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Display Layout & Density:**
- **Sectioned with headers** — grouped into logical sections (e.g., Identity, Skills, Preferences, Filters) with clear section headers
- **Bordered table** using tabulate or box-drawing characters for structured grid appearance
- **Branded header** line to clearly demarcate the profile section (e.g., "═══ Job Radar Profile ═══")
- **Only show set fields** — hide fields that are empty or at default values to reduce noise

**Startup Behavior:**
- Profile preview displays **after wizard check, before search** — profile always reflects the latest state
- Preview shows **every run** — consistent experience, user always knows what they're searching with
- `--view-profile` **prints profile then offers to edit** — asks "Want to edit? (y/N)" as a convenient shortcut
- If `--view-profile` and no profile exists, **launch wizard automatically** to create one
- **Clear separator line** between profile preview and search output

**Field Presentation:**
- List fields (skills, titles, dealbreakers) displayed as **comma-separated inline** — compact, fits in table cells
- **Show all items** in lists — no truncation, user sees exactly what's configured
- Numeric fields show **just the value** — no range hints (e.g., "Min Score: 3.5" not "3.5 (0.0-5.0)")
- Boolean fields use **friendly labels** — "Yes" / "No" or "Enabled" / "Disabled" instead of true/false

**Suppression & Control:**
- **--no-wizard covers preview suppression** — one flag for quiet mode, no separate --no-preview flag
- Preview **respects NO_COLOR** automatically (Phase 18 infrastructure already in place)
- Edit mode from --view-profile **launches quick-edit menu** (Phase 26's interactive flow, once available)

### Claude's Discretion

- Exact section grouping of fields
- Table style (tabulate format choice)
- Separator line style
- Color scheme for the preview (within NO_COLOR constraints)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tabulate | 0.9.0 | Profile table formatting | Chosen in milestone research; pure Python, 50KB, supports grid formats with box-drawing characters, handles column alignment automatically |
| json (stdlib) | - | Profile/config loading | Already used by profile_manager.py and config.py |
| argparse (stdlib) | - | CLI flag handling | Already used; add `--view-profile` flag |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| textwrap (stdlib) | - | Long text wrapping | If profile fields (e.g., highlights) exceed column width; combine with tabulate's maxcolwidths |
| colorama | 0.4.6 | ANSI color codes | Already in dependencies; use existing `_Colors` class for NO_COLOR compliance |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tabulate | rich | Rich is 4MB+ with Pygments dependency; overkill for simple table display. Already rejected in stack research. |
| tabulate | Manual string formatting | Error-prone, doesn't handle alignment/wrapping. Don't hand-roll table layout. |
| Separate --no-preview flag | Reuse --no-wizard | User decision: one flag for quiet mode. Simpler UX. |

**Installation:**
```bash
# Already in pyproject.toml from Phase 24 milestone planning
# No new dependencies needed
```

## Architecture Patterns

### Recommended Module Structure

```
job_radar/
├── profile_display.py    # NEW: Profile preview formatting
├── profile_manager.py    # EXISTING: Profile I/O (load/save/validate)
├── search.py            # MODIFY: Integrate preview into main() flow
└── wizard.py            # EXISTING: Interactive profile creation
```

### Pattern 1: Profile Display Function

**What:** Single-purpose function that formats and prints profile data
**When to use:** Startup preview, --view-profile command

**Example:**
```python
# job_radar/profile_display.py
from tabulate import tabulate

def display_profile(profile: dict, config: dict | None = None) -> None:
    """Display formatted profile preview with sections and borders.

    Parameters
    ----------
    profile : dict
        Validated profile dict from profile_manager.load_profile()
    config : dict | None
        Config dict from config.load_config() for preferences display

    Notes
    -----
    - Filters out None/empty fields per CONTEXT.md (only show set fields)
    - Uses tabulate with rounded_grid or simple_grid format
    - Respects NO_COLOR via _Colors class from search.py
    - Groups fields into sections: Identity, Skills, Preferences, Filters
    """
    from .search import _Colors as C  # Reuse existing color infrastructure

    # Branded header
    print(f"\n{C.CYAN}{'═' * 60}")
    print(f"{'Job Radar Profile':^60}")
    print(f"{'═' * 60}{C.RESET}\n")

    # Build table data (only non-empty fields)
    rows = []

    # Identity section
    rows.append([f"{C.BOLD}IDENTITY{C.RESET}", ""])
    if profile.get("name"):
        rows.append(["Name", profile["name"]])
    if profile.get("years_experience") is not None:
        level = profile.get("level", "")
        level_str = f" ({level} level)" if level else ""
        rows.append(["Experience", f"{profile['years_experience']} years{level_str}"])

    # Skills section
    rows.append([f"\n{C.BOLD}SKILLS{C.RESET}", ""])
    if profile.get("core_skills"):
        rows.append(["Core Skills", ", ".join(profile["core_skills"])])
    if profile.get("secondary_skills"):
        rows.append(["Secondary Skills", ", ".join(profile["secondary_skills"])])

    # ... (additional sections)

    table = tabulate(rows, tablefmt="simple_grid", colalign=("left", "left"))
    print(table)

    # Separator line
    print(f"\n{C.DIM}{'─' * 60}{C.RESET}\n")
```

**Source:** Pattern derived from wizard.py celebration summary (lines 520-552) and existing `_Colors` class usage in search.py.

### Pattern 2: Integration into main() Flow

**What:** Insert profile preview after profile load, before search
**When to use:** Every run (unless --no-wizard suppresses)

**Example:**
```python
# job_radar/search.py main()
def main():
    # ... existing config/args parsing ...

    # Profile loading (existing)
    if args.no_wizard:
        profile = load_profile(profile_path_str)
    else:
        profile = load_profile_with_recovery(profile_path_str)

    # NEW: Profile preview (after wizard check, before search)
    if not args.no_wizard:  # Reuse flag per CONTEXT.md decision
        from .profile_display import display_profile
        display_profile(profile, config)

    # ... existing search flow starts here ...
```

**Source:** User decision from CONTEXT.md — "after wizard check, before search" and "--no-wizard covers preview suppression".

### Pattern 3: --view-profile Early Exit

**What:** Display profile and exit, with optional edit prompt
**When to use:** User wants to inspect or update profile without running search

**Example:**
```python
# job_radar/search.py parse_args()
profile_group.add_argument(
    "--view-profile",
    action="store_true",
    help="Display profile and exit (optionally edit)",
)

# main() early exit handler
if args.view_profile:
    from .profile_display import display_profile

    # If no profile exists, launch wizard
    if not Path(profile_path_str).exists():
        print(f"\n{C.YELLOW}No profile found — launching setup wizard...{C.RESET}\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            sys.exit(1)

    # Load and display
    profile = load_profile(profile_path_str)
    display_profile(profile, config)

    # Offer to edit (Phase 26 forward-looking)
    try:
        import questionary
        edit = questionary.confirm("Want to edit?", default=False).ask()
        if edit:
            # Phase 26: launch quick-edit menu (not implemented yet)
            print(f"\n{C.YELLOW}Edit mode coming in Phase 26{C.RESET}")
    except (ImportError, KeyboardInterrupt):
        pass

    sys.exit(0)
```

**Source:** argparse --version pattern (displays info and exits), CONTEXT.md decision for --view-profile behavior.

### Anti-Patterns to Avoid

- **Duplicating color infrastructure:** Don't create new color codes; reuse `_Colors` class from search.py to maintain NO_COLOR compliance
- **Manual table formatting:** Don't hand-roll column alignment or borders; use tabulate
- **Showing all fields:** Don't display None/empty fields; filter them out per user decision
- **Adding --no-preview flag:** Don't create new flag; reuse --no-wizard per user decision

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table column alignment | Manual spacing with f-strings | tabulate library | Handles variable-width content, Unicode characters, alignment edge cases |
| Box-drawing characters | Hardcoded ─│┌┐└┘ strings | tabulate tablefmt="simple_grid" or "rounded_grid" | Automatic corner detection, cross-platform compatibility |
| Text wrapping in cells | Manual split() and truncation | tabulate maxcolwidths + textwrap | Handles word boundaries, preserves readability |
| NO_COLOR detection | New environment check | Existing _Colors class in search.py | Already handles NO_COLOR, TTY detection, Windows VT100 |

**Key insight:** tabulate handles table display complexity (alignment, borders, wrapping). Job Radar already has color infrastructure. Don't recreate either.

## Common Pitfalls

### Pitfall 1: Breaking NO_COLOR Compliance

**What goes wrong:** Hardcoding ANSI color codes directly (e.g., `\033[36m`) instead of using the `_Colors` class breaks accessibility for users who set NO_COLOR=1.

**Why it happens:** Developer forgets that color codes are conditional, not universal.

**How to avoid:** Always import and use `_Colors` class from search.py, which respects NO_COLOR environment variable.

**Warning signs:** Colors appear in NO_COLOR=1 environment, accessibility complaints.

**Example:**
```python
# BAD: Hardcoded color
print("\033[36m" + "Profile" + "\033[0m")

# GOOD: Use existing _Colors class
from .search import _Colors as C
print(f"{C.CYAN}Profile{C.RESET}")
```

**Source:** Existing _Colors implementation in search.py lines 45-84, NO_COLOR standard (https://no-color.org/).

### Pitfall 2: Displaying Empty/None Fields

**What goes wrong:** Table shows rows like "Location: (not set)" or "Dealbreakers: None", creating visual noise and defeating the user decision to "only show set fields".

**Why it happens:** Iterating over all profile keys without filtering for truthiness.

**How to avoid:** Filter fields before building table rows — only add row if value is not None and not empty list/string.

**Warning signs:** Table has many "(not set)" placeholders, user complains about clutter.

**Example:**
```python
# BAD: Shows all fields
rows = [
    ["Location", profile.get("location", "(not set)")],
    ["Dealbreakers", profile.get("dealbreakers") or "(not set)"],
]

# GOOD: Only show set fields
rows = []
if profile.get("location"):
    rows.append(["Location", profile["location"]])
if profile.get("dealbreakers"):
    rows.append(["Dealbreakers", ", ".join(profile["dealbreakers"])])
```

**Source:** User decision from CONTEXT.md — "only show set fields".

### Pitfall 3: Truncating List Fields

**What goes wrong:** Lists like skills or titles display as "Python, JavaScript, Docker... (3 more)" instead of showing all items, hiding configured settings from user.

**Why it happens:** Developer assumes lists are too long for display, adds truncation logic.

**How to avoid:** Display all items in list fields per user decision — "show all items in lists, no truncation".

**Warning signs:** User can't see all configured skills/titles in preview, confusion about what's actually in profile.

**Example:**
```python
# BAD: Truncates list
skills = profile.get("core_skills", [])
skills_display = ", ".join(skills[:5]) + ("..." if len(skills) > 5 else "")

# GOOD: Show all items
if profile.get("core_skills"):
    rows.append(["Core Skills", ", ".join(profile["core_skills"])])
```

**Source:** User decision from CONTEXT.md — "show all items in lists".

### Pitfall 4: Interleaving Preview with Search Output

**What goes wrong:** Profile preview and search output run together without clear separation, making it hard to distinguish "what's my profile" from "what's my search results".

**Why it happens:** Missing separator line between preview and search start.

**How to avoid:** Print clear separator line after profile preview, before search Step 1.

**Warning signs:** User can't tell where profile ends and search begins in terminal output.

**Example:**
```python
# BAD: No separator
display_profile(profile, config)
print(f"\n{C.BOLD}Step 1:{C.RESET} Fetching job listings...")

# GOOD: Clear separator
display_profile(profile, config)
print(f"\n{C.DIM}{'─' * 60}{C.RESET}\n")  # Separator line
print(f"{C.BOLD}Step 1:{C.RESET} Fetching job listings...")
```

**Source:** User decision from CONTEXT.md — "clear separator line between profile preview and search output".

## Code Examples

Verified patterns from codebase analysis:

### Field Filtering (Only Non-Empty)

```python
# Source: Adapted from wizard.py summary display (lines 520-548)
# Pattern: Only add row if field is set
rows = []

# String field — only if not None and not empty
if profile.get("location"):
    rows.append(["Location", profile["location"]])

# List field — only if not None and not empty list
if profile.get("core_skills"):
    rows.append(["Core Skills", ", ".join(profile["core_skills"])])

# Numeric field — only if not None (0 is valid)
if profile.get("years_experience") is not None:
    rows.append(["Experience", f"{profile['years_experience']} years"])

# Nested with default — only if truthy after get()
if profile.get("arrangement"):
    rows.append(["Arrangement", ", ".join(profile["arrangement"])])
```

### Boolean Field Display (Friendly Labels)

```python
# Source: wizard.py line 551 (new_only display)
# Pattern: Convert bool to Yes/No, not True/False

# BAD: Shows "True" / "False"
rows.append(["New Jobs Only", config.get("new_only", True)])

# GOOD: Shows "Yes" / "No"
new_only = config.get("new_only", True)
rows.append(["New Jobs Only", "Yes" if new_only else "No"])
```

### Reusing Existing Color Infrastructure

```python
# Source: search.py lines 72-84 (_Colors class)
# Pattern: Import and use existing _Colors for NO_COLOR compliance

from .search import _Colors as C

# Branded header with color
print(f"\n{C.CYAN}{'═' * 60}")
print(f"{'Job Radar Profile':^60}")
print(f"{'═' * 60}{C.RESET}\n")

# Section headers with bold
rows.append([f"{C.BOLD}IDENTITY{C.RESET}", ""])

# Separator line with dim
print(f"\n{C.DIM}{'─' * 60}{C.RESET}\n")
```

### Tabulate Grid Format Selection

```python
# Source: GitHub astanin/python-tabulate (official repo)
# Available grid formats with box-drawing characters:

from tabulate import tabulate

data = [["Field", "Value"], ["Name", "John Doe"]]

# Simple grid (single-line box drawing)
print(tabulate(data, tablefmt="simple_grid"))
# Output:
# ┌───────┬──────────┐
# │ Field │ Value    │
# ├───────┼──────────┤
# │ Name  │ John Doe │
# └───────┴──────────┘

# Rounded grid (rounded corners)
print(tabulate(data, tablefmt="rounded_grid"))
# Output:
# ╭───────┬──────────╮
# │ Field │ Value    │
# ├───────┼──────────┤
# │ Name  │ John Doe │
# ╰───────┴──────────╯

# Recommendation: Use simple_grid or rounded_grid for clean borders
```

### Profile Field Grouping by Section

```python
# Source: wizard.py lines 522-548 (summary display grouping)
# Pattern: Group related fields with section headers

rows = []

# Identity section
rows.append([f"{C.BOLD}IDENTITY{C.RESET}", ""])
if profile.get("name"):
    rows.append(["Name", profile["name"]])
if profile.get("years_experience") is not None:
    level_str = f" ({profile['level']} level)" if profile.get("level") else ""
    rows.append(["Experience", f"{profile['years_experience']} years{level_str}"])

# Skills section
rows.append([f"\n{C.BOLD}SKILLS{C.RESET}", ""])
if profile.get("core_skills"):
    rows.append(["Core Skills", ", ".join(profile["core_skills"])])
if profile.get("secondary_skills"):
    rows.append(["Secondary Skills", ", ".join(profile["secondary_skills"])])

# Preferences section (from config.json)
if config:
    rows.append([f"\n{C.BOLD}PREFERENCES{C.RESET}", ""])
    if config.get("min_score") is not None:
        rows.append(["Min Score", f"{config['min_score']:.1f}"])
    if config.get("new_only") is not None:
        rows.append(["New Jobs Only", "Yes" if config["new_only"] else "No"])

# Filters section
rows.append([f"\n{C.BOLD}FILTERS{C.RESET}", ""])
if profile.get("dealbreakers"):
    rows.append(["Dealbreakers", ", ".join(profile["dealbreakers"])])
if profile.get("comp_floor"):
    rows.append(["Min Compensation", f"${profile['comp_floor']:,}"])
```

### Integration Point in search.py main()

```python
# Source: search.py lines 449-456 (profile loading)
# Pattern: Insert preview after profile load, before search

def main():
    # ... existing args/config parsing ...

    # Profile path resolution (existing)
    profile_path_str = args.profile
    if not profile_path_str:
        from .paths import get_data_dir
        profile_path_str = str(get_data_dir() / "profile.json")

    # Profile loading (existing)
    if args.no_wizard:
        profile = load_profile(profile_path_str)
    else:
        profile = load_profile_with_recovery(profile_path_str)

    # NEW: Profile preview (unless suppressed)
    if not args.no_wizard:
        from .profile_display import display_profile
        display_profile(profile, config)

    # Existing search flow continues
    name = profile["name"]
    log_level = logging.DEBUG if args.verbose else logging.INFO
    # ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual profile inspection (open JSON in editor) | Automatic startup preview | Phase 25 (this phase) | User always sees current settings before search |
| Separate --no-preview flag | Reuse --no-wizard for suppression | Context discussion 2026-02-12 | Simpler UX, one flag for quiet mode |
| Display all profile fields | Filter to show only set fields | Context discussion 2026-02-12 | Reduces visual noise, focuses on configured settings |

**Deprecated/outdated:**
- N/A (this is a new feature, no prior implementation)

## Open Questions

1. **Should config.json preferences (min_score, new_only) appear in profile preview?**
   - What we know: Config is separate from profile (config.py vs profile_manager.py)
   - What's unclear: User decision doesn't explicitly mention config fields
   - Recommendation: Include config preferences in "PREFERENCES" section — user always wants to know "what am I searching with" which includes thresholds. Mark clearly as preferences vs profile data.

2. **What's the optimal maxcolwidths for list fields?**
   - What we know: Terminal width assumed 80+ per success criteria
   - What's unclear: Should we set maxcolwidths to prevent wrapping, or let it wrap naturally?
   - Recommendation: Don't set maxcolwidths initially — user decision says "show all items", wrapping is better than truncation. If wrapping becomes an issue in testing, set maxcolwidths=[None, 50] (field name unlimited, value max 50 chars).

3. **Should separator use box-drawing (─) or ASCII (-)?**
   - What we know: tabulate uses box-drawing for grid formats
   - What's unclear: Do separators need to be plain ASCII for compatibility?
   - Recommendation: Use box-drawing (─) to match table aesthetic. If compatibility issues arise, switch to `-` * 60. Test on Windows Terminal, macOS Terminal, and Linux terminals during verification.

## Sources

### Primary (HIGH confidence)

- `/home/corye/Claude/Job-Radar/job_radar/profile_manager.py` - Profile schema, validation, load/save patterns
- `/home/corye/Claude/Job-Radar/job_radar/search.py` - Existing _Colors class (lines 45-84), main() flow (lines 394-661)
- `/home/corye/Claude/Job-Radar/job_radar/wizard.py` - Profile summary display pattern (lines 520-552)
- `/home/corye/Claude/Job-Radar/job_radar/config.py` - Config structure (min_score, new_only, etc.)
- `/home/corye/Claude/Job-Radar/profiles/_template.json` - Complete profile field list
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html) - Action types, early exit patterns
- [Python tabulate GitHub](https://github.com/astanin/python-tabulate) - Grid formats, colalign, maxcolwidths
- [NO_COLOR standard](https://no-color.org/) - Environment variable specification
- `.planning/research/STACK.md` - tabulate 0.9.0 selection rationale, version compatibility
- `.planning/phases/25-profile-preview/25-CONTEXT.md` - All user decisions for this phase

### Secondary (MEDIUM confidence)

- [Python Tabulate: A Full Guide | DataCamp](https://www.datacamp.com/tutorial/python-tabulate) - Table format examples, column alignment
- [How to Customize Column Widths in Python tabulate](https://likegeeks.com/column-widths-tabulate/) - maxcolwidths usage
- [Build Command-Line Interfaces With Python's argparse – Real Python](https://realpython.com/command-line-interfaces-python-argparse/) - CLI patterns, early exit strategies
- [Command Line Interface Guidelines](https://clig.dev/) - Separator lines, visual dividers in terminal output

### Tertiary (LOW confidence)

- None. All recommendations based on codebase analysis and official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - tabulate 0.9.0 already chosen in milestone research, zero new dependencies
- Architecture: HIGH - Patterns derived from existing wizard.py summary and search.py flow
- Pitfalls: MEDIUM-HIGH - NO_COLOR and field filtering patterns verified in codebase, others from user decisions

**Research date:** 2026-02-12
**Valid until:** 2026-03-14 (30 days for stable libraries/patterns)
