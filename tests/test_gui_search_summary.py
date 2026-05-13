"""Tests for GUI search completion summaries."""

import queue
import threading
from unittest.mock import patch

from job_radar.gui.search_summary import (
    cancellation_message,
    completion_message,
    error_message,
    source_summary_lines,
    source_warning_message,
    zero_result_lines,
)
from job_radar.gui.worker_thread import SearchWorker


def test_completion_message_handles_zero_one_and_many():
    """Completion copy is grammatically useful for common counts."""
    assert completion_message(0) == "Search complete. No matching jobs found."
    assert completion_message(1) == "Search complete! 1 job found"
    assert completion_message(2) == "Search complete! 2 jobs found"


def test_source_warning_message_summarizes_partial_failures():
    """Partial source failures get concise visible GUI copy."""
    summary = {
        "query_failures": 2,
        "failed_sources": ["Dice", "RemoteOK"],
    }

    message = source_warning_message(summary)

    assert message is not None
    assert "2 source queries failed" in message
    assert "Dice, RemoteOK" in message


def test_source_summary_lines_include_jobs_and_warnings():
    """Per-source summary lines include counts and warning counts."""
    summary = {
        "sources": [
            {"name": "Dice", "job_count": 1, "warning_count": 0},
            {"name": "RemoteOK", "job_count": 0, "warning_count": 2},
        ]
    }

    assert source_summary_lines(summary) == [
        "Dice: 1 job",
        "RemoteOK: 0 jobs (2 query warnings)",
    ]


def test_zero_result_lines_reuse_next_action_guidance():
    """Zero-result GUI state has concrete next actions."""
    assert zero_result_lines(3) == []
    lines = zero_result_lines(0)
    assert lines
    assert any("minimum score" in line for line in lines)


def test_interruption_messages_explain_report_state():
    """Cancel and error messages explain whether a report exists."""
    assert "No new report was generated" in cancellation_message()
    assert "before a report could be generated" in error_message("network down")
    assert "network down" in error_message("network down")


def test_clear_cache_settings_handler_updates_status_label(tmp_path):
    """Settings cache clear action reports the removed file count."""
    from job_radar.gui.main_window import MainWindow

    class StatusLabel:
        def __init__(self):
            self.text = ""

        def configure(self, **kwargs):
            self.text = kwargs["text"]

    window = type("Window", (), {"_cache_status_label": StatusLabel()})()

    with patch("job_radar.cache.get_data_dir", return_value=tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "response.json").write_text("{}", encoding="utf-8")

        MainWindow._on_clear_cache(window)

    assert "Removed 1 cached response file" in window._cache_status_label.text


def test_search_worker_emits_completion_summary(tmp_path):
    """SearchWorker includes source warnings and per-source counts on completion."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }

    def fake_fetch_all(_profile, on_source_progress=None):
        on_source_progress("Dice", 1, 2, "started", 0)
        on_source_progress("Dice", 1, 2, "complete", 0)
        on_source_progress("RemoteOK", 2, 2, "started", 0)
        on_source_progress("RemoteOK", 2, 2, "complete", 3)
        return [], {
            "query_failures": 1,
            "failed_sources": ["dice"],
            "query_failure_details": [
                {"source": "dice", "query": "Backend Engineer", "error": "timeout"}
            ],
        }

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", return_value=[]):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["Dice", "RemoteOK"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=lambda scored: scored):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.report.generate_report", return_value={"html": str(tmp_path / "jobs.html")}):
                                worker = SearchWorker(result_queue, stop_event, profile, {"min_score": 2.8})
                                worker.run()

    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    complete = [message for message in messages if message[0] == "search_complete"][0]
    assert complete[1] == 0
    assert complete[2].endswith("jobs.html")
    summary = complete[3]
    assert summary["query_failures"] == 1
    assert summary["failed_sources"] == ["Dice"]
    assert summary["sources"] == [
        {"name": "Dice", "job_count": 0, "warning_count": 1},
        {"name": "RemoteOK", "job_count": 3, "warning_count": 0},
    ]
