"""Tests for GUI search completion summaries."""

import queue
import threading
from datetime import date
from unittest.mock import patch

import pytest

from job_radar.gui.search_summary import (
    cache_summary_line,
    cancellation_message,
    completion_message,
    error_message,
    source_summary_lines,
    source_warning_message,
    zero_result_lines,
)
from job_radar.gui.worker_thread import (
    SearchWorker,
    apply_preferred_skills,
    filter_by_company,
    filter_by_location_strictness,
    filter_by_required_skills,
    normalize_source_progress,
    resolve_date_filter,
)
from job_radar.sources import JobResult


@pytest.fixture(autouse=True)
def source_health_recorder():
    """Prevent GUI worker tests from writing source health into real tracker data."""
    with patch("job_radar.tracker.record_source_health") as recorder:
        yield recorder


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


def test_source_summary_lines_include_source_timing():
    """Per-source summary lines include elapsed source timing when available."""
    summary = {
        "sources": [
            {"name": "Dice", "job_count": 4, "warning_count": 0, "duration_seconds": 1.234},
            {"name": "Adzuna", "job_count": 2, "warning_count": 1, "duration_seconds": 65.0},
        ]
    }

    assert source_summary_lines(summary) == [
        "Dice: 4 jobs in 1.2s",
        "Adzuna: 2 jobs in 1m 05s (1 query warning)",
    ]


def test_cache_summary_line_includes_hits_misses_and_writes():
    """Cache summary copy exposes hit/miss counters from completed searches."""
    summary = {
        "cache_stats": {
            "hits": 3,
            "misses": 2,
            "writes": 2,
            "disabled": 1,
        }
    }

    assert cache_summary_line(summary) == "Cache: 3 hits, 2 misses, 2 writes, 1 uncached requests"
    assert cache_summary_line({"cache_stats": {}}) is None


def test_zero_result_lines_reuse_next_action_guidance():
    """Zero-result GUI state has concrete next actions."""
    assert zero_result_lines(3) == []
    lines = zero_result_lines(0)
    assert lines
    assert any("minimum score" in line for line in lines)


def test_zero_result_lines_prioritize_profile_readiness_guidance():
    """Zero-result GUI guidance starts with profile-specific next actions when available."""
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }

    lines = zero_result_lines(0, profile)

    assert lines[0] == "Add years of experience so seniority matching is more accurate"
    assert lines[1] == "Add a target location or work arrangement to reduce weak matches"
    assert any("minimum score" in line for line in lines)


def test_interruption_messages_explain_report_state():
    """Cancel and error messages explain whether a report exists."""
    assert "No new report was generated" in cancellation_message()
    assert "before a report could be generated" in error_message("network down")
    assert "network down" in error_message("network down")


def test_normalize_source_progress_clamps_display_bounds():
    """Source progress counters are safe for GUI progress bars."""
    assert normalize_source_progress(2, 5) == (2, 5)
    assert normalize_source_progress(9, 3) == (3, 3)
    assert normalize_source_progress(-1, 0) == (0, 1)
    assert normalize_source_progress("bad", "bad") == (0, 1)


def test_filter_by_company_applies_include_and_exclude_terms():
    """Company filters match case-insensitively against company names."""
    jobs = [
        JobResult(
            title="Engineer",
            company="Northstar Tools",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="LedgerWorks",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/2",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="ScaleOps",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/3",
            source="Dice",
        ),
    ]

    filtered = filter_by_company(
        jobs,
        include="northstar, ledger",
        exclude="ledger",
    )

    assert [job.company for job in filtered] == ["Northstar Tools"]


def test_filter_by_required_skills_keeps_only_jobs_with_all_required_skills():
    """Must-have skills filter keeps jobs matching every required skill."""
    jobs = [
        JobResult(
            title="Engineer",
            company="Northstar Tools",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build NodeJS services on k8s",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="LedgerWorks",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build Python services",
            url="https://example.com/2",
            source="Dice",
        ),
    ]

    filtered = filter_by_required_skills(jobs, "node.js, kubernetes")

    assert [job.company for job in filtered] == ["Northstar Tools"]


