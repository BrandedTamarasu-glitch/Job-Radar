"""Export helpers for the application pipeline."""

import csv
from pathlib import Path

from job_radar.gui.applications_view_model import build_applications_view_model


APPLICATION_EXPORT_COLUMNS = [
    "status",
    "title",
    "company",
    "notes",
    "next_action",
    "next_action_date",
    "updated",
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
                "job_key": row.key,
            })
    return rows


def export_applications_csv(applications: dict, output_path: str | Path) -> Path:
    """Write application pipeline entries to a CSV file and return the path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=APPLICATION_EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(application_rows_for_export(applications))

    return path
