"""View-model helpers for installer launch status display."""

from __future__ import annotations

from pathlib import Path


def install_prompt_message(platform: str) -> str:
    """Return the installer confirmation status line for a platform."""
    if platform == "darwin":
        return "Opening installer DMG..."
    if platform == "win32":
        return "Launching installer... Windows may show a security prompt."
    return "Launching installer..."


def install_launch_status_message(platform: str) -> str:
    """Return the in-progress installer launch status line for a platform."""
    if platform == "darwin":
        return "Opening installer DMG..."
    return "Launching installer..."


def install_launch_error_message(installer_path: Path, error: object) -> str:
    """Return the installer launch failure dialog message."""
    return f"Couldn't launch installer. File saved at: {installer_path}\n\n{error}"


def installer_not_found_message(dest_path: str) -> str:
    """Return the missing-installer re-download prompt."""
    return f"Installer file not found. Download again?\n\n{dest_path}"
