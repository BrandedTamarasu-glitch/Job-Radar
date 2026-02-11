# Phase 8: Entry Point Integration - Research

**Researched:** 2026-02-09
**Domain:** Python CLI configuration precedence, profile path handling, validation with fallback
**Confidence:** HIGH

## Summary

Phase 8 connects the wizard (Phase 7) to the search pipeline by implementing automatic profile path resolution with proper precedence (CLI flag > config.json > default path), error handling (backup corrupt files, re-run wizard), and backward compatibility (v1.0 configs work, dev mode unchanged). The implementation requires minimal refactoring since the wizard already creates both profile.json and config.json atomically, and search.py already has robust profile loading with validation.

The research confirms that the existing architecture (wizard → paths.py → config.py → search.py) provides the right foundation. The main work is:
1. Add `profile_path` field to wizard's config.json output
2. Update config.py to recognize `profile_path` as a known key
3. Refactor search.py to load profile from config.json setting (with CLI override)
4. Add validation-triggered wizard re-run on corrupt/missing profiles
5. Add `--no-wizard` and `--validate-profile` developer flags

**Primary recommendation:** Use config.json as profile path bridge (wizard writes it, search reads it) with argparse precedence preserved via two-pass parsing pattern already established in search.py. No external validation libraries needed - current JSON error handling is sufficient.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| argparse | stdlib (3.14+) | CLI argument parsing | Python standard library, robust precedence handling via `set_defaults()` |
| json | stdlib | Profile/config serialization | Python standard library, adequate for validation needs |
| pathlib | stdlib | Cross-platform path handling | Already used project-wide per PyInstaller best practices |
| tempfile | stdlib | Atomic file writes | Already used in wizard.py for corruption-safe writes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| platformdirs | 4.x | Platform-specific data dirs | Already used for `~/.job-radar` equivalent on all OSes |
| questionary | 4.x | Interactive prompts | Already used for wizard, same for wizard re-run triggers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| json validation | pydantic | Pydantic adds dependency for marginal benefit - current JSONDecodeError catching sufficient |
| argparse precedence | ConfigArgParse | ConfigArgParse adds dependency but project already has working two-pass pattern |
| manual validation | jsonschema | jsonschema adds dependency - profile structure simple enough for manual checks |

**Installation:**
No new dependencies required - all necessary libraries already in pyproject.toml.

## Architecture Patterns

### Recommended Integration Flow
```
Entry point (__main__.py):
├── SSL fix (if frozen)
├── Display banner
├── First-run check → wizard (if needed)
│   └── Writes: profile.json + config.json (with profile_path field)
├── Load config (config.py)
│   ├── Read config.json → extract profile_path
│   └── Set argparse defaults (two-pass pattern)
└── Run search (search.py)
    ├── Parse args (CLI --profile overrides config profile_path)
    ├── Validate profile → on error: backup + re-run wizard
    └── Execute search with validated profile
```

### Pattern 1: Configuration Precedence (Standard Pattern)
**What:** CLI flags take precedence over config file values, which take precedence over hardcoded defaults
**When to use:** Anytime mixing config files with CLI arguments
**Example:**
```python
# Source: ConfigArgParse documentation and argparse best practices
# Already implemented in search.py lines 318-325

# Two-pass parsing to establish precedence
pre_parser = argparse.ArgumentParser(add_help=False)
pre_parser.add_argument("--config", default=None)
pre_args, _ = pre_parser.parse_known_args()

# Load config and set defaults
config = load_config(pre_args.config)  # Returns dict with profile_path
args = parse_args(config)  # set_defaults(**config) applied

# CLI args override config values automatically via argparse
```

