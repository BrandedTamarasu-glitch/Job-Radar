"""Safety helpers for generated reports."""

from __future__ import annotations

from urllib.parse import urlsplit


SAFE_EXTERNAL_URL_SCHEMES = {"http", "https"}


def safe_external_url(url: str | None) -> str:
    """Return a safe clickable external URL, or an empty string when unsafe."""
    if not url:
        return ""
    candidate = str(url).strip()
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return ""
    if parsed.scheme.lower() not in SAFE_EXTERNAL_URL_SCHEMES:
        return ""
    if not parsed.netloc:
        return ""
    return candidate
