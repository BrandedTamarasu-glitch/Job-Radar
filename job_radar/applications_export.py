"""Export helpers for the application pipeline."""

import csv
import json
from datetime import datetime
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


def export_application_followups_ics(applications: dict, output_path: str | Path) -> Path:
    """Write dated application follow-ups to an iCalendar file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Job Radar//Application Follow-ups//EN",
    ]
    for row in application_rows_for_export(applications):
        due_date = row.get("next_action_date", "").strip()
        next_action = row.get("next_action", "").strip()
        if not due_date or not next_action or not _valid_ics_date(due_date):
            continue

        uid = f"{row.get('job_key', '')}-{due_date}@job-radar"
        summary = f"{next_action} - {row.get('title') or 'Application'}"
        company = row.get("company")
        description = f"{row.get('status', '')} at {company}" if company else row.get("status", "")
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{_escape_ics_text(uid)}",
            f"DTSTART;VALUE=DATE:{due_date.replace('-', '')}",
            f"SUMMARY:{_escape_ics_text(summary)}",
            f"DESCRIPTION:{_escape_ics_text(description)}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
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


def import_report_status_updates_json(input_path: str | Path) -> dict[str, dict[str, str]]:
    """Read report-exported pending status updates into tracker entries."""
    path = Path(input_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    applications = data.get("applications") if isinstance(data, dict) else None
    if not isinstance(applications, dict):
        raise ValueError("Status update file must contain an applications object")

    imported: dict[str, dict[str, str]] = {}
    for raw_key, raw_entry in applications.items():
        if not isinstance(raw_entry, dict):
            continue
        title = str(raw_entry.get("title") or "").strip()
        company = str(raw_entry.get("company") or "").strip()
        key = str(raw_key or "").strip() or job_key(title, company)
        status = normalize_application_status(raw_entry.get("status"))
        if not key or status == "needs_status":
            continue

        entry = {
            "title": title,
            "company": company,
            "status": status,
            "updated": str(raw_entry.get("updated") or "").strip(),
        }
        imported[key] = {
            field: value for field, value in entry.items()
            if value not in ("", None)
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


def _valid_ics_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _escape_ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )
