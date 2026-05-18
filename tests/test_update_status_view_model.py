from datetime import datetime, timedelta, timezone

from job_radar.gui.update_status_view_model import (
    build_update_status_display,
    format_last_check_relative_time,
)


def test_format_last_check_relative_time_handles_empty_and_invalid_values():
    assert format_last_check_relative_time(None) == "Never"
    assert format_last_check_relative_time("not a timestamp") == "Unknown"


def test_format_last_check_relative_time_uses_compact_ranges():
    now = datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc)

    assert format_last_check_relative_time(
        (now - timedelta(seconds=120)).isoformat(),
        now=now,
    ) == "Just now"
    assert format_last_check_relative_time(
        (now - timedelta(minutes=20)).isoformat(),
        now=now,
    ) == "20m ago"
    assert format_last_check_relative_time(
        (now - timedelta(hours=5)).isoformat(),
        now=now,
    ) == "5h ago"
    assert format_last_check_relative_time(
        (now - timedelta(days=3)).isoformat(),
        now=now,
    ) == "3d ago"


def test_build_update_status_display_formats_never_checked_state():
    display = build_update_status_display(
        current_version="2.7.0",
        status_info={},
    )

    assert display.text == "v2.7.0 -- Last checked: Never -- Never checked"
    assert display.color == "gray"


def test_build_update_status_display_formats_success_and_failure_states():
    now = datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc)
    last_check = (now - timedelta(minutes=10)).isoformat()

    success = build_update_status_display(
        current_version="2.7.0",
        status_info={"last_check": last_check, "check_success": True},
        now=now,
    )
    failure = build_update_status_display(
        current_version="2.7.0",
        status_info={"last_check": last_check, "check_success": False},
        now=now,
    )

    assert success.text == "v2.7.0 -- Last checked: 10m ago -- Up to date"
    assert success.color == "green"
    assert failure.text == "v2.7.0 -- Last checked: 10m ago -- Check failed"
    assert failure.color == "orange"


def test_build_update_status_display_prioritizes_available_update():
    now = datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc)
    last_check = (now - timedelta(minutes=10)).isoformat()

    display = build_update_status_display(
        current_version="2.7.0",
        status_info={"last_check": last_check, "check_success": True},
        update_version="2.8.0",
        now=now,
    )
    skipped = build_update_status_display(
        current_version="2.7.0",
        status_info={"last_check": last_check, "check_success": True},
        update_version="2.8.0",
        update_skipped=True,
        now=now,
    )

    assert display.text == "v2.7.0 -- Last checked: 10m ago -- v2.8.0 available"
    assert display.color == "orange"
    assert skipped.text == "v2.7.0 -- Last checked: 10m ago -- v2.8.0 available (skipped)"
    assert skipped.color == "gray"
