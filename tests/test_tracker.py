"""Parametrized tests for tracker functions with tmp_path isolation."""

import json
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from job_radar.tracker import (
    TRACKER_SEEN_RETENTION_DAYS,
    _load_tracker,
    _prune_old_seen_jobs,
    _tracker_path,
    get_application_entry,
    get_application_status,
    get_source_health_history,
    get_stats,
    filter_scored_by_application_status,
    job_key,
    mark_seen,
    record_source_health,
    update_application_details,
    update_application_status,
)


# ---------------------------------------------------------------------------
# job_key stability tests (TEST-04)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title,company,expected", [
    ("Python Developer", "TestCorp", "python developer||testcorp"),  # basic lowering
    ("  Python Developer  ", "  TestCorp  ", "python developer||testcorp"),  # whitespace stripped
    ("PYTHON DEVELOPER", "TESTCORP", "python developer||testcorp"),  # all caps
    ("Senior Dev", "Company A", "senior dev||company a"),  # different title
], ids=[
    "basic_lowering",
    "whitespace_stripped",
    "all_caps",
    "different_title",
])
def test_job_key_stable(title, company, expected):
    """Test job_key generates stable dedup keys regardless of whitespace and casing (TEST-04)."""
    assert job_key(title, company) == expected


def test_job_key_different_jobs_differ():
    """Test job_key produces different keys for different jobs (TEST-04)."""
    # Different titles, same company
    assert job_key("Python Dev", "CompanyA") != job_key("Java Dev", "CompanyA")

    # Same title, different companies
    assert job_key("Python Dev", "CompanyA") != job_key("Python Dev", "CompanyB")


# ---------------------------------------------------------------------------
# mark_seen new/seen annotation tests (TEST-05)
# ---------------------------------------------------------------------------

def test_mark_seen_new_job(tmp_path, job_factory):
    """Test mark_seen marks first-time jobs as is_new=True (TEST-05)."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        # Create one job via job_factory
        job = job_factory(title="Python Developer", company="TestCorp")
        result = {"job": job, "score": {"overall": 4.2}}

        # Call mark_seen
        annotated = mark_seen([result])

        # Assert is_new is True
        assert annotated[0]["is_new"] is True
        assert isinstance(annotated[0]["first_seen"], str)

        # Assert tracker file exists on disk
        tracker_path = tmp_path / "tracker.json"
        assert tracker_path.exists()


def test_mark_seen_repeat_job(tmp_path, job_factory):
    """Test mark_seen marks repeat jobs as is_new=False (TEST-05)."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        # Create one job
        job = job_factory(title="Senior Python Dev", company="AcmeCorp")
        result = {"job": job, "score": {"overall": 4.5}}

        # First call: should be new
        annotated1 = mark_seen([result])
        assert annotated1[0]["is_new"] is True
        first_seen_date = annotated1[0]["first_seen"]

        # Second call with same job: should NOT be new
        result2 = {"job": job, "score": {"overall": 4.5}}
        annotated2 = mark_seen([result2])
        assert annotated2[0]["is_new"] is False

        # first_seen should be the same date
        assert annotated2[0]["first_seen"] == first_seen_date

        with open(tmp_path / "tracker.json", encoding="utf-8") as f:
            tracker = json.load(f)
        entry = tracker["seen_jobs"][job_key("Senior Python Dev", "AcmeCorp")]
        assert entry["last_seen"] == date.today().isoformat()


def test_mark_seen_multiple_jobs(tmp_path, job_factory):
    """Test mark_seen correctly handles multiple jobs with mixed new/repeat (TEST-05)."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        # Create 3 different jobs
        job1 = job_factory(title="Python Developer", company="TestCorp")
        job2 = job_factory(title="Backend Engineer", company="DevShop")
        job3 = job_factory(title="Full Stack Dev", company="WebCo")

        results = [
            {"job": job1, "score": {"overall": 4.2}},
            {"job": job2, "score": {"overall": 3.8}},
            {"job": job3, "score": {"overall": 4.0}},
        ]

        # First call: all 3 should be new
        annotated1 = mark_seen(results)
        assert all(r["is_new"] is True for r in annotated1)

        # Second call: 2 repeats + 1 new job
        job4 = job_factory(title="Senior Engineer", company="NewCorp")
        results2 = [
            {"job": job1, "score": {"overall": 4.2}},  # repeat
            {"job": job2, "score": {"overall": 3.8}},  # repeat
            {"job": job4, "score": {"overall": 4.5}},  # new
        ]

        annotated2 = mark_seen(results2)
        assert annotated2[0]["is_new"] is False  # job1 repeat
        assert annotated2[1]["is_new"] is False  # job2 repeat
        assert annotated2[2]["is_new"] is True   # job4 new


# ---------------------------------------------------------------------------
# get_stats aggregation tests (TEST-06)
# ---------------------------------------------------------------------------

def test_get_stats_empty(tmp_path):
    """Test get_stats returns zeros when no tracker file exists (TEST-06)."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        stats = get_stats()

        assert stats["total_unique_jobs_seen"] == 0
        assert stats["total_runs"] == 0
        assert stats["avg_new_per_run_last_7"] == 0


def test_get_stats_after_runs(tmp_path, job_factory):
    """Test get_stats returns correct aggregation after multiple runs (TEST-06)."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        # First run: 5 different jobs
        jobs_run1 = [
            job_factory(title=f"Job {i}", company=f"Company {i}")
            for i in range(5)
        ]
        results_run1 = [
            {"job": job, "score": {"overall": 4.0}}
            for job in jobs_run1
        ]
        mark_seen(results_run1)

        # Check stats after first run
        stats1 = get_stats()
        assert stats1["total_unique_jobs_seen"] == 5
        assert stats1["total_runs"] == 1
        assert stats1["avg_new_per_run_last_7"] == 5.0

        # Second run: 3 new jobs + 2 repeats
        jobs_run2_new = [
            job_factory(title=f"New Job {i}", company=f"NewCo {i}")
            for i in range(3)
        ]
        results_run2 = [
            {"job": jobs_run1[0], "score": {"overall": 4.0}},  # repeat
            {"job": jobs_run1[1], "score": {"overall": 4.0}},  # repeat
        ] + [
            {"job": job, "score": {"overall": 4.0}}
            for job in jobs_run2_new
        ]
        mark_seen(results_run2)

        # Check stats after second run
        stats2 = get_stats()
        assert stats2["total_unique_jobs_seen"] == 8  # 5 + 3 new
        assert stats2["total_runs"] == 2
        assert stats2["avg_new_per_run_last_7"] == 4.0  # (5+3)/2


# ---------------------------------------------------------------------------
# tracker pruning tests
# ---------------------------------------------------------------------------

def test_prune_old_seen_jobs_removes_stale_entries_without_status():
    """Test old seen jobs without application status are pruned."""
    today = date(2026, 5, 13)
    stale_date = today - timedelta(days=TRACKER_SEEN_RETENTION_DAYS + 1)
    fresh_date = today - timedelta(days=TRACKER_SEEN_RETENTION_DAYS)
    tracker = {
        "seen_jobs": {
            "stale||company": {"first_seen": stale_date.isoformat()},
            "fresh||company": {"first_seen": fresh_date.isoformat()},
        },
        "applications": {},
        "run_history": [],
    }

    pruned = _prune_old_seen_jobs(tracker, today=today)

    assert pruned == 1
    assert "stale||company" not in tracker["seen_jobs"]
    assert "fresh||company" in tracker["seen_jobs"]


def test_prune_old_seen_jobs_keeps_entries_with_application_status():
    """Test application status protects old seen jobs from pruning."""
    today = date(2026, 5, 13)
    stale_date = today - timedelta(days=TRACKER_SEEN_RETENTION_DAYS + 30)
    tracker = {
        "seen_jobs": {
            "applied||company": {"first_seen": stale_date.isoformat()},
        },
        "applications": {
            "applied||company": {"status": "applied"},
        },
        "run_history": [],
    }

    pruned = _prune_old_seen_jobs(tracker, today=today)

    assert pruned == 0
    assert "applied||company" in tracker["seen_jobs"]


def test_prune_old_seen_jobs_uses_last_seen_when_available():
    """Test recently re-seen jobs are retained even with old first_seen dates."""
    today = date(2026, 5, 13)
    tracker = {
        "seen_jobs": {
            "active||company": {
                "first_seen": "2025-01-01",
                "last_seen": today.isoformat(),
            },
        },
        "applications": {},
        "run_history": [],
    }

    pruned = _prune_old_seen_jobs(tracker, today=today)

    assert pruned == 0
    assert "active||company" in tracker["seen_jobs"]


def test_prune_old_seen_jobs_keeps_malformed_legacy_dates():
    """Test legacy records with malformed dates are retained."""
    tracker = {
        "seen_jobs": {
            "legacy||company": {"first_seen": "not-a-date"},
        },
        "applications": {},
        "run_history": [],
    }

    pruned = _prune_old_seen_jobs(tracker, today=date(2026, 5, 13))

    assert pruned == 0
    assert "legacy||company" in tracker["seen_jobs"]


# ---------------------------------------------------------------------------
# application pipeline metadata tests
# ---------------------------------------------------------------------------

def test_update_application_status_persists_notes_and_next_action(tmp_path):
    """Application status can carry notes plus next-action metadata."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        update_application_status(
            "Backend Engineer",
            "Acme",
            "applied",
            notes="Submitted through referral",
            next_action="Follow up with recruiter",
            next_action_date="2026-05-20",
        )

        entry = get_application_entry("Backend Engineer", "Acme")

    assert entry is not None
    assert entry["status"] == "applied"
    assert entry["notes"] == "Submitted through referral"
    assert entry["next_action"] == "Follow up with recruiter"
    assert entry["next_action_date"] == "2026-05-20"
    assert "updated" in entry


