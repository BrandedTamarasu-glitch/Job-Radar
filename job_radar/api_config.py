"""API credential management for external job sources.

Loads API keys from the app-data credential file using python-dotenv, provides
graceful degradation when credentials are missing (skip source instead of crash),
and ensures .env.example template exists for first-time users.
"""

import logging
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from job_radar.paths import get_data_dir

log = logging.getLogger(__name__)

API_CREDENTIALS_FILENAME = ".env"
API_CREDENTIAL_KEYS = (
    "JSEARCH_API_KEY",
    "USAJOBS_EMAIL",
    "USAJOBS_API_KEY",
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
    "AUTHENTIC_JOBS_API_KEY",
    "SERPAPI_API_KEY",
)


class ApiCredentialError(RuntimeError):
    """Raised when API credentials cannot be loaded or saved."""


def get_api_credentials_path() -> Path:
    """Return the app-private credential file path."""
    return get_data_dir() / API_CREDENTIALS_FILENAME


def get_legacy_cwd_credentials_path() -> Path:
    """Return the legacy cwd credential path used by older releases."""
    return Path.cwd() / API_CREDENTIALS_FILENAME


def load_api_credentials():
    """Load API credentials from the app-data credential file.

    If a legacy cwd `.env` exists and app-data credentials do not, migrate it once
    to app data before loading. Ancestor directory search is intentionally avoided.
    """
    dotenv_path = get_api_credentials_path()
    _migrate_legacy_credentials(dotenv_path)

    if not dotenv_path.exists():
        log.info("No API credential file found - API sources will be skipped")
        return

    try:
        load_dotenv(dotenv_path, override=False)
        log.debug("Loaded API credentials from %s", dotenv_path)
    except Exception as e:
        raise ApiCredentialError(f"Failed to load API credentials from {dotenv_path}: {e}") from e


def get_api_key(key_name: str, source_name: str) -> str | None:
    """Get API key from environment, with graceful degradation.

    Parameters
    ----------
    key_name : str
        Environment variable name (e.g., "ADZUNA_APP_ID")
    source_name : str
        Human-readable source name for warning messages (e.g., "Adzuna")

    Returns
    -------
    str | None
        API key value if found, None if missing (source should be skipped)

    Notes
    -----
    Logs warning on missing key, guiding user to run --setup-apis. Warning only
    fires once per source per run (each key checked once during fetch cycle).
    """
    key_value = os.getenv(key_name)

    if not key_value:
        log.warning(
            "Skipping %s: %s not found in API credentials. Run 'job-radar --setup-apis' to configure.",
            source_name,
            key_name,
        )
        return None

    return key_value


def read_api_credentials_file(path: Path | None = None) -> dict[str, str]:
    """Read key/value pairs from an API credential file."""
    credentials_path = get_api_credentials_path() if path is None else Path(path)
    values: dict[str, str] = {}
    if not credentials_path.exists():
        return values
    try:
        for line in credentials_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    except OSError as e:
        raise ApiCredentialError(f"Failed to read API credentials from {credentials_path}: {e}") from e
    return values


def save_api_credentials(credentials: dict[str, str]) -> Path:
    """Merge and save API credentials under the app-data directory."""
    credentials_path = get_api_credentials_path()
    existing = read_api_credentials_file(credentials_path)
    existing.update({key: value for key, value in credentials.items() if value})
    content = _format_credentials(existing)
    _write_private_text(credentials_path, content)
    load_dotenv(credentials_path, override=True)
    return credentials_path


def _migrate_legacy_credentials(destination: Path) -> None:
    """Copy a legacy cwd `.env` into app data once without ancestor search."""
    if destination.exists():
        return
    legacy_path = get_legacy_cwd_credentials_path()
    if not legacy_path.exists() or legacy_path.resolve() == destination.resolve():
        return
    try:
        values = read_api_credentials_file(legacy_path)
    except ApiCredentialError as e:
        log.warning("Failed to read legacy API credentials: %s", e)
        return
    if not values:
        return
    try:
        _write_private_text(destination, _format_credentials(values))
        log.info("Migrated legacy API credentials to app data at %s", destination)
    except ApiCredentialError as e:
        log.warning("Failed to migrate legacy API credentials: %s", e)


def _write_private_text(path: Path, content: str) -> None:
    """Atomically write private text with owner-only permissions where supported."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        Path(tmp_path).replace(path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise ApiCredentialError(f"Failed to write API credentials to {path}: {e}") from e


def _format_credentials(values: dict[str, str]) -> str:
    """Format credentials with stable sections."""
    lines = ["# Job Radar API Configuration", ""]
    sections = [
        ("# JSearch API (LinkedIn, Indeed, Glassdoor aggregator)", ("JSEARCH_API_KEY",)),
        ("# USAJobs API (Federal Government Jobs)", ("USAJOBS_EMAIL", "USAJOBS_API_KEY")),
        ("# Adzuna API", ("ADZUNA_APP_ID", "ADZUNA_APP_KEY")),
        ("# Authentic Jobs API", ("AUTHENTIC_JOBS_API_KEY",)),
        ("# SerpAPI (Google Jobs)", ("SERPAPI_API_KEY",)),
    ]
    for heading, keys in sections:
        lines.append(heading)
        for key in keys:
            lines.append(f"{key}={values.get(key, '')}")
        lines.append("")
    for key in sorted(set(values) - set(API_CREDENTIAL_KEYS)):
        lines.append(f"{key}={values[key]}")
    return "\n".join(lines).rstrip() + "\n"


def ensure_env_example():
    """Create .env.example template if it doesn't exist.

    Checks current working directory for .env.example. If missing, creates
    template with all required API keys and signup URLs. Handles OSError
    gracefully (logs warning, doesn't crash).
    """
    example_path = os.path.join(os.getcwd(), ".env.example")

    if os.path.exists(example_path):
        return

    template_content = """# Job Radar API Configuration
# Copy this file to .env and fill in your API keys

# Adzuna API Credentials
# Sign up at: https://developer.adzuna.com/
ADZUNA_APP_ID=
ADZUNA_APP_KEY=

# Authentic Jobs API Key
# Sign up at: https://authenticjobs.com/api/
AUTHENTIC_JOBS_API_KEY=

# SerpAPI (Google Jobs)
# Sign up at: https://serpapi.com/
# Free tier: 100 searches/month
SERPAPI_API_KEY=
"""

    try:
        with open(example_path, "w", encoding="utf-8") as f:
            f.write(template_content)
        log.debug(f"Created .env.example at {example_path}")
    except OSError as e:
        log.warning(f"Failed to create .env.example: {e}")
