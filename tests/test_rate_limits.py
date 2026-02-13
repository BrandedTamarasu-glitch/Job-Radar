"""Tests for rate_limits module covering rate limiter functionality."""

import pytest
from pathlib import Path
from job_radar.rate_limits import (
    BACKEND_API_MAP,
    RATE_LIMITS,
    check_rate_limit,
    get_rate_limit_status,
    get_rate_limiter,
)


@pytest.fixture(autouse=True)
def reset_limiter_cache():
    """Reset module-level limiter cache between tests to prevent pollution."""
    from job_radar import rate_limits
    import time

    # Clear before test
    rate_limits._limiters.clear()
    rate_limits._connections.clear()

    yield

    # Clean up after test - wait for background threads to finish
    time.sleep(0.05)  # Give background leaker thread time to complete

    # Clear limiters first (this stops the background threads)
    rate_limits._limiters.clear()

    # Then close connections
    for conn in rate_limits._connections.values():
        try:
            conn.close()
        except:
            pass
    rate_limits._connections.clear()


def test_rate_limits_dict_has_expected_sources():
    """Test RATE_LIMITS dict contains expected source configurations."""
    assert "adzuna" in RATE_LIMITS
    assert "authentic_jobs" in RATE_LIMITS


def test_check_rate_limit_allows_first_call(tmp_path, monkeypatch):
    """Test check_rate_limit returns True on first call (not rate limited)."""
    monkeypatch.chdir(tmp_path)

    result = check_rate_limit("adzuna")

    assert result is True


def test_check_rate_limit_returns_bool(tmp_path, monkeypatch):
    """Test check_rate_limit returns boolean value."""
    monkeypatch.chdir(tmp_path)

    result = check_rate_limit("adzuna")

    assert isinstance(result, bool)


def test_get_rate_limit_status_returns_dict(tmp_path, monkeypatch):
    """Test get_rate_limit_status returns dict with expected keys."""
    monkeypatch.chdir(tmp_path)

    status = get_rate_limit_status("adzuna")

    assert isinstance(status, dict)
    assert "remaining" in status
    assert "configured_rate" in status
    assert "reset_time" in status


def test_rate_limit_creates_db_file(tmp_path, monkeypatch):
    """Test rate limiter creates SQLite database file."""
    monkeypatch.chdir(tmp_path)

    check_rate_limit("adzuna")

    db_path = tmp_path / ".rate_limits" / "adzuna.db"
    assert db_path.exists()


def test_independent_source_limits(tmp_path, monkeypatch):
    """Test different sources have independent rate limits."""
    monkeypatch.chdir(tmp_path)

    # Both should be allowed on first call (independent limits)
    result_adzuna = check_rate_limit("adzuna")
    result_authentic = check_rate_limit("authentic_jobs")

    assert result_adzuna is True
    assert result_authentic is True

    # Verify separate DB files created
    adzuna_db = tmp_path / ".rate_limits" / "adzuna.db"
    authentic_db = tmp_path / ".rate_limits" / "authentic_jobs.db"
    assert adzuna_db.exists()
    assert authentic_db.exists()


def test_cleanup_closes_all_connections(tmp_path, monkeypatch):
    """Test _cleanup_connections closes all SQLite connections and clears limiters."""
    from job_radar import rate_limits

    monkeypatch.chdir(tmp_path)

    # Create multiple rate limiters (creates connections and limiters)
    check_rate_limit("adzuna")
    check_rate_limit("authentic_jobs")

    # Verify connections and limiters exist
    assert len(rate_limits._connections) == 2
    assert len(rate_limits._limiters) == 2
    assert "adzuna" in rate_limits._connections
    assert "authentic_jobs" in rate_limits._connections

    # Call cleanup
    rate_limits._cleanup_connections()

    # Verify both limiters and connections were cleared
    # Limiters must be cleared first to stop background threads
    assert len(rate_limits._limiters) == 0
    assert len(rate_limits._connections) == 0


def test_shared_backend_limiters(tmp_path, monkeypatch):
    """Test sources mapped to same backend API share limiter instance."""
    from job_radar import rate_limits

    monkeypatch.chdir(tmp_path)

    # Temporarily add test mapping for sources sharing same backend
    # Simulate future JSearch scenario where multiple sources share backend
    original_map = rate_limits.BACKEND_API_MAP.copy()
    rate_limits.BACKEND_API_MAP.update({
        "test_source_1": "shared_backend",
        "test_source_2": "shared_backend",
    })

    # Add rate config for the shared backend
    rate_limits.RATE_LIMITS["shared_backend"] = [rate_limits.Rate(60, rate_limits.Duration.MINUTE)]

    try:
        # Get limiters for both sources
        limiter1 = get_rate_limiter("test_source_1")
        limiter2 = get_rate_limiter("test_source_2")

        # Both sources should get the same limiter instance
        assert limiter1 is limiter2, "Sources with same backend should share limiter instance"

        # Should only create one connection (for shared_backend, not per source)
        assert len(rate_limits._connections) == 1
        assert "shared_backend" in rate_limits._connections

        # Should only create one limiter cache entry
        assert len(rate_limits._limiters) == 1
        assert "shared_backend" in rate_limits._limiters

        # Should only create one database file (using backend name)
        db_path = tmp_path / ".rate_limits" / "shared_backend.db"
        assert db_path.exists()

    finally:
        # Restore original mapping
        rate_limits.BACKEND_API_MAP.clear()
        rate_limits.BACKEND_API_MAP.update(original_map)


