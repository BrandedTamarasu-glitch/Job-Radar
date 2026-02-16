"""Tests for update_checker module -- version detection and suppress tracking."""

import json
import queue
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from job_radar.update_checker import UpdateChecker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_config_path(tmp_path):
    """Temporary config.json path for isolated tests."""
    return tmp_path / "config.json"


@pytest.fixture
def checker(temp_config_path):
    """UpdateChecker instance with temporary config path."""
    with patch("job_radar.update_checker.get_data_dir", return_value=temp_config_path.parent):
        return UpdateChecker()


@pytest.fixture
def checker_with_queue(temp_config_path):
    """UpdateChecker with a result queue for async tests."""
    result_queue = queue.Queue()
    with patch("job_radar.update_checker.get_data_dir", return_value=temp_config_path.parent):
        return UpdateChecker(result_queue=result_queue), result_queue


# ---------------------------------------------------------------------------
# Version comparison tests
# ---------------------------------------------------------------------------


def test_version_comparison_newer():
    """is_newer_version correctly identifies newer versions."""
    assert UpdateChecker.is_newer_version("2.1.0", "2.2.0") is True
    assert UpdateChecker.is_newer_version("1.9.0", "1.10.0") is True  # NOT string sorting
    assert UpdateChecker.is_newer_version("2.0.0", "3.0.0") is True


def test_version_comparison_same():
    """is_newer_version returns False for same versions."""
    assert UpdateChecker.is_newer_version("2.1.0", "2.1.0") is False


def test_version_comparison_older():
    """is_newer_version returns False for older versions."""
    assert UpdateChecker.is_newer_version("2.2.0", "2.1.0") is False
    assert UpdateChecker.is_newer_version("3.0.0", "2.9.0") is False


def test_version_comparison_prerelease():
    """is_newer_version handles pre-releases correctly."""
    # Pre-release is older than release
    assert UpdateChecker.is_newer_version("2.1.0", "2.1.0-rc1") is False
    assert UpdateChecker.is_newer_version("2.0.0", "2.1.0-beta") is True


def test_version_comparison_invalid():
    """is_newer_version handles invalid versions gracefully."""
    assert UpdateChecker.is_newer_version("invalid", "2.1.0") is False
    assert UpdateChecker.is_newer_version("2.1.0", "invalid") is False
    assert UpdateChecker.is_newer_version("", "2.1.0") is False


# ---------------------------------------------------------------------------
# Check throttling tests
# ---------------------------------------------------------------------------


def test_should_check_first_run(checker, temp_config_path):
    """should_check returns True when no last_check exists."""
    assert checker.should_check() is True


def test_should_check_elapsed(checker, temp_config_path):
    """should_check returns True when 24+ hours have elapsed."""
    # Create config with old timestamp (25 hours ago)
    old_time = datetime.now(timezone.utc) - timedelta(hours=25)
    config = {
        "update_state": {
            "last_check": old_time.isoformat(),
            "auto_check_enabled": True,
        }
    }
    temp_config_path.write_text(json.dumps(config), encoding="utf-8")

    assert checker.should_check() is True


def test_should_check_too_recent(checker, temp_config_path):
    """should_check returns False when check was recent (< 24h)."""
    # Create config with recent timestamp (2 hours ago)
    recent_time = datetime.now(timezone.utc) - timedelta(hours=2)
    config = {
        "update_state": {
            "last_check": recent_time.isoformat(),
            "auto_check_enabled": True,
        }
    }
    temp_config_path.write_text(json.dumps(config), encoding="utf-8")

    assert checker.should_check() is False


def test_should_check_disabled(checker, temp_config_path):
    """should_check returns False when auto_check_enabled is False."""
    config = {
        "update_state": {
            "auto_check_enabled": False,
        }
    }
    temp_config_path.write_text(json.dumps(config), encoding="utf-8")

    assert checker.should_check() is False


# ---------------------------------------------------------------------------
# Suppress tracking tests
# ---------------------------------------------------------------------------


def test_should_show_banner_not_suppressed(checker):
    """should_show_banner returns True for unsuppressed version."""
    assert checker.should_show_banner("2.3.0") is True


