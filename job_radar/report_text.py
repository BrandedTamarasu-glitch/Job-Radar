"""Shared text formatting helpers for generated reports."""

from __future__ import annotations


def make_snippet(text: str, max_len: int = 80) -> str:
    """Create a short snippet from description text, safe for tables."""
    if not text:
        return "—"
    clean = text.replace("|", " ").replace("\n", " ").strip()
    if len(clean) > max_len:
        return clean[:max_len - 3].rsplit(" ", 1)[0] + "..."
    return clean if clean else "—"


def markdown_cell(value: str) -> str:
    """Escape a value for use inside a Markdown table cell."""
    return value.replace("|", "\\|").replace("\n", " ").strip()
