"""Path resolution for both development and PyInstaller frozen modes."""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Check if running in a PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to a bundled resource.

    In development: resolves relative to the job_radar package directory.
    In frozen mode: resolves relative to sys._MEIPASS (PyInstaller bundle root).
    """
    if is_frozen():
        base_path = Path(sys._MEIPASS)
    else:
        # In dev, resources live alongside the package
        base_path = Path(__file__).parent
    return base_path / relative_path


def get_data_dir() -> Path:
    """Get platform-specific user data directory. Creates it if missing.

    Windows: %APPDATA%\\JobRadar
    macOS:   ~/Library/Application Support/JobRadar
    Linux:   ~/.local/share/JobRadar
    """
    from platformdirs import user_data_dir
    data_dir = Path(user_data_dir("JobRadar", "JobRadar"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_file() -> Path:
    """Get error log path: ~/job-radar-error.log."""
    return Path.home() / 'job-radar-error.log'
