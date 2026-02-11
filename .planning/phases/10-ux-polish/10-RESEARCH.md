# Phase 10: UX Polish - Research

**Researched:** 2026-02-09
**Domain:** Python CLI UX improvements (progress indicators, error handling, help text, signal handling)
**Confidence:** HIGH

## Summary

This phase enhances user-facing messaging and error handling for the Job Radar CLI application. The research focused on Python best practices for five specific UX domains: progress indicators, friendly error messages, welcome banners, help text formatting, and graceful interrupt handling.

The standard approach for CLI UX improvements in Python uses built-in libraries (argparse, signal, sys) with minimal external dependencies. Progress indicators should use simple text-based output with `sys.stdout.write()` and `\r` for same-line updates. Error handling should catch all exceptions, display friendly messages to users, and log technical details to a separate file. Help text should use argparse's `add_argument_group()` to organize flags functionally. Signal handling for Ctrl+C should use try-except blocks for KeyboardInterrupt at the top level.

All user decisions from CONTEXT.md are incorporated: plain text progress (no colors/symbols), friendly actionable error messages (no tracebacks), boxed welcome banner with version, and functionally-grouped help text with examples.

**Primary recommendation:** Use Python stdlib features (argparse, signal, sys.stdout) for all UX enhancements. No external libraries needed beyond what's already installed (questionary for wizard). Implement progress messaging as simple text updates, error handling with exception catching + logging, and help text with argument groups.

## Standard Stack

The established libraries/tools for Python CLI UX improvements:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| argparse | stdlib (3.10+) | Command-line argument parsing and help text generation | Built-in, comprehensive, officially recommended for Python CLIs |
| signal | stdlib | Signal handling for graceful shutdown | Built-in, cross-platform signal management |
| sys | stdlib | Standard streams (stdout, stderr, stdin) | Built-in, direct control over terminal output |
| logging | stdlib | Structured error logging to files | Built-in, mature logging framework with levels and handlers |
| pathlib | stdlib | File path operations | Built-in, required by PyInstaller best practices (decision 06-01) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| textwrap | stdlib | Text wrapping and indentation | Multi-line help text formatting |
| datetime | stdlib | Timestamps for error logs | Error logging timestamp generation |
| traceback | stdlib | Exception traceback formatting | Logging detailed error info to files (not shown to users) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| argparse | click, typer | More features but adds dependencies. argparse sufficient for Job Radar's needs |
| sys.stdout.write | tqdm, rich | Pretty progress bars but adds dependencies and may not work in all terminals (decision: plain text only) |
| Manual box drawing | pyfiglet (already installed), art | Pyfiglet already installed for banner.py, can fall back to manual box drawing |

**Installation:**
No new dependencies needed. All core libraries are Python stdlib. Pyfiglet already in pyproject.toml for banner.py (can be optional fallback).

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── __main__.py          # Top-level KeyboardInterrupt handler
├── search.py            # Progress callbacks, error display
├── sources.py           # Progress reporting from fetch operations
├── banner.py            # Welcome banner + error logging utilities
└── help_text.py         # (NEW) Custom help formatter for argparse
```

### Pattern 1: Progress Messaging (Plain Text, Vertical Stack)

**What:** Display progress updates that stack vertically (one line per source) without overwriting previous lines

**When to use:** When fetching from multiple job sources (4 sources) where users need reassurance during 10-30 second operations

**Example:**
```python
# Source: User decision from CONTEXT.md + Python best practices

# In sources.py - callback from parallel fetcher
def fetch_all(profile: dict, on_progress=None) -> list[JobResult]:
    completed = 0
    total = len(queries)

    for future in as_completed(futures):
        completed += 1
        if on_progress:
            on_progress(completed, total, source_name)

# In search.py - display progress
def _on_fetch_progress(done, total, source):
    """Print progress update - one line per source, plain text."""
    print(f"  Fetching {source}... ({done}/{total})")
    if done == total:
        print(f"  {source} complete")
