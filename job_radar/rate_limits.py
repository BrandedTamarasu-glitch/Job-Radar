"""Rate limiting infrastructure with persistent SQLite backend.

Provides per-source rate limiters using pyrate-limiter with SQLiteBucket for
persistence across application restarts. Rate limits are configured per source
with conservative defaults to avoid 429 errors.
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

log = logging.getLogger(__name__)


# Rate limit configurations per source (conservative defaults)
RATE_LIMITS = {
    "adzuna": [
        Rate(100, Duration.MINUTE),
        Rate(1000, Duration.HOUR),
    ],
    "authentic_jobs": [
        Rate(60, Duration.MINUTE),
    ],
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

    Parameters
    ----------
    source : str
        Source name (e.g., "adzuna", "authentic_jobs")

    Returns
    -------
    Limiter
        Rate limiter instance with persistent SQLite backend
    """
    if source in _limiters:
        return _limiters[source]

    # Create .rate_limits/ directory
    rate_limits_dir = Path.cwd() / ".rate_limits"
    rate_limits_dir.mkdir(exist_ok=True)

    # Get rate configuration (with fallback default)
    rates = RATE_LIMITS.get(source, [Rate(60, Duration.MINUTE)])

    # Create SQLite database and connection
    # Use check_same_thread=False to allow background leaker thread access
    db_path = rate_limits_dir / f"{source}.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    _connections[source] = conn

    # Create table if it doesn't exist
    table_name = "rate_limits"
    create_query = SQLiteQueries.CREATE_BUCKET_TABLE.format(table=table_name)
    conn.execute(create_query)
    conn.commit()

    # Create bucket and limiter
    bucket = SQLiteBucket(rates, conn, table_name)
    factory = SingleBucketFactory(bucket)
    limiter = Limiter(factory)

    _limiters[source] = limiter
    log.debug(f"Initialized rate limiter for {source} with {len(rates)} rate(s)")

    return limiter


def check_rate_limit(source: str, verbose: bool = False) -> bool:
    """Check if request is within rate limit.

    Non-blocking check that returns immediately. If rate limited, logs warning
    with retry time in 12-hour format (e.g., "2:35pm").

    Parameters
    ----------
    source : str
        Source name (e.g., "adzuna", "authentic_jobs")
    verbose : bool, default False
        If True, log remaining calls and reset time

    Returns
    -------
    bool
        True if allowed (within rate limit), False if rate limited
    """
    limiter = get_rate_limiter(source)

    # Non-blocking acquire (skip immediately if rate limited)
    allowed = limiter.try_acquire(source, blocking=False)

    if not allowed:
        # Calculate retry time using the shortest configured rate
        rates = RATE_LIMITS.get(source, [Rate(60, Duration.MINUTE)])
        shortest_duration = min(r.interval for r in rates)
        reset_at = datetime.datetime.now() + datetime.timedelta(seconds=shortest_duration)
        reset_str = reset_at.strftime('%I:%M%p').lstrip('0').lower()

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
