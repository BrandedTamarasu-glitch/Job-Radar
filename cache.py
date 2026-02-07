"""HTTP response caching and retry logic for job fetchers."""

import hashlib
import json
import logging
import os
import time
from typing import Optional

import requests

log = logging.getLogger(__name__)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CACHE_DIR = os.path.join(_SCRIPT_DIR, ".cache")
_CACHE_MAX_AGE_SECONDS = 4 * 3600  # 4 hours


def _cache_path(url: str) -> str:
    """Return a filesystem-safe cache path for a URL."""
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"{url_hash}.json")


def _read_cache(url: str) -> Optional[str]:
    """Read cached response if it exists and is fresh."""
    path = _cache_path(url)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            entry = json.load(f)
        if time.time() - entry["ts"] > _CACHE_MAX_AGE_SECONDS:
            os.remove(path)
            return None
        log.debug("Cache hit: %s", url[:80])
        return entry["body"]
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def _write_cache(url: str, body: str):
    """Write a response to cache."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    path = _cache_path(url)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"url": url, "ts": time.time(), "body": body}, f)
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
    if os.path.isdir(_CACHE_DIR):
        for f in os.listdir(_CACHE_DIR):
            path = os.path.join(_CACHE_DIR, f)
            if f.endswith(".json"):
                os.remove(path)
        log.info("Cache cleared")
