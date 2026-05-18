"""Main GUI window for Job Radar desktop application.

Integrates ProfileForm (create/edit), SearchControls (date/score/new-only),
and SearchWorker (full search pipeline) into a tabbed interface. Manages
navigation, progress display, and report opening.
"""

import os
import queue
import sys
import threading
import webbrowser
from datetime import date
from datetime import timedelta
from pathlib import Path

import customtkinter as ctk
import requests

from job_radar import __version__
from job_radar.api_config import (
    ApiCredentialError,
    get_api_credentials_path,
    read_api_credentials_file,
    save_api_credentials,
)
from job_radar.application_templates import (
    render_application_note_template,
)
from job_radar.applications_export import (
    export_application_followups_ics,
    export_applications_csv,
    import_report_status_updates_json,
)
from job_radar.browser import open_report_in_browser
from job_radar.data_portability import export_app_data_bundle, validate_app_data_bundle
from job_radar.demo_report import generate_demo_report
from job_radar.paths import get_data_dir
from job_radar.paths import get_results_dir
from job_radar.profile_readiness import (
    assess_profile_readiness,
    readiness_guidance_lines,
    scoring_signal_guidance_lines,
)
from job_radar.profile_manager import load_profile
from job_radar.config import load_config
from job_radar.tracker import (
    get_all_application_statuses,
    get_application_next_actions,
    merge_application_entries,
    get_source_health_history,
    update_application_details,
    update_application_status,
)
from job_radar.update_checker import UpdateChecker, launch_installer, cleanup_old_installers, extract_summary
from job_radar.gui.api_status_view_model import (
    ApiStatusDisplay,
    api_error_status,
    api_missing_credentials_status,
    api_missing_key_status,
    api_network_error_status,
    api_response_status,
    api_testing_status,
    api_timeout_status,
)
from job_radar.gui.applications_view_model import (
    append_application_note,
    application_calendar_export_error_message,
    application_calendar_export_success_message,
    application_detail_update_error_message,
    application_followup_snooze_error_message,
    application_followup_update_error_message,
    application_status_from_label,
    application_status_import_error_message,
    application_status_import_success_message,
    application_status_update_error_message,
    application_template_insert_error_message,
    applications_csv_export_error_message,
    applications_csv_export_success_message,
    format_next_action_due_text,
    normalize_application_detail_input,
)
from job_radar.gui.applications_tab import ApplicationsTabCallbacks, build_applications_tab_content
from job_radar.gui.dashboard_view_model import build_dashboard_actions
from job_radar.gui.dashboard_panel import add_dashboard_next_steps
from job_radar.gui.dialogs import show_message_dialog
from job_radar.gui.profile_panel import add_profile_field, add_profile_summary_panel
from job_radar.gui.profile_form import ProfileForm
from job_radar.gui.profile_view_model import (
    build_profile_readiness_display,
    build_profile_summary_rows,
    profile_load_error_message,
)
from job_radar.gui.review_state_view_model import format_review_state_summary
from job_radar.gui.search_controls import SearchControls
from job_radar.gui.search_panel import (
    add_recent_searches_panel,
    add_saved_searches_panel,
    add_search_readiness_guidance,
    build_search_cancelled_panel,
    build_search_completion_panel,
    build_search_error_panel,
    build_search_progress_panel,
)
from job_radar.gui.search_summary import (
    bullet_block_text,
    cache_summary_line,
    review_queue_text,
    search_context_lines,
    source_fetching_message,
    source_job_count_line,
    source_progress_count_text,
    source_summary_lines,
    source_warning_message,
    zero_result_lines,
)
from job_radar.gui.settings_panel import (
    add_api_credentials_panel,
    add_api_key_section,
    add_danger_zone,
    add_storage_maintenance_panel,
    add_update_settings_panel,
)
from job_radar.gui.maintenance_view_model import (
    app_data_bundle_validation_message,
    app_data_export_error_message,
    app_data_export_success_message,
    build_feedback_diagnostics_summary,
    build_local_maintenance_summary,
    cache_clear_error_message,
    cache_clear_success_message,
    dismissed_review_cleanup_error_message,
    dismissed_review_cleanup_success_message,
    format_feedback_diagnostics_lines,
    format_local_maintenance_lines,
)
from job_radar.gui.source_diagnostics_view_model import (
    format_source_diagnostics_lines,
    format_pre_run_source_strategy_lines,
    format_source_toggle_recommendations,
    build_source_diagnostics,
)
from job_radar.gui.worker_thread import create_search_worker, create_download_worker, normalize_source_progress
from job_radar.gui.scoring_config import ScoringConfigWidget
from job_radar.gui.update_banner import UpdateBanner, DownloadConfirmDialog
from job_radar.gui.update_status_view_model import build_update_status_display
from job_radar.gui.changelog_dialog import ChangelogDialog
from job_radar.gui.welcome_panel import build_welcome_screen
from job_radar.gui.installer_dialogs import InstallConfirmDialog, LinuxInstallInstructionsDialog
from job_radar.gui.install_status_view_model import (
    install_launch_error_message,
    install_launch_status_message,
    install_prompt_message,
    installer_not_found_message,
)
from job_radar.gui.uninstall_dialog import (
    BackupOfferDialog,
    PathPreviewDialog,
    FinalConfirmationDialog,
    DeletionProgressDialog,
)
from job_radar.rate_limits import get_quota_usage
from job_radar.review_state import clear_review_state_by_state, review_state_counts
from job_radar.saved_searches import (
    load_search_history,
    load_recent_search_panel_rows,
    load_saved_search_panel_rows,
    record_search_run,
    record_recent_search,
    saved_search_error_message,
    saved_search_success_message,
    save_named_search,
    summarize_search_config,
)
from job_radar.uninstaller import (
    get_uninstall_paths,
    create_backup,
    delete_app_data,
    get_binary_path,
    create_cleanup_script,
)
from dotenv import load_dotenv


