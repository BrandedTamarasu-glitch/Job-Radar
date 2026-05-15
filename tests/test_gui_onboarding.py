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


def test_profile_tab_includes_dashboard_next_steps():
    source = inspect.getsource(MainWindow._build_profile_tab)

    assert "_dashboard_actions(readiness)" in source
    assert "_add_dashboard_next_steps" in source


def test_dashboard_actions_use_local_state_sources():
    source = inspect.getsource(MainWindow._dashboard_actions)

    assert "get_all_application_statuses()" in source
    assert "get_application_next_actions" in source
    assert "review_state_counts()" in source
    assert "load_search_history()" in source
    assert "build_dashboard_actions" in source
    assert "except Exception" in source


def test_dashboard_next_steps_link_to_target_tabs():
    source = inspect.getsource(MainWindow._add_dashboard_next_steps)

    assert "Next Steps" in source
    assert "action.detail" in source
    assert "command=lambda target=action.target: self._show_tab(target)" in source


def test_show_tab_builds_lazy_tabs_before_navigation():
    source = inspect.getsource(MainWindow._show_tab)

    assert 'tab_name not in self._tabs_built' in source
    assert '_build_search_tab(self._tabview.tab("Search"))' in source
    assert '_build_applications_tab(self._tabview.tab("Applications"))' in source
    assert "self._tabview.set(tab_name)" in source


def test_applications_tab_includes_next_action_queue():
    source = inspect.getsource(MainWindow._build_applications_tab)

    assert "get_application_next_actions" in source
    assert "_add_application_next_action_queue" in source
    assert "limit=5" in source


def test_applications_tab_includes_direct_edit_controls():
    source = inspect.getsource(MainWindow._build_applications_tab)

    assert "_prompt_application_next_action" in source
    assert "_prompt_application_due_date" in source
    assert "_prompt_application_notes" in source
    assert "Edit Notes" in source


def test_search_complete_includes_review_state_summary():
    source = inspect.getsource(MainWindow._show_search_complete)

    assert "_review_state_summary_lines" in source
    assert "Review queue:" in source


def test_search_run_metadata_records_review_counts():
    source = inspect.getsource(MainWindow._record_search_run_metadata)

    assert "review_counts=review_state_counts()" in source


def test_next_action_due_text_formats_queue_states():
    assert MainWindow._format_next_action_due_text(None, {
        "is_overdue": True,
        "days_until": -2,
    }) == "Overdue by 2 day(s)"
    assert MainWindow._format_next_action_due_text(None, {"days_until": 0}) == "Due today"
    assert MainWindow._format_next_action_due_text(None, {"days_until": 3}) == "Due in 3 day(s)"
    assert MainWindow._format_next_action_due_text(None, {}) == "No due date"


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


def test_real_search_stores_active_config_for_completion_metadata():
    source = inspect.getsource(MainWindow._start_real_search)

    assert "self._active_search_config = search_config.copy()" in source


def test_search_idle_includes_recent_searches_panel():
    source = inspect.getsource(MainWindow._show_search_idle)

    assert "_add_recent_searches_panel" in source
    assert "_add_saved_searches_panel" in source


def test_recent_search_panel_loads_and_applies_configs():
    source = inspect.getsource(MainWindow._add_recent_searches_panel)

    assert "load_search_history()" in source
    assert "_apply_recent_search" in source
    assert "recent_searches[:3]" in source
    assert "format_run_summary(item)" in source
    assert "format_search_insight(item)" in source


def test_apply_recent_search_uses_search_controls_defaults():
    source = inspect.getsource(MainWindow._apply_recent_search)

    assert "self._search_controls.set_defaults(config)" in source


def test_saved_search_panel_loads_and_applies_named_searches():
    source = inspect.getsource(MainWindow._add_saved_searches_panel)

    assert "Saved Searches" in source
    assert "Save Current" in source
    assert "_apply_saved_search" in source
    assert "format_run_summary(item)" in source
    assert "format_search_insight(item)" in source


def test_save_current_search_persists_named_search():
    source = inspect.getsource(MainWindow._save_current_search)

    assert "summarize_search_config(config)" in source
    assert "save_named_search(name, config)" in source
    assert "self._search_controls.validate()" in source


def test_apply_saved_search_uses_search_controls_defaults():
    source = inspect.getsource(MainWindow._apply_saved_search)

    assert "self._search_controls.set_defaults(config)" in source


def test_search_completion_records_run_metadata():
    source = inspect.getsource(MainWindow._on_search_complete)

    assert "self._record_search_run_metadata(summary)" in source


def test_run_metadata_recording_is_non_blocking():
    source = inspect.getsource(MainWindow._record_search_run_metadata)

    assert "record_search_run(" in source
    assert "self._active_search_config" in source
    assert "result_stats" in source
    assert "except Exception" in source
