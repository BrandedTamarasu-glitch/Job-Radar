from types import SimpleNamespace

from job_radar.gui.profile_view_model import (
    build_profile_readiness_display,
    build_profile_summary_rows,
    profile_load_error_message,
)


def test_build_profile_summary_rows_formats_core_and_optional_fields():
    rows = build_profile_summary_rows({
        "name": "Test User",
        "target_titles": ["Backend Engineer", "Platform Engineer"],
        "core_skills": ["Python", "Docker"],
        "secondary_skills": ["React"],
        "level": "senior",
        "years_experience": 8,
        "location": "Remote",
        "arrangement": ["remote", "hybrid"],
        "dealbreakers": ["onsite only"],
        "comp_floor": 150000,
    })

    by_label = {row.label: row.value for row in rows}

    assert by_label["Name:"] == "Test User"
    assert by_label["Target Titles:"] == "Backend Engineer, Platform Engineer"
    assert by_label["Core Skills:"] == "Python, Docker"
    assert by_label["Secondary Skills:"] == "React"
    assert by_label["Level / Experience:"] == "senior / 8 years"
    assert by_label["Location / Arrangement:"] == "Remote / remote, hybrid"
    assert by_label["Dealbreakers:"] == "onsite only"
    assert by_label["Compensation Floor:"] == "$150,000"


def test_build_profile_summary_rows_uses_defaults_and_skips_empty_optional_fields():
    rows = build_profile_summary_rows({})
    by_label = {row.label: row.value for row in rows}

    assert by_label["Name:"] == "N/A"
    assert by_label["Target Titles:"] == "N/A"
    assert by_label["Core Skills:"] == "N/A"
    assert by_label["Level / Experience:"] == "N/A / N/A years"
    assert by_label["Location / Arrangement:"] == "N/A / N/A"
    assert "Secondary Skills:" not in by_label
    assert "Dealbreakers:" not in by_label
    assert "Compensation Floor:" not in by_label


def test_profile_load_error_message_includes_error_detail():
    assert profile_load_error_message(ValueError("bad json")) == "Could not load profile: bad json"


def test_build_profile_readiness_display_formats_summary_and_guidance():
    readiness = SimpleNamespace(
        status="Needs Work",
        score=3,
        max_score=5,
        missing_required=["Add target titles", "Add core skills"],
        recommendations=["Add location"],
    )

    display = build_profile_readiness_display(readiness, ["Signal one", "Signal two"])

    assert display.summary == "Needs Work (3/5)"
    assert display.guidance_text == "- Add target titles\n- Add core skills"
    assert display.scoring_signals_text == "Signal one\nSignal two"


def test_build_profile_readiness_display_falls_back_to_recommendations():
    readiness = SimpleNamespace(
        status="Ready",
        score=5,
        max_score=5,
        missing_required=[],
        recommendations=["Improve location", "Add highlights", "Add salary", "Ignored"],
    )

    display = build_profile_readiness_display(readiness, [])

    assert display.summary == "Ready (5/5)"
    assert display.guidance_text == "- Improve location\n- Add highlights\n- Add salary"
    assert display.scoring_signals_text is None
