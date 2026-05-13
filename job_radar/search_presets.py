"""Reusable search presets for common job search modes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchPreset:
    """A named, in-memory overlay for a candidate profile."""

    name: str
    description: str
    title_prefix: tuple[str, ...] = ()
    overrides: dict[str, Any] | None = None


SEARCH_PRESETS: dict[str, SearchPreset] = {
    "remote-backend": SearchPreset(
        name="remote-backend",
        description="Prioritize remote backend, Python, and API engineering searches.",
        title_prefix=(
            "Senior Backend Engineer",
            "Backend Engineer",
            "Python Developer",
            "API Engineer",
        ),
        overrides={
            "location": "Remote",
            "target_market": "Remote",
            "arrangement": ["remote"],
        },
    ),
    "local-hybrid": SearchPreset(
        name="local-hybrid",
        description="Keep your local market while emphasizing hybrid roles.",
        overrides={
            "arrangement": ["hybrid"],
        },
    ),
    "contract": SearchPreset(
        name="contract",
        description="Bias searches toward contract and freelance engineering roles.",
        title_prefix=(
            "Contract Software Engineer",
            "Contract Backend Engineer",
            "Freelance Python Developer",
        ),
    ),
}


def preset_choices() -> list[str]:
    """Return preset names in stable display order."""
    return list(SEARCH_PRESETS)


def format_preset_list() -> str:
    """Return a printable preset list for CLI help output."""
    lines = ["Available search presets:"]
    for preset in SEARCH_PRESETS.values():
        lines.append(f"  {preset.name:15} {preset.description}")
    return "\n".join(lines)


def apply_search_preset(profile: dict, preset_name: str | None) -> dict:
    """Apply a preset to a profile without mutating the original profile."""
    if not preset_name:
        return deepcopy(profile)

    preset = SEARCH_PRESETS[preset_name]
    result = deepcopy(profile)

    if preset.title_prefix:
        result["target_titles"] = _dedupe(
            list(preset.title_prefix) + list(result.get("target_titles", []))
        )

    for key, value in (preset.overrides or {}).items():
        result[key] = deepcopy(value)

    return result


def _dedupe(items: list[str]) -> list[str]:
    """Deduplicate strings while preserving order."""
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped
