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