def test_apply_preferred_skills_appends_without_mutating_profile():
    """Nice-to-have GUI skills are added to the per-search profile only."""
    profile = {
        "core_skills": ["Python"],
        "secondary_skills": ["Docker"],
    }

    search_profile = apply_preferred_skills(profile, "docker, Kubernetes, Redis")

    assert search_profile["secondary_skills"] == ["Docker", "Kubernetes", "Redis"]
    assert profile["secondary_skills"] == ["Docker"]


def test_filter_by_location_strictness_uses_arrangement_and_text_hints():
    """Location strictness applies hard arrangement filters when requested."""
    jobs = [
        JobResult(
            title="Engineer",
            company="RemoteCo",
            location="Anywhere",
            arrangement="unknown",
            salary="Not listed",
            date_posted="Today",
            description="Distributed remote team",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="HybridCo",
            location="Austin, TX",
            arrangement="hybrid",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/2",
            source="Dice",
        ),
        JobResult(
            title="Engineer",
            company="OfficeCo",
            location="New York, NY",
            arrangement="on-site",
            salary="Not listed",
            date_posted="Today",
            description="Build software",
            url="https://example.com/3",
            source="Dice",
        ),
    ]

    assert [
        job.company for job in filter_by_location_strictness(jobs, "remote_only")
    ] == ["RemoteCo"]
    assert [
        job.company for job in filter_by_location_strictness(jobs, "remote_or_hybrid")
    ] == ["RemoteCo", "HybridCo"]
    assert [
        job.company for job in filter_by_location_strictness(jobs, "exclude_onsite")
    ] == ["RemoteCo", "HybridCo"]
    assert filter_by_location_strictness(jobs, "profile") == jobs


def test_resolve_date_filter_maps_freshness_presets():
    """Freshness presets resolve to concrete date boundaries."""
    today = date(2026, 5, 13)

    assert resolve_date_filter({"freshness": "any"}, today=today) == (None, None)
    assert resolve_date_filter({"freshness": "past_24h"}, today=today) == (
        "2026-05-12",
        "2026-05-13",
    )
    assert resolve_date_filter({"freshness": "past_48h"}, today=today) == (
        "2026-05-11",
        "2026-05-13",
    )
    assert resolve_date_filter({"freshness": "past_7d"}, today=today) == (
        "2026-05-06",
        "2026-05-13",
    )
    assert resolve_date_filter({
        "freshness": "past_24h",
        "from_date": "2026-05-01",
        "to_date": "2026-05-03",
    }, today=today) == ("2026-05-01", "2026-05-03")


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


