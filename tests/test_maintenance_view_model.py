"""Tests for local maintenance summary helpers."""

import json

from job_radar.gui.maintenance_view_model import (
    app_data_bundle_validation_message,
    app_data_export_error_message,
    app_data_export_success_message,
    build_feedback_diagnostics_summary,
    build_local_maintenance_summary,
    cache_clear_error_message,
    cache_clear_success_message,
    clear_dismissed_reviews_status,
    dismissed_review_cleanup_error_message,
    feedback_diagnostics_text,
    dismissed_review_cleanup_success_message,
    format_feedback_diagnostics_lines,
    format_local_maintenance_lines,
    local_maintenance_text,
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


def test_local_maintenance_text_joins_summary_lines(tmp_path):
    data_dir = tmp_path / "data"
    results_dir = data_dir / "results"
    data_dir.mkdir()
    results_dir.mkdir()

    text = local_maintenance_text(data_dir, results_dir)

    assert "Local data:" in text
    assert "HTTP cache:" in text
    assert "\n" in text


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


def test_feedback_diagnostics_text_joins_redacted_lines(tmp_path):
    data_dir = tmp_path / "private-user" / "data"
    results_dir = data_dir / "results"
    data_dir.mkdir(parents=True)
    results_dir.mkdir()

    text = feedback_diagnostics_text(data_dir, results_dir)

    assert "Feedback diagnostics (redacted):" in text
    assert "Privacy: do not include API keys" in text
    assert "private-user" not in text


def test_maintenance_status_messages_are_consistent_for_settings(tmp_path):
    assert cache_clear_success_message(3, tmp_path / "cache") == (
        f"Removed 3 cached response file(s) from {tmp_path / 'cache'}"
    )
    assert cache_clear_error_message(OSError("locked")) == "Failed to clear cache: locked"
    assert app_data_export_success_message(tmp_path / "bundle.zip") == (
        f"Exported app data to {tmp_path / 'bundle.zip'}"
    )
    assert app_data_export_error_message(OSError("disk full")) == (
        "Failed to export app data: disk full"
    )
    assert dismissed_review_cleanup_success_message(4) == (
        "Cleared 4 dismissed review item(s)"
    )
    assert dismissed_review_cleanup_error_message(RuntimeError("busy")) == (
        "Dismissed review cleanup failed: busy"
    )


def test_app_data_bundle_validation_message_handles_valid_and_invalid_results():
    assert app_data_bundle_validation_message(
        is_valid=True,
        files=["profile.json"],
        errors=[],
    ) == "Bundle is valid: 1 file ready to restore"
    assert app_data_bundle_validation_message(
        is_valid=True,
        files=["profile.json", "tracker.json"],
        errors=[],
    ) == "Bundle is valid: 2 files ready to restore"
    assert app_data_bundle_validation_message(
        is_valid=False,
        files=[],
        errors=["missing manifest", "bad checksum"],
    ) == "Bundle validation failed: missing manifest; bad checksum"


def test_clear_dismissed_reviews_status_returns_success_and_error():
    counts = iter([{"dismissed": 5}, {"dismissed": 2}])
    calls = []

    message, color = clear_dismissed_reviews_status(
        review_counts_func=lambda: next(counts),
        clear_review_state_func=lambda state, limit: calls.append((state, limit)),
    )

    assert message == "Cleared 3 dismissed review item(s)"
    assert color == "green"
    assert calls == [("dismissed", 50)]

    def fail_clear(state, limit):
        raise RuntimeError("busy")

    message, color = clear_dismissed_reviews_status(
        review_counts_func=lambda: {"dismissed": 5},
        clear_review_state_func=fail_clear,
    )

    assert message == "Dismissed review cleanup failed: busy"
    assert color == "red"