def test_update_application_details_preserves_existing_status(tmp_path):
    """Notes/next-action edits do not clobber the tracked application status."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        update_application_status("Backend Engineer", "Acme", "interviewing")
        update_application_details(
            "Backend Engineer",
            "Acme",
            notes="Panel scheduled",
            next_action="Prepare system design examples",
            next_action_date="2026-05-21",
        )

        entry = get_application_entry("Backend Engineer", "Acme")
        status = get_application_status("Backend Engineer", "Acme")

    assert status == "interviewing"
    assert entry["status"] == "interviewing"
    assert entry["notes"] == "Panel scheduled"
    assert entry["next_action"] == "Prepare system design examples"
    assert entry["next_action_date"] == "2026-05-21"


def test_update_application_details_can_create_unstatused_entry(tmp_path):
    """Users can save notes before choosing a pipeline status."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        update_application_details(
            "Backend Engineer",
            "Acme",
            notes="Interesting role; review later",
        )

        entry = get_application_entry("Backend Engineer", "Acme")
        status = get_application_status("Backend Engineer", "Acme")

    assert status is None
    assert entry["notes"] == "Interesting role; review later"
    assert entry["title"] == "Backend Engineer"
    assert entry["company"] == "Acme"


def test_filter_scored_by_application_status_hides_rejected_and_skipped(job_factory):
    """Report filtering can hide terminal application statuses."""
    kept_job = job_factory(title="Backend Engineer", company="Acme")
    rejected_job = job_factory(title="Platform Engineer", company="Ledger")
    skipped_job = job_factory(title="SRE", company="OpsCo")
    results = [
        {"job": kept_job, "score": {"overall": 4.2}},
        {"job": rejected_job, "score": {"overall": 4.0}},
        {"job": skipped_job, "score": {"overall": 3.8}},
    ]
    applications = {
        job_key("Platform Engineer", "Ledger"): {"status": "rejected"},
        job_key("SRE", "OpsCo"): {"status": "skipped"},
    }

    filtered = filter_scored_by_application_status(
        results,
        {"rejected", "skipped"},
        applications=applications,
    )

    assert [item["job"].company for item in filtered] == ["Acme"]


