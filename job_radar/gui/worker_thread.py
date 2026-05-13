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
from pathlib import Path

import requests


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
            from job_radar.sources import (
                fetch_all,
                generate_manual_urls,
                get_automated_source_display_names,
                get_source_display_name,
            )
            from job_radar.scoring import score_job
            from job_radar.report import generate_report
            from job_radar.tracker import mark_seen, get_stats
            from job_radar.search import filter_by_date
            from job_radar.paths import get_results_dir

            # Step 1: Load API credentials
            load_api_credentials()

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 2: Fetch all results with progress callback
            source_runs = {}

            def on_source_progress(source_name, current, total, status, job_count):
                """Callback for source-level progress updates."""
                if status == "started":
                    source_runs.setdefault(source_name, {
                        "name": source_name,
                        "job_count": 0,
                        "warning_count": 0,
                    })
                    self._queue.put(("source_started", source_name, current, total))
                elif status == "complete":
                    source_runs[source_name] = {
                        "name": source_name,
                        "job_count": job_count,
                        "warning_count": 0,
                    }
                    self._queue.put(("source_complete", source_name, current, total, job_count))

            results, dedup_stats = fetch_all(self._profile, on_source_progress=on_source_progress)
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
                "sources": list(source_runs.values()),
                "query_failures": dedup_stats.get("query_failures", 0),
                "failed_sources": sorted(set(failed_source_names), key=str.casefold),
                "source_warnings": source_failures,
            }

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 3: Apply date filter if specified
            from_date = self._search_config.get("from_date")
            to_date = self._search_config.get("to_date")
            if from_date and to_date:
                results = filter_by_date(results, from_date, to_date)

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 4: Score all results and filter dealbreakers
            scored = []
            for result in results:
                score = score_job(result, self._profile)
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

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Step 8: Generate report
            manual_urls = generate_manual_urls(self._profile)
            tracker_stats = get_stats()

            # Build sources_searched list (all sources we attempted)
            sources_searched = get_automated_source_display_names()

            report_result = generate_report(
                profile=self._profile,
                scored_results=scored,
                manual_urls=manual_urls,
                sources_searched=sources_searched,
                from_date=from_date or "",
                to_date=to_date or "",
                output_dir=str(get_results_dir()),
                tracker_stats=tracker_stats,
                min_score=min_score,
                source_failures=source_failures,
            )

            report_path = report_result["html"]
            job_count = len(scored)

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
