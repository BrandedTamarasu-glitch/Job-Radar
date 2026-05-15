"""Tests for local maintenance summary helpers."""

import json

from job_radar.gui.maintenance_view_model import (
    build_feedback_diagnostics_summary,
    build_local_maintenance_summary,
    format_feedback_diagnostics_lines,
    format_local_maintenance_lines,
)


def test_local_maintenance_summary_counts_local_state(tmp_path):
    data_dir = tmp_path / "data"
    results_dir = data_dir / "results"
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(parents=True)
    results_dir.mkdir()
    (cache_dir / "a.json").write_text("cache", encoding="utf-8")
    (results_dir / "tracker.json").write_text(json.dumps({
        "seen_jobs": {"a": {}, "b": {}},
        "applications": {"a": {}},
        "source_health_history": [{}, {}],
    }), encoding="utf-8")
    (data_dir / "review_state.json").write_text(json.dumps({
        "jobs": {"a": {}, "b": {}, "c": {}},
    }), encoding="utf-8")
    (data_dir / "saved_searches.json").write_text(json.dumps({
        "recent": [{}, {}],
        "saved": [{}],
    }), encoding="utf-8")

    summary = build_local_maintenance_summary(data_dir, results_dir)

    assert summary.cache_files == 1
    assert summary.cache_bytes == 5
    assert summary.tracker_seen_jobs == 2
    assert summary.tracker_applications == 1
    assert summary.source_health_runs == 2
    assert summary.review_jobs == 3
    assert summary.saved_recent == 2
    assert summary.saved_named == 1
    assert summary.total_bytes > summary.cache_bytes


def test_local_maintenance_lines_include_suggestions_for_large_state(tmp_path):
    data_dir = tmp_path / "data"
    results_dir = data_dir / "results"
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(parents=True)
    results_dir.mkdir()
    for index in range(100):
        (cache_dir / f"{index}.json").write_text("x", encoding="utf-8")
    (results_dir / "tracker.json").write_text(json.dumps({
        "seen_jobs": {str(index): {} for index in range(5000)},
        "source_health_history": [{} for _ in range(20)],
    }), encoding="utf-8")

    lines = format_local_maintenance_lines(
        build_local_maintenance_summary(data_dir, results_dir)
    )

    assert any("HTTP cache: 100 file(s)" in line for line in lines)
    assert any("clear HTTP cache" in line for line in lines)
    assert any("tracker history" in line for line in lines)
    assert any("retained-run cap" in line for line in lines)


def test_feedback_diagnostics_summary_is_privacy_safe(tmp_path):
    data_dir = tmp_path / "private-user" / "data"
    results_dir = data_dir / "results"
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(parents=True)
    results_dir.mkdir()
    (cache_dir / "tokenish-cache-name.json").write_text("cache", encoding="utf-8")
    (results_dir / "tracker.json").write_text(json.dumps({
        "seen_jobs": {"secret-company-role": {}},
        "applications": {"private-application-note": {}},
        "source_health_history": [{}, {}],
    }), encoding="utf-8")
    (data_dir / "review_state.json").write_text(json.dumps({
        "jobs": {"private-review-id": {}},
    }), encoding="utf-8")
    (data_dir / "saved_searches.json").write_text(json.dumps({
        "recent": [{"name": "secret recent search"}],
        "saved": [{"name": "secret saved search"}],
    }), encoding="utf-8")

    summary = build_feedback_diagnostics_summary(
        data_dir,
        results_dir,
        app_version="2.6.0",
        operating_system="TestOS",
    )
    lines = format_feedback_diagnostics_lines(summary)
    text = "\n".join(lines)

    assert "Version: 2.6.0" in text
    assert "Operating system: TestOS" in text
    assert "1 seen job(s)" in text
    assert "1 application(s)" in text
    assert "1 saved search(es)" in text
    assert "1 recent search shortcut(s)" in text
    assert "2 source diagnostic run(s)" in text
    assert "Privacy: do not include API keys" in text
    assert "private-user" not in text
    assert "secret-company-role" not in text
    assert "private-application-note" not in text
    assert "secret saved search" not in text
    assert "tokenish-cache-name" not in text
