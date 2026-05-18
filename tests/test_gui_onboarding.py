import inspect

from job_radar.gui.applications_tab import _add_application_next_action_queue, build_applications_tab_content
from job_radar.gui.applications_view_model import format_next_action_due_text
from job_radar.gui.dashboard_panel import add_dashboard_next_steps
from job_radar.gui.demo_report_view_model import demo_report_error_message, demo_report_success_message
from job_radar.gui.dialogs import show_message_dialog
from job_radar.gui.main_window import MainWindow
from job_radar.gui.profile_panel import add_profile_field, add_profile_summary_panel, clear_profile_content
from job_radar.gui.profile_form import PROFILE_FIELD_HINTS, ProfileForm
from job_radar.gui.search_panel import (
    add_recent_searches_panel,
    add_saved_searches_panel,
    add_search_readiness_guidance,
    build_search_idle_shell,
    build_search_cancelled_panel,
    build_search_completion_panel,
    build_search_error_panel,
    clear_search_content,
    pack_search_idle_actions,
    build_search_progress_panel,
    replace_success_message,
)
from job_radar.gui.search_summary import search_readiness_guidance_lines
from job_radar.gui.settings_panel import (
    add_api_credentials_panel,
    add_api_key_section,
    add_danger_zone,
    add_jobicy_api_status,
    add_jsearch_setup_tip,
    add_scoring_config_panel,
    add_settings_separator,
    add_storage_maintenance_panel,
    add_update_settings_panel,
)
from job_radar.gui.tab_shell import MAIN_TAB_NAMES, build_main_tabview
from job_radar.gui.welcome_panel import build_welcome_screen
from job_radar.gui.window_shell import clear_content_except_header


def test_welcome_screen_exposes_demo_report_preview():
    source = inspect.getsource(build_welcome_screen)

    assert "Preview Demo Report" in source
    assert "command=on_preview_demo" in source
    assert "Get Started" in source
    assert "on_get_started" in source


def test_window_shell_clear_preserves_header_row():
    source = inspect.getsource(clear_content_except_header)

    assert 'widget.winfo_manager() == "grid"' in source
    assert 'widget.grid_info().get("row") == 0' in source
    assert "widget.destroy()" in source


def test_main_tab_shell_registers_expected_tabs():
    source = inspect.getsource(build_main_tabview)

    assert MAIN_TAB_NAMES == ("Profile", "Search", "Applications", "Settings")
    assert "ctk.CTkTabview(parent, command=on_tab_change)" in source
    assert "row=2" in source
    assert "for tab_name in MAIN_TAB_NAMES" in source
    assert "tabview.add(tab_name)" in source


def test_profile_save_navigation_reuses_search_success_flow():
    created_source = inspect.getsource(MainWindow._on_profile_created)
    updated_source = inspect.getsource(MainWindow._on_profile_updated)
    helper_source = inspect.getsource(MainWindow._show_search_tab_with_success)

    assert '_show_search_tab_with_success("Profile created successfully!")' in created_source
    assert '_show_search_tab_with_success("Profile updated successfully!")' in updated_source
    assert 'self._build_tab_if_needed("Search")' in helper_source
    assert 'self._tabview.set("Search")' in helper_source
    assert "self._show_success_message(message)" in helper_source


def test_search_success_message_helper_replaces_existing_label():
    source = inspect.getsource(replace_success_message)
    window_source = inspect.getsource(MainWindow._show_success_message)

    assert "existing_label.destroy()" in source
    assert "text_color=\"green\"" in source
    assert "row=1" in source
    assert "return success_label" in source
    assert "replace_success_message" in window_source
    assert "self.after(3000, self._hide_success_message)" in window_source


def test_demo_report_feedback_supports_welcome_and_search_contexts():
    source = inspect.getsource(MainWindow._open_demo_report)

    assert "_show_demo_report_message" in source
    assert "_has_search_content" in source
    assert "demo_report_success_message" in source
    assert "demo_report_error_message" in source
    assert "Open manually:" in inspect.getsource(demo_report_success_message)
    assert "Could not generate demo report:" in inspect.getsource(demo_report_error_message)


def test_search_idle_includes_profile_readiness_guidance():
    source = inspect.getsource(MainWindow._show_search_idle)

    assert "_add_search_readiness_guidance" in source
    assert "clear_search_content(self._search_content)" in source


def test_search_state_views_reuse_clear_content_helper():
    helper_source = inspect.getsource(clear_search_content)

    assert "for widget in parent.winfo_children()" in helper_source
    assert "widget.destroy()" in helper_source
    assert "clear_search_content(self._search_content)" in inspect.getsource(MainWindow._show_search_progress)
    assert "clear_search_content(self._search_content)" in inspect.getsource(MainWindow._show_search_complete)
    assert "clear_search_content(self._search_content)" in inspect.getsource(MainWindow._on_search_cancelled)
    assert "clear_search_content(self._search_content)" in inspect.getsource(MainWindow._show_search_error)