```

**Why this pattern:**
- No colors/symbols (decision: plain text only, works everywhere including CI)
- Vertical stacking (decision: no in-place updates with \r)
- Minimal verbosity (decision: "Fetching Indeed... (1/4)" format)
- No job counts during fetch (decision: progress indicator shows source count, not job count)

### Pattern 2: Friendly Error Messages (User-facing + Debug Logs)

**What:** Catch all exceptions, show friendly actionable messages to users, log technical details to error file

**When to use:** For all error conditions: network failures, zero results, missing files, corrupt data, etc.

**Example:**
```python
# Source: Official Python docs + User decisions from CONTEXT.md

# Network error handling
try:
    results = fetch_dice(query)
except requests.RequestException as e:
    # User sees: friendly + actionable
    print("Couldn't reach Dice — check your internet connection")
    # Log technical details
    log_error_to_file(f"Network error: {e}", exception=e)

# Zero results handling
if not scored:
    print("No matches yet — try broadening your skills or lowering min_score")
    # Not an error, just informative

# Critical errors - exit cleanly
try:
    profile = load_profile(path)
except Exception as e:
    print(f"Error: {error_message}")
    print(f"Details logged to: {error_log_path}")
    sys.exit(1)
```

**Why this pattern:**
- Never show Python tracebacks to users (decision: hide technical details)
- Always actionable suggestions (decision: "check your internet connection", "try lowering min_score")
- Log full exception details to file for debugging (decision: error log file location is Claude's discretion)
- Exit cleanly with code 1 on critical errors (decision: don't try to continue with partial data)

### Pattern 3: Welcome Banner (Boxed Text with Version)

**What:** Display app name, version, and profile name in a boxed text banner on every run

**When to use:** At application launch, before wizard or search begins

**Example:**
```python
# Source: User decisions from CONTEXT.md + Python string formatting

def display_banner(version: str, profile_name: str = None) -> None:
    """Display welcome banner with version and profile name.

    Falls back to simple box if pyfiglet unavailable.
    """
    try:
        import pyfiglet
        # Try fancy banner first
        banner = pyfiglet.figlet_format("Job Radar", font="slant")
        print(banner.rstrip())
        print(f"  Version {version}")
        if profile_name:
            print(f"  Searching for {profile_name}")
        print("\n  Run with --help for options\n")
    except Exception:
        # Fallback: simple boxed text (decision: boxed text style)
        width = 60
        print("=" * width)
        print(f"  Job Radar v{version}".ljust(width))
        if profile_name:
            print(f"  Searching for {profile_name}".ljust(width))
        print("=" * width)
        print("\n  Run with --help for options\n")
```

**Why this pattern:**
- Every run (decision: banner frequency = every run)
- Boxed text style (decision: more visual than plain text, less space than ASCII art)
- Personalized with profile name (decision: "Job Radar v1.1 — Searching for [Your Name]")
- Help hint included (decision: add "Run with --help for options")
- Box drawing characters are Claude's discretion (can use = or Unicode box-drawing chars)

### Pattern 4: Help Text with Argument Groups

**What:** Organize argparse flags into functional groups with wizard-first explanation and examples

**When to use:** For --help output to guide non-technical users through CLI options

**Example:**
```python
# Source: Official Python argparse docs (https://docs.python.org/3/library/argparse.html)

import argparse
import textwrap

