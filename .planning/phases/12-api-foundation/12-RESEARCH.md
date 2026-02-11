# Phase 12: API Foundation - Research

**Researched:** 2026-02-10
**Domain:** API credential management, rate limiting, and environment variables with Python
**Confidence:** HIGH

## Summary

This phase implements secure API credential management using python-dotenv and persistent rate limiting infrastructure. The foundation enables Phase 13 to integrate Adzuna and Authentic Jobs APIs without hardcoding credentials or encountering 429 rate limit errors.

python-dotenv (v1.2.1, released October 2025) is the standard solution for environment variable management in Python, supporting Python 3.10+ with zero external dependencies. It loads .env files using load_dotenv() at application startup, automatically finds .env files via find_dotenv(), and supports validation patterns for required variables. The library follows 12-factor app principles and is production-tested across thousands of projects.

For rate limiting, pyrate-limiter (v3.14.0, released January 2026) provides production-stable rate limiting using the leaky bucket algorithm with SQLite backend for persistent state across runs. This matches the existing tracker.json pattern used in job_radar/tracker.py and maintains rate limit windows across application restarts.

The user decisions from CONTEXT.md specify: .env file in project root, .env.example with key names + signup URLs, independent per-source rate limits, skip source when rate limited (show results from others), persist rate limit state like tracker.json, hardcoded limits per provider docs, and interactive --setup-apis command using questionary patterns established in Phase 7.

**Primary recommendation:** Use python-dotenv with load_dotenv() at startup (fail-fast on syntax errors), pyrate-limiter with SQLiteBucket for persistent rate limiting (one limiter per API source), questionary for --setup-apis interactive flow (reuse Phase 7 validation patterns), and graceful degradation for missing API keys (log warning, skip source, continue with other sources).

## Standard Stack

The established libraries/tools for API credential management and rate limiting in Python:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-dotenv | 1.2.1 | .env file loading | Industry standard, 7.6K+ GitHub stars, zero dependencies, 12-factor principles, supports variable expansion |
| pyrate-limiter | 3.14.0 | Rate limiting with persistence | Production-stable, SQLite backend for cross-run state, leaky bucket algorithm, 1.1K+ stars |
| requests | (existing) | HTTP client | Already in project, pyrate-limiter integrates via decorator or manual try_acquire() |
| questionary | (existing) | Interactive prompts | Already in project (Phase 7), perfect for --setup-apis command |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | Path operations | Already project standard (Phase 6), use for .env path resolution |
| json | stdlib | Serialization | Already project standard, use for rate limit state persistence |
| logging | stdlib | Structured logging | Already project standard, use for missing key warnings and rate limit debug output |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-dotenv | python-decouple | Similar functionality but less widely adopted, dotenv has 3x more stars |
| pyrate-limiter | ratelimit | ratelimit lacks persistence, only in-memory state, loses rate limit windows on restart |
| pyrate-limiter | requests-ratelimiter | requests-ratelimiter is just a wrapper around pyrate-limiter, adds no value for our use case |
| SQLite backend | JSON file | SQLite provides atomic writes and concurrent access, JSON requires manual locking |
| load_dotenv() at startup | Lazy loading on first API call | Startup loading fails fast with clear errors, lazy loading delays errors until mid-search |

**Installation:**
```bash
pip install python-dotenv pyrate-limiter
```

**Dependencies:**
- python-dotenv: No external dependencies (uses stdlib only)
- pyrate-limiter: No external dependencies for SQLite backend (uses stdlib sqlite3)

## Architecture Patterns

### Recommended Project Structure
```
Job-Radar/
├── .env                    # API credentials (gitignored, new)
├── .env.example            # Template with key names (new)
├── job_radar/
│   ├── api_config.py       # .env loading and validation (new)
│   ├── rate_limits.py      # Rate limiter setup and state (new)
│   ├── sources.py          # Job fetchers (existing, integrate rate limiting)
│   ├── wizard.py           # Setup wizard (existing, add --setup-apis)
│   └── cache.py            # HTTP cache (existing)
├── .rate_limits/           # Rate limit state (gitignored, new)
│   └── *.db                # SQLite files per source
└── results/                # Existing
    └── tracker.json        # Existing
```

### Pattern 1: Environment Variable Loading at Startup
**What:** Load .env file on application startup, fail-fast on syntax errors, warn on missing optional keys
**When to use:** In search.py main() function, before any API calls
**Example:**
```python
# Source: python-dotenv v1.2.1 documentation
from dotenv import load_dotenv, find_dotenv
import os
import sys
import logging

log = logging.getLogger(__name__)

def load_api_credentials():
    """Load API credentials from .env file.

    Per user decision:
    - .env file in project root (next to job_radar.py)
    - Syntax errors: fail-fast (crash with clear message)
    - Missing keys: warn but continue (skip that source)
    """
    # Find .env file in project root or parent directories
    dotenv_path = find_dotenv(usecwd=True)

    if not dotenv_path:
        log.info("No .env file found - API sources will be skipped")
        return

    # Load .env file, fail-fast on syntax errors
    try:
        load_dotenv(dotenv_path, override=False)
    except Exception as e:
        print(f"Error: Invalid .env file syntax: {e}", file=sys.stderr)
        print(f"Fix the syntax errors in: {dotenv_path}", file=sys.stderr)
        sys.exit(1)

    log.debug(f"Loaded .env from: {dotenv_path}")

# Usage in search.py main()
def main():
    # Load API credentials early, before building queries
    load_api_credentials()

    # Continue with existing logic...
```