def test_should_show_banner_suppressed_active(checker, temp_config_path):
    """should_show_banner returns False when version is actively suppressed."""
    # Suppress until 1 hour in the future
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    config = {
        "update_state": {
            "suppressed_versions": {
                "2.3.0": future_time.isoformat()
            }
        }
    }
    temp_config_path.write_text(json.dumps(config), encoding="utf-8")

    assert checker.should_show_banner("2.3.0") is False


def test_should_show_banner_suppressed_expired(checker, temp_config_path):
    """should_show_banner returns True when suppress has expired."""
    # Suppress expired 1 hour ago
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    config = {
        "update_state": {
            "suppressed_versions": {
                "2.3.0": past_time.isoformat()
            }
        }
    }
    temp_config_path.write_text(json.dumps(config), encoding="utf-8")

    assert checker.should_show_banner("2.3.0") is True


def test_should_show_banner_different_version(checker, temp_config_path):
    """should_show_banner is per-version (different version shows)."""
    # Suppress 2.3.0 but check 2.4.0
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    config = {
        "update_state": {
            "suppressed_versions": {
                "2.3.0": future_time.isoformat()
            }
        }
    }
    temp_config_path.write_text(json.dumps(config), encoding="utf-8")

    assert checker.should_show_banner("2.4.0") is True


# ---------------------------------------------------------------------------
# Dismiss version tests
# ---------------------------------------------------------------------------


def test_dismiss_version_24h(checker, temp_config_path):
    """dismiss_version saves 24-hour expiry correctly."""
    checker.dismiss_version("2.3.0", hours=24)

    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    expiry_str = config["update_state"]["suppressed_versions"]["2.3.0"]
    expiry = datetime.fromisoformat(expiry_str)

    # Should be ~24 hours in the future (allow 5 second tolerance for test execution)
    expected = datetime.now(timezone.utc) + timedelta(hours=24)
    diff = abs((expiry - expected).total_seconds())
    assert diff < 5


def test_dismiss_version_7d(checker, temp_config_path):
    """dismiss_version saves 7-day expiry correctly."""
    checker.dismiss_version("2.3.0", hours=168)  # 7 days

    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    expiry_str = config["update_state"]["suppressed_versions"]["2.3.0"]
    expiry = datetime.fromisoformat(expiry_str)

    # Should be ~168 hours in the future
    expected = datetime.now(timezone.utc) + timedelta(hours=168)
    diff = abs((expiry - expected).total_seconds())
    assert diff < 5


# ---------------------------------------------------------------------------
# GitHub API check tests
# ---------------------------------------------------------------------------