def test_search_worker_emits_completion_summary(tmp_path, source_health_recorder):
    """SearchWorker includes source warnings, counts, and timings on completion."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }

    def fake_fetch_all(_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
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
            "cache_stats": {"hits": 2, "misses": 1, "writes": 1, "disabled": 0},
        }

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", return_value=[]):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["Dice", "RemoteOK"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=lambda scored: scored):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.gui.worker_thread.time.monotonic", side_effect=[10.0, 10.25, 20.0, 21.5]):
                                with patch("job_radar.report.generate_report", return_value={
                                    "html": str(tmp_path / "jobs.html"),
                                    "stats": {"total": 0, "new": 0, "high_score": 0},
                                }):
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
    assert summary["cache_stats"] == {"hits": 2, "misses": 1, "writes": 1, "disabled": 0}
    assert summary["result_stats"] == {"total": 0, "new": 0, "high_score": 0}
    assert summary["sources"] == [
        {"name": "Dice", "job_count": 0, "warning_count": 1, "duration_seconds": 0.25},
        {"name": "RemoteOK", "job_count": 3, "warning_count": 0, "duration_seconds": 1.5},
    ]
    source_health_recorder.assert_called_once_with(summary)


def test_search_worker_cancellation_after_fetch_skips_report(tmp_path, source_health_recorder):
    """Worker stops cleanly if cancellation is requested during fetch."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }

    def fake_fetch_all(_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        on_source_progress("Dice", 9, 3, "started", 0)
        stop_event.set()
        return [], {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.report.generate_report") as generate_report:
                worker = SearchWorker(result_queue, stop_event, profile, {"min_score": 2.8})
                worker.run()

    messages = []
    while not result_queue.empty():
        messages.append(result_queue.get())

    assert ("source_started", "Dice", 3, 3) in messages
    assert messages[-1] == ("cancelled",)
    generate_report.assert_not_called()
    source_health_recorder.assert_not_called()


def test_search_worker_applies_gui_search_preset(tmp_path):
    """SearchWorker applies selected GUI preset before fetching and reporting."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    captured = {}
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
        "location": "Austin, TX",
    }

    def fake_fetch_all(fetch_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        captured["fetch_profile"] = fetch_profile
        if on_source_progress:
            on_source_progress("RemoteOK", 1, 1, "started", 0)
            on_source_progress("RemoteOK", 1, 1, "complete", 0)
        return [], {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    def fake_generate_manual_urls(report_profile, selected_manual_sources=None):
        captured["manual_profile"] = report_profile
        captured["selected_manual_sources"] = selected_manual_sources
        return []

    def fake_generate_report(**kwargs):
        captured["report_profile"] = kwargs["profile"]
        return {"html": str(tmp_path / "jobs.html")}

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", side_effect=fake_generate_manual_urls):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["RemoteOK"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=lambda scored: scored):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.report.generate_report", side_effect=fake_generate_report):
                                worker = SearchWorker(
                                    result_queue,
                                    stop_event,
                                    profile,
                                    {"min_score": 2.8, "preset": "remote-backend"},
                                )
                                worker.run()

    assert captured["fetch_profile"]["location"] == "Remote"
    assert captured["fetch_profile"]["arrangement"] == ["remote"]
    assert captured["fetch_profile"]["target_titles"][0] == "Senior Backend Engineer"
    assert captured["manual_profile"] == captured["fetch_profile"]
    assert captured["selected_manual_sources"] is None
    assert captured["report_profile"] == captured["fetch_profile"]
    assert profile["location"] == "Austin, TX"


def test_search_worker_applies_selected_sources(tmp_path):
    """SearchWorker passes selected automated and manual source keys."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    captured = {}
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }

    def fake_fetch_all(fetch_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        captured["selected_sources"] = selected_sources
        return [], {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    def fake_generate_report(**kwargs):
        captured["sources_searched"] = kwargs["sources_searched"]
        captured["manual_urls"] = kwargs["manual_urls"]
        return {"html": str(tmp_path / "jobs.html")}

    def fake_generate_manual_urls(report_profile, selected_manual_sources=None):
        captured["selected_manual_sources"] = selected_manual_sources
        return [
            {
                "source": "LinkedIn",
                "title": "Backend Engineer",
                "url": "https://example.com/linkedin",
            }
        ]

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", side_effect=fake_generate_manual_urls):
                with patch("job_radar.sources.get_selected_source_display_names", return_value=["Dice"]):
                    with patch("job_radar.sources.get_manual_source_display_names", return_value=["LinkedIn"]):
                        with patch("job_radar.tracker.mark_seen", side_effect=lambda scored: scored):
                            with patch("job_radar.tracker.get_stats", return_value=None):
                                with patch("job_radar.report.generate_report", side_effect=fake_generate_report):
                                    worker = SearchWorker(
                                        result_queue,
                                        stop_event,
                                        profile,
                                        {
                                            "min_score": 2.8,
                                            "selected_sources": ["dice"],
                                            "selected_manual_sources": ["linkedin"],
                                        },
                                    )
                                    worker.run()

    assert captured["selected_sources"] == ["dice"]
    assert captured["selected_manual_sources"] == ["linkedin"]
    assert captured["manual_urls"][0]["source"] == "LinkedIn"
    assert captured["sources_searched"] == ["Dice", "LinkedIn"]


def test_search_worker_filters_companies_before_scoring_and_tracking(tmp_path):
    """SearchWorker applies company filters before scoring/tracking/reporting."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    captured = {}
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }
    jobs = [
        JobResult(
            title="Backend Engineer",
            company="Northstar Tools",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build Python APIs",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Backend Engineer",
            company="LedgerWorks",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build Python APIs",
            url="https://example.com/2",
            source="Dice",
        ),
    ]

    def fake_fetch_all(fetch_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        return jobs, {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    def fake_mark_seen(scored):
        captured["tracked_companies"] = [item["job"].company for item in scored]
        return scored

    def fake_generate_report(**kwargs):
        captured["reported_companies"] = [
            item["job"].company for item in kwargs["scored_results"]
        ]
        return {"html": str(tmp_path / "jobs.html")}

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", return_value=[]):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["Dice"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=fake_mark_seen):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.report.generate_report", side_effect=fake_generate_report):
                                worker = SearchWorker(
                                    result_queue,
                                    stop_event,
                                    profile,
                                    {
                                        "min_score": 0,
                                        "include_companies": "northstar, ledger",
                                        "exclude_companies": "ledger",
                                    },
                                )
                                worker.run()

    assert captured["tracked_companies"] == ["Northstar Tools"]
    assert captured["reported_companies"] == ["Northstar Tools"]


def test_search_worker_hides_rejected_and_skipped_applications_before_report(tmp_path):
    """SearchWorker can suppress rejected/skipped tracker entries from reports."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    captured = {}
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }
    jobs = [
        JobResult(
            title="Backend Engineer",
            company="Northstar Tools",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build Python APIs",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Platform Engineer",
            company="LedgerWorks",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build Python APIs",
            url="https://example.com/2",
            source="Dice",
        ),
    ]

    def fake_fetch_all(fetch_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        return jobs, {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    def fake_generate_report(**kwargs):
        captured["reported_companies"] = [
            item["job"].company for item in kwargs["scored_results"]
        ]
        return {"html": str(tmp_path / "jobs.html")}

    applications = {
        "platform engineer||ledgerworks": {"status": "rejected"},
    }

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", return_value=[]):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["Dice"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=lambda scored: scored):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.tracker.get_all_application_statuses", return_value=applications):
                                with patch("job_radar.report.generate_report", side_effect=fake_generate_report):
                                    worker = SearchWorker(
                                        result_queue,
                                        stop_event,
                                        profile,
                                        {
                                            "min_score": 0,
                                            "hide_rejected_skipped": True,
                                        },
                                    )
                                    worker.run()

    assert captured["reported_companies"] == ["Northstar Tools"]


def test_search_worker_filters_required_skills_before_scoring_and_tracking(tmp_path):
    """SearchWorker applies must-have skill filters before tracking/reporting."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    captured = {}
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }
    jobs = [
        JobResult(
            title="Backend Engineer",
            company="Northstar Tools",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build NodeJS APIs on k8s",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Backend Engineer",
            company="LedgerWorks",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build Python APIs",
            url="https://example.com/2",
            source="Dice",
        ),
    ]

    def fake_fetch_all(fetch_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        return jobs, {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    def fake_mark_seen(scored):
        captured["tracked_companies"] = [item["job"].company for item in scored]
        return scored

    def fake_generate_report(**kwargs):
        captured["reported_companies"] = [
            item["job"].company for item in kwargs["scored_results"]
        ]
        return {"html": str(tmp_path / "jobs.html")}

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", return_value=[]):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["Dice"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=fake_mark_seen):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.report.generate_report", side_effect=fake_generate_report):
                                worker = SearchWorker(
                                    result_queue,
                                    stop_event,
                                    profile,
                                    {
                                        "min_score": 0,
                                        "required_skills": "node.js, kubernetes",
                                    },
                                )
                                worker.run()

    assert captured["tracked_companies"] == ["Northstar Tools"]
    assert captured["reported_companies"] == ["Northstar Tools"]


def test_search_worker_applies_preferred_skills_to_search_profile(tmp_path):
    """SearchWorker scores/reports with per-search nice-to-have skills."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    captured = {}
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
        "secondary_skills": ["Docker"],
    }

    def fake_fetch_all(fetch_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        captured["fetch_profile"] = fetch_profile
        return [], {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    def fake_generate_report(**kwargs):
        captured["report_profile"] = kwargs["profile"]
        return {"html": str(tmp_path / "jobs.html")}

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", return_value=[]):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["Dice"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=lambda scored: scored):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.report.generate_report", side_effect=fake_generate_report):
                                worker = SearchWorker(
                                    result_queue,
                                    stop_event,
                                    profile,
                                    {
                                        "min_score": 0,
                                        "preferred_skills": "docker, Kubernetes, Redis",
                                    },
                                )
                                worker.run()

    assert captured["fetch_profile"]["secondary_skills"] == [
        "Docker",
        "Kubernetes",
        "Redis",
    ]
    assert captured["report_profile"]["secondary_skills"] == [
        "Docker",
        "Kubernetes",
        "Redis",
    ]
    assert profile["secondary_skills"] == ["Docker"]


def test_search_worker_filters_location_strictness_before_scoring_and_tracking(tmp_path):
    """SearchWorker applies GUI location strictness before tracking/reporting."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    captured = {}
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }
    jobs = [
        JobResult(
            title="Backend Engineer",
            company="RemoteCo",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="Today",
            description="Build Python APIs",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Backend Engineer",
            company="OfficeCo",
            location="New York, NY",
            arrangement="onsite",
            salary="Not listed",
            date_posted="Today",
            description="Build Python APIs in office",
            url="https://example.com/2",
            source="Dice",
        ),
    ]

    def fake_fetch_all(fetch_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        return jobs, {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    def fake_mark_seen(scored):
        captured["tracked_companies"] = [item["job"].company for item in scored]
        return scored

    def fake_generate_report(**kwargs):
        captured["reported_companies"] = [
            item["job"].company for item in kwargs["scored_results"]
        ]
        return {"html": str(tmp_path / "jobs.html")}

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", return_value=[]):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["Dice"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=fake_mark_seen):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.report.generate_report", side_effect=fake_generate_report):
                                worker = SearchWorker(
                                    result_queue,
                                    stop_event,
                                    profile,
                                    {
                                        "min_score": 0,
                                        "location_strictness": "remote_only",
                                    },
                                )
                                worker.run()

    assert captured["tracked_companies"] == ["RemoteCo"]
    assert captured["reported_companies"] == ["RemoteCo"]


def test_search_worker_applies_freshness_before_scoring_and_tracking(tmp_path):
    """SearchWorker converts freshness presets into date filters."""
    result_queue = queue.Queue()
    stop_event = threading.Event()
    captured = {}
    profile = {
        "name": "Test User",
        "target_titles": ["Backend Engineer"],
        "core_skills": ["Python"],
    }
    today = date.today().isoformat()
    jobs = [
        JobResult(
            title="Backend Engineer",
            company="FreshCo",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted=today,
            description="Build Python APIs",
            url="https://example.com/1",
            source="Dice",
        ),
        JobResult(
            title="Backend Engineer",
            company="OldCo",
            location="Remote",
            arrangement="remote",
            salary="Not listed",
            date_posted="2020-01-01",
            description="Build Python APIs",
            url="https://example.com/2",
            source="Dice",
        ),
    ]

    def fake_fetch_all(fetch_profile, on_source_progress=None, selected_sources=None, cancellation_event=None):
        return jobs, {
            "query_failures": 0,
            "failed_sources": [],
            "query_failure_details": [],
        }

    def fake_mark_seen(scored):
        captured["tracked_companies"] = [item["job"].company for item in scored]
        return scored

    def fake_generate_report(**kwargs):
        captured["reported_companies"] = [
            item["job"].company for item in kwargs["scored_results"]
        ]
        captured["from_date"] = kwargs["from_date"]
        captured["to_date"] = kwargs["to_date"]
        return {"html": str(tmp_path / "jobs.html")}

    with patch("job_radar.api_config.load_api_credentials"):
        with patch("job_radar.sources.fetch_all", side_effect=fake_fetch_all):
            with patch("job_radar.sources.generate_manual_urls", return_value=[]):
                with patch("job_radar.sources.get_automated_source_display_names", return_value=["Dice"]):
                    with patch("job_radar.tracker.mark_seen", side_effect=fake_mark_seen):
                        with patch("job_radar.tracker.get_stats", return_value=None):
                            with patch("job_radar.report.generate_report", side_effect=fake_generate_report):
                                worker = SearchWorker(
                                    result_queue,
                                    stop_event,
                                    profile,
                                    {
                                        "min_score": 0,
                                        "freshness": "past_24h",
                                    },
                                )
                                worker.run()

    assert captured["tracked_companies"] == ["FreshCo"]
    assert captured["reported_companies"] == ["FreshCo"]
    assert captured["to_date"] == today
    assert captured["from_date"] <= today