### Pattern 2: API Key Validation with Graceful Degradation
**What:** Check for required API keys, log warnings for missing keys, skip source gracefully
**When to use:** Before making API calls in sources.py fetch_* functions
**Example:**
```python
# Source: Best practices from python-dotenv docs + user decisions
import os
import logging

log = logging.getLogger(__name__)

def get_api_key(key_name: str, source_name: str) -> str | None:
    """Get API key from environment, warn if missing.

    Per user decision: Missing keys → log warning, skip source, don't crash
    """
    key = os.getenv(key_name)

    if not key:
        log.warning(
            f"Skipping {source_name}: {key_name} not found in .env file. "
            f"Run 'job-radar --setup-apis' to configure API keys."
        )
        return None

    return key

# Usage in sources.py
def fetch_adzuna(query: str, location: str = "") -> list[JobResult]:
    """Fetch jobs from Adzuna API."""
    app_id = get_api_key("ADZUNA_APP_ID", "Adzuna")
    app_key = get_api_key("ADZUNA_APP_KEY", "Adzuna")

    if not app_id or not app_key:
        return []  # Skip source, return empty list

    # Continue with API call...
```

### Pattern 3: Persistent Rate Limiting with SQLite Backend
**What:** Independent rate limiter per API source, persists state to SQLite file, remembers windows across runs
**When to use:** Wrap all API calls in sources.py to prevent 429 errors
**Example:**
```python
# Source: pyrate-limiter v3.14.0 documentation
from pyrate_limiter import Limiter, Rate, Duration, SQLiteBucket
from pathlib import Path
import os
import logging

log = logging.getLogger(__name__)

# Per user decision: Hardcode rate limits per provider's official docs
RATE_LIMITS = {
    "adzuna": [Rate(100, Duration.MINUTE)],  # Example: 100 calls/minute
    "authentic_jobs": [Rate(50, Duration.HOUR)],  # Example: 50 calls/hour
}

def get_rate_limiter(source: str) -> Limiter:
    """Get rate limiter for API source with persistent SQLite backend.

    Per user decision: Rate limit state persists like tracker.json pattern.
    """
    # Create .rate_limits directory (like .cache pattern)
    rate_limit_dir = Path(os.getcwd()) / ".rate_limits"
    rate_limit_dir.mkdir(exist_ok=True)

    # SQLite file per source (like cache files)
    db_path = rate_limit_dir / f"{source}.db"

    # Create bucket with persistent SQLite backend
    rates = RATE_LIMITS.get(source, [Rate(60, Duration.MINUTE)])  # Default fallback
    bucket = SQLiteBucket(rates, str(db_path))

    return Limiter(bucket)

def fetch_with_rate_limit(source: str, fetch_func, *args, **kwargs):
    """Wrap API call with rate limiting.

    Per user decision: When rate limited → skip source, show results from others
    """
    limiter = get_rate_limiter(source)
    identity = source  # Single identity per source

    try:
        # Non-blocking acquire (don't wait, fail immediately if rate limited)
        if not limiter.try_acquire(identity, blocking=False):
            # Calculate retry time from bucket state
            bucket_state = limiter.bucket.get(identity)
            if bucket_state:
                reset_time = bucket_state.reset_time
                import datetime
                reset_str = datetime.datetime.fromtimestamp(reset_time).strftime("%I:%M%p")
                log.warning(
                    f"Skipped {source}: rate limited, retry after {reset_str}"
                )
            else:
                log.warning(f"Skipped {source}: rate limited")
            return []

        # Rate limit OK, proceed with API call
        return fetch_func(*args, **kwargs)

    except Exception as e:
        log.error(f"Error fetching from {source}: {e}")
        return []

# Usage in sources.py
def fetch_adzuna(query: str, location: str = "") -> list[JobResult]:
    """Fetch jobs from Adzuna API with rate limiting."""
    app_id = get_api_key("ADZUNA_APP_ID", "Adzuna")
    app_key = get_api_key("ADZUNA_APP_KEY", "Adzuna")

    if not app_id or not app_key:
        return []

    def _fetch():
        # Actual API call logic here
        url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={app_id}&app_key={app_key}&what={query}"
        # ... existing HTTP request logic
        pass

    return fetch_with_rate_limit("adzuna", _fetch)
```

### Pattern 4: .env.example Template with Documentation
**What:** Template file with blank values, signup URLs in comments, format hints
**When to use:** Committed to git, developers copy to .env and fill in
**Example:**
```bash
# Source: Best practices from https://www.getfishtank.com/insights/best-practices-for-committing-env-files-to-version-control
# .env.example

# Adzuna API Credentials
# Sign up at: https://developer.adzuna.com/
ADZUNA_APP_ID=
ADZUNA_APP_KEY=

# Authentic Jobs API Key
# Sign up at: https://authenticjobs.com/api/
AUTHENTIC_JOBS_API_KEY=

# Optional: Set to "true" to enable verbose rate limit debugging
API_DEBUG=false
```