# ---------------------------------------------------------------------------
# source health history tests
# ---------------------------------------------------------------------------

def test_record_source_health_persists_run_summary(tmp_path):
    """Source health history stores compact per-run source diagnostics."""
    summary = {
        "sources": [
            {
                "name": "Dice",
                "job_count": 3,
                "warning_count": 1,
                "duration_seconds": 1.23456,
            },
            {"name": "RemoteOK", "job_count": 0, "warning_count": 0},
        ],
        "query_failures": 1,
        "failed_sources": ["Dice"],
        "source_warnings": [{"source": "dice", "query": "Backend", "error": "timeout"}],
        "cache_stats": {"hits": 2, "misses": 1, "writes": 1, "disabled": 0},
    }

    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        entry = record_source_health(summary, timestamp="2026-05-13T12:00:00")
        history = get_source_health_history()

    assert entry["timestamp"] == "2026-05-13T12:00:00"
    assert entry["total_jobs"] == 3
    assert entry["query_failures"] == 1
    assert entry["failed_sources"] == ["Dice"]
    assert entry["cache_stats"] == {"hits": 2, "misses": 1, "writes": 1, "disabled": 0}
    assert entry["sources"] == [
        {
            "name": "Dice",
            "job_count": 3,
            "warning_count": 1,
            "duration_seconds": 1.235,
        },
        {"name": "RemoteOK", "job_count": 0, "warning_count": 0},
    ]
    assert history == [entry]


def test_record_source_health_retains_recent_runs(tmp_path):
    """Source health history is capped to the most recent runs."""
    with patch("job_radar.tracker._TRACKER_PATH", str(tmp_path / "tracker.json")):
        for index in range(4):
            record_source_health(
                {
                    "sources": [{"name": f"Source {index}", "job_count": index}],
                    "query_failures": 0,
                },
                timestamp=f"2026-05-13T12:00:0{index}",
                retention_runs=2,
            )
        history = get_source_health_history()
        limited = get_source_health_history(limit=1)

    assert [entry["timestamp"] for entry in history] == [
        "2026-05-13T12:00:02",
        "2026-05-13T12:00:03",
    ]
    assert [entry["timestamp"] for entry in limited] == ["2026-05-13T12:00:03"]


# ---------------------------------------------------------------------------
# tracker path tests
# ---------------------------------------------------------------------------

def test_tracker_default_path_uses_app_data_results_dir(tmp_path, monkeypatch):
    """Production tracker lives under the app data results directory."""
    data_results = tmp_path / "data" / "results"
    monkeypatch.setattr("job_radar.tracker.get_results_dir", lambda: data_results)
    monkeypatch.setattr("job_radar.tracker._TRACKER_PATH", None)

    assert _tracker_path() == data_results / "tracker.json"


def test_load_tracker_reads_legacy_launch_tracker_when_app_data_missing(tmp_path, monkeypatch):
    """Existing launch-directory trackers are read before the app-data file exists."""
    legacy_tracker = tmp_path / "results" / "tracker.json"
    legacy_tracker.parent.mkdir()
    legacy_tracker.write_text(
        json.dumps({
            "seen_jobs": {"legacy||company": {"first_seen": "2026-01-01"}},
            "applications": {},
            "run_history": [],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr("job_radar.tracker._TRACKER_PATH", None)
    monkeypatch.setattr("job_radar.tracker._LEGACY_TRACKER_PATH", str(legacy_tracker))
    monkeypatch.setattr("job_radar.tracker.get_results_dir", lambda: tmp_path / "data" / "results")

    tracker = _load_tracker()

    assert "legacy||company" in tracker["seen_jobs"]