parser = argparse.ArgumentParser(
    prog='job-radar',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        Job Radar - Intelligent job search for your profile

        FIRST TIME? Run without flags to launch the interactive setup wizard.
        The wizard will ask for your name, skills, target titles, and preferences.
        '''),
    epilog=textwrap.dedent('''\
        Examples:
          job-radar                          # Launch wizard (first run) or search with saved profile
          job-radar --min-score 3.5          # Search with custom minimum score
          job-radar --profile custom.json    # Use a different profile

        For more info: https://github.com/yourusername/job-radar
        ''')
)

# Search Options group
search_group = parser.add_argument_group('Search Options')
search_group.add_argument('--min-score', type=float,
                          help='Minimum match score (1-5, default 2.8)')
search_group.add_argument('--new-only', action='store_true',
                          help='Only show new (unseen) results')

# Output Options group
output_group = parser.add_argument_group('Output Options')
output_group.add_argument('--output', default='results',
                          help='Output directory for reports')
output_group.add_argument('--no-open', action='store_true',
                          help="Don't auto-open report in browser")

# Profile Options group
profile_group = parser.add_argument_group('Profile Options')
profile_group.add_argument('--profile',
                           help='Path to candidate profile JSON file')
```

**Why this pattern:**
- Wizard-first explanation at top (decision: explain interactive wizard first)
- "Or use these flags" in description (decision: flags are for skipping wizard)
- Usage examples in epilog (decision: 2-3 common scenarios)
- Flags grouped by function (decision: "Search Options", "Output Options", "Profile Options")
- One-line descriptions (decision: brief but clear)
- RawDescriptionHelpFormatter preserves custom formatting in description/epilog

### Pattern 5: Graceful Ctrl+C Handling

**What:** Catch KeyboardInterrupt at top level and exit cleanly without traceback

**When to use:** During wizard prompts and during long-running search operations

**Example:**
```python
# Source: Official Python signal docs + Exception handling best practices
# https://docs.python.org/3/library/signal.html

# In __main__.py (top level)
def main():
    try:
        # Wizard
        from job_radar.wizard import run_setup_wizard
        run_setup_wizard()

        # Search
        from job_radar.search import main as search_main
        search_main()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        # Friendly error + log
        from job_radar.banner import log_error_and_exit
        log_error_and_exit(f"Fatal error: {e}", exception=e)

# In wizard.py (already handles Ctrl+C with questionary)
# questionary returns None on Ctrl+C, wizard asks to confirm exit

# In search.py (during long operations)
# KeyboardInterrupt propagates up to __main__.py handler
```

**Why this pattern:**
- Single top-level handler (simple, catches all Ctrl+C cases)
- No traceback shown (print clean message before exit)
- Exit code 0 for user interrupt (not an error, user chose to exit)
- Questionary already handles Ctrl+C gracefully (returns None, can confirm)
- Implementation is Claude's discretion (decision: just needs to exit gracefully without traceback)

### Anti-Patterns to Avoid

- **Using colors/ANSI codes for progress:** Decision specifies plain text only (CI-friendly, works everywhere)
- **In-place progress updates with \r:** Decision specifies vertical stacking (each source gets its own line)
- **Showing Python tracebacks to users:** Decision specifies never show tracebacks (friendly messages only)
- **Alphabetical flag ordering in help:** Decision specifies functional grouping (Search Options, Output Options, etc.)
- **Complex signal handlers:** Python docs warn signal handlers can interrupt code at critical points. Use simple try-except KeyboardInterrupt instead.
- **Multiple KeyboardInterrupt handlers:** One top-level handler is sufficient and clearer than scattering handlers throughout code

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Help text formatting | Custom --help logic | argparse.add_argument_group() | Built-in, handles line wrapping, maintains consistency |
| Terminal output buffering | Manual flush() everywhere | print(..., flush=True) or sys.stdout.write() + flush() | Built-in Python 3.3+, simpler API |
| Box drawing characters | Manual ASCII art | Simple = or - characters, or Unicode box-drawing chars | Keeps fallback simple, avoids encoding issues |
| Progress bars | Custom animation loops | Simple print() statements (per decision: plain text only) | Simpler, CI-friendly, no flicker issues |
| Error logging | Manual file append | logging module with FileHandler | Built-in, thread-safe, supports rotation and levels |
| Exception formatting | String manipulation | traceback.format_exc() | Built-in, handles all exception types correctly |

**Key insight:** Python's standard library provides mature, battle-tested solutions for all UX needs. External libraries (click, rich, tqdm) add features but also dependencies and complexity. For Job Radar's user decisions (plain text, no colors, simple progress), stdlib is perfect.

## Common Pitfalls

### Pitfall 1: Unbuffered Output Not Visible

**What goes wrong:** Progress updates don't appear until operation completes, defeating the purpose of progress indicators

**Why it happens:** Python buffers stdout by default. Print statements accumulate in buffer until newline or buffer full

**How to avoid:** Use `flush=True` parameter in print() or call `sys.stdout.flush()` after writes

**Warning signs:** Progress messages appear all at once after operation finishes instead of incrementally

**Code example:**
```python
# WRONG - progress won't show until end
for i in range(4):
    print(f"Fetching source {i}...")
    time.sleep(5)

# RIGHT - flush after each print
for i in range(4):
    print(f"Fetching source {i}...", flush=True)
    time.sleep(5)
```

### Pitfall 2: argparse Groups Don't Affect Parsing

**What goes wrong:** Developers expect add_argument_group() to affect validation or behavior

**Why it happens:** Argument groups only affect help text display, not parsing logic

**How to avoid:** Use groups purely for help organization. Use add_mutually_exclusive_group() if you need parsing constraints

**Warning signs:** Tests fail because grouped arguments don't behave differently

**Code example:**
```python
# add_argument_group() only affects help display
search_group = parser.add_argument_group('Search Options')
search_group.add_argument('--min-score', type=float)  # Same as parser.add_argument()

# For actual parsing constraints, use:
exclusive = parser.add_mutually_exclusive_group()
exclusive.add_argument('--new-only', action='store_true')
exclusive.add_argument('--all', action='store_true')
```

### Pitfall 3: KeyboardInterrupt Interrupts Cleanup

**What goes wrong:** Ctrl+C during file writes or resource cleanup leaves system in inconsistent state

**Why it happens:** KeyboardInterrupt can occur at any point, including inside context managers before `__exit__` runs

**How to avoid:**
1. Use atomic writes (temp file + rename) for important files
2. Catch KeyboardInterrupt at top level only, not in cleanup code
3. Use try-finally for critical cleanup (not context managers if interruption is a concern)

**Warning signs:** Corrupt profile.json files, orphaned temp files, unclosed database connections after Ctrl+C

**Code example:**
```python
# WRONG - KeyboardInterrupt can occur between __enter__ and __exit__
with open(profile_path, 'w') as f:
    json.dump(data, f)  # If Ctrl+C here, file may be partial

# RIGHT - atomic write with temp file (already used in wizard.py)
def _write_json_atomic(path: Path, data: dict):
    fd, tmp_path = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        Path(tmp_path).replace(path)  # Atomic on Unix and Windows
    except:
        os.unlink(tmp_path)
        raise
```

### Pitfall 4: Error Messages Leak Sensitive Information

**What goes wrong:** Error messages shown to users contain file paths, API keys, or internal implementation details

**Why it happens:** Default exception messages include stack traces and variable values

**How to avoid:** Catch exceptions, extract safe summary, log full details to file, show only safe summary to user

**Warning signs:** Error messages contain `/Users/dev/.env`, database connection strings, or API tokens

**Code example:**
```python
# WRONG - leaks internal details
try:
    api_key = os.environ['SECRET_API_KEY']
    response = requests.get(url, headers={'Authorization': api_key})
except Exception as e:
    print(f"Error: {e}")  # Shows full URL, headers, API key

# RIGHT - safe message to user, details in log
try:
    api_key = os.environ['SECRET_API_KEY']
    response = requests.get(url, headers={'Authorization': api_key})
except requests.RequestException as e:
    print("Couldn't connect to job board — check your internet connection")
    log_error_to_file(f"Network error: {e}", exception=e)  # Full details in file
```

### Pitfall 5: Help Text Too Long or Too Short

**What goes wrong:** Users either get overwhelmed (200-line help text) or confused (no examples)

**Why it happens:** No clear guidelines on what to include in help text

**How to avoid:** Follow user decisions: one-line descriptions per flag, 2-3 usage examples, wizard explanation at top

**Warning signs:** Users ask basic questions answered in --help, or --help output requires scrolling multiple screens

**Code example:**
```python
# WRONG - too verbose
parser.add_argument('--min-score',
    help='''Minimum match score threshold for filtering results.
    The scoring algorithm evaluates jobs on a 1-5 scale based on
    skill matches, title relevance, and dealbreaker presence.
    Lower scores (2.0-2.5) show more results but lower quality.
    Higher scores (3.5-4.0) show fewer results but better matches.
    Default is 2.8 which balances quantity and quality.''')

# RIGHT - one-line, clear (per user decision)
parser.add_argument('--min-score', type=float,
    help='Minimum match score (1-5, default 2.8)')
```

## Code Examples

Verified patterns from official sources and user decisions:

### Progress Indicator (Plain Text, Vertical Stack)

```python
# Source: User decision from CONTEXT.md + Python best practices
# File: job_radar/search.py

def _on_fetch_progress(done, total, source):
    """Display progress during job board fetching.

    Shows one line per source completion with plain text format.
    Per CONTEXT.md: Minimal verbosity, plain text only, stack vertically.
    """
    print(f"  Fetching {source}... ({done}/{total})", flush=True)
    if done == total:
        print(f"  All sources complete")

# In main()
print(f"\n{C.BOLD}Step 1:{C.RESET} Fetching job listings...")
all_results = fetch_all(profile, on_progress=_on_fetch_progress)
```

### Friendly Error Messages

```python
# Source: User decision from CONTEXT.md + error handling best practices
# File: job_radar/banner.py (extended)

import sys
import traceback
from datetime import datetime
from pathlib import Path

def log_error_and_exit(error_message: str, exception: Exception | None = None) -> None:
    """Log error to file and exit with friendly message.

    Per CONTEXT.md:
    - Show friendly + actionable message to user
    - Log technical details to error file
    - Exit cleanly with code 1
    """
    error_log = get_log_file()

    # Log technical details to file
    try:
        with open(error_log, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n[{timestamp}] {error_message}\n")
            if exception:
                f.write(f"Exception: {type(exception).__name__}: {exception}\n")
                f.write(traceback.format_exc())
    except Exception:
        pass  # Fail silently if can't write log

    # Show friendly message to user (no traceback)
    print(f"\nError: {error_message}")
    print(f"Details logged to: {error_log}")
    sys.exit(1)

# Usage in sources.py
try:
    body = fetch_with_retry(url, headers=HEADERS)
except requests.RequestException as e:
    # User sees: "Couldn't reach Indeed — check your internet connection"
    print(f"Couldn't reach {source} — check your internet connection")
    log_error_to_file(f"Network error fetching {source}: {e}", exception=e)
    return []
```

### Welcome Banner (Boxed Text)

```python
# Source: User decision from CONTEXT.md + pyfiglet fallback
# File: job_radar/banner.py (modified)

def display_banner(version: str = "1.1", profile_name: str | None = None) -> None:
    """Display welcome banner with version and profile name.

    Per CONTEXT.md:
    - Every run (banner frequency)
    - Boxed text style (more visual than plain, less space than ASCII art)
    - Name + version + profile name
    - Help hint below banner
    """
    try:
        import pyfiglet
        banner = pyfiglet.figlet_format("Job Radar", font="slant")
        print(banner.rstrip())
        print(f"  Version {version}")
        if profile_name:
            print(f"  Searching for {profile_name}")
    except Exception:
        # Fallback: simple boxed text (decision: box drawing is Claude's discretion)
        width = 60
        line = "=" * width
        print(f"\n{line}")
        print(f"  Job Radar v{version}".ljust(width))
        if profile_name:
            print(f"  Searching for {profile_name}".ljust(width))
        print(line)

    print("\n  Run with --help for options\n")
```

### Help Text with Groups and Examples

```python
# Source: Official argparse docs (https://docs.python.org/3/library/argparse.html)
# File: job_radar/search.py (modified parse_args)

import argparse
import textwrap

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with grouped help text and examples.

    Per CONTEXT.md:
    - Wizard-first explanation
    - 2-3 usage examples
    - Flags grouped by function
    - One-line descriptions
    """
    parser = argparse.ArgumentParser(
        prog='job-radar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
            Job Radar - Intelligent job search for your profile

            FIRST TIME? Run without flags to launch the interactive setup wizard.
            The wizard will ask for your name, skills, target titles, and preferences.

            Or use these flags to skip the wizard and customize your search:
            '''),
        epilog=textwrap.dedent('''\
            Examples:
              job-radar                          # Launch wizard (first run) or search
              job-radar --min-score 3.5          # Search with higher quality threshold
              job-radar --profile custom.json    # Use a different profile file

            For more information: https://github.com/yourusername/job-radar
            ''')
    )

    # Search Options
    search_group = parser.add_argument_group('Search Options')
    search_group.add_argument('--min-score', type=float,
        help='Minimum match score (1-5, default 2.8)')
    search_group.add_argument('--new-only', action=argparse.BooleanOptionalAction,
        help='Only show new (unseen) results')
    search_group.add_argument('--from', dest='from_date',
        help='Start date (YYYY-MM-DD, default: 48 hours ago)')
    search_group.add_argument('--to', dest='to_date',
        help='End date (YYYY-MM-DD, default: today)')

    # Output Options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output', default='results',
        help='Output directory for reports')
    output_group.add_argument('--no-open', action='store_true',
        help="Don't auto-open report in browser")

    # Profile Options
    profile_group = parser.add_argument_group('Profile Options')
    profile_group.add_argument('--profile',
        help='Path to candidate profile JSON')
    profile_group.add_argument('--validate-profile', metavar='PATH',
        help='Validate profile JSON and exit')

    # Developer Options
    dev_group = parser.add_argument_group('Developer Options')
    dev_group.add_argument('--dry-run', action='store_true',
        help='Show queries without fetching')
    dev_group.add_argument('--verbose', '-v', action='store_true',
        help='Enable debug logging')
    dev_group.add_argument('--no-cache', action='store_true',
        help='Disable HTTP caching')
    dev_group.add_argument('--no-wizard', action='store_true',
        help='Skip wizard (for testing)')

    return parser
