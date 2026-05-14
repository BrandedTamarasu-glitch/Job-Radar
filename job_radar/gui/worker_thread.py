"""Worker thread module for non-blocking GUI operations.

Implements thread-safe communication via queue.Queue and cooperative
cancellation via threading.Event. All widget updates MUST happen in the
main GUI thread via queue messages — worker threads never touch widgets.

Provides both mock workers (for testing) and real SearchWorker (for production).
"""

import hashlib
import queue
import threading
import time
from datetime import date, timedelta
from pathlib import Path

import requests


FRESHNESS_DAY_WINDOWS = {
    "past_24h": 1,
    "past_48h": 2,
    "past_7d": 7,
}


def normalize_source_progress(current: int | float | None, total: int | float | None) -> tuple[int, int]:
    """Clamp source progress counters to a safe display range."""
    try:
        safe_total = int(total or 0)
    except (TypeError, ValueError):
        safe_total = 0
    safe_total = max(1, safe_total)

    try:
        safe_current = int(current or 0)
    except (TypeError, ValueError):
        safe_current = 0
    safe_current = min(max(0, safe_current), safe_total)
    return safe_current, safe_total


def parse_company_filter(value: str | list[str] | None) -> list[str]:
    """Parse comma-separated company filter text into normalized terms."""
    if not value:
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = value
    return [
        item.strip().casefold()
        for item in raw_items
        if item and item.strip()
    ]


def parse_skill_filter(value: str | list[str] | None) -> list[str]:
    """Parse comma-separated skill filter text while preserving display casing."""
    if not value:
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = value
    return [
        item.strip()
        for item in raw_items
        if item and item.strip()
    ]


def apply_preferred_skills(profile: dict, preferred_skills=None) -> dict:
    """Return a profile copy with per-search nice-to-have skills appended."""
    parsed_skills = parse_skill_filter(preferred_skills)
    if not parsed_skills:
        return profile

    search_profile = profile.copy()
    secondary_skills = list(search_profile.get("secondary_skills", []))
    seen = {skill.casefold() for skill in secondary_skills}
    for skill in parsed_skills:
        if skill.casefold() not in seen:
            secondary_skills.append(skill)
            seen.add(skill.casefold())
    search_profile["secondary_skills"] = secondary_skills
    return search_profile


def filter_by_company(results: list, include=None, exclude=None) -> list:
    """Filter jobs by company include/exclude terms."""
    include_terms = parse_company_filter(include)
    exclude_terms = parse_company_filter(exclude)
    if not include_terms and not exclude_terms:
        return results

    filtered = []
    for result in results:
        company = getattr(result, "company", "").casefold()
        if include_terms and not any(term in company for term in include_terms):
            continue
        if exclude_terms and any(term in company for term in exclude_terms):
            continue
        filtered.append(result)
    return filtered


def filter_by_required_skills(results: list, required_skills=None) -> list:
    """Filter jobs that do not contain every required skill."""
    if not required_skills:
        return results

    from job_radar.scoring import missing_required_skills

    return [
        result for result in results
        if not missing_required_skills(result, required_skills)
    ]


def infer_job_arrangement(result) -> str:
    """Infer normalized job arrangement from arrangement/location/description."""
    arrangement = getattr(result, "arrangement", "") or "unknown"
    arrangement = arrangement.strip().casefold()
    if arrangement == "on-site":
        arrangement = "onsite"
    if arrangement in {"remote", "hybrid", "onsite"}:
        return arrangement

    text = " ".join([
        getattr(result, "location", "") or "",
        getattr(result, "description", "") or "",
    ]).casefold()
    if "hybrid" in text:
        return "hybrid"
    if "remote" in text:
        return "remote"
    if "on-site" in text or "onsite" in text or "in-office" in text:
        return "onsite"
    return "unknown"


def filter_by_location_strictness(results: list, strictness: str | None = None) -> list:
    """Apply hard arrangement filtering requested from GUI search controls."""
    if not strictness or strictness == "profile":
        return results

    filtered = []
    for result in results:
        arrangement = infer_job_arrangement(result)
        if strictness == "remote_only" and arrangement == "remote":
            filtered.append(result)
        elif strictness == "remote_or_hybrid" and arrangement in {"remote", "hybrid"}:
            filtered.append(result)
        elif strictness == "hybrid_only" and arrangement == "hybrid":
            filtered.append(result)
        elif strictness == "onsite_only" and arrangement == "onsite":
            filtered.append(result)
        elif strictness == "exclude_onsite" and arrangement != "onsite":
            filtered.append(result)
    return filtered


