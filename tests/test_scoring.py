"""Parametrized tests for all scoring functions."""

import pytest
from job_radar.scoring import (
    _parse_salary_number,
    _check_dealbreakers,
    _score_skill_match,
    _score_title_relevance,
    _score_seniority,
    _score_location,
    _score_domain,
    _score_response_likelihood,
    score_job,
)


# ---------------------------------------------------------------------------
# Salary parsing tests (TEST-03)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("$120k", 120000.0),
    ("$60/hr", 124800.0),  # 60 * 2080
    ("$120,000", 120000.0),
    ("$150000", 150000.0),  # no comma, bare number > 1000
    ("Not listed", None),
    ("", None),
    (None, None),  # guard against None input
    ("Competitive salary", None),  # non-numeric text
    ("$100k-$150k", 100000.0),  # range: parses first number with k suffix
], ids=[
    "$120k",
    "$60/hr_hourly",
    "$120,000_with_comma",
    "$150000_bare",
    "Not_listed",
    "empty_string",
    "None_input",
    "non_numeric",
    "range_format",
])
def test_parse_salary_number(text, expected):
    """Test salary parsing with various formats (TEST-03)."""
    result = _parse_salary_number(text)
    if expected is None:
        assert result is None
    else:
        assert result == expected


# ---------------------------------------------------------------------------
# Dealbreaker detection tests (TEST-02)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("description,dealbreakers,expected", [
    ("Must relocate to NYC", ["relocate"], "relocate"),  # exact match
    ("Requires on-site presence daily", ["on-site"], "on-site"),  # substring
    ("RELOCATION REQUIRED for role", ["relocation"], "relocation"),  # case-insensitive
    ("Remote-friendly distributed team", ["on-site"], None),  # no match
    ("Any description text here", [], None),  # empty dealbreakers
], ids=[
    "exact_match",
    "substring_match",
    "case_insensitive",
    "no_match",
    "empty_dealbreakers",
])
def test_check_dealbreakers(job_factory, description, dealbreakers, expected):
    """Test dealbreaker detection with exact/substring/case-insensitive matching (TEST-02)."""
    job = job_factory(description=description)
    profile = {"dealbreakers": dealbreakers}
    result = _check_dealbreakers(job, profile)
    assert result == expected


# ---------------------------------------------------------------------------
# Skill matching tests (TEST-01)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("core_skills,secondary_skills,description,expected_min,expected_max", [
    (["Python", "FastAPI"], [], "Python and FastAPI developer", 4.0, 5.0),  # all core match
    (["Rust", "Haskell"], [], "Python and FastAPI developer", 1.0, 1.5),  # no match
    (["Python"], ["Docker"], "Python and Docker developer", 3.0, 5.0),  # secondary match
    ([], [], "Python developer", 1.0, 1.0),  # empty skills (ratio=0 -> score=1.0)
], ids=[
    "all_core_match",
    "no_match",
    "secondary_match",
    "empty_skills",
])
def test_score_skill_match(job_factory, core_skills, secondary_skills, description, expected_min, expected_max):
    """Test skill matching with core and secondary skills (TEST-01)."""
    job = job_factory(description=description)
    profile = {
        "core_skills": core_skills,
        "secondary_skills": secondary_skills,
    }
    result = _score_skill_match(job, profile)
    assert "score" in result
    assert expected_min <= result["score"] <= expected_max


# ---------------------------------------------------------------------------
# Fuzzy variant matching tests (TEST-GAP-01 - v1.0 milestone audit)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("core_skills,description,expected_in_matched", [
    (["node.js"], "Looking for a NodeJS developer", "node.js"),  # nodejs variant
    (["kubernetes"], "Experience with k8s required", "kubernetes"),  # k8s variant
    ([".NET"], "Must know dotnet framework", ".NET"),  # dotnet variant
    (["C#"], "Seeking csharp programmer", "C#"),  # csharp variant
    (["python"], "Need python3 scripting skills", "python"),  # python3 variant
    (["go"], "Backend role using golang", "go"),  # golang variant (not "going")
], ids=[
    "nodejs_variant",
    "k8s_variant",
    "dotnet_variant",
    "csharp_variant",
    "python3_variant",
    "go_boundary_with_golang",
])
def test_score_skill_match_fuzzy_variants(job_factory, core_skills, description, expected_in_matched):
    """Test cross-variant skill matching (TEST-GAP-01).

    Regression tests for fuzzy normalization: profile skill in one form should match
    job text containing a different variant form. Covers all 4 audit-identified pairs
    plus additional boundary cases.
    """
    job = job_factory(description=description)
    profile = {
        "core_skills": core_skills,
        "secondary_skills": [],
    }
    result = _score_skill_match(job, profile)

    # Single core skill matched: ratio=1.0 -> score = 1.0 + 1.0*4.0 = 5.0
    assert result["score"] >= 4.0, f"Expected high score for matched variant, got {result['score']}"
    assert expected_in_matched in result["matched_core"], \
        f"Expected '{expected_in_matched}' in matched_core, got {result['matched_core']}"


