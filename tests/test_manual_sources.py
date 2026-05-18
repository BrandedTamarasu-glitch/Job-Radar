"""Tests for manual source URL generation helpers."""

from job_radar.manual_sources import (
    MANUAL_SOURCE_REGISTRY,
    _slugify_for_wellfound,
    generate_manual_urls,
    generate_wellfound_url,
    get_manual_source_display_names,
)


def test_wellfound_url_uses_remote_role_path():
    assert (
        generate_wellfound_url("Backend Developer", "Remote - US")
        == "https://wellfound.com/role/r/backend-developer"
    )


def test_wellfound_url_slugifies_role_and_location():
    assert (
        generate_wellfound_url("Senior Full-Stack Engineer", "New York, NY")
        == "https://wellfound.com/role/l/senior-full-stack-engineer/new-york-ny"
    )


def test_slugify_for_wellfound_collapses_separators():
    assert _slugify_for_wellfound("  Staff, Platform  Engineer!! ") == "staff-platform-engineer"


def test_generate_manual_urls_filters_selected_sources():
    urls = generate_manual_urls(
        {
            "target_titles": ["Software Engineer", "Backend Engineer"],
            "target_market": "Remote",
        },
        selected_manual_sources=["linkedin"],
    )

    assert [url["source"] for url in urls] == ["LinkedIn", "LinkedIn"]


def test_manual_display_names_follow_registry_order():
    assert get_manual_source_display_names() == [
        source.display_name for source in MANUAL_SOURCE_REGISTRY.values()
    ]
