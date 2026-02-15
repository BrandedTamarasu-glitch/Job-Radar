"""Worker thread module for non-blocking GUI operations.

Implements thread-safe communication via queue.Queue and cooperative
cancellation via threading.Event. All widget updates MUST happen in the
main GUI thread via queue messages — worker threads never touch widgets.

Provides both mock workers (for testing) and real SearchWorker (for production).
"""

import queue
import threading
import time


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
        - ("search_complete", job_count: int, report_path: str)
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
            from job_radar.sources import fetch_all, generate_manual_urls
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
            def on_source_progress(source_name, current, total, status, job_count):
                """Callback for source-level progress updates."""
                if status == "started":
                    self._queue.put(("source_started", source_name, current, total))
                elif status == "complete":
                    self._queue.put(("source_complete", source_name, current, total, job_count))

            results, dedup_stats = fetch_all(self._profile, on_source_progress=on_source_progress)

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
            sources_searched = [
                "Dice", "HN Hiring", "RemoteOK", "We Work Remotely",
                "Adzuna", "Authentic Jobs", "LinkedIn", "Indeed", "Glassdoor", "USAJobs (Federal)"
            ]

            report_result = generate_report(
                profile=self._profile,
                scored_results=scored,
                manual_urls=manual_urls,
                sources_searched=sources_searched,
                from_date=from_date or "",
                to_date=to_date or "",
                output_dir=str(get_results_dir()),
                tracker_stats=tracker_stats,
                min_score=min_score
            )

            report_path = report_result["html"]
            job_count = len(scored)

            # Step 9: Send completion message
            self._queue.put(("search_complete", job_count, report_path))

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
