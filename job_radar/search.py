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
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional

from .deps import get_os_info
from .sources import fetch_all, generate_manual_urls, build_search_queries
from .scoring import score_job
from .report import generate_report
from .tracker import mark_seen, get_stats

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

def parse_args():
    parser = argparse.ArgumentParser(
        description="Search and score job listings for a candidate profile."
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="Path to candidate profile JSON file",
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
        "--open",
        action="store_true",
        help="Auto-open the report after generation.",
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
        action="store_true",
        help="Only show new (unseen) results in the report.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Minimum score threshold for results (e.g. 3.0). Default: 2.8.",
    )
    return parser.parse_args()


def load_profile(path: str) -> dict:
    """Load and validate a candidate profile JSON file."""
    if not os.path.exists(path):
        print(f"{C.RED}Error: Profile not found: {path}{C.RESET}")
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        profile = json.load(f)

    required = ["name", "target_titles", "core_skills"]
    for field in required:
        if field not in profile:
            print(f"{C.RED}Error: Profile missing required field: {field}{C.RESET}")
            sys.exit(1)

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
# Report opener
# ---------------------------------------------------------------------------

def _open_file(path: str):
    """Open a file with the OS default application."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", path])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", path])
        elif system == "Windows":
            os.startfile(path)
        else:
            log.warning("Don't know how to open files on %s", system)
    except Exception as e:
        log.warning("Failed to open file: %s", e)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

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

    # Load profile
    profile = load_profile(args.profile)
    name = profile["name"]

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
    report_path = generate_report(
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

    # Summary
    recommended = [r for r in scored if r["score"]["overall"] >= 3.5]
    strong = [r for r in scored if r["score"]["overall"] >= 4.0]

    print(f"\n{C.BOLD}{'='*60}")
    print(f"  SEARCH COMPLETE — {name}")
    print(f"{'='*60}{C.RESET}")
    print(f"  Total results:      {len(scored)}")
    print(f"  New this run:       {C.GREEN}{new_count}{C.RESET}")
    print(f"  Recommended (3.5+): {C.YELLOW}{len(recommended)}{C.RESET}")
    print(f"  Strong (4.0+):      {C.GREEN}{len(strong)}{C.RESET}")
    if dealbreaker_count:
        print(f"  Dealbreakers:       {C.RED}{dealbreaker_count}{C.RESET}")
    print(f"  Report saved to:    {report_path}")

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
    print(f"  Open the report for full details: {report_path}")
    print()

    # Auto-open if requested
    if args.open:
        print(f"  Opening report...")
        _open_file(report_path)


if __name__ == "__main__":
    main()
