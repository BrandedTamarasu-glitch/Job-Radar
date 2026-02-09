"""Startup banner and error logging for Job Radar."""

import sys
from datetime import datetime
from pathlib import Path

from .paths import get_log_file


def display_banner(version: str = "1.1") -> None:
    """Display 'Job Radar v1.1' ASCII art banner on launch.

    Uses pyfiglet with 'slant' font. Falls back to simple text
    banner if pyfiglet is unavailable or fails.
    """
    try:
        import pyfiglet
        banner = pyfiglet.figlet_format("Job Radar", font="slant")
        print(banner.rstrip())
        print(f"  Version {version}\n")
    except Exception:
        print("=" * 50)
        print(f"  Job Radar v{version}")
        print("=" * 50)
        print()


def log_error_and_exit(error_message: str, exception: Exception | None = None) -> None:
    """Log error to ~/job-radar-error.log and exit with brief console message."""
    error_log = get_log_file()

    try:
        with open(error_log, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {error_message}\n")
            if exception:
                f.write(f"  Exception: {type(exception).__name__}: {exception}\n")
    except Exception:
        pass  # Fail silently if can't write log

    print(f"Error: {error_message}")
    print(f"Details logged to: {error_log}")
    sys.exit(1)
