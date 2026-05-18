"""View-model helpers for local data maintenance summaries."""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from job_radar import __version__


@dataclass(frozen=True)
class LocalMaintenanceSummary:
    """Display-ready counts for local Job Radar state."""

    total_bytes: int
    cache_files: int
    cache_bytes: int
    tracker_applications: int
    tracker_seen_jobs: int
    source_health_runs: int
    review_jobs: int
    saved_recent: int
    saved_named: int
    suggestions: list[str]


@dataclass(frozen=True)
class FeedbackDiagnosticsSummary:
    """Privacy-safe diagnostics users can share for post-release feedback."""

    app_version: str
    operating_system: str
    local_data_bytes: int
    cache_files: int
    tracker_applications: int
    tracker_seen_jobs: int
    source_health_runs: int
    review_jobs: int
    saved_recent: int
    saved_named: int
    suggestions: list[str]


def build_local_maintenance_summary(
    data_dir: Path,
    results_dir: Path,
) -> LocalMaintenanceSummary:
    """Summarize local app data without leaving the app data tree."""
    data_dir = Path(data_dir)
    results_dir = Path(results_dir)
    cache_dir = data_dir / "cache"
    cache_files, cache_bytes = _directory_file_count_and_size(cache_dir)
    total_bytes = _directory_file_count_and_size(data_dir)[1]

    tracker = _read_json(results_dir / "tracker.json")
    review_state = _read_json(data_dir / "review_state.json")
    saved_searches = _read_json(data_dir / "saved_searches.json")

    tracker_applications = _dict_count(tracker.get("applications"))
    tracker_seen_jobs = _dict_count(tracker.get("seen_jobs"))
    source_health_runs = _list_count(tracker.get("source_health_history"))
    review_jobs = _dict_count(review_state.get("jobs"))
    saved_recent = _list_count(saved_searches.get("recent"))
    saved_named = _list_count(saved_searches.get("saved"))

    suggestions = _maintenance_suggestions(
        cache_files=cache_files,
        cache_bytes=cache_bytes,
        tracker_seen_jobs=tracker_seen_jobs,
        source_health_runs=source_health_runs,
        review_jobs=review_jobs,
        saved_searches=saved_recent + saved_named,
    )

    return LocalMaintenanceSummary(
        total_bytes=total_bytes,
        cache_files=cache_files,
        cache_bytes=cache_bytes,
        tracker_applications=tracker_applications,
        tracker_seen_jobs=tracker_seen_jobs,
        source_health_runs=source_health_runs,
        review_jobs=review_jobs,
        saved_recent=saved_recent,
        saved_named=saved_named,
        suggestions=suggestions,
    )


def build_feedback_diagnostics_summary(
    data_dir: Path,
    results_dir: Path,
    *,
    app_version: str = __version__,
    operating_system: str | None = None,
) -> FeedbackDiagnosticsSummary:
    """Build a privacy-safe diagnostics summary for user feedback."""
    maintenance = build_local_maintenance_summary(data_dir, results_dir)
    return FeedbackDiagnosticsSummary(
        app_version=app_version,
        operating_system=operating_system or platform.platform(),
        local_data_bytes=maintenance.total_bytes,
        cache_files=maintenance.cache_files,
        tracker_applications=maintenance.tracker_applications,
        tracker_seen_jobs=maintenance.tracker_seen_jobs,
        source_health_runs=maintenance.source_health_runs,
        review_jobs=maintenance.review_jobs,
        saved_recent=maintenance.saved_recent,
        saved_named=maintenance.saved_named,
        suggestions=maintenance.suggestions,
    )


def format_local_maintenance_lines(summary: LocalMaintenanceSummary) -> list[str]:
    """Return Settings-ready local maintenance lines."""
    lines = [
        f"Local data: {_format_bytes(summary.total_bytes)} total",
        f"HTTP cache: {summary.cache_files} file(s), {_format_bytes(summary.cache_bytes)}",
        (
            "History: "
            f"{summary.tracker_seen_jobs} seen job(s), "
            f"{summary.tracker_applications} application(s), "
            f"{summary.source_health_runs} source diagnostic run(s)"
        ),
        (
            "Workflow state: "
            f"{summary.review_jobs} reviewed job(s), "
            f"{summary.saved_named} saved search(es), "
            f"{summary.saved_recent} recent search shortcut(s)"
        ),
    ]
    if summary.suggestions:
        lines.extend(f"Suggestion: {suggestion}" for suggestion in summary.suggestions)
    else:
        lines.append("Suggestion: no local maintenance needed right now.")
    return lines


