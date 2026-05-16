"""Tests for Applications pipeline view-model helpers."""

from job_radar.gui.applications_view_model import (
    APPLICATION_STATUS_ORDER,
    append_application_note,
    application_next_action_row,
    application_status_from_label,
    application_status_menu_labels,
    build_applications_view_model,
    filter_application_next_actions,
    format_next_action_due_text,
    normalize_application_detail_input,
    normalize_application_status,
)


def _group_by_status(groups):
    return {group.status: group for group in groups}


def test_applications_view_model_groups_pipeline_statuses():
    """Tracker entries are grouped into stable pipeline status buckets."""
    applications = {
        "backend engineer||acme": {
            "title": "Backend Engineer",
            "company": "Acme",
            "status": "applied",
            "notes": "Referral submitted",
            "next_action": "Follow up",
            "next_action_date": "2026-05-20",
            "updated": "2026-05-13T10:00:00",
        },
        "platform engineer||northstar": {
            "title": "Platform Engineer",
            "company": "Northstar",
            "status": "interviewing",
            "updated": "2026-05-14T10:00:00",
        },
        "frontend engineer||ledgerworks": {
            "title": "Frontend Engineer",
            "company": "LedgerWorks",
            "status": "rejected",
            "updated": "2026-05-12T10:00:00",
        },
        "staff engineer||scaleops": {
            "title": "Staff Engineer",
            "company": "ScaleOps",
            "status": "offer",
            "updated": "2026-05-15T10:00:00",
        },
    }

    groups = _group_by_status(build_applications_view_model(applications))

    assert [group.status for group in build_applications_view_model(applications)] == APPLICATION_STATUS_ORDER
    assert groups["applied"].count == 1
    assert groups["interviewing"].count == 1
    assert groups["rejected"].count == 1
    assert groups["offer"].count == 1
    assert groups["applied"].rows[0].notes == "Referral submitted"
    assert groups["applied"].rows[0].next_action == "Follow up"
    assert groups["applied"].rows[0].next_action_date == "2026-05-20"


def test_applications_view_model_groups_note_only_entries_as_needs_status():
    """Note-only tracker entries remain visible in a needs-status bucket."""
    applications = {
        "backend engineer||acme": {
            "title": "Backend Engineer",
            "company": "Acme",
            "notes": "Review later",
            "updated": "2026-05-13T10:00:00",
        },
        "platform engineer||northstar": {
            "title": "Platform Engineer",
            "company": "Northstar",
            "status": "unknown-new-status",
            "updated": "2026-05-14T10:00:00",
        },
    }

    groups = _group_by_status(build_applications_view_model(applications))

    assert groups["needs_status"].count == 2
    assert [row.company for row in groups["needs_status"].rows] == ["Northstar", "Acme"]
    assert groups["needs_status"].rows[1].notes == "Review later"


def test_normalize_application_status_accepts_known_statuses_case_insensitively():
    """Status normalization tolerates casing and blanks."""
    assert normalize_application_status("Applied") == "applied"
    assert normalize_application_status(" INTERVIEWING ") == "interviewing"
    assert normalize_application_status("offer") == "offer"
    assert normalize_application_status("rejected") == "rejected"
    assert normalize_application_status("skipped") == "skipped"
    assert normalize_application_status("") == "needs_status"
    assert normalize_application_status(None) == "needs_status"


def test_append_application_note_adds_template_after_existing_notes():
    combined = append_application_note(
        "Sent application through careers page.",
        "Follow up with recruiter next week.",
    )

    assert combined == (
        "Sent application through careers page.\n\n"
        "Follow up with recruiter next week."
    )


def test_append_application_note_handles_empty_notes_and_blank_template():
    assert append_application_note("", "  Draft cover letter.  ") == "Draft cover letter."
    assert append_application_note("Existing note.", "   ") == "Existing note."


def test_application_status_menu_labels_puts_current_status_first():
    labels = application_status_menu_labels("interviewing")

    assert labels[0] == "Interviewing"
    assert labels == ["Interviewing", "Applied", "Offer", "Rejected", "Skipped"]


def test_application_status_menu_labels_defaults_to_editable_statuses():
    assert application_status_menu_labels("needs_status") == [
        "Applied",
        "Interviewing",
        "Offer",
        "Rejected",
        "Skipped",
    ]


def test_filter_application_next_actions_supports_followup_focus_modes():
    actions = [
        {"company": "OverdueCo", "is_overdue": True, "days_until": -2},
        {"company": "TodayCo", "is_overdue": False, "days_until": 0},
        {"company": "SoonCo", "is_overdue": False, "days_until": 5},
        {"company": "LaterCo", "is_overdue": False, "days_until": 12},
        {"company": "UnscheduledCo", "is_overdue": False, "days_until": None},
    ]

    assert [action["company"] for action in filter_application_next_actions(actions)] == [
        "OverdueCo",
        "TodayCo",
        "SoonCo",
        "LaterCo",
        "UnscheduledCo",
    ]
    assert [
        action["company"]
        for action in filter_application_next_actions(actions, "overdue")
    ] == ["OverdueCo"]
    assert [
        action["company"]
        for action in filter_application_next_actions(actions, "due_soon")
    ] == ["TodayCo", "SoonCo"]


def test_format_next_action_due_text_formats_queue_states():
    assert format_next_action_due_text({
        "is_overdue": True,
        "days_until": -2,
    }) == "Overdue by 2 day(s)"
    assert format_next_action_due_text({"days_until": 0}) == "Due today"
    assert format_next_action_due_text({"days_until": 3}) == "Due in 3 day(s)"
    assert format_next_action_due_text({"next_action_date": "2026-05-20"}) == "Due 2026-05-20"
    assert format_next_action_due_text({}) == "No due date"


def test_application_next_action_row_normalizes_display_text():
    row = application_next_action_row({
        "title": "",
        "company": "",
        "status": "needs_status",
        "days_until": 0,
    })

    assert row.title == "Untitled"
    assert row.company == "Unknown company"
    assert row.status_label == "Needs Status"
    assert row.due_text == "Due today"


def test_application_status_from_label_maps_display_labels_to_tracker_values():
    assert application_status_from_label(" Applied ") == "applied"
    assert application_status_from_label("INTERVIEWING") == "interviewing"


def test_normalize_application_detail_input_strips_text_and_preserves_cancel():
    assert normalize_application_detail_input("  Follow up tomorrow  ") == "Follow up tomorrow"
    assert normalize_application_detail_input("   ") == ""
    assert normalize_application_detail_input(None) is None
