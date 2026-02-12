"""Worker thread module for non-blocking GUI operations.

Implements thread-safe communication via queue.Queue and cooperative
cancellation via threading.Event. All widget updates MUST happen in the
main GUI thread via queue messages — worker threads never touch widgets.

This module will be replaced by real search workers in Phase 29.
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
