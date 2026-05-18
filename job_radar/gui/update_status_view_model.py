"""View-model helpers for Settings update status display."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class UpdateStatusDisplay:
    """Display text and color for the Settings update status label."""

    text: str
    color: str


def build_update_status_display(
    *,
    current_version: str,
    status_info: dict[str, Any],
    update_version: str | None = None,
    update_skipped: bool = False,
    now: datetime | None = None,
) -> UpdateStatusDisplay:
    """Return Settings update status label display data."""
    relative_time = format_last_check_relative_time(status_info.get("last_check"), now=now)
    status, color = _base_update_status(relative_time, status_info.get("check_success"))

    if update_version and update_skipped:
        status = f"v{update_version} available (skipped)"
        color = "gray"
    elif update_version:
        status = f"v{update_version} available"
        color = "orange"

    return UpdateStatusDisplay(
        text=f"v{current_version} -- Last checked: {relative_time} -- {status}",
        color=color,
    )


def format_last_check_relative_time(
    last_check: object,
    *,
    now: datetime | None = None,
) -> str:
    """Format update-check timestamp as compact relative text."""
    if not last_check:
        return "Never"

    try:
        last_check_dt = datetime.fromisoformat(str(last_check))
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        elapsed = current_time - last_check_dt
    except Exception:
        return "Unknown"

    total_seconds = elapsed.total_seconds()
    if total_seconds < 300:
        return "Just now"
    if total_seconds < 3600:
        return f"{int(total_seconds / 60)}m ago"
    if total_seconds < 86400:
        return f"{int(total_seconds / 3600)}h ago"
    return f"{int(total_seconds / 86400)}d ago"


def format_skipped_versions_status(skipped_versions: list[str] | tuple[str, ...]) -> str:
    """Format the Settings skipped-version status line."""
    if not skipped_versions:
        return ""
    return f"Skipped: {', '.join('v' + version for version in skipped_versions)}"


def _base_update_status(relative_time: str, check_success: object) -> tuple[str, str]:
    if relative_time == "Never":
        return "Never checked", "gray"
    if check_success:
        return "Up to date", "green"
    if check_success is False:
        return "Check failed", "orange"
    return "Unknown", "gray"
