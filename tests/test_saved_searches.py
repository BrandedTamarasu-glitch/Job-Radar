import json
from datetime import datetime, timezone

from job_radar.saved_searches import (
    delete_named_search,
    format_search_insight,
    format_run_summary,
    load_search_history,
    normalize_search_config,
    prioritize_changed_searches,
    record_search_run,
    record_recent_search,
    save_named_search,
    summarize_search_config,
)


def test_load_search_history_returns_empty_state_for_missing_file(tmp_path):
    state = load_search_history(tmp_path / "missing.json")

    assert state == {"version": 1, "recent": [], "saved": []}


def test_load_search_history_recovers_from_corrupt_json(tmp_path):
    path = tmp_path / "saved_searches.json"
    path.write_text("{bad json", encoding="utf-8")

    state = load_search_history(path)

    assert state == {"version": 1, "recent": [], "saved": []}


def test_normalize_search_config_keeps_known_json_safe_keys():
    config = {
        "preset": "remote-backend",
        "min_score": 3.2,
        "new_only": True,
        "selected_sources": ["remoteok", "", "dice"],
        "match_calibration": "strict",
        "unknown": "ignored",
    }

    normalized = normalize_search_config(config)

    assert normalized["preset"] == "remote-backend"
    assert normalized["min_score"] == 3.2
    assert normalized["new_only"] is True
    assert normalized["selected_sources"] == ["remoteok", "dice"]
    assert normalized["match_calibration"] == "strict"
    assert "unknown" not in normalized


def test_record_recent_search_dedupes_and_moves_latest_to_front(tmp_path):
    path = tmp_path / "saved_searches.json"
    first_time = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 5, 14, 13, 0, tzinfo=timezone.utc)

    record_recent_search({"preset": "remote-backend"}, path=path, now=first_time)
    state = record_recent_search({"preset": "remote-backend"}, path=path, now=second_time)

    assert len(state["recent"]) == 1
    assert state["recent"][0]["last_run_at"] == second_time.isoformat()
    assert state["recent"][0]["config"]["preset"] == "remote-backend"


def test_record_recent_search_caps_history(tmp_path):
    path = tmp_path / "saved_searches.json"

    for index in range(4):
        record_recent_search({"preset": f"preset-{index}"}, path=path, limit=3)

    state = json.loads(path.read_text(encoding="utf-8"))

    assert len(state["recent"]) == 3
    assert state["recent"][0]["config"]["preset"] == "preset-3"
    assert state["recent"][-1]["config"]["preset"] == "preset-1"


def test_summarize_search_config_prefers_meaningful_parts():
    label = summarize_search_config(
        {
            "preset": "remote-backend",
            "freshness": "past_48h",
            "location_strictness": "remote_only",
            "required_skills": "Python, FastAPI",
        }
    )

    assert label == "remote-backend | past 48h | remote only | must: Python, FastAPI"


def test_save_named_search_adds_saved_entry_without_clearing_recent(tmp_path):
    path = tmp_path / "saved_searches.json"
    record_recent_search({"preset": "remote-backend"}, path=path)

    state = save_named_search("Morning remote", {"preset": "remote-backend"}, path=path)

    assert len(state["recent"]) == 1
    assert state["saved"][0]["name"] == "Morning remote"
    assert state["saved"][0]["config"]["preset"] == "remote-backend"


def test_save_named_search_replaces_case_insensitive_name(tmp_path):
    path = tmp_path / "saved_searches.json"

    save_named_search("Remote", {"preset": "remote-backend"}, path=path)
    state = save_named_search("remote", {"preset": "contract"}, path=path)

    assert len(state["saved"]) == 1
    assert state["saved"][0]["name"] == "remote"
    assert state["saved"][0]["config"]["preset"] == "contract"


def test_save_named_search_rejects_blank_name(tmp_path):
    path = tmp_path / "saved_searches.json"

    try:
        save_named_search("   ", {"preset": "remote-backend"}, path=path)
    except ValueError as exc:
        assert "cannot be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_delete_named_search_removes_matching_name(tmp_path):
    path = tmp_path / "saved_searches.json"
    save_named_search("Remote", {"preset": "remote-backend"}, path=path)
    save_named_search("Contract", {"preset": "contract"}, path=path)

    state = delete_named_search("remote", path=path)

    assert [item["name"] for item in state["saved"]] == ["Contract"]


def test_record_search_run_updates_matching_recent_and_saved(tmp_path):
    path = tmp_path / "saved_searches.json"
    config = {"preset": "remote-backend"}
    run_time = datetime(2026, 5, 14, 15, 0, tzinfo=timezone.utc)

    record_recent_search(config, path=path)
    save_named_search("Remote", config, path=path)
    state = record_search_run(
        config,
        {"total": 12, "new": 5, "high_score": 3},
        path=path,
        now=run_time,
    )

    assert state["recent"][0]["run_count"] == 1
    assert state["saved"][0]["run_count"] == 1
    assert state["recent"][0]["last_run_at"] == run_time.isoformat()
    assert state["saved"][0]["last_result_stats"] == {
        "total": 12,
        "new": 5,
        "high_score": 3,
    }


