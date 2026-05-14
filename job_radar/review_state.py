"""Persistent search-result review state for shortlist triage."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from job_radar.paths import get_data_dir
from job_radar.tracker import job_key


REVIEW_STATE_FILENAME = "review_state.json"
REVIEW_STATES = {"shortlisted", "dismissed", "maybe_later"}


def get_review_state_path() -> Path:
    """Return the app-data path for search-result review state."""
    return get_data_dir() / REVIEW_STATE_FILENAME


def load_review_state(path: Path | None = None) -> dict:
    """Load review state, returning an empty valid structure on failure."""
    path = path or get_review_state_path()
    if not path.exists():
        return _empty_state()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_state()

    if not isinstance(data, dict):
        return _empty_state()

    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        jobs = {}

    normalized_jobs = {}
    for key, entry in jobs.items():
        if not isinstance(entry, dict):
            continue
        state = str(entry.get("state") or "").strip()
        if state not in REVIEW_STATES:
            continue
        normalized_jobs[str(key)] = {
            "state": state,
            "title": str(entry.get("title") or ""),
            "company": str(entry.get("company") or ""),
            "updated_at": str(entry.get("updated_at") or ""),
        }

    return {"version": 1, "jobs": normalized_jobs}


def set_job_review_state(
    title: str,
    company: str,
    state: str,
    *,
    path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Set a job's review state to shortlisted, dismissed, or maybe_later."""
    clean_state = state.strip()
    if clean_state not in REVIEW_STATES:
        raise ValueError(f"Unknown job review state: {state}")

    path = path or get_review_state_path()
    data = load_review_state(path)
    data["jobs"][job_key(title, company)] = {
        "state": clean_state,
        "title": title,
        "company": company,
        "updated_at": _timestamp(now),
    }
    _write_state(path, data)
    return deepcopy(data)


def clear_job_review_state(title: str, company: str, *, path: Path | None = None) -> dict:
    """Remove a job's review state if one exists."""
    path = path or get_review_state_path()
    data = load_review_state(path)
    data["jobs"].pop(job_key(title, company), None)
    _write_state(path, data)
    return deepcopy(data)


def get_job_review_state(title: str, company: str, *, path: Path | None = None) -> str | None:
    """Return a job's persisted review state, if set."""
    data = load_review_state(path)
    entry = data["jobs"].get(job_key(title, company))
    return entry.get("state") if entry else None


def review_state_counts(path: Path | None = None) -> dict[str, int]:
    """Return counts for each supported review state."""
    counts = {state: 0 for state in sorted(REVIEW_STATES)}
    data = load_review_state(path)
    for entry in data["jobs"].values():
        state = entry.get("state")
        if state in counts:
            counts[state] += 1
    return counts


def _empty_state() -> dict:
    return {"version": 1, "jobs": {}}


def _timestamp(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).isoformat()


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)
