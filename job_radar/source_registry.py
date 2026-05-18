"""Shared source registry definitions and display-name helpers."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceDefinition:
    """Metadata and query runner for an automated job source."""

    key: str
    display_name: str
    phase: str
    fetcher: Callable[[dict, dict], list[Any]]

    def fetch(self, query: dict, profile: dict) -> list[Any]:
        """Run this source's fetcher for one query dict."""
        return self.fetcher(query, profile)


@dataclass(frozen=True)
class ManualSourceDefinition:
    """Metadata and URL generator for manual check sources."""

    key: str
    display_name: str
    generator: Callable[[str, str], str]


SOURCE_PHASE_ORDER = ("scraper", "api", "aggregator")

_AUTOMATED_SOURCE_SPECS = (
    ("dice", "Dice", "scraper"),
    ("hn_hiring", "HN Hiring", "scraper"),
    ("remoteok", "RemoteOK", "scraper"),
    ("weworkremotely", "We Work Remotely", "scraper"),
    ("adzuna", "Adzuna", "api"),
    ("authentic_jobs", "Authentic Jobs", "api"),
    ("usajobs", "USAJobs (Federal)", "api"),
    ("jobicy", "Jobicy (Remote)", "api"),
    ("hiringcafe", "hiring.cafe", "api"),
    ("jsearch", "JSearch", "aggregator"),
    ("serpapi", "SerpAPI (Google Jobs)", "aggregator"),
)


def build_source_registry(
    fetchers: Mapping[str, Callable[[dict, dict], list[Any]]],
) -> dict[str, SourceDefinition]:
    """Build the automated source registry from per-source query fetchers."""
    return {
        key: SourceDefinition(key, display_name, phase, fetchers[key])
        for key, display_name, phase in _AUTOMATED_SOURCE_SPECS
    }


def selected_automated_source_display_names(
    registry: Mapping[str, SourceDefinition],
    phase_order: Sequence[str],
    selected_sources: Sequence[str] | None = None,
) -> list[str]:
    """Return automated source display names in phase order."""
    selected = set(selected_sources) if selected_sources is not None else None
    return [
        source.display_name
        for phase in phase_order
        for source in registry.values()
        if source.phase == phase
        and (selected is None or source.key in selected)
    ]


def selected_manual_source_display_names(
    registry: Mapping[str, ManualSourceDefinition],
    selected_sources: Sequence[str] | None = None,
) -> list[str]:
    """Return manual source display names in registry order."""
    selected = set(selected_sources) if selected_sources is not None else None
    return [
        source.display_name
        for source in registry.values()
        if selected is None or source.key in selected
    ]


def source_queries_by_phase(
    queries: Sequence[Mapping[str, Any]],
    registry: Mapping[str, SourceDefinition],
    phase_order: Sequence[str],
    selected_sources: Sequence[str] | None = None,
) -> tuple[list[Mapping[str, Any]], dict[str, list[Mapping[str, Any]]]]:
    """Filter queries by selected source keys and group known sources by phase."""
    selected = set(selected_sources) if selected_sources is not None else None
    filtered_queries = [
        query for query in queries
        if selected is None or query.get("source") in selected
    ]
    grouped_queries = {
        phase: [
            query for query in filtered_queries
            if query.get("source") in registry
            and registry[str(query["source"])].phase == phase
        ]
        for phase in phase_order
    }
    return filtered_queries, grouped_queries


def source_display_name(
    registry: Mapping[str, SourceDefinition],
    fallback_names: Mapping[str, str],
    source: str,
) -> str:
    """Return a human-readable source name from the registry or fallback map."""
    definition = registry.get(source)
    if definition:
        return definition.display_name
    return fallback_names.get(source, source)
