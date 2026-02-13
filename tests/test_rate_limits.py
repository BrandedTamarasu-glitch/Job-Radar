"""Tests for rate_limits module covering rate limiter functionality."""

import pytest
from pathlib import Path
from job_radar.rate_limits import RATE_LIMITS, check_rate_limit, get_rate_limit_status


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
