"""HTTP response caching and retry logic for job fetchers."""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional

import requests

from .paths import get_data_dir

log = logging.getLogger(__name__)

_CACHE_MAX_AGE_SECONDS = 4 * 3600  # 4 hours


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


def fetch_with_retry(
    url: str,
    headers: dict,
    timeout: int = 15,
    retries: int = 3,
    backoff: float = 2.0,
    use_cache: bool = True,
) -> Optional[str]:
    """Fetch a URL with retry, backoff, and optional caching.

    Returns:
        Response body text, or None on failure.
    """
    if use_cache:
        cached = _read_cache(url)
        if cached is not None:
            return cached

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
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


def clear_cache():
    """Remove all cached responses."""
    cache_dir = get_cache_dir()
    if cache_dir.is_dir():
        for path in cache_dir.iterdir():
            if path.suffix == ".json":
                path.unlink()
        log.info("Cache cleared")
