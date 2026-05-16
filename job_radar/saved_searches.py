"""Persistence helpers for saved and recent GUI searches."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from job_radar.json_io import write_json_atomic
from job_radar.paths import get_data_dir


RECENT_SEARCH_LIMIT = 10
SAVED_SEARCHES_FILENAME = "saved_searches.json"
SAVED_SEARCHES_SCHEMA_VERSION = 1
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

    return _normalize_state(data)


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
    review_delta = _format_review_delta(
        stats.get("review") or {},
        previous.get("review") or {},
    )
    if review_delta:
        deltas.append(review_delta)
    changed = [delta for delta in deltas if delta]
    if not changed:
        return "No result movement since the previous run."
    return f"Change: {', '.join(changed)} vs previous."


def format_search_history_detail(item: dict[str, Any]) -> str:
    """Return the two-line search-history detail shown in the GUI."""
    return f"{format_run_summary(item)}\n{format_search_insight(item)}"


def prioritize_changed_searches(
    items: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Return saved/recent searches with changed runs first, preserving ties."""
    indexed_items = list(enumerate(items))
    indexed_items.sort(
        key=lambda pair: (
            -_search_change_score(pair[1]),
            pair[0],
        )
    )
    return [item for _, item in indexed_items[:max(1, limit)]]


def _empty_state() -> dict:
    return {"version": SAVED_SEARCHES_SCHEMA_VERSION, "recent": [], "saved": []}


def _normalize_state(data: dict[str, Any]) -> dict:
    return {
        "version": SAVED_SEARCHES_SCHEMA_VERSION,
        "recent": _normalize_search_items(data.get("recent")),
        "saved": _normalize_search_items(data.get("saved")),
    }


def _normalize_search_items(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        config = item.get("config")
        normalized_item: dict[str, Any] = {
            "name": str(item.get("name") or ""),
            "config": normalize_search_config(config if isinstance(config, dict) else {}),
        }
        for key in ("created_at", "updated_at", "last_run_at"):
            if item.get(key):
                normalized_item[key] = str(item[key])
        if item.get("run_count") is not None:
            normalized_item["run_count"] = _coerce_int(item.get("run_count"))
        for key in ("last_result_stats", "previous_result_stats"):
            stats = item.get(key)
            if isinstance(stats, dict):
                normalized_item[key] = _normalize_run_stats(stats)
                review = stats.get("review")
                if isinstance(review, dict):
                    normalized_item[key]["review"] = _normalize_review_counts(review)
        normalized.append(normalized_item)
    return normalized


def _timestamp(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).isoformat()


def _normalize_run_stats(stats: dict[str, Any] | None) -> dict[str, int]:
    stats = stats or {}
    return {
        "total": _coerce_int(stats.get("total")),
        "new": _coerce_int(stats.get("new")),
        "high_score": _coerce_int(stats.get("high_score")),
    }


def _normalize_review_counts(counts: dict[str, Any]) -> dict[str, int]:
    return {
        "shortlisted": _coerce_int(counts.get("shortlisted")),
        "maybe_later": _coerce_int(counts.get("maybe_later")),
        "dismissed": _coerce_int(counts.get("dismissed")),
    }


def _coerce_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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


def _format_review_delta(current: dict[str, Any], previous: dict[str, Any]) -> str:
    parts = [
        _format_stat_delta("shortlisted", current, previous),
        _format_stat_delta("maybe later", current, previous, key="maybe_later"),
        _format_stat_delta("dismissed", current, previous),
    ]
    changed = [part for part in parts if part]
    if not changed:
        return ""
    return f"review: {', '.join(changed)}"


def _search_change_score(item: dict[str, Any]) -> int:
    current = item.get("last_result_stats") or {}
    previous = item.get("previous_result_stats") or {}
    if not current or not previous:
        return 0

    score = (
        abs(int(current.get("total") or 0) - int(previous.get("total") or 0))
        + abs(int(current.get("new") or 0) - int(previous.get("new") or 0)) * 2
        + abs(int(current.get("high_score") or 0) - int(previous.get("high_score") or 0)) * 3
    )
    current_review = current.get("review") or {}
    previous_review = previous.get("review") or {}
    for key in ("shortlisted", "maybe_later", "dismissed"):
        score += abs(int(current_review.get(key) or 0) - int(previous_review.get(key) or 0))
    return score


def _write_state(path: Path, state: dict) -> None:
    write_json_atomic(path, _normalize_state(state))
