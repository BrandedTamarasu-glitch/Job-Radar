"""View-model helpers for source performance diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from job_radar.sources import get_source_display_name


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
        if self.failure_count >= 2 or self.reliability_score < 70:
            return "temporarily uncheck this source in Search > Sources, then retry later"
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

    @property
    def reliability_score(self) -> int:
        """Return a coarse 0-100 reliability score from recent source history."""
        if self.runs <= 0 and self.failure_count <= 0:
            return 0
        total_observations = max(1, self.runs + self.failure_count)
        penalty = (self.failure_count * 35) + (self.warning_count * 10)
        if self.average_duration is not None and self.average_duration >= 30:
            penalty += 10
        score = round(100 - (penalty / total_observations))
        return max(0, min(100, score))


def build_source_diagnostics(history: list[dict[str, Any]], limit: int = 5) -> list[SourceDiagnosticRow]:
    """Aggregate source health history into slowest-source diagnostics."""
    by_source: dict[str, SourceDiagnosticRow] = {}

    for run in history:
        for source in run.get("sources", []):
            name = _display_source_name(source.get("name") or "Unknown source")
            row = by_source.setdefault(name, SourceDiagnosticRow(name=name))
            row.runs += 1
            row.total_jobs += int(source.get("job_count") or 0)
            row.warning_count += int(source.get("warning_count") or 0)
            if source.get("duration_seconds") is not None:
                row.durations.append(float(source["duration_seconds"]))

        for failed_name in run.get("failed_sources", []) or []:
            name = _display_source_name(failed_name)
            row = by_source.setdefault(name, SourceDiagnosticRow(name=name))
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
            f"{row.failure_count} {failure_noun}; "
            f"reliability {row.reliability_score}/100; {row.recommended_action}"
        )

    toggle_lines = format_source_toggle_recommendations(
        build_source_diagnostics(history, limit=limit)
    )
    if toggle_lines:
        lines.extend(toggle_lines)

    selection_lines = format_source_selection_strategy_lines(history, limit=limit)
    if selection_lines:
        lines.extend(selection_lines)

    coverage_lines = format_source_coverage_lines(history)
    if coverage_lines:
        lines.extend(coverage_lines)

    strategy_lines = format_preset_strategy_lines(history, limit=limit)
    if strategy_lines:
        lines.extend(strategy_lines)

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


def format_preset_strategy_lines(history: list[dict[str, Any]], limit: int = 3) -> list[str]:
    """Return preset strategy recommendations from recent source outcomes."""
    stats_by_preset: dict[str, dict[str, Any]] = {}
    for run in history:
        config = run.get("search_config") or {}
        if not config:
            continue

        preset = str(config.get("preset") or "custom")
        stats = stats_by_preset.setdefault(
            preset,
            {
                "runs": 0,
                "total_jobs": 0,
                "failures": 0,
                "sources": set(),
            },
        )
        stats["runs"] += 1
        stats["total_jobs"] += int(run.get("total_jobs") or 0)
        stats["failures"] += len(run.get("failed_sources", []) or [])

        for source_name in config.get("selected_sources", []) or []:
            stats["sources"].add(_display_source_name(source_name))
        for source in run.get("sources", []) or []:
            stats["sources"].add(_display_source_name(source.get("name") or "Unknown source"))

    ranked = []
    for preset, stats in stats_by_preset.items():
        runs = max(1, int(stats["runs"]))
        failures = int(stats["failures"])
        total_jobs = int(stats["total_jobs"])
        average_jobs = total_jobs / runs
        ranked.append(
            {
                "preset": preset,
                "runs": runs,
                "failures": failures,
                "total_jobs": total_jobs,
                "average_jobs": average_jobs,
                "source_count": len(stats["sources"]),
            }
        )

    ranked.sort(
        key=lambda item: (
            item["failures"] > 0,
            item["average_jobs"] < 1,
            item["failures"],
            item["average_jobs"],
            item["preset"].casefold(),
        ),
        reverse=True,
    )

    lines = []
    for item in ranked[:limit]:
        preset = item["preset"]
        runs = item["runs"]
        run_noun = "run" if runs == 1 else "runs"
        failures = item["failures"]
        if failures:
            failure_noun = "failure" if failures == 1 else "failures"
            lines.append(
                f"Preset strategy: {preset} had {failures} source {failure_noun} "
                f"across {runs} recent {run_noun}; review Source controls before rerunning."
            )
            continue

        average_jobs = item["average_jobs"]
        if average_jobs < 1:
            lines.append(
                f"Preset strategy: {preset} averaged {average_jobs:.1f} jobs per run; "
                "broaden filters or try another preset before rerunning."
            )
            continue

        source_count = item["source_count"]
        source_noun = "source" if source_count == 1 else "sources"
        lines.append(
            f"Preset strategy: {preset} averaged {average_jobs:.1f} jobs per run "
            f"across {source_count} {source_noun}."
        )
    return lines


def format_pre_run_source_strategy_lines(
    history: list[dict[str, Any]],
    *,
    limit: int = 2,
) -> list[str]:
    """Return short Search-tab guidance from recent source strategy outcomes."""
    if not history:
        return []

    rows = build_source_diagnostics(history, limit=limit)
    lines = []
    used_source_names = set()
    for row in rows:
        if row.failure_count >= 2 or row.reliability_score < 70:
            lines.append(
                f"Before rerunning: {row.name} has recent reliability issues; "
                "consider unchecking it in Sources."
            )
            used_source_names.add(row.name)
        elif row.failure_count:
            lines.append(
                f"Before rerunning: {row.name} failed recently; keep it selected only if you need its coverage."
            )
            used_source_names.add(row.name)

    if len(lines) < limit:
        for selection_line in format_source_selection_strategy_lines(history, limit=limit):
            if any(f" {name} " in selection_line for name in used_source_names):
                continue
            lines.append(selection_line.replace("Source selection:", "Before rerunning:", 1))
            if len(lines) >= limit:
                break

    if len(lines) < limit:
        for strategy_line in format_preset_strategy_lines(history, limit=limit):
            if "review Source controls" in strategy_line or "broaden filters" in strategy_line:
                lines.append(strategy_line.replace("Preset strategy:", "Before rerunning:", 1))
            if len(lines) >= limit:
                break

    return lines[:limit]


def format_source_selection_strategy_lines(
    history: list[dict[str, Any]],
    *,
    limit: int = 3,
) -> list[str]:
    """Return concrete source-selection recommendations from recent outcomes."""
    by_source: dict[str, dict[str, int]] = {}
    for run in history:
        for source in run.get("sources", []) or []:
            name = _display_source_name(source.get("name") or "Unknown source")
            stats = by_source.setdefault(name, {"runs": 0, "total_jobs": 0, "failures": 0})
            stats["runs"] += 1
            stats["total_jobs"] += int(source.get("job_count") or 0)
        for failed_source in run.get("failed_sources", []) or []:
            name = _display_source_name(failed_source)
            stats = by_source.setdefault(name, {"runs": 0, "total_jobs": 0, "failures": 0})
            stats["failures"] += 1

    ranked = []
    for name, stats in by_source.items():
        runs = max(1, int(stats["runs"]))
        total_jobs = int(stats["total_jobs"])
        failures = int(stats["failures"])
        average_jobs = total_jobs / runs
        priority = 0
        if failures >= 2 or (failures and average_jobs < 1):
            priority = 3
        elif average_jobs < 1:
            priority = 2
        elif average_jobs >= 3 and failures == 0:
            priority = 1
        if priority:
            ranked.append({
                "name": name,
                "runs": runs,
                "total_jobs": total_jobs,
                "failures": failures,
                "average_jobs": average_jobs,
                "priority": priority,
            })

    ranked.sort(
        key=lambda item: (
            item["priority"],
            item["failures"],
            item["average_jobs"],
            item["name"].casefold(),
        ),
        reverse=True,
    )

    lines = []
    for item in ranked[:limit]:
        name = item["name"]
        failures = item["failures"]
        average_jobs = item["average_jobs"]
        if item["priority"] == 3:
            failure_noun = "failure" if failures == 1 else "failures"
            lines.append(
                f"Source selection: uncheck {name} for the next rerun unless you need its coverage "
                f"({failures} recent {failure_noun}, {average_jobs:.1f} jobs/run)."
            )
        elif item["priority"] == 2:
            lines.append(
                f"Source selection: {name} has been low-yield recently "
                f"({average_jobs:.1f} jobs/run); pair it with broader sources."
            )
        else:
            lines.append(
                f"Source selection: keep {name} enabled for similar searches "
                f"({average_jobs:.1f} jobs/run, no recent failures)."
            )
    return lines


def format_source_toggle_recommendations(rows: list[SourceDiagnosticRow]) -> list[str]:
    """Return source-toggle recommendations for unreliable recent sources."""
    recommendations = []
    for row in rows:
        if row.failure_count >= 2 or row.reliability_score < 70:
            recommendations.append(
                f"Source toggle recommendation: disable {row.name} temporarily and rerun the search."
            )
    return recommendations


def format_source_coverage_lines(history: list[dict[str, Any]]) -> list[str]:
    """Return source/preset coverage gaps from recent source history."""
    gaps_by_preset: dict[str, set[str]] = {}
    for run in history:
        config = run.get("search_config") or {}
        preset = str(config.get("preset") or "custom")
        for source in run.get("sources", []) or []:
            if int(source.get("job_count") or 0) == 0:
                gaps_by_preset.setdefault(preset, set()).add(
                    _display_source_name(source.get("name") or "Unknown source")
                )
        for failed_source in run.get("failed_sources", []) or []:
            gaps_by_preset.setdefault(preset, set()).add(_display_source_name(failed_source))

    lines = []
    for preset, sources in sorted(gaps_by_preset.items()):
        if sources:
            lines.append(
                f"Coverage gap: {preset} had no recent jobs from {', '.join(sorted(sources, key=str.casefold))}."
            )
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


def _display_source_name(source_name: Any) -> str:
    """Return a user-facing source name for either source keys or display names."""
    name = str(source_name or "Unknown source")
    return get_source_display_name(name)
