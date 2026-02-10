"""Startup banner and error logging for Job Radar."""

import sys
import traceback
from datetime import datetime
from pathlib import Path

from .paths import get_log_file


def display_banner(version: str = "1.1", profile_name: str | None = None) -> None:
    """Display 'Job Radar v1.1' ASCII art banner on launch.

    Uses pyfiglet with 'slant' font. Falls back to simple text
    banner if pyfiglet is unavailable or fails.

    Parameters
    ----------
    version : str
        Version string to display (e.g., "1.1.0")
    profile_name : str | None
        Candidate profile name to display. If None, profile line is omitted.
    """
    try:
        import pyfiglet
        banner = pyfiglet.figlet_format("Job Radar", font="slant")
        print(banner.rstrip())
        print(f"  Version {version}")
        if profile_name:
            print(f"  Searching for {profile_name}")
        print(f"\n  Run with --help for options\n")
    except Exception:
        print("=" * 50)
        print(f"  Job Radar v{version}")
        if profile_name:
            print(f"  Searching for {profile_name}")
        print("=" * 50)
        print(f"  Run with --help for options\n")


def log_error_and_exit(error_message: str, exception: Exception | None = None) -> None:
    """Log error to ~/job-radar-error.log and exit with brief console message."""
    error_log = get_log_file()

    try:
        with open(error_log, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {error_message}\n")
            if exception:
                f.write(f"  Exception: {type(exception).__name__}: {exception}\n")
                # Write full traceback for debugging
                f.write(traceback.format_exc())
                f.write("\n")
    except Exception:
        pass  # Fail silently if can't write log

    print(f"Error: {error_message}")
    print(f"Details logged to: {error_log}")
    sys.exit(1)


def log_error_to_file(error_message: str, exception: Exception | None = None) -> None:
    """Log error to ~/job-radar-error.log without exiting (fire-and-forget).

    Parameters
    ----------
    error_message : str
        Human-readable error message to log
    exception : Exception | None
        Optional exception object to log with traceback

    Notes
    -----
    Used for non-fatal errors (e.g., individual source failures).
    Fails silently if unable to write log file.
    """
    try:
        error_log = get_log_file()
        with open(error_log, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {error_message}\n")
            if exception:
                f.write(f"  Exception: {type(exception).__name__}: {exception}\n")
                # Write full traceback for debugging
                f.write(traceback.format_exc())
                f.write("\n")
    except Exception:
        pass  # Fail silently if can't write log
