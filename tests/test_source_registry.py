"""Tests for shared source registry helpers."""

from job_radar.source_registry import (
    ManualSourceDefinition,
    SourceDefinition,
    selected_automated_source_display_names,
    selected_manual_source_display_names,
    source_queries_by_phase,
    source_display_name,
)


def _fetch(query: dict, profile: dict) -> list[dict]:
    return [{"query": query, "profile": profile}]


def _manual_url(title: str, location: str) -> str:
    return f"https://example.com/jobs?q={title}&l={location}"


def test_source_definition_runs_fetcher():
    definition = SourceDefinition("dice", "Dice", "scraper", _fetch)

    assert definition.fetch({"query": "python"}, {"location": "Remote"}) == [
        {"query": {"query": "python"}, "profile": {"location": "Remote"}}
    ]


def test_selected_automated_source_display_names_follow_phase_order():
    registry = {
        "agg": SourceDefinition("agg", "Aggregator", "aggregator", _fetch),
        "api": SourceDefinition("api", "API Source", "api", _fetch),
        "scraper": SourceDefinition("scraper", "Scraper", "scraper", _fetch),
    }

    assert selected_automated_source_display_names(
        registry,
        ("scraper", "api", "aggregator"),
        ["agg", "scraper"],
    ) == ["Scraper", "Aggregator"]


def test_selected_automated_source_display_names_respects_empty_selection():
    registry = {
        "scraper": SourceDefinition("scraper", "Scraper", "scraper", _fetch),
    }

    assert selected_automated_source_display_names(registry, ("scraper",), []) == []


def test_selected_manual_source_display_names_respects_selection():
    registry = {
        "wellfound": ManualSourceDefinition("wellfound", "Wellfound", _manual_url),
        "linkedin": ManualSourceDefinition("linkedin", "LinkedIn", _manual_url),
    }

    assert selected_manual_source_display_names(registry, ["linkedin"]) == ["LinkedIn"]


def test_source_display_name_uses_registry_then_fallback_then_source_key():
    registry = {
        "dice": SourceDefinition("dice", "Dice", "scraper", _fetch),
    }

    assert source_display_name(registry, {"legacy": "Legacy"}, "dice") == "Dice"
    assert source_display_name(registry, {"legacy": "Legacy"}, "legacy") == "Legacy"
    assert source_display_name(registry, {"legacy": "Legacy"}, "unknown") == "unknown"


def test_source_queries_by_phase_filters_and_groups_known_sources():
    registry = {
        "dice": SourceDefinition("dice", "Dice", "scraper", _fetch),
        "adzuna": SourceDefinition("adzuna", "Adzuna", "api", _fetch),
        "jsearch": SourceDefinition("jsearch", "JSearch", "aggregator", _fetch),
    }
    queries = [
        {"source": "jsearch", "query": "backend"},
        {"source": "dice", "query": "backend"},
        {"source": "unknown", "query": "backend"},
        {"source": "adzuna", "query": "backend"},
    ]

    filtered, grouped = source_queries_by_phase(
        queries,
        registry,
        ("scraper", "api", "aggregator"),
        selected_sources=["dice", "jsearch", "unknown"],
    )

    assert filtered == queries[:3]
    assert grouped == {
        "scraper": [{"source": "dice", "query": "backend"}],
        "api": [],
        "aggregator": [{"source": "jsearch", "query": "backend"}],
    }


def test_source_queries_by_phase_respects_empty_selection():
    registry = {
        "dice": SourceDefinition("dice", "Dice", "scraper", _fetch),
    }

    filtered, grouped = source_queries_by_phase(
        [{"source": "dice", "query": "backend"}],
        registry,
        ("scraper",),
        selected_sources=[],
    )

    assert filtered == []
    assert grouped == {"scraper": []}
