#!/usr/bin/env python3
"""Job Search Optimization Toolkit — CLI entry point.

Usage:
    job-radar --profile profiles/your_name.json
    job-radar --profile profiles/your_name.json --from 2026-02-05 --to 2026-02-06
    job-radar --profile profiles/your_name.json --dry-run
    job-radar --profile profiles/your_name.json --open
"""

import argparse
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta
from typing import Optional

from . import __version__
from .config import load_config
from .deps import get_os_info
from .profile_manager import (
    load_profile as _pm_load_profile,
    ProfileValidationError,
    ProfileNotFoundError,
    ProfileCorruptedError,
)
from .sources import fetch_all, generate_manual_urls, build_search_queries
from .scoring import score_job
from .report import generate_report
from .tracker import mark_seen, get_stats
from .browser import open_report_in_browser

log = logging.getLogger("search")


# ---------------------------------------------------------------------------
# Color output helpers
# ---------------------------------------------------------------------------

def _colors_supported() -> bool:
    """Check if the terminal supports ANSI escape codes."""
    # Respect NO_COLOR standard (https://no-color.org/)
    if os.environ.get("NO_COLOR") is not None:
        return False
    if not sys.stdout.isatty():
        return False
    if platform.system() != "Windows":
        return True
    # Windows: modern terminals (Windows Terminal, VS Code, etc.) support ANSI.
    # WT_SESSION is set by Windows Terminal; TERM_PROGRAM by VS Code terminal.
    if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
        return True
    # Try enabling VT100 processing on older Windows consoles
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # STD_OUTPUT_HANDLE = -11, ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        return True
    except Exception:
        return False


class _Colors:
    """ANSI color codes, disabled on non-TTY or unsupported terminals."""
    _enabled = _colors_supported()

    RESET = "\033[0m" if _enabled else ""
    BOLD = "\033[1m" if _enabled else ""
    GREEN = "\033[32m" if _enabled else ""
    YELLOW = "\033[33m" if _enabled else ""
    RED = "\033[31m" if _enabled else ""
    CYAN = "\033[36m" if _enabled else ""
    DIM = "\033[2m" if _enabled else ""

C = _Colors


def _score_color(score: float) -> str:
    """Return color code for a score value."""
    if score >= 4.0:
        return C.GREEN
    elif score >= 3.5:
        return C.YELLOW
    else:
        return C.DIM


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def parse_args(config: dict | None = None):
    description = textwrap.dedent("""\
        Job Radar - Search and score job listings against your profile

        FIRST TIME? Just run without any flags to launch the setup wizard.
        The wizard guides you through creating your profile and preferences.

        RETURNING? Run without flags to search with your saved profile.
        Or use the flags below to customize your search:
    """)

    epilog = textwrap.dedent("""\
        Examples:
          job-radar                          Launch wizard (first run) or search
          job-radar --min-score 3.5          Search with higher quality threshold
          job-radar --profile path/to.json   Use a specific profile file
          job-radar --no-color               Disable colored output

        Accessibility:
          Set NO_COLOR=1 to disable all terminal colors.
          Use --profile to bypass the interactive wizard with screen readers.

        Docs: https://github.com/coryebert/job-radar
    """)

    parser = argparse.ArgumentParser(
        prog='job-radar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description,
        epilog=epilog
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"job-radar {__version__}",
    )

    # Search Options
    search_group = parser.add_argument_group('Search Options')
    search_group.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Minimum match score (1-5, default 2.8)",
    )
    search_group.add_argument(
        "--new-only",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Only show new (unseen) results",
    )
    search_group.add_argument(
        "--from",
        dest="from_date",
        default=None,
        help="Start date YYYY-MM-DD (default: 48 hours ago)",
    )
    search_group.add_argument(
        "--to",
        dest="to_date",
        default=None,
        help="End date YYYY-MM-DD (default: today)",
    )

    # Output Options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        "--output",
        default="results",
        help="Output directory for reports (default: results/)",
    )
    output_group.add_argument(
        "--no-open",
        action="store_true",
        help="Don't auto-open report in browser",
    )
    output_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output (also respects NO_COLOR env var)",
    )

    # Profile Options
    profile_group = parser.add_argument_group('Profile Options')
    profile_group.add_argument(
        "--profile",
        required=False,
        help="Path to candidate profile JSON",
    )
    profile_group.add_argument(
        "--config",
        default=None,
        help="Path to config file (default: auto-detect)",
    )
    profile_group.add_argument(
        "--validate-profile",
        metavar="PATH",
        help="Validate a profile JSON and exit",
    )

    # API Options
    api_group = parser.add_argument_group('API Options')
    api_group.add_argument(
        "--setup-apis",
        action="store_true",
        help="Interactive setup for API source credentials",
    )
    api_group.add_argument(
        "--test-apis",
        action="store_true",
        help="Test configured API keys and report status",
    )

    # Developer Options
    dev_group = parser.add_argument_group('Developer Options')
    dev_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show search queries without fetching",
    )
    dev_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    dev_group.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable HTTP response caching",
    )
    dev_group.add_argument(
        "--no-wizard",
        action="store_true",
        help="Skip setup wizard (for testing)",
    )

    if config:
        parser.set_defaults(**config)
    return parser.parse_args()


