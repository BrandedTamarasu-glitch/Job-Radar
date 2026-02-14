"""Rate limiting infrastructure with persistent SQLite backend.

Provides per-source rate limiters using pyrate-limiter with SQLiteBucket for
persistence across application restarts. Rate limits are configured per source
with conservative defaults to avoid 429 errors.

Rate limits can be customized via config.json:

    {
      "rate_limits": {
        "adzuna": [{"limit": 200, "interval": 60}],
        "jsearch": [{"limit": 100, "interval": 60}, {"limit": 500, "interval": 3600}]
      }
    }

Where "limit" is the number of requests and "interval" is the time period in seconds.
Config overrides are merged with hardcoded defaults. Invalid configs show warnings
and fall back to defaults.
"""

import atexit
import datetime
import logging
import os
import sqlite3
from pathlib import Path

from pyrate_limiter import (
    Duration,
    Limiter,
    Rate,
    SingleBucketFactory,
    SQLiteBucket,
    SQLiteQueries,
)

from .config import load_config

log = logging.getLogger(__name__)


def _load_rate_limits() -> dict:
    """Load rate limits from config file with fallback to defaults.

    Config format in config.json:
    {
      "rate_limits": {
        "adzuna": [{"limit": 200, "interval": 60}],
        "jsearch": [{"limit": 100, "interval": 60}, {"limit": 500, "interval": 3600}]
      }
    }

    Returns dict mapping backend API names to Rate objects.
    """
    # Hardcoded defaults (conservative)
    defaults = {
        "adzuna": [Rate(100, Duration.MINUTE), Rate(1000, Duration.HOUR)],
        "authentic_jobs": [Rate(60, Duration.MINUTE)],
        "jsearch": [Rate(100, Duration.MINUTE)],      # 100 req/min (RapidAPI free tier)
        "usajobs": [Rate(60, Duration.MINUTE)],        # 60 req/min (conservative for gov API)
        "serpapi": [Rate(50, Duration.MINUTE)],        # Conservative for free tier (100 searches/month cap)
        "jobicy": [Rate(1, Duration.HOUR)],            # Per docs: "once per hour"
    }

    # Load config file
    config = load_config()
    config_limits = config.get("rate_limits", {})

    if not isinstance(config_limits, dict):
        log.warning("Config rate_limits must be a dict, got %s - using defaults", type(config_limits).__name__)
        return defaults

    # Merge config overrides with defaults
    result = defaults.copy()
    for backend_api, rate_configs in config_limits.items():
        if not isinstance(rate_configs, list):
            log.warning("Config rate_limits[%s] must be a list, got %s - skipping", backend_api, type(rate_configs).__name__)
            continue

        rates = []
        for rate_config in rate_configs:
            if not isinstance(rate_config, dict):
                log.warning("Config rate_limits[%s] entry must be a dict - skipping", backend_api)
                continue

            limit = rate_config.get("limit")
            interval = rate_config.get("interval")

            if not isinstance(limit, int) or limit <= 0:
                log.warning("Config rate_limits[%s] limit must be positive int - skipping", backend_api)
                continue

            if not isinstance(interval, (int, float)) or interval <= 0:
                log.warning("Config rate_limits[%s] interval must be positive number - skipping", backend_api)
                continue

            rates.append(Rate(limit, interval))

        if rates:
            result[backend_api] = rates
            log.debug("Loaded custom rate limits for %s: %d rate(s)", backend_api, len(rates))

    return result


# Rate limit configurations per source (conservative defaults)
RATE_LIMITS = _load_rate_limits()

# Map sources to backend APIs - sources sharing the same backend API share rate limiters
# This is critical for JSearch integration where multiple sources (linkedin, indeed,
# glassdoor) all use the same JSearch API and should share rate limits
BACKEND_API_MAP = {
    "adzuna": "adzuna",
    "authentic_jobs": "authentic_jobs",
    # JSearch aggregator — all sources share same rate limiter instance
    "linkedin": "jsearch",
    "indeed": "jsearch",
    "glassdoor": "jsearch",
    "jsearch_other": "jsearch",
    # USAJobs — single source
    "usajobs": "usajobs",
    # SerpAPI — single source
    "serpapi": "serpapi",
    # Jobicy — single source (no API key required, but rate limited)
    "jobicy": "jobicy",
}

