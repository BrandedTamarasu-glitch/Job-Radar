"""API credential management for external job sources.

Loads API keys from .env file using python-dotenv, provides graceful degradation
when credentials are missing (skip source instead of crash), and ensures .env.example
template exists for first-time users.
"""

import logging
import os
import sys

from dotenv import find_dotenv, load_dotenv

log = logging.getLogger(__name__)


def load_api_credentials():
    """Load API credentials from .env file.

    Uses find_dotenv(usecwd=True) to locate .env in project root. If no .env file
    is found, logs an info message (not an error) — API sources will be skipped.
    If .env exists but has syntax errors, prints clear error to stderr and exits.
    """
    dotenv_path = find_dotenv(usecwd=True)

    if not dotenv_path:
        log.info("No .env file found - API sources will be skipped")
        return

    try:
        load_dotenv(dotenv_path, override=False)
        log.debug(f"Loaded API credentials from {dotenv_path}")
    except Exception as e:
        print(f"Error: .env file is corrupted at {dotenv_path}", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("Run 'job-radar --setup-apis' to recreate", file=sys.stderr)
        sys.exit(1)


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
        log.warning(f"Skipping {source_name}: {key_name} not found in .env file. "
                   f"Run 'job-radar --setup-apis' to configure.")
        return None

    return key_value


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
"""

    try:
        with open(example_path, "w", encoding="utf-8") as f:
            f.write(template_content)
        log.debug(f"Created .env.example at {example_path}")
    except OSError as e:
        log.warning(f"Failed to create .env.example: {e}")
