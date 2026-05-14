"""Persistence helpers for saved and recent GUI searches."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from job_radar.paths import get_data_dir


RECENT_SEARCH_LIMIT = 10
SAVED_SEARCHES_FILENAME = "saved_searches.json"
SEARCH_CONFIG_KEYS = (
    "from_date",
    "to_date",
    "freshness",
    "min_score",
    "new_only",
    "preset",
    "selected_sources",
    "selected_manual_sources",
    "include_companies",
    "exclude_companies",
    "required_skills",
    "preferred_skills",
    "location_strictness",
)


def get_saved_searches_path() -> Path:
    """Return the app-data path for saved search state."""
    return get_data_dir() / SAVED_SEARCHES_FILENAME


def load_search_history(path: Path | None = None) -> dict:
    """Load saved search state, returning a valid empty structure on failure."""
    path = path or get_saved_searches_path()
    if not path.exists():
        return _empty_state()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_state()

    if not isinstance(data, dict):
        return _empty_state()

    recent = data.get("recent")
    saved = data.get("saved")
    return {
        "version": 1,
        "recent": recent if isinstance(recent, list) else [],
        "saved": saved if isinstance(saved, list) else [],
    }


def record_recent_search(
    config: dict[str, Any],
    path: Path | None = None,
    limit: int = RECENT_SEARCH_LIMIT,
    now: datetime | None = None,
) -> dict:
    """Record a recent search config, deduping equivalent configs."""
    path = path or get_saved_searches_path()
    state = load_search_history(path)
    normalized_config = normalize_search_config(config)
    timestamp = _timestamp(now)

    recent = [
        item for item in state["recent"]
        if item.get("config") != normalized_config
    ]
    recent.insert(
        0,
        {
            "name": summarize_search_config(normalized_config),
            "created_at": timestamp,
            "last_run_at": timestamp,
            "config": normalized_config,
        },
    )
    state["recent"] = recent[:limit]
    _write_state(path, state)
    return deepcopy(state)


def save_named_search(
    name: str,
    config: dict[str, Any],
    path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Create or replace a named saved search."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Saved search name cannot be empty")

    path = path or get_saved_searches_path()
    state = load_search_history(path)
    timestamp = _timestamp(now)
    normalized_config = normalize_search_config(config)

    saved = [
        item for item in state["saved"]
        if str(item.get("name", "")).casefold() != clean_name.casefold()
    ]
    saved.insert(
        0,
        {
            "name": clean_name,
            "created_at": timestamp,
            "updated_at": timestamp,
            "config": normalized_config,
        },
    )
    state["saved"] = saved
    _write_state(path, state)
    return deepcopy(state)


def delete_named_search(name: str, path: Path | None = None) -> dict:
    """Delete a named saved search if present."""
    clean_name = name.strip()
    path = path or get_saved_searches_path()
    state = load_search_history(path)
    state["saved"] = [
        item for item in state["saved"]
        if str(item.get("name", "")).casefold() != clean_name.casefold()
    ]
    _write_state(path, state)
    return deepcopy(state)


def normalize_search_config(config: dict[str, Any]) -> dict:
    """Return a stable, JSON-safe subset of a search config."""
    normalized: dict[str, Any] = {}
    for key in SEARCH_CONFIG_KEYS:
        value = config.get(key)
        if isinstance(value, list):
            normalized[key] = [str(item) for item in value if str(item).strip()]
        elif isinstance(value, bool) or value is None:
            normalized[key] = value
        elif isinstance(value, (int, float)):
            normalized[key] = value
        else:
            normalized[key] = str(value).strip()
    return normalized


def summarize_search_config(config: dict[str, Any]) -> str:
    """Return a concise label for a saved/recent search."""
    parts: list[str] = []
    preset = config.get("preset")
    if preset:
        parts.append(str(preset))

    freshness = config.get("freshness")
    if freshness and freshness != "any":
        parts.append(str(freshness).replace("_", " "))

    strictness = config.get("location_strictness")
    if strictness and strictness != "profile":
        parts.append(str(strictness).replace("_", " "))

    required = config.get("required_skills")
    if required:
        parts.append(f"must: {required}")

    return " | ".join(parts) if parts else "Custom search"


def _empty_state() -> dict:
    return {"version": 1, "recent": [], "saved": []}


def _timestamp(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).isoformat()


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)
