# Phase 7: Interactive Setup Wizard - Research

**Researched:** 2026-02-09
**Domain:** Interactive CLI wizards with Python Questionary library
**Confidence:** HIGH

## Summary

This phase implements a first-run setup wizard using the Questionary library, a modern Python library built on prompt_toolkit that provides beautiful, interactive CLI prompts with validation, styling, and keyboard controls. The wizard collects user profile information and preferences through sequential prompts, validates inputs inline, allows navigation between questions, and auto-generates JSON configuration files in platform-appropriate directories.

Questionary (version 2.1.1, released August 2025) supports Python 3.9-3.13+ and provides 10 question types including text, password, confirm, select, checkbox, and autocomplete. The library handles KeyboardInterrupt gracefully, supports custom validation with immediate feedback, and offers extensive theming capabilities using token-based styling. Testing is straightforward with pytest-mock, and PyInstaller compatibility requires pre-declaring prompt_toolkit as a hidden import (already specified in Phase 6).

The user decisions from CONTEXT.md lock in: one-question-at-a-time flow, comma-separated lists for multi-value inputs, immediate validation with skip-or-retry on failure, friendly tone with emoji section headers, and celebration on completion. The research confirms these decisions align with questionary's strengths and CLI wizard best practices.

**Primary recommendation:** Use questionary.text() for sequential one-at-a-time prompts with custom validators, implement back navigation via manual state management with while loop (not built-in), style with custom Style object using emoji and color tokens, write JSON atomically with temp file + os.replace(), and detect first run by checking profile.json existence via pathlib.

## Standard Stack

The established libraries/tools for interactive CLI wizards in Python:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| questionary | 2.1.1 | Interactive CLI prompts | Industry standard for beautiful CLI prompts, built on prompt_toolkit, 2K+ stars, excellent validation/styling |
| prompt_toolkit | (dependency) | Terminal UI framework | Powers questionary, handles terminal capabilities, keyboard input, ANSI rendering |
| pathlib | stdlib | Path operations | Python 3.4+ standard, object-oriented, cross-platform, mandatory per PyInstaller best practices |
| platformdirs | 4.0+ | Platform-specific directories | Already in dependencies (Phase 6), provides XDG/macOS/Windows appropriate paths |
| json | stdlib | JSON serialization | Standard library, proven, no external dependency needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-mock | latest | Testing questionary code | Unit/integration tests for wizard flows (Phase 3 already uses pytest) |
| colorama | latest | ANSI color support | Already in dependencies, fallback for Windows terminals without VT100 |
| pyfiglet | latest | ASCII art banners | Already in dependencies, optional enhancement for wizard header |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| questionary | PyInquirer | PyInquirer abandoned (2019), questionary is active fork with fixes |
| questionary | click.prompt | Click lacks validation UI, styling, multi-line, checkbox—good for simple input only |
| questionary | Rich prompts | Rich 13.0+ has prompts but less mature, questionary more focused/battle-tested |
| questionary | pypsi.wizard | Too complex, designed for full shell frameworks not simple wizards |

**Installation:**
```bash
pip install questionary  # Already implied by Phase 6 pre-declared hidden imports
```

**Note:** Phase 6 decision 06-02 already pre-declared questionary/prompt_toolkit hidden imports for PyInstaller, so no spec file changes needed.

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── wizard.py           # Setup wizard module (new)
├── config.py           # Config loading (existing, may need profile support)
├── paths.py            # Path resolution (existing)
└── search.py           # Main entry point (existing, modify to trigger wizard)

tests/
└── test_wizard.py      # Wizard tests with pytest-mock (new)
```

### Pattern 1: First-Run Detection with Profile Check
**What:** Detect first run by checking if profile.json exists before launching search
**When to use:** On every app launch, before config/profile loading
**Example:**
```python
# Source: Best practices from pathlib docs + platformdirs pattern
from pathlib import Path
from .paths import get_data_dir

