"""Config file loading for job-radar CLI.

Loads persistent defaults from ~/.job-radar/config.json so users
don't have to repeat common flags on every run.
"""

import json
import sys
from pathlib import Path

LEGACY_CONFIG_PATH = Path("~/.job-radar/config.json")


def _default_config_path() -> Path:
    """Return default config path, using platform-appropriate directory."""
    from .paths import get_data_dir
    return get_data_dir() / "config.json"

# Underscore names match argparse dest names.
# "profile" excluded: required=True, argparse validates before set_defaults applies.
# "config" excluded: circular reference.
KNOWN_KEYS = {"min_score", "new_only", "output"}


def load_config(config_path: str | None = None) -> dict:
    """Load config from JSON file, returning a dict of recognized keys.

    Parameters
    ----------
    config_path:
        Path to config file. If None, uses platform-appropriate default path
        with fallback to legacy ~/.job-radar/config.json for backward compatibility.

    Returns
    -------
    dict
        Recognized config values. Empty dict if file missing or invalid.
    """
    if config_path is not None:
        path = Path(config_path).expanduser()
    else:
        path = _default_config_path()
        # Backward compatibility: check legacy path if new path doesn't exist
        if not path.exists():
            legacy_path = LEGACY_CONFIG_PATH.expanduser()
            if legacy_path.exists():
                path = legacy_path

    # CONF-03: missing file = no behavior change
    if not path.exists():
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        print(
            f"Warning: Could not parse config file {path}: {e.msg} (line {e.lineno})",
            file=sys.stderr,
        )
        return {}

    if not isinstance(raw, dict):
        print(
            f"Warning: Config file {path} must be a JSON object, got {type(raw).__name__}",
            file=sys.stderr,
        )
        return {}

    result = {}
    for key, value in raw.items():
        if key not in KNOWN_KEYS:
            # CONF-05: warn on unknown keys
            print(f"Warning: Unrecognized config key: '{key}'", file=sys.stderr)
        else:
            result[key] = value

    return result
