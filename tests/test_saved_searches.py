import json
from datetime import datetime, timezone

from job_radar.saved_searches import (
    delete_named_search,
    load_search_history,
    normalize_search_config,
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
        "unknown": "ignored",
    }

    normalized = normalize_search_config(config)

    assert normalized["preset"] == "remote-backend"
    assert normalized["min_score"] == 3.2
    assert normalized["new_only"] is True
    assert normalized["selected_sources"] == ["remoteok", "dice"]
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


def test_record_search_run_ignores_non_matching_configs(tmp_path):
    path = tmp_path / "saved_searches.json"

    save_named_search("Remote", {"preset": "remote-backend"}, path=path)
    state = record_search_run({"preset": "contract"}, {"total": 2}, path=path)

    assert "run_count" not in state["saved"][0]
