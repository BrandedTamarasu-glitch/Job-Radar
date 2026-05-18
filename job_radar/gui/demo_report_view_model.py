"""Display text helpers for GUI demo-report actions."""


def demo_report_success_message(report_path: str, opened: bool) -> str:
    """Return GUI feedback after a demo report is generated."""
    message = "Demo report generated."
    if not opened:
        message += f" Open manually: {report_path}"
    return message


def demo_report_error_message(error: Exception) -> str:
    """Return GUI feedback when demo report generation fails."""
    return f"Could not generate demo report: {error}"