# ---------------------------------------------------------------------------
# Title relevance tests (TEST-01)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("job_title,target_titles,expected_min", [
    ("Senior Python Developer", ["Senior Python Developer"], 5.0),  # exact match
    ("Senior Python Developer II", ["Senior Python Developer"], 4.0),  # contained match
    ("Python Software Engineer", ["Senior Python Developer"], 2.0),  # word overlap
    ("Marketing Manager", ["Senior Python Developer"], 1.0),  # no match
    ("Any Title", [], 3.0),  # no target titles (default neutral)
], ids=[
    "exact_match",
    "contained_match",
    "word_overlap",
    "no_match",
    "no_target_titles",
])
def test_score_title_relevance(job_factory, job_title, target_titles, expected_min):
    """Test title relevance scoring (TEST-01)."""
    job = job_factory(title=job_title)
    profile = {"target_titles": target_titles}
    result = _score_title_relevance(job, profile)
    assert "score" in result
    assert result["score"] >= expected_min


# ---------------------------------------------------------------------------
# Seniority alignment tests (TEST-01)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("job_title,level,years,expected_min,expected_max", [
    ("Senior Developer", "senior", 7, 4.5, 5.0),  # match
    ("Junior Developer", "senior", 7, 1.0, 2.0),  # mismatch
    ("Developer", "mid", 5, 3.0, 4.0),  # unknown level
], ids=[
    "match",
    "mismatch",
    "unknown_level",
])
def test_score_seniority(job_factory, job_title, level, years, expected_min, expected_max):
    """Test seniority alignment scoring (TEST-01)."""
    job = job_factory(title=job_title)
    profile = {
        "level": level,
        "years_experience": years,
    }
    result = _score_seniority(job, profile)
    assert "score" in result
    assert expected_min <= result["score"] <= expected_max


# ---------------------------------------------------------------------------
# Location/arrangement tests (TEST-01)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("arrangement,candidate_arrangements,expected_min", [
    ("remote", ["remote", "hybrid"], 5.0),  # remote match
    ("onsite", ["remote"], 1.0),  # onsite wrong location
    ("unknown", ["remote"], 2.5),  # unknown arrangement
], ids=[
    "remote_match",
    "onsite_wrong_location",
    "unknown_arrangement",
])
def test_score_location(job_factory, arrangement, candidate_arrangements, expected_min):
    """Test location and arrangement scoring (TEST-01)."""
    job = job_factory(arrangement=arrangement, location="Unknown City")
    profile = {"arrangement": candidate_arrangements}
    result = _score_location(job, profile)
    assert "score" in result
    assert result["score"] >= expected_min


# ---------------------------------------------------------------------------
# Domain relevance tests (TEST-01)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("description,domains,expected_min", [
    ("fintech startup hiring", ["fintech"], 4.0),  # domain match
    ("retail company hiring", ["fintech", "healthcare"], 3.0),  # no match
    ("any description", [], 3.0),  # no domains set
], ids=[
    "domain_match",
    "no_match",
    "no_domains_set",
])
def test_score_domain(job_factory, description, domains, expected_min):
    """Test domain relevance scoring (TEST-01)."""
    job = job_factory(description=description)
    profile = {"domain_expertise": domains}
    result = _score_domain(job, profile)
    assert "score" in result
    assert result["score"] >= expected_min


# ---------------------------------------------------------------------------
# Response likelihood tests (TEST-01)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("company,source,description,expected_min", [
    ("Robert Half", "Dice", "standard listing", 4.0),  # staffing firm
    ("TestCo", "HN Hiring", "small team building", 3.0),  # HN source
    ("BigCorp", "Dice", "standard listing", 2.5),  # default
], ids=[
    "staffing_firm",
    "hn_source",
    "default",
])
def test_score_response_likelihood(job_factory, company, source, description, expected_min):
    """Test response likelihood scoring (TEST-01)."""
    job = job_factory(company=company, source=source, description=description)
    result = _score_response_likelihood(job)
    assert "score" in result
    assert result["score"] >= expected_min


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