**Adaptation for Phase 8:**
```python
# config.py: Add profile_path to KNOWN_KEYS
KNOWN_KEYS = {"min_score", "new_only", "output", "profile_path"}

# wizard.py: Write profile_path to config.json
config_data = {
    "min_score": float(answers['min_score']),
    "new_only": answers['new_only'],
    "profile_path": str(profile_path),  # NEW
}

# search.py: Use profile_path from config if no --profile flag
def parse_args(config: dict | None = None):
    parser.add_argument(
        "--profile",
        required=False,  # No longer required - fallback to config
        help="Path to candidate profile JSON file",
    )
    if config:
        parser.set_defaults(**config)  # Applies profile_path from config
    return parser.parse_args()

# Later in main():
profile_path_arg = args.profile
if not profile_path_arg:
    # Fallback to default location if config didn't provide it
    from .paths import get_data_dir
    profile_path_arg = str(get_data_dir() / "profile.json")
profile = load_profile(profile_path_arg)
```

### Pattern 2: Validation with Automatic Recovery
**What:** On validation failure, backup corrupt file and re-run wizard to create fresh profile
**When to use:** User-editable config files that may become corrupt
**Example:**
```python
# Source: json-repair patterns and atomic file operations best practices

def load_profile_with_recovery(path: str) -> dict:
    """Load profile with automatic wizard re-run on corruption."""
    if not os.path.exists(path):
        # Missing profile - re-run wizard
        print(f"Profile not found at {path}. Running setup wizard...")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            sys.exit(1)
        # Wizard creates profile, try loading again
        return load_profile_with_recovery(path)

    try:
        with open(path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        # Corrupt JSON - backup and re-run wizard
        backup_path = f"{path}.bak"
        shutil.copy(path, backup_path)
        print(f"Profile JSON corrupt. Backed up to {backup_path}")
        print("Running setup wizard to create fresh profile...")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            sys.exit(1)
        return load_profile_with_recovery(path)

    # Validate structure
    required = ["name", "target_titles", "core_skills"]
    missing = [f for f in required if f not in profile]
    if missing:
        # Invalid structure - backup and re-run wizard
        backup_path = f"{path}.bak"
        shutil.copy(path, backup_path)
        print(f"Profile missing fields: {', '.join(missing)}")
        print(f"Backed up to {backup_path}. Running setup wizard...")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            sys.exit(1)
        return load_profile_with_recovery(path)

    return profile
```

### Pattern 3: Development Mode Flags
**What:** Add flags that preserve developer workflow while wizard is integrated
**When to use:** CLI tools transitioning from manual config to automatic setup
**Example:**
```python
# Source: Python argparse best practices and CLI testing patterns

parser.add_argument(
    "--no-wizard",
    action="store_true",
    help="Skip wizard checks (for development/testing)",
)

parser.add_argument(
    "--validate-profile",
    metavar="PATH",
    help="Validate profile.json without running search (debug mode)",
)

# In main():
if args.validate_profile:
    # Debug mode: validate and exit
    try:
        profile = load_profile(args.validate_profile)
        print(f"✓ Profile valid: {profile['name']}")
        print(f"  Titles: {len(profile['target_titles'])}")
        print(f"  Skills: {len(profile['core_skills'])}")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Profile invalid: {e}")
        sys.exit(1)

# First-run check respects --no-wizard
if not args.no_wizard:
    if is_first_run():
        # Run wizard...
```

### Pattern 4: Backward Compatibility with Legacy Configs
**What:** Support v1.0 config.json files that lack `profile_path` field
**When to use:** Upgrading CLI tools with existing user base
**Example:**
```python
# Source: PEP 387 backward compatibility policy

# search.py main():
profile_path_arg = args.profile
if not profile_path_arg:
    # No CLI flag - check if config provided profile_path
    config = load_config(args.config)
    if "profile_path" in config:
        # v1.1+ config with profile_path
        profile_path_arg = config["profile_path"]
    else:
        # Legacy v1.0 config OR first-run - use default location
        from .paths import get_data_dir
        profile_path_arg = str(get_data_dir() / "profile.json")

profile = load_profile_with_recovery(profile_path_arg)
```

