"""View-model helpers for the Applications pipeline screen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


APPLICATION_STATUS_LABELS = {
    "applied": "Applied",
    "interviewing": "Interviewing",
    "offer": "Offer",
    "rejected": "Rejected",
    "skipped": "Skipped",
    "needs_status": "Needs Status",
}

APPLICATION_STATUS_ORDER = [
    "applied",
    "interviewing",
    "offer",
    "rejected",
    "skipped",
    "needs_status",
]

APPLICATION_EDITABLE_STATUS_ORDER = [
    "applied",
    "interviewing",
    "offer",
    "rejected",
    "skipped",
]


@dataclass(frozen=True)
class ApplicationRow:
    """Display-ready application tracker row."""

    key: str
    title: str
    company: str
    status: str
    status_label: str
    notes: str
    next_action: str
    next_action_date: str
    updated: str


@dataclass(frozen=True)
class ApplicationGroup:
    """Grouped application rows for one pipeline status."""

    status: str
    label: str
    count: int
    rows: list[ApplicationRow]


def normalize_application_status(status: str | None) -> str:
    """Return a stable display bucket for tracker status values."""
    normalized = (status or "").strip().casefold()
    if normalized in APPLICATION_STATUS_LABELS and normalized != "needs_status":
        return normalized
    return "needs_status"


def application_row_from_entry(key: str, entry: dict[str, Any]) -> ApplicationRow:
    """Build a display row from a tracker application entry."""
    status = normalize_application_status(entry.get("status"))
    return ApplicationRow(
        key=key,
        title=str(entry.get("title") or ""),
        company=str(entry.get("company") or ""),
        status=status,
        status_label=APPLICATION_STATUS_LABELS[status],
        notes=str(entry.get("notes") or ""),
        next_action=str(entry.get("next_action") or ""),
        next_action_date=str(entry.get("next_action_date") or ""),
        updated=str(entry.get("updated") or ""),
    )


def build_applications_view_model(applications: dict[str, dict[str, Any]]) -> list[ApplicationGroup]:
    """Group tracker application entries for the Applications view."""
    grouped: dict[str, list[ApplicationRow]] = {
        status: [] for status in APPLICATION_STATUS_ORDER
    }

    for key, entry in applications.items():
        row = application_row_from_entry(key, entry)
        grouped[row.status].append(row)

    groups = []
    for status in APPLICATION_STATUS_ORDER:
        rows = sorted(
            grouped[status],
            key=lambda row: (row.updated, row.company.casefold(), row.title.casefold()),
            reverse=True,
        )
        groups.append(
            ApplicationGroup(
                status=status,
                label=APPLICATION_STATUS_LABELS[status],
                count=len(rows),
                rows=rows,
            )
        )

    return groups


def append_application_note(existing_notes: str | None, note: str) -> str:
    """Append a rendered note template to an application's existing notes."""
    existing = (existing_notes or "").strip()
    rendered = note.strip()
    if not rendered:
        return existing
    if not existing:
        return rendered
    return f"{existing}\n\n{rendered}"


def application_status_menu_labels(current_status: str | None) -> list[str]:
    """Return status menu labels with the current editable status first."""
    current = normalize_application_status(current_status)
    statuses = list(APPLICATION_EDITABLE_STATUS_ORDER)
    if current in statuses:
        statuses.remove(current)
        statuses.insert(0, current)
    return [APPLICATION_STATUS_LABELS[status] for status in statuses]


def application_status_from_label(label: str) -> str:
    """Map a display label selected in the GUI back to a tracker status value."""
    normalized = label.strip().casefold()
    for status in APPLICATION_EDITABLE_STATUS_ORDER:
        if APPLICATION_STATUS_LABELS[status].casefold() == normalized:
            return status
    raise ValueError(f"Unknown application status label: {label}")


def normalize_application_detail_input(value: str | None) -> str | None:
    """Normalize optional free-text application detail input from GUI dialogs."""
    if value is None:
        return None
    return value.strip()
