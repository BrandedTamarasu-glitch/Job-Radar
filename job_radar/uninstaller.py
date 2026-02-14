"""Uninstaller module for Job Radar application.

Provides backup creation, data deletion, path enumeration, and platform-specific
cleanup script generation for complete application uninstallation.
"""

import logging
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

from .paths import get_data_dir, get_log_file, is_frozen
from .rate_limits import _cleanup_connections

log = logging.getLogger(__name__)


def get_uninstall_paths() -> list[tuple[str, str]]:
    """Get list of all application data paths with descriptions.

    Returns only paths that exist on disk.

    Returns
    -------
    list[tuple[str, str]]
        List of (path, description) tuples for files/directories to be deleted.
        Each entry has a human-readable description.
    """
    paths = []
    data_dir = get_data_dir()
    log_file = get_log_file()

    # Data directory contents
    profile_json = data_dir / "profile.json"
    if profile_json.exists():
        paths.append((str(profile_json), "profile.json - Your search preferences"))

    config_json = data_dir / "config.json"
    if config_json.exists():
        paths.append((str(config_json), "config.json - Application settings"))

    backups_dir = data_dir / "backups"
    if backups_dir.exists():
        paths.append((str(backups_dir), "backups/ - Profile backup files"))

    # Rate limit databases (current working directory)
    rate_limits_dir = Path.cwd() / ".rate_limits"
    if rate_limits_dir.exists():
        paths.append((str(rate_limits_dir), ".rate_limits/ - API rate limit databases"))

    # Cache directory if it exists
    cache_dir = data_dir / "cache"
    if cache_dir.exists():
        paths.append((str(cache_dir), "cache/ - Temporary cached data"))

    # Log file
    if log_file.exists():
        paths.append((str(log_file), "job-radar-error.log - Error logs"))

    return paths


def create_backup(save_path: str) -> None:
    """Create backup ZIP containing profile.json and config.json.

    Creates a ZIP file at the specified path containing only profile.json
    and config.json from the data directory. Files are stored at the root
    of the ZIP (no directory nesting).

    Parameters
    ----------
    save_path : str
        Path where the backup ZIP file should be created

    Raises
    ------
    Exception
        If ZIP file cannot be written (caller should handle error presentation)
    """
    data_dir = get_data_dir()
    files_to_backup = [
        ("profile.json", data_dir / "profile.json"),
        ("config.json", data_dir / "config.json"),
    ]

    with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for arcname, file_path in files_to_backup:
            if file_path.exists():
                zf.write(file_path, arcname=arcname)
                log.debug(f"Added {arcname} to backup")


def delete_app_data() -> list[tuple[str, str]]:
    """Delete all application data with best-effort error collection.

    Cleans up rate limiter SQLite connections before deletion to prevent
    "database is locked" errors. Deletes the data directory and log file.
    Continues on failure and collects all errors.

    Returns
    -------
    list[tuple[str, str]]
        List of (path, error_message) tuples for failed deletions.
        Empty list indicates complete success.
    """
    failures = []

    # Step 1: Close SQLite connections before deletion
    try:
        _cleanup_connections()
        log.debug("Cleaned up rate limiter connections")
    except Exception as e:
        log.warning(f"Error during connection cleanup: {e}")
        # Continue anyway - this is best-effort

    # Step 2: Delete data directory
    data_dir = get_data_dir()
    if data_dir.exists():
        def onerror(func, path, exc_info):
            """Collect deletion errors instead of raising."""
            error_msg = str(exc_info[1]) if exc_info[1] else "Unknown error"
            failures.append((path, error_msg))
            log.debug(f"Failed to delete {path}: {error_msg}")

        try:
            shutil.rmtree(data_dir, onerror=onerror)
            log.debug(f"Deleted data directory: {data_dir}")
        except Exception as e:
            failures.append((str(data_dir), str(e)))
            log.warning(f"Error deleting data directory: {e}")

    # Step 3: Delete log file
    log_file = get_log_file()
    if log_file.exists():
        try:
            log_file.unlink()
            log.debug(f"Deleted log file: {log_file}")
        except Exception as e:
            failures.append((str(log_file), str(e)))
            log.warning(f"Error deleting log file: {e}")

    return failures


def get_binary_path() -> Path | None:
    """Get path to application binary if running as frozen executable.

    Returns
    -------
    Path | None
        Path to the executable if frozen, None if running in development mode
    """
    if is_frozen():
        return Path(sys.executable)
    return None


def create_cleanup_script(binary_path: Path) -> tuple[str, str | None]:
    """Generate platform-specific cleanup script for binary deletion.

    Creates a script that will delete the application binary after the app
    exits. The script is executed in the background.

    Parameters
    ----------
    binary_path : Path
        Path to the application binary to delete

    Returns
    -------
    tuple[str, str | None]
        (message, script_path_or_none) where message is a user-facing
        instruction string and script_path_or_none is the path to the
        created script (or None if only manual instructions).
    """
    platform = sys.platform

    try:
        if platform == "darwin":
            # macOS: Check if inside .app bundle
            app_path = binary_path
            if ".app" in str(binary_path):
                # Resolve to .app directory
                parts = binary_path.parts
                for i, part in enumerate(parts):
                    if part.endswith(".app"):
                        app_path = Path(*parts[:i+1])
                        break

            # Create shell script to move to Trash
            script_path = Path.home() / ".job-radar-cleanup.sh"
            script_content = f"""#!/bin/bash
sleep 3
osascript -e 'tell application "Finder" to delete POSIX file "{app_path}"'
rm -f "$0"
"""
            script_path.write_text(script_content)
            script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)

            # Execute in background
            subprocess.Popen(
                ["/bin/bash", str(script_path)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return ("Data removed. The app will be moved to Trash shortly.", str(script_path))

        elif platform == "win32":
            # Windows: Create batch file
            script_path = Path.home() / "job-radar-cleanup.bat"
            script_content = f"""@echo off
timeout /t 3 /nobreak >nul
del /f /q "{binary_path}"
del /f /q "%~f0"
"""
            script_path.write_text(script_content)

            # Execute in background with no window
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                [str(script_path)],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return ("Data removed. The application will be deleted shortly.", str(script_path))

        else:
            # Linux: Create shell script
            script_path = Path.home() / ".job-radar-cleanup.sh"
            script_content = f"""#!/bin/bash
sleep 3
rm -f "{binary_path}"
rm -f "$0"
"""
            script_path.write_text(script_content)
            script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)

            # Execute in background
            subprocess.Popen(
                ["/bin/bash", str(script_path)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return ("Data removed. The application will be deleted shortly.", str(script_path))

    except Exception as e:
        log.warning(f"Failed to create cleanup script: {e}")
        return (f"Data removed. Please manually delete: {binary_path}", None)
