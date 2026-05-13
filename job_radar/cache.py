"""HTTP response caching and retry logic for job fetchers."""

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

from .paths import get_data_dir

log = logging.getLogger(__name__)

_CACHE_MAX_AGE_SECONDS = 4 * 3600  # 4 hours
DEFAULT_REQUEST_TIMEOUT = 15.0
REQUEST_TIMEOUT_ENV = "JOB_RADAR_REQUEST_TIMEOUT"
CACHE_MAINTENANCE_INTERVAL_SECONDS = 3600
_LAST_CACHE_MAINTENANCE = 0.0


def resolve_request_timeout(value: int | float | str | None = None) -> float:
    """Resolve HTTP request timeout from explicit value or environment."""
    raw_value = value if value is not None else os.environ.get(REQUEST_TIMEOUT_ENV)
    if raw_value in (None, ""):
        return DEFAULT_REQUEST_TIMEOUT

    try:
        timeout = float(raw_value)
    except (TypeError, ValueError):
        log.warning(
            "%s must be a positive number, got %r; using default %.1f",
            REQUEST_TIMEOUT_ENV,
            raw_value,
            DEFAULT_REQUEST_TIMEOUT,
        )
        return DEFAULT_REQUEST_TIMEOUT

    if timeout <= 0:
        log.warning(
            "%s must be greater than 0, got %s; using default %.1f",
            REQUEST_TIMEOUT_ENV,
            timeout,
            DEFAULT_REQUEST_TIMEOUT,
        )
        return DEFAULT_REQUEST_TIMEOUT

    return timeout


def get_cache_dir() -> Path:
    """Return the platform-specific HTTP cache directory."""
    return get_data_dir() / "cache"


def _cache_path(url: str) -> Path:
    """Return a filesystem-safe cache path for a URL."""
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return get_cache_dir() / f"{url_hash}.json"


def _read_cache(url: str) -> Optional[str]:
    """Read cached response if it exists and is fresh."""
    path = _cache_path(url)
    if not path.exists():
        return None
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - entry["ts"] > _CACHE_MAX_AGE_SECONDS:
            path.unlink()
            return None
        log.debug("Cache hit: %s", url[:80])
        return entry["body"]
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def _write_cache(url: str, body: str):
    """Write a response to cache."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(url)
    try:
        path.write_text(
            json.dumps({"url": url, "ts": time.time(), "body": body}),
            encoding="utf-8",
        )
    except OSError as e:
        log.debug("Cache write failed: %s", e)


def prune_stale_cache(
    *,
    max_age_seconds: int | float = _CACHE_MAX_AGE_SECONDS,
    now: float | None = None,
) -> int:
    """Remove stale or unreadable cached response files."""
    cache_dir = get_cache_dir()
    if not cache_dir.is_dir():
        return 0

    current_time = time.time() if now is None else now
    pruned = 0

    for path in cache_dir.glob("*.json"):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
            timestamp = float(entry["ts"])
            should_prune = current_time - timestamp > max_age_seconds
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            should_prune = True

        if should_prune:
            try:
                path.unlink()
                pruned += 1
            except OSError as e:
                log.debug("Cache prune failed for %s: %s", path, e)

    if pruned:
        log.info("Pruned %d stale cache file(s)", pruned)
    return pruned


def _maybe_prune_stale_cache(now: float | None = None) -> int:
    """Run cache pruning at most once per maintenance interval."""
    global _LAST_CACHE_MAINTENANCE

    current_time = time.time() if now is None else now
    if current_time - _LAST_CACHE_MAINTENANCE < CACHE_MAINTENANCE_INTERVAL_SECONDS:
        return 0

    _LAST_CACHE_MAINTENANCE = current_time
    return prune_stale_cache(now=current_time)


def fetch_with_retry(
    url: str,
    headers: dict,
    timeout: int | float | str | None = None,
    retries: int = 3,
    backoff: float = 2.0,
    use_cache: bool = True,
) -> Optional[str]:
    """Fetch a URL with retry, backoff, and optional caching.

    Returns:
        Response body text, or None on failure.
    """
    request_timeout = resolve_request_timeout(timeout)

    if use_cache:
        _maybe_prune_stale_cache()
        cached = _read_cache(url)
        if cached is not None:
            return cached

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=request_timeout)
            resp.raise_for_status()
            body = resp.text
            if use_cache:
                _write_cache(url, body)
            return body
        except requests.RequestException as e:
            last_error = e
            if attempt < retries:
                wait = backoff ** attempt
                log.warning(
                    "Fetch attempt %d/%d failed for %s: %s (retry in %.1fs)",
                    attempt, retries, url[:80], e, wait,
                )
                time.sleep(wait)
            else:
                log.error("All %d fetch attempts failed for %s: %s", retries, url[:80], e)

    return None


def clear_cache() -> int:
    """Remove all cached responses and return the number of files removed."""
    cache_dir = get_cache_dir()
    removed = 0
    if cache_dir.is_dir():
        for path in cache_dir.iterdir():
            if path.suffix == ".json":
                path.unlink()
                removed += 1
        log.info("Cache cleared (%d file(s) removed)", removed)
    return removed