def test_score_job_dealbreaker_returns_zero(job_factory, sample_profile):
    """Test that dealbreakers result in 0.0 overall score (Integration)."""
    job = job_factory(description="relocation required for this role")
    result = score_job(job, sample_profile)
    assert result["overall"] == 0.0
    assert result["dealbreaker"] == "relocation required"


def test_score_job_overall_range(job_factory, sample_profile):
    """Test that normal jobs score between 1.0 and 5.0 (Integration)."""
    job = job_factory()
    result = score_job(job, sample_profile)
    assert 1.0 <= result["overall"] <= 5.0
    assert "components" in result
    assert "recommendation" in result


# ---------------------------------------------------------------------------
# Configurable scoring weights (Phase 33-02)
# ---------------------------------------------------------------------------

def test_score_job_uses_profile_weights(job_factory):
    """Test that score_job uses profile scoring_weights instead of hardcoded values."""
    # Create a profile that heavily weights skill_match (0.60) and minimizes others
    profile_custom_weights = {
        "core_skills": ["Python", "FastAPI"],
        "secondary_skills": [],
        "target_titles": ["Backend Developer"],
        "level": "mid",
        "years_experience": 5,
        "arrangement": ["remote"],
        "location": "San Francisco",
        "domain_expertise": [],
        "scoring_weights": {
            "skill_match": 0.60,
            "title_relevance": 0.08,
            "seniority": 0.08,
            "location": 0.08,
            "domain": 0.08,
            "response_likelihood": 0.08,
        }
    }

    # Same profile with default weights
    profile_default_weights = {
        "core_skills": ["Python", "FastAPI"],
        "secondary_skills": [],
        "target_titles": ["Backend Developer"],
        "level": "mid",
        "years_experience": 5,
        "arrangement": ["remote"],
        "location": "San Francisco",
        "domain_expertise": [],
        # No scoring_weights - will use defaults (skill_match=0.25)
    }

    # Job with perfect skill match (5.0) but poor title match (1.5)
    job = job_factory(
        title="Marketing Manager",  # Poor title match
        description="Python and FastAPI expert needed",  # Perfect skill match
        arrangement="remote"
    )

    result_custom = score_job(job, profile_custom_weights)
    result_default = score_job(job, profile_default_weights)

    # With custom weights (skill_match=0.60), overall score should be higher
    # because skill_match has more weight despite poor title match
    assert result_custom["overall"] > result_default["overall"], \
        f"Custom weights (skill=0.60) should score higher than defaults (skill=0.25). " \
        f"Custom: {result_custom['overall']}, Default: {result_default['overall']}"


def test_score_job_default_weights_fallback(job_factory):
    """Test that score_job falls back to DEFAULT_SCORING_WEIGHTS when profile has no scoring_weights."""
    profile = {
        "core_skills": ["Python"],
        "target_titles": ["Developer"],
        "level": "mid",
        "years_experience": 5,
        # No scoring_weights key - should fall back gracefully
    }

    job = job_factory(description="Python developer needed")
    result = score_job(job, profile)

    # Should return a valid score without crashing
    assert "overall" in result
    assert 1.0 <= result["overall"] <= 5.0
    assert "components" in result


def test_score_stability_default_weights(job_factory):
    """Test that scores are identical when using explicit DEFAULT_SCORING_WEIGHTS vs no weights (fallback).

    CRITICAL: This ensures score stability during migration - existing profiles without
    scoring_weights should produce the same scores as before.
    """
    from job_radar.profile_manager import DEFAULT_SCORING_WEIGHTS

    # Profile WITH explicit default weights
    profile_explicit = {
        "core_skills": ["Python", "Docker"],
        "secondary_skills": ["Kubernetes"],
        "target_titles": ["DevOps Engineer"],
        "level": "senior",
        "years_experience": 7,
        "arrangement": ["remote"],
        "location": "Austin",
        "domain_expertise": ["fintech"],
        "scoring_weights": DEFAULT_SCORING_WEIGHTS,
    }

    # Profile WITHOUT scoring_weights (uses fallback)
    profile_fallback = {
        "core_skills": ["Python", "Docker"],
        "secondary_skills": ["Kubernetes"],
        "target_titles": ["DevOps Engineer"],
        "level": "senior",
        "years_experience": 7,
        "arrangement": ["remote"],
        "location": "Austin",
        "domain_expertise": ["fintech"],
        # No scoring_weights - will use DEFAULT_SCORING_WEIGHTS fallback
    }

    # Score the same job with both profiles
    job = job_factory(
        title="Senior DevOps Engineer",
        description="Python, Docker, Kubernetes required. Fintech experience preferred.",
        arrangement="remote",
        location="Remote"
    )

    result_explicit = score_job(job, profile_explicit)
    result_fallback = score_job(job, profile_fallback)

    # Overall scores MUST be identical (score stability)
    assert result_explicit["overall"] == result_fallback["overall"], \
        f"Scores must be identical for migration stability. " \
        f"Explicit: {result_explicit['overall']}, Fallback: {result_fallback['overall']}"