# Cache limiters to avoid re-creating objects
_limiters: dict[str, Limiter] = {}
_connections: dict[str, sqlite3.Connection] = {}


def _cleanup_connections() -> None:
    """Close all SQLite connections on application exit.

    Registered with atexit to prevent "database is locked" errors on exit.
    Handles cleanup failures gracefully to avoid crashing during shutdown.

    CRITICAL: Must clear _limiters dict first to stop background threads
    before closing connections. pyrate-limiter runs background leak() threads
    that access the SQLite connections - closing connections while threads
    are active causes segmentation faults.
    """
    if not _connections and not _limiters:
        return

    # Step 1: Clear limiters to stop background threads
    # This prevents threads from accessing connections during cleanup
    _limiters.clear()

    # Step 2: Give threads time to finish their current operation
    # Background threads check for limiter existence before operations
    import time
    if _connections:
        time.sleep(0.1)  # 100ms should be sufficient for threads to exit

    # Step 3: Close connections
    closed_count = 0
    for source, conn in list(_connections.items()):
        try:
            conn.close()
            closed_count += 1
        except Exception as e:
            # Don't crash on cleanup failures - log and continue
            log.debug(f"Error closing rate limiter connection for {source}: {e}")

    if closed_count > 0:
        log.debug(f"Closed {closed_count} rate limiter database connections")

    _connections.clear()


# Register cleanup handler to run on application exit
atexit.register(_cleanup_connections)


def get_rate_limiter(source: str) -> Limiter:
    """Get or create a rate limiter for the given source.

    Creates .rate_limits/ directory and SQLite database for persistent state.
    Limiters are cached to avoid re-initialization.

    Sources sharing the same backend API (via BACKEND_API_MAP) will share
    the same rate limiter instance to prevent hitting API limits faster
    when multiple sources use the same backend.

    Parameters
    ----------
    source : str
        Source name (e.g., "adzuna", "authentic_jobs", "linkedin")

    Returns
    -------
    Limiter
        Rate limiter instance with persistent SQLite backend
    """
    # Look up backend API (fallback to source name if not mapped)
    backend_api = BACKEND_API_MAP.get(source, source)

    # Check if limiter already exists for this backend API
    if backend_api in _limiters:
        return _limiters[backend_api]

    # Create .rate_limits/ directory
    rate_limits_dir = Path.cwd() / ".rate_limits"
    rate_limits_dir.mkdir(exist_ok=True)

    # Get rate configuration using backend API name (with fallback default)
    rates = RATE_LIMITS.get(backend_api, [Rate(60, Duration.MINUTE)])

    # Create SQLite database and connection using backend API name
    # Use check_same_thread=False to allow background leaker thread access
    db_path = rate_limits_dir / f"{backend_api}.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    _connections[backend_api] = conn

    # Create table if it doesn't exist
    table_name = "rate_limits"
    create_query = SQLiteQueries.CREATE_BUCKET_TABLE.format(table=table_name)
    conn.execute(create_query)
    conn.commit()

    # Create bucket and limiter
    bucket = SQLiteBucket(rates, conn, table_name)
    factory = SingleBucketFactory(bucket)
    limiter = Limiter(factory)

    # Cache using backend API name (so multiple sources share the same limiter)
    _limiters[backend_api] = limiter
    log.debug(f"Initialized rate limiter for {source} (backend: {backend_api}) with {len(rates)} rate(s)")

    return limiter


