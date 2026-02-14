"""Auto-update configuration infrastructure.

Prepares the foundation for future auto-update feature.
Does NOT implement the update mechanism itself - just the
configuration and version comparison utilities.

Future phases will add:
- GUI notification when update available
- Download and install workflow
"""

import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# URL where update manifest JSON is hosted
# Will be populated when GitHub Pages or similar hosting is configured
UPDATE_CHECK_URL = "https://coryebert.github.io/Job-Radar/update.json"

# Update manifest schema:
# {
#     "version": "2.1.0",
#     "min_version": "2.0.0",
#     "release_url": "https://github.com/coryebert/Job-Radar/releases/latest",
#     "macos_dmg_url": "https://github.com/.../Job-Radar-v2.1.0-macos.dmg",
#     "windows_exe_url": "https://github.com/.../Job-Radar-Setup-v2.1.0.exe",
#     "linux_tar_url": "https://github.com/.../job-radar-v2.1.0-linux.tar.gz",
#     "changelog": "https://github.com/coryebert/Job-Radar/blob/main/CHANGELOG.md"
# }


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string like '2.1.0' into a comparable tuple (2, 1, 0)."""
    try:
        # Strip leading 'v' if present
        cleaned = version_str.lstrip("v")
        return tuple(int(p) for p in cleaned.split("."))
    except (ValueError, AttributeError):
        log.warning("Could not parse version: %s", version_str)
        return (0, 0, 0)


def is_update_available(
    current_version: str, latest_version: str
) -> bool:
    """Check if latest_version is newer than current_version."""
    return parse_version(latest_version) > parse_version(current_version)


def is_version_supported(
    current_version: str, min_version: str
) -> bool:
    """Check if current_version meets the minimum version requirement."""
    return parse_version(current_version) >= parse_version(min_version)


def get_update_config() -> dict:
    """Return the update configuration dictionary.

    Returns a dict with UPDATE_CHECK_URL and other config
    that future auto-update code will use.
    """
    return {
        "check_url": UPDATE_CHECK_URL,
        "enabled": False,  # Disabled until auto-update is implemented
    }