### Anti-Patterns to Avoid
- **Removing --profile flag validation too early:** Keep --profile as explicit override even after adding config.json support. Emergency escape hatch if config breaks.
- **Silent fallback on validation failures:** Always inform user when backing up corrupt profile and re-running wizard. Silence hides data loss.
- **Treating dev mode differently than frozen mode:** Both should run wizard on first-run. Don't make dev mode "special" - breaks consistency testing.
- **Using sys.exit() in __main__.py wizard flow:** Already implemented correctly (lines 34-44) with graceful return codes. Don't change to sys.exit() mid-function.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config precedence | Custom if/else chains | argparse `set_defaults()` + two-pass | Already implemented pattern, well-tested, handles edge cases |
| JSON validation | Custom field checker | Existing load_profile() validation | search.py lines 184-219 already validate all required fields with helpful errors |
| Atomic file writes | open() + write() | tempfile + os.replace() | wizard.py `_write_json_atomic()` already implements this correctly |
| Profile path resolution | os.path.join | pathlib | Project standard per PyInstaller best practices (decision 06-01) |
| First-run detection | Environment variable | File existence check | wizard.py `is_first_run()` already implements this (line 123-132) |

**Key insight:** The wizard (Phase 7) and config module (Phase 2) already implement robust patterns. Phase 8 is primarily about connecting existing pieces, not building new infrastructure.

## Common Pitfalls

### Pitfall 1: Config set_defaults() and required=True Interaction
**What goes wrong:** argparse `required=True` is checked before `set_defaults()` applies, so profile_path from config.json never gets used
**Why it happens:** Argparse validates required args during parsing, but set_defaults() is called before parsing
**How to avoid:** Change `--profile` to `required=False` and manually check after parsing with fallback logic
**Warning signs:** Error "argument --profile: required" even when config.json contains profile_path
**Example fix:**
```python
# WRONG:
parser.add_argument("--profile", required=True)
parser.set_defaults(**config)  # profile_path from config ignored

# RIGHT:
parser.add_argument("--profile", required=False)
parser.set_defaults(**config)  # profile_path from config used if no CLI flag
args = parser.parse_args()
if not args.profile:
    args.profile = config.get("profile_path", default_profile_path)
```

### Pitfall 2: Circular Import Between wizard.py and search.py
**What goes wrong:** search.py tries to import run_setup_wizard, wizard.py imports paths module, paths module imports something from search.py (circular dependency)
**Why it happens:** Adding wizard import to search.py creates new import cycle
**How to avoid:** Import wizard functions locally inside functions, not at module level
**Warning signs:** ImportError: cannot import name 'X' from partially initialized module
**Example fix:**
```python
# WRONG (in search.py):
from .wizard import run_setup_wizard  # Module-level import

def load_profile_with_recovery(path):
    run_setup_wizard()  # May cause circular import

# RIGHT:
def load_profile_with_recovery(path):
    from .wizard import run_setup_wizard  # Local import
    run_setup_wizard()  # Safe from circular imports
```

### Pitfall 3: Wizard Re-run Infinite Loop
**What goes wrong:** Validation fails → wizard runs → writes corrupt profile → validation fails again → infinite loop
**Why it happens:** Wizard itself has bugs or validation is too strict, keeps failing same check
**How to avoid:** Add max retry counter (2 attempts), then fall back to --profile flag requirement with clear error message
**Warning signs:** Program hangs after "Running setup wizard..." message, CPU spins
**Example fix:**
```python
def load_profile_with_recovery(path: str, _retry_count: int = 0) -> dict:
    if _retry_count > 1:
        print("Error: Failed to create valid profile after multiple attempts.")
        print("Please use --profile flag to specify profile manually.")
        sys.exit(1)

    try:
        return load_profile(path)
    except Exception:
        # Backup, run wizard, retry with incremented counter
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            sys.exit(1)
        return load_profile_with_recovery(path, _retry_count + 1)
```

