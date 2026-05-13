"""Tests for application pipeline CSV export helpers."""

import csv

from job_radar.applications_export import (
    APPLICATION_EXPORT_COLUMNS,
    application_rows_for_export,
    export_applications_csv,
)


def test_application_rows_for_export_flattens_grouped_pipeline_entries():
    """Application export rows preserve status labels and follow-up metadata."""
    applications = {
        "backend engineer||acme": {
            "title": "Backend Engineer",
            "company": "Acme",
            "status": "applied",
            "notes": "Submitted through referral",
            "next_action": "Follow up",
            "next_action_date": "2026-05-20",
            "updated": "2026-05-13T10:00:00",
        },
        "platform engineer||northstar": {
            "title": "Platform Engineer",
            "company": "Northstar",
            "notes": "Review later",
            "updated": "2026-05-14T10:00:00",
        },
    }

    rows = application_rows_for_export(applications)

    assert rows == [
        {
            "status": "Applied",
            "title": "Backend Engineer",
            "company": "Acme",
            "notes": "Submitted through referral",
            "next_action": "Follow up",
            "next_action_date": "2026-05-20",
            "updated": "2026-05-13T10:00:00",
            "job_key": "backend engineer||acme",
        },
        {
            "status": "Needs Status",
            "title": "Platform Engineer",
            "company": "Northstar",
            "notes": "Review later",
            "next_action": "",
            "next_action_date": "",
            "updated": "2026-05-14T10:00:00",
            "job_key": "platform engineer||northstar",
        },
    ]


def test_export_applications_csv_writes_utf8_csv(tmp_path):
    """CSV export writes stable headers and preserves commas safely."""
    applications = {
        "backend engineer||acme": {
            "title": "Backend Engineer",
            "company": "Acme, Inc.",
            "status": "interviewing",
            "notes": "Panel, then hiring manager",
            "next_action": "Send thank-you note",
            "next_action_date": "2026-05-21",
            "updated": "2026-05-13T10:00:00",
        },
    }

    path = export_applications_csv(applications, tmp_path / "applications.csv")

    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == APPLICATION_EXPORT_COLUMNS
    assert rows == [
        {
            "status": "Interviewing",
            "title": "Backend Engineer",
            "company": "Acme, Inc.",
            "notes": "Panel, then hiring manager",
            "next_action": "Send thank-you note",
            "next_action_date": "2026-05-21",
            "updated": "2026-05-13T10:00:00",
            "job_key": "backend engineer||acme",
        }
    ]