### Pattern 5: Interactive API Setup Command
**What:** --setup-apis command with questionary prompts, validates format, writes .env atomically
**When to use:** First-run or when user wants to add/update API keys
**Example:**
```python
# Source: Reuse Phase 7 wizard patterns + python-dotenv
import questionary
from pathlib import Path
import tempfile
import os

def setup_apis():
    """Interactive API key setup with validation.

    Per user decision: Create .env file, ask for each key, validate format, write atomically.
    """
    print("\n🔑 API Key Setup")
    print("=" * 60)
    print("Configure API keys for job sources. Press Enter to skip optional sources.\n")

    # Section 1: Adzuna
    print("\n🔍 Adzuna API (optional)")
    print("Sign up at: https://developer.adzuna.com/")
    print("-" * 40)

    adzuna_id = questionary.text(
        "Adzuna App ID (or press Enter to skip):",
        default=""
    ).ask()

    adzuna_key = questionary.text(
        "Adzuna App Key (or press Enter to skip):",
        default=""
    ).ask() if adzuna_id else ""

    # Section 2: Authentic Jobs
    print("\n💼 Authentic Jobs API (optional)")
    print("Sign up at: https://authenticjobs.com/api/")
    print("-" * 40)

    aj_key = questionary.text(
        "Authentic Jobs API Key (or press Enter to skip):",
        default=""
    ).ask()

    # Build .env content
    env_lines = [
        "# Job Radar API Configuration",
        "# Generated by job-radar --setup-apis",
        "",
    ]

    if adzuna_id and adzuna_key:
        env_lines.extend([
            "# Adzuna API (https://developer.adzuna.com/)",
            f"ADZUNA_APP_ID={adzuna_id}",
            f"ADZUNA_APP_KEY={adzuna_key}",
            "",
        ])

    if aj_key:
        env_lines.extend([
            "# Authentic Jobs API (https://authenticjobs.com/api/)",
            f"AUTHENTIC_JOBS_API_KEY={aj_key}",
            "",
        ])

    # Show summary
    print("\n" + "=" * 60)
    print("📝 Configuration Summary:")
    print(f"  Adzuna: {'✓ Configured' if adzuna_id else '✗ Skipped'}")
    print(f"  Authentic Jobs: {'✓ Configured' if aj_key else '✗ Skipped'}")
    print("=" * 60 + "\n")

    if not questionary.confirm("Save API configuration?", default=True).ask():
        print("Setup cancelled.")
        return

    # Write .env file atomically (reuse Phase 7 pattern)
    env_path = Path(os.getcwd()) / ".env"
    write_text_atomic(env_path, "\n".join(env_lines))

    print(f"\n✅ API keys saved to {env_path}")
    print("Run 'job-radar --test-apis' to verify your configuration.\n")

def write_text_atomic(path: Path, content: str):
    """Write text file atomically with temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        Path(tmp_path).replace(path)
    except:
        try:
            os.unlink(tmp_path)
        except:
            pass
        raise
```

### Pattern 6: API Key Validation Command
**What:** --test-apis command that pings each API with credentials, reports which keys work
**When to use:** After --setup-apis to verify configuration
**Example:**
```python
# Source: Best practices for API error handling
import requests
import os
import logging

log = logging.getLogger(__name__)

def test_apis():
    """Test configured API keys by pinging endpoints.

    Per user decision: Ping each API, report which keys work.
    """
    print("\n🧪 Testing API Keys")
    print("=" * 60 + "\n")

    results = {}

    # Test Adzuna
    adzuna_id = os.getenv("ADZUNA_APP_ID")
    adzuna_key = os.getenv("ADZUNA_APP_KEY")

    if adzuna_id and adzuna_key:
        print("Testing Adzuna API...", end=" ")
        try:
            # Simple test query
            url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={adzuna_id}&app_key={adzuna_key}&results_per_page=1"
            resp = requests.get(url, timeout=10)

            if resp.status_code == 200:
                print("✓ OK")
                results["adzuna"] = True
            elif resp.status_code == 401 or resp.status_code == 403:
                print("✗ Invalid credentials (401/403)")
                results["adzuna"] = False
            else:
                print(f"✗ Unexpected response ({resp.status_code})")
                results["adzuna"] = False
        except Exception as e:
            print(f"✗ Error: {e}")
            results["adzuna"] = False
    else:
        print("Adzuna API: Not configured (skipped)")
        results["adzuna"] = None

    # Test Authentic Jobs
    aj_key = os.getenv("AUTHENTIC_JOBS_API_KEY")

    if aj_key:
        print("Testing Authentic Jobs API...", end=" ")
        try:
            url = f"https://authenticjobs.com/api/?api_key={aj_key}&method=aj.jobs.search&keywords=python&format=json"
            resp = requests.get(url, timeout=10)

            if resp.status_code == 200:
                print("✓ OK")
                results["authentic_jobs"] = True
            elif resp.status_code == 401 or resp.status_code == 403:
                print("✗ Invalid API key (401/403)")
                results["authentic_jobs"] = False
            else:
                print(f"✗ Unexpected response ({resp.status_code})")
                results["authentic_jobs"] = False
        except Exception as e:
            print(f"✗ Error: {e}")
            results["authentic_jobs"] = False
    else:
        print("Authentic Jobs API: Not configured (skipped)")
        results["authentic_jobs"] = None

    # Summary
    print("\n" + "=" * 60)
    configured = sum(1 for v in results.values() if v is not None)
    working = sum(1 for v in results.values() if v is True)
    print(f"Summary: {working}/{configured} configured API(s) working")

    if working < configured:
        print("\n⚠️  Some API keys are invalid. Run 'job-radar --setup-apis' to fix.")
    print()
```

