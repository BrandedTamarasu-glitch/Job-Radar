"""Tests for source fetching configuration helpers."""

from job_radar.source_config import (
    resolve_max_workers,
    resolve_slow_query_threshold,
    source_cache_ttl,
)


def test_resolve_max_workers_prefers_explicit_value(monkeypatch):
    monkeypatch.setenv("JOB_RADAR_MAX_WORKERS", "9")

    assert resolve_max_workers("3") == 3


def test_resolve_slow_query_threshold_reads_environment(monkeypatch):
    monkeypatch.setenv("JOB_RADAR_SLOW_QUERY_SECONDS", "2.5")

    assert resolve_slow_query_threshold() == 2.5


def test_source_cache_ttl_source_override_beats_global(monkeypatch):
    monkeypatch.setenv("JOB_RADAR_SOURCE_CACHE_TTL_SECONDS", "600")
    monkeypatch.setenv("JOB_RADAR_SOURCE_CACHE_TTL_USAJOBS_SECONDS", "1800")

    assert source_cache_ttl("usajobs") == 1800
    assert source_cache_ttl("dice") == 600


def test_source_cache_ttl_normalizes_source_key_for_override(monkeypatch):
    monkeypatch.setenv("JOB_RADAR_SOURCE_CACHE_TTL_FOO_BAR_SECONDS", "120")

    assert source_cache_ttl("foo-bar") == 120
