"""HTTP cache path and lifecycle tests."""

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