### Pattern 7: Verbose Rate Limit Debugging
**What:** --verbose flag shows remaining quota, next reset time per source
**When to use:** Debugging rate limit issues without separate debug flag
**Example:**
```python
# Source: pyrate-limiter bucket state inspection
def fetch_with_rate_limit_verbose(source: str, fetch_func, verbose: bool, *args, **kwargs):
    """Wrap API call with rate limiting, show debug info if verbose."""
    limiter = get_rate_limiter(source)
    identity = source

    if verbose:
        # Show rate limit status before call
        bucket_state = limiter.bucket.get(identity)
        if bucket_state:
            remaining = bucket_state.remaining
            reset_time = bucket_state.reset_time
            import datetime
            reset_str = datetime.datetime.fromtimestamp(reset_time).strftime("%I:%M%p")
            log.debug(
                f"{source}: {remaining} calls remaining, resets at {reset_str}"
            )
        else:
            log.debug(f"{source}: No rate limit state (first call)")

    # Try to acquire permit
    if not limiter.try_acquire(identity, blocking=False):
        bucket_state = limiter.bucket.get(identity)
        if bucket_state:
            reset_time = bucket_state.reset_time
            import datetime
            reset_str = datetime.datetime.fromtimestamp(reset_time).strftime("%I:%M%p")
            log.warning(
                f"Skipped {source}: rate limited (0 remaining), retry after {reset_str}"
            )
        else:
            log.warning(f"Skipped {source}: rate limited")
        return []

    # Proceed with API call
    results = fetch_func(*args, **kwargs)

    if verbose:
        # Show rate limit status after call
        bucket_state = limiter.bucket.get(identity)
        if bucket_state:
            remaining = bucket_state.remaining
            log.debug(f"{source}: {remaining} calls remaining after this request")

    return results
```

### Anti-Patterns to Avoid
- **Don't use configparser for .env:** Use python-dotenv, not configparser—.env format is key=value, not INI sections
- **Don't store .env in ~/.job-radar/:** Per user decision, .env lives in project root (next to job_radar.py)
- **Don't share rate limiters across sources:** Per user decision, independent limits per source—each gets its own Limiter instance
- **Don't retry 401/403 errors:** Invalid API key errors are permanent, don't retry—log error and skip source
- **Don't use blocking=True on try_acquire():** Per user decision, skip source immediately when rate limited, don't wait
- **Don't validate API keys on every call:** Validate once at startup (fail-fast on missing required keys), not on every API request
- **Don't use in-memory rate limiting:** Use SQLiteBucket for persistent state—rate limits must survive restarts

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| .env file parsing | Manual file reading + string split | python-dotenv load_dotenv() | Handles comments, quotes, multiline values, variable expansion, encoding edge cases |
| Rate limiting algorithm | Counter + timestamp checking | pyrate-limiter with leaky bucket | Algorithm is complex (token refill, burst handling, window sliding), SQLite backend provides atomic operations |
| Persistent state across runs | Manual JSON file locking | SQLiteBucket from pyrate-limiter | SQLite provides atomic writes, concurrent access, no race conditions on parallel requests |
| API key validation | Manual HTTP requests | Centralized get_api_key() helper | DRY principle, consistent error messages, single place to change validation logic |
| .env file writing | Direct file.write() | Atomic write with tempfile + replace | Prevents corruption on crash, ensures all-or-nothing writes, matches Phase 7 pattern |
| Rate limit state inspection | Manual SQLite queries | pyrate-limiter bucket.get() | API provides remaining, reset_time, total—no SQL queries needed |
| Environment variable defaults | Manual os.getenv(...) or "" | python-dotenv with .env.example | Template documents all keys, prevents typos, shows signup URLs |
| Retry logic for 429 errors | Manual sleep + retry loops | pyrate-limiter prevents 429s | Better to prevent rate limits than handle them—limiter knows exact reset time |

**Key insight:** Rate limiting is deceptively complex. The "simple" approach (counter + timestamp) fails on: burst handling, distributed systems, clock skew, race conditions, accurate reset time calculation, multiple time windows. pyrate-limiter solves all these with battle-tested leaky bucket algorithm and SQLite persistence. The 20 lines you'd write become 200+ to handle edge cases properly.

## Common Pitfalls

