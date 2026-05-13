"""Cross-run job tracking — dedup, application status, and trend stats.

Stores seen jobs and application statuses in a JSON file alongside results.
"""

import json
import logging
import os
from datetime import date, datetime
from pathlib import Path

from .paths import get_results_dir

log = logging.getLogger(__name__)

_TRACKER_PATH: str | None = None
_LEGACY_TRACKER_PATH = os.path.join(os.getcwd(), "results", "tracker.json")
TRACKER_SEEN_RETENTION_DAYS = 180
TRACKER_SOURCE_HEALTH_RETENTION_RUNS = 90


def _default_tracker_path() -> Path:
    """Return the default tracker path in the platform app data results dir."""
    return get_results_dir() / "tracker.json"


def _tracker_path() -> Path:
    """Return the active tracker path, honoring tests that patch _TRACKER_PATH."""
    return Path(_TRACKER_PATH) if _TRACKER_PATH else _default_tracker_path()


def _read_tracker_file(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _load_tracker() -> dict:
    """Load tracker data from disk."""
    tracker_path = _tracker_path()
    if not tracker_path.exists():
        legacy_path = Path(_LEGACY_TRACKER_PATH)
        if _TRACKER_PATH is None and legacy_path.exists():
            try:
                return _read_tracker_file(legacy_path)
            except (json.JSONDecodeError, OSError) as e:
                log.warning("Failed to load legacy tracker: %s", e)
        return {"seen_jobs": {}, "applications": {}, "run_history": []}
    try:
        return _read_tracker_file(tracker_path)
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Failed to load tracker: %s", e)
        return {"seen_jobs": {}, "applications": {}, "run_history": []}


def _save_tracker(data: dict):
    """Save tracker data to disk."""
    tracker_path = _tracker_path()
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tracker_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        log.warning("Failed to save tracker: %s", e)


def job_key(title: str, company: str) -> str:
    """Generate a stable key for dedup."""
    return f"{title.lower().strip()}||{company.lower().strip()}"


def _parse_iso_date(value: str | None) -> date | None:
    """Parse an ISO date string, returning None for legacy/malformed values."""
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def _prune_old_seen_jobs(
    tracker: dict,
    *,
    today: date | None = None,
    retention_days: int = TRACKER_SEEN_RETENTION_DAYS,
) -> int:
    """Prune stale seen-job entries without application status.

    Entries with application state or malformed dates are retained so pruning
    cannot discard user-managed status data or legacy records we cannot age.
    """
    current_date = today or date.today()
    applications = tracker.get("applications", {})
    seen_jobs = tracker.get("seen_jobs", {})
    pruned_keys = []

    for key, entry in seen_jobs.items():
        if key in applications:
            continue

        seen_date = _parse_iso_date(entry.get("last_seen") or entry.get("first_seen"))
        if seen_date is None:
            continue

        if (current_date - seen_date).days > retention_days:
            pruned_keys.append(key)

    for key in pruned_keys:
        del seen_jobs[key]

    return len(pruned_keys)


def mark_seen(scored_results: list[dict]) -> list[dict]:
    """Mark each result as 'new' or 'seen'. Returns annotated results.

    Also records newly seen jobs in the tracker.
    """
    tracker = _load_tracker()
    seen = tracker["seen_jobs"]
    today = date.today().isoformat()

    for r in scored_results:
        job = r["job"]
        key = job_key(job.title, job.company)
        if key in seen:
            r["is_new"] = False
            r["first_seen"] = seen[key]["first_seen"]
            seen[key]["last_seen"] = today
        else:
            r["is_new"] = True
            r["first_seen"] = today
            seen[key] = {
                "first_seen": today,
                "last_seen": today,
                "title": job.title,
                "company": job.company,
                "source": job.source,
                "score": r["score"]["overall"],
            }

    # Record this run
    tracker["run_history"].append({
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "total_results": len(scored_results),
        "new_results": sum(1 for r in scored_results if r["is_new"]),
    })

    # Keep only last 90 days of run history
    tracker["run_history"] = tracker["run_history"][-90:]
    _prune_old_seen_jobs(tracker)

    _save_tracker(tracker)
    return scored_results


def get_stats() -> dict:
    """Return summary statistics across runs."""
    tracker = _load_tracker()
    history = tracker["run_history"]
    total_seen = len(tracker["seen_jobs"])

    recent_runs = history[-7:] if history else []
    avg_new = (
        sum(r.get("new_results", 0) for r in recent_runs) / len(recent_runs)
        if recent_runs
        else 0
    )

    return {
        "total_unique_jobs_seen": total_seen,
        "total_runs": len(history),
        "avg_new_per_run_last_7": round(avg_new, 1),
    }


def record_source_health(
    summary: dict,
    *,
    timestamp: str | None = None,
    retention_runs: int = TRACKER_SOURCE_HEALTH_RETENTION_RUNS,
) -> dict:
    """Persist per-source run health for later diagnostics."""
    tracker = _load_tracker()
    source_health_history = tracker.setdefault("source_health_history", [])
    sources = []
    for source in summary.get("sources", []):
        entry = {
            "name": source.get("name", "Unknown source"),
            "job_count": int(source.get("job_count") or 0),
            "warning_count": int(source.get("warning_count") or 0),
        }
        if source.get("duration_seconds") is not None:
            entry["duration_seconds"] = round(float(source["duration_seconds"]), 3)
        sources.append(entry)

    health_entry = {
        "timestamp": timestamp or datetime.now().isoformat(),
        "sources": sources,
        "query_failures": int(summary.get("query_failures") or 0),
        "failed_sources": list(summary.get("failed_sources") or []),
        "total_jobs": sum(source["job_count"] for source in sources),
    }
    if summary.get("source_warnings") is not None:
        health_entry["source_warnings"] = list(summary.get("source_warnings") or [])

    source_health_history.append(health_entry)
    tracker["source_health_history"] = source_health_history[-retention_runs:]
    _save_tracker(tracker)
    return health_entry


def get_source_health_history(limit: int | None = None) -> list[dict]:
    """Return persisted source health runs in chronological order."""
    tracker = _load_tracker()
    history = tracker.get("source_health_history", [])
    if limit is None:
        return list(history)
    return list(history[-limit:])


def update_application_status(
    title: str,
    company: str,
    status: str,
    *,
    notes: str | None = None,
    next_action: str | None = None,
    next_action_date: str | None = None,
):
    """Update application status for a job.

    Status values: 'applied', 'skipped', 'interviewing', 'rejected', 'offer'.
    """
    tracker = _load_tracker()
    key = job_key(title, company)
    existing = tracker["applications"].get(key, {})
    entry = {
        **existing,
        "title": title,
        "company": company,
        "status": status,
        "updated": datetime.now().isoformat(),
    }
    if notes is not None:
        entry["notes"] = notes
    if next_action is not None:
        entry["next_action"] = next_action
    if next_action_date is not None:
        entry["next_action_date"] = next_action_date

    tracker["applications"][key] = entry
    _save_tracker(tracker)


def get_application_status(title: str, company: str) -> str | None:
    """Get application status for a job, or None if not tracked."""
    tracker = _load_tracker()
    key = job_key(title, company)
    entry = tracker["applications"].get(key)
    return entry.get("status") if entry else None


def update_application_details(
    title: str,
    company: str,
    *,
    notes: str | None = None,
    next_action: str | None = None,
    next_action_date: str | None = None,
):
    """Update application notes and next-action metadata without changing status."""
    tracker = _load_tracker()
    key = job_key(title, company)
    existing = tracker["applications"].get(key, {})
    entry = {
        **existing,
        "title": title,
        "company": company,
        "updated": datetime.now().isoformat(),
    }
    if notes is not None:
        entry["notes"] = notes
    if next_action is not None:
        entry["next_action"] = next_action
    if next_action_date is not None:
        entry["next_action_date"] = next_action_date

    tracker["applications"][key] = entry
    _save_tracker(tracker)


def get_application_entry(title: str, company: str) -> dict | None:
    """Get full application tracker entry for a job, or None if untracked."""
    tracker = _load_tracker()
    key = job_key(title, company)
    entry = tracker["applications"].get(key)
    return entry.copy() if entry else None


def get_all_application_statuses() -> dict:
    """Get all application statuses from tracker.

    Returns the entire applications dict from tracker.json.
    Avoids repeated file reads when embedding status for all jobs.
    """
    tracker = _load_tracker()
    return tracker.get("applications", {})


def filter_scored_by_application_status(
    scored_results: list[dict],
    hidden_statuses: set[str] | tuple[str, ...] | list[str],
    *,
    applications: dict | None = None,
) -> list[dict]:
    """Remove scored jobs whose tracked application status should be hidden."""
    if not hidden_statuses:
        return scored_results

    hidden = {status.casefold() for status in hidden_statuses}
    application_entries = applications if applications is not None else get_all_application_statuses()
    filtered = []
    for result in scored_results:
        job = result["job"]
        entry = application_entries.get(job_key(job.title, job.company)) or {}
        status = (entry.get("status") or "").casefold()
        if status in hidden:
            continue
        filtered.append(result)
    return filtered
