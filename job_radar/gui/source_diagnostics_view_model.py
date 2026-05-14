"""View-model helpers for source performance diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceDiagnosticRow:
    """Aggregated source health metrics for Settings diagnostics."""

    name: str
    runs: int = 0
    durations: list[float] = field(default_factory=list)
    total_jobs: int = 0
    warning_count: int = 0
    failure_count: int = 0

    @property
    def average_duration(self) -> float | None:
        if not self.durations:
            return None
        return sum(self.durations) / len(self.durations)

    @property
    def max_duration(self) -> float | None:
        if not self.durations:
            return None
        return max(self.durations)

    @property
    def health_label(self) -> str:
        """Return a compact source-health label for Settings diagnostics."""
        if self.failure_count:
            return "Needs attention"
        if self.warning_count:
            return "Watch"
        if self.average_duration is not None and self.average_duration >= 30:
            return "Slow"
        return "Healthy"

    @property
    def recommended_action(self) -> str:
        """Return a concise user-facing source-health recommendation."""
        if self.failure_count:
            return "retry later or uncheck this source in Search > Sources if failures continue"
        if self.warning_count:
            return "review warnings before relying on results"
        if self.average_duration is not None and self.average_duration >= 30:
            return "consider cache freshness or source timeout tuning"
        return "no action needed"

    @property
    def health_priority(self) -> int:
        """Return sort priority so unhealthy sources stay visible."""
        if self.failure_count:
            return 3
        if self.warning_count:
            return 2
        if self.average_duration is not None and self.average_duration >= 30:
            return 1
        return 0


def build_source_diagnostics(history: list[dict[str, Any]], limit: int = 5) -> list[SourceDiagnosticRow]:
    """Aggregate source health history into slowest-source diagnostics."""
    by_source: dict[str, SourceDiagnosticRow] = {}

    for run in history:
        for source in run.get("sources", []):
            name = source.get("name") or "Unknown source"
            row = by_source.setdefault(name, SourceDiagnosticRow(name=name))
            row.runs += 1
            row.total_jobs += int(source.get("job_count") or 0)
            row.warning_count += int(source.get("warning_count") or 0)
            if source.get("duration_seconds") is not None:
                row.durations.append(float(source["duration_seconds"]))

        for failed_name in run.get("failed_sources", []) or []:
            row = by_source.setdefault(failed_name, SourceDiagnosticRow(name=failed_name))
            row.failure_count += 1

    rows = list(by_source.values())
    rows.sort(
        key=lambda row: (
            row.health_priority,
            row.failure_count,
            row.warning_count,
            row.average_duration or -1,
            row.name.casefold(),
        ),
        reverse=True,
    )
    return rows[:limit]


def build_cache_totals(history: list[dict[str, Any]]) -> dict[str, int]:
    """Aggregate cache counters from source health history."""
    totals = {"hits": 0, "misses": 0, "writes": 0, "disabled": 0}
    for run in history:
        stats = run.get("cache_stats") or {}
        for key in totals:
            totals[key] += int(stats.get(key) or 0)
    return totals


def format_cache_freshness_line(cache_totals: dict[str, int]) -> str | None:
    """Return a compact cache freshness summary from aggregate counters."""
    hits = int(cache_totals.get("hits") or 0)
    misses = int(cache_totals.get("misses") or 0)
    disabled = int(cache_totals.get("disabled") or 0)
    total_reads = hits + misses + disabled
    if total_reads == 0:
        return None

    cache_percent = round((hits / total_reads) * 100)
    parts = [
        f"{cache_percent}% served from cache",
        f"{misses} live refreshes",
    ]
    if disabled:
        parts.append(f"{disabled} uncached requests")
    return "Cache freshness: " + ", ".join(parts)


def format_source_diagnostics_lines(
    history: list[dict[str, Any]],
    *,
    limit: int = 5,
) -> list[str]:
    """Return Settings-ready plain-text source diagnostic lines."""
    if not history:
        return ["No source diagnostics recorded yet. Run a search to populate this section."]

    lines = [
        "Source controls: use Search > Sources to temporarily disable unreliable sources, then refresh diagnostics after reruns."
    ]
    for row in build_source_diagnostics(history, limit=limit):
        duration_text = "timing unavailable"
        if row.average_duration is not None and row.max_duration is not None:
            duration_text = (
                f"avg {_format_duration(row.average_duration)}, "
                f"max {_format_duration(row.max_duration)}"
            )
        run_noun = "run" if row.runs == 1 else "runs"
        warning_noun = "warning" if row.warning_count == 1 else "warnings"
        failure_noun = "failure" if row.failure_count == 1 else "failures"
        lines.append(
            f"{row.name} ({row.health_label}): {duration_text}; {row.runs} {run_noun}; "
            f"{row.total_jobs} jobs; {row.warning_count} {warning_noun}; "
            f"{row.failure_count} {failure_noun}; {row.recommended_action}"
        )

    cache_totals = build_cache_totals(history)
    if any(cache_totals.values()):
        lines.append(
            "Cache totals: "
            f"{cache_totals['hits']} hits, "
            f"{cache_totals['misses']} misses, "
            f"{cache_totals['writes']} writes, "
            f"{cache_totals['disabled']} uncached requests"
        )
        freshness_line = format_cache_freshness_line(cache_totals)
        if freshness_line:
            lines.append(freshness_line)
    return lines


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining_seconds = int(round(seconds % 60))
    if remaining_seconds == 60:
        minutes += 1
        remaining_seconds = 0
    return f"{minutes}m {remaining_seconds:02d}s"
