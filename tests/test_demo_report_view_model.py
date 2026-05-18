"""Tests for GUI demo-report feedback text."""

from job_radar.gui.demo_report_view_model import (
    demo_report_error_message,
    demo_report_success_message,
)


def test_demo_report_success_message_mentions_manual_path_when_browser_does_not_open():
    assert demo_report_success_message("/tmp/demo.html", opened=True) == "Demo report generated."
    assert demo_report_success_message("/tmp/demo.html", opened=False) == (
        "Demo report generated. Open manually: /tmp/demo.html"
    )


def test_demo_report_error_message_includes_exception_detail():
    assert demo_report_error_message(RuntimeError("disk full")) == (
        "Could not generate demo report: disk full"
    )
