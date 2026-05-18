"""Top-level window shell helpers."""

from __future__ import annotations


def clear_content_except_header(window) -> None:
    """Remove all top-level content except the row-0 header."""
    for widget in list(window.winfo_children()):
        if widget.winfo_manager() == "grid" and widget.grid_info().get("row") == 0:
            continue
        widget.destroy()
