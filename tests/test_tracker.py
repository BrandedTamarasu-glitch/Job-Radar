"""Parametrized tests for tracker functions with tmp_path isolation."""

import pytest
from unittest.mock import patch
from job_radar.tracker import job_key, mark_seen, get_stats, _TRACKER_PATH


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
# Production tracker safety test
# ---------------------------------------------------------------------------

def test_tracker_never_touches_production():
    """Test that documents where production tracker lives (safety documentation)."""
    # This test verifies isolation by documenting the production path
    # All other tests MUST use tmp_path + patch to avoid touching this file
    assert "results/tracker.json" in _TRACKER_PATH
    assert _TRACKER_PATH.endswith("results/tracker.json")