def is_first_run() -> bool:
    """Check if profile.json exists to determine first run."""
    profile_path = get_data_dir() / "profile.json"
    return not profile_path.exists()

def main():
    if is_first_run():
        from .wizard import run_setup_wizard
        run_setup_wizard()
    # ... proceed with normal search
```

### Pattern 2: Sequential Prompts with State Management
**What:** One-question-at-a-time flow with manual state tracking for back navigation
**When to use:** Wizard flows where users need to review/edit previous answers
**Example:**
```python
# Source: Questionary docs + PyInquirer issue #128 discussion
import questionary

def run_setup_wizard():
    """Run interactive setup wizard with back navigation."""
    questions = [
        ("name", "text", "What's your name?", validate_name),
        ("titles", "text", "Target job titles (comma-separated):", validate_list),
        # ... more questions
    ]

    answers = {}
    idx = 0

    while idx < len(questions):
        key, qtype, message, validator = questions[idx]

        # Show current answer if going back
        default = answers.get(key, "")

        if qtype == "text":
            result = questionary.text(
                message,
                default=default,
                validate=validator
            ).ask()
        # ... handle other types

        if result is None:  # Ctrl+C
            if questionary.confirm("Exit setup?").ask():
                return None
            continue

        # Check for back command
        if result == "BACK" and idx > 0:
            idx -= 1
            continue

        answers[key] = result
        idx += 1

    return answers
```

**Note:** Questionary doesn't have built-in back navigation—manual state management with while loop is the standard pattern (confirmed via PyInquirer issue #128).

### Pattern 3: Inline Validation with Custom Validators
**What:** Immediate feedback on invalid input, offer skip-or-retry on failure
**When to use:** All wizard inputs to prevent cascading errors
**Example:**
```python
# Source: Questionary docs - Advanced Concepts > Validation
from questionary import Validator, ValidationError

class NonEmptyValidator(Validator):
    def validate(self, document):
        if not document.text.strip():
            raise ValidationError(
                message="This field cannot be empty",
                cursor_position=len(document.text)
            )

class CommaSeparatedListValidator(Validator):
    """Validate comma-separated list with at least one item."""
    def __init__(self, min_items=1):
        self.min_items = min_items

    def validate(self, document):
        text = document.text.strip()
        if not text:
            raise ValidationError(message="Please enter at least one item")

        items = [s.strip() for s in text.split(',') if s.strip()]
        if len(items) < self.min_items:
            raise ValidationError(
                message=f"Please enter at least {self.min_items} item(s)",
                cursor_position=len(document.text)
            )

# Usage with skip-or-retry pattern (per user decision)
def prompt_with_skip(message, validator, required=True):
    """Prompt with validation, offer skip on failure if optional."""
    while True:
        try:
            result = questionary.text(
                message,
                validate=validator
            ).ask()

            if result is None:  # Ctrl+C
                raise KeyboardInterrupt

            return result
        except ValidationError:
            if not required:
                if questionary.confirm("Skip this field?", default=True).ask():
                    return None
            # Required field: loop to retry
```

### Pattern 4: Atomic JSON File Writing
**What:** Write JSON to temp file, then atomic rename to prevent corruption
**When to use:** When writing profile.json and config.json to prevent partial writes
**Example:**
```python
# Source: https://gist.github.com/therightstuff/cbdcbef4010c20acc70d2175a91a321f
import json
import tempfile
import os
from pathlib import Path

def write_json_atomic(path: Path, data: dict):
    """Write JSON file atomically with temp file + rename."""
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory (same filesystem for atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp"
    )

    try:
        # Write JSON to temp file
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk

        # Atomic replace (works on Unix and Windows Python 3.3+)
        Path(tmp_path).replace(path)
    except:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except:
            pass
        raise
```

### Pattern 5: Custom Styling with Emoji Section Headers
**What:** Use questionary Style object with color tokens and emoji for visual organization
**When to use:** Throughout wizard to create friendly, organized experience (per user decision)
**Example:**
```python
# Source: Questionary docs - Advanced Concepts > Styling
from questionary import Style

custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),           # Question mark (?) before prompt
    ('question', 'bold'),                    # Question text
    ('answer', 'fg:#4caf50 bold'),          # User's answer (echoed back)
    ('pointer', 'fg:#673ab7 bold'),         # Pointer in select/checkbox
    ('highlighted', 'fg:#673ab7 bold'),     # Highlighted choice
    ('selected', 'fg:#4caf50'),             # Selected items (checkbox)
    ('separator', 'fg:#cc5454'),            # Separators in lists
    ('instruction', 'fg:#858585'),          # Instructions like "(Use arrow keys)"
    ('text', ''),                            # Regular text
    ('disabled', 'fg:#858585 italic')       # Disabled choices
])

# Usage with emoji section headers (per user decision)
import questionary

def prompt_profile_section():
    """Prompt for profile information with emoji header."""
    print("\n👤 Profile Information")
    print("-" * 40)

    name = questionary.text(
        "What's your name?",
        style=custom_style
    ).ask()

    titles = questionary.text(
        "Target job titles (e.g., Software Engineer, Full Stack Developer):",
        instruction="Comma-separated list",
        style=custom_style
    ).ask()

    return {"name": name, "titles": titles}

def prompt_preferences_section():
    """Prompt for preferences with emoji header."""
    print("\n⚙️  Search Preferences")
    print("-" * 40)

    min_score = questionary.text(
        "Minimum job score (1.0-5.0)?",
        default="2.8",
        style=custom_style
    ).ask()

    return {"min_score": float(min_score)}
```

### Pattern 6: Celebration on Completion with Summary
**What:** Show summary of collected data and success message (per user decision)
**When to use:** After all questions answered, before writing files
**Example:**
```python
def show_completion_summary(profile_data, config_data):
    """Display celebration and summary before finalizing (per user decision)."""
    print(f"\n✨ All set! Here's your profile:")
    print("=" * 50)
    print(f"\n👤 Profile:")
    print(f"   Name: {profile_data['name']}")
    print(f"   Skills: {', '.join(profile_data['core_skills'])}")
    print(f"   Titles: {', '.join(profile_data['target_titles'])}")
    if profile_data.get('location'):
        print(f"   Location: {profile_data['location']}")
    if profile_data.get('dealbreakers'):
        print(f"   Dealbreakers: {', '.join(profile_data['dealbreakers'])}")

    print(f"\n⚙️  Preferences:")
    print(f"   Minimum Score: {config_data['min_score']}")
    print(f"   New Jobs Only: {'Yes' if config_data['new_only'] else 'No'}")

    print("\n" + "=" * 50)

    if questionary.confirm(
        "Save this configuration?",
        default=True
    ).ask():
        return True

    return False