### Pitfall 4: Path Expansion Inconsistency
**What goes wrong:** Config.json contains `~/.job-radar/profile.json` but load_profile() receives unexpanded tilde, file not found
**Why it happens:** JSON files store strings literally; Python doesn't auto-expand `~`
**How to avoid:** Always use `Path(path).expanduser()` when loading path from config, or store absolute paths in config.json
**Warning signs:** Profile not found error despite file existing at expected location
**Example fix:**
```python
# wizard.py: Write absolute path to config
profile_path = get_data_dir() / "profile.json"
config_data["profile_path"] = str(profile_path)  # Absolute path

# search.py: Expand if relative/tilde path provided
profile_path = Path(args.profile).expanduser()
profile = load_profile(str(profile_path))
```

### Pitfall 5: PyInstaller Frozen Detection Not Checked
**What goes wrong:** Development mode works fine, but frozen executable fails with "profile not found" because get_data_dir() returns wrong path
**Why it happens:** Assuming get_data_dir() behavior is same in frozen vs dev mode without verifying
**How to avoid:** Test both modes. paths.py already handles this correctly (lines 26-36), but verify profile resolution works in frozen build
**Warning signs:** Works with `python -m job_radar`, fails with `./dist/job-radar/job-radar`
**Example verification:**
```bash
# Test dev mode
python -m job_radar  # Should run wizard on first-run

# Build and test frozen mode
pyinstaller job-radar.spec --clean
./dist/job-radar/job-radar  # Should also run wizard on first-run

# Verify both write to same location
python -c "from job_radar.paths import get_data_dir; print(get_data_dir())"
```

## Code Examples

Verified patterns from project codebase and research:

### Example 1: Two-Pass Argument Parsing with Config Precedence
```python
# Source: job_radar/search.py lines 318-325 (existing pattern)
# Adaptation: Add profile_path to config flow

def main():
    # Pass 1: Extract --config flag to load config file
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", default=None)
    pre_args, _ = pre_parser.parse_known_args()

    # Load config (includes profile_path if present)
    config = load_config(pre_args.config)

    # Pass 2: Parse all args with config defaults applied
    args = parse_args(config)

    # Profile path resolution with precedence:
    # 1. CLI --profile flag (highest)
    # 2. config.json profile_path field
    # 3. default location (lowest)
    profile_path_str = args.profile
    if not profile_path_str:
        from .paths import get_data_dir
        default_path = get_data_dir() / "profile.json"
        profile_path_str = str(default_path)

    # Load with automatic recovery on corruption
    profile = load_profile_with_recovery(profile_path_str)
```

### Example 2: Profile Loading with Wizard Recovery
```python
# Source: Research on validation patterns + existing search.py validation
# New function to add to search.py

def load_profile_with_recovery(path: str, _retry: int = 0) -> dict:
    """Load profile with automatic wizard re-run on validation failure.

    Handles:
    - Missing file: re-run wizard
    - Corrupt JSON: backup to .bak, re-run wizard
    - Invalid structure: backup to .bak, re-run wizard
    - Max 2 retries to prevent infinite loops

    Parameters
    ----------
    path : str
        Path to profile.json
    _retry : int
        Internal retry counter (do not set manually)

    Returns
    -------
    dict
        Validated profile dictionary
    """
    from pathlib import Path
    import shutil

    # Prevent infinite loops
    if _retry > 1:
        print(f"{C.RED}Error: Could not create valid profile after multiple attempts.{C.RESET}")
        print(f"\n{C.YELLOW}Please use --profile flag with a valid profile file.{C.RESET}")
        sys.exit(1)

    path_obj = Path(path).expanduser()

    # Check 1: File exists
    if not path_obj.exists():
        print(f"\n{C.YELLOW}Profile not found: {path}{C.RESET}")
        print("Running setup wizard to create profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    # Check 2: Valid JSON
    try:
        with open(path_obj, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        backup_path = f"{path}.bak"
        shutil.copy(path_obj, backup_path)
        print(f"\n{C.RED}Error: Profile JSON is corrupt{C.RESET}")
        print(f"  {e.msg} (line {e.lineno})")
        print(f"  Backed up to: {backup_path}\n")
        print("Running setup wizard to create fresh profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    # Check 3: Valid structure (reuse existing validation from load_profile)
    required = ["name", "target_titles", "core_skills"]
    missing = [f for f in required if f not in profile]
    if missing:
        backup_path = f"{path}.bak"
        shutil.copy(path_obj, backup_path)
        print(f"\n{C.RED}Error: Profile missing required fields: {', '.join(missing)}{C.RESET}")
        print(f"  Backed up to: {backup_path}\n")
        print("Running setup wizard to create fresh profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    # Type validation (reuse from load_profile)
    if not isinstance(profile.get("target_titles"), list) or not profile["target_titles"]:
        backup_path = f"{path}.bak"
        shutil.copy(path_obj, backup_path)
        print(f"\n{C.RED}Error: 'target_titles' must be a non-empty list{C.RESET}")
        print(f"  Backed up to: {backup_path}\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    if not isinstance(profile.get("core_skills"), list) or not profile["core_skills"]:
        backup_path = f"{path}.bak"
        shutil.copy(path_obj, backup_path)
        print(f"\n{C.RED}Error: 'core_skills' must be a non-empty list{C.RESET}")
        print(f"  Backed up to: {backup_path}\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    # Success - return validated profile
    return profile
```