def resolve_date_filter(search_config: dict, today: date | None = None) -> tuple[str | None, str | None]:
    """Resolve GUI freshness/custom settings into date-filter boundaries."""
    from_date = search_config.get("from_date")
    to_date = search_config.get("to_date")
    if from_date and to_date:
        return from_date, to_date

    freshness = search_config.get("freshness") or "any"
    days = FRESHNESS_DAY_WINDOWS.get(freshness)
    if days is None:
        return None, None

    today = today or date.today()
    return (today - timedelta(days=days)).isoformat(), today.isoformat()


class MockSearchWorker:
    """Simulates a long-running search operation for threading validation.

    Communicates with GUI via queue.Queue. Supports cancellation via
    threading.Event. Will be replaced by real SearchWorker in Phase 29.
    """

    def __init__(self, result_queue: queue.Queue, stop_event: threading.Event):
        """Initialize worker with communication queue and stop event.

        Args:
            result_queue: Queue for sending messages to GUI thread
            stop_event: Event for cooperative cancellation
        """
        self._queue = result_queue
        self._stop_event = stop_event
        self._sources = ["Dice", "HN Hiring", "RemoteOK", "We Work Remotely", "Adzuna"]

    def run(self):
        """Execute mock search operation (runs in worker thread).

        Sends progress messages via queue as each source is processed.
        Checks stop_event periodically for cancellation.
        Simulates 12.5+ seconds of work (5 sources x 2.5s each).
        """
        try:
            total_sources = len(self._sources)

            for idx, source in enumerate(self._sources):
                # Check for cancellation before starting source
                if self._stop_event.is_set():
                    self._queue.put(("cancelled",))
                    return

                # Send progress update
                self._queue.put(("progress", source, idx + 1, total_sources))

                # Simulate network fetch
                time.sleep(2.5)

                # Check for cancellation after fetch
                if self._stop_event.is_set():
                    self._queue.put(("cancelled",))
                    return

            # All sources complete
            self._queue.put(("complete", total_sources))

        except Exception as e:
            # Send error to GUI
            self._queue.put(("error", str(e)))

    def cancel(self):
        """Request cancellation of the worker operation."""
        self._stop_event.set()


class MockErrorWorker:
    """Simulates a worker that encounters an error during operation.

    Used for testing error dialog handling in the GUI.
    """

    def __init__(self, result_queue: queue.Queue, stop_event: threading.Event):
        """Initialize error worker with communication queue and stop event.

        Args:
            result_queue: Queue for sending messages to GUI thread
            stop_event: Event for cooperative cancellation
        """
        self._queue = result_queue
        self._stop_event = stop_event
        self._sources = ["Dice", "HN Hiring", "RemoteOK", "We Work Remotely", "Adzuna"]

    def run(self):
        """Execute mock search that fails after 2 sources."""
        try:
            total_sources = len(self._sources)

            for idx, source in enumerate(self._sources):
                # Check for cancellation
                if self._stop_event.is_set():
                    self._queue.put(("cancelled",))
                    return

                # Send progress update
                self._queue.put(("progress", source, idx + 1, total_sources))

                # Simulate network fetch
                time.sleep(1.0)

                # Fail after 2 sources
                if idx == 1:
                    raise ConnectionError("Simulated network error: Connection refused")

        except Exception as e:
            # Send error to GUI
            self._queue.put(("error", str(e)))

    def cancel(self):
        """Request cancellation of the worker operation."""
        self._stop_event.set()


def create_mock_worker(result_queue: queue.Queue):
    """Create a mock search worker with thread.

    Convenience function that sets up the worker and thread with
    proper configuration (daemon=True for clean exit).

    Args:
        result_queue: Queue for worker to send messages to GUI

    Returns:
        Tuple of (worker, thread). Caller must call thread.start().
    """
    stop_event = threading.Event()
    worker = MockSearchWorker(result_queue, stop_event)
    thread = threading.Thread(target=worker.run, daemon=True)
    return worker, thread


