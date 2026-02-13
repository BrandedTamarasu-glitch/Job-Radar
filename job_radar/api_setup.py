"""Interactive API credential setup and validation commands.

Provides --setup-apis wizard for collecting API keys and --test-apis validation
for checking configured credentials. Uses questionary for interactive prompts
and atomic file writes to ensure .env is never corrupted.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

import questionary
import requests
from questionary import Style

log = logging.getLogger(__name__)

# Custom style for cross-platform safe colors
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'bold'),
    ('answer', 'fg:green bold'),
    ('instruction', 'fg:ansigray'),
])


def setup_apis():
    """Interactive API key setup wizard.

    Prompts user for API keys for each supported job source, validates inputs,
    and atomically writes .env file to project root. Uses questionary for
    interactive prompts with skip support (press Enter to skip optional sources).

    Returns
    -------
    None
        Exits after writing .env or on cancellation

    Notes
    -----
    Atomic write using tempfile.mkstemp() + Path.replace() ensures .env is
    never partially written (crash-safe). KeyboardInterrupt (Ctrl+C) is
    handled gracefully with cleanup message.
    """
    print("\n" + "=" * 60)
    print("API Key Setup")
    print("=" * 60)
    print("\nConfigure API keys for job sources. Press Enter to skip optional sources.\n")

    credentials = {}

    # Section 1 - Adzuna
    print("=" * 60)
    print("Adzuna API")
    print("=" * 60)
    print("Sign up at: https://developer.adzuna.com/\n")

    try:
        adzuna_app_id = questionary.text(
            "ADZUNA_APP_ID (press Enter to skip):",
            style=custom_style
        ).ask()

        if adzuna_app_id is None:  # Ctrl+C
            print("\nSetup cancelled.")
            return

        if adzuna_app_id.strip():
            adzuna_app_key = questionary.text(
                "ADZUNA_APP_KEY:",
                style=custom_style
            ).ask()

            if adzuna_app_key is None:  # Ctrl+C
                print("\nSetup cancelled.")
                return

            if adzuna_app_key.strip():
                credentials["ADZUNA_APP_ID"] = adzuna_app_id.strip()
                credentials["ADZUNA_APP_KEY"] = adzuna_app_key.strip()

    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        return

    # Section 2 - Authentic Jobs
    print("\n" + "=" * 60)
    print("Authentic Jobs API")
    print("=" * 60)
    print("Sign up at: https://authenticjobs.com/api/\n")

    try:
        authentic_jobs_key = questionary.text(
            "AUTHENTIC_JOBS_API_KEY (press Enter to skip):",
            style=custom_style
        ).ask()

        if authentic_jobs_key is None:  # Ctrl+C
            print("\nSetup cancelled.")
            return

        if authentic_jobs_key.strip():
            credentials["AUTHENTIC_JOBS_API_KEY"] = authentic_jobs_key.strip()

    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        return

    # Section 3 - JSearch
    print("\n" + "=" * 60)
    print("JSearch API (LinkedIn, Indeed, Glassdoor)")
    print("=" * 60)
    print("Sign up at: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch\n")

    try:
        jsearch_key = questionary.text(
            "JSEARCH_API_KEY (press Enter to skip):",
            style=custom_style
        ).ask()

        if jsearch_key is None:  # Ctrl+C
            print("\nSetup cancelled.")
            return

        if jsearch_key.strip():
            # Validate key with test request
            print("  Testing...", end=" ", flush=True)
            try:
                test_url = "https://jsearch.p.rapidapi.com/search?query=test&num_pages=1"
                headers = {
                    "X-RapidAPI-Key": jsearch_key.strip(),
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                }
                response = requests.get(test_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    print("✓ Key is valid")
                    credentials["JSEARCH_API_KEY"] = jsearch_key.strip()
                elif response.status_code in (401, 403):
                    print(f"✗ Invalid key (HTTP {response.status_code})")
                    credentials["JSEARCH_API_KEY"] = jsearch_key.strip()
                else:
                    print(f"⚠ Could not validate (HTTP {response.status_code}) — key saved anyway")
                    credentials["JSEARCH_API_KEY"] = jsearch_key.strip()
            except requests.Timeout:
                print("⚠ Could not validate (timeout) — key saved anyway")
                credentials["JSEARCH_API_KEY"] = jsearch_key.strip()
            except requests.RequestException as e:
                print(f"⚠ Could not validate (network error) — key saved anyway")
                credentials["JSEARCH_API_KEY"] = jsearch_key.strip()

    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        return

    # Section 4 - USAJobs
    print("\n" + "=" * 60)
    print("USAJobs API (Federal Government Jobs)")
    print("=" * 60)
    print("Sign up at: https://developer.usajobs.gov/apirequest/\n")

    try:
        usajobs_email = questionary.text(
            "USAJOBS_EMAIL (press Enter to skip):",
            style=custom_style
        ).ask()

        if usajobs_email is None:  # Ctrl+C
            print("\nSetup cancelled.")
            return

        if usajobs_email.strip():
            usajobs_key = questionary.text(
                "USAJOBS_API_KEY:",
                style=custom_style
            ).ask()

            if usajobs_key is None:  # Ctrl+C
                print("\nSetup cancelled.")
                return

            if usajobs_key.strip():
                # Validate key with test request
                print("  Testing...", end=" ", flush=True)
                try:
                    test_url = "https://data.usajobs.gov/api/search?Keyword=test&ResultsPerPage=1"
                    headers = {
                        "Host": "data.usajobs.gov",
                        "User-Agent": usajobs_email.strip(),
                        "Authorization-Key": usajobs_key.strip()
                    }
                    response = requests.get(test_url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        print("✓ Key is valid")
                        credentials["USAJOBS_API_KEY"] = usajobs_key.strip()
                        credentials["USAJOBS_EMAIL"] = usajobs_email.strip()
                    elif response.status_code in (401, 403):
                        print(f"✗ Invalid credentials (HTTP {response.status_code})")
                        credentials["USAJOBS_API_KEY"] = usajobs_key.strip()
                        credentials["USAJOBS_EMAIL"] = usajobs_email.strip()
                    else:
                        print(f"⚠ Could not validate (HTTP {response.status_code}) — credentials saved anyway")
                        credentials["USAJOBS_API_KEY"] = usajobs_key.strip()
                        credentials["USAJOBS_EMAIL"] = usajobs_email.strip()
                except requests.Timeout:
                    print("⚠ Could not validate (timeout) — credentials saved anyway")
                    credentials["USAJOBS_API_KEY"] = usajobs_key.strip()
                    credentials["USAJOBS_EMAIL"] = usajobs_email.strip()
                except requests.RequestException as e:
                    print(f"⚠ Could not validate (network error) — credentials saved anyway")
                    credentials["USAJOBS_API_KEY"] = usajobs_key.strip()
                    credentials["USAJOBS_EMAIL"] = usajobs_email.strip()

    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        return

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if credentials:
        print("\nConfigured sources:")
        if "ADZUNA_APP_ID" in credentials:
            print("  ✓ Adzuna")
        if "AUTHENTIC_JOBS_API_KEY" in credentials:
            print("  ✓ Authentic Jobs")
        if "JSEARCH_API_KEY" in credentials:
            print("  ✓ JSearch (LinkedIn, Indeed, Glassdoor)")
        if "USAJOBS_API_KEY" in credentials:
            print("  ✓ USAJobs (Federal)")
    else:
        print("\nNo sources configured (all skipped)")

    # Show tip for JSearch if not configured
    if "JSEARCH_API_KEY" not in credentials:
        print("\nTip: Set up JSearch API key to search LinkedIn, Indeed, and Glassdoor")

    # Confirm save
    try:
        confirmed = questionary.confirm(
            "\nSave configuration?",
            default=True,
            style=custom_style
        ).ask()

        if confirmed is None or not confirmed:
            print("\nSetup cancelled.")
            return

    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        return

    # Build .env content
    env_lines = ["# Job Radar API Configuration\n"]
    env_lines.append("# Generated by job-radar --setup-apis\n\n")

    if "ADZUNA_APP_ID" in credentials:
        env_lines.append("# Adzuna API Credentials\n")
        env_lines.append(f"ADZUNA_APP_ID={credentials['ADZUNA_APP_ID']}\n")
        env_lines.append(f"ADZUNA_APP_KEY={credentials['ADZUNA_APP_KEY']}\n\n")

    if "AUTHENTIC_JOBS_API_KEY" in credentials:
        env_lines.append("# Authentic Jobs API Key\n")
        env_lines.append(f"AUTHENTIC_JOBS_API_KEY={credentials['AUTHENTIC_JOBS_API_KEY']}\n\n")

    if "JSEARCH_API_KEY" in credentials:
        env_lines.append("# JSearch API Key (RapidAPI)\n")
        env_lines.append(f"JSEARCH_API_KEY={credentials['JSEARCH_API_KEY']}\n\n")

    if "USAJOBS_API_KEY" in credentials:
        env_lines.append("# USAJobs API Credentials\n")
        env_lines.append(f"USAJOBS_API_KEY={credentials['USAJOBS_API_KEY']}\n")
        env_lines.append(f"USAJOBS_EMAIL={credentials['USAJOBS_EMAIL']}\n\n")

    env_content = "".join(env_lines)

    # Atomic write to .env
    env_path = Path.cwd() / ".env"

    # Create temp file in same directory (same filesystem for atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        dir=env_path.parent,
        prefix=env_path.name + ".",
        suffix=".tmp"
    )

    try:
        # Write content to temp file
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(env_content)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk

        # Atomic replace
        Path(tmp_path).replace(env_path)

        print(f"\n✅ Configuration saved to {env_path}")
        print("\nNext steps:")
        print("  1. Run 'job-radar --test-apis' to verify your credentials")
        print("  2. Run 'job-radar' to start searching for jobs\n")

    except Exception as e:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except:
            pass
        print(f"\nError: Failed to write .env file: {e}", file=sys.stderr)
        sys.exit(1)


def test_apis():
    """Test configured API keys and report status.

    Loads credentials from .env, makes minimal test requests to each configured
    API source, and reports pass/fail status with error details. Non-configured
    sources are skipped with "(skipped)" status.

    Returns
    -------
    None
        Prints results to stdout and exits

    Notes
    -----
    Test requests:
    - Adzuna: GET /v1/api/jobs/us/search/1 with results_per_page=1
    - Authentic Jobs: GET /?method=aj.jobs.search&keywords=test&format=json

    Network errors (timeout, connection) are reported separately from auth
    failures (401/403) to help users diagnose issues.
    """
    from .api_config import load_api_credentials

    # Load credentials first
    load_api_credentials()

    print("\n" + "=" * 60)
    print("Testing API Keys")
    print("=" * 60 + "\n")

    results = {}

    # Test Adzuna
    print("Adzuna API:")
    adzuna_app_id = os.getenv("ADZUNA_APP_ID")
    adzuna_app_key = os.getenv("ADZUNA_APP_KEY")

    if not adzuna_app_id or not adzuna_app_key:
        print("  ✗ Not configured (skipped)\n")
        results["adzuna"] = "skipped"
    else:
        try:
            url = (
                f"https://api.adzuna.com/v1/api/jobs/us/search/1"
                f"?app_id={adzuna_app_id}&app_key={adzuna_app_key}&results_per_page=1"
            )
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                print("  ✓ Pass\n")
                results["adzuna"] = "pass"
            elif response.status_code in (401, 403):
                print("  ✗ Fail: Invalid credentials\n")
                results["adzuna"] = "fail"
            else:
                print(f"  ✗ Error: HTTP {response.status_code}\n")
                results["adzuna"] = "error"

        except requests.Timeout:
            print("  ✗ Error: Request timeout\n")
            results["adzuna"] = "error"
        except requests.RequestException as e:
            print(f"  ✗ Error: Network error ({e})\n")
            results["adzuna"] = "error"

    # Test Authentic Jobs
    print("Authentic Jobs API:")
    authentic_jobs_key = os.getenv("AUTHENTIC_JOBS_API_KEY")

    if not authentic_jobs_key:
        print("  ✗ Not configured (skipped)\n")
        results["authentic_jobs"] = "skipped"
    else:
        try:
            url = (
                f"https://authenticjobs.com/api/"
                f"?api_key={authentic_jobs_key}&method=aj.jobs.search&keywords=test&format=json"
            )
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                print("  ✓ Pass\n")
                results["authentic_jobs"] = "pass"
            elif response.status_code in (401, 403):
                print("  ✗ Fail: Invalid credentials\n")
                results["authentic_jobs"] = "fail"
            else:
                print(f"  ✗ Error: HTTP {response.status_code}\n")
                results["authentic_jobs"] = "error"

        except requests.Timeout:
            print("  ✗ Error: Request timeout\n")
            results["authentic_jobs"] = "error"
        except requests.RequestException as e:
            print(f"  ✗ Error: Network error ({e})\n")
            results["authentic_jobs"] = "error"

    # Test JSearch
    print("JSearch API:")
    jsearch_key = os.getenv("JSEARCH_API_KEY")

    if not jsearch_key:
        print("  ✗ Not configured (skipped)")
        print("  Tip: Set up JSearch API key to search LinkedIn, Indeed, and Glassdoor\n")
        results["jsearch"] = "skipped"
    else:
        try:
            url = "https://jsearch.p.rapidapi.com/search?query=test&num_pages=1"
            headers = {
                "X-RapidAPI-Key": jsearch_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                print("  ✓ Pass\n")
                results["jsearch"] = "pass"
            elif response.status_code in (401, 403):
                print("  ✗ Fail: Invalid credentials\n")
                results["jsearch"] = "fail"
            else:
                print(f"  ✗ Error: HTTP {response.status_code}\n")
                results["jsearch"] = "error"

        except requests.Timeout:
            print("  ✗ Error: Request timeout\n")
            results["jsearch"] = "error"
        except requests.RequestException as e:
            print(f"  ✗ Error: Network error ({e})\n")
            results["jsearch"] = "error"

    # Test USAJobs
    print("USAJobs API:")
    usajobs_key = os.getenv("USAJOBS_API_KEY")
    usajobs_email = os.getenv("USAJOBS_EMAIL")

    if not usajobs_key or not usajobs_email:
        print("  ✗ Not configured (skipped)\n")
        results["usajobs"] = "skipped"
    else:
        try:
            url = "https://data.usajobs.gov/api/search?Keyword=test&ResultsPerPage=1"
            headers = {
                "Host": "data.usajobs.gov",
                "User-Agent": usajobs_email,
                "Authorization-Key": usajobs_key
            }
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                print("  ✓ Pass\n")
                results["usajobs"] = "pass"
            elif response.status_code in (401, 403):
                print("  ✗ Fail: Invalid credentials\n")
                results["usajobs"] = "fail"
            else:
                print(f"  ✗ Error: HTTP {response.status_code}\n")
                results["usajobs"] = "error"

        except requests.Timeout:
            print("  ✗ Error: Request timeout\n")
            results["usajobs"] = "error"
        except requests.RequestException as e:
            print(f"  ✗ Error: Network error ({e})\n")
            results["usajobs"] = "error"

    # Summary
    print("=" * 60)
    configured = [k for k, v in results.items() if v != "skipped"]
    working = [k for k, v in results.items() if v == "pass"]

    print(f"Summary: {len(working)}/{len(configured)} configured APIs working")

    if len(working) < len(configured):
        print("\nTip: Run 'job-radar --setup-apis' to reconfigure failed sources")

    print()