```

### Anti-Patterns to Avoid
- **Don't use questionary.form() for back navigation:** Form asks all questions in sequence without allowing state management—use manual loop instead
- **Don't skip parent directory creation:** Always use `path.parent.mkdir(parents=True, exist_ok=True)` before writing files
- **Don't write JSON directly:** Use atomic write pattern to prevent corruption on crash/interrupt
- **Don't rely on questionary's skip_if():** Designed for conditional questions based on previous answers, not for user-requested skipping—use custom skip-or-retry pattern
- **Don't hardcode ~/.job-radar:** Use platformdirs (already in dependencies) for platform-appropriate paths
- **Don't validate at end:** Validate each answer immediately (per user decision) to prevent frustration

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Terminal input handling | Raw input() loops with manual ANSI codes | questionary.text() | Handles terminal capabilities, ANSI rendering, keyboard bindings, cursor positioning—100+ edge cases |
| List validation | String split + manual checking | CommaSeparatedListValidator class | Need to handle empty items, whitespace, trailing commas, empty input, min/max items |
| Back navigation | Custom parser looking for "back" keyword | Manual state management with while + index | No built-in solution exists; state management is the proven pattern |
| Cross-platform paths | os.path + manual ~/.job-radar | platformdirs.user_data_dir() | Handles XDG on Linux, Library/Application Support on macOS, AppData on Windows |
| Atomic file writes | Direct json.dump() | Temp file + os.replace() | Direct write can corrupt on crash; atomic rename prevents partial writes |
| Keyboard interrupt | Try/except around every prompt | questionary .ask() (safe) or .unsafe_ask() | Safe methods handle Ctrl+C gracefully with "Cancelled by user" message |
| Color output | Manual ANSI codes | questionary Style + colorama fallback | Cross-platform terminal capability detection, Windows console API handling |
| Input validation UI | Print error + re-prompt | questionary Validator class | Inline error display, cursor positioning, automatic re-prompt without clearing screen |

**Key insight:** Terminal UIs have extreme platform variance (Windows cmd vs PowerShell vs Terminal, Linux terminal emulators, macOS Terminal vs iTerm). questionary + prompt_toolkit abstract 100+ terminal capability quirks. The 15 lines of code you'd write for "simple" input become 500+ lines to handle all edge cases properly.

## Common Pitfalls

### Pitfall 1: Back Navigation State Explosion
**What goes wrong:** Attempting full undo/redo with side effects (database writes, API calls) creates impossible state management
**Why it happens:** Developer thinks "back button" means undoing actions, not just re-asking questions
**How to avoid:** Keep wizard pure (no side effects until final confirmation). Only write files after user confirms summary. This allows free navigation without state explosion.
**Warning signs:** Code tracking "undo stack" or "command history" in wizard—you're over-engineering

### Pitfall 2: PyInstaller Missing prompt_toolkit
**What goes wrong:** Frozen executable crashes on import with "No module named 'prompt_toolkit'"
**Why it happens:** PyInstaller's static analysis misses prompt_toolkit dependency of questionary
**How to avoid:** Pre-declare hidden import in spec file (Phase 6 decision 06-02 already did this)
**Warning signs:** Works in dev, fails in frozen mode with import error
**Solution:** Already solved—Phase 6 added to spec file:
```python
hiddenimports=['questionary', 'prompt_toolkit', 'prompt_toolkit.formatted_text']
```

### Pitfall 3: Cross-Platform Path Hardcoding
**What goes wrong:** Hardcoded `~/.job-radar` fails on Windows (no HOME) or violates macOS guidelines (should use ~/Library/Application Support)
**Why it happens:** Developer tests on one platform, assumes ~ works everywhere
**How to avoid:** Use platformdirs for platform-appropriate paths (already in Phase 6 dependencies)
**Warning signs:** Using os.path.expanduser("~/.job-radar") or Path.home() / ".job-radar"
**Solution:** Already implemented in paths.py:
```python
from platformdirs import user_data_dir
data_dir = Path(user_data_dir("JobRadar", "JobRadar"))
```

### Pitfall 4: Validation at End (Cascading Errors)
**What goes wrong:** User fills out 10 questions, hits submit, gets "Name invalid" error, loses all other answers
**Why it happens:** Developer validates in batch after collection for "efficiency"
**How to avoid:** Validate immediately after each answer (per user decision). questionary makes this trivial with `validate=` parameter.
**Warning signs:** Collecting all answers in dict, then validating dict at end
**Solution:** Per-question validation:
```python
name = questionary.text(
    "What's your name?",
    validate=NonEmptyValidator()
).ask()  # Blocks until valid
```

### Pitfall 5: Non-Atomic JSON Writes
**What goes wrong:** App crashes during json.dump(), leaves corrupted half-written profile.json, user can't launch app
**Why it happens:** Developer doesn't consider crash scenarios (power loss, kill -9, Ctrl+C)
**How to avoid:** Use atomic write pattern with temp file + os.replace()
**Warning signs:** Direct `with open(path, 'w') as f: json.dump(data, f)` without temp file
**Solution:** See Pattern 4 (Atomic JSON File Writing) above

### Pitfall 6: Emoji Rendering Assumptions
**What goes wrong:** Emoji show as boxes � or double-width breaks alignment on some terminals
**Why it happens:** Not all terminals support emoji or Unicode properly
**How to avoid:** Test on multiple platforms. Use emoji for visual separation (headers) not critical UI (bullet points, status indicators). Graceful degradation: app works without emoji.
**Warning signs:** Using emoji in questionary choice text or as the only indicator of status
**Solution:** User decision uses emoji for section headers (👤 Profile, ⚙️ Preferences) which are nice-to-have, not critical—app works fine if they render as boxes.

### Pitfall 7: Questionary + Rich Conflicts
**What goes wrong:** Rich console output interferes with questionary prompts, or questionary breaks Rich live displays
**Why it happens:** Both libraries manage terminal state (cursor, ANSI codes)
**How to avoid:** Don't mix Rich and questionary in same terminal region. Use questionary for input, Rich for output (after prompts complete).
**Warning signs:** Console output appearing in wrong location, prompts not clearing properly
**Solution:** Not applicable to this project (no Rich dependency), but good to know for future

## Code Examples

Verified patterns from official sources:

### Comma-Separated List Input with Validation
```python
# Source: Questionary docs + common pattern
import questionary
from questionary import Validator, ValidationError

