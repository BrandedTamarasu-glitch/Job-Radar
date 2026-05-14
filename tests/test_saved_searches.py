import json
from datetime import datetime, timezone

from job_radar.saved_searches import (
    load_search_history,
    normalize_search_config,
    record_recent_search,
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