def test_profile_readiness_guidance_links_to_profile_tab():
    source = inspect.getsource(add_search_readiness_guidance)
    helper_source = inspect.getsource(search_readiness_guidance_lines)
    window_source = inspect.getsource(MainWindow._add_search_readiness_guidance)

    assert "Profile readiness:" in source
    assert "Review Profile" in source
    assert "command=on_review_profile" in source
    assert "readiness_guidance_lines(readiness)" in helper_source
    assert "scoring_signal_guidance_lines" in helper_source
    assert "search_readiness_guidance_lines(readiness)" in window_source


def test_profile_tab_includes_dashboard_next_steps():
    source = inspect.getsource(MainWindow._build_profile_tab)

    assert "clear_profile_content(parent)" in source
    assert "_dashboard_actions(readiness)" in source
    assert "_add_dashboard_next_steps" in source
    assert "add_profile_summary_panel" in source


def test_profile_edit_reuses_profile_clear_helper():
    helper_source = inspect.getsource(clear_profile_content)
    source = inspect.getsource(MainWindow._on_edit_profile)

    assert "for widget in parent.winfo_children()" in helper_source
    assert "widget.destroy()" in helper_source
    assert "clear_profile_content(profile_tab)" in source


def test_profile_summary_panel_includes_readiness_and_edit_action():
    source = inspect.getsource(add_profile_summary_panel)

    assert "Profile Readiness:" in source
    assert "Scoring Signals:" in source
    assert "Edit Profile" in source
    assert "command=lambda: on_edit(profile)" in source


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
    helper_source = inspect.getsource(MainWindow._build_tab_if_needed)

    assert "self._build_tab_if_needed(tab_name)" in source
    assert 'tab_name in self._tabs_built' in helper_source
    assert '_build_search_tab(self._tabview.tab("Search"))' in helper_source
    assert '_build_applications_tab(self._tabview.tab("Applications"))' in helper_source
    assert "self._tabview.set(tab_name)" in source


def test_tab_change_reuses_lazy_tab_builder():
    source = inspect.getsource(MainWindow._on_tab_change)

    assert "current_tab = self._tabview.get()" in source
    assert "self._build_tab_if_needed(current_tab)" in source


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
    assert "build_search_completion_panel" in source


def test_search_completion_panel_includes_report_actions():
    source = inspect.getsource(build_search_completion_panel)

    assert "completion_message(job_count)" in source
    assert "Open Report" in source
    assert "New Search" in source
    assert "on_open_report" in source
    assert "on_new_search" in source


def test_search_error_panel_includes_retry_and_back_actions():
    source = inspect.getsource(build_search_error_panel)

    assert "Search failed" in source
    assert "error_message(message)" in source
    assert "Try Again" in source
    assert "Back to Search" in source


def test_search_cancelled_panel_includes_new_search_action():
    source = inspect.getsource(build_search_cancelled_panel)

    assert "Search cancelled" in source
    assert "cancellation_message()" in source
    assert "New Search" in source
    assert "on_new_search" in source


def test_modal_message_dialog_centers_and_closes():
    source = inspect.getsource(show_message_dialog)

    assert "CTkToplevel(parent)" in source
    assert "dialog.grab_set()" in source
    assert "dialog.geometry(f\"+{x}+{y}\")" in source
    assert "command=dialog.destroy" in source


def test_search_run_metadata_records_review_counts():
    source = inspect.getsource(MainWindow._record_search_run_metadata)

    assert "review_counts=review_state_counts()" in source


def test_next_action_due_text_formats_queue_states():
    assert format_next_action_due_text({
        "is_overdue": True,
        "days_until": -2,
    }) == "Overdue by 2 day(s)"
    assert format_next_action_due_text({"days_until": 0}) == "Due today"
    assert format_next_action_due_text({"days_until": 3}) == "Due in 3 day(s)"
    assert format_next_action_due_text({}) == "No due date"


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
    helper_source = inspect.getsource(add_storage_maintenance_panel)

    assert "_local_maintenance_text()" in source
    assert "Storage Maintenance" in helper_source
    assert "Clear Dismissed Reviews" in helper_source


