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


def test_search_idle_includes_profile_readiness_guidance():
    source = inspect.getsource(MainWindow._show_search_idle)

    assert "_add_search_readiness_guidance" in source


def test_profile_readiness_guidance_links_to_profile_tab():
    source = inspect.getsource(MainWindow._add_search_readiness_guidance)

    assert "Profile readiness:" in source
    assert "Review Profile" in source
    assert "command=self._show_profile_tab" in source
