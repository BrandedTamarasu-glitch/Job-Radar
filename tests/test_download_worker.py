"""Tests for DownloadWorker — streaming, cancellation, SHA256 verification."""

import queue
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from job_radar.gui.worker_thread import DownloadWorker, create_download_worker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def result_queue():
    """Queue for worker messages."""
    return queue.Queue()


@pytest.fixture
def stop_event():
    """Threading event for cancellation."""
    return threading.Event()


@pytest.fixture
def temp_download_path(tmp_path):
    """Temporary file path for download destination."""
    return str(tmp_path / "installer.exe")


# ---------------------------------------------------------------------------
# SHA256 computation tests
# ---------------------------------------------------------------------------


def test_compute_sha256_known_content(tmp_path, result_queue, stop_event):
    """_compute_sha256 returns correct hash for known content."""
    # Create temp file with known content
    test_file = tmp_path / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)

    # Known SHA256 hash of "Hello, World!"
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

    worker = DownloadWorker(result_queue, stop_event, "http://example.com", None, str(test_file))
    computed = worker._compute_sha256(str(test_file))

    assert computed == expected_hash


# ---------------------------------------------------------------------------
# Cancellation tests
# ---------------------------------------------------------------------------


def test_cancel_sets_stop_event(result_queue, stop_event, temp_download_path):
    """cancel() sets the stop_event."""
    worker = DownloadWorker(result_queue, stop_event, "http://example.com", None, temp_download_path)

    assert not stop_event.is_set()
    worker.cancel()
    assert stop_event.is_set()


# ---------------------------------------------------------------------------
# Download tests with mocked requests
# ---------------------------------------------------------------------------


@patch("job_radar.gui.worker_thread.requests.get")
def test_download_success_with_progress(mock_get, result_queue, stop_event, temp_download_path):
    """DownloadWorker downloads file with progress updates and completion message."""
    # Mock response with 3 chunks
    chunk1 = b"A" * 8192
    chunk2 = b"B" * 8192
    chunk3 = b"C" * 4096

    mock_response = Mock()
    mock_response.headers.get.return_value = str(len(chunk1) + len(chunk2) + len(chunk3))
    mock_response.iter_content.return_value = [chunk1, chunk2, chunk3]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    worker = DownloadWorker(
        result_queue,
        stop_event,
        "http://example.com/installer.exe",
        None,  # No digest
        temp_download_path
    )

    worker.run()

    # Verify file written
    downloaded_content = Path(temp_download_path).read_bytes()
    assert downloaded_content == chunk1 + chunk2 + chunk3

    # Verify queue messages
    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    # Should have at least final progress and completion
    assert any(msg[0] == "download_progress" for msg in messages)
    assert messages[-1][0] == "download_complete"
    assert messages[-1][1] == temp_download_path


@patch("job_radar.gui.worker_thread.requests.get")
def test_download_cancellation_mid_download(mock_get, result_queue, stop_event, temp_download_path):
    """DownloadWorker cancels mid-download and deletes partial file."""
    chunk1 = b"A" * 8192
    chunk2 = b"B" * 8192

    # Custom iterator that sets stop_event after first chunk
    def chunk_generator():
        yield chunk1
        stop_event.set()  # Cancel after first chunk
        yield chunk2

    mock_response = Mock()
    mock_response.headers.get.return_value = str(len(chunk1) + len(chunk2))
    mock_response.iter_content.return_value = chunk_generator()
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    worker = DownloadWorker(
        result_queue,
        stop_event,
        "http://example.com/installer.exe",
        None,
        temp_download_path
    )

    worker.run()

    # Verify partial file was deleted
    assert not Path(temp_download_path).exists()

    # Verify cancellation message
    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    assert any(msg[0] == "download_cancelled" for msg in messages)


@patch("job_radar.gui.worker_thread.requests.get")
def test_download_sha256_mismatch(mock_get, result_queue, stop_event, temp_download_path):
    """DownloadWorker detects SHA256 mismatch and deletes file."""
    chunk = b"A" * 1024

    mock_response = Mock()
    mock_response.headers.get.return_value = str(len(chunk))
    mock_response.iter_content.return_value = [chunk]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Provide wrong digest
    wrong_digest = "sha256:0000000000000000000000000000000000000000000000000000000000000000"

    worker = DownloadWorker(
        result_queue,
        stop_event,
        "http://example.com/installer.exe",
        wrong_digest,
        temp_download_path
    )

    worker.run()

    # Verify file was deleted
    assert not Path(temp_download_path).exists()

    # Verify failure message
    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    assert any(msg[0] == "download_failed" for msg in messages)
    assert any("Hash verification" in msg[1] for msg in messages if msg[0] == "download_failed")


