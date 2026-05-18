import inspect

from job_radar.gui.applications_tab import _add_application_next_action_queue, build_applications_tab_content
from job_radar.gui.dashboard_panel import add_dashboard_next_steps
from job_radar.gui.main_window import MainWindow
from job_radar.gui.profile_panel import add_profile_field
from job_radar.gui.profile_form import PROFILE_FIELD_HINTS, ProfileForm
from job_radar.gui.search_panel import add_search_readiness_guidance


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
    source = inspect.getsource(add_search_readiness_guidance)

    assert "Profile readiness:" in source
    assert "Review Profile" in source
    assert "command=on_review_profile" in source


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
    assert "build_local_maintenance_summary" in source
    assert "format_source_toggle_recommendations" in source
    assert "build_dashboard_actions" in source
    assert "except Exception" in source


def test_dashboard_next_steps_link_to_target_tabs():
    source = inspect.getsource(add_dashboard_next_steps)

    assert "Next Steps" in source
    assert "action.detail" in source
    assert "command=lambda target=action.target: on_select(target)" in source


def test_profile_field_helper_builds_label_value_rows():
    source = inspect.getsource(add_profile_field)

    assert 'font=ctk.CTkFont(weight="bold")' in source
    assert "column=0" in source
    assert "column=1" in source


def test_show_tab_builds_lazy_tabs_before_navigation():
    source = inspect.getsource(MainWindow._show_tab)

    assert 'tab_name not in self._tabs_built' in source
    assert '_build_search_tab(self._tabview.tab("Search"))' in source
    assert '_build_applications_tab(self._tabview.tab("Applications"))' in source
    assert "self._tabview.set(tab_name)" in source


def test_applications_tab_includes_next_action_queue():
    source = inspect.getsource(build_applications_tab_content)

    assert "get_application_next_actions" in source
    assert "filter_application_next_actions" in source
    assert "_add_application_next_action_queue" in source
    assert "limit=5" in source


def test_application_next_action_queue_includes_complete_action():
    source = inspect.getsource(_add_application_next_action_queue)

    assert "Complete" in source
    assert "callbacks.complete_next_action" in source
    assert "Snooze 3d" in source
    assert "callbacks.snooze_next_action" in source


def test_complete_application_next_action_clears_followup_details():
    source = inspect.getsource(MainWindow._complete_application_next_action)

    assert "update_application_details" in source
    assert 'next_action=""' in source
    assert 'next_action_date=""' in source
    assert "_build_applications_tab(parent)" in source


def test_snooze_application_next_action_moves_due_date_forward():
    source = inspect.getsource(MainWindow._snooze_application_next_action)

    assert "timedelta(days=3)" in source
    assert "update_application_details" in source
    assert "next_action=str(queued_action.get(\"next_action\") or \"\")" in source
    assert "next_action_date=snoozed_date" in source
    assert "_build_applications_tab(parent)" in source


def test_applications_tab_includes_direct_edit_controls():
    source = inspect.getsource(build_applications_tab_content)

    assert "Export Calendar" in source
    assert "callbacks.export_calendar" in source
    assert "callbacks.prompt_next_action" in source
    assert "callbacks.prompt_due_date" in source
    assert "callbacks.prompt_notes" in source
    assert "Edit Notes" in source


def test_calendar_export_writes_followup_ics_file():
    source = inspect.getsource(MainWindow._export_application_followups_ics)

    assert "export_application_followups_ics" in source
    assert "application-followups-" in source
    assert ".ics" in source


def test_search_complete_includes_review_state_summary():
    source = inspect.getsource(MainWindow._show_search_complete)

    assert "_review_state_summary_lines" in source
    assert "review_queue_text" in source


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
    assert "search_context_lines(summary, self._active_search_config)" in source


def test_settings_tab_includes_local_maintenance_summary():
    source = inspect.getsource(MainWindow._build_settings_tab)

    assert "_local_maintenance_text()" in source
    assert "Storage Maintenance" in source
    assert "Clear Dismissed Reviews" in source


def test_settings_tab_includes_privacy_safe_feedback_diagnostics():
    source = inspect.getsource(MainWindow._build_settings_tab)
    helper_source = inspect.getsource(MainWindow._feedback_diagnostics_text)

    assert "Feedback Diagnostics" in source
    assert "_feedback_diagnostics_text()" in source
    assert "build_feedback_diagnostics_summary" in helper_source
    assert "format_feedback_diagnostics_lines" in helper_source


def test_feedback_diagnostics_can_be_copied_from_settings():
    source = inspect.getsource(MainWindow._build_settings_tab)
    handler_source = inspect.getsource(MainWindow._on_copy_feedback_diagnostics)

    assert "Copy Feedback Diagnostics" in source
    assert "command=self._on_copy_feedback_diagnostics" in source
    assert "self.clipboard_clear()" in handler_source
    assert "self.clipboard_append(text)" in handler_source
    assert "Copied redacted feedback diagnostics to clipboard" in handler_source


def test_clear_dismissed_reviews_uses_bounded_review_helper():
    source = inspect.getsource(MainWindow._on_clear_dismissed_reviews)

    assert 'clear_review_state_by_state("dismissed", limit=50)' in source
    assert "review_state_counts()" in source
    assert "dismissed_review_cleanup_success_message" in source


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

    assert "load_recent_search_panel_rows()" in source
    assert "_apply_recent_search" in source
    assert "row.detail" in source


def test_apply_recent_search_uses_search_controls_defaults():
    source = inspect.getsource(MainWindow._apply_recent_search)

    assert "self._search_controls.set_defaults(config)" in source


def test_saved_search_panel_loads_and_applies_named_searches():
    source = inspect.getsource(MainWindow._add_saved_searches_panel)

    assert "Saved Searches" in source
    assert "Save Current" in source
    assert "_apply_saved_search" in source
    assert "load_saved_search_panel_rows()" in source
    assert "row.detail" in source


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


def test_search_tab_receives_pre_run_source_strategy_guidance():
    source = inspect.getsource(MainWindow._show_search_idle)

    assert "source_strategy_lines=self._pre_run_source_strategy_lines()" in source
    helper_source = inspect.getsource(MainWindow._pre_run_source_strategy_lines)
    assert "get_source_health_history(limit=20)" in helper_source
    assert "format_pre_run_source_strategy_lines(history)" in helper_source


def test_run_metadata_recording_is_non_blocking():
    source = inspect.getsource(MainWindow._record_search_run_metadata)

    assert "record_search_run(" in source
    assert "self._active_search_config" in source
    assert "result_stats" in source
    assert "except Exception" in source
