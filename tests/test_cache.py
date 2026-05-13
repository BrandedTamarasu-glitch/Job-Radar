"""HTTP cache path and lifecycle tests."""

import json

from job_radar import cache


def test_cache_dir_uses_app_data_dir(tmp_path, monkeypatch):
    """HTTP cache lives under app data, not the current working directory."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)

    assert cache.get_cache_dir() == data_dir / "cache"
    assert cache._cache_path("https://example.com").parent == data_dir / "cache"


def test_clear_cache_removes_only_json_cache_files(tmp_path, monkeypatch):
    """clear_cache removes cached responses and leaves unrelated files alone."""
    data_dir = tmp_path / "data"
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(parents=True)
    cached = cache_dir / "response.json"
    unrelated = cache_dir / "notes.txt"
    cached.write_text("{}", encoding="utf-8")
    unrelated.write_text("keep", encoding="utf-8")
    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)

    cache.clear_cache()

    assert not cached.exists()
    assert unrelated.exists()


def test_clear_cache_ignores_missing_cache_dir(tmp_path, monkeypatch):
    """clear_cache is safe when no cache directory exists yet."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)

    cache.clear_cache()

    assert not (data_dir / "cache").exists()


def test_prune_stale_cache_removes_only_stale_json_files(tmp_path, monkeypatch):
    """prune_stale_cache removes stale cache entries and keeps fresh/unrelated files."""
    data_dir = tmp_path / "data"
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(parents=True)
    stale = cache_dir / "stale.json"
    fresh = cache_dir / "fresh.json"
    unrelated = cache_dir / "notes.txt"
    stale.write_text(json.dumps({"ts": 1000, "body": "old"}), encoding="utf-8")
    fresh.write_text(json.dumps({"ts": 10_000, "body": "new"}), encoding="utf-8")
    unrelated.write_text("keep", encoding="utf-8")
    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)

    pruned = cache.prune_stale_cache(max_age_seconds=3600, now=10_000)

    assert pruned == 1
    assert not stale.exists()
    assert fresh.exists()
    assert unrelated.exists()


def test_prune_stale_cache_removes_unreadable_json_files(tmp_path, monkeypatch):
    """prune_stale_cache removes corrupt JSON cache entries."""
    data_dir = tmp_path / "data"
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(parents=True)
    corrupt = cache_dir / "corrupt.json"
    corrupt.write_text("{", encoding="utf-8")
    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)

    pruned = cache.prune_stale_cache(now=10_000)

    assert pruned == 1
    assert not corrupt.exists()


def test_maybe_prune_stale_cache_respects_maintenance_interval(monkeypatch):
    """The maintenance hook avoids scanning on every cached request."""
    calls = []
    monkeypatch.setattr("job_radar.cache._LAST_CACHE_MAINTENANCE", 0.0)
    monkeypatch.setattr(
        "job_radar.cache.prune_stale_cache",
        lambda now: calls.append(now) or 2,
    )

    assert cache._maybe_prune_stale_cache(now=3600) == 2
    assert cache._maybe_prune_stale_cache(now=3601) == 0
    assert cache._maybe_prune_stale_cache(now=7200) == 2
    assert calls == [3600, 7200]


def test_resolve_request_timeout_defaults_without_env(monkeypatch):
    """Request timeout preserves the historical default."""
    monkeypatch.delenv("JOB_RADAR_REQUEST_TIMEOUT", raising=False)

    assert cache.resolve_request_timeout() == 15.0


def test_resolve_request_timeout_accepts_explicit_value():
    """Explicit timeout values are accepted for source-specific calls."""
    assert cache.resolve_request_timeout(8) == 8.0
    assert cache.resolve_request_timeout("2.5") == 2.5


def test_resolve_request_timeout_reads_environment(monkeypatch):
    """Users can tune default request timeout with an environment variable."""
    monkeypatch.setenv("JOB_RADAR_REQUEST_TIMEOUT", "6.5")

    assert cache.resolve_request_timeout() == 6.5


def test_resolve_request_timeout_falls_back_for_invalid_values(monkeypatch):
    """Invalid timeout settings fall back instead of crashing fetches."""
    assert cache.resolve_request_timeout("not-a-number") == 15.0
    assert cache.resolve_request_timeout(0) == 15.0

    monkeypatch.setenv("JOB_RADAR_REQUEST_TIMEOUT", "-1")
    assert cache.resolve_request_timeout() == 15.0


def test_fetch_with_retry_uses_resolved_timeout(monkeypatch):
    """fetch_with_retry passes the resolved timeout to requests."""
    calls = []

    class Response:
        text = "ok"

        def raise_for_status(self):
            return None

    def fake_get(url, headers, timeout):
        calls.append(timeout)
        return Response()

    monkeypatch.setenv("JOB_RADAR_REQUEST_TIMEOUT", "4")
    monkeypatch.setattr("job_radar.cache.requests.get", fake_get)

    assert cache.fetch_with_retry("https://example.com", headers={}, use_cache=False) == "ok"
    assert calls == [4.0]