def format_feedback_diagnostics_lines(summary: FeedbackDiagnosticsSummary) -> list[str]:
    """Return a shareable diagnostics summary without private local contents."""
    lines = [
        "Feedback diagnostics (redacted):",
        f"Version: {summary.app_version}",
        f"Operating system: {summary.operating_system}",
        f"Local data size: {_format_bytes(summary.local_data_bytes)}",
        (
            "Workflow counts: "
            f"{summary.tracker_seen_jobs} seen job(s), "
            f"{summary.tracker_applications} application(s), "
            f"{summary.review_jobs} reviewed job(s)"
        ),
        (
            "Search state: "
            f"{summary.saved_named} saved search(es), "
            f"{summary.saved_recent} recent search shortcut(s), "
            f"{summary.source_health_runs} source diagnostic run(s)"
        ),
        f"Cache files: {summary.cache_files}",
    ]
    if summary.suggestions:
        lines.extend(f"Maintenance signal: {suggestion}" for suggestion in summary.suggestions)
    else:
        lines.append("Maintenance signal: none")
    lines.append(
        "Privacy: do not include API keys, profile/resume contents, saved search names, "
        "application notes, tracker records, or local filesystem paths."
    )
    return lines


def local_maintenance_text(data_dir: Path, results_dir: Path) -> str:
    """Return Settings-ready local maintenance summary text."""
    summary = build_local_maintenance_summary(data_dir, results_dir)
    return "\n".join(format_local_maintenance_lines(summary))


def feedback_diagnostics_text(data_dir: Path, results_dir: Path) -> str:
    """Return privacy-safe feedback diagnostics text for Settings."""
    summary = build_feedback_diagnostics_summary(data_dir, results_dir)
    return "\n".join(format_feedback_diagnostics_lines(summary))


def cache_clear_success_message(removed: int, cache_dir: Path) -> str:
    """Return Settings feedback after clearing cached responses."""
    return f"Removed {removed} cached response file(s) from {cache_dir}"


def cache_clear_error_message(error: object) -> str:
    """Return Settings feedback after cache clearing fails."""
    return f"Failed to clear cache: {error}"


def dismissed_review_cleanup_success_message(removed: int) -> str:
    """Return Settings feedback after clearing dismissed review items."""
    return f"Cleared {removed} dismissed review item(s)"


def dismissed_review_cleanup_error_message(error: object) -> str:
    """Return Settings feedback after dismissed review cleanup fails."""
    return f"Dismissed review cleanup failed: {error}"


def app_data_export_success_message(export_path: Path) -> str:
    """Return Settings feedback after app-data export succeeds."""
    return f"Exported app data to {export_path}"


def app_data_export_error_message(error: object) -> str:
    """Return Settings feedback after app-data export fails."""
    return f"Failed to export app data: {error}"


def app_data_bundle_validation_message(
    *,
    is_valid: bool,
    files: list[str],
    errors: list[str],
) -> str:
    """Return Settings feedback after app-data bundle validation."""
    if is_valid:
        file_noun = "file" if len(files) == 1 else "files"
        return f"Bundle is valid: {len(files)} {file_noun} ready to restore"
    return "Bundle validation failed: " + "; ".join(errors)


def _directory_file_count_and_size(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    count = 0
    size = 0
    for item in path.rglob("*"):
        if item.is_file():
            count += 1
            try:
                size += item.stat().st_size
            except OSError:
                continue
    return count, size


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _dict_count(value: Any) -> int:
    return len(value) if isinstance(value, dict) else 0


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _maintenance_suggestions(
    *,
    cache_files: int,
    cache_bytes: int,
    tracker_seen_jobs: int,
    source_health_runs: int,
    review_jobs: int,
    saved_searches: int,
) -> list[str]:
    suggestions = []
    if cache_files >= 100 or cache_bytes >= 50 * 1024 * 1024:
        suggestions.append("clear HTTP cache if source results feel stale or disk use matters")
    if tracker_seen_jobs >= 5000:
        suggestions.append("export app data before pruning or resetting long-running tracker history")
    if source_health_runs >= 20:
        suggestions.append("source diagnostics history is at the retained-run cap")
    if review_jobs >= 500:
        suggestions.append("review queue is large; clear dismissed jobs from reports you no longer need")
    if saved_searches >= 50:
        suggestions.append("remove saved or recent searches you no longer rerun")
    return suggestions


def _format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"