@patch("job_radar.gui.worker_thread.requests.get")
def test_download_null_digest_skips_verification(mock_get, result_queue, stop_event, temp_download_path):
    """DownloadWorker skips verification when digest is None."""
    chunk = b"A" * 1024

    mock_response = Mock()
    mock_response.headers.get.return_value = str(len(chunk))
    mock_response.iter_content.return_value = [chunk]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    worker = DownloadWorker(
        result_queue,
        stop_event,
        "http://example.com/installer.exe",
        None,  # No digest
        temp_download_path
    )

    worker.run()

    # Verify file exists (not deleted)
    assert Path(temp_download_path).exists()

    # Verify completion message (not failure)
    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    assert any(msg[0] == "download_complete" for msg in messages)
    assert not any(msg[0] == "download_failed" for msg in messages)


@patch("job_radar.gui.worker_thread.requests.get")
def test_download_network_error(mock_get, result_queue, stop_event, temp_download_path):
    """DownloadWorker handles network errors gracefully."""
    import requests
    mock_get.side_effect = requests.ConnectionError("Connection refused")

    worker = DownloadWorker(
        result_queue,
        stop_event,
        "http://example.com/installer.exe",
        None,
        temp_download_path
    )

    worker.run()

    # Verify failure message
    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    assert any(msg[0] == "download_failed" for msg in messages)


# ---------------------------------------------------------------------------
# Factory function tests
# ---------------------------------------------------------------------------


def test_create_download_worker_returns_worker_and_thread(result_queue, temp_download_path):
    """create_download_worker returns worker and thread tuple."""
    worker, thread = create_download_worker(
        result_queue,
        "http://example.com/installer.exe",
        None,
        temp_download_path
    )

    assert isinstance(worker, DownloadWorker)
    assert isinstance(thread, threading.Thread)
    assert thread.daemon is True


@patch("job_radar.gui.worker_thread.requests.get")
def test_create_download_worker_thread_runs(mock_get, result_queue, temp_download_path):
    """create_download_worker thread executes worker.run()."""
    chunk = b"A" * 1024

    mock_response = Mock()
    mock_response.headers.get.return_value = str(len(chunk))
    mock_response.iter_content.return_value = [chunk]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    worker, thread = create_download_worker(
        result_queue,
        "http://example.com/installer.exe",
        None,
        temp_download_path
    )

    thread.start()
    thread.join(timeout=2)

    # Verify completion message
    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    assert any(msg[0] == "download_complete" for msg in messages)


# ---------------------------------------------------------------------------
# SHA256 verification tests
# ---------------------------------------------------------------------------


@patch("job_radar.gui.worker_thread.requests.get")
def test_download_sha256_success_with_prefix(mock_get, result_queue, stop_event, temp_download_path):
    """DownloadWorker handles digest with 'sha256:' prefix correctly."""
    chunk = b"Hello, World!"

    mock_response = Mock()
    mock_response.headers.get.return_value = str(len(chunk))
    mock_response.iter_content.return_value = [chunk]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Correct digest with prefix
    correct_digest = "sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

    worker = DownloadWorker(
        result_queue,
        stop_event,
        "http://example.com/installer.exe",
        correct_digest,
        temp_download_path
    )

    worker.run()

    # Verify file exists
    assert Path(temp_download_path).exists()

    # Verify completion message (not failure)
    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    assert any(msg[0] == "download_complete" for msg in messages)
    assert not any(msg[0] == "download_failed" for msg in messages)


@patch("job_radar.gui.worker_thread.requests.get")
def test_download_sha256_success_without_prefix(mock_get, result_queue, stop_event, temp_download_path):
    """DownloadWorker handles digest without prefix correctly."""
    chunk = b"Hello, World!"

    mock_response = Mock()
    mock_response.headers.get.return_value = str(len(chunk))
    mock_response.iter_content.return_value = [chunk]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Correct digest without prefix
    correct_digest = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

    worker = DownloadWorker(
        result_queue,
        stop_event,
        "http://example.com/installer.exe",
        correct_digest,
        temp_download_path
    )

    worker.run()

    # Verify file exists
    assert Path(temp_download_path).exists()

    # Verify completion message (not failure)
    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    assert any(msg[0] == "download_complete" for msg in messages)
    assert not any(msg[0] == "download_failed" for msg in messages)