def test_score_job_custom_weights_math(job_factory):
    """Test that weighted sum calculation is correct with custom weights."""
    profile = {
        "core_skills": ["Python"],
        "target_titles": ["Developer"],
        "level": "mid",
        "years_experience": 5,
        "arrangement": ["remote"],
        "location": "Seattle",
        "domain_expertise": ["healthcare"],
        "scoring_weights": {
            "skill_match": 0.50,
            "title_relevance": 0.10,
            "seniority": 0.10,
            "location": 0.10,
            "domain": 0.10,
            "response_likelihood": 0.10,
        }
    }

    # Create a simple job to get predictable component scores
    job = job_factory(
        title="Python Developer",  # Good title match
        description="Python developer needed. Healthcare domain.",  # Skills + domain
        arrangement="remote",
        location="Remote",
        company="TestCo"
    )

    result = score_job(job, profile)

    # Manually calculate expected weighted sum
    components = result["components"]
    expected_overall = (
        components["skill_match"]["score"] * 0.50
        + components["title_relevance"]["score"] * 0.10
        + components["seniority"]["score"] * 0.10
        + components["location"]["score"] * 0.10
        + components["domain"]["score"] * 0.10
        + components["response"]["score"] * 0.10
    )

    # Round to match scoring.py rounding
    expected_overall = round(expected_overall, 1)

    assert result["overall"] == expected_overall, \
        f"Weighted sum mismatch. Expected: {expected_overall}, Got: {result['overall']}"


# ---------------------------------------------------------------------------
# Staffing firm preference (Phase 33-02)
# ---------------------------------------------------------------------------

def test_staffing_boost_adds_half_point(job_factory):
    """Test that staffing_preference='boost' adds +0.5 to staffing firm jobs."""
    profile_boost = {
        "core_skills": ["Python"],
        "target_titles": ["Developer"],
        "level": "mid",
        "years_experience": 5,
        "staffing_preference": "boost",
    }

    profile_neutral = {
        "core_skills": ["Python"],
        "target_titles": ["Developer"],
        "level": "mid",
        "years_experience": 5,
        "staffing_preference": "neutral",
    }

    # Staffing firm job
    job = job_factory(
        company="Robert Half",
        description="Python developer needed"
    )

    result_boost = score_job(job, profile_boost)
    result_neutral = score_job(job, profile_neutral)

    # Boost should be ~0.5 higher than neutral
    diff = result_boost["overall"] - result_neutral["overall"]
    assert 0.4 <= diff <= 0.6, \
        f"Boost should add ~0.5 points. Got diff: {diff}"
    assert "staffing_note" in result_boost["components"]


def test_staffing_penalize_subtracts_one_point(job_factory):
    """Test that staffing_preference='penalize' subtracts -1.0 from staffing firm jobs."""
    profile_penalize = {
        "core_skills": ["Python"],
        "target_titles": ["Developer"],
        "level": "mid",
        "years_experience": 5,
        "staffing_preference": "penalize",
    }

    profile_neutral = {
        "core_skills": ["Python"],
        "target_titles": ["Developer"],
        "level": "mid",
        "years_experience": 5,
        "staffing_preference": "neutral",
    }

    # Staffing firm job
    job = job_factory(
        company="TekSystems",
        description="Python developer needed"
    )

    result_penalize = score_job(job, profile_penalize)
    result_neutral = score_job(job, profile_neutral)

    # Penalize should be ~1.0 lower than neutral
    diff = result_neutral["overall"] - result_penalize["overall"]
    assert 0.9 <= diff <= 1.1, \
        f"Penalize should subtract ~1.0 points. Got diff: {diff}"
    assert "staffing_note" in result_penalize["components"]