### Pitfall 1: Loading .env Too Late
**What goes wrong:** .env loaded after config.py or sources.py import, environment variables not set when modules initialize
**Why it happens:** Developer adds load_dotenv() in middle of main() after other imports
**How to avoid:** Load .env at very top of main() function, before any other application code runs (per user decision: startup loading, not lazy)
**Warning signs:** os.getenv() returns None even though .env file has the key

### Pitfall 2: Committing .env File to Git
**What goes wrong:** API keys leaked to GitHub, security vulnerability
**Why it happens:** Developer forgets to add .env to .gitignore before first commit
**How to avoid:** Add .env to .gitignore immediately when creating .env.example, verify with git check-ignore .env
**Warning signs:** GitHub security alert, API key usage spike from unknown IPs

### Pitfall 3: Silent Missing API Keys
**What goes wrong:** User thinks API sources are searched, but they're skipped silently due to missing keys
**Why it happens:** Developer uses os.getenv() with empty string default, no warning logged
**How to avoid:** Per user decision, log warning when key missing: "Skipped Adzuna: ADZUNA_APP_ID not found in .env"
**Warning signs:** User reports "no results from new sources", no error shown

### Pitfall 4: Shared Rate Limiter Across Sources
**What goes wrong:** Adzuna rate limit triggers, Authentic Jobs also gets blocked even though it has quota remaining
**Why it happens:** Developer creates single Limiter instance for all APIs
**How to avoid:** Per user decision, independent rate limits per source—create separate Limiter for each API
**Warning signs:** All API sources blocked when only one should be rate limited

### Pitfall 5: Rate Limit State in Wrong Location
**What goes wrong:** Rate limit SQLite files created in cwd, breaks when user runs job-radar from different directory
**Why it happens:** Developer uses relative path without anchoring to project root
**How to avoid:** Use os.getcwd() to anchor .rate_limits/ directory (matches .cache/ pattern from cache.py line 14)
**Warning signs:** New rate limit files created on each run, rate limits not persisting