def create_mock_error_worker(result_queue: queue.Queue):
    """Create a mock error worker with thread for error testing.

    Args:
        result_queue: Queue for worker to send messages to GUI

    Returns:
        Tuple of (worker, thread). Caller must call thread.start().
    """
    stop_event = threading.Event()
    worker = MockErrorWorker(result_queue, stop_event)
    thread = threading.Thread(target=worker.run, daemon=True)
    return worker, thread


class SearchWorker:
    """Real search worker that executes the full job search pipeline.

    Runs the complete search flow: fetch -> filter -> score -> track -> report.
    Communicates with GUI via queue messages. Supports cooperative cancellation.
    Handles partial source failures gracefully (fetch_all logs and continues).

    Queue message protocol:
        - ("source_started", source_name: str, current: int, total: int)
        - ("source_complete", source_name: str, current: int, total: int, job_count: int)
        - ("search_complete", job_count: int, report_path: str, summary: dict)
        - ("cancelled",)
        - ("error", message: str)
    """

    def __init__(
        self,
        result_queue: queue.Queue,
        stop_event: threading.Event,
        profile: dict,
        search_config: dict
    ):
        """Initialize search worker.

        Args:
            result_queue: Queue for sending messages to GUI thread
            stop_event: Event for cooperative cancellation
            profile: Candidate profile dict
            search_config: Search configuration dict with keys:
                - from_date: str|None
                - to_date: str|None
                - min_score: float
                - new_only: bool
        """
        self._queue = result_queue
        self._stop_event = stop_event
        self._profile = profile
        self._search_config = search_config

    def run(self):
        """Execute the full search pipeline (runs in worker thread).

        Pipeline: fetch_all -> date filter -> score -> dealbreaker filter ->
                 mark_seen -> new_only filter -> min_score filter -> report.

        Sends progress messages via queue. Checks stop_event for cancellation.
        """
        try:
            # Lazy imports to avoid circular dependencies and keep module importable
            from job_radar.api_config import load_api_credentials
            from job_radar.search_presets import apply_search_preset
            from job_radar.sources import (
                fetch_all,
                generate_manual_urls,
                get_automated_source_display_names,
                get_manual_source_display_names,
                get_selected_source_display_names,
                get_source_display_name,
            )
            from job_radar.scoring import score_job
            from job_radar.report import generate_report
            from job_radar.tracker import (
                filter_scored_by_application_status,
                get_stats,
                mark_seen,
                record_source_health,
            )
            from job_radar.search import filter_by_date
            from job_radar.paths import get_results_dir

            search_profile = apply_search_preset(
                self._profile,
                self._search_config.get("preset"),
            )
            search_profile = apply_preferred_skills(
                search_profile,
                self._search_config.get("preferred_skills"),
            )

            # Step 1: Load API credentials
            load_api_credentials()

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 2: Fetch all results with progress callback
            source_runs = {}

            def on_source_progress(source_name, current, total, status, job_count):
                """Callback for source-level progress updates."""
                current, total = normalize_source_progress(current, total)
                if status == "started":
                    started_at = time.monotonic()
                    source_runs.setdefault(source_name, {
                        "name": source_name,
                        "job_count": 0,
                        "warning_count": 0,
                    })
                    source_runs[source_name]["started_at"] = started_at
                    self._queue.put(("source_started", source_name, current, total))
                elif status == "complete":
                    started_at = source_runs.get(source_name, {}).get("started_at")
                    duration_seconds = (
                        round(time.monotonic() - started_at, 3)
                        if started_at is not None
                        else None
                    )
                    source_runs[source_name] = {
                        "name": source_name,
                        "job_count": job_count,
                        "warning_count": 0,
                        "duration_seconds": duration_seconds,
                    }
                    self._queue.put(("source_complete", source_name, current, total, job_count))

            selected_sources = (
                self._search_config["selected_sources"]
                if "selected_sources" in self._search_config
                else None
            )
            results, dedup_stats = fetch_all(
                search_profile,
                on_source_progress=on_source_progress,
                selected_sources=selected_sources,
                cancellation_event=self._stop_event,
            )
            source_failures = dedup_stats.get("query_failure_details") or []
            failed_source_names = [
                get_source_display_name(failure.get("source", "unknown"))
                for failure in source_failures
            ]
            for source_name in failed_source_names:
                source_runs.setdefault(source_name, {
                    "name": source_name,
                    "job_count": 0,
                    "warning_count": 0,
                })
                source_runs[source_name]["warning_count"] += 1

            run_summary = {
                "sources": [
                    {
                        key: value
                        for key, value in source.items()
                        if key != "started_at"
                    }
                    for source in source_runs.values()
                ],
                "query_failures": dedup_stats.get("query_failures", 0),
                "failed_sources": sorted(set(failed_source_names), key=str.casefold),
                "source_warnings": source_failures,
                "cache_stats": dedup_stats.get("cache_stats", {}),
            }

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 3: Apply date filter if specified
            from_date, to_date = resolve_date_filter(self._search_config)
            if from_date and to_date:
                results = filter_by_date(results, from_date, to_date)

            results = filter_by_company(
                results,
                include=self._search_config.get("include_companies"),
                exclude=self._search_config.get("exclude_companies"),
            )
            results = filter_by_required_skills(
                results,
                self._search_config.get("required_skills"),
            )
            results = filter_by_location_strictness(
                results,
                self._search_config.get("location_strictness"),
            )

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 4: Score all results and filter dealbreakers
            scored = []
            for result in results:
                score = score_job(result, search_profile)
                # Filter out dealbreakers
                if not score.get("dealbreaker"):
                    scored.append({
                        "job": result,
                        "score": score
                    })

            # Sort by score descending
            scored.sort(key=lambda x: x["score"]["overall"], reverse=True)

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 5: Mark seen/new
            scored = mark_seen(scored)

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 6: Apply new_only filter
            if self._search_config.get("new_only", False):
                scored = [r for r in scored if r.get("is_new", True)]

            # Step 7: Apply min_score filter
            min_score = self._search_config.get("min_score", 2.8)
            scored = [r for r in scored if r["score"]["overall"] >= min_score]
            if self._search_config.get("hide_rejected_skipped", False):
                scored = filter_scored_by_application_status(scored, {"rejected", "skipped"})

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 8: Generate report
            selected_manual_sources = (
                self._search_config["selected_manual_sources"]
                if "selected_manual_sources" in self._search_config
                else None
            )
            manual_urls = generate_manual_urls(
                search_profile,
                selected_manual_sources=selected_manual_sources,
            )
            record_source_health(run_summary)
            tracker_stats = get_stats()

            # Build sources_searched list (all sources we attempted)
            automated_sources_searched = (
                get_selected_source_display_names(selected_sources)
                if selected_sources
                else get_automated_source_display_names()
            )
            sources_searched = automated_sources_searched + get_manual_source_display_names(
                selected_manual_sources,
            )

            report_result = generate_report(
                profile=search_profile,
                scored_results=scored,
                manual_urls=manual_urls,
                sources_searched=sources_searched,
                from_date=from_date or "",
                to_date=to_date or "",
                output_dir=str(get_results_dir()),
                tracker_stats=tracker_stats,
                min_score=min_score,
                source_failures=source_failures,
                source_warnings=dedup_stats.get("slow_query_warnings"),
            )

            report_path = report_result["html"]
            job_count = len(scored)
            run_summary["result_stats"] = report_result.get("stats", {})

            # Step 9: Send completion message
            self._queue.put(("search_complete", job_count, report_path, run_summary))

        except Exception as e:
            # Send error to GUI
            self._queue.put(("error", str(e)))

    def cancel(self):
        """Request cancellation of the search operation."""
        self._stop_event.set()