@patch("job_radar.update_checker.requests.get")
@patch("job_radar.update_checker.__version__", "2.1.0")
def test_check_for_updates_newer_version(mock_get, checker_with_queue, temp_config_path):
    """check_for_updates detects newer version and queues result."""
    checker, result_queue = checker_with_queue

    # Mock GitHub API response
    mock_response = Mock()
    mock_response.json.return_value = {
        "tag_name": "v2.2.0",
        "html_url": "https://github.com/coryebert/Job-Radar/releases/tag/v2.2.0"
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    checker.check_for_updates()

    # Check queue message (now includes tag_name)
    result = result_queue.get(timeout=1)
    assert result[0] == "update_available"
    assert result[1] == "2.2.0"
    assert "releases/tag/v2.2.0" in result[2]
    assert result[3] == "v2.2.0"  # tag_name

    # Check config updated
    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    assert config["update_state"]["check_success"] is True
    assert "last_check" in config["update_state"]


@patch("job_radar.update_checker.requests.get")
@patch("job_radar.update_checker.__version__", "2.2.0")
def test_check_for_updates_same_version(mock_get, checker_with_queue, temp_config_path):
    """check_for_updates detects same version."""
    checker, result_queue = checker_with_queue

    mock_response = Mock()
    mock_response.json.return_value = {
        "tag_name": "v2.2.0",
        "html_url": "https://github.com/coryebert/Job-Radar/releases/tag/v2.2.0"
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    checker.check_for_updates()

    result = result_queue.get(timeout=1)
    assert result[0] == "up_to_date"


@patch("job_radar.update_checker.requests.get")
@patch("job_radar.update_checker.__version__", "2.3.0")
def test_check_for_updates_older_version(mock_get, checker_with_queue, temp_config_path):
    """check_for_updates handles older remote version (dev build)."""
    checker, result_queue = checker_with_queue

    mock_response = Mock()
    mock_response.json.return_value = {
        "tag_name": "v2.2.0",
        "html_url": "https://github.com/coryebert/Job-Radar/releases/tag/v2.2.0"
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    checker.check_for_updates()

    result = result_queue.get(timeout=1)
    assert result[0] == "up_to_date"


@patch("job_radar.update_checker.requests.get")
def test_check_for_updates_network_error(mock_get, checker_with_queue, temp_config_path):
    """check_for_updates handles network errors gracefully."""
    checker, result_queue = checker_with_queue

    # Simulate timeout
    import requests
    mock_get.side_effect = requests.Timeout("Connection timeout")

    checker.check_for_updates()

    result = result_queue.get(timeout=1)
    assert result[0] == "check_failed"
    assert "timeout" in result[1].lower()

    # Config should still be updated
    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    assert config["update_state"]["check_success"] is False


# ---------------------------------------------------------------------------
# Config persistence tests
# ---------------------------------------------------------------------------


def test_get_update_status(checker, temp_config_path):
    """get_update_status returns current state."""
    config = {
        "update_state": {
            "last_check": "2026-02-16T10:30:00Z",
            "check_success": True,
            "auto_check_enabled": True,
        }
    }
    temp_config_path.write_text(json.dumps(config), encoding="utf-8")

    status = checker.get_update_status()
    assert status["last_check"] == "2026-02-16T10:30:00Z"
    assert status["check_success"] is True
    assert status["auto_check_enabled"] is True


def test_set_auto_check(checker, temp_config_path):
    """set_auto_check toggles auto_check_enabled flag."""
    checker.set_auto_check(False)

    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    assert config["update_state"]["auto_check_enabled"] is False

    checker.set_auto_check(True)

    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    assert config["update_state"]["auto_check_enabled"] is True


def test_config_atomic_write(checker, temp_config_path):
    """Config writes use atomic pattern (no temp files left behind)."""
    checker.dismiss_version("2.3.0", hours=24)

    # Check no .tmp files left in directory
    tmp_files = list(temp_config_path.parent.glob("*.tmp"))
    assert len(tmp_files) == 0

    # Config file should exist
    assert temp_config_path.exists()


# ---------------------------------------------------------------------------
# Skip version tests
# ---------------------------------------------------------------------------


def test_skip_version_stores_none_expiry(checker, temp_config_path):
    """skip_version stores None as expiry in suppressed_versions."""
    checker.skip_version("2.3.0")

    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    assert config["update_state"]["suppressed_versions"]["2.3.0"] is None


def test_should_show_banner_false_for_skipped(checker, temp_config_path):
    """should_show_banner returns False for permanently skipped versions."""
    checker.skip_version("2.3.0")
    assert checker.should_show_banner("2.3.0") is False


def test_should_show_banner_true_for_expired_dismiss(checker, temp_config_path):
    """should_show_banner returns True for expired time-based dismissals."""
    # Dismiss with expired timestamp
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    config = {
        "update_state": {
            "suppressed_versions": {
                "2.3.0": past_time.isoformat()
            }
        }
    }
    temp_config_path.write_text(json.dumps(config), encoding="utf-8")

    assert checker.should_show_banner("2.3.0") is True


def test_is_version_skipped_true_for_none(checker, temp_config_path):
    """is_version_skipped returns True for permanently skipped versions."""
    checker.skip_version("2.3.0")
    assert checker.is_version_skipped("2.3.0") is True


def test_is_version_skipped_false_for_timestamp(checker, temp_config_path):
    """is_version_skipped returns False for time-based dismissals."""
    checker.dismiss_version("2.3.0", hours=24)
    assert checker.is_version_skipped("2.3.0") is False


def test_is_version_skipped_false_for_unknown(checker):
    """is_version_skipped returns False for unknown versions."""
    assert checker.is_version_skipped("9.9.9") is False


def test_clear_skipped_versions_removes_none(checker, temp_config_path):
    """clear_skipped_versions removes permanent skips but preserves time-based."""
    # Skip two versions permanently
    checker.skip_version("2.3.0")
    checker.skip_version("2.4.0")

    # Dismiss one version with timestamp
    checker.dismiss_version("2.5.0", hours=24)

    # Clear skipped versions
    checker.clear_skipped_versions()

    # Check config
    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    suppressed = config["update_state"]["suppressed_versions"]

    # 2.3.0 and 2.4.0 should be removed (None values)
    assert "2.3.0" not in suppressed
    assert "2.4.0" not in suppressed

    # 2.5.0 should still be present (has timestamp)
    assert "2.5.0" in suppressed
    assert suppressed["2.5.0"] is not None


def test_get_skipped_versions_returns_list(checker, temp_config_path):
    """get_skipped_versions returns list of permanently skipped versions."""
    checker.skip_version("2.3.0")
    checker.skip_version("2.4.0")

    # Also dismiss a version with timestamp (should NOT be in list)
    checker.dismiss_version("2.5.0", hours=24)

    skipped = checker.get_skipped_versions()
    assert isinstance(skipped, list)
    assert "2.3.0" in skipped
    assert "2.4.0" in skipped
    assert "2.5.0" not in skipped


# ---------------------------------------------------------------------------
# Release notes tests
# ---------------------------------------------------------------------------


@patch("job_radar.update_checker.requests.get")
def test_fetch_release_notes_returns_body(mock_get, checker):
    """fetch_release_notes returns body from GitHub API."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "body": "## What's New\n\n- Feature A"
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    body = checker.fetch_release_notes("v2.3.0")
    assert body == "## What's New\n\n- Feature A"


@patch("job_radar.update_checker.requests.get")
def test_fetch_release_notes_empty_on_error(mock_get, checker):
    """fetch_release_notes returns empty string on network error."""
    import requests
    mock_get.side_effect = requests.Timeout("Connection timeout")

    body = checker.fetch_release_notes("v2.3.0")
    assert body == ""


@patch("job_radar.update_checker.requests.get")
def test_fetch_release_notes_empty_when_no_body(mock_get, checker):
    """fetch_release_notes returns empty string when body is None."""
    mock_response = Mock()
    mock_response.json.return_value = {"body": None}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    body = checker.fetch_release_notes("v2.3.0")
    assert body == ""


def test_cache_release_notes_persists(checker, temp_config_path):
    """cache_release_notes stores body in config."""
    checker.cache_release_notes("2.3.0", "notes text")

    config = json.loads(temp_config_path.read_text(encoding="utf-8"))
    cache = config["update_state"]["release_notes_cache"]["2.3.0"]

    assert cache["body"] == "notes text"
    assert "fetched_at" in cache


def test_get_cached_release_notes_hit(checker, temp_config_path):
    """get_cached_release_notes returns cached body when available."""
    checker.cache_release_notes("2.3.0", "notes text")
    body = checker.get_cached_release_notes("2.3.0")
    assert body == "notes text"


def test_get_cached_release_notes_miss(checker):
    """get_cached_release_notes returns None for uncached version."""
    body = checker.get_cached_release_notes("9.9.9")
    assert body is None


# ---------------------------------------------------------------------------
# Summary extraction tests
# ---------------------------------------------------------------------------


def test_extract_summary_bullets():
    """extract_summary returns first 5 bullets formatted with •."""
    from job_radar.update_checker import extract_summary

    markdown = """## What's New

- Feature one
- Feature two
- Feature three
- Feature four
- Feature five
- Feature six
- Feature seven
"""

    summary = extract_summary(markdown)

    # Should have 5 bullets
    assert summary.count("•") == 5
    assert "Feature one" in summary
    assert "Feature five" in summary
    assert "Feature six" not in summary
    assert "Feature seven" not in summary


def test_extract_summary_paragraph():
    """extract_summary returns paragraph when no bullets."""
    from job_radar.update_checker import extract_summary

    markdown = """## What's New

This is a text paragraph describing the release.
"""

    summary = extract_summary(markdown)
    assert "This is a text paragraph describing the release." in summary


def test_extract_summary_empty():
    """extract_summary returns fallback for empty input."""
    from job_radar.update_checker import extract_summary

    summary = extract_summary("")
    assert summary == "No release notes available for this version."

    summary = extract_summary("   \n\n  ")
    assert summary == "No release notes available for this version."


def test_extract_summary_truncates_long():
    """extract_summary truncates long paragraphs to 400 chars."""
    from job_radar.update_checker import extract_summary

    # 500 char paragraph (no heading)
    long_text = "a" * 500
    markdown = long_text

    summary = extract_summary(markdown)
    assert len(summary) <= 403  # 400 + "..."
    assert summary.endswith("...")
