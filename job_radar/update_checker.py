"""Auto-update checker for Job Radar.

Checks GitHub Releases API for new versions, with throttling, per-version
suppress tracking, and atomic config persistence.
"""

import json
import logging
import os
import queue
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from packaging.version import InvalidVersion, Version

from job_radar import __version__
from job_radar.paths import get_data_dir

log = logging.getLogger(__name__)

# GitHub API constants
GITHUB_API_URL = "https://api.github.com/repos/BrandedTamarasu-glitch/Job-Radar/releases/latest"
GITHUB_RELEASES_TAG_URL = "https://api.github.com/repos/BrandedTamarasu-glitch/Job-Radar/releases/tags/{tag}"
CHECK_INTERVAL_HOURS = 24
REQUEST_TIMEOUT = 10


def get_platform_asset_pattern() -> str:
    """Get regex pattern for installer filename based on platform.

    Returns:
        Regex pattern string for matching installer filenames

    Raises:
        RuntimeError: If platform is not supported
    """
    if sys.platform == "darwin":
        return r"\.dmg$"
    elif sys.platform == "win32":
        return r"\.exe$"
    elif sys.platform.startswith("linux"):
        return r"\.tar\.gz$"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


class UpdateChecker:
    """Manages update checks, version comparison, and suppress tracking."""

    def __init__(self, result_queue: queue.Queue | None = None):
        """Initialize update checker.

        Args:
            result_queue: Optional queue for async result messages.
                Messages are tuples:
                - ("update_available", version, url)
                - ("up_to_date",)
                - ("check_failed", error_message)
        """
        self.result_queue = result_queue
        self.config_path = get_data_dir() / "config.json"

    @staticmethod
    def is_newer_version(current: str, latest: str) -> bool:
        """Check if latest version is newer than current using semantic versioning.

        Uses packaging.version.Version for PEP 440 compliant comparison.
        Handles version strings with or without 'v' prefix.

        Args:
            current: Current version string (e.g., "2.1.0")
            latest: Latest version string to compare (e.g., "2.2.0")

        Returns:
            True if latest > current, False otherwise.
            Returns False on any InvalidVersion error.

        Examples:
            >>> UpdateChecker.is_newer_version("2.1.0", "2.2.0")
            True
            >>> UpdateChecker.is_newer_version("1.9.0", "1.10.0")
            True
            >>> UpdateChecker.is_newer_version("2.1.0", "2.1.0-rc1")
            False
        """
        try:
            # Strip 'v' prefix if present
            current_clean = current.lstrip("v")
            latest_clean = latest.lstrip("v")

            current_ver = Version(current_clean)
            latest_ver = Version(latest_clean)

            return latest_ver > current_ver
        except InvalidVersion:
            return False

    def _load_config(self) -> dict:
        """Load config.json, returning empty dict if missing or invalid."""
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            log.warning("Could not load config from %s", self.config_path)
            return {}

    def _save_config(self, config: dict) -> None:
        """Save config.json atomically using temp-file-plus-rename pattern."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=self.config_path.parent,
            prefix=self.config_path.name + ".",
            suffix=".tmp",
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            Path(tmp_path).replace(self.config_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise

    def _get_update_state(self) -> dict:
        """Get update_state section from config, creating if missing."""
        config = self._load_config()
        return config.setdefault("update_state", {})

    def _update_state(self, updates: dict) -> None:
        """Update specific fields in update_state section."""
        config = self._load_config()
        update_state = config.setdefault("update_state", {})
        update_state.update(updates)
        config["update_state"] = update_state
        self._save_config(config)

    def should_check(self) -> bool:
        """Determine if update check should run based on throttling and user preferences.

        Returns False if:
        - auto_check_enabled is explicitly set to False
        - last_check was less than 24 hours ago

        Returns True if:
        - First run (no last_check exists)
        - 24+ hours since last check
        - auto_check_enabled is True or not set (default True)
        """
        state = self._get_update_state()

        # Check user preference (default to enabled)
        if not state.get("auto_check_enabled", True):
            return False

        # Check throttle
        last_check_str = state.get("last_check")
        if not last_check_str:
            return True  # First run

        try:
            last_check = datetime.fromisoformat(last_check_str)
            elapsed = datetime.now(timezone.utc) - last_check
            return elapsed >= timedelta(hours=CHECK_INTERVAL_HOURS)
        except (ValueError, TypeError):
            # Invalid timestamp -> allow check
            return True

    def should_show_banner(self, version: str) -> bool:
        """Check if update banner should be shown for a specific version.

        Returns False if version is currently suppressed (expiry in future).
        Returns True if:
        - Version not in suppressed_versions
        - Version suppress has expired
        - Different version (per-version tracking)

        Args:
            version: Version string to check (e.g., "2.3.0")
        """
        state = self._get_update_state()
        suppressed = state.get("suppressed_versions", {})

        if version not in suppressed:
            return True

        # Check if suppress has expired
        try:
            expiry = datetime.fromisoformat(suppressed[version])
            return datetime.now(timezone.utc) >= expiry
        except (ValueError, TypeError):
            # Invalid expiry -> show banner
            return True

    def dismiss_version(self, version: str, hours: int) -> None:
        """Suppress update notifications for a version for specified duration.

        Args:
            version: Version string to suppress (e.g., "2.3.0")
            hours: Duration in hours (24 for "Dismiss", 168 for "Remind Later")
        """
        expiry = datetime.now(timezone.utc) + timedelta(hours=hours)
        expiry_str = expiry.isoformat()

        config = self._load_config()
        update_state = config.setdefault("update_state", {})
        suppressed = update_state.setdefault("suppressed_versions", {})
        suppressed[version] = expiry_str

        self._save_config(config)

    def check_for_updates(self) -> None:
        """Check GitHub Releases API for new version.

        Queries the latest release, compares with current __version__,
        and puts result on queue (if provided).

        Updates config with:
        - last_check: Current timestamp
        - check_success: True if API call succeeded, False on error

        Queue messages:
        - ("update_available", version, url, tag_name) if newer version found
        - ("up_to_date",) if no update needed
        - ("check_failed", error_message) on network error
        """
        now = datetime.now(timezone.utc).isoformat()

        try:
            response = requests.get(
                GITHUB_API_URL,
                headers={"User-Agent": f"Job-Radar/{__version__}"},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()
            tag_name = data.get("tag_name", "")
            html_url = data.get("html_url", "")

            # Strip 'v' prefix from tag
            latest_version = tag_name.lstrip("v")

            # Update state (success)
            self._update_state({
                "last_check": now,
                "check_success": True,
            })

            # Compare versions
            if self.is_newer_version(__version__, latest_version):
                if self.result_queue:
                    self.result_queue.put(("update_available", latest_version, html_url, tag_name))
            else:
                if self.result_queue:
                    self.result_queue.put(("up_to_date",))

        except requests.Timeout as e:
            self._update_state({
                "last_check": now,
                "check_success": False,
            })
            error_msg = f"Connection timeout: {e}"
            if self.result_queue:
                self.result_queue.put(("check_failed", error_msg))

        except requests.RequestException as e:
            self._update_state({
                "last_check": now,
                "check_success": False,
            })
            error_msg = f"Network error: {e}"
            if self.result_queue:
                self.result_queue.put(("check_failed", error_msg))

        except Exception as e:
            # Unexpected error (JSON parse, etc.)
            self._update_state({
                "last_check": now,
                "check_success": False,
            })
            error_msg = f"Update check error: {e}"
            log.exception("Unexpected error during update check")
            if self.result_queue:
                self.result_queue.put(("check_failed", error_msg))

    def get_update_status(self) -> dict:
        """Get current update check status for display in Settings.

        Returns:
            dict with keys:
            - last_check: ISO timestamp string or None
            - check_success: bool or None
            - auto_check_enabled: bool (default True)
        """
        state = self._get_update_state()
        return {
            "last_check": state.get("last_check"),
            "check_success": state.get("check_success"),
            "auto_check_enabled": state.get("auto_check_enabled", True),
        }

    def set_auto_check(self, enabled: bool) -> None:
        """Enable or disable automatic update checks.

        Args:
            enabled: True to enable auto-check, False to disable
        """
        self._update_state({"auto_check_enabled": enabled})

    def fetch_release_assets(self, tag: str) -> list[dict]:
        """Fetch release assets from GitHub for a specific tag.

        Args:
            tag: Release tag name (e.g., "v2.2.0")

        Returns:
            List of asset dicts with keys: name, browser_download_url, digest, size.
            Returns empty list on any error.
        """
        url = GITHUB_RELEASES_TAG_URL.format(tag=tag)

        try:
            response = requests.get(
                url,
                headers={"User-Agent": f"Job-Radar/{__version__}"},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()
            assets_raw = data.get("assets", [])

            # Extract relevant fields from each asset
            assets = []
            for asset in assets_raw:
                assets.append({
                    "name": asset.get("name", ""),
                    "browser_download_url": asset.get("browser_download_url", ""),
                    "digest": asset.get("digest"),  # May be None
                    "size": asset.get("size", 0),
                })

            return assets

        except requests.RequestException as e:
            log.error("Failed to fetch release assets for tag %s: %s", tag, e)
            return []

    def select_platform_asset(self, assets: list[dict]) -> dict | None:
        """Select the appropriate installer asset for the current platform.

        Args:
            assets: List of asset dicts (from fetch_release_assets)

        Returns:
            Asset dict for current platform, or None if no match found
        """
        try:
            pattern = get_platform_asset_pattern()
        except RuntimeError as e:
            log.error("Cannot select asset: %s", e)
            return None

        for asset in assets:
            if re.search(pattern, asset["name"], re.IGNORECASE):
                return asset

        return None

    def get_installer_download_path(self, version: str) -> Path:
        """Get the destination path for downloaded installer.

        Uses system temp directory with version-stamped filename.

        Args:
            version: Version string (e.g., "2.2.0")

        Returns:
            Path to destination file
        """
        temp_dir = tempfile.gettempdir()

        # Determine filename based on platform
        if sys.platform == "darwin":
            filename = f"Job-Radar-v{version}-installer.dmg"
        elif sys.platform == "win32":
            filename = f"Job-Radar-Setup-v{version}.exe"
        elif sys.platform.startswith("linux"):
            filename = f"job-radar-v{version}-installer.tar.gz"
        else:
            # Fallback
            filename = f"job-radar-v{version}-installer"

        return Path(temp_dir) / filename