def create_search_worker(result_queue: queue.Queue, profile: dict, search_config: dict):
    """Create a real search worker with thread.

    Convenience function that sets up the worker and thread with
    proper configuration (daemon=True for clean exit).

    Args:
        result_queue: Queue for worker to send messages to GUI
        profile: Candidate profile dict
        search_config: Search configuration dict from SearchControls.get_config()

    Returns:
        Tuple of (worker, thread). Caller must call thread.start().
    """
    stop_event = threading.Event()
    worker = SearchWorker(result_queue, stop_event, profile, search_config)
    thread = threading.Thread(target=worker.run, daemon=True)
    return worker, thread


class DownloadWorker:
    """Downloads installer file with streaming, progress updates, and SHA256 verification.

    Communicates with GUI via queue.Queue. Supports cooperative cancellation via
    threading.Event. Deletes partial files on cancellation. Verifies SHA256 digest
    after download (gracefully skips if digest is None).

    Queue message protocol:
        - ("download_progress", downloaded: int, total_size: int)
        - ("download_complete", dest_path: str)
        - ("download_cancelled",)
        - ("download_failed", error_message: str)
    """

    def __init__(
        self,
        result_queue: queue.Queue,
        stop_event: threading.Event,
        asset_url: str,
        asset_digest: str | None,
        dest_path: str
    ):
        """Initialize download worker.

        Args:
            result_queue: Queue for sending messages to GUI thread
            stop_event: Event for cooperative cancellation
            asset_url: URL of the installer file to download
            asset_digest: SHA256 digest (with optional "sha256:" prefix) or None
            dest_path: Destination file path for downloaded installer
        """
        self._queue = result_queue
        self._stop_event = stop_event
        self._asset_url = asset_url
        self._asset_digest = asset_digest
        self._dest_path = dest_path

    def run(self):
        """Execute the download operation (runs in worker thread).

        Downloads file in 8KB chunks with progress updates every ~100KB.
        Checks stop_event for cancellation and deletes partial file if cancelled.
        Verifies SHA256 digest after download (skips if digest is None).
        """
        try:
            # Step 1: Start streaming download
            response = requests.get(
                self._asset_url,
                stream=True,
                timeout=30,
                headers={"User-Agent": "Job-Radar/auto-update"}
            )
            response.raise_for_status()

            # Step 2: Get total size
            total_size = int(response.headers.get('content-length', 0))

            # Step 3: Download file in chunks
            downloaded = 0
            cancelled = False
            with open(self._dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # Check for cancellation before writing
                    if self._stop_event.is_set():
                        cancelled = True
                        break

                    # Write chunk
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Send progress update every ~100KB
                    if downloaded % (100 * 1024) < 8192:
                        self._queue.put(("download_progress", downloaded, total_size))

            if cancelled:
                # Delete partial file (after closing handle for Windows compat)
                Path(self._dest_path).unlink(missing_ok=True)
                self._queue.put(("download_cancelled",))
                return

            # Send final 100% progress
            self._queue.put(("download_progress", total_size, total_size))

            # Step 4: Verify SHA256 if digest provided
            if self._asset_digest:
                computed_hash = self._compute_sha256(self._dest_path)

                # Extract expected hash (strip "sha256:" prefix if present)
                expected_hash = self._asset_digest
                if expected_hash.startswith("sha256:"):
                    expected_hash = expected_hash[7:]

                if computed_hash.lower() != expected_hash.lower():
                    # Hash mismatch - delete file
                    Path(self._dest_path).unlink(missing_ok=True)
                    self._queue.put((
                        "download_failed",
                        "Hash verification failed — file may be corrupted"
                    ))
                    return
            else:
                # No digest available - skip verification
                import logging
                log = logging.getLogger(__name__)
                log.warning("Asset has no digest field - skipping verification")

            # Step 5: Download complete
            self._queue.put(("download_complete", self._dest_path))

        except Exception as e:
            # Send error to GUI
            self._queue.put(("download_failed", str(e)))

    def _compute_sha256(self, filepath: str) -> str:
        """Compute SHA256 hash of a file.

        Args:
            filepath: Path to file to hash

        Returns:
            Hexadecimal SHA256 digest string
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def cancel(self):
        """Request cancellation of the download operation."""
        self._stop_event.set()


def create_download_worker(
    result_queue: queue.Queue,
    asset_url: str,
    asset_digest: str | None,
    dest_path: str
) -> tuple:
    """Create a download worker with thread.

    Convenience function that sets up the worker and thread with
    proper configuration (daemon=True for clean exit).

    Args:
        result_queue: Queue for worker to send messages to GUI
        asset_url: URL of the installer file to download
        asset_digest: SHA256 digest or None
        dest_path: Destination file path for downloaded installer

    Returns:
        Tuple of (worker, thread). Caller must call thread.start().
    """
    stop_event = threading.Event()
    worker = DownloadWorker(result_queue, stop_event, asset_url, asset_digest, dest_path)
    thread = threading.Thread(target=worker.run, daemon=True)
    return worker, thread