### Example 3: Wizard Updates config.json with profile_path
```python
# Source: job_radar/wizard.py lines 323-327 (existing config creation)
# Adaptation: Add profile_path field

# In run_setup_wizard() function after building profile_data:
config_data = {
    "min_score": float(answers['min_score']),
    "new_only": answers['new_only'],
    "profile_path": str(profile_path),  # NEW: Tell search.py where profile is
}

# Write files atomically (existing code continues)
data_dir = get_data_dir()
profile_path = data_dir / "profile.json"
config_path = data_dir / "config.json"

_write_json_atomic(profile_path, profile_data)
_write_json_atomic(config_path, config_data)
```

### Example 4: Developer Flags for Testing
```python
# Source: Research on CLI testing patterns
# Add to parse_args() function in search.py

parser.add_argument(
    "--no-wizard",
    action="store_true",
    help="Skip first-run wizard (for development/testing with --profile flag)",
)

parser.add_argument(
    "--validate-profile",
    metavar="PATH",
    help="Validate profile JSON and exit (debug mode)",
)

# In main() after config loading:
if args.validate_profile:
    # Debug mode: validate profile and exit
    print(f"\n{C.BOLD}Validating profile:{C.RESET} {args.validate_profile}\n")
    try:
        profile = load_profile(args.validate_profile)
        print(f"{C.GREEN}✓ Profile valid{C.RESET}")
        print(f"  Name: {profile['name']}")
        print(f"  Titles: {len(profile['target_titles'])} ({', '.join(profile['target_titles'][:3])}...)")
        print(f"  Skills: {len(profile['core_skills'])} ({', '.join(profile['core_skills'][:5])}...)")
        if "dealbreakers" in profile:
            print(f"  Dealbreakers: {len(profile['dealbreakers'])}")
        print()
        sys.exit(0)
    except Exception as e:
        print(f"{C.RED}✗ Profile invalid:{C.RESET} {e}\n")
        sys.exit(1)

# First-run check with --no-wizard bypass
if not args.no_wizard:
    try:
        from job_radar.wizard import is_first_run, run_setup_wizard
        if is_first_run():
            print("\nWelcome to Job Radar!")
            # ... (existing wizard flow)
    except ImportError:
        pass  # questionary not installed
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual profile path in README | Auto-discover from config.json | Phase 8 (v1.1) | Users no longer need to remember --profile flag after wizard |
| --profile required flag | --profile optional with config fallback | Phase 8 (v1.1) | Seamless wizard → search flow, but --profile still works as override |
| No validation error recovery | Automatic wizard re-run on corrupt profile | Phase 8 (v1.1) | Users don't need to manually fix JSON syntax errors |
| Separate dev vs prod behavior | Identical behavior dev and frozen | Phase 8 (v1.1) | Testing parity improves reliability |
| profile.json + config.json separate | config.json bridges to profile.json | Phase 8 (v1.1) | Config becomes source of truth for profile location |

**Deprecated/outdated:**
- **Manual --profile flag requirement:** Still works but no longer required after wizard run
- **v1.0 config.json format without profile_path:** Still supported (backward compatibility) but new installs get profile_path field

## Open Questions

Things that couldn't be fully resolved:

1. **Should wizard update config.json if user manually moves profile.json?**
   - What we know: Wizard writes absolute path to config.json; if user moves profile.json later, config becomes stale
   - What's unclear: Should we add profile path auto-discovery (search multiple locations) or require user to re-run wizard with new path?
   - Recommendation: Keep simple - require `--profile` flag if user moves profile.json. Document in error message: "Profile not found at {path}. Use --profile flag to specify new location or re-run setup wizard."

2. **Should --validate-profile trigger wizard on validation failure?**
   - What we know: --validate-profile is debug flag for checking profile without running search
   - What's unclear: Should validation-only mode also offer to fix via wizard, or just report errors?
   - Recommendation: Validation-only mode should ONLY report errors (diagnostic tool). Automatic recovery only happens during normal search runs.

3. **How verbose should wizard re-run messages be?**
   - What we know: User needs to understand why wizard is running again (corrupt profile detected)
   - What's unclear: Balance between helpful context vs overwhelming users with technical details
   - Recommendation: Two-line message: "Profile corrupt/missing at {path}. Running setup wizard to create fresh profile..." Users who need details can check backup .bak file.

## Sources

### Primary (HIGH confidence)
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html) - Official Python 3.14 documentation for CLI argument parsing
- [PyInstaller Runtime Information](https://pyinstaller.org/en/stable/runtime-information.html) - Official PyInstaller 6.18.0 docs on sys.frozen detection
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html) - Official Python 3.14 documentation for path handling
- Existing codebase (job_radar/search.py, wizard.py, config.py, paths.py) - Verified current implementation patterns

### Secondary (MEDIUM confidence)
- [ConfigArgParse library documentation](https://pypi.org/project/ConfigArgParse/) - Alternative approach for config file precedence patterns
- [Python os.replace function guide](https://zetcode.com/python/os-replace/) - Atomic file operation patterns
- [How to Use Python argparse to Read Arguments from a File](https://www.pythontutorials.net/blog/how-to-get-argparse-to-read-arguments-from-a-file-with-an-option-rather-than-prefix/) - Config file integration patterns
- [PEP 387 Backwards Compatibility Policy](https://peps.python.org/pep-0387/) - Python's official backward compatibility guidelines
- [2026 Showdown: PyInstaller vs cx_Freeze vs Nuitka](https://ahmedsyntax.com/2026-comparison-pyinstaller-vs-cx-freeze-vs-nui/) - Frozen executable behavior patterns

### Tertiary (LOW confidence)
- [Python CLI first-run detection patterns](https://www.linkedin.com/pulse/automate-cli-configuration-using-python-script-blahuta-sc-cleared-) - General automation patterns, not specific to first-run detection
- [json-repair library](https://pypi.org/project/json-repair/) - Not needed for this phase (current JSONDecodeError handling sufficient)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, no new dependencies needed
- Architecture: HIGH - Two-pass parsing pattern already established, wizard already writes both files atomically
- Pitfalls: HIGH - Specific issues identified from codebase structure and argparse documentation

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days - stable domain, stdlib APIs don't change frequently)

**Key constraints from CONTEXT.md honored:**
- ✓ Config file setting for profile_path with CLI override precedence
- ✓ Legacy config handling (v1.0 backward compatibility)
- ✓ Wizard integration with automatic profile_path update
- ✓ Error handling flow (backup, re-run wizard, emergency override)
- ✓ Development mode behavior identical to frozen mode
- ✓ Profile validation at startup with automatic recovery
- ✓ Developer flags (--no-wizard, --validate-profile)
