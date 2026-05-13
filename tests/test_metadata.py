"""Project metadata consistency tests."""

import tomllib
from pathlib import Path

from job_radar import __version__


def test_package_version_matches_pyproject():
    """Runtime version and package metadata stay in sync."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert __version__ == pyproject["project"]["version"]
