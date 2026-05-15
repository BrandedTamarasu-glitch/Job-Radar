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

    removed = cache.clear_cache()

    assert removed == 1
    assert not cached.exists()
    assert unrelated.exists()


def test_clear_cache_ignores_missing_cache_dir(tmp_path, monkeypatch):
    """clear_cache is safe when no cache directory exists yet."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)

    removed = cache.clear_cache()

    assert removed == 0
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


def test_fetch_with_retry_tracks_cache_hits_misses_and_writes(tmp_path, monkeypatch):
    """fetch_with_retry records cache counters for misses, writes, and hits."""
    data_dir = tmp_path / "data"
    calls = []

    class Response:
        text = "cached body"

        def raise_for_status(self):
            return None

    def fake_get(url, headers, timeout):
        calls.append(url)
        return Response()

    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.cache.requests.get", fake_get)
    cache.reset_cache_stats()

    first = cache.fetch_with_retry("https://example.com/jobs", headers={})
    second = cache.fetch_with_retry("https://example.com/jobs", headers={})

    assert first == "cached body"
    assert second == "cached body"
    assert calls == ["https://example.com/jobs"]
    assert cache.get_cache_stats() == {
        "hits": 1,
        "misses": 1,
        "writes": 1,
        "disabled": 0,
    }


def test_cache_entry_omits_raw_credential_bearing_url(tmp_path, monkeypatch):
    """Cached response metadata does not persist full API URLs with secrets."""
    data_dir = tmp_path / "data"

    class Response:
        text = "cached body"

        def raise_for_status(self):
            return None

    url = "https://example.com/jobs?app_key=secret-value&q=python"
    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.cache.requests.get", lambda *args, **kwargs: Response())

    assert cache.fetch_with_retry(url, headers={}) == "cached body"

    entry = json.loads(cache._cache_path(url).read_text(encoding="utf-8"))
    assert "url" not in entry
    assert entry["url_hash"]
    assert "secret-value" not in json.dumps(entry)


def test_redact_url_masks_credential_query_values():
    """Log-safe URLs retain shape without leaking key values."""
    redacted = cache._redact_url("https://example.com/jobs?app_key=secret&q=python&token=abc")

    assert "secret" not in redacted
    assert "abc" not in redacted
    assert "app_key=REDACTED" in redacted
    assert "token=REDACTED" in redacted
    assert "q=python" in redacted


def test_fetch_with_retry_tracks_disabled_cache_requests(monkeypatch):
    """fetch_with_retry records uncached requests when cache is disabled."""
    class Response:
        text = "live body"

        def raise_for_status(self):
            return None

    monkeypatch.setattr("job_radar.cache.requests.get", lambda *args, **kwargs: Response())
    cache.reset_cache_stats()

    assert cache.fetch_with_retry("https://example.com/jobs", headers={}, use_cache=False) == "live body"
    assert cache.get_cache_stats() == {
        "hits": 0,
        "misses": 0,
        "writes": 0,
        "disabled": 1,
    }


def test_fetch_with_retry_honors_custom_cache_ttl(tmp_path, monkeypatch):
    """fetch_with_retry treats cached entries as stale using caller-provided TTL."""
    data_dir = tmp_path / "data"
    calls = []

    class Response:
        text = "fresh body"

        def raise_for_status(self):
            return None

    def fake_get(url, headers, timeout):
        calls.append(url)
        return Response()

    monkeypatch.setattr("job_radar.cache.get_data_dir", lambda: data_dir)
    cache_path = cache._cache_path("https://example.com/jobs")
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps({"url": "https://example.com/jobs", "ts": 1000, "body": "old body"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("job_radar.cache.time.time", lambda: 1301)
    monkeypatch.setattr("job_radar.cache.requests.get", fake_get)
    cache.reset_cache_stats()

    body = cache.fetch_with_retry(
        "https://example.com/jobs",
        headers={},
        cache_ttl_seconds=300,
    )

    assert body == "fresh body"
    assert calls == ["https://example.com/jobs"]
    assert cache.get_cache_stats() == {
        "hits": 0,
        "misses": 1,
        "writes": 1,
        "disabled": 0,
    }
