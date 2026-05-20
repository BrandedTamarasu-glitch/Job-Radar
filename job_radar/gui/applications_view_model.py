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

APPLICATION_FOLLOWUP_FILTER_LABELS = {
    "all": "All",
    "overdue": "Overdue",
    "due_soon": "Due Soon",
}

APPLICATION_FOLLOWUP_FILTER_ORDER = ["all", "overdue", "due_soon"]


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


@dataclass(frozen=True)
class ApplicationNextActionRow:
    """Display-ready follow-up queue row."""

    due_text: str
    title: str
    company: str
    status_label: str


@dataclass(frozen=True)
class ApplicationPipelineDisplayRow:
    """Display text for a grouped application pipeline row."""

    heading: str
    detail_text: str


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


def filter_application_next_actions(
    actions: list[dict[str, Any]],
    followup_filter: str = "all",
    due_soon_days: int = 7,
) -> list[dict[str, Any]]:
    """Filter follow-up queue rows for Applications tab focus modes."""
    if followup_filter == "overdue":
        return [action for action in actions if action.get("is_overdue")]
    if followup_filter == "due_soon":
        return [
            action for action in actions
            if not action.get("is_overdue")
            and isinstance(action.get("days_until"), int)
            and 0 <= int(action["days_until"]) <= due_soon_days
        ]
    return actions


def application_followup_filter_options() -> list[tuple[str, str]]:
    """Return stable follow-up filter options for the Applications tab."""
    return [
        (filter_key, APPLICATION_FOLLOWUP_FILTER_LABELS[filter_key])
        for filter_key in APPLICATION_FOLLOWUP_FILTER_ORDER
    ]


def format_next_action_due_text(action: dict[str, Any]) -> str:
    """Return a compact due-date label for an application next action."""
    days_until = action.get("days_until")
    if action.get("is_overdue"):
        return f"Overdue by {abs(int(days_until or 0))} day(s)"
    if days_until == 0:
        return "Due today"
    if isinstance(days_until, int) and days_until > 0:
        return f"Due in {days_until} day(s)"
    if action.get("next_action_date"):
        return f"Due {action['next_action_date']}"
    return "No due date"


def application_next_action_row(action: dict[str, Any]) -> ApplicationNextActionRow:
    """Build display text for a follow-up queue action."""
    return ApplicationNextActionRow(
        due_text=format_next_action_due_text(action),
        title=str(action.get("title") or "Untitled"),
        company=str(action.get("company") or "Unknown company"),
        status_label=str(action.get("status") or "needs_status").replace("_", " ").title(),
    )


def application_pipeline_display_row(row: ApplicationRow) -> ApplicationPipelineDisplayRow:
    """Build heading and detail text for an Applications pipeline row."""
    details = []
    if row.next_action:
        next_action = row.next_action
        if row.next_action_date:
            next_action = f"{next_action} ({row.next_action_date})"
        details.append(f"Next: {next_action}")
    if row.notes:
        details.append(f"Notes: {row.notes}")
    if row.updated:
        details.append(f"Updated: {row.updated[:10]}")

    heading = f"{row.title or 'Untitled'} — {row.company or 'Unknown company'}"
    detail_text = " | ".join(details) if details else "No follow-up details."
    return ApplicationPipelineDisplayRow(heading=heading, detail_text=detail_text)


def applications_csv_export_success_message(export_path: object) -> str:
    """Return Applications tab feedback after CSV export succeeds."""
    return f"Exported to {export_path}"


def applications_csv_export_error_message(error: object) -> str:
    """Return Applications tab feedback after CSV export fails."""
    return f"Export failed: {error}"


def application_status_import_success_message(changed_count: int) -> str:
    """Return Applications tab feedback after report status import succeeds."""
    return f"Imported {changed_count} report status update(s) into Applications"


def application_status_import_error_message(error: object) -> str:
    """Return Applications tab feedback after report status import fails."""
    return f"Report status import failed: {error}"


def application_calendar_export_success_message(export_path: object) -> str:
    """Return Applications tab feedback after follow-up calendar export succeeds."""
    return f"Exported calendar to {export_path}"


def application_calendar_export_error_message(error: object) -> str:
    """Return Applications tab feedback after follow-up calendar export fails."""
    return f"Calendar export failed: {error}"


def application_followup_update_error_message(error: object) -> str:
    """Return Applications tab feedback after completing a follow-up fails."""
    return f"Follow-up update failed: {error}"


def application_followup_snooze_error_message(error: object) -> str:
    """Return Applications tab feedback after snoozing a follow-up fails."""
    return f"Follow-up snooze failed: {error}"


def application_template_insert_error_message(error: object) -> str:
    """Return Applications tab feedback after note-template insertion fails."""
    return f"Template insert failed: {error}"


def application_status_update_error_message(error: object) -> str:
    """Return Applications tab feedback after a pipeline status update fails."""
    return f"Status update failed: {error}"


def application_detail_update_error_message(error: object) -> str:
    """Return Applications tab feedback after direct application edits fail."""
    return f"Application update failed: {error}"


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
