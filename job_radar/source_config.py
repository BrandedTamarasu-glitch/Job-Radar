"""Configuration helpers for source fetching."""

import logging
import os
import re

log = logging.getLogger(__name__)


DEFAULT_MAX_WORKERS = 6
MAX_WORKERS_ENV = "JOB_RADAR_MAX_WORKERS"
DEFAULT_SLOW_QUERY_SECONDS = 8.0
SLOW_QUERY_ENV = "JOB_RADAR_SLOW_QUERY_SECONDS"
SOURCE_CACHE_TTL_ENV = "JOB_RADAR_SOURCE_CACHE_TTL_SECONDS"
SOURCE_CACHE_TTL_SOURCE_ENV_PREFIX = "JOB_RADAR_SOURCE_CACHE_TTL_"
SOURCE_CACHE_TTL_SECONDS = {
    "dice": 60 * 60,
    "hn_hiring": 6 * 3600,
    "remoteok": 2 * 3600,
    "weworkremotely": 2 * 3600,
    "adzuna": 2 * 3600,
    "authentic_jobs": 4 * 3600,
    "jsearch": 2 * 3600,
    "usajobs": 12 * 3600,
    "hiringcafe": 2 * 3600,
    "serpapi": 2 * 3600,
    "jobicy": 2 * 3600,
}


def resolve_max_workers(value: int | str | None = None) -> int:
    """Resolve fetch parallelism from an explicit value or environment."""
    raw_value = value if value is not None else os.environ.get(MAX_WORKERS_ENV)
    if raw_value in (None, ""):
        return DEFAULT_MAX_WORKERS

    try:
        workers = int(raw_value)
    except (TypeError, ValueError):
        log.warning(
            "%s must be a positive integer, got %r; using default %s",
            MAX_WORKERS_ENV,
            raw_value,
            DEFAULT_MAX_WORKERS,
        )
        return DEFAULT_MAX_WORKERS

    if workers < 1:
        log.warning(
            "%s must be at least 1, got %s; using default %s",
            MAX_WORKERS_ENV,
            workers,
            DEFAULT_MAX_WORKERS,
        )
        return DEFAULT_MAX_WORKERS

    return workers


def resolve_slow_query_threshold(value: int | float | str | None = None) -> float:
    """Resolve slow query warning threshold from explicit value or environment."""
    raw_value = value if value is not None else os.environ.get(SLOW_QUERY_ENV)
    if raw_value in (None, ""):
        return DEFAULT_SLOW_QUERY_SECONDS

    try:
        threshold = float(raw_value)
    except (TypeError, ValueError):
        log.warning(
            "%s must be a non-negative number, got %r; using default %.1f",
            SLOW_QUERY_ENV,
            raw_value,
            DEFAULT_SLOW_QUERY_SECONDS,
        )
        return DEFAULT_SLOW_QUERY_SECONDS

    if threshold < 0:
        log.warning(
            "%s must be non-negative, got %s; using default %.1f",
            SLOW_QUERY_ENV,
            threshold,
            DEFAULT_SLOW_QUERY_SECONDS,
        )
        return DEFAULT_SLOW_QUERY_SECONDS

    return threshold


def source_cache_ttl(source_key: str) -> int:
    """Return cache TTL seconds for a source key."""
    source_env = _source_cache_ttl_env_name(source_key)
    raw_value = os.environ.get(source_env) or os.environ.get(SOURCE_CACHE_TTL_ENV)
    fallback = SOURCE_CACHE_TTL_SECONDS.get(source_key, 4 * 3600)
    if raw_value in (None, ""):
        return fallback
    return _resolve_positive_int(
        raw_value,
        fallback=fallback,
        setting=source_env if os.environ.get(source_env) else SOURCE_CACHE_TTL_ENV,
    )


def _source_cache_ttl_env_name(source_key: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]+", "_", str(source_key).upper()).strip("_")
    return f"{SOURCE_CACHE_TTL_SOURCE_ENV_PREFIX}{normalized}_SECONDS"


def _resolve_positive_int(value, *, fallback: int, setting: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        log.warning("%s must be a positive integer, got %r; using default %s", setting, value, fallback)
        return fallback
    if parsed < 1:
        log.warning("%s must be at least 1, got %s; using default %s", setting, parsed, fallback)
        return fallback
    return parsed