def test_settings_tab_includes_privacy_safe_feedback_diagnostics():
    source = inspect.getsource(MainWindow._build_settings_tab)
    panel_source = inspect.getsource(add_storage_maintenance_panel)
    helper_source = inspect.getsource(MainWindow._feedback_diagnostics_text)

    assert "Feedback Diagnostics" in panel_source
    assert "_feedback_diagnostics_text()" in source
    assert "build_feedback_diagnostics_summary" in helper_source
    assert "format_feedback_diagnostics_lines" in helper_source


def test_feedback_diagnostics_can_be_copied_from_settings():
    source = inspect.getsource(add_storage_maintenance_panel)
    handler_source = inspect.getsource(MainWindow._on_copy_feedback_diagnostics)

    assert "Copy Feedback Diagnostics" in source
    assert "command=on_copy_feedback_diagnostics" in source
    assert "self.clipboard_clear()" in handler_source
    assert "self.clipboard_append(text)" in handler_source
    assert "Copied redacted feedback diagnostics to clipboard" in handler_source


def test_settings_api_helpers_include_public_source_and_setup_tip():
    jobicy_source = inspect.getsource(add_jobicy_api_status)
    tip_source = inspect.getsource(add_jsearch_setup_tip)

    assert "Jobicy (Remote Jobs)" in jobicy_source
    assert "Always available" in jobicy_source
    assert "JSearch API key" in tip_source
    assert "LinkedIn, Indeed, and Glassdoor" in tip_source


def test_settings_api_section_helper_builds_fields_and_test_controls():
    source = inspect.getsource(add_api_key_section)

    assert "Test API Key" in source
    assert "on_test(fields)" in source
    assert "api_fields[field_id]" in source
    assert "quota_labels[backend_api]" in source


def test_settings_api_credentials_panel_lists_sources_and_save_action():
    source = inspect.getsource(add_api_credentials_panel)

    assert "API Key Settings" in source
    assert "API_CREDENTIAL_SECTIONS" in source
    assert "add_jobicy_api_status" in source
    assert "add_jsearch_setup_tip" in source
    assert "Save API Keys" in source


def test_settings_update_panel_builds_status_and_controls():
    source = inspect.getsource(add_update_settings_panel)

    assert "Updates" in source
    assert "update_status_text" in source
    assert "Check for Updates" in source
    assert "View release notes" in source
    assert "Clear skipped versions" in source


def test_settings_separator_helper_keeps_section_dividers_consistent():
    source = inspect.getsource(add_settings_separator)
    tab_source = inspect.getsource(MainWindow._build_settings_tab)

    assert "ctk.CTkFrame(parent, height=height, fg_color=fg_color)" in source
    assert "separator.pack(fill=\"x\", pady=pady, padx=10)" in source
    assert "add_settings_separator(scroll_frame" in tab_source
    assert 'height=1, fg_color="gray", pady=(10, 20)' in tab_source


def test_settings_danger_zone_includes_uninstall_action():
    source = inspect.getsource(add_danger_zone)

    assert "Danger Zone" in source
    assert "Uninstall Job Radar" in source
    assert "command=on_uninstall" in source


def test_settings_scoring_panel_builds_widget_with_save_callback():
    source = inspect.getsource(add_scoring_config_panel)

    assert "ScoringConfigWidget" in source
    assert "on_save_callback=on_save" in source
    assert "scoring_config.pack" in source


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


def test_search_progress_panel_exposes_updatable_widgets():
    source = inspect.getsource(build_search_progress_panel)

    assert "Starting search..." in source
    assert "Source 0 of 0" in source
    assert "command=on_cancel" in source
    assert "SearchProgressWidgets" in source


def test_search_idle_includes_recent_searches_panel():
    source = inspect.getsource(MainWindow._show_search_idle)

    assert "_add_recent_searches_panel" in source
    assert "_add_saved_searches_panel" in source
    assert "build_search_idle_shell" in source
    assert "pack_search_idle_actions" in source


def test_search_idle_shell_builds_controls_and_actions():
    source = inspect.getsource(build_search_idle_shell)

    assert "SearchControls" in source
    assert "Run Search" in source
    assert "Preview Demo Report" in source
    assert "Profile required to run search" in source
    assert "SearchIdleWidgets" in source


def test_recent_search_panel_loads_and_applies_configs():
    source = inspect.getsource(add_recent_searches_panel)

    assert "Recent Searches" in source
    assert "on_apply(cfg)" in source
    assert "row.detail" in source


def test_apply_recent_search_uses_search_controls_defaults():
    source = inspect.getsource(MainWindow._apply_recent_search)

    assert "self._search_controls.set_defaults(config)" in source


def test_saved_search_panel_loads_and_applies_named_searches():
    source = inspect.getsource(add_saved_searches_panel)

    assert "Saved Searches" in source
    assert "Save Current" in source
    assert "on_apply(cfg)" in source
    assert "on_save_current" in source
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