def check_rate_limit(source: str, verbose: bool = False) -> bool:
    """Check if request is within rate limit.

    Non-blocking check that returns immediately. If rate limited, logs warning
    with retry time in 12-hour format (e.g., "2:35pm").

    Parameters
    ----------
    source : str
        Source name (e.g., "adzuna", "authentic_jobs", "linkedin")
    verbose : bool, default False
        If True, log remaining calls and reset time

    Returns
    -------
    bool
        True if allowed (within rate limit), False if rate limited
    """
    # Look up backend API to get correct rate configuration
    backend_api = BACKEND_API_MAP.get(source, source)
    limiter = get_rate_limiter(source)

    # Non-blocking acquire (skip immediately if rate limited)
    allowed = limiter.try_acquire(source, blocking=False)

    if not allowed:
        # Calculate retry time using the backend API's configured rate
        rates = RATE_LIMITS.get(backend_api, [Rate(60, Duration.MINUTE)])
        shortest_duration = min(r.interval for r in rates)
        reset_at = datetime.datetime.now() + datetime.timedelta(seconds=shortest_duration)
        reset_str = reset_at.strftime('%I:%M%p').lstrip('0').lower()

        # Keep user-facing message with source name (not backend API)
        log.warning(f"Skipped {source}: rate limited, retry after {reset_str}")
        return False

    if verbose:
        # Log remaining capacity (best-effort)
        log.debug(f"{source}: rate limit check passed")

    return True


def get_rate_limit_status(source: str) -> dict:
    """Get rate limit status for debugging.

    Returns dictionary with remaining capacity, reset time, and configured rate.
    This is best-effort and may return "unknown" for fields that can't be
    determined without hitting the rate limit.

    Parameters
    ----------
    source : str
        Source name (e.g., "adzuna", "authentic_jobs")

    Returns
    -------
    dict
        Status dict with keys: remaining, reset_time, configured_rate
    """
    rates = RATE_LIMITS.get(source, [Rate(60, Duration.MINUTE)])

    # Format configured rate for display
    rate_strs = []
    for r in rates:
        if r.interval == Duration.MINUTE:
            rate_strs.append(f"{r.limit}/min")
        elif r.interval == Duration.HOUR:
            rate_strs.append(f"{r.limit}/hour")
        elif r.interval == Duration.DAY:
            rate_strs.append(f"{r.limit}/day")
        else:
            rate_strs.append(f"{r.limit}/{r.interval}s")

    configured_rate = ", ".join(rate_strs)

    # Try to get remaining capacity
    # Note: pyrate-limiter v4 doesn't expose remaining count easily
    # We would need to track puts manually or query the SQLite bucket directly
    return {
        "remaining": "unknown",
        "reset_time": None,
        "configured_rate": configured_rate,
    }


def get_quota_usage(source: str) -> tuple[int, int, str] | None:
    """Get current quota usage for a rate-limited source.

    Queries the pyrate-limiter SQLite bucket table directly to count
    items within the current rate window. Returns (used, limit, period)
    tuple or None if quota info is not available.

    Parameters
    ----------
    source : str
        Source name (e.g., "serpapi", "jsearch", "adzuna")

    Returns
    -------
    tuple[int, int, str] | None
        (used_count, limit, period_label) or None if not available.
        period_label is one of "minute", "hour", "day", or "{N}s".
    """
    import time

    backend_api = BACKEND_API_MAP.get(source, source)

    # Get rate configuration
    rates = RATE_LIMITS.get(backend_api)
    if not rates:
        return None

    # Get SQLite connection (must already be initialized)
    conn = _connections.get(backend_api)
    if not conn:
        return None

    # Use the shortest rate window for display (most relevant for quota)
    shortest_rate = min(rates, key=lambda r: r.interval)
    limit = shortest_rate.limit
    interval_seconds = shortest_rate.interval

    # Calculate current window start
    now = time.time()
    window_start = now - interval_seconds

    try:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM rate_limits WHERE created_at >= ?",
            (window_start,)
        )
        used = cursor.fetchone()[0]

        # Format period label
        if interval_seconds <= 60:
            period = "minute"
        elif interval_seconds <= 3600:
            period = "hour"
        elif interval_seconds <= 86400:
            period = "day"
        else:
            period = f"{int(interval_seconds)}s"

        return (used, limit, period)
    except Exception as e:
        log.debug("Could not get quota for %s: %s", source, e)
        return None