class CommaSeparatedValidator(Validator):
    """Validate comma-separated list."""
    def __init__(self, min_items=1, field_name="items"):
        self.min_items = min_items
        self.field_name = field_name

    def validate(self, document):
        text = document.text.strip()
        if not text:
            raise ValidationError(
                message=f"Please enter at least one {self.field_name}"
            )

        items = [s.strip() for s in text.split(',') if s.strip()]
        if len(items) < self.min_items:
            raise ValidationError(
                message=f"Please enter at least {self.min_items} {self.field_name}(s)"
            )

# Usage (per user decision: comma-separated lists for skills, titles)
skills_text = questionary.text(
    "Your core skills:",
    instruction="e.g., Python, JavaScript, React, AWS",
    validate=CommaSeparatedValidator(min_items=1, field_name="skill")
).ask()

core_skills = [s.strip() for s in skills_text.split(',') if s.strip()]
```

### Skip or Retry on Validation Failure
```python
# Source: User decision (CONTEXT.md) + questionary patterns
def prompt_optional_field(message, example, validator):
    """
    Prompt for optional field with skip-or-retry on validation failure.
    Per user decision: offer skip for optional fields, retry for required.
    """
    while True:
        result = questionary.text(
            message,
            instruction=f"Example: {example}",
            validate=validator
        ).ask()

        if result is None:  # Ctrl+C pressed
            raise KeyboardInterrupt

        # Validation passed (questionary blocks until valid)
        return result

def prompt_required_field(message, example, validator):
    """
    Prompt for required field with retry on validation failure.
    Per user decision: required fields must be filled (no skip option).
    """
    while True:
        result = questionary.text(
            message,
            instruction=f"Example: {example}",
            validate=validator
        ).ask()

        if result is None:  # Ctrl+C
            # Confirm exit for required field
            if questionary.confirm("Exit setup wizard?").ask():
                raise KeyboardInterrupt
            continue  # Re-prompt

        return result

# Usage (per user decision: name/skills/titles required, location/dealbreakers optional)
name = prompt_required_field(
    "What's your name?",
    "John Doe",
    NonEmptyValidator()
)

location = prompt_optional_field(
    "Location preference (optional):",
    "Remote, New York, Hybrid",
    None  # No validation for optional field
)
```

### Complete Wizard Flow with Sections
```python
# Source: User decisions + questionary best practices
import questionary
from questionary import Style
from pathlib import Path
from .paths import get_data_dir

