from job_radar.profile_readiness import (
    assess_profile_readiness,
    readiness_guidance_lines,
    scoring_signal_guidance_lines,
)


def test_profile_readiness_flags_missing_required_fields():
    readiness = assess_profile_readiness({})

    assert readiness.status == "Needs setup"
    assert readiness.is_search_ready is False
    assert "Add your name" in readiness.missing_required
    assert "Add at least one target title" in readiness.missing_required
    assert "Add at least one core skill" in readiness.missing_required


def test_profile_readiness_marks_complete_profile_strong():
    readiness = assess_profile_readiness(
        {
            "name": "Test User",
            "target_titles": ["Backend Engineer"],
            "core_skills": ["Python", "PostgreSQL"],
            "secondary_skills": ["Docker"],
            "years_experience": 6,
            "location": "Remote",
            "arrangement": ["remote"],
            "dealbreakers": ["relocation required"],
            "comp_floor": 130000,
        }
    )

    assert readiness.status == "Strong"
    assert readiness.score == readiness.max_score
    assert readiness.is_search_ready is True
    assert readiness.missing_required == ()


def test_profile_readiness_recommends_match_quality_fields():
    readiness = assess_profile_readiness(
        {
            "name": "Test User",
            "target_titles": ["Backend Engineer"],
            "core_skills": ["Python"],
        }
    )

    assert readiness.status == "Basic"
    assert readiness.is_search_ready is True
    assert readiness.missing_required == ()
    assert any("years of experience" in item for item in readiness.recommendations)
    assert any("target location" in item for item in readiness.recommendations)
    assert any("Seniority signal" in item for item in readiness.scoring_signal_recommendations)
    assert any("Location signal" in item for item in readiness.scoring_signal_recommendations)


def test_profile_readiness_recommends_scoring_signal_specific_fields():
    readiness = assess_profile_readiness(
        {
            "name": "Test User",
            "target_titles": ["Backend Engineer"],
            "core_skills": ["Python"],
            "years_experience": 6,
            "location": "Remote",
            "arrangement": ["remote"],
            "dealbreakers": ["relocation required"],
        }
    )

    assert any("Title relevance signal" in item for item in readiness.scoring_signal_recommendations)
    assert any("Skill match signal" in item for item in readiness.scoring_signal_recommendations)
    assert any("Domain signal" in item for item in readiness.scoring_signal_recommendations)


def test_readiness_guidance_prioritizes_missing_required_fields():
    readiness = assess_profile_readiness({})

    lines = readiness_guidance_lines(readiness, limit=2)

    assert lines == ["Add your name", "Add at least one target title"]


def test_readiness_guidance_omits_strong_profiles():
    readiness = assess_profile_readiness(
        {
            "name": "Test User",
            "target_titles": ["Backend Engineer"],
            "core_skills": ["Python", "PostgreSQL"],
            "secondary_skills": ["Docker"],
            "years_experience": 6,
            "location": "Remote",
            "arrangement": ["remote"],
            "dealbreakers": ["relocation required"],
        }
    )

    assert readiness_guidance_lines(readiness) == []


def test_scoring_signal_guidance_limits_signal_recommendations():
    readiness = assess_profile_readiness(
        {
            "name": "Test User",
            "target_titles": ["Backend Engineer"],
            "core_skills": ["Python"],
        }
    )

    lines = scoring_signal_guidance_lines(readiness, limit=2)

    assert len(lines) == 2
    assert lines[0].startswith("Title relevance signal:")
    assert lines[1].startswith("Skill match signal:")