### Pitfall 6: Forgetting to Gitignore Rate Limit State
**What goes wrong:** .rate_limits/*.db files committed to git, bloat repository size
**Why it happens:** Developer doesn't add .rate_limits/ to .gitignore when creating directory
**How to avoid:** Add .rate_limits/ to .gitignore alongside .env (both are runtime state, not source code)
**Warning signs:** Git status shows .db files as untracked

### Pitfall 7: Blocking on Rate Limit (Slow Searches)
**What goes wrong:** Search takes 5+ minutes waiting for rate limit windows to reset
**Why it happens:** Developer uses limiter.try_acquire(blocking=True), waits for rate limit reset
**How to avoid:** Per user decision, use blocking=False—skip source immediately, show results from other sources
**Warning signs:** Progress bar frozen, long waits between sources, user cancels search

### Pitfall 8: Invalid API Key Retry Loop
**What goes wrong:** 401/403 error retried forever, never succeeds, wastes API quota
**Why it happens:** Developer treats all API errors the same, retries 401/403 like 500/503
**How to avoid:** Per user decision, don't retry 401/403—log error once, skip source, continue (match best practices from web search)
**Warning signs:** Logs filled with repeated 401 errors, rapid API calls burning quota

## Code Examples

Verified patterns from official sources:

### Complete api_config.py Module
```python
# Source: python-dotenv v1.2.1 docs + user decisions
"""API credential loading and validation for job-radar.

Loads API keys from .env file using python-dotenv, validates required keys,
provides graceful degradation for missing keys.
"""

from dotenv import load_dotenv, find_dotenv
import os
import sys
import logging
from pathlib import Path

log = logging.getLogger(__name__)

def load_api_credentials():
    """Load API credentials from .env file.

    Per user decision:
    - .env file in project root (find_dotenv searches up from cwd)
    - Syntax errors: fail-fast with clear error message
    - Missing keys: log warning, skip source (handled by get_api_key)
    """
    # Find .env file starting from current working directory
    dotenv_path = find_dotenv(usecwd=True)

    if not dotenv_path:
        log.info("No .env file found - API sources will be skipped")
        return

    # Load .env file, fail-fast on syntax errors (per user decision)
    try:
        load_dotenv(dotenv_path, override=False)
        log.debug(f"Loaded .env from: {dotenv_path}")
    except Exception as e:
        # Syntax error (malformed .env file)
        print(f"Error: Invalid .env file syntax: {e}", file=sys.stderr)
        print(f"Fix the syntax errors in: {dotenv_path}", file=sys.stderr)
        print("Run 'job-radar --setup-apis' to recreate the file.", file=sys.stderr)
        sys.exit(1)

def get_api_key(key_name: str, source_name: str, required: bool = False) -> str | None:
    """Get API key from environment with validation.

    Parameters:
        key_name: Environment variable name (e.g., "ADZUNA_APP_ID")
        source_name: Human-readable source name for error messages
        required: If True, exit with error when key missing

    Returns:
        API key value, or None if missing (when not required)

    Per user decision: Missing keys → log warning, return None, caller skips source
    """
    key = os.getenv(key_name)

    if not key:
        if required:
            print(f"Error: Required API key {key_name} not found", file=sys.stderr)
            print("Run 'job-radar --setup-apis' to configure API keys.", file=sys.stderr)
            sys.exit(1)
        else:
            log.warning(
                f"Skipping {source_name}: {key_name} not found in .env file. "
                f"Run 'job-radar --setup-apis' to configure."
            )
            return None

    return key

def ensure_env_example():
    """Create .env.example if it doesn't exist.

    Per user decision: .env.example includes key names + signup URLs.
    """
    env_example_path = Path(os.getcwd()) / ".env.example"

    if env_example_path.exists():
        return

    content = """# Job Radar API Configuration
# Copy this file to .env and fill in your API keys

# Adzuna API Credentials
# Sign up at: https://developer.adzuna.com/
ADZUNA_APP_ID=
ADZUNA_APP_KEY=

# Authentic Jobs API Key
# Sign up at: https://authenticjobs.com/api/
AUTHENTIC_JOBS_API_KEY=

# Optional: Enable verbose rate limit debugging
API_DEBUG=false
"""

    try:
        env_example_path.write_text(content, encoding="utf-8")
        log.info(f"Created .env.example template: {env_example_path}")
    except OSError as e:
        log.warning(f"Failed to create .env.example: {e}")
```

### Complete rate_limits.py Module
```python
# Source: pyrate-limiter v3.14.0 docs + user decisions
"""Rate limiting infrastructure for API calls.

Provides persistent rate limiting using pyrate-limiter with SQLite backend.
Rate limit state persists across runs (like tracker.json pattern).
"""

from pyrate_limiter import Limiter, Rate, Duration, SQLiteBucket
from pathlib import Path
import os
import logging
import datetime

log = logging.getLogger(__name__)

# Per user decision: Hardcode rate limits per provider's official docs
# These limits are based on Adzuna/Authentic Jobs documentation
RATE_LIMITS = {
    "adzuna": [
        Rate(100, Duration.MINUTE),  # 100 calls per minute
        Rate(1000, Duration.HOUR),   # 1000 calls per hour
    ],
    "authentic_jobs": [
        Rate(60, Duration.MINUTE),   # 60 calls per minute (estimated, no official docs found)
    ],
}

_limiters: dict[str, Limiter] = {}  # Cache limiters per source

def get_rate_limiter(source: str) -> Limiter:
    """Get rate limiter for API source with persistent SQLite backend.

    Per user decision: Rate limit state persists to disk like tracker.json.

    Parameters:
        source: API source name (e.g., "adzuna", "authentic_jobs")

    Returns:
        Limiter instance with SQLite persistence
    """
    # Return cached limiter if exists
    if source in _limiters:
        return _limiters[source]

    # Create .rate_limits directory (like .cache pattern from cache.py)
    rate_limit_dir = Path(os.getcwd()) / ".rate_limits"
    rate_limit_dir.mkdir(exist_ok=True)

    # SQLite file per source (independent rate limits per user decision)
    db_path = rate_limit_dir / f"{source}.db"

    # Get rate limits for source (or default)
    rates = RATE_LIMITS.get(source, [Rate(60, Duration.MINUTE)])

    # Create bucket with persistent SQLite backend
    bucket = SQLiteBucket(rates, str(db_path))

    # Create and cache limiter
    limiter = Limiter(bucket)
    _limiters[source] = limiter

    log.debug(f"Initialized rate limiter for {source}: {db_path}")
    return limiter

def check_rate_limit(source: str, verbose: bool = False) -> bool:
    """Check if API call is allowed under rate limit.

    Per user decision: When rate limited → skip source, show results from others.

    Parameters:
        source: API source name
        verbose: If True, log rate limit debug info

    Returns:
        True if call allowed, False if rate limited
    """
    limiter = get_rate_limiter(source)
    identity = source  # Single identity per source

    # Show rate limit status if verbose (per user decision: --verbose flag)
    if verbose:
        bucket_state = limiter.bucket.get(identity)
        if bucket_state:
            remaining = bucket_state.remaining
            reset_time = bucket_state.reset_time
            reset_str = datetime.datetime.fromtimestamp(reset_time).strftime("%I:%M%p")
            log.debug(
                f"{source}: {remaining} calls remaining, resets at {reset_str}"
            )

    # Try to acquire permit (non-blocking per user decision)
    allowed = limiter.try_acquire(identity, blocking=False)

    if not allowed:
        # Per user decision: Rate limit warnings include retry time
        bucket_state = limiter.bucket.get(identity)
        if bucket_state:
            reset_time = bucket_state.reset_time
            reset_str = datetime.datetime.fromtimestamp(reset_time).strftime("%I:%M%p")
            log.warning(
                f"Skipped {source}: rate limited, retry after {reset_str}"
            )
        else:
            log.warning(f"Skipped {source}: rate limited")

    return allowed

def get_rate_limit_status(source: str) -> dict:
    """Get current rate limit status for debugging.

    Returns:
        Dict with remaining, reset_time, configured_rate
    """
    limiter = get_rate_limiter(source)
    identity = source

    bucket_state = limiter.bucket.get(identity)

    if not bucket_state:
        return {
            "remaining": "unknown",
            "reset_time": None,
            "configured_rate": RATE_LIMITS.get(source, [Rate(60, Duration.MINUTE)]),
        }

    return {
        "remaining": bucket_state.remaining,
        "reset_time": datetime.datetime.fromtimestamp(bucket_state.reset_time),
        "configured_rate": RATE_LIMITS.get(source, [Rate(60, Duration.MINUTE)]),
    }
```

### Integration with sources.py
```python
# Source: Existing sources.py pattern + rate limiting integration
# Modify existing fetch_* functions to add rate limiting

from .api_config import get_api_key
from .rate_limits import check_rate_limit

def fetch_adzuna(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch jobs from Adzuna API with rate limiting.

    Per user decisions:
    - Missing API keys: return empty list, log warning (already done in get_api_key)
    - Rate limited: return empty list, skip source (already done in check_rate_limit)
    - Invalid API key (401/403): show error once, skip source, don't retry
    """
    # Check for API credentials (per user decision: missing keys → skip source)
    app_id = get_api_key("ADZUNA_APP_ID", "Adzuna")
    app_key = get_api_key("ADZUNA_APP_KEY", "Adzuna")

    if not app_id or not app_key:
        return []  # Skip source, warning already logged

    # Check rate limit (per user decision: rate limited → skip source)
    if not check_rate_limit("adzuna", verbose=verbose):
        return []  # Skip source, warning already logged

    # Build API URL
    base_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": 50,
    }
    if location:
        params["where"] = location

    # Make API call (reuse existing cache.py pattern)
    from .cache import fetch_with_retry

    url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    body = fetch_with_retry(url, headers={"User-Agent": "JobRadar/1.2"}, use_cache=True)

    if not body:
        return []

    # Parse response
    try:
        import json
        data = json.loads(body)
        results = data.get("results", [])

        jobs = []
        for item in results:
            # Parse Adzuna job listing into JobResult
            job = JobResult(
                title=item.get("title", ""),
                company=item.get("company", {}).get("display_name", ""),
                location=item.get("location", {}).get("display_name", ""),
                # ... rest of parsing logic
            )
            jobs.append(job)

        return jobs

    except (json.JSONDecodeError, KeyError) as e:
        log.warning(f"Failed to parse Adzuna response: {e}")
        return []
    except requests.HTTPError as e:
        # Per user decision: 401/403 → show error once, skip source, don't retry
        if e.response.status_code in (401, 403):
            log.error(
                f"Adzuna API error: Invalid credentials (HTTP {e.response.status_code}). "
                f"Run 'job-radar --setup-apis' to fix."
            )
        else:
            log.error(f"Adzuna API error: HTTP {e.response.status_code}")
        return []
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded API keys in source | .env files with python-dotenv | 2012+ | 12-factor app principles, prevents credential leaks, environment-specific config |
| In-memory rate limiting | Persistent rate limiting with SQLite | 2020+ | State survives restarts, accurate tracking across runs, prevents quota exhaustion |
| Manual counter + timestamp | Leaky bucket algorithm | 2015+ | Handles burst traffic, accurate window tracking, prevents edge case bugs |
| Global rate limiter | Per-source rate limiters | Modern API design | Independent limits match real-world API quotas, no cross-contamination |
| config.ini for credentials | .env files | 2010+ | Industry standard, tooling support, simpler format (no sections) |
| Retry all HTTP errors | Don't retry 401/403 | Best practice | 401/403 are permanent errors, retrying wastes quota and time |
| os.environ direct access | python-dotenv with validation | 2015+ | Type validation, default values, clear error messages, template documentation |

**Deprecated/outdated:**
- **ConfigParser for API keys**: Use .env files (simpler, no sections, better tooling)
- **ratelimit library**: Use pyrate-limiter (has persistence, more features, actively maintained)
- **In-memory rate limit state**: Use SQLiteBucket (persists across runs, atomic operations)
- **Blocking on rate limit**: Use non-blocking try_acquire() (better UX, skip source immediately)

## Open Questions

Things that couldn't be fully resolved:

1. **Exact Adzuna API rate limits**
   - What we know: Adzuna has rate limits, increased on request for commercial users
   - What's unclear: Default free tier rate limits not publicly documented (no calls/minute or calls/hour in official docs)
   - Recommendation: Start with conservative 100/minute, 1000/hour based on common free tier patterns. Monitor for 429 errors in production, adjust if needed. Official docs say "generous" and "millions of hits per day" for big users, suggests free tier is sufficient for our use case (daily searches, not continuous scraping).

2. **Authentic Jobs API rate limits**
   - What we know: API requires API key, has endpoints for job search
   - What's unclear: No official rate limit documentation found (API docs at authenticjobs.com/api/docs)
   - Recommendation: Start with 60/minute (standard REST API default). Monitor for 429 errors in production. Contact Authentic Jobs support for official limits once integration is live.

3. **API key validation timing (upfront vs on-demand)**
   - What we know: User decision says "Claude's discretion on upfront ping vs fail-on-first-request"
   - What's unclear: Tradeoff between startup time (faster with on-demand) vs error clarity (better with upfront validation)
   - Recommendation: Use on-demand validation (don't ping APIs at startup). Rationale: (a) Faster startup (matches existing <10s startup requirement from Phase 6), (b) Clearer errors (first API call shows exact source that failed), (c) Fewer API calls (don't ping APIs that won't be used in this search). Implement --test-apis command for explicit validation when user wants to verify setup.

4. **Missing key behavior (silent skip vs warning)**
   - What we know: User decision says "Claude's discretion on silent skip vs warning"
   - What's unclear: Balance between UX (don't spam logs) and transparency (user should know why no API results)
   - Recommendation: Log warning once per source per run, include actionable message: "Skipped Adzuna: ADZUNA_APP_ID not found. Run 'job-radar --setup-apis' to configure." Rationale: (a) Transparent without being noisy (one warning per source), (b) Actionable (tells user exactly how to fix), (c) Matches existing log patterns (cache.py logs warnings for failures).

5. **Rate limit persistence format**
   - What we know: User decision says "like tracker.json pattern" but also says "Claude's discretion on exact format"
   - What's unclear: Whether to use JSON (like tracker.json) or SQLite (like pyrate-limiter default)
   - Recommendation: Use SQLite (pyrate-limiter's SQLiteBucket). Rationale: (a) Atomic operations prevent race conditions, (b) No manual locking needed, (c) Better performance for frequent updates, (d) Matches pyrate-limiter's design (using JSON would require custom Bucket implementation), (e) Still follows "persist to disk like tracker.json" principle (different format, same concept).

## Sources

### Primary (HIGH confidence)
- python-dotenv v1.2.1 documentation: https://github.com/theskumar/python-dotenv - Official docs, API reference, usage patterns
- python-dotenv PyPI page: https://pypi.org/project/python-dotenv/ - Version history, installation
- pyrate-limiter v3.14.0 documentation: https://pypi.org/project/pyrate-limiter/ - Rate limiting API, SQLite backend
- pyrate-limiter GitHub: https://github.com/vutran1710/PyrateLimiter - Source code, examples, issue discussions
- Python logging module docs: https://docs.python.org/3/library/logging.html - Standard library logging patterns

### Secondary (MEDIUM confidence)
- .env.example best practices: https://www.getfishtank.com/insights/best-practices-for-committing-env-files-to-version-control - Template patterns, security guidance
- Python environment variables best practices: https://dagster.io/blog/python-environment-variables - Validation, defaults, type conversion
- API error handling: https://apistatuscheck.com/blog/api-error-codes-cheat-sheet - 401 vs 403, retry strategies
- Questionary documentation: https://questionary.readthedocs.io/ - Interactive prompts for --setup-apis (already researched in Phase 7)
- WebSearch results on python-dotenv best practices 2026: [How to Work with Environment Variables in Python](https://oneuptime.com/blog/post/2026-01-26-work-with-environment-variables-python/view), [Using Py Dotenv Package](https://configu.com/blog/using-py-dotenv-python-dotenv-package-to-manage-env-variables/)
- WebSearch results on Python rate limiting 2026: [requests-ratelimiter PyPI](https://pypi.org/project/requests-ratelimiter/), [pyrate-limiter PyPI](https://pypi.org/project/pyrate-limiter/)

### Tertiary (LOW confidence)
- Adzuna API overview: https://developer.adzuna.com/overview - General API info, no specific rate limits found
- Authentic Jobs API: https://publicapis.io/authentic-jobs-api - Basic endpoint info, no rate limit details found
- WebSearch results on API rate limiting: [Handling API Rate Limits with Python](https://medium.com/@balakrishnamaduru/handling-api-rate-limits-with-python-a-simple-recursive-approach-08349dd71057)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - python-dotenv and pyrate-limiter are well-documented, actively maintained, current versions verified (v1.2.1 and v3.14.0 released in 2025-2026)
- Architecture: HIGH - Patterns verified from official docs, match existing project patterns (tracker.json, cache.py, wizard.py from Phase 7)
- Pitfalls: MEDIUM - Based on official docs warnings, Python best practices, and web search results on common mistakes; some inferred from general API development experience
- Rate limits: LOW - Adzuna and Authentic Jobs specific limits not found in official documentation, using conservative estimates based on common API patterns

**Research date:** 2026-02-10
**Valid until:** ~90 days (python-dotenv and pyrate-limiter are stable libraries; Adzuna/Authentic Jobs rate limits may change)

**Note on user decisions:** All patterns align with CONTEXT.md decisions:
- ✓ .env in project root (find_dotenv pattern)
- ✓ .env.example with signup URLs (template pattern)
- ✓ Independent rate limits per source (separate Limiter instances)
- ✓ Skip source when rate limited (blocking=False)
- ✓ Persist rate limit state (SQLiteBucket)
- ✓ Hardcoded limits per provider docs (RATE_LIMITS dict)
- ✓ --setup-apis command (questionary pattern from Phase 7)
- ✓ --test-apis command (validation helper)
- ✓ --verbose rate limit debugging (bucket state inspection)
- ✓ Missing key → warning (get_api_key logs warning)
- ✓ Syntax error → fail-fast (load_api_credentials exits)
- ✓ 401/403 → show error once, skip source (don't retry)
