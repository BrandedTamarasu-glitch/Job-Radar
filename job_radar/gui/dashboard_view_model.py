"""View-model helpers for the desktop dashboard and next-step panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DashboardAction:
    """A prioritized action shown on the opening desktop screen."""

    title: str
    detail: str
    target: str
    priority: int


def build_dashboard_actions(
    *,
    readiness: Any | None = None,
    review_counts: dict[str, int] | None = None,
    next_actions: list[dict[str, Any]] | None = None,
    search_history: dict[str, Any] | None = None,
    maintenance_suggestions: list[str] | None = None,
    source_quality_issues: list[str] | None = None,
    limit: int = 4,
) -> list[DashboardAction]:
    """Return prioritized next actions for the Profile tab dashboard."""
    actions: list[DashboardAction] = []

    if _readiness_needs_attention(readiness):
        status = str(getattr(readiness, "status", "Profile needs attention"))
        score = getattr(readiness, "score", None)
        max_score = getattr(readiness, "max_score", None)
        score_text = (
            f" ({score}/{max_score})"
            if score is not None and max_score is not None
            else ""
        )
        actions.append(
            DashboardAction(
                title="Review profile",
                detail=(
                    f"{status}{score_text}. Improve profile details before relying "
                    "on match scores."
                ),
                target="Profile",
                priority=10,
            )
        )

    overdue = [item for item in next_actions or [] if item.get("is_overdue")]
    due_today = [item for item in next_actions or [] if item.get("days_until") == 0]
    upcoming = [
        item
        for item in next_actions or []
        if not item.get("is_overdue") and item.get("days_until") not in (None, 0)
    ]
    if overdue:
        actions.append(
            DashboardAction(
                title="Handle overdue follow-ups",
                detail=f"{len(overdue)} application follow-up(s) are overdue.",
                target="Applications",
                priority=20,
            )
        )
    elif due_today:
        actions.append(
            DashboardAction(
                title="Handle today's follow-ups",
                detail=f"{len(due_today)} application follow-up(s) are due today.",
                target="Applications",
                priority=30,
            )
        )
    elif upcoming:
        actions.append(
            DashboardAction(
                title="Review upcoming follow-ups",
                detail=f"{len(upcoming)} application follow-up(s) are scheduled soon.",
                target="Applications",
                priority=55,
            )
        )

    counts = review_counts or {}
    shortlisted = int(counts.get("shortlisted") or 0)
    maybe_later = int(counts.get("maybe_later") or 0)
    if shortlisted or maybe_later:
        parts = []
        if shortlisted:
            parts.append(f"{shortlisted} shortlisted")
        if maybe_later:
            parts.append(f"{maybe_later} maybe-later")
        actions.append(
            DashboardAction(
                title="Review saved search decisions",
                detail=f"{', '.join(parts)} job(s) are waiting in the review queue.",
                target="Search",
                priority=40,
            )
        )

    history = search_history or {}
    recent = history.get("recent") if isinstance(history.get("recent"), list) else []
    saved = history.get("saved") if isinstance(history.get("saved"), list) else []
    changed_saved = _changed_search_count(saved)
    if changed_saved:
        actions.append(
            DashboardAction(
                title="Review changed saved searches",
                detail=(
                    f"{_bounded_count(changed_saved)} saved search(es) changed "
                    "since the previous run."
                ),
                target="Search",
                priority=45,
            )
        )
    elif saved:
        actions.append(
            DashboardAction(
                title="Run a saved search",
                detail=f"{len(saved)} saved search(es) are ready to rerun.",
                target="Search",
                priority=60,
            )
        )
    elif recent:
        actions.append(
            DashboardAction(
                title="Repeat a recent search",
                detail=f"{len(recent)} recent search(es) are available as shortcuts.",
                target="Search",
                priority=70,
            )
        )
    else:
        actions.append(
            DashboardAction(
                title="Run your first search",
                detail=(
                    "Start with the recommended preset, then save searches you "
                    "expect to repeat."
                ),
                target="Search",
                priority=80,
            )
        )

    if maintenance_suggestions:
        actions.append(
            DashboardAction(
                title="Review maintenance suggestions",
                detail=maintenance_suggestions[0],
                target="Settings",
                priority=65,
            )
        )

    if source_quality_issues:
        actions.append(
            DashboardAction(
                title="Review source quality",
                detail=source_quality_issues[0],
                target="Settings",
                priority=50,
            )
        )

    actions.sort(key=lambda action: action.priority)
    return actions[:max(1, limit)]


def _changed_search_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if _search_changed(item))


def _bounded_count(value: int) -> str:
    if value > 99:
        return "99+"
    return str(value)


def _search_changed(item: dict[str, Any]) -> bool:
    current = item.get("last_result_stats") or {}
    previous = item.get("previous_result_stats") or {}
    if not current or not previous:
        return False

    for key in ("total", "new", "high_score"):
        if int(current.get(key) or 0) != int(previous.get(key) or 0):
            return True

    current_review = current.get("review") or {}
    previous_review = previous.get("review") or {}
    for key in ("shortlisted", "maybe_later", "dismissed"):
        if int(current_review.get(key) or 0) != int(previous_review.get(key) or 0):
            return True
    return False


def _readiness_needs_attention(readiness: Any | None) -> bool:
    if readiness is None:
        return False
    status = str(getattr(readiness, "status", "")).casefold()
    score = getattr(readiness, "score", None)
    max_score = getattr(readiness, "max_score", None)
    if status and status not in {"strong", "complete"}:
        return True
    if isinstance(score, int) and isinstance(max_score, int):
        return score < max_score
    return False
