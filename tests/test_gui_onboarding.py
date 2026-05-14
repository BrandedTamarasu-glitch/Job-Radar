import inspect

from job_radar.gui.main_window import MainWindow
from job_radar.gui.profile_form import PROFILE_FIELD_HINTS, ProfileForm


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


def test_profile_form_hints_cover_match_quality_fields():
    assert "target_titles" in PROFILE_FIELD_HINTS
    assert "core_skills" in PROFILE_FIELD_HINTS
    assert "secondary_skills" in PROFILE_FIELD_HINTS
    assert "location" in PROFILE_FIELD_HINTS
    assert "arrangement" in PROFILE_FIELD_HINTS
    assert "comp_floor" in PROFILE_FIELD_HINTS
    assert "dealbreakers" in PROFILE_FIELD_HINTS


def test_profile_form_renders_field_hints():
    source = inspect.getsource(ProfileForm._show_form)

    assert 'self._add_field_hint(form_frame, "target_titles")' in source
    assert 'self._add_field_hint(form_frame, "core_skills")' in source
    assert 'self._add_field_hint(form_frame, "dealbreakers")' in source


def test_search_complete_loads_profile_for_zero_result_guidance():
    source = inspect.getsource(MainWindow._show_search_complete)

    assert "zero_result_lines(job_count, self._load_current_profile_for_guidance())" in source


def test_real_search_records_recent_search_before_progress():
    source = inspect.getsource(MainWindow._start_real_search)

    assert "self._record_recent_search(search_config)" in source
    assert source.index("self._record_recent_search(search_config)") < source.index("self._show_search_progress()")


def test_recent_search_recording_is_non_blocking():
    source = inspect.getsource(MainWindow._record_recent_search)

    assert "record_recent_search(search_config)" in source
    assert "except Exception" in source