class MainWindow(ctk.CTk):
    """Main application window with system theme, header, tabs, and routing.

    Routes to welcome screen on first launch (no profile), or tabbed interface
    for users with existing profiles. Manages profile creation/editing flow,
    search execution with progress display, and report opening.
    """

    def __init__(self):
        super().__init__()

        # Clean up old installer files from previous sessions
        cleanup_old_installers()

        # Set appearance and theme
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Configure window
        self.title("Job Radar")
        self.geometry("900x600")
        self.minsize(700, 500)

        # Grid layout: row 0 = header (fixed), row 1 = banner (fixed), row 2 = content (expands)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Threading infrastructure
        self._queue = queue.Queue()
        self._worker = None
        self._worker_thread = None

        # State tracking
        self._profile_exists = self._has_profile()
        self._report_path = None
        self._tabview = None
        self._success_message_label = None
        self._welcome_status_label = None

        # Update checker state
        self._update_banner = None
        self._update_checker = UpdateChecker(self._queue)
        self._manual_check_button = None
        self._update_status_label = None
        self._manual_check_pending = False
        self._update_tag = None  # GitHub tag for fetching assets
        self._update_version = None  # Track available update version for Settings display
        self._update_release_url = None  # Track release URL for Settings link
        self._release_notes_label = None  # Settings "View release notes" link reference
        self._clear_skipped_btn = None  # Settings "Clear skipped versions" button reference
        self._skipped_status_label = None  # Settings skipped version status label reference
        self._cache_status_label = None  # Settings cache maintenance status label reference
        self._source_diagnostics_textbox = None  # Settings source diagnostics text reference
        self._applications_export_status_label = None  # Applications tab export status
        self._application_followup_filter = "all"  # Applications follow-up queue filter
        self._saved_search_status_label = None  # Search tab saved-search feedback
        self._active_search_config = None  # Search config for completion metadata

        # Download worker state
        self._download_worker = None
        self._download_thread = None
        self._download_cancelled_this_session = False  # Session-only suppress flag
        self._installer_path = None  # Path to downloaded installer file

        # Create header
        self._create_header()

        # Check if profile exists and route to appropriate view
        if not self._profile_exists:
            self._show_welcome_screen()
        else:
            self._show_main_tabs()
            # Start background update check if profile exists
            self._start_update_check()

        # Start queue polling loop
        self._check_queue()

        # Register cleanup handler for app exit
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """Handle app closing - cancel download worker if active."""
        if self._download_worker:
            self._download_worker.cancel()
        self.destroy()

    def _create_header(self):
        """Create header frame with app name and version."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        # App title on left
        title_label = ctk.CTkLabel(
            header_frame,
            text="Job Radar",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")

        # Version on right
        version_label = ctk.CTkLabel(
            header_frame,
            text=f"v{__version__}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version_label.pack(side="right")

    def _has_profile(self) -> bool:
        """Check if profile.json exists in the data directory."""
        return (get_data_dir() / "profile.json").exists()

    def _show_welcome_screen(self):
        """Display welcome screen for first-time users."""
        # Clear ALL content (grid, place, pack) except header
        for widget in list(self.winfo_children()):
            # Keep only header (row 0 grid widget)
            if widget.winfo_manager() == 'grid' and widget.grid_info().get('row') == 0:
                continue
            widget.destroy()

        self._welcome_status_label = build_welcome_screen(
            self,
            on_get_started=self._on_get_started,
            on_preview_demo=self._open_demo_report,
        )

    def _on_get_started(self):
        """Handle Get Started button click - show profile form in create mode."""
        # Clear ALL content (grid, place, pack) except header
        for widget in list(self.winfo_children()):
            # Keep only header (row 0 grid widget)
            if widget.winfo_manager() == 'grid' and widget.grid_info().get('row') == 0:
                continue
            widget.destroy()

        # Create ProfileForm in create mode (directly in row 1, no container)
        form = ProfileForm(
            parent=self,
            on_save_callback=self._on_profile_created,
            on_cancel_callback=self._show_welcome_screen,
            existing_profile=None
        )
        form.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _on_profile_created(self, profile_data: dict):
        """Handle successful profile creation.

        Parameters
        ----------
        profile_data : dict
            Saved profile data
        """
        # Update state
        self._profile_exists = True

        # Show main tabs and navigate to Search tab with success message
        self._show_main_tabs()
        # Manually trigger tab build before programmatic switch (lazy loading workaround)
        if "Search" not in self._tabs_built:
            self._build_search_tab(self._tabview.tab("Search"))
            self._tabs_built.add("Search")
        self._tabview.set("Search")
        self._show_success_message("Profile created successfully!")

    def _on_profile_updated(self, profile_data: dict):
        """Handle successful profile update.

        Parameters
        ----------
        profile_data : dict
            Saved profile data
        """
        # Rebuild profile tab content with updated data
        self._build_profile_tab(self._tabview.tab("Profile"))

        # Navigate to Search tab with success message
        # Manually trigger tab build before programmatic switch (lazy loading workaround)
        if "Search" not in self._tabs_built:
            self._build_search_tab(self._tabview.tab("Search"))
            self._tabs_built.add("Search")
        self._tabview.set("Search")
        self._show_success_message("Profile updated successfully!")

    def _show_success_message(self, message: str):
        """Display temporary success message on Search tab.

        Parameters
        ----------
        message : str
            Success message text
        """
        # Remove existing success message if present
        if self._success_message_label:
            self._success_message_label.destroy()
            self._success_message_label = None

        # Create success message label — use grid row 1 (row 0 is content)
        self._success_message_label = ctk.CTkLabel(
            self._search_content,
            text=message,
            text_color="green",
            font=ctk.CTkFont(size=13)
        )
        self._success_message_label.grid(row=1, column=0, pady=(0, 10))

        # Auto-hide after 3 seconds
        self.after(3000, self._hide_success_message)

    def _hide_success_message(self):
        """Hide success message label."""
        if self._success_message_label:
            self._success_message_label.destroy()
            self._success_message_label = None

    def _show_main_tabs(self):
        """Display tabbed interface for users with existing profiles."""
        # Clear ALL content (grid, place, pack) except header
        for widget in list(self.winfo_children()):
            # Keep only header (row 0 grid widget)
            if widget.winfo_manager() == 'grid' and widget.grid_info().get('row') == 0:
                continue
            widget.destroy()

        # Create tabview (row 2 for content, row 1 reserved for banner)
        self._tabview = ctk.CTkTabview(self, command=self._on_tab_change)
        self._tabview.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self._tabview.add("Profile")
        self._tabview.add("Search")
        self._tabview.add("Applications")
        self._tabview.add("Settings")

        # Track which tabs have been built (lazy loading)
        self._tabs_built = set()

        # Set default to Profile tab
        self._tabview.set("Profile")

        # Build only the Profile tab initially (lazy-load others on first access)
        self._build_profile_tab(self._tabview.tab("Profile"))
        self._tabs_built.add("Profile")

    def _on_tab_change(self):
        """Handle tab change - lazy-build tabs on first access."""
        current_tab = self._tabview.get()

        # Build tab if not already built
        if current_tab not in self._tabs_built:
            if current_tab == "Search":
                self._build_search_tab(self._tabview.tab("Search"))
            elif current_tab == "Applications":
                self._build_applications_tab(self._tabview.tab("Applications"))
            elif current_tab == "Settings":
                self._build_settings_tab(self._tabview.tab("Settings"))
            self._tabs_built.add(current_tab)

    def _build_profile_tab(self, parent):
        """Build Profile tab with profile summary display and Edit button.

        Parameters
        ----------
        parent
            Parent tab widget
        """
        # Clear existing content
        for widget in parent.winfo_children():
            widget.destroy()

        # Create scrollable frame for profile content
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Try to load and display profile
        try:
            profile_path = get_data_dir() / "profile.json"
            profile = load_profile(profile_path)
            readiness = assess_profile_readiness(profile)

            # Configure grid for label-value pairs
            scroll_frame.grid_columnconfigure(0, weight=0)  # Labels (left)
            scroll_frame.grid_columnconfigure(1, weight=1)  # Values (right)

            row = 0

            dashboard_actions = self._dashboard_actions(readiness)
            row = self._add_dashboard_next_steps(scroll_frame, row, dashboard_actions)

            readiness_display = build_profile_readiness_display(
                readiness,
                scoring_signal_guidance_lines(readiness, limit=3),
            )
            add_profile_summary_panel(
                scroll_frame,
                row,
                profile=profile,
                readiness_display=readiness_display,
                summary_rows=build_profile_summary_rows(profile),
                on_edit=self._on_edit_profile,
            )

        except Exception as e:
            # Error loading profile
            error_label = ctk.CTkLabel(
                scroll_frame,
                text=profile_load_error_message(e),
                text_color="red"
            )
            error_label.pack(pady=20)

    def _dashboard_actions(self, readiness):
        """Build profile dashboard actions without blocking the profile view."""
        try:
            applications = get_all_application_statuses()
        except Exception:
            applications = {}

        try:
            next_actions = get_application_next_actions(
                applications=applications,
                limit=5,
            )
        except Exception:
            next_actions = []

        try:
            review_counts = review_state_counts()
        except Exception:
            review_counts = {}

        try:
            search_history = load_search_history()
        except Exception:
            search_history = {"recent": [], "saved": []}

        try:
            maintenance_summary = build_local_maintenance_summary(
                get_data_dir(),
                get_results_dir(),
            )
            maintenance_suggestions = maintenance_summary.suggestions
        except Exception:
            maintenance_suggestions = []

        try:
            source_quality_issues = format_source_toggle_recommendations(
                build_source_diagnostics(get_source_health_history(limit=20))
            )
        except Exception:
            source_quality_issues = []

        return build_dashboard_actions(
            readiness=readiness,
            review_counts=review_counts,
            next_actions=next_actions,
            search_history=search_history,
            maintenance_suggestions=maintenance_suggestions,
            source_quality_issues=source_quality_issues,
        )

    def _add_dashboard_next_steps(self, parent, row, actions):
        """Render the profile dashboard next-step queue."""
        return add_dashboard_next_steps(parent, row, actions, on_select=self._show_tab)

    def _on_edit_profile(self, profile: dict):
        """Handle Edit Profile button click.

        Parameters
        ----------
        profile : dict
            Current profile data
        """
        # Clear profile tab content
        profile_tab = self._tabview.tab("Profile")
        for widget in profile_tab.winfo_children():
            widget.destroy()

        # Create ProfileForm in edit mode
        form = ProfileForm(
            parent=profile_tab,
            on_save_callback=self._on_profile_updated,
            on_cancel_callback=lambda: self._build_profile_tab(self._tabview.tab("Profile")),
            existing_profile=profile
        )
        form.pack(fill="both", expand=True)

    def _add_profile_field(self, parent, row, label_text, value_text):
        """Add a label-value pair to the profile grid.

        Parameters
        ----------
        parent
            Parent widget
        row : int
            Grid row number
        label_text : str
            Label text
        value_text : str
            Value text
        """
        add_profile_field(parent, row, label_text, value_text)

    def _build_search_tab(self, parent):
        """Build Search tab with search controls and threading integration.

        Parameters
        ----------
        parent
            Parent tab widget
        """
        # Create content frame that will hold either idle or progress state
        self._search_content = ctk.CTkFrame(parent, fg_color="transparent")
        self._search_content.pack(fill="both", expand=True, padx=10, pady=10)
        self._search_content.grid_rowconfigure(0, weight=1)
        self._search_content.grid_columnconfigure(0, weight=1)

        # Start with idle state
        self._show_search_idle()

    def _build_applications_tab(self, parent):
        """Build Applications tab with grouped pipeline statuses."""
        self._applications_export_status_label = build_applications_tab_content(
            parent,
            followup_filter=self._application_followup_filter,
            callbacks=ApplicationsTabCallbacks(
                export_csv=self._export_applications_csv,
                import_status_updates=lambda: self._import_report_status_updates(parent),
                export_calendar=self._export_application_followups_ics,
                refresh=lambda: self._build_applications_tab(parent),
                set_followup_filter=lambda key: self._set_application_followup_filter(parent, key),
                update_status=lambda row, selected: self._update_application_status_from_menu(
                    parent,
                    row,
                    selected,
                ),
                prompt_next_action=lambda row: self._prompt_application_next_action(parent, row),
                prompt_due_date=lambda row: self._prompt_application_due_date(parent, row),
                prompt_notes=lambda row: self._prompt_application_notes(parent, row),
                insert_note_template=lambda row, key: self._insert_application_note_template(
                    parent,
                    row,
                    key,
                ),
                complete_next_action=lambda action: self._complete_application_next_action(parent, action),
                snooze_next_action=lambda action: self._snooze_application_next_action(parent, action),
            ),
        )

    def _set_application_followup_filter(self, parent, followup_filter: str):
        """Set the Applications follow-up filter and rebuild the tab."""
        self._application_followup_filter = followup_filter
        self._build_applications_tab(parent)

    def _format_next_action_due_text(self, action: dict) -> str:
        """Return a compact due-date label for an application next action."""
        return format_next_action_due_text(action)

    def _complete_application_next_action(self, parent, queued_action: dict):
        """Clear a queued next action after the user completes it."""
        try:
            update_application_details(
                str(queued_action.get("title") or ""),
                str(queued_action.get("company") or ""),
                notes=str(queued_action.get("notes") or ""),
                next_action="",
                next_action_date="",
            )
            self._build_applications_tab(parent)
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_followup_update_error_message(e),
                    text_color="red",
                )

    def _snooze_application_next_action(self, parent, queued_action: dict):
        """Move a queued follow-up three days forward."""
        try:
            snoozed_date = (date.today() + timedelta(days=3)).isoformat()
            update_application_details(
                str(queued_action.get("title") or ""),
                str(queued_action.get("company") or ""),
                notes=str(queued_action.get("notes") or ""),
                next_action=str(queued_action.get("next_action") or ""),
                next_action_date=snoozed_date,
            )
            self._build_applications_tab(parent)
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_followup_snooze_error_message(e),
                    text_color="red",
                )

    def _insert_application_note_template(self, parent, application_row, template_key: str):
        """Append a rendered application note template and refresh the Applications tab."""
        try:
            profile = self._load_current_profile_for_guidance() or {}
            application = {
                "title": application_row.title,
                "company": application_row.company,
                "notes": application_row.notes,
            }
            rendered_note = render_application_note_template(
                template_key,
                application=application,
                profile=profile,
            )
            updated_notes = append_application_note(application_row.notes, rendered_note)
            update_application_details(
                application_row.title,
                application_row.company,
                notes=updated_notes,
            )
            self._build_applications_tab(parent)
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_template_insert_error_message(e),
                    text_color="red",
                )

    def _update_application_status_from_menu(self, parent, application_row, selected_label: str):
        """Update an application's status from a GUI menu selection."""
        try:
            status = application_status_from_label(selected_label)
            if status == application_row.status:
                return
            update_application_status(
                application_row.title,
                application_row.company,
                status,
                notes=application_row.notes,
                next_action=application_row.next_action,
                next_action_date=application_row.next_action_date,
            )
            self._build_applications_tab(parent)
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_status_update_error_message(e),
                    text_color="red",
                )

    def _prompt_application_next_action(self, parent, application_row):
        """Prompt for next-action text and persist it to the tracker."""
        dialog = ctk.CTkInputDialog(
            text="Next action",
            title=f"{application_row.title or 'Application'} next action",
        )
        value = normalize_application_detail_input(dialog.get_input())
        if value is None:
            return
        self._update_application_details_from_gui(
            parent,
            application_row,
            next_action=value,
            next_action_date=application_row.next_action_date,
        )

    def _prompt_application_due_date(self, parent, application_row):
        """Prompt for due-date text and persist it to the tracker."""
        dialog = ctk.CTkInputDialog(
            text="Due date (YYYY-MM-DD)",
            title=f"{application_row.title or 'Application'} due date",
        )
        value = normalize_application_detail_input(dialog.get_input())
        if value is None:
            return
        self._update_application_details_from_gui(
            parent,
            application_row,
            next_action=application_row.next_action,
            next_action_date=value,
        )

    def _prompt_application_notes(self, parent, application_row):
        """Prompt for replacement notes and persist them to the tracker."""
        dialog = ctk.CTkInputDialog(
            text="Notes",
            title=f"{application_row.title or 'Application'} notes",
        )
        value = normalize_application_detail_input(dialog.get_input())
        if value is None:
            return
        self._update_application_details_from_gui(
            parent,
            application_row,
            notes=value,
            next_action=application_row.next_action,
            next_action_date=application_row.next_action_date,
        )

    def _update_application_details_from_gui(
        self,
        parent,
        application_row,
        *,
        notes: str | None = None,
        next_action: str | None = None,
        next_action_date: str | None = None,
    ):
        """Persist GUI application detail edits and refresh the grouped view."""
        try:
            update_application_details(
                application_row.title,
                application_row.company,
                notes=notes,
                next_action=next_action,
                next_action_date=next_action_date,
            )
            self._build_applications_tab(parent)
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_detail_update_error_message(e),
                    text_color="red",
                )

    def _export_applications_csv(self):
        """Export tracked application pipeline entries to CSV."""
        try:
            applications = get_all_application_statuses()
            output_path = get_results_dir() / f"applications-{date.today().isoformat()}.csv"
            export_path = export_applications_csv(applications, output_path)
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=applications_csv_export_success_message(export_path),
                    text_color="green",
                )
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=applications_csv_export_error_message(e),
                    text_color="red",
                )

    def _import_report_status_updates(self, parent):
        """Import pending status updates exported from an HTML report."""
        try:
            from tkinter import filedialog

            path = filedialog.askopenfilename(
                title="Import Report Status Updates",
                filetypes=[
                    ("Job Radar status updates", "job-status-updates-*.json"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*"),
                ],
            )
            if not path:
                return

            imported = import_report_status_updates_json(path)
            changed = merge_application_entries(imported)
            self._build_applications_tab(parent)
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_status_import_success_message(changed),
                    text_color="green",
                )
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_status_import_error_message(e),
                    text_color="red",
                )

    def _export_application_followups_ics(self):
        """Export dated application follow-ups to an iCalendar file."""
        try:
            applications = get_all_application_statuses()
            output_path = get_results_dir() / f"application-followups-{date.today().isoformat()}.ics"
            export_path = export_application_followups_ics(applications, output_path)
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_calendar_export_success_message(export_path),
                    text_color="green",
                )
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=application_calendar_export_error_message(e),
                    text_color="red",
                )

    def _on_clear_dismissed_reviews(self):
        """Clear a bounded batch of dismissed review-state entries."""
        try:
            before = review_state_counts().get("dismissed", 0)
            clear_review_state_by_state("dismissed", limit=50)
            after = review_state_counts().get("dismissed", 0)
            removed = max(0, before - after)
            message = dismissed_review_cleanup_success_message(removed)
            color = "green"
        except Exception as e:
            message = dismissed_review_cleanup_error_message(e)
            color = "red"

        if self._cache_status_label:
            self._cache_status_label.configure(text=message, text_color=color)

    def _show_search_idle(self):
        """Display idle state with search controls and Run Search button."""
        # Clear current content
        for widget in self._search_content.winfo_children():
            widget.destroy()

        # Clear worker references
        self._worker = None
        self._worker_thread = None
        self._report_path = None

        # Content frame (centered)
        content_frame = ctk.CTkFrame(self._search_content, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        # Search controls widget
        self._search_controls = SearchControls(
            content_frame,
            source_strategy_lines=self._pre_run_source_strategy_lines(),
        )
        self._search_controls.pack(pady=(0, 20))

        self._add_search_readiness_guidance(content_frame)
        self._add_saved_searches_panel(content_frame)
        self._add_recent_searches_panel(content_frame)

        # Run Search button
        self._search_button = ctk.CTkButton(
            content_frame,
            text="Run Search",
            height=40,
            width=200,
            state="normal" if self._profile_exists else "disabled",
            command=self._start_real_search
        )
        self._search_button.pack(pady=(0, 10))

        preview_btn = ctk.CTkButton(
            content_frame,
            text="Preview Demo Report",
            height=36,
            width=200,
            command=self._open_demo_report,
            fg_color="transparent",
            border_width=2,
        )
        preview_btn.pack(pady=(0, 10))

        # Warning label (only visible when no profile)
        if not self._profile_exists:
            warning_label = ctk.CTkLabel(
                content_frame,
                text="Profile required to run search",
                text_color="red"
            )
            warning_label.pack()

    def _add_search_readiness_guidance(self, parent):
        """Add optional profile quality guidance above the search action."""
        if not self._profile_exists:
            return

        try:
            profile = load_profile(get_data_dir() / "profile.json")
            readiness = assess_profile_readiness(profile)
        except Exception:
            return

        guidance_lines = readiness_guidance_lines(readiness)
        signal_lines = scoring_signal_guidance_lines(
            readiness,
            limit=max(0, 3 - len(guidance_lines)),
        )
        guidance_lines = guidance_lines + signal_lines
        if not guidance_lines:
            return

        add_search_readiness_guidance(
            parent,
            readiness,
            guidance_lines,
            on_review_profile=self._show_profile_tab,
        )

    def _show_profile_tab(self):
        """Navigate to the Profile tab when available."""
        self._show_tab("Profile")

    def _show_tab(self, tab_name: str):
        """Navigate to a tab, building lazy content first when needed."""
        if self._tabview is not None:
            if tab_name not in self._tabs_built:
                if tab_name == "Profile":
                    self._build_profile_tab(self._tabview.tab("Profile"))
                elif tab_name == "Search":
                    self._build_search_tab(self._tabview.tab("Search"))
                elif tab_name == "Applications":
                    self._build_applications_tab(self._tabview.tab("Applications"))
                elif tab_name == "Settings":
                    self._build_settings_tab(self._tabview.tab("Settings"))
                self._tabs_built.add(tab_name)
            self._tabview.set(tab_name)

    def _add_recent_searches_panel(self, parent):
        """Show recent searches with one-click apply controls."""
        rows = load_recent_search_panel_rows()
        add_recent_searches_panel(parent, rows, on_apply=self._apply_recent_search)

    def _apply_recent_search(self, config: dict):
        """Apply a recent search config to the current Search controls."""
        if hasattr(self, "_search_controls") and self._search_controls is not None:
            self._search_controls.set_defaults(config)

    def _add_saved_searches_panel(self, parent):
        """Show named saved searches and a save-current control."""
        rows = load_saved_search_panel_rows()
        self._saved_search_status_label = add_saved_searches_panel(
            parent,
            rows,
            on_apply=self._apply_saved_search,
            on_save_current=self._save_current_search,
        )

    def _apply_saved_search(self, config: dict):
        """Apply a named saved search config to the current Search controls."""
        if hasattr(self, "_search_controls") and self._search_controls is not None:
            self._search_controls.set_defaults(config)

    def _save_current_search(self):
        """Save the current search config using its generated summary label."""
        if not hasattr(self, "_search_controls") or self._search_controls is None:
            return
        is_valid, error_msg = self._search_controls.validate()
        if not is_valid:
            if self._saved_search_status_label is not None:
                self._saved_search_status_label.configure(text=error_msg, text_color="red")
            return

        config = self._search_controls.get_config()
        name = summarize_search_config(config)
        try:
            save_named_search(name, config)
            if self._saved_search_status_label is not None:
                self._saved_search_status_label.configure(
                    text=saved_search_success_message(name),
                    text_color="green",
                )
        except Exception as e:
            if self._saved_search_status_label is not None:
                self._saved_search_status_label.configure(
                    text=saved_search_error_message(e),
                    text_color="red",
                )

    def _open_demo_report(self):
        """Generate and open the no-network demo report from the GUI."""
        try:
            report_result = generate_demo_report(output_dir=str(get_results_dir()))
            self._report_path = report_result["html"]
            browser_result = open_report_in_browser(
                self._report_path,
                auto_open=load_config().get("auto_open_browser", True),
            )
            message = "Demo report generated."
            if not browser_result["opened"]:
                message += f" Open manually: {self._report_path}"
            self._show_demo_report_message(message, "green")
        except Exception as e:
            message = f"Could not generate demo report: {e}"
            if self._has_search_content():
                self._show_search_error(message)
            else:
                self._show_error_dialog(message)

    def _show_demo_report_message(self, message: str, text_color: str = "green"):
        """Show demo-report feedback in the active GUI context."""
        if self._has_search_content():
            self._show_success_message(message)
            return

        if self._welcome_status_label is not None and self._welcome_status_label.winfo_exists():
            self._welcome_status_label.configure(text=message, text_color=text_color)

    def _has_search_content(self) -> bool:
        """Return True when the Search tab content frame is available."""
        return (
            hasattr(self, "_search_content")
            and self._search_content is not None
            and self._search_content.winfo_exists()
        )

    def _show_search_progress(self):
        """Display progress state with progress bar, per-source job counts, and cancel button."""
        # Clear current content
        for widget in self._search_content.winfo_children():
            widget.destroy()

        widgets = build_search_progress_panel(
            self._search_content,
            on_cancel=self._cancel_search,
        )
        self._progress_label = widgets.progress_label
        self._progress_bar = widgets.progress_bar
        self._progress_count = widgets.progress_count
        self._job_count_display = widgets.job_count_display

    def _show_search_complete(self, job_count: int, summary: dict | None = None):
        """Display completion state with Open Report and New Search buttons.

        Parameters
        ----------
        job_count : int
            Total number of jobs found
        summary : dict | None
            Optional per-source completion and warning summary.
        """
        # Clear current content
        for widget in self._search_content.winfo_children():
            widget.destroy()

        warning_message = source_warning_message(summary)
        next_actions = zero_result_lines(job_count, self._load_current_profile_for_guidance())
        next_action_text = bullet_block_text("Try next", next_actions)

        summary_lines = source_summary_lines(summary)
        cache_line = cache_summary_line(summary)
        if cache_line:
            summary_lines.append(cache_line)

        context_lines = search_context_lines(summary, self._active_search_config)
        context_text = bullet_block_text("Run context", context_lines)

        review_lines = self._review_state_summary_lines()
        review_text = review_queue_text(review_lines)

        build_search_completion_panel(
            self._search_content,
            job_count=job_count,
            warning_message=warning_message,
            next_action_text=next_action_text,
            summary_lines=summary_lines,
            context_text=context_text,
            review_text=review_text,
            on_open_report=self._open_report,
            on_new_search=self._show_search_idle,
        )

    def _review_state_summary_lines(self) -> list[str]:
        """Return persisted review-state summary lines for the Search completion screen."""
        try:
            return format_review_state_summary(review_state_counts())
        except Exception:
            return []

    def _load_current_profile_for_guidance(self) -> dict | None:
        """Load the saved profile for non-blocking guidance text."""
        if not self._profile_exists:
            return None
        try:
            return load_profile(get_data_dir() / "profile.json")
        except Exception:
            return None

    def _check_queue(self):
        """Process messages from worker thread queue (runs in main GUI thread)."""
        try:
            # Process all pending messages
            while True:
                try:
                    msg = self._queue.get_nowait()
                    msg_type = msg[0]

                    if msg_type == "source_started":
                        _, source_name, current, total = msg
                        self._on_source_started(source_name, current, total)
                    elif msg_type == "source_complete":
                        _, source_name, current, total, job_count = msg
                        self._on_source_complete(source_name, current, total, job_count)
                    elif msg_type == "search_complete":
                        _, job_count, report_path, *rest = msg
                        summary = rest[0] if rest else None
                        self._on_search_complete(job_count, report_path, summary)
                    elif msg_type == "cancelled":
                        self._on_search_cancelled()
                    elif msg_type == "error":
                        _, error_msg = msg
                        self._show_search_error(error_msg)
                    # Update checker messages
                    elif msg_type == "update_available":
                        _, version, release_url, tag_name = msg
                        # Store tag and version info for later use
                        self._update_tag = tag_name
                        self._update_version = version
                        self._update_release_url = release_url
                        if self._update_checker.should_show_banner(version):
                            self._show_update_banner(version, release_url)
                        else:
                            # Banner not shown but update available - refresh Settings if exists
                            if self._update_status_label:
                                self._refresh_update_status()
                        # If manual check pending, update Settings UI
                        if self._manual_check_pending:
                            # Check if version is skipped for status display
                            if self._update_checker.is_version_skipped(version):
                                self._on_manual_check_result("Update available! (skipped)")
                            else:
                                self._on_manual_check_result("Update available!")
                    elif msg_type == "up_to_date":
                        # If manual check pending, update Settings UI
                        if self._manual_check_pending:
                            self._on_manual_check_result("Up to date!")
                    elif msg_type == "check_failed":
                        _, error = msg
                        # If manual check pending, update Settings UI
                        if self._manual_check_pending:
                            self._on_manual_check_result("Check failed")
                    # Download worker messages
                    elif msg_type == "download_progress":
                        _, downloaded, total = msg
                        if self._update_banner:
                            self._update_banner.update_progress(downloaded, total)
                    elif msg_type == "download_complete":
                        _, dest_path = msg
                        if self._update_banner:
                            self._update_banner.show_complete(dest_path)
                        self._download_worker = None
                        self._download_thread = None
                    elif msg_type == "download_failed":
                        _, error = msg
                        if self._update_banner:
                            self._update_banner.show_failure(error)
                        self._download_worker = None
                        self._download_thread = None
                    elif msg_type == "download_cancelled":
                        if self._update_banner:
                            self._update_banner.destroy()
                            self._update_banner = None
                        self._download_worker = None
                        self._download_thread = None
                    elif msg_type == "asset_ready":
                        _, asset, version = msg
                        # Show confirmation dialog
                        DownloadConfirmDialog(
                            self,
                            version,
                            asset['size'],
                            on_confirm=lambda: self._start_download(asset, version)
                        )
                    elif msg_type == "asset_failed":
                        _, error = msg
                        if self._update_banner:
                            self._update_banner.show_failure(error)
                    elif msg_type == "release_notes_ready":
                        _, version, body = msg
                        self._show_changelog_dialog(version, body)
                    # Backward compatibility with mock worker messages
                    elif msg_type == "progress":
                        _, source, current, total = msg
                        self._update_progress(source, current, total)
                    elif msg_type == "complete":
                        _, total = msg
                        self._update_progress("Complete", total, total)
                        self.after(2000, self._show_search_idle)

                except queue.Empty:
                    break

        finally:
            # Re-schedule next check
            self.after(100, self._check_queue)

    def _start_update_check(self):
        """Start background update check if conditions are met."""
        # Only run if profile exists (already checked by caller)
        if not self._update_checker.should_check():
            return

        # Start daemon thread for update check
        def check_thread():
            self._update_checker.check_for_updates()

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()

    def _show_update_banner(self, version: str, release_url: str):
        """Display update banner at row 1.

        Parameters
        ----------
        version : str
            Version string of available update
        release_url : str
            GitHub Releases URL
        """
        # Check session suppress flag
        if self._download_cancelled_this_session:
            return

        # Store version and release URL for Settings display
        self._update_version = version
        self._update_release_url = release_url

        # Destroy existing banner if any
        if self._update_banner:
            self._update_banner.destroy()
            self._update_banner = None

        # Create banner at row 1
        self._update_banner = UpdateBanner(
            self,
            version=version,
            release_url=release_url,
            on_dismiss=lambda v: self._dismiss_update(v, 24),
            on_remind=lambda v: self._dismiss_update(v, 168),
            on_download=self._on_download_requested,
            on_skip=self._on_skip_version,
            on_view_changelog=self._on_view_changelog
        )
        self._update_banner.grid(row=1, column=0, sticky="ew")

        # Set cancel and install callbacks
        self._update_banner.set_cancel_callback(self._on_download_cancel)
        self._update_banner.set_install_callback(self._on_install_now)

    def _dismiss_update(self, version: str, hours: int):
        """Dismiss update banner for specified duration.

        Parameters
        ----------
        version : str
            Version to suppress
        hours : int
            Duration in hours (24 for X, 168 for Remind Later)
        """
        self._update_checker.dismiss_version(version, hours)

        # Destroy banner
        if self._update_banner:
            self._update_banner.destroy()
            self._update_banner = None

    def _on_skip_version(self, version: str):
        """Handle Skip This Version click from banner dropdown.

        Parameters
        ----------
        version : str
            Version to skip permanently
        """
        # Skip version permanently
        self._update_checker.skip_version(version)

        # Show skip confirmation in banner
        if self._update_banner:
            self._update_banner.show_skip_confirmation()

        # Schedule banner dismiss after 1.5 seconds
        def _dismiss_after_skip():
            if self._update_banner:
                self._update_banner.destroy()
                self._update_banner = None

        self.after(1500, _dismiss_after_skip)

        # Refresh Settings status if label exists
        if self._update_status_label:
            self._refresh_update_status()

    def _on_view_changelog(self, version: str):
        """Handle version number click from banner - show changelog dialog.

        Parameters
        ----------
        version : str
            Version to view release notes for
        """
        # Check cache first
        cached = self._update_checker.get_cached_release_notes(version)

        if cached:
            # Show dialog immediately with cached notes
            self._show_changelog_dialog(version, cached)
        else:
            # Fetch in background thread
            def fetch_thread():
                tag = self._update_tag if self._update_tag else f"v{version}"
                body = self._update_checker.fetch_release_notes(tag)
                self._update_checker.cache_release_notes(version, body)
                self._queue.put(("release_notes_ready", version, body))

            threading.Thread(target=fetch_thread, daemon=True).start()

    def _show_changelog_dialog(self, version: str, body: str):
        """Show ChangelogDialog with extracted summary.

        Parameters
        ----------
        version : str
            Version string
        body : str
            Full release notes markdown body
        """
        summary = extract_summary(body)

        # Use stored release_url if available, otherwise construct
        github_url = self._update_release_url if self._update_release_url else \
            f"https://github.com/BrandedTamarasu-glitch/Job-Radar/releases/tag/v{version}"

        ChangelogDialog(self, version, summary, github_url)

    def _on_download_requested(self, version: str):
        """Handle download request from banner.

        Fetches release assets in background thread, then shows confirmation dialog.

        Parameters
        ----------
        version : str
            Version string to download
        """
        def fetch_asset_thread():
            try:
                # Use stored tag or construct from version
                tag = self._update_tag if self._update_tag else f"v{version}"
                assets = self._update_checker.fetch_release_assets(tag)
                asset = self._update_checker.select_platform_asset(assets)

                if asset is None:
                    self._queue.put(("asset_failed", "No installer found for your platform"))
                else:
                    self._queue.put(("asset_ready", asset, version))
            except Exception as e:
                self._queue.put(("asset_failed", str(e)))

        thread = threading.Thread(target=fetch_asset_thread, daemon=True)
        thread.start()

    def _start_download(self, asset: dict, version: str):
        """Start download worker with asset URL and destination path.

        Parameters
        ----------
        asset : dict
            GitHub asset dictionary with 'browser_download_url', 'size', 'digest'
        version : str
            Version string
        """
        # Get destination path
        dest_path = self._update_checker.get_installer_download_path(version)

        # Transform banner to progress state
        if self._update_banner:
            self._update_banner.show_progress()

        # Create download worker
        worker, thread = create_download_worker(
            self._queue,
            asset['browser_download_url'],
            asset.get('digest'),
            str(dest_path)
        )

        # Store worker and thread
        self._download_worker = worker
        self._download_thread = thread

        # Start download
        thread.start()

    def _on_download_cancel(self):
        """Handle download cancellation from banner."""
        # Cancel worker
        if self._download_worker:
            self._download_worker.cancel()

        # Set session suppress flag
        self._download_cancelled_this_session = True

        # Destroy banner
        if self._update_banner:
            self._update_banner.destroy()
            self._update_banner = None

    def _on_install_now(self, dest_path: str):
        """Handle Install Now / Open Download button click from banner.

        Parameters
        ----------
        dest_path : str
            Path to downloaded installer file
        """
        # Store installer path
        self._installer_path = Path(dest_path)

        # Check if file exists
        if not self._installer_path.exists():
            # Show error dialog with re-download option
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Installer Not Found",
                installer_not_found_message(dest_path),
                parent=self
            )
            if result and self._update_banner:
                # Reset banner to notification state so user can re-download
                self._update_banner.show_notification()
            return

        # Platform-specific handling
        if sys.platform.startswith("linux"):
            # Linux: Show instructions dialog (no confirmation, no app close)
            LinuxInstallInstructionsDialog(
                self,
                self._installer_path,
                self._update_banner.version
            )
            return

        # macOS/Windows: Show confirmation dialog with platform-specific message
        platform_message = install_prompt_message(sys.platform)

        # Show confirmation dialog
        InstallConfirmDialog(
            self,
            self._update_banner.version,
            platform_message,
            on_confirm=self._execute_install
        )

    def _execute_install(self):
        """Execute installer launch after user confirmation."""
        # Determine platform message for status
        platform_message = install_launch_status_message(sys.platform)

        # Update banner to show status
        if self._update_banner:
            self._update_banner.complete_message.configure(text=platform_message)

        # Try to launch installer
        try:
            launch_installer(self._installer_path)
        except RuntimeError as e:
            self._show_install_error(install_launch_error_message(self._installer_path, e))
            return
        except Exception as e:
            self._show_install_error(install_launch_error_message(self._installer_path, e))
            return

        # On success: Update banner message
        if self._update_banner:
            self._update_banner.complete_message.configure(text="Installer launched. Closing app...")

        # Schedule app exit after 1.5 seconds
        self.after(1500, self.destroy)

    def _show_install_error(self, error_msg: str):
        """Show install error dialog and reset banner to complete state.

        Parameters
        ----------
        error_msg : str
            Error message including file path
        """
        from tkinter import messagebox
        messagebox.showerror(
            "Installer Launch Failed",
            error_msg,
            parent=self
        )

        # Reset banner to complete state so user can retry
        if self._update_banner and self._installer_path:
            self._update_banner.show_complete(str(self._installer_path))

    def _on_manual_check_result(self, result_text: str):
        """Handle manual check result from Settings tab.

        Parameters
        ----------
        result_text : str
            Result message to display in button
        """
        if self._manual_check_button is not None:
            # Update button text
            self._manual_check_button.configure(text=result_text, state="normal")

            # Reset button text after 3 seconds
            def reset_button_text():
                if self._manual_check_button is not None:
                    self._manual_check_button.configure(text="Check for Updates")

            self.after(3000, reset_button_text)

        # Update status label if exists
        if self._update_status_label is not None:
            self._refresh_update_status()

        # Reset flag
        self._manual_check_pending = False

    def _refresh_update_status(self):
        """Refresh the update status label in Settings tab."""
        if self._update_status_label is None:
            return

        status_info = self._update_checker.get_update_status()
        display = build_update_status_display(
            current_version=__version__,
            status_info=status_info,
            update_version=self._update_version,
            update_skipped=bool(
                self._update_version
                and self._update_checker.is_version_skipped(self._update_version)
            ),
        )
        self._update_status_label.configure(text=display.text, text_color=display.color)

    def _refresh_update_status_initial(self, parent):
        """Create and populate the initial update status label in Settings tab.

        Parameters
        ----------
        parent
            Parent widget (scroll_frame)
        """
        status_info = self._update_checker.get_update_status()
        display = build_update_status_display(
            current_version=__version__,
            status_info=status_info,
        )
        self._update_status_label = ctk.CTkLabel(
            parent,
            text=display.text,
            text_color=display.color,
            font=ctk.CTkFont(size=12)
        )
        self._update_status_label.pack(pady=(0, 5), anchor="w", padx=10)

    def _on_manual_check_click(self):
        """Handle manual Check for Updates button click in Settings tab."""
        # Disable button and show "Checking..." state
        self._manual_check_button.configure(text="Checking...", state="disabled")
        self._manual_check_pending = True

        # Start background check
        def check_thread():
            self._update_checker.check_for_updates()

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()

    def _on_auto_check_toggle(self):
        """Handle auto-check toggle switch change in Settings tab."""
        enabled = self._auto_check_var.get()
        self._update_checker.set_auto_check(enabled)

    def _refresh_skipped_status(self):
        """Refresh skipped versions status label in Settings tab."""
        if not self._skipped_status_label:
            return

        skipped = self._update_checker.get_skipped_versions()
        if skipped:
            self._skipped_status_label.configure(
                text=f"Skipped: {', '.join('v' + v for v in skipped)}"
            )
        else:
            self._skipped_status_label.configure(text="")

    def _on_settings_view_notes(self):
        """Handle 'View release notes' link click in Settings tab."""
        if self._update_version:
            self._on_view_changelog(self._update_version)

    def _on_clear_skipped(self):
        """Handle 'Clear skipped versions' button click in Settings tab."""
        self._update_checker.clear_skipped_versions()

        # Refresh skipped status label
        self._refresh_skipped_status()

        # Hide clear button
        if self._clear_skipped_btn:
            self._clear_skipped_btn.pack_forget()

        # Refresh update status label
        if self._update_status_label:
            self._refresh_update_status()

    def _on_clear_cache(self):
        """Handle 'Clear HTTP Cache' button click in Settings tab."""
        from job_radar.cache import clear_cache, get_cache_dir

        try:
            removed = clear_cache()
            message = cache_clear_success_message(removed, get_cache_dir())
        except OSError as e:
            message = cache_clear_error_message(e)

        if self._cache_status_label:
            self._cache_status_label.configure(text=message)

    def _on_export_app_data(self):
        """Export portable app data bundle from Settings."""
        try:
            output_path = get_results_dir() / f"job-radar-data-{date.today().isoformat()}.zip"
            export_path = export_app_data_bundle(output_path)
            message = app_data_export_success_message(export_path)
        except OSError as e:
            message = app_data_export_error_message(e)

        if self._cache_status_label:
            self._cache_status_label.configure(text=message)

    def _on_validate_app_data_bundle(self):
        """Prompt for and validate a portable app-data bundle."""
        dialog = ctk.CTkInputDialog(
            text="Path to Job Radar app-data ZIP",
            title="Validate App Data Bundle",
        )
        value = (dialog.get_input() or "").strip()
        if not value:
            return

        result = validate_app_data_bundle(value)
        message = app_data_bundle_validation_message(
            is_valid=result.is_valid,
            files=result.files,
            errors=result.errors,
        )

        if self._cache_status_label:
            self._cache_status_label.configure(text=message)

    def _source_diagnostics_text(self) -> str:
        """Return current source diagnostics text for the Settings tab."""
        history = get_source_health_history(limit=20)
        return "\n".join(format_source_diagnostics_lines(history))

    def _pre_run_source_strategy_lines(self) -> list[str]:
        """Return current source strategy guidance for the Search tab."""
        try:
            history = get_source_health_history(limit=20)
        except Exception:
            return []
        return format_pre_run_source_strategy_lines(history)

    def _local_maintenance_text(self) -> str:
        """Return current local maintenance summary text for Settings."""
        summary = build_local_maintenance_summary(get_data_dir(), get_results_dir())
        return "\n".join(format_local_maintenance_lines(summary))

    def _feedback_diagnostics_text(self) -> str:
        """Return privacy-safe feedback diagnostics text for Settings."""
        summary = build_feedback_diagnostics_summary(get_data_dir(), get_results_dir())
        return "\n".join(format_feedback_diagnostics_lines(summary))

    def _on_copy_feedback_diagnostics(self):
        """Copy privacy-safe feedback diagnostics to the clipboard."""
        text = self._feedback_diagnostics_text()
        self.clipboard_clear()
        self.clipboard_append(text)
        if self._cache_status_label:
            self._cache_status_label.configure(
                text="Copied redacted feedback diagnostics to clipboard"
            )

    def _refresh_source_diagnostics(self):
        """Refresh source diagnostics text in Settings."""
        if not self._source_diagnostics_textbox:
            return
        self._source_diagnostics_textbox.configure(state="normal")
        self._source_diagnostics_textbox.delete("1.0", "end")
        self._source_diagnostics_textbox.insert("end", self._source_diagnostics_text())
        self._source_diagnostics_textbox.configure(state="disabled")

    def _start_real_search(self):
        """Start real search operation with full pipeline execution."""
        # Validate search controls
        is_valid, error_msg = self._search_controls.validate()
        if not is_valid:
            self._show_error_dialog(error_msg)
            return

        # Get search configuration
        search_config = self._search_controls.get_config()
        search_config["hide_rejected_skipped"] = load_config().get("hide_rejected_skipped", False)

        # Load profile
        try:
            profile_path = get_data_dir() / "profile.json"
            profile = load_profile(profile_path)
        except Exception as e:
            self._show_error_dialog(f"Failed to load profile: {e}")
            return

        # Show progress state
        self._record_recent_search(search_config)
        self._active_search_config = search_config.copy()
        self._show_search_progress()

        # Create and start real search worker
        self._worker, self._worker_thread = create_search_worker(
            self._queue,
            profile,
            search_config
        )
        self._worker_thread.start()

    def _record_recent_search(self, search_config: dict):
        """Persist recent search config without blocking search execution."""
        try:
            record_recent_search(search_config)
        except Exception:
            log.debug("Could not record recent search", exc_info=True)

    def _cancel_search(self):
        """Cancel the currently running search operation."""
        if self._worker:
            self._worker.cancel()

    def _on_source_started(self, source_name: str, current: int, total: int):
        """Handle source started message.

        Parameters
        ----------
        source_name : str
            Name of source being fetched
        current : int
            Current source number
        total : int
            Total number of sources
        """
        current, total = normalize_source_progress(current, total)
        self._progress_label.configure(text=source_fetching_message(source_name))
        self._progress_bar.set(current / total)
        self._progress_count.configure(text=source_progress_count_text(current, total))

    def _on_source_complete(self, source_name: str, current: int, total: int, job_count: int):
        """Handle source complete message and display per-source job count.

        Parameters
        ----------
        source_name : str
            Name of completed source
        current : int
            Current source number
        total : int
            Total number of sources
        job_count : int
            Number of jobs found from this source
        """
        # Update progress bar
        current, total = normalize_source_progress(current, total)
        self._progress_bar.set(current / total)
        self._progress_count.configure(text=source_progress_count_text(current, total))

        # Add job count to display
        self._job_count_display.configure(state="normal")
        self._job_count_display.insert("end", source_job_count_line(source_name, job_count))
        self._job_count_display.configure(state="disabled")

    def _update_progress(self, source: str, current: int, total: int):
        """Update progress display (backward compatible with mock worker).

        Parameters
        ----------
        source : str
            Source name
        current : int
            Current source number
        total : int
            Total number of sources
        """
        current, total = normalize_source_progress(current, total)
        self._progress_label.configure(text=source_fetching_message(source))
        self._progress_bar.set(current / total)
        self._progress_count.configure(text=source_progress_count_text(current, total))

    def _on_search_complete(self, job_count: int, report_path: str, summary: dict | None = None):
        """Handle search completion.

        Parameters
        ----------
        job_count : int
            Total number of jobs found
        report_path : str
            Path to generated HTML report
        summary : dict | None
            Optional per-source completion and warning summary.
        """
        self._report_path = report_path
        self._record_search_run_metadata(summary)
        self._show_search_complete(job_count, summary)
        self.update_quota_display()

    def _record_search_run_metadata(self, summary: dict | None):
        """Persist result stats for the active saved/recent search config."""
        if not self._active_search_config:
            return
        try:
            result_stats = (summary or {}).get("result_stats") or {}
            record_search_run(
                self._active_search_config,
                result_stats,
                review_counts=review_state_counts(),
            )
        except Exception:
            log.debug("Could not record search run metadata", exc_info=True)

    def _on_search_cancelled(self):
        """Handle search cancellation."""
        self._worker = None
        self._worker_thread = None
        for widget in self._search_content.winfo_children():
            widget.destroy()

        build_search_cancelled_panel(
            self._search_content,
            on_new_search=self._show_search_idle,
        )

    def _show_search_error(self, message: str):
        """Display a persistent search error state with retry controls."""
        self._worker = None
        self._worker_thread = None
        for widget in self._search_content.winfo_children():
            widget.destroy()

        build_search_error_panel(
            self._search_content,
            message=message,
            on_retry=self._start_real_search,
            on_back_to_search=self._show_search_idle,
        )

    def _open_report(self):
        """Open HTML report in default browser."""
        if self._report_path:
            report_uri = Path(self._report_path).resolve().as_uri()
            webbrowser.open(report_uri)

    def _show_error_dialog(self, message: str):
        """Show modal error dialog.

        Parameters
        ----------
        message : str
            Error message to display
        """
        show_message_dialog(self, title="Error", message=message)

    def _build_settings_tab(self, parent):
        """Build Settings tab with Updates section and API key configuration.

        Parameters
        ----------
        parent
            Parent tab widget
        """
        # Create scrollable frame for settings content
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        status_info = self._update_checker.get_update_status()
        update_status = build_update_status_display(
            current_version=__version__,
            status_info=status_info,
        )
        update_widgets = add_update_settings_panel(
            scroll_frame,
            update_status_text=update_status.text,
            update_status_color=update_status.color,
            auto_check_enabled=status_info.get("auto_check_enabled", True),
            update_available=bool(self._update_version),
            has_skipped_versions=bool(self._update_checker.get_skipped_versions()),
            on_manual_check=self._on_manual_check_click,
            on_auto_check_toggle=self._on_auto_check_toggle,
            on_view_release_notes=self._on_settings_view_notes,
            on_clear_skipped=self._on_clear_skipped,
        )
        self._update_status_label = update_widgets.update_status_label
        self._manual_check_button = update_widgets.manual_check_button
        self._auto_check_var = update_widgets.auto_check_var
        self._release_notes_label = update_widgets.release_notes_label
        self._skipped_status_label = update_widgets.skipped_status_label
        self._clear_skipped_btn = update_widgets.clear_skipped_button

        self._refresh_skipped_status()

        # Separator between Updates and API Key Settings
        separator = ctk.CTkFrame(scroll_frame, height=1, fg_color="gray")
        separator.pack(fill="x", pady=(10, 20), padx=10)

        # Load current env values from the app-data credential file.
        env_path = get_api_credentials_path()
        if env_path.exists():
            load_dotenv(env_path, override=False)

        # Store API field references for saving
        self._api_fields = {}
        self._api_status_labels = {}
        self._quota_labels = {}

        self._quota_labels["jobicy"] = add_api_credentials_panel(
            scroll_frame,
            on_add_api_section=self._add_api_section,
            on_save=self._save_api_keys,
            show_jsearch_tip=not os.getenv("JSEARCH_API_KEY", "").strip(),
        )

        # Separator between API settings and scoring config
        separator = ctk.CTkFrame(scroll_frame, height=2, fg_color="gray70")
        separator.pack(fill="x", pady=(20, 10), padx=10)

        maintenance_widgets = add_storage_maintenance_panel(
            scroll_frame,
            maintenance_text=self._local_maintenance_text(),
            feedback_diagnostics_text=self._feedback_diagnostics_text(),
            source_diagnostics_text=self._source_diagnostics_text(),
            on_clear_cache=self._on_clear_cache,
            on_clear_dismissed_reviews=self._on_clear_dismissed_reviews,
            on_export_app_data=self._on_export_app_data,
            on_validate_app_data_bundle=self._on_validate_app_data_bundle,
            on_copy_feedback_diagnostics=self._on_copy_feedback_diagnostics,
            on_refresh_source_diagnostics=self._refresh_source_diagnostics,
        )
        self._cache_status_label = maintenance_widgets.cache_status_label
        self._source_diagnostics_textbox = maintenance_widgets.source_diagnostics_textbox

        # Separator between storage maintenance and scoring config
        separator = ctk.CTkFrame(scroll_frame, height=2, fg_color="gray70")
        separator.pack(fill="x", pady=(20, 10), padx=10)

        # Load profile for scoring config widget
        try:
            profile_path = get_data_dir() / "profile.json"
            profile = load_profile(profile_path)
        except Exception:
            profile = None

        # Scoring configuration widget
        self._scoring_config = ScoringConfigWidget(
            scroll_frame,
            profile=profile,
            on_save_callback=self._on_scoring_saved
        )
        self._scoring_config.pack(fill="x", padx=10, pady=(10, 20))

        # Separator before Danger Zone
        danger_separator = ctk.CTkFrame(scroll_frame, height=2, fg_color="gray70")
        danger_separator.pack(fill="x", pady=(20, 10), padx=10)

        add_danger_zone(scroll_frame, on_uninstall=self._start_uninstall)

    def _add_api_section(self, parent, title, fields, signup_url):
        """Add an API configuration section with fields and test button.

        Parameters
        ----------
        parent
            Parent widget
        title : str
            Section title
        fields : list of tuple
            List of (env_var_name, label, field_id) tuples
        signup_url : str
            Signup URL for the API
        """
        widgets = add_api_key_section(
            parent,
            title,
            fields,
            signup_url,
            on_test=self._test_api_keys,
        )
        self._api_fields.update(widgets.api_fields)
        self._api_status_labels.update(widgets.status_labels)
        self._quota_labels.update(widgets.quota_labels)

    def _test_api_keys(self, fields):
        """Test API keys by making validation requests.

        Parameters
        ----------
        fields : list of tuple
            List of (env_var_name, label, field_id) tuples
        """
        # Get field values
        field_values = {}
        for env_var, label, field_id in fields:
            entry, _ = self._api_fields[field_id]
            field_values[env_var] = entry.get().strip()

        # Get status label
        status_label = self._api_status_labels[fields[0][2]]

        # Run test in thread to avoid blocking GUI
        def test_thread():
            # Determine which API to test based on fields
            if "JSEARCH_API_KEY" in field_values:
                self._test_jsearch(field_values["JSEARCH_API_KEY"], status_label)
            elif "USAJOBS_API_KEY" in field_values:
                self._test_usajobs(
                    field_values.get("USAJOBS_EMAIL", ""),
                    field_values.get("USAJOBS_API_KEY", ""),
                    status_label
                )
            elif "ADZUNA_APP_ID" in field_values:
                self._test_adzuna(
                    field_values.get("ADZUNA_APP_ID", ""),
                    field_values.get("ADZUNA_APP_KEY", ""),
                    status_label
                )
            elif "AUTHENTIC_JOBS_API_KEY" in field_values:
                self._test_authentic_jobs(field_values["AUTHENTIC_JOBS_API_KEY"], status_label)
            elif "SERPAPI_API_KEY" in field_values:
                self._test_serpapi(field_values["SERPAPI_API_KEY"], status_label)

        self._configure_api_status(status_label, api_testing_status())
        threading.Thread(target=test_thread, daemon=True).start()

    def _configure_api_status(self, status_label, display: ApiStatusDisplay):
        """Apply API credential test status display data to a label."""
        status_label.configure(text=display.text, text_color=display.color)

    def _configure_api_status_async(self, status_label, display: ApiStatusDisplay):
        """Apply API credential test status display data from a worker thread."""
        self.after(0, lambda: self._configure_api_status(status_label, display))

    def _test_jsearch(self, api_key, status_label):
        """Test JSearch API key."""
        if not api_key:
            self._configure_api_status_async(status_label, api_missing_key_status())
            return

        try:
            url = "https://jsearch.p.rapidapi.com/search"
            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            params = {"query": "test", "num_pages": "1"}
            response = requests.get(url, headers=headers, params=params, timeout=10)

            self._configure_api_status_async(status_label, api_response_status(response.status_code))
        except (requests.Timeout, requests.RequestException):
            self._configure_api_status_async(status_label, api_network_error_status())

    def _test_usajobs(self, email, api_key, status_label):
        """Test USAJobs API credentials."""
        if not email or not api_key:
            self._configure_api_status_async(
                status_label,
                api_missing_credentials_status("email and API key"),
            )
            return

        try:
            url = "https://data.usajobs.gov/api/search"
            headers = {
                "Host": "data.usajobs.gov",
                "User-Agent": email,
                "Authorization-Key": api_key
            }
            params = {"Keyword": "test", "ResultsPerPage": "1"}
            response = requests.get(url, headers=headers, params=params, timeout=10)

            self._configure_api_status_async(
                status_label,
                api_response_status(response.status_code, invalid_credentials=True),
            )
        except (requests.Timeout, requests.RequestException):
            self._configure_api_status_async(status_label, api_network_error_status())

    def _test_adzuna(self, app_id, app_key, status_label):
        """Test Adzuna API credentials."""
        if not app_id or not app_key:
            self._configure_api_status_async(
                status_label,
                api_missing_credentials_status("App ID and App Key"),
            )
            return

        try:
            url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": "test",
                "results_per_page": "1"
            }
            response = requests.get(url, params=params, timeout=10)

            self._configure_api_status_async(
                status_label,
                api_response_status(response.status_code, invalid_credentials=True),
            )
        except (requests.Timeout, requests.RequestException):
            self._configure_api_status_async(status_label, api_network_error_status())

    def _test_authentic_jobs(self, api_key, status_label):
        """Test Authentic Jobs API key."""
        if not api_key:
            self._configure_api_status_async(status_label, api_missing_key_status())
            return

        try:
            url = "https://authenticjobs.com/api/"
            params = {
                "api_key": api_key,
                "method": "aj.jobs.search",
                "keywords": "test",
                "perpage": "1",
                "format": "json"
            }
            response = requests.get(url, params=params, timeout=10)

            self._configure_api_status_async(status_label, api_response_status(response.status_code))
        except (requests.Timeout, requests.RequestException):
            self._configure_api_status_async(status_label, api_network_error_status())

    def _test_serpapi(self, api_key, status_label):
        """Test SerpAPI key."""
        if not api_key:
            self._configure_api_status_async(status_label, api_missing_key_status())
            return

        try:
            url = f"https://serpapi.com/search?engine=google_jobs&q=test&api_key={api_key}"
            response = requests.get(url, timeout=10)

            self._configure_api_status_async(
                status_label,
                api_response_status(response.status_code, fallback="http"),
            )

        except requests.Timeout:
            self._configure_api_status_async(status_label, api_timeout_status())
        except requests.RequestException as e:
            self._configure_api_status_async(status_label, api_error_status(e))

    def _save_api_keys(self):
        """Save API keys to the app-data credential file atomically."""
        # Collect all field values
        env_vars = {}
        for field_id, (entry, env_var) in self._api_fields.items():
            value = entry.get().strip()
            if value:  # Only save non-empty values
                env_vars[env_var] = value

        try:
            existing_vars = read_api_credentials_file()
        except ApiCredentialError as e:
            self._show_error_dialog(f"Failed to read existing API keys: {e}")
            return

        # Merge with new values
        existing_vars.update(env_vars)

        try:
            save_api_credentials(existing_vars)
            self._show_info_dialog("API keys saved successfully!")
        except ApiCredentialError as e:
            self._show_error_dialog(f"Failed to save API keys: {e}")

    def update_quota_display(self):
        """Update quota usage displays for all configured APIs.

        Called after each search completes. Queries SQLite buckets directly
        for current window usage. Shows warning color (orange) when >80% used.
        """
        if not hasattr(self, '_quota_labels'):
            return

        for backend_api, label in self._quota_labels.items():
            try:
                quota_info = get_quota_usage(backend_api)
                if quota_info:
                    used, limit, period = quota_info
                    percentage = (used / limit) * 100 if limit > 0 else 0

                    # Color based on usage
                    if percentage >= 100:
                        color = "red"
                    elif percentage >= 80:
                        color = "orange"
                    else:
                        color = "gray"

                    self.after(0, lambda l=label, t=f"{used}/{limit} this {period}", c=color: (
                        l.configure(text=t, text_color=c)
                    ))
                else:
                    self.after(0, lambda l=label: l.configure(text=""))
            except Exception:
                pass  # Quota display is best-effort

    def _on_scoring_saved(self):
        """Handle scoring configuration save success."""
        # No tab navigation needed -- user stays on Settings tab
        pass

    def _start_uninstall(self):
        """Orchestrate the full uninstall flow.

        Steps:
        1. Offer backup
        2. Preview paths to be deleted
        3. Final confirmation with checkbox
        4. Delete data in background thread
        5. Handle results (failures, binary cleanup)
        6. Quit app
        """
        # Step 1: Offer backup
        backup_dialog = BackupOfferDialog(self)
        backup_dialog.wait_window()

        if backup_dialog.result == "cancel":
            return

        # Step 2: Preview paths to be deleted
        try:
            paths = get_uninstall_paths()
        except Exception as e:
            self._show_error_dialog(f"Failed to enumerate paths: {e}")
            return

        if not paths:
            self._show_error_dialog("No application data found to uninstall.")
            return

        preview_dialog = PathPreviewDialog(self, paths)
        preview_dialog.wait_window()

        if not preview_dialog.result:
            return

        # Step 3: Final confirmation
        confirmation_dialog = FinalConfirmationDialog(self)
        confirmation_dialog.wait_window()

        if not confirmation_dialog.result:
            return

        # Step 4: Show progress dialog and delete in background thread
        progress_dialog = DeletionProgressDialog(self)

        # Container for thread result
        result_container = {"failures": None, "done": False}

        def delete_thread():
            """Background deletion thread."""
            failures = delete_app_data()
            result_container["failures"] = failures
            result_container["done"] = True

        # Start deletion thread
        thread = threading.Thread(target=delete_thread, daemon=True)
        thread.start()

        # Poll for completion
        def check_completion():
            if result_container["done"]:
                progress_dialog.close()
                self._handle_uninstall_results(result_container["failures"])
            else:
                self.after(100, check_completion)

        self.after(100, check_completion)

    def _handle_uninstall_results(self, failures: list[tuple[str, str]]):
        """Handle uninstall results and quit app.

        Parameters
        ----------
        failures : list[tuple[str, str]]
            List of (path, error_message) tuples for failed deletions
        """
        # Step 5: Handle results
        if failures:
            # Partial failure - show what failed
            failure_msg = "Some files could not be deleted:\n\n"
            for path, error in failures[:5]:  # Show first 5
                failure_msg += f"• {path}\n  Error: {error}\n"
            if len(failures) > 5:
                failure_msg += f"\n...and {len(failures) - 5} more"

            self._show_error_dialog(failure_msg)

        # Check if binary cleanup needed
        binary_path = get_binary_path()
        if binary_path:
            try:
                message, script_path = create_cleanup_script(binary_path)
                final_msg = message
            except Exception as e:
                final_msg = f"Data removed. Please manually delete: {binary_path}"
        else:
            final_msg = "Data removed successfully."

        # Step 6: Show final success dialog and quit
        success_dialog = ctk.CTkToplevel(self)
        success_dialog.title("Uninstall Complete")
        success_dialog.geometry("400x200")
        success_dialog.transient(self)
        success_dialog.grab_set()

        # Center on parent
        success_dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - success_dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - success_dialog.winfo_height()) // 2
        success_dialog.geometry(f"+{x}+{y}")

        # Message
        msg_label = ctk.CTkLabel(
            success_dialog,
            text=f"{final_msg}\n\nGoodbye!",
            wraplength=350,
            font=ctk.CTkFont(size=13),
            text_color="green"
        )
        msg_label.pack(pady=30, padx=20)

        # OK button that quits
        ok_btn = ctk.CTkButton(
            success_dialog,
            text="OK",
            width=100,
            command=lambda: (success_dialog.destroy(), self.quit())
        )
        ok_btn.pack(pady=(0, 20))

    def _show_info_dialog(self, message: str):
        """Show modal info dialog.

        Parameters
        ----------
        message : str
            Info message to display
        """
        show_message_dialog(
            self,
            title="Success",
            message=message,
            geometry="400x150",
            text_color="green",
        )


def launch_gui():
    """Create and run the main GUI window."""
    app = MainWindow()
    app.mainloop()
