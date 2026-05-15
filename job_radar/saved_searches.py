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
    "match_calibration",
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


def record_search_run(
    config: dict[str, Any],
    stats: dict[str, Any] | None,
    path: Path | None = None,
    now: datetime | None = None,
    review_counts: dict[str, Any] | None = None,
) -> dict:
    """Attach last-run metadata to matching recent and saved searches."""
    path = path or get_saved_searches_path()
    state = load_search_history(path)
    normalized_config = normalize_search_config(config)
    timestamp = _timestamp(now)
    run_stats = _normalize_run_stats(stats)
    if review_counts is not None:
        run_stats["review"] = _normalize_review_counts(review_counts)

    for collection_name in ("recent", "saved"):
        for item in state[collection_name]:
            if item.get("config") != normalized_config:
                continue
            if "last_result_stats" in item:
                item["previous_result_stats"] = item["last_result_stats"]
            item["last_run_at"] = timestamp
            item["last_result_stats"] = run_stats
            item["run_count"] = int(item.get("run_count") or 0) + 1

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


def format_run_summary(item: dict[str, Any]) -> str:
    """Return compact last-run metadata for display."""
    run_count = int(item.get("run_count") or 0)
    stats = item.get("last_result_stats") or {}
    if not run_count or not stats:
        return "Not run yet"

    total = int(stats.get("total") or 0)
    new = int(stats.get("new") or 0)
    high_score = int(stats.get("high_score") or 0)
    run_word = "run" if run_count == 1 else "runs"
    delta = _format_total_delta(stats, item.get("previous_result_stats") or {})
    review = _format_review_counts(stats.get("review") or {})
    review_text = f", {review}" if review else ""
    return (
        f"Last run: {total} results{delta}, {new} new, "
        f"{high_score} high-score{review_text} | {run_count} {run_word}"
    )


def format_search_insight(item: dict[str, Any]) -> str:
    """Return a concise previous-run comparison for display."""
    stats = item.get("last_result_stats") or {}
    if not stats:
        return "Comparison starts after the first completed run."

    previous = item.get("previous_result_stats") or {}
    if not previous:
        return "Comparison starts after the next completed run."

    deltas = [
        _format_stat_delta("total", stats, previous),
        _format_stat_delta("new", stats, previous),
        _format_stat_delta("high-score", stats, previous, key="high_score"),
    ]
    changed = [delta for delta in deltas if delta]
    if not changed:
        return "No result movement since the previous run."
    return f"Change: {', '.join(changed)} vs previous."


def _empty_state() -> dict:
    return {"version": 1, "recent": [], "saved": []}


def _timestamp(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).isoformat()


def _normalize_run_stats(stats: dict[str, Any] | None) -> dict[str, int]:
    stats = stats or {}
    return {
        "total": int(stats.get("total") or 0),
        "new": int(stats.get("new") or 0),
        "high_score": int(stats.get("high_score") or 0),
    }


def _normalize_review_counts(counts: dict[str, Any]) -> dict[str, int]:
    return {
        "shortlisted": int(counts.get("shortlisted") or 0),
        "maybe_later": int(counts.get("maybe_later") or 0),
        "dismissed": int(counts.get("dismissed") or 0),
    }


def _format_review_counts(counts: dict[str, Any]) -> str:
    shortlisted = int(counts.get("shortlisted") or 0)
    maybe_later = int(counts.get("maybe_later") or 0)
    dismissed = int(counts.get("dismissed") or 0)
    parts = []
    if shortlisted:
        parts.append(f"{shortlisted} shortlisted")
    if maybe_later:
        parts.append(f"{maybe_later} maybe later")
    if dismissed:
        parts.append(f"{dismissed} dismissed")
    return ", ".join(parts)


def _format_total_delta(current: dict[str, Any], previous: dict[str, Any]) -> str:
    if not previous:
        return ""

    delta = int(current.get("total") or 0) - int(previous.get("total") or 0)
    if delta == 0:
        return ", no change"
    sign = "+" if delta > 0 else ""
    return f", {sign}{delta} vs previous"


def _format_stat_delta(
    label: str,
    current: dict[str, Any],
    previous: dict[str, Any],
    key: str | None = None,
) -> str:
    key = key or label
    delta = int(current.get(key) or 0) - int(previous.get(key) or 0)
    if delta == 0:
        return ""
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta} {label}"


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)
