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
from datetime import datetime, timedelta
from typing import Optional

from . import __version__
from .config import load_config
from .deps import get_os_info
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
    parser = argparse.ArgumentParser(
        description="Search and score job listings for a candidate profile."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"job-radar {__version__}",
    )
    parser.add_argument(
        "--profile",
        required=False,
        help="Path to candidate profile JSON file",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to custom config file (default: ~/.job-radar/config.json)",
    )
    parser.add_argument(
        "--from",
        dest="from_date",
        default=None,
        help="Start date for results filter (YYYY-MM-DD). Default: 48 hours ago.",
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        default=None,
        help="End date for results filter (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Output directory for reports. Default: results/",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't auto-open report in browser",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what queries would be run without fetching.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable HTTP response caching.",
    )
    parser.add_argument(
        "--new-only",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Only show new (unseen) results in the report.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Minimum score threshold for results (e.g. 3.0). Default: 2.8.",
    )
    parser.add_argument(
        "--no-wizard",
        action="store_true",
        help="Skip first-run wizard (use with --profile for testing)",
    )
    parser.add_argument(
        "--validate-profile",
        metavar="PATH",
        help="Validate profile JSON and exit without searching",
    )
    if config:
        parser.set_defaults(**config)
    return parser.parse_args()


def load_profile(path: str) -> dict:
    """Load and validate a candidate profile JSON file."""
    if not os.path.exists(path):
        print(f"{C.RED}Error: Profile not found: {path}{C.RESET}")
        print(f"\n{C.YELLOW}Tip:{C.RESET} Create a profile from the template:")
        print(f"  cp profiles/_template.json profiles/your_name.json")
        print(f"  # Edit the file with your details")
        print(f"  job-radar --profile profiles/your_name.json")
        sys.exit(1)

    try:
        with open(path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        print(f"{C.RED}Error: Invalid JSON in profile: {e.msg} (line {e.lineno}){C.RESET}")
        sys.exit(1)

    if not isinstance(profile, dict):
        print(f"{C.RED}Error: Profile must be a JSON object, got {type(profile).__name__}{C.RESET}")
        sys.exit(1)

    # Check required fields
    required = ["name", "target_titles", "core_skills"]
    missing = [f for f in required if f not in profile]
    if missing:
        print(f"{C.RED}Error: Profile missing required fields: {', '.join(missing)}{C.RESET}")
        print(f"\n{C.YELLOW}Required fields:{C.RESET}")
        print(f"  - name: Your full name")
        print(f"  - target_titles: List of job titles to search (e.g., [\"Software Engineer\", \"Backend Developer\"])")
        print(f"  - core_skills: List of your top 5-7 technologies (e.g., [\"Python\", \"Django\", \"PostgreSQL\"])")
        sys.exit(1)

    # Validate field types and values
    if not isinstance(profile.get("target_titles"), list) or not profile["target_titles"]:
        print(f"{C.RED}Error: 'target_titles' must be a non-empty list of strings{C.RESET}")
        sys.exit(1)

    if not isinstance(profile.get("core_skills"), list) or not profile["core_skills"]:
        print(f"{C.RED}Error: 'core_skills' must be a non-empty list of strings{C.RESET}")
        sys.exit(1)

    # Warn about recommended fields
    recommended = {
        "level": "Seniority level (e.g., 'mid', 'senior')",
        "years_experience": "Total years of professional experience",
        "arrangement": "Work preferences (e.g., ['remote', 'hybrid'])",
    }
    warnings = []
    for field, description in recommended.items():
        if field not in profile:
            warnings.append(f"  - {field}: {description}")

    if warnings:
        print(f"\n{C.YELLOW}Warning: Missing recommended fields:{C.RESET}")
        for w in warnings:
            print(w)
        print(f"{C.DIM}These fields improve scoring accuracy. See WORKFLOW.md for details.{C.RESET}\n")

    return profile


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
    from pathlib import Path

    # Max retry check
    if _retry > 1:
        print(f"\n{C.RED}Error: Profile setup failed after multiple attempts{C.RESET}")
        print(f"\n{C.YELLOW}Tip:{C.RESET} Use --profile flag to specify a valid profile:")
        print(f"  job-radar --profile profiles/your_name.json")
        sys.exit(1)

    # Expand path (handle ~ in paths)
    expanded_path = Path(path).expanduser()
    path_str = str(expanded_path)

    # Check 1: File missing
    if not expanded_path.exists():
        print(f"\n{C.YELLOW}Profile not found:{C.RESET} {path_str}")
        print("Running setup wizard to create profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    # Check 2: JSON decode error (corrupt file)
    try:
        with open(expanded_path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        backup_path = f"{path_str}.bak"
        shutil.copy(expanded_path, backup_path)
        print(f"\n{C.RED}Profile corrupted:{C.RESET} Invalid JSON at line {e.lineno}")
        print(f"Backed up to: {backup_path}")
        print("Running setup wizard to create new profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    # Check 3: Missing required fields
    required = ["name", "target_titles", "core_skills"]
    missing = [f for f in required if f not in profile]
    if missing:
        backup_path = f"{path_str}.bak"
        shutil.copy(expanded_path, backup_path)
        print(f"\n{C.RED}Profile incomplete:{C.RESET} Missing required fields: {', '.join(missing)}")
        print(f"Backed up to: {backup_path}")
        print("Running setup wizard to create complete profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    # Check 4: Invalid field types/values
    if not isinstance(profile.get("target_titles"), list) or not profile["target_titles"]:
        backup_path = f"{path_str}.bak"
        shutil.copy(expanded_path, backup_path)
        print(f"\n{C.RED}Profile invalid:{C.RESET} 'target_titles' must be a non-empty list")
        print(f"Backed up to: {backup_path}")
        print("Running setup wizard to create valid profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    if not isinstance(profile.get("core_skills"), list) or not profile["core_skills"]:
        backup_path = f"{path_str}.bak"
        shutil.copy(expanded_path, backup_path)
        print(f"\n{C.RED}Profile invalid:{C.RESET} 'core_skills' must be a non-empty list")
        print(f"Backed up to: {backup_path}")
        print("Running setup wizard to create valid profile...\n")
        from .wizard import run_setup_wizard
        if not run_setup_wizard():
            print("\nSetup cancelled.")
            sys.exit(1)
        return load_profile_with_recovery(path, _retry + 1)

    # Profile valid - return it
    return profile


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

    def _on_fetch_progress(done, total, source):
        # Clear line and print progress (carriage return overwrites previous)
        print(f"\r  Fetching... {done}/{total} queries complete", end="", flush=True)
        if done == total:
            print()  # newline after final progress

    # Temporarily suppress fetch-level log output so it doesn't interleave with progress
    fetch_loggers = [logging.getLogger(n) for n in ("sources", "cache")]
    prev_levels = [l.level for l in fetch_loggers]
    if not args.verbose:
        for l in fetch_loggers:
            l.setLevel(logging.WARNING)

    all_results = fetch_all(profile, on_progress=_on_fetch_progress)

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

    # Step 5: Generate report
    manual_urls = generate_manual_urls(profile)
    sources_searched = list({r["job"].source for r in scored}) if scored else ["Dice", "HN Hiring", "RemoteOK", "WWR"]
    tracker_stats = get_stats()

    print(f"\n{C.BOLD}Step 5:{C.RESET} Generating report...")
    min_score = args.min_score if args.min_score is not None else 2.8

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
        print(f"\n{C.RED}Error: Report generation failed: {e}{C.RESET}")
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
        print(f"  Dealbreakers:       {C.RED}{dealbreaker_count}{C.RESET}")
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
