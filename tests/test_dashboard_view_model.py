from types import SimpleNamespace

from job_radar.gui.dashboard_view_model import build_dashboard_actions


def readiness(status="Strong", score=4, max_score=4):
    return SimpleNamespace(status=status, score=score, max_score=max_score)


def test_dashboard_prioritizes_incomplete_profile():
    actions = build_dashboard_actions(
        readiness=readiness("Needs work", 2, 4),
        review_counts={"shortlisted": 2},
        next_actions=[],
        search_history={"recent": [{"name": "recent"}], "saved": []},
    )

    assert actions[0].title == "Review profile"
    assert actions[0].target == "Profile"


def test_dashboard_prioritizes_overdue_followups_after_profile_is_ready():
    actions = build_dashboard_actions(
        readiness=readiness(),
        review_counts={"shortlisted": 2},
        next_actions=[{"is_overdue": True, "days_until": -1}],
        search_history={"recent": [], "saved": [{"name": "daily"}]},
    )

    assert actions[0].title == "Handle overdue follow-ups"
    assert actions[0].target == "Applications"


def test_dashboard_surfaces_review_queue_before_saved_searches():
    actions = build_dashboard_actions(
        readiness=readiness(),
        review_counts={"shortlisted": 1, "maybe_later": 3},
        next_actions=[],
        search_history={"recent": [], "saved": [{"name": "daily"}]},
    )

    assert [action.title for action in actions[:2]] == [
        "Review saved search decisions",
        "Run a saved search",
    ]


def test_dashboard_calls_out_changed_saved_searches():
    actions = build_dashboard_actions(
        readiness=readiness(),
        review_counts={},
        next_actions=[],
        search_history={
            "recent": [],
            "saved": [
                {
                    "name": "daily",
                    "previous_result_stats": {"total": 8, "new": 2, "high_score": 1},
                    "last_result_stats": {"total": 12, "new": 2, "high_score": 1},
                },
                {
                    "name": "flat",
                    "previous_result_stats": {"total": 5, "new": 1, "high_score": 1},
                    "last_result_stats": {"total": 5, "new": 1, "high_score": 1},
                },
            ],
        },
    )

    assert actions[0].title == "Review changed saved searches"
    assert actions[0].detail == "1 saved search(es) changed since the previous run."
    assert actions[0].target == "Search"


def test_dashboard_bounds_large_changed_search_counts():
    changed_searches = [
        {
            "name": f"changed-{index}",
            "previous_result_stats": {"total": index, "new": 0, "high_score": 0},
            "last_result_stats": {"total": index + 1, "new": 0, "high_score": 0},
        }
        for index in range(150)
    ]

    actions = build_dashboard_actions(
        readiness=readiness(),
        review_counts={},
        next_actions=[],
        search_history={"recent": [], "saved": changed_searches},
    )

    assert len(actions) == 1
    assert actions[0].detail == "99+ saved search(es) changed since the previous run."


def test_dashboard_surfaces_maintenance_suggestions():
    actions = build_dashboard_actions(
        readiness=readiness(),
        review_counts={},
        next_actions=[],
        search_history={"recent": [{"name": "recent"}], "saved": []},
        maintenance_suggestions=["clear HTTP cache if source results feel stale"],
    )

    assert [action.title for action in actions[:2]] == [
        "Review maintenance suggestions",
        "Repeat a recent search",
    ]
    assert actions[0].target == "Settings"


def test_dashboard_defaults_to_first_search_when_history_is_empty():
    actions = build_dashboard_actions(
        readiness=readiness(),
        review_counts={},
        next_actions=[],
        search_history={"recent": [], "saved": []},
    )

    assert len(actions) == 1
    assert actions[0].title == "Run your first search"
    assert actions[0].target == "Search"


def test_dashboard_limits_output():
    actions = build_dashboard_actions(
        readiness=readiness("Partial", 3, 4),
        review_counts={"shortlisted": 1, "maybe_later": 1},
        next_actions=[{"is_overdue": True, "days_until": -1}],
        search_history={"recent": [{"name": "recent"}], "saved": [{"name": "daily"}]},
        limit=2,
    )

    assert len(actions) == 2
    assert [action.title for action in actions] == [
        "Review profile",
        "Handle overdue follow-ups",
    ]
