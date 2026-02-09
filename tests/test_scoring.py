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
