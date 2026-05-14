"""Export helpers for the application pipeline."""

import csv
from pathlib import Path

from job_radar.gui.applications_view_model import (
    APPLICATION_STATUS_LABELS,
    build_applications_view_model,
    normalize_application_status,
)
from job_radar.tracker import job_key


APPLICATION_EXPORT_COLUMNS = [
    "status",
    "title",
    "company",
    "notes",
    "next_action",
    "next_action_date",
    "updated",
    "timeline",
    "job_key",
]


def application_rows_for_export(applications: dict) -> list[dict[str, str]]:
    """Return flattened application rows in view-model group order."""
    rows = []
    for group in build_applications_view_model(applications):
        for row in group.rows:
            rows.append({
                "status": row.status_label,
                "title": row.title,
                "company": row.company,
                "notes": row.notes,
                "next_action": row.next_action,
                "next_action_date": row.next_action_date,
                "updated": row.updated,
                "timeline": _format_timeline_summary(applications.get(row.key, {})),
                "job_key": row.key,
            })
    return rows


def _format_timeline_summary(entry: dict) -> str:
    """Return a compact timeline summary for CSV portability."""
    parts = []
    for event in entry.get("timeline") or []:
        timestamp = str(event.get("timestamp") or "")[:10]
        changed = ", ".join(sorted((event.get("changes") or {}).keys()))
        if timestamp and changed:
            parts.append(f"{timestamp}: {changed}")
    return " | ".join(parts)


def export_applications_csv(applications: dict, output_path: str | Path) -> Path:
    """Write application pipeline entries to a CSV file and return the path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=APPLICATION_EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(application_rows_for_export(applications))

    return path


def import_applications_csv(input_path: str | Path) -> dict[str, dict[str, str]]:
    """Read an applications CSV export into tracker application entries."""
    path = Path(input_path)
    imported: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("title") or "").strip()
            company = (row.get("company") or "").strip()
            key = (row.get("job_key") or "").strip() or job_key(title, company)
            if not key:
                continue

            entry = {
                "title": title,
                "company": company,
                "status": _status_value_from_export(row.get("status")),
                "notes": (row.get("notes") or "").strip(),
                "next_action": (row.get("next_action") or "").strip(),
                "next_action_date": (row.get("next_action_date") or "").strip(),
                "updated": (row.get("updated") or "").strip(),
            }
            imported[key] = {
                field: value for field, value in entry.items()
                if value not in ("", "needs_status")
            }
    return imported


def _status_value_from_export(value: str | None) -> str:
    """Convert a display status label or raw status into tracker status value."""
    normalized = normalize_application_status(value)
    if normalized != "needs_status":
        return normalized

    display_to_value = {
        label.casefold(): status
        for status, label in APPLICATION_STATUS_LABELS.items()
    }
    return display_to_value.get(str(value or "").strip().casefold(), "needs_status")