def test_record_search_run_can_store_review_counts(tmp_path):
    path = tmp_path / "saved_searches.json"
    config = {"preset": "remote-backend"}

    save_named_search("Remote", config, path=path)
    state = record_search_run(
        config,
        {"total": 12, "new": 5, "high_score": 3},
        path=path,
        review_counts={"shortlisted": 2, "maybe_later": 1, "dismissed": 4},
    )

    assert state["saved"][0]["last_result_stats"]["review"] == {
        "shortlisted": 2,
        "maybe_later": 1,
        "dismissed": 4,
    }


def test_record_search_run_rolls_last_stats_to_previous(tmp_path):
    path = tmp_path / "saved_searches.json"
    config = {"preset": "remote-backend"}

    save_named_search("Remote", config, path=path)
    record_search_run(config, {"total": 8, "new": 4, "high_score": 2}, path=path)
    state = record_search_run(config, {"total": 12, "new": 5, "high_score": 3}, path=path)

    assert state["saved"][0]["previous_result_stats"] == {
        "total": 8,
        "new": 4,
        "high_score": 2,
    }
    assert state["saved"][0]["last_result_stats"]["total"] == 12


def test_record_search_run_ignores_non_matching_configs(tmp_path):
    path = tmp_path / "saved_searches.json"

    save_named_search("Remote", {"preset": "remote-backend"}, path=path)
    state = record_search_run({"preset": "contract"}, {"total": 2}, path=path)

    assert "run_count" not in state["saved"][0]


def test_format_run_summary_handles_never_run_item():
    assert format_run_summary({}) == "Not run yet"


def test_format_run_summary_includes_result_counts():
    item = {
        "run_count": 2,
        "last_result_stats": {"total": 12, "new": 5, "high_score": 3},
    }

    assert format_run_summary(item) == "Last run: 12 results, 5 new, 3 high-score | 2 runs"


def test_format_run_summary_includes_review_counts_when_present():
    item = {
        "run_count": 2,
        "last_result_stats": {
            "total": 12,
            "new": 5,
            "high_score": 3,
            "review": {"shortlisted": 2, "maybe_later": 1, "dismissed": 0},
        },
    }

    assert format_run_summary(item) == (
        "Last run: 12 results, 5 new, 3 high-score, "
        "2 shortlisted, 1 maybe later | 2 runs"
    )


def test_format_run_summary_includes_previous_total_delta():
    item = {
        "run_count": 2,
        "previous_result_stats": {"total": 8, "new": 2, "high_score": 1},
        "last_result_stats": {"total": 12, "new": 5, "high_score": 3},
    }

    assert format_run_summary(item) == (
        "Last run: 12 results, +4 vs previous, 5 new, 3 high-score | 2 runs"
    )


def test_format_search_insight_waits_for_completed_runs():
    assert format_search_insight({}) == "Comparison starts after the first completed run."
    assert format_search_insight({"last_result_stats": {"total": 8}}) == (
        "Comparison starts after the next completed run."
    )


def test_format_search_insight_summarizes_result_deltas():
    item = {
        "previous_result_stats": {"total": 8, "new": 2, "high_score": 1},
        "last_result_stats": {"total": 12, "new": 5, "high_score": 3},
    }

    assert format_search_insight(item) == (
        "Change: +4 total, +3 new, +2 high-score vs previous."
    )


def test_format_search_insight_includes_review_state_deltas():
    item = {
        "previous_result_stats": {
            "total": 12,
            "new": 5,
            "high_score": 3,
            "review": {"shortlisted": 1, "maybe_later": 2, "dismissed": 4},
        },
        "last_result_stats": {
            "total": 12,
            "new": 5,
            "high_score": 3,
            "review": {"shortlisted": 3, "maybe_later": 1, "dismissed": 4},
        },
    }

    assert format_search_insight(item) == (
        "Change: review: +2 shortlisted, -1 maybe later vs previous."
    )


def test_format_search_insight_handles_flat_runs():
    item = {
        "previous_result_stats": {"total": 8, "new": 2, "high_score": 1},
        "last_result_stats": {"total": 8, "new": 2, "high_score": 1},
    }

    assert format_search_insight(item) == "No result movement since the previous run."


def test_prioritize_changed_searches_surfaces_largest_changes_first():
    items = [
        {
            "name": "No change",
            "previous_result_stats": {"total": 5, "new": 1, "high_score": 1},
            "last_result_stats": {"total": 5, "new": 1, "high_score": 1},
        },
        {
            "name": "Small change",
            "previous_result_stats": {"total": 5, "new": 1, "high_score": 1},
            "last_result_stats": {"total": 6, "new": 1, "high_score": 1},
        },
        {
            "name": "Large change",
            "previous_result_stats": {
                "total": 5,
                "new": 1,
                "high_score": 1,
                "review": {"shortlisted": 0},
            },
            "last_result_stats": {
                "total": 9,
                "new": 3,
                "high_score": 2,
                "review": {"shortlisted": 2},
            },
        },
    ]

    prioritized = prioritize_changed_searches(items, limit=2)

    assert [item["name"] for item in prioritized] == ["Large change", "Small change"]


def test_prioritize_changed_searches_preserves_order_for_ties():
    items = [{"name": "First"}, {"name": "Second"}, {"name": "Third"}]

    prioritized = prioritize_changed_searches(items, limit=2)

    assert [item["name"] for item in prioritized] == ["First", "Second"]
