"""Execution bookkeeping for automated source fetch runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceExecutionState:
    """Mutable per-run source fetch bookkeeping."""

    queries: list[dict]
    completed: int = 0
    sources_started: int = 0
    sources_done: int = 0
    query_failures: list[dict] = field(default_factory=list)
    slow_query_warnings: list[dict] = field(default_factory=list)
    seen: set[tuple[str, str]] = field(default_factory=set)
    source_names: list[str] = field(init=False)
    source_query_counts: dict[str, int] = field(init=False)
    source_completed: dict[str, int] = field(init=False)
    source_job_counts: dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        self.source_names = []
        self.source_query_counts = {}
        self.source_completed = {}
        self.source_job_counts = {}
        for query in self.queries:
            source = query["source"]
            if source not in self.source_names:
                self.source_names.append(source)
            self.source_query_counts[source] = self.source_query_counts.get(source, 0) + 1
            self.source_completed[source] = 0
            self.source_job_counts[source] = 0

    @property
    def total_queries(self) -> int:
        return len(self.queries)

    @property
    def total_sources(self) -> int:
        return len(self.source_names)

    def mark_source_started(self) -> int:
        self.sources_started += 1
        return self.sources_started

    def mark_query_complete(self) -> int:
        self.completed += 1
        return self.completed

    def record_slow_query(self, query: dict, elapsed: float, threshold: float) -> None:
        self.slow_query_warnings.append({
            "source": query["source"],
            "query": query.get("query", ""),
            "elapsed_seconds": round(elapsed, 2),
            "threshold_seconds": threshold,
        })

    def record_result(self, query_source: str, result: Any) -> bool:
        key = (result.title.lower().strip(), result.company.lower().strip())
        if key in self.seen:
            return False
        self.seen.add(key)
        self.source_job_counts[query_source] = self.source_job_counts.get(query_source, 0) + 1
        self.source_job_counts[result.source] = self.source_job_counts.get(result.source, 0) + 1
        return True

    def record_failure(self, query: dict, error: Exception) -> None:
        self.query_failures.append({
            "source": query["source"],
            "query": query.get("query", ""),
            "error": str(error),
        })

    def mark_source_query_complete(self, source: str) -> bool:
        self.source_completed[source] += 1
        if self.source_completed[source] != self.source_query_counts[source]:
            return False
        self.sources_done += 1
        return True

    def completed_source_count(self) -> int:
        return self.sources_done

    def job_count_for_source(self, source: str) -> int:
        return self.source_job_counts.get(source, 0)
