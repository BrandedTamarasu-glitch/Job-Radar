"""Cross-run job tracking — dedup, application status, and trend stats.

Stores seen jobs and application statuses in a JSON file alongside results.
"""

import json
import logging
import os
from datetime import date, datetime

log = logging.getLogger(__name__)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TRACKER_PATH = os.path.join(_SCRIPT_DIR, "results", "tracker.json")


def _load_tracker() -> dict:
    """Load tracker data from disk."""
    if not os.path.exists(_TRACKER_PATH):
        return {"seen_jobs": {}, "applications": {}, "run_history": []}
    try:
        with open(_TRACKER_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Failed to load tracker: %s", e)
        return {"seen_jobs": {}, "applications": {}, "run_history": []}


def _save_tracker(data: dict):
    """Save tracker data to disk."""
    os.makedirs(os.path.dirname(_TRACKER_PATH), exist_ok=True)
    try:
        with open(_TRACKER_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        log.warning("Failed to save tracker: %s", e)


def job_key(title: str, company: str) -> str:
    """Generate a stable key for dedup."""
    return f"{title.lower().strip()}||{company.lower().strip()}"


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
        else:
            r["is_new"] = True
            r["first_seen"] = today
            seen[key] = {
                "first_seen": today,
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


def update_application_status(title: str, company: str, status: str):
    """Update application status for a job.

    Status values: 'applied', 'skipped', 'interviewing', 'rejected', 'offer'.
    """
    tracker = _load_tracker()
    key = job_key(title, company)
    tracker["applications"][key] = {
        "title": title,
        "company": company,
        "status": status,
        "updated": datetime.now().isoformat(),
    }
    _save_tracker(tracker)


def get_application_status(title: str, company: str) -> str | None:
    """Get application status for a job, or None if not tracked."""
    tracker = _load_tracker()
    key = job_key(title, company)
    entry = tracker["applications"].get(key)
    return entry["status"] if entry else None