def load_profile(path: str) -> dict:
    """Load and validate a candidate profile JSON file."""
    from pathlib import Path as _Path
    try:
        return _pm_load_profile(_Path(path))
    except ProfileNotFoundError:
        print(f"{C.RED}Error: Profile not found: {path}{C.RESET}")
        print(f"\n{C.YELLOW}Tip:{C.RESET} Create a profile from the template:")
        print(f"  cp profiles/_template.json profiles/your_name.json")
        print(f"  job-radar --profile profiles/your_name.json")
        sys.exit(1)
    except ProfileCorruptedError as e:
        print(f"{C.RED}Error: {e}{C.RESET}")
        sys.exit(1)
    except ProfileValidationError as e:
        print(f"{C.RED}Error: {e}{C.RESET}")
        sys.exit(1)


def load_profile_with_recovery(path: str, _retry: int = 0) -> dict:
    """Load profile with wizard recovery on corrupt/missing files.

    Parameters
    ----------
    path : str
        Path to profile JSON file
    _retry : int
        Internal retry counter (max 2 attempts)

    Returns
    -------
    dict
        Validated profile dict

    Notes
    -----
    On missing or corrupt profile, backs up corrupt file (if exists),
    runs setup wizard, and retries. Max 2 retry attempts to prevent
    infinite loops. Uses local wizard import to avoid circular imports.
    """
    from pathlib import Path as _Path

    if _retry > 1:
        print(f"\n{C.RED}Error: Profile setup failed after multiple attempts{C.RESET}")
        print(f"\n{C.YELLOW}Tip:{C.RESET} Use --profile flag to specify a valid profile:")
        print(f"  job-radar --profile profiles/your_name.json")
        sys.exit(1)

    expanded_path = _Path(path).expanduser()

    try:
        return _pm_load_profile(expanded_path)
    except ProfileNotFoundError:
        print(f"\n{C.YELLOW}Profile not found:{C.RESET} {expanded_path}")
        print("Running setup wizard to create profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)
    except (ProfileCorruptedError, ProfileValidationError) as e:
        # Per user decision: warn and offer to re-run wizard on invalid profile
        backup_path = f"{expanded_path}.bak"
        shutil.copy(expanded_path, backup_path)
        print(f"\n{C.RED}Profile invalid:{C.RESET} {e}")
        print(f"Backed up to: {backup_path}")
        print("Running setup wizard to create valid profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)


# ---------------------------------------------------------------------------
# Date filtering
# ---------------------------------------------------------------------------

def _parse_relative_date(text: str) -> Optional[datetime]:
    """Parse relative date strings like 'Today', 'Yesterday', '2d ago', 'about 19 hours ago'."""
    import re
    text = text.strip().lower()
    now = datetime.now()

    if text == "today":
        return now
    if text == "yesterday":
        return now - timedelta(days=1)

    m = re.match(r'(\d+)\s*d(?:ays?)?\s+ago', text)
    if m:
        return now - timedelta(days=int(m.group(1)))

    m = re.match(r'(?:about\s+)?(\d+)\s*hours?\s+ago', text)
    if m:
        return now - timedelta(hours=int(m.group(1)))

    m = re.match(r'(?:about\s+)?(\d+)\s*min(?:utes?)?\s+ago', text)
    if m:
        return now - timedelta(minutes=int(m.group(1)))

    return None


def filter_by_date(results, from_date: str, to_date: str):
    """Filter results by date range. Best-effort since date formats vary."""
    filtered = []
    try:
        dt_from = datetime.strptime(from_date, "%Y-%m-%d")
        dt_to = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    except (ValueError, TypeError):
        return results

    for r in results:
        try:
            posted = None
            date_str = r.date_posted.strip()

            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%B %d, %Y", "%b %d, %Y"]:
                try:
                    posted = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

            if posted is None:
                posted = _parse_relative_date(date_str)

            if posted is not None:
                if dt_from <= posted <= dt_to:
                    filtered.append(r)
            else:
                # Can't parse date — only include if it looks recent
                lower = date_str.lower()
                if any(w in lower for w in ["today", "yesterday", "hour", "minute", "just", "recent"]):
                    filtered.append(r)
                elif "ago" in lower:
                    filtered.append(r)
                # else: exclude — unparseable date with no freshness indicators
        except Exception:
            filtered.append(r)  # include on parse errors to avoid silently dropping

    return filtered




# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Two-pass: extract --config before full parse so config defaults apply
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", default=None)
    pre_args, _ = pre_parser.parse_known_args()

    config = load_config(pre_args.config)
    args = parse_args(config)

    # Handle --no-color flag by setting NO_COLOR env var
    if args.no_color:
        os.environ["NO_COLOR"] = "1"
        # Reinitialize color codes
        _Colors._enabled = False
        _Colors.RESET = ""
        _Colors.BOLD = ""
        _Colors.GREEN = ""
        _Colors.YELLOW = ""
        _Colors.RED = ""
        _Colors.CYAN = ""
        _Colors.DIM = ""

    # Early exit handlers for API commands (no profile needed)
    if args.setup_apis:
        from .api_setup import setup_apis
        setup_apis()
        sys.exit(0)

    if args.test_apis:
        from .api_setup import test_apis
        test_apis()
        sys.exit(0)

    # Profile path resolution: CLI --profile > config.json profile_path > default location
    if args.validate_profile:
        # Debug mode: validate and exit
        try:
            profile = load_profile(args.validate_profile)
            print(f"\n{C.GREEN}Profile valid:{C.RESET} {args.validate_profile}")
            print(f"  Name: {profile['name']}")
            print(f"  Titles: {len(profile['target_titles'])}")
            print(f"  Skills: {len(profile['core_skills'])}")
            sys.exit(0)
        except SystemExit:
            raise  # Re-raise sys.exit from load_profile
        except Exception as e:
            print(f"\n{C.RED}Profile invalid:{C.RESET} {e}")
            sys.exit(1)

    profile_path_str = args.profile
    if not profile_path_str:
        # No CLI flag - use default wizard profile location
        from .paths import get_data_dir
        profile_path_str = str(get_data_dir() / "profile.json")

    if args.no_wizard:
        # Developer mode - use load_profile (no wizard recovery)
        profile = load_profile(profile_path_str)
    else:
        # Normal mode - use recovery (auto-wizard on corrupt/missing)
        profile = load_profile_with_recovery(profile_path_str)

    name = profile["name"]

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )
    # Quiet down noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # Load API credentials from .env (before fetching)
    from .api_config import load_api_credentials
    load_api_credentials()

    # Disable cache if requested
    if args.no_cache:
        from . import cache
        cache._CACHE_MAX_AGE_SECONDS = 0

    # Defaults: 48 hours ago to now
    from datetime import date as _date
    today = _date.today()
    from_date = args.from_date or (today - timedelta(days=2)).isoformat()
    to_date = args.to_date or today.isoformat()

    print(f"\n{C.BOLD}{'='*60}")
    print(f"  Job Search — {name}")
    print(f"  Date range: {from_date} to {to_date}")
    _os_info = get_os_info()
    print(f"  Platform: {_os_info['os_name']} ({_os_info['arch']})")
    print(f"{'='*60}{C.RESET}\n")

    # Dry-run mode — show queries and exit
    if args.dry_run:
        queries = build_search_queries(profile)
        print(f"{C.CYAN}Dry run — {len(queries)} queries would be executed:{C.RESET}\n")
        for i, q in enumerate(queries, 1):
            source = q["source"].upper()
            query = q["query"]
            location = q.get("location", "")
            loc_str = f" (location: {location})" if location else ""
            print(f"  {i:2d}. [{source}] {query}{loc_str}")
        print(f"\n{C.DIM}Manual check URLs would also be generated for: "
              f"{', '.join(profile.get('target_titles', [])[:3])}{C.RESET}")
        return

    # Step 1: Fetch
    print(f"{C.BOLD}Step 1:{C.RESET} Fetching job listings...")

    def _on_source_progress(source_name, count, total, status):
        """Display source-level progress — plain text, one line per event.

        Called TWICE per source:
        - status='started': prints "Fetching {source}... (N/M)" when source begins
        - status='complete': prints "{source} complete" when source finishes

        This provides real-time feedback: users see "Fetching..." the moment
        a source starts, not after it's already done.
        """
        if status == "started":
            print(f"  Fetching {source_name}... ({count}/{total})", flush=True)
        elif status == "complete":
            print(f"  {source_name} complete", flush=True)

    # Temporarily suppress fetch-level log output so it doesn't interleave with progress
    fetch_loggers = [logging.getLogger(n) for n in ("sources", "cache")]
    prev_levels = [l.level for l in fetch_loggers]
    if not args.verbose:
        for l in fetch_loggers:
            l.setLevel(logging.WARNING)

    try:
        all_results = fetch_all(profile, on_source_progress=_on_source_progress)
    except Exception as e:
        print("\nCouldn't fetch job listings — check your internet connection")
        from .banner import log_error_to_file
        log_error_to_file(f"Fetch failed: {e}", exception=e)
        sys.exit(1)

    for l, prev in zip(fetch_loggers, prev_levels):
        l.setLevel(prev)

    # Step 2: Date filter
    print(f"\n{C.BOLD}Step 2:{C.RESET} Filtering by date range ({from_date} to {to_date})...")
    filtered = filter_by_date(all_results, from_date, to_date)
    print(f"  {len(filtered)} results after date filtering (from {len(all_results)} total)")

    # Step 3: Score
    print(f"\n{C.BOLD}Step 3:{C.RESET} Scoring results against profile...")
    scored = []
    dealbreaker_count = 0
    for job in filtered:
        score = score_job(job, profile)
        if score.get("dealbreaker"):
            dealbreaker_count += 1
            continue
        scored.append({"job": job, "score": score})

    scored.sort(key=lambda x: x["score"]["overall"], reverse=True)
    if dealbreaker_count:
        print(f"  {C.DIM}{dealbreaker_count} results filtered by dealbreakers{C.RESET}")

    # Step 4: Track (dedup across runs)
    print(f"\n{C.BOLD}Step 4:{C.RESET} Tracking new vs. seen results...")
    scored = mark_seen(scored)
    new_count = sum(1 for r in scored if r.get("is_new", True))
    seen_count = len(scored) - new_count
    print(f"  {C.GREEN}{new_count} new{C.RESET}, {C.DIM}{seen_count} previously seen{C.RESET}")

    # Apply --new-only and --min-score filters
    pre_filter_count = len(scored)
    if args.new_only:
        scored = [r for r in scored if r.get("is_new", True)]
        print(f"  {C.DIM}--new-only: {pre_filter_count - len(scored)} seen results filtered{C.RESET}")
    if args.min_score is not None:
        before = len(scored)
        scored = [r for r in scored if r["score"]["overall"] >= args.min_score]
        print(f"  {C.DIM}--min-score {args.min_score}: {before - len(scored)} results below threshold{C.RESET}")

    # Check for zero results after scoring
    min_score = args.min_score if args.min_score is not None else 2.8
    if not scored:
        print(f"\n  No matches found — try broadening your skills or lowering min_score")
        print(f"  Current min_score: {min_score}")
        # Continue to generate report (includes manual check URLs)

    # Step 5: Generate report
    manual_urls = generate_manual_urls(profile)
    sources_searched = list({r["job"].source for r in scored}) if scored else ["Dice", "HN Hiring", "RemoteOK", "WWR"]
    tracker_stats = get_stats()

    print(f"\n{C.BOLD}Step 5:{C.RESET} Generating report...")

    try:
        report_result = generate_report(
            profile=profile,
            scored_results=scored,
            manual_urls=manual_urls,
            sources_searched=sources_searched,
            from_date=from_date,
            to_date=to_date,
            output_dir=args.output,
            tracker_stats=tracker_stats,
            min_score=min_score,
        )
    except Exception as e:
        print(f"\nReport generation failed — your results were found but couldn't be saved")
        print(f"Try running again or check available disk space")
        from .banner import log_error_to_file
        log_error_to_file(f"Report generation failed: {e}", exception=e)
        sys.exit(1)

    # Extract paths and stats from report result
    html_path = report_result["html"]
    md_path = report_result["markdown"]
    report_stats = report_result["stats"]

    # Summary
    recommended = [r for r in scored if r["score"]["overall"] >= 3.5]
    strong = [r for r in scored if r["score"]["overall"] >= 4.0]

    print(f"\n{C.BOLD}{'='*60}")
    print(f"  SEARCH COMPLETE — {name}")
    print(f"{'='*60}{C.RESET}")
    print(f"  Total results:      {report_stats['total']}")
    print(f"  New this run:       {C.GREEN}{report_stats['new']}{C.RESET}")
    print(f"  Recommended (3.5+): {C.YELLOW}{len(recommended)}{C.RESET}")
    print(f"  Strong (4.0+):      {C.GREEN}{len(strong)}{C.RESET}")
    if dealbreaker_count:
        print(f"  Dealbreakers:       {C.RED}{dealbreaker_count} filtered{C.RESET}")
    print(f"\n  Report (HTML):      {html_path}")
    print(f"  Report (Markdown):  {md_path}")

    # Tracker stats
    if tracker_stats["total_runs"] > 1:
        print(f"\n  {C.DIM}Lifetime: {tracker_stats['total_unique_jobs_seen']} unique jobs | "
              f"Avg {tracker_stats['avg_new_per_run_last_7']} new/run{C.RESET}")

    if recommended:
        print(f"\n  {C.BOLD}Top results:{C.RESET}")
        for r in recommended[:5]:
            job = r["job"]
            s = r["score"]["overall"]
            new_tag = f" {C.GREEN}[NEW]{C.RESET}" if r.get("is_new") else ""
            color = _score_color(s)
            print(f"    {color}[{s}/5.0]{C.RESET} {job.title} — {job.company} ({job.location}){new_tag}")
        print()

    print(f"  Manual check URLs generated: {len(manual_urls)}")
    print()

    # Browser opening
    auto_open = not args.no_open and config.get("auto_open_browser", True)

    if not scored:
        print(f"  {C.DIM}No results to display — skipping browser{C.RESET}\n")
    else:
        browser_result = open_report_in_browser(html_path, auto_open=auto_open)
        if browser_result["opened"]:
            print(f"  {C.GREEN}Report opened in default browser{C.RESET}\n")
        else:
            print(f"  Browser: {browser_result['reason']}. Open manually: {html_path}\n")


if __name__ == "__main__":
    main()
