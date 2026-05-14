import inspect

from job_radar.gui.main_window import MainWindow


def test_welcome_screen_exposes_demo_report_preview():
    source = inspect.getsource(MainWindow._show_welcome_screen)

    assert "Preview Demo Report" in source
    assert "command=self._open_demo_report" in source


def test_demo_report_feedback_supports_welcome_and_search_contexts():
    source = inspect.getsource(MainWindow._open_demo_report)

    assert "_show_demo_report_message" in source
    assert "_has_search_content" in source