```

### Graceful Ctrl+C Handling

```python
# Source: Python signal docs + KeyboardInterrupt best practices
# File: job_radar/__main__.py (modified)

def main():
    """Main entry point with graceful interrupt handling."""
    _fix_ssl_for_frozen()

    try:
        # Display banner
        from job_radar.banner import display_banner
        from job_radar import __version__
        display_banner(version=__version__)

        # Wizard
        import argparse as _argparse
        _pre = _argparse.ArgumentParser(add_help=False)
        _pre.add_argument("--no-wizard", action="store_true")
        _pre_args, _ = _pre.parse_known_args()

        if not _pre_args.no_wizard:
            try:
                from job_radar.wizard import is_first_run, run_setup_wizard
                if is_first_run():
                    print("\nWelcome to Job Radar!")
                    print("Let's set up your profile before your first search.\n")
                    if not run_setup_wizard():
                        print("\nSetup cancelled. Run again when you're ready!")
                        sys.exit(0)
                    print()
            except ImportError:
                pass  # questionary not installed

        # Search
        from job_radar.search import main as search_main
        search_main()

    except KeyboardInterrupt:
        # Per CONTEXT.md: graceful exit without traceback
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)

    except Exception as e:
        # Per CONTEXT.md: friendly error + log technical details
        try:
            from job_radar.banner import log_error_and_exit
            log_error_and_exit(f"Fatal error: {e}", exception=e)
        except Exception:
            # Last resort if logging fails
            print(f"\nFatal error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| print() without flush | print(..., flush=True) | Python 3.3+ | Real-time progress indicators work reliably |
| ArgumentParser with flat flags | add_argument_group() for organization | Python 2.7+ | Cleaner help text, functional grouping |
| signal.signal() for Ctrl+C | try-except KeyboardInterrupt | Current best practice (2024+) | Simpler, safer (avoids signal handler pitfalls) |
| Manual box drawing | Unicode box-drawing chars (U+2500–U+257F) | Python 3.0+ (Unicode) | Cleaner banners, but need fallback for old terminals |
| HelpFormatter subclasses | RawDescriptionHelpFormatter | Python 2.7+ | Preserve custom formatting without subclassing |

**Deprecated/outdated:**
- **optparse:** Deprecated since Python 2.7, replaced by argparse. Don't use for new code.
- **signal handlers for simple cleanup:** Python docs now recommend KeyboardInterrupt exceptions for simpler cases. Signal handlers are overkill unless doing complex async I/O.
- **Carriage return (\r) progress bars:** Still works but user decided on vertical stacking instead (simpler, CI-friendly, no flicker)

## Open Questions

1. **Box drawing characters for banner**
   - What we know: User decided "boxed text" style, exact characters are Claude's discretion
   - What's unclear: ASCII (= and -) vs Unicode box-drawing chars (├─┤)
   - Recommendation: Use simple ASCII (=/-) for maximum compatibility, or Unicode with ASCII fallback. Pyfiglet already installed for fancy banners.

2. **Error log file rotation**
   - What we know: Error log location is ~/job-radar-error.log
   - What's unclear: Should error log rotate/truncate after N entries, or append indefinitely?
   - Recommendation: Start with simple append (simpler). Add rotation in v2 if log file grows too large (use logging.handlers.RotatingFileHandler).

3. **Progress callback granularity**
   - What we know: Progress updates per source (4 sources total)
   - What's unclear: Should callback fire per query (12+ queries) or per source completion (4 times)?
   - Recommendation: Per source completion (decision: minimal verbosity). Each source reports when complete, not per-query.

## Sources

### Primary (HIGH confidence)
- [Python argparse official docs](https://docs.python.org/3/library/argparse.html) - add_argument_group(), formatter classes, help text
- [Python signal official docs](https://docs.python.org/3/library/signal.html) - Signal handling, KeyboardInterrupt patterns
- User decisions from CONTEXT.md - All UX style decisions (plain text, boxed banner, friendly errors, etc.)
- Current codebase analysis - Existing patterns in banner.py, wizard.py, search.py

### Secondary (MEDIUM confidence)
- [Progress Bars in Python Guide](https://www.datacamp.com/tutorial/progress-bars-in-python) - Plain text progress techniques
- [Python CLI UX Best Practices (2026)](https://medium.com/@wilson79/10-best-python-cli-libraries-for-developers-picking-the-right-one-for-your-project-cefb0bd41df1) - Modern CLI patterns
- [Error Handling Best Practices](https://llego.dev/posts/error-handling-strategies-best-practices-python/) - Friendly error messages, logging strategies
- [Python Print Flush Guide](https://medium.com/@ryan_forrester_/python-print-flush-complete-guide-b10ab1512390) - Buffering and real-time output

### Tertiary (LOW confidence)
- Various blog posts on argparse formatting - Supplementary examples
- FIGlet/pyfiglet documentation - Banner generation (already used in banner.py)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib except pyfiglet (already installed)
- Architecture: HIGH - Patterns verified from official docs + user decisions
- Pitfalls: HIGH - Based on Python docs warnings + common CLI development issues

**Research date:** 2026-02-09
**Valid until:** 60 days (stable domain - Python stdlib changes slowly, user decisions locked)