def test_staffing_neutral_no_adjustment(job_factory):
    """Test that staffing_preference='neutral' applies no adjustment to staffing firm jobs."""
    profile = {
        "core_skills": ["Python"],
        "target_titles": ["Developer"],
        "level": "mid",
        "years_experience": 5,
        "staffing_preference": "neutral",
    }

    # Score a staffing firm job
    job_staffing = job_factory(
        company="Robert Half",
        description="Python developer needed"
    )

    # Score a non-staffing job
    job_direct = job_factory(
        company="TechCorp",
        description="Python developer needed"
    )

    result_staffing = score_job(job_staffing, profile)
    result_direct = score_job(job_direct, profile)

    # Both should have similar scores (no staffing adjustment)
    # Allow small variance from other factors but should be close
    assert abs(result_staffing["overall"] - result_direct["overall"]) <= 0.5
    assert "staffing_note" not in result_staffing["components"]


def test_staffing_preference_missing_defaults_neutral(job_factory):
    """Test that missing staffing_preference defaults to neutral (no adjustment)."""
    profile = {
        "core_skills": ["Python"],
        "target_titles": ["Developer"],
        "level": "mid",
        "years_experience": 5,
        # No staffing_preference key - should default to neutral
    }

    job = job_factory(
        company="Robert Half",
        description="Python developer needed"
    )

    result = score_job(job, profile)

    # Should score without crashing and no staffing adjustment
    assert "overall" in result
    assert 1.0 <= result["overall"] <= 5.0
    assert "staffing_note" not in result["components"]


def test_staffing_boost_capped_at_5(job_factory):
    """Test that staffing boost does not push score above 5.0."""
    profile = {
        "core_skills": ["Python", "FastAPI", "Docker"],
        "secondary_skills": ["Kubernetes", "PostgreSQL"],
        "target_titles": ["Senior Python Developer"],
        "level": "senior",
        "years_experience": 8,
        "arrangement": ["remote"],
        "location": "San Francisco",
        "domain_expertise": ["fintech"],
        "staffing_preference": "boost",
    }

    # Perfect match job from staffing firm
    job = job_factory(
        title="Senior Python Developer",
        description="Python, FastAPI, Docker, Kubernetes, PostgreSQL. Fintech domain. Remote.",
        company="Robert Half",
        arrangement="remote",
        location="Remote",
        source="Dice"
    )

    result = score_job(job, profile)

    # Score should not exceed 5.0 even with boost
    assert result["overall"] <= 5.0, \
        f"Score should be capped at 5.0, got {result['overall']}"


def test_staffing_penalize_floored_at_1(job_factory):
    """Test that staffing penalize does not push score below 1.0."""
    profile = {
        "core_skills": ["Rust", "Haskell"],
        "target_titles": ["Functional Programming Engineer"],
        "level": "junior",
        "years_experience": 1,
        "arrangement": ["onsite"],
        "location": "New York",
        "domain_expertise": ["cryptocurrency"],
        "staffing_preference": "penalize",
    }

    # Poor match job from staffing firm
    job = job_factory(
        title="Marketing Manager",
        description="Marketing role, no tech skills required",
        company="Robert Half",
        arrangement="remote",
        location="California",
        source="LinkedIn"
    )

    result = score_job(job, profile)

    # Score should not go below 1.0 even with penalize
    assert result["overall"] >= 1.0, \
        f"Score should be floored at 1.0, got {result['overall']}"


# ---------------------------------------------------------------------------
# Response likelihood without hardcoded staffing boost (Phase 33-02)
# ---------------------------------------------------------------------------

def test_response_likelihood_staffing_no_boost(job_factory):
    """Test that _score_response_likelihood no longer boosts staffing firms.

    The old hardcoded +4.5 boost has been removed from _score_response_likelihood().
    Staffing firm handling now lives in score_job() via staffing_preference.
    """
    job = job_factory(
        company="Robert Half",
        description="Standard listing"
    )

    result = _score_response_likelihood(job)

    # Should score 3.0 (base score), NOT 4.5 (old hardcoded boost removed)
    assert result["score"] == 3.0, \
        f"Staffing firms should score 3.0 base in _score_response_likelihood, got {result['score']}"

    # Reason should NOT mention staffing firm
    assert "staffing firm" not in result["reason"].lower(), \
        f"_score_response_likelihood should not mention staffing firms. Got: {result['reason']}"
