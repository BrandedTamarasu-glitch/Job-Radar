from job_radar.gui.profile_view_model import (
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
