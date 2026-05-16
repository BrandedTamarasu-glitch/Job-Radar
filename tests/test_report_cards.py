"""Tests for hero and recommended report card rendering."""

from __future__ import annotations

from job_radar.report_cards import html_hero_section, html_job_card, html_recommended_section


def _result(job, *, score: float = 3.7, is_new: bool = True) -> dict:
    return {
        "job": job,
        "score": {
            "overall": score,
            "recommendation": "Good match",
            "components": {
                "skill_match": {
                    "ratio": "2/3",
                    "matched_core": ["Python", "FastAPI"],
                    "missing_core": ["PostgreSQL"],
                    "matched_secondary": ["Docker"],
                },
                "title_relevance": {"reason": "Related"},
                "seniority": {"reason": "Matches level"},
                "response": {"likelihood": "High", "reason": "Strong fit"},
            },
        },
        "is_new": is_new,
    }


def test_html_job_card_renders_recommended_card(job_factory, sample_profile):
    card = html_job_card(_result(job_factory(), score=3.7), 1, sample_profile)

    assert 'class="card mb-3 job-item tier-rec"' in card
    assert 'tabindex="0"' in card
    assert "1. Senior Python Developer" in card
    assert "TestCorp" in card
    assert "Why this matched:" in card
    assert "Stack match:</strong> 2/3" in card
    assert "Missing must-have skills" in card
    assert "Nice-to-have matches" in card
    assert 'aria-label="Change application status"' in card
    assert 'data-review-state="shortlisted"' in card
    assert "Top Match" not in card


def test_html_hero_section_renders_heading_action_bar_and_cards(job_factory, sample_profile):
    section = html_hero_section([_result(job_factory(), score=4.2)], sample_profile)

    assert 'aria-labelledby="hero-heading"' in section
    assert 'class="hero-jobs-section"' in section
    assert "Top Matches (Score >= 4.0)" in section
    assert "Copy All Top Match URLs" in section
    assert 'onclick="copyAllHeroUrls(this)"' in section
    assert "Top Match" in section
    assert "Senior Python Developer" in section


def test_html_hero_section_omits_empty_section(sample_profile):
    assert html_hero_section([], sample_profile) == ""


def test_html_job_card_renders_hero_card_with_top_match_label(job_factory, sample_profile):
    card = html_job_card(_result(job_factory(), score=4.2), 2, sample_profile, hero=True)

    assert 'class="card mb-3 job-item hero-job tier-strong"' in card
    assert "2. Senior Python Developer" in card
    assert "Top Match" in card
    assert "New listing, not seen in previous searches" in card


def test_html_recommended_section_renders_heading_action_bar_and_cards(job_factory, sample_profile):
    section = html_recommended_section([_result(job_factory(), score=3.7)], sample_profile)

    assert 'aria-labelledby="recommended-heading"' in section
    assert "Recommended Roles (Score 3.5 - 3.9)" in section
    assert "Copy All Recommended URLs" in section
    assert 'onclick="copyAllRecommendedUrls(this)"' in section
    assert "Export Status Updates" in section
    assert "Senior Python Developer" in section


def test_html_recommended_section_renders_empty_state(sample_profile):
    section = html_recommended_section([], sample_profile)

    assert 'aria-labelledby="recommended-heading"' in section
    assert "No results scored 3.5 to 3.9 in this search run." in section
    assert "Copy All Recommended URLs" not in section


def test_html_job_card_escapes_text_and_neutralizes_unsafe_urls(job_factory, sample_profile):
    job = job_factory(
        title="<Backend>",
        company="<Acme>",
        url="javascript:alert(1)",
    )

    card = html_job_card(_result(job, is_new=False), 1, sample_profile)

    assert "<Backend>" not in card
    assert "&lt;Backend&gt;" in card
    assert "<Acme>" not in card
    assert "&lt;Acme&gt;" in card
    assert "javascript:alert" not in card
    assert 'class="card mb-3 tier-rec"' in card
    assert 'tabindex="0"' not in card
    assert "New listing, not seen in previous searches" not in card
