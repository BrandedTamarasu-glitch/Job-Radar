"""View-model helpers for uninstall result display."""

from __future__ import annotations

from pathlib import Path


def uninstall_failure_message(failures: list[tuple[str, str]]) -> str:
    """Format partial uninstall failure details for the error dialog."""
    lines = ["Some files could not be deleted:", ""]
    for path, error in failures[:5]:
        lines.append(f"- {path}")
        lines.append(f"  Error: {error}")
    if len(failures) > 5:
        lines.append("")
        lines.append(f"...and {len(failures) - 5} more")
    return "\n".join(lines)


def uninstall_final_message(binary_path: Path | str | None, cleanup_message: str | None) -> str:
    """Return the uninstall completion message."""
    if cleanup_message:
        return cleanup_message
    if binary_path:
        return f"Data removed. Please manually delete: {binary_path}"
    return "Data removed successfully."