def test_backend_map_fallback(tmp_path, monkeypatch):
    """Test unmapped sources use source name as backend (backward compatibility)."""
    from job_radar import rate_limits

    monkeypatch.chdir(tmp_path)

    # Use a source not in BACKEND_API_MAP
    unmapped_source = "unmapped_test_source"
    assert unmapped_source not in rate_limits.BACKEND_API_MAP

    # Get limiter for unmapped source
    limiter = get_rate_limiter(unmapped_source)

    # Should create connection and limiter using source name as fallback
    assert unmapped_source in rate_limits._connections
    assert unmapped_source in rate_limits._limiters

    # Should create database file using source name
    db_path = tmp_path / ".rate_limits" / f"{unmapped_source}.db"
    assert db_path.exists()


def test_rate_limits_loaded_from_config(tmp_path, monkeypatch):
    """Test rate limits are loaded from config.json when present."""
    import json
    from job_radar import rate_limits

    monkeypatch.chdir(tmp_path)

    # Create config file with custom rate limits
    config_dir = tmp_path / ".job-radar"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({
        "rate_limits": {
            "adzuna": [{"limit": 200, "interval": 60}],
            "custom_api": [{"limit": 50, "interval": 30}]
        }
    }))

    # Mock the config path to use tmp_path
    monkeypatch.setenv("HOME", str(tmp_path))

    # Reload rate_limits module to pick up new config
    import importlib
    importlib.reload(rate_limits)

    # Verify custom limits were loaded
    assert "adzuna" in rate_limits.RATE_LIMITS
    assert len(rate_limits.RATE_LIMITS["adzuna"]) == 1  # Custom has 1 rate, not default's 2
    assert rate_limits.RATE_LIMITS["adzuna"][0].limit == 200

    assert "custom_api" in rate_limits.RATE_LIMITS
    assert len(rate_limits.RATE_LIMITS["custom_api"]) == 1
    assert rate_limits.RATE_LIMITS["custom_api"][0].limit == 50
    assert rate_limits.RATE_LIMITS["custom_api"][0].interval == 30


def test_rate_limits_invalid_config_uses_defaults(tmp_path, monkeypatch, caplog):
    """Test invalid rate limit configs show warnings and use defaults."""
    import json
    from job_radar import rate_limits
    import logging

    monkeypatch.chdir(tmp_path)
    caplog.set_level(logging.WARNING)

    # Create config file with invalid rate limits
    config_dir = tmp_path / ".job-radar"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({
        "rate_limits": "not_a_dict"  # Invalid: should be dict
    }))

    # Mock the config path
    monkeypatch.setenv("HOME", str(tmp_path))

    # Reload rate_limits module
    import importlib
    importlib.reload(rate_limits)

    # Should fall back to defaults
    assert "adzuna" in rate_limits.RATE_LIMITS
    assert len(rate_limits.RATE_LIMITS["adzuna"]) == 2  # Default has 2 rates

    # Should log warning
    assert "must be a dict" in caplog.text


def test_rate_limits_config_override_merges_with_defaults(tmp_path, monkeypatch):
    """Test config overrides only specified backends, keeps defaults for others."""
    import json
    from job_radar import rate_limits

    monkeypatch.chdir(tmp_path)

    # Create config with override for adzuna only
    config_dir = tmp_path / ".job-radar"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({
        "rate_limits": {
            "adzuna": [{"limit": 300, "interval": 60}]
        }
    }))

    # Mock the config path
    monkeypatch.setenv("HOME", str(tmp_path))

    # Reload rate_limits module
    import importlib
    importlib.reload(rate_limits)

    # adzuna should use custom limit
    assert "adzuna" in rate_limits.RATE_LIMITS
    assert rate_limits.RATE_LIMITS["adzuna"][0].limit == 300

    # authentic_jobs should still use default
    assert "authentic_jobs" in rate_limits.RATE_LIMITS
    assert rate_limits.RATE_LIMITS["authentic_jobs"][0].limit == 60