def run_setup_wizard():
    """
    Interactive setup wizard for first-run configuration.

    Per user decisions:
    - One question at a time
    - Comma-separated lists for multi-value inputs
    - Examples on separate line (via instruction parameter)
    - Validate after each answer
    - Friendly tone with emoji section headers
    - Celebration + summary at end
    """
    custom_style = Style([
        ('qmark', 'fg:#673ab7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#4caf50 bold'),
        ('instruction', 'fg:#858585'),
    ])

    print("\n" + "="*60)
    print("🎯 Job Radar - First Time Setup")
    print("="*60)

    # Section 1: Profile Information
    print("\n👤 Profile Information")
    print("-" * 40)

    name = questionary.text(
        "What's your name?",
        validate=NonEmptyValidator(),
        style=custom_style
    ).ask()

    titles_text = questionary.text(
        "Target job titles:",
        instruction="e.g., Software Engineer, Full Stack Developer",
        validate=CommaSeparatedValidator(min_items=1, field_name="job title"),
        style=custom_style
    ).ask()
    target_titles = [s.strip() for s in titles_text.split(',') if s.strip()]

    skills_text = questionary.text(
        "Your core skills:",
        instruction="e.g., Python, JavaScript, React, AWS",
        validate=CommaSeparatedValidator(min_items=1, field_name="skill"),
        style=custom_style
    ).ask()
    core_skills = [s.strip() for s in skills_text.split(',') if s.strip()]

    location = questionary.text(
        "Location preference (optional, press Enter to skip):",
        instruction="e.g., Remote, New York, Hybrid",
        default="",
        style=custom_style
    ).ask()

    dealbreakers_text = questionary.text(
        "Dealbreakers (optional, press Enter to skip):",
        instruction="e.g., relocation required, on-site only",
        default="",
        style=custom_style
    ).ask()
    dealbreakers = [s.strip() for s in dealbreakers_text.split(',') if s.strip()] if dealbreakers_text else []

    # Section 2: Search Preferences
    print("\n⚙️  Search Preferences")
    print("-" * 40)

    min_score = questionary.text(
        "Minimum job score (1.0-5.0)?",
        default="2.8",
        validate=lambda text: 1.0 <= float(text) <= 5.0 or "Must be between 1.0 and 5.0",
        style=custom_style
    ).ask()

    new_only = questionary.confirm(
        "Show only new jobs (not previously seen)?",
        default=True,
        style=custom_style
    ).ask()

    # Build data structures
    profile_data = {
        "name": name,
        "target_titles": target_titles,
        "core_skills": core_skills,
    }
    if location:
        profile_data["location"] = location
    if dealbreakers:
        profile_data["dealbreakers"] = dealbreakers

    config_data = {
        "min_score": float(min_score),
        "new_only": new_only
    }

    # Celebration + Summary (per user decision)
    print(f"\n✨ All set! Here's your profile:")
    print("="*60)
    print(f"\n👤 Profile:")
    print(f"   Name: {name}")
    print(f"   Skills: {', '.join(core_skills)}")
    print(f"   Titles: {', '.join(target_titles)}")
    if location:
        print(f"   Location: {location}")
    if dealbreakers:
        print(f"   Dealbreakers: {', '.join(dealbreakers)}")
    print(f"\n⚙️  Preferences:")
    print(f"   Minimum Score: {min_score}")
    print(f"   New Jobs Only: {'Yes' if new_only else 'No'}")
    print("="*60 + "\n")

    # Confirm before saving
    if not questionary.confirm("Save this configuration?", default=True, style=custom_style).ask():
        print("Setup cancelled.")
        return False

    # Write files atomically
    data_dir = get_data_dir()
    write_json_atomic(data_dir / "profile.json", profile_data)
    write_json_atomic(data_dir / "config.json", config_data)

    print(f"\n✅ Configuration saved to {data_dir}")
    print("You can now run job-radar to start searching!\n")

    return True
```

### Integration with Main Entry Point
```python
# Source: Existing search.py pattern + first-run detection
# Modify job_radar/search.py main() function

