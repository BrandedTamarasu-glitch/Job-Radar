"""Browser opening utilities with headless environment detection."""

import logging
import os
import sys
import webbrowser
from pathlib import Path

log = logging.getLogger(__name__)


def is_headless_environment() -> bool:
    """
    Detect if running in a headless/CI/server environment.

    Checks for:
    - CI environment variables (GitHub Actions, GitLab, Travis, CircleCI)
    - Jenkins BUILD_ID
    - Missing DISPLAY on Linux (X11 headless)

    Returns:
        True if headless environment detected, False otherwise.

    Note:
        macOS does not require DISPLAY variable (doesn't use X11 by default),
        so DISPLAY check is skipped on Darwin platform.
    """
    # GitHub Actions, GitLab CI, Travis, CircleCI all set CI=true
    if os.environ.get("CI") == "true":
        log.debug("Headless environment detected: CI=true")
        return True

    # GitHub Actions specific
    if os.environ.get("GITHUB_ACTIONS") == "true":
        log.debug("Headless environment detected: GITHUB_ACTIONS=true")
        return True

    # Jenkins
    if os.environ.get("BUILD_ID"):
        log.debug("Headless environment detected: BUILD_ID present (Jenkins)")
        return True

    # Headless Linux (no X11 display)
    # Skip DISPLAY check on macOS - it doesn't use X11 by default
    if os.name == "posix" and sys.platform != "darwin" and not os.environ.get("DISPLAY"):
        log.debug("Headless environment detected: POSIX without DISPLAY")
        return True

    return False


def open_report_in_browser(html_path: str, auto_open: bool = True) -> dict:
    """
    Open HTML report in the default browser with environment detection.

    Uses pathlib.as_uri() to generate proper file:// URLs that work cross-platform,
    including Windows drive letters, UNC paths, and special characters.

    Args:
        html_path: Path to HTML file (absolute or relative)
        auto_open: If False, skip opening regardless of environment

    Returns:
        Dict with keys:
            - opened: bool (True if browser opened successfully)
            - reason: str (why browser didn't open, if applicable)

    Example:
        >>> result = open_report_in_browser("/path/to/report.html")
        >>> if result["opened"]:
        >>>     print("Report opened in browser")
        >>> else:
        >>>     print(f"Could not open: {result['reason']}")
    """
    if not auto_open:
        log.info("Browser auto-open disabled by user")
        return {"opened": False, "reason": "auto-open disabled by user"}

    if is_headless_environment():
        log.info("Skipping browser open in headless environment")
        return {"opened": False, "reason": "headless environment detected"}

    try:
        # Convert path to absolute file:// URL
        # CRITICAL: Use resolve() first to get absolute path, then as_uri()
        # This handles Windows drive letters, UNC paths, and special characters correctly
        file_path = Path(html_path).resolve()
        file_url = file_path.as_uri()

        log.debug(f"Opening browser with URL: {file_url}")
        success = webbrowser.open(file_url)

        if success:
            log.info(f"Report opened in browser: {html_path}")
            return {"opened": True, "reason": ""}
        else:
            log.warning("webbrowser.open() returned False - browser not available")
            return {"opened": False, "reason": "browser not available"}

    except Exception as e:
        log.warning(f"Failed to open browser: {e}")
        return {"opened": False, "reason": f"error: {e}"}
