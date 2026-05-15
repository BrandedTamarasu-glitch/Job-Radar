"""Tests for application pipeline CSV export helpers."""

import csv

from job_radar.applications_export import (
    APPLICATION_EXPORT_COLUMNS,
    application_rows_for_export,
    export_application_followups_ics,
    export_applications_csv,
    import_applications_csv,
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
            "timeline": [
                {
                    "timestamp": "2026-05-13T10:00:00",
                    "changes": {"status": {}, "next_action": {}},
                }
            ],
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
            "timeline": "2026-05-13: next_action, status",
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
            "timeline": "",
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
            "timeline": [
                {
                    "timestamp": "2026-05-13T10:00:00",
                    "changes": {"status": {}, "notes": {}},
                }
            ],
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
            "timeline": "2026-05-13: notes, status",
            "job_key": "backend engineer||acme",
        }
    ]


def test_export_application_followups_ics_writes_dated_followups(tmp_path):
    applications = {
        "backend engineer||acme": {
            "title": "Backend Engineer",
            "company": "Acme, Inc.",
            "status": "interviewing",
            "next_action": "Send thank-you note",
            "next_action_date": "2026-05-21",
        },
        "platform engineer||northstar": {
            "title": "Platform Engineer",
            "company": "Northstar",
            "status": "applied",
            "next_action": "Follow up",
        },
        "bad date||co": {
            "title": "Bad Date",
            "company": "Co",
            "status": "applied",
            "next_action": "Follow up",
            "next_action_date": "tomorrow",
        },
    }

    path = export_application_followups_ics(applications, tmp_path / "followups.ics")

    text = path.read_text(encoding="utf-8")
    assert "BEGIN:VCALENDAR" in text
    assert "BEGIN:VEVENT" in text
    assert "DTSTART;VALUE=DATE:20260521" in text
    assert "SUMMARY:Send thank-you note - Backend Engineer" in text
    assert "DESCRIPTION:Interviewing at Acme\\, Inc." in text
    assert "Platform Engineer" not in text
    assert "Bad Date" not in text


def test_import_applications_csv_restores_tracker_entries(tmp_path):
    """Application CSV import maps display labels back to tracker entries."""
    path = tmp_path / "applications.csv"
    path.write_text(
        "status,title,company,notes,next_action,next_action_date,updated,timeline,job_key\n"
        "Interviewing,Backend Engineer,\"Acme, Inc.\",Panel scheduled,"
        "Send thank-you,2026-05-21,2026-05-13T10:00:00,,backend engineer||acme\n"
        "Needs Status,Review Role,Northstar,Review later,,,,,\n",
        encoding="utf-8",
    )

    imported = import_applications_csv(path)

    assert imported["backend engineer||acme"] == {
        "title": "Backend Engineer",
        "company": "Acme, Inc.",
        "status": "interviewing",
        "notes": "Panel scheduled",
        "next_action": "Send thank-you",
        "next_action_date": "2026-05-21",
        "updated": "2026-05-13T10:00:00",
    }
    assert imported["review role||northstar"] == {
        "title": "Review Role",
        "company": "Northstar",
        "notes": "Review later",
    }