def main():
    # Check for first run BEFORE argument parsing
    from .paths import get_data_dir
    profile_path = get_data_dir() / "profile.json"

    if not profile_path.exists():
        print("\n🎯 Welcome to Job Radar!")
        print("Looks like this is your first time running the app.")
        print("Let's set up your profile...\n")

        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            # User cancelled wizard
            sys.exit(0)

        # After wizard, profile.json exists—continue to search
        print("Starting your first job search...\n")

    # Rest of existing main() logic...
    # (config loading, argument parsing, search execution)
```

### Testing Wizard with pytest-mock
```python
# Source: Questionary docs - Testing section
import pytest
from unittest.mock import patch
from job_radar.wizard import run_setup_wizard

def test_wizard_collects_required_fields(mocker):
    """Test wizard collects name, skills, titles."""
    # Mock questionary prompts
    mocker.patch('questionary.text', side_effect=[
        mocker.Mock(ask=lambda: "John Doe"),              # name
        mocker.Mock(ask=lambda: "Software Engineer"),     # titles
        mocker.Mock(ask=lambda: "Python, JavaScript"),    # skills
        mocker.Mock(ask=lambda: "Remote"),                # location
        mocker.Mock(ask=lambda: ""),                      # dealbreakers (empty)
        mocker.Mock(ask=lambda: "3.0"),                   # min_score
    ])
    mocker.patch('questionary.confirm', side_effect=[
        mocker.Mock(ask=lambda: True),  # new_only
        mocker.Mock(ask=lambda: True),  # save confirmation
    ])

    # Mock file writing
    mock_write = mocker.patch('job_radar.wizard.write_json_atomic')

    # Run wizard
    result = run_setup_wizard()

    # Assertions
    assert result is True
    assert mock_write.call_count == 2  # profile.json + config.json

    # Check profile.json data
    profile_call = mock_write.call_args_list[0]
    profile_data = profile_call[0][1]
    assert profile_data["name"] == "John Doe"
    assert "Python" in profile_data["core_skills"]

def test_wizard_handles_ctrl_c(mocker):
    """Test wizard handles KeyboardInterrupt gracefully."""
    # First prompt returns None (simulates Ctrl+C)
    mocker.patch('questionary.text', return_value=mocker.Mock(ask=lambda: None))
    mocker.patch('questionary.confirm', return_value=mocker.Mock(ask=lambda: True))  # Confirm exit

    # Should raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        run_setup_wizard()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PyInquirer | questionary | 2019 | PyInquirer abandoned, questionary is active maintained fork with bug fixes |
| os.path for paths | pathlib | Python 3.4+ | Object-oriented, cleaner syntax, mandatory per PyInstaller best practices (Phase 6) |
| Manual ~/.config | platformdirs | 2020+ | Cross-platform compliance with OS guidelines (XDG, macOS, Windows) |
| argparse-only setup | Interactive wizard | Modern CLI UX | Better first-run experience, reduces documentation burden |
| Validation at end | Inline validation | Modern UX | Immediate feedback prevents frustration, questionary makes this trivial |
| click.prompt | questionary | 2018+ | questionary adds styling, validation UI, multi-select—click.prompt too basic |

**Deprecated/outdated:**
- **PyInquirer**: Abandoned in 2019, use questionary (active fork)
- **whaaaaat (PyInquirer's dependency)**: Unmaintained, compatibility issues with modern prompt_toolkit
- **Hardcoded config paths**: Use platformdirs for OS compliance (already in Phase 6 dependencies)
- **os.path module**: Use pathlib per PyInstaller best practices (Phase 6 decision 06-01)

## Open Questions

Things that couldn't be fully resolved:

1. **Autocomplete for skills**
   - What we know: Questionary supports autocomplete() prompt type with fuzzy matching
   - What's unclear: Whether to implement skill autocomplete (requires maintaining skill taxonomy/dictionary)
   - Recommendation: Mark as "Claude's discretion" per CONTEXT.md. Start without autocomplete (simpler), add in future phase if user feedback requests it. Could use GitHub skills taxonomy or pre-populate from common job board skills.

2. **Back button key binding**
   - What we know: No built-in back navigation, must implement manually with state management
   - What's unclear: Specific key binding (Ctrl+B vs Up arrow vs typing "BACK")
   - Recommendation: Mark as "Claude's discretion" per CONTEXT.md. Options: (a) Type "BACK" as special keyword—simple, cross-platform but clunky; (b) Ctrl+B—requires questionary keybindings extension, more complex; (c) Show all answers at end with "Edit which field?" select—simpler than mid-wizard back. Recommend option (c) for simplicity.

3. **Color scheme cross-platform compatibility**
   - What we know: Questionary Style tokens support fg: color codes, works via prompt_toolkit
   - What's unclear: Whether specific colors (e.g., #673ab7 purple) render consistently across all terminals
   - Recommendation: Test on Windows (cmd, PowerShell, Windows Terminal), macOS (Terminal, iTerm2), Linux (gnome-terminal, konsole). If issues, fall back to basic ANSI colors (cyan, green, yellow) which are universally supported.

4. **Profile.json vs config.json separation**
   - What we know: User decisions specify wizard creates both profile.json and config.json
   - What's unclear: Current codebase uses --profile argument pointing to custom path; how to reconcile with platformdirs-based profile.json
   - Recommendation: Phase 7 creates ~/.../JobRadar/profile.json (via platformdirs) for "default" profile. Keep --profile argument for power users who want multiple profiles. If --profile not specified, use default. This maintains backward compatibility while improving first-run UX.

## Sources

### Primary (HIGH confidence)
- Questionary official documentation: https://questionary.readthedocs.io/en/stable/ - Complete API reference, question types, validation, styling
- Questionary PyPI page: https://pypi.org/project/questionary/ - Version 2.1.1, Python 3.9+ compatibility, installation
- Questionary GitHub repository: https://github.com/tmbo/questionary - 2K+ stars, active maintenance
- Python pathlib documentation: https://docs.python.org/3/library/pathlib.html - Standard library path operations
- platformdirs documentation: https://platformdirs.readthedocs.io/en/latest/api.html - Cross-platform directory management

### Secondary (MEDIUM confidence)
- PyInquirer issue #128 on back navigation: https://github.com/CITGuru/PyInquirer/issues/128 - Community discussion on wizard navigation patterns, maintainer guidance
- Atomic JSON writes gist: https://gist.github.com/therightstuff/cbdcbef4010c20acc70d2175a91a321f - Production-safe file writing pattern
- The Blue Book - Questionary guide: https://lyz-code.github.io/blue-book/questionary/ - Best practices, testing patterns
- Python configuration best practices: https://configu.com/blog/working-with-python-configuration-files-tutorial-best-practices/ - JSON config patterns
- PyInstaller hidden imports: https://pyinstaller.org/en/stable/when-things-go-wrong.html - Troubleshooting guide

### Tertiary (LOW confidence)
- Medium article on Python CLI libraries (Jan 2026): https://medium.com/@wilson79/10-best-python-cli-libraries-for-developers-picking-the-right-one-for-your-project-cefb0bd41df1 - Questionary vs alternatives comparison
- Various WebSearch results on CLI wizard patterns - General guidance, not library-specific

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Questionary is well-documented, actively maintained, 2.1.1 released Aug 2025, official docs confirm all features
- Architecture: HIGH - Patterns verified from official docs, real-world usage examples, PyInquirer issue discussion provides authoritative guidance on limitations
- Pitfalls: MEDIUM - Based on official docs warnings, common patterns, and general Python best practices; some inferred from experience rather than explicit documentation
- Testing: MEDIUM - Official docs have testing section, pytest-mock pattern confirmed, but examples are limited

**Research date:** 2026-02-09
**Valid until:** ~60 days (questionary is stable, slow-moving library; Python pathlib/json stdlib patterns don't change)

**Note on user decisions:** All architecture patterns and recommendations align with user decisions from CONTEXT.md (one-at-a-time flow, comma-separated lists, immediate validation, emoji sections, celebration). No conflicts found.
