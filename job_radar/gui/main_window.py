"""Main GUI window for Job Radar desktop application.

Integrates ProfileForm (create/edit), SearchControls (date/score/new-only),
and SearchWorker (full search pipeline) into a tabbed interface. Manages
navigation, progress display, and report opening.
"""

import os
import queue
import sys
import tempfile
import threading
import webbrowser
from datetime import date
from pathlib import Path

import customtkinter as ctk
import requests

from job_radar import __version__
from job_radar.applications_export import export_applications_csv
from job_radar.browser import open_report_in_browser
from job_radar.demo_report import generate_demo_report
from job_radar.paths import get_data_dir
from job_radar.paths import get_results_dir
from job_radar.profile_readiness import assess_profile_readiness, readiness_guidance_lines
from job_radar.profile_manager import load_profile
from job_radar.config import load_config
from job_radar.tracker import get_all_application_statuses, get_source_health_history
from job_radar.update_checker import UpdateChecker, launch_installer, cleanup_old_installers, extract_summary
from job_radar.gui.applications_view_model import build_applications_view_model
from job_radar.gui.profile_form import ProfileForm
from job_radar.gui.search_controls import SearchControls
from job_radar.gui.search_summary import (
    cancellation_message,
    cache_summary_line,
    completion_message,
    error_message,
    source_summary_lines,
    source_warning_message,
    zero_result_lines,
)
from job_radar.gui.source_diagnostics_view_model import format_source_diagnostics_lines
from job_radar.gui.worker_thread import create_search_worker, create_download_worker
from job_radar.gui.scoring_config import ScoringConfigWidget
from job_radar.gui.update_banner import UpdateBanner, DownloadConfirmDialog
from job_radar.gui.changelog_dialog import ChangelogDialog
from job_radar.gui.installer_dialogs import InstallConfirmDialog, LinuxInstallInstructionsDialog
from job_radar.gui.uninstall_dialog import (
    BackupOfferDialog,
    PathPreviewDialog,
    FinalConfirmationDialog,
    DeletionProgressDialog,
)
from job_radar.rate_limits import get_quota_usage
from job_radar.saved_searches import record_recent_search
from job_radar.uninstaller import (
    get_uninstall_paths,
    create_backup,
    delete_app_data,
    get_binary_path,
    create_cleanup_script,
)
from dotenv import find_dotenv, load_dotenv


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

        # Content frame (centered using place - avoids grid overlay issues)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.place(in_=self, relx=0.5, rely=0.5, anchor="center")

        # Title
        title = ctk.CTkLabel(
            content_frame,
            text="Welcome to Job Radar",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))

        # Description paragraphs
        desc1 = ctk.CTkLabel(
            content_frame,
            text="Job Radar searches multiple job boards, scores each listing against your profile, "
                 "and generates a ranked report — so you focus on the best matches.",
            wraplength=500,
            justify="left"
        )
        desc1.pack(pady=(0, 15))

        desc2 = ctk.CTkLabel(
            content_frame,
            text="Set up your profile to get started. You'll enter your skills, target titles, and preferences.",
            wraplength=500,
            justify="left"
        )
        desc2.pack(pady=(0, 30))

        # Get Started button
        get_started_btn = ctk.CTkButton(
            content_frame,
            text="Get Started",
            height=40,
            width=200,
            command=self._on_get_started
        )
        get_started_btn.pack()

        preview_btn = ctk.CTkButton(
            content_frame,
            text="Preview Demo Report",
            height=36,
            width=200,
            command=self._open_demo_report,
            fg_color="transparent",
            border_width=2,
        )
        preview_btn.pack(pady=(12, 0))

        self._welcome_status_label = ctk.CTkLabel(
            content_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=500,
            justify="center",
        )
        self._welcome_status_label.pack(pady=(14, 0))

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

            readiness_text = (
                f"{readiness.status} ({readiness.score}/{readiness.max_score})"
            )
            self._add_profile_field(scroll_frame, row, "Profile Readiness:", readiness_text)
            row += 1

            readiness_items = list(readiness.missing_required or readiness.recommendations[:3])
            if readiness_items:
                readiness_label = ctk.CTkLabel(
                    scroll_frame,
                    text="\n".join(f"- {item}" for item in readiness_items),
                    text_color="gray",
                    wraplength=680,
                    justify="left",
                    anchor="w",
                )
                readiness_label.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
                row += 1

            # Name
            self._add_profile_field(scroll_frame, row, "Name:", profile.get("name", "N/A"))
            row += 1

            # Target Titles
            titles = ", ".join(profile.get("target_titles", []))
            self._add_profile_field(scroll_frame, row, "Target Titles:", titles or "N/A")
            row += 1

            # Core Skills
            core_skills = ", ".join(profile.get("core_skills", []))
            self._add_profile_field(scroll_frame, row, "Core Skills:", core_skills or "N/A")
            row += 1

            # Secondary Skills (if present)
            if "secondary_skills" in profile and profile["secondary_skills"]:
                secondary_skills = ", ".join(profile["secondary_skills"])
                self._add_profile_field(scroll_frame, row, "Secondary Skills:", secondary_skills)
                row += 1

            # Level / Years Experience
            level = profile.get("level", "N/A")
            years = profile.get("years_experience", "N/A")
            self._add_profile_field(scroll_frame, row, "Level / Experience:", f"{level} / {years} years")
            row += 1

            # Location / Arrangement
            location = profile.get("location", "N/A")
            arrangement = ", ".join(profile.get("arrangement", [])) if profile.get("arrangement") else "N/A"
            self._add_profile_field(scroll_frame, row, "Location / Arrangement:", f"{location} / {arrangement}")
            row += 1

            # Dealbreakers (if present)
            if "dealbreakers" in profile and profile["dealbreakers"]:
                dealbreakers = ", ".join(profile["dealbreakers"])
                self._add_profile_field(scroll_frame, row, "Dealbreakers:", dealbreakers)
                row += 1

            # Compensation Floor (if present)
            if "comp_floor" in profile and profile["comp_floor"]:
                comp_formatted = f"${profile['comp_floor']:,}"
                self._add_profile_field(scroll_frame, row, "Compensation Floor:", comp_formatted)
                row += 1

            # Edit Profile button at bottom
            edit_btn = ctk.CTkButton(
                scroll_frame,
                text="Edit Profile",
                height=40,
                width=150,
                command=lambda: self._on_edit_profile(profile)
            )
            edit_btn.grid(row=row, column=0, columnspan=2, pady=(20, 0))

        except Exception as e:
            # Error loading profile
            error_label = ctk.CTkLabel(
                scroll_frame,
                text=f"Could not load profile: {e}",
                text_color="red"
            )
            error_label.pack(pady=20)

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
        # Label (bold, left-aligned)
        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)

        # Value (left-aligned, wrapping)
        value = ctk.CTkLabel(
            parent,
            text=value_text,
            anchor="w"
        )
        value.grid(row=row, column=1, sticky="w", pady=5)

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
        for widget in parent.winfo_children():
            widget.destroy()

        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame,
            text="Applications",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            actions_frame,
            text="Export CSV",
            width=120,
            command=self._export_applications_csv,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions_frame,
            text="Refresh",
            width=100,
            command=lambda: self._build_applications_tab(parent),
        ).pack(side="left")

        self._applications_export_status_label = ctk.CTkLabel(
            scroll_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._applications_export_status_label.grid(row=1, column=0, sticky="w", pady=(0, 8))

        applications = get_all_application_statuses()
        groups = build_applications_view_model(applications)
        total_rows = sum(group.count for group in groups)

        if total_rows == 0:
            ctk.CTkLabel(
                scroll_frame,
                text="No application pipeline entries yet.",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).grid(row=2, column=0, sticky="w", pady=20)
            return

        row_index = 2
        for group in groups:
            group_frame = ctk.CTkFrame(scroll_frame)
            group_frame.grid(row=row_index, column=0, sticky="ew", pady=(0, 10))
            group_frame.grid_columnconfigure(0, weight=1)
            row_index += 1

            ctk.CTkLabel(
                group_frame,
                text=f"{group.label} ({group.count})",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

            if group.count == 0:
                ctk.CTkLabel(
                    group_frame,
                    text="No jobs in this status.",
                    text_color="gray",
                ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
                continue

            for item_index, item in enumerate(group.rows, start=1):
                details = []
                if item.next_action:
                    next_action = item.next_action
                    if item.next_action_date:
                        next_action = f"{next_action} ({item.next_action_date})"
                    details.append(f"Next: {next_action}")
                if item.notes:
                    details.append(f"Notes: {item.notes}")
                if item.updated:
                    details.append(f"Updated: {item.updated[:10]}")

                ctk.CTkLabel(
                    group_frame,
                    text=f"{item.title or 'Untitled'} — {item.company or 'Unknown company'}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    anchor="w",
                ).grid(row=item_index * 2 - 1, column=0, sticky="ew", padx=16, pady=(4, 0))

                ctk.CTkLabel(
                    group_frame,
                    text=" | ".join(details) if details else "No follow-up details.",
                    text_color="gray",
                    wraplength=760,
                    anchor="w",
                    justify="left",
                ).grid(row=item_index * 2, column=0, sticky="ew", padx=16, pady=(0, 6))

    def _export_applications_csv(self):
        """Export tracked application pipeline entries to CSV."""
        try:
            applications = get_all_application_statuses()
            output_path = get_results_dir() / f"applications-{date.today().isoformat()}.csv"
            export_path = export_applications_csv(applications, output_path)
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=f"Exported to {export_path}",
                    text_color="green",
                )
        except Exception as e:
            if self._applications_export_status_label is not None:
                self._applications_export_status_label.configure(
                    text=f"Export failed: {e}",
                    text_color="red",
                )

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
        self._search_controls = SearchControls(content_frame)
        self._search_controls.pack(pady=(0, 20))

        self._add_search_readiness_guidance(content_frame)

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
        if not guidance_lines:
            return

        guidance_frame = ctk.CTkFrame(parent)
        guidance_frame.pack(fill="x", pady=(0, 16))
        guidance_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            guidance_frame,
            text=f"Profile readiness: {readiness.status} ({readiness.score}/{readiness.max_score})",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            guidance_frame,
            text="\n".join(f"- {line}" for line in guidance_lines),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=520,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

        ctk.CTkButton(
            guidance_frame,
            text="Review Profile",
            width=130,
            command=self._show_profile_tab,
            fg_color="transparent",
            border_width=2,
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=12, pady=10)

    def _show_profile_tab(self):
        """Navigate to the Profile tab when available."""
        if self._tabview is not None:
            self._tabview.set("Profile")

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

        # Content frame (centered)
        content_frame = ctk.CTkFrame(self._search_content, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        # Progress label
        self._progress_label = ctk.CTkLabel(
            content_frame,
            text="Starting search...",
            font=ctk.CTkFont(size=14)
        )
        self._progress_label.pack(pady=(0, 15))

        # Progress bar
        self._progress_bar = ctk.CTkProgressBar(
            content_frame,
            width=400
        )
        self._progress_bar.set(0)
        self._progress_bar.pack(pady=(0, 10))

        # Progress count
        self._progress_count = ctk.CTkLabel(
            content_frame,
            text="Source 0 of 0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self._progress_count.pack(pady=(0, 15))

        # Per-source job count display (scrollable textbox)
        self._job_count_display = ctk.CTkTextbox(
            content_frame,
            width=400,
            height=100,
            state="disabled"
        )
        self._job_count_display.pack(pady=(0, 20))

        # Cancel button
        cancel_btn = ctk.CTkButton(
            content_frame,
            text="Cancel",
            height=35,
            width=150,
            command=self._cancel_search,
            fg_color="red",
            hover_color="darkred"
        )
        cancel_btn.pack()

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

        # Content frame (centered)
        content_frame = ctk.CTkFrame(self._search_content, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        # Completion message
        completion_label = ctk.CTkLabel(
            content_frame,
            text=completion_message(job_count),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="green" if job_count else "orange"
        )
        completion_label.pack(pady=(0, 15))

        warning_message = source_warning_message(summary)
        if warning_message:
            warning_label = ctk.CTkLabel(
                content_frame,
                text=warning_message,
                font=ctk.CTkFont(size=12),
                text_color="orange",
                wraplength=420,
                justify="center"
            )
            warning_label.pack(pady=(0, 12))

        next_actions = zero_result_lines(job_count, self._load_current_profile_for_guidance())
        if next_actions:
            next_action_text = "Try next:\n" + "\n".join(f"- {line}" for line in next_actions)
            next_action_label = ctk.CTkLabel(
                content_frame,
                text=next_action_text,
                font=ctk.CTkFont(size=12),
                text_color="gray",
                wraplength=420,
                justify="left"
            )
            next_action_label.pack(pady=(0, 16))

        summary_lines = source_summary_lines(summary)
        cache_line = cache_summary_line(summary)
        if cache_line:
            summary_lines.append(cache_line)
        if summary_lines:
            summary_box = ctk.CTkTextbox(
                content_frame,
                width=420,
                height=min(180, max(80, len(summary_lines) * 24)),
                state="normal"
            )
            summary_box.insert("end", "\n".join(summary_lines))
            summary_box.configure(state="disabled")
            summary_box.pack(pady=(0, 20))

        # Open Report button
        open_report_btn = ctk.CTkButton(
            content_frame,
            text="Open Report",
            height=40,
            width=200,
            command=self._open_report
        )
        open_report_btn.pack(pady=(0, 15))

        # New Search button
        new_search_btn = ctk.CTkButton(
            content_frame,
            text="New Search",
            height=40,
            width=200,
            command=self._show_search_idle,
            fg_color="transparent",
            border_width=2
        )
        new_search_btn.pack()

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
                f"Installer file not found. Download again?\n\n{dest_path}",
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
        if sys.platform == "darwin":
            platform_message = "Opening installer DMG..."
        elif sys.platform == "win32":
            platform_message = "Launching installer... Windows may show a security prompt."
        else:
            platform_message = "Launching installer..."

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
        if sys.platform == "darwin":
            platform_message = "Opening installer DMG..."
        elif sys.platform == "win32":
            platform_message = "Launching installer..."
        else:
            platform_message = "Launching installer..."

        # Update banner to show status
        if self._update_banner:
            self._update_banner.complete_message.configure(text=platform_message)

        # Try to launch installer
        try:
            launch_installer(self._installer_path)
        except RuntimeError as e:
            error_msg = f"Couldn't launch installer. File saved at: {self._installer_path}\n\n{e}"
            self._show_install_error(error_msg)
            return
        except Exception as e:
            error_msg = f"Couldn't launch installer. File saved at: {self._installer_path}\n\n{e}"
            self._show_install_error(error_msg)
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
        last_check = status_info.get("last_check")
        check_success = status_info.get("check_success")

        # Format relative time
        if last_check:
            try:
                from datetime import datetime, timezone
                last_check_dt = datetime.fromisoformat(last_check)
                now = datetime.now(timezone.utc)
                elapsed = now - last_check_dt

                if elapsed.total_seconds() < 300:  # < 5 minutes
                    relative_time = "Just now"
                elif elapsed.total_seconds() < 3600:  # < 1 hour
                    minutes = int(elapsed.total_seconds() / 60)
                    relative_time = f"{minutes}m ago"
                elif elapsed.total_seconds() < 86400:  # < 1 day
                    hours = int(elapsed.total_seconds() / 3600)
                    relative_time = f"{hours}h ago"
                else:
                    days = int(elapsed.total_seconds() / 86400)
                    relative_time = f"{days}d ago"
            except Exception:
                relative_time = "Unknown"
        else:
            relative_time = "Never"

        # Determine status
        if relative_time == "Never":
            status = "Never checked"
            status_color = "gray"
        elif check_success:
            status = "Up to date"
            status_color = "green"
        elif check_success is False:
            status = "Check failed"
            status_color = "orange"
        else:
            status = "Unknown"
            status_color = "gray"

        # Check for skipped version or available update
        if self._update_version and self._update_checker.is_version_skipped(self._update_version):
            status = f"v{self._update_version} available (skipped)"
            status_color = "gray"
        elif self._update_version:
            status = f"v{self._update_version} available"
            status_color = "orange"

        # Update label
        status_text = f"v{__version__} -- Last checked: {relative_time} -- {status}"
        self._update_status_label.configure(text=status_text, text_color=status_color)

    def _refresh_update_status_initial(self, parent):
        """Create and populate the initial update status label in Settings tab.

        Parameters
        ----------
        parent
            Parent widget (scroll_frame)
        """
        status_info = self._update_checker.get_update_status()
        last_check = status_info.get("last_check")
        check_success = status_info.get("check_success")

        # Format relative time
        if last_check:
            try:
                from datetime import datetime, timezone
                last_check_dt = datetime.fromisoformat(last_check)
                now = datetime.now(timezone.utc)
                elapsed = now - last_check_dt

                if elapsed.total_seconds() < 300:  # < 5 minutes
                    relative_time = "Just now"
                elif elapsed.total_seconds() < 3600:  # < 1 hour
                    minutes = int(elapsed.total_seconds() / 60)
                    relative_time = f"{minutes}m ago"
                elif elapsed.total_seconds() < 86400:  # < 1 day
                    hours = int(elapsed.total_seconds() / 3600)
                    relative_time = f"{hours}h ago"
                else:
                    days = int(elapsed.total_seconds() / 86400)
                    relative_time = f"{days}d ago"
            except Exception:
                relative_time = "Unknown"
        else:
            relative_time = "Never"

        # Determine status
        if relative_time == "Never":
            status = "Never checked"
            status_color = "gray"
        elif check_success:
            status = "Up to date"
            status_color = "green"
        elif check_success is False:
            status = "Check failed"
            status_color = "orange"
        else:
            status = "Unknown"
            status_color = "gray"

        # Create status label
        status_text = f"v{__version__} -- Last checked: {relative_time} -- {status}"
        self._update_status_label = ctk.CTkLabel(
            parent,
            text=status_text,
            text_color=status_color,
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
            message = f"Removed {removed} cached response file(s) from {get_cache_dir()}"
        except OSError as e:
            message = f"Failed to clear cache: {e}"

        if self._cache_status_label:
            self._cache_status_label.configure(text=message)

    def _source_diagnostics_text(self) -> str:
        """Return current source diagnostics text for the Settings tab."""
        history = get_source_health_history(limit=20)
        return "\n".join(format_source_diagnostics_lines(history))

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
        self._progress_label.configure(text=f"Fetching {source_name}...")
        self._progress_bar.set(current / total)
        self._progress_count.configure(text=f"Source {current} of {total}")

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
        self._progress_bar.set(current / total)
        self._progress_count.configure(text=f"Source {current} of {total}")

        # Add job count to display
        self._job_count_display.configure(state="normal")
        self._job_count_display.insert("end", f"{source_name}: {job_count} jobs found\n")
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
        self._progress_label.configure(text=f"Fetching {source}...")
        self._progress_bar.set(current / total)
        self._progress_count.configure(text=f"Source {current} of {total}")

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
        self._show_search_complete(job_count, summary)
        self.update_quota_display()

    def _on_search_cancelled(self):
        """Handle search cancellation."""
        self._worker = None
        self._worker_thread = None
        for widget in self._search_content.winfo_children():
            widget.destroy()

        content_frame = ctk.CTkFrame(self._search_content, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        cancel_label = ctk.CTkLabel(
            content_frame,
            text="Search cancelled",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="orange"
        )
        cancel_label.pack(pady=(0, 12))

        detail_label = ctk.CTkLabel(
            content_frame,
            text=cancellation_message(),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=420,
            justify="center"
        )
        detail_label.pack(pady=(0, 20))

        new_search_btn = ctk.CTkButton(
            content_frame,
            text="New Search",
            height=40,
            width=200,
            command=self._show_search_idle,
            fg_color="transparent",
            border_width=2
        )
        new_search_btn.pack()

    def _show_search_error(self, message: str):
        """Display a persistent search error state with retry controls."""
        self._worker = None
        self._worker_thread = None
        for widget in self._search_content.winfo_children():
            widget.destroy()

        content_frame = ctk.CTkFrame(self._search_content, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        error_label = ctk.CTkLabel(
            content_frame,
            text="Search failed",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="red"
        )
        error_label.pack(pady=(0, 12))

        detail_label = ctk.CTkLabel(
            content_frame,
            text=error_message(message),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=420,
            justify="center"
        )
        detail_label.pack(pady=(0, 20))

        retry_btn = ctk.CTkButton(
            content_frame,
            text="Try Again",
            height=40,
            width=200,
            command=self._start_real_search
        )
        retry_btn.pack(pady=(0, 15))

        new_search_btn = ctk.CTkButton(
            content_frame,
            text="Back to Search",
            height=40,
            width=200,
            command=self._show_search_idle,
            fg_color="transparent",
            border_width=2
        )
        new_search_btn.pack()

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
        # Create modal dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("400x200")

        # Make modal
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Error message
        error_label = ctk.CTkLabel(
            dialog,
            text=message,
            wraplength=350,
            font=ctk.CTkFont(size=13)
        )
        error_label.pack(pady=30, padx=20)

        # OK button
        ok_btn = ctk.CTkButton(
            dialog,
            text="OK",
            width=100,
            command=dialog.destroy
        )
        ok_btn.pack(pady=(0, 20))

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

        # === Updates Section ===
        updates_title = ctk.CTkLabel(
            scroll_frame,
            text="Updates",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        updates_title.pack(pady=(0, 10), anchor="w", padx=10)

        # Status info line
        self._refresh_update_status_initial(scroll_frame)

        # Check for Updates button
        self._manual_check_button = ctk.CTkButton(
            scroll_frame,
            text="Check for Updates",
            width=150,
            command=self._on_manual_check_click
        )
        self._manual_check_button.pack(pady=(10, 10), anchor="w", padx=10)

        # Auto-check toggle
        status_info = self._update_checker.get_update_status()
        auto_check_enabled = status_info.get("auto_check_enabled", True)

        self._auto_check_var = ctk.BooleanVar(value=auto_check_enabled)

        auto_check_switch = ctk.CTkSwitch(
            scroll_frame,
            text="Check for updates automatically on launch",
            variable=self._auto_check_var,
            command=self._on_auto_check_toggle
        )
        auto_check_switch.pack(pady=(0, 10), anchor="w", padx=10)

        # "View release notes" link (only when update available)
        self._release_notes_label = ctk.CTkButton(
            scroll_frame,
            text="View release notes",
            fg_color="transparent",
            text_color=("#3498DB", "#5DADE2"),
            hover_color=("gray90", "gray20"),
            font=ctk.CTkFont(size=12, underline=True),
            anchor="w",
            width=150,
            height=25,
            cursor="hand2",
            command=self._on_settings_view_notes
        )
        # Only pack if update available
        if self._update_version:
            self._release_notes_label.pack(anchor="w", padx=10)

        # Skipped versions status label
        self._skipped_status_label = ctk.CTkLabel(
            scroll_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self._skipped_status_label.pack(anchor="w", padx=10)
        self._refresh_skipped_status()

        # "Clear skipped versions" button
        self._clear_skipped_btn = ctk.CTkButton(
            scroll_frame,
            text="Clear skipped versions",
            width=180,
            fg_color="transparent",
            border_width=1,
            command=self._on_clear_skipped
        )
        # Only pack if there are skipped versions
        if self._update_checker.get_skipped_versions():
            self._clear_skipped_btn.pack(anchor="w", padx=10, pady=(5, 10))

        # Separator between Updates and API Key Settings
        separator = ctk.CTkFrame(scroll_frame, height=1, fg_color="gray")
        separator.pack(fill="x", pady=(10, 20), padx=10)

        # === API Key Settings Section ===
        # Title
        title_label = ctk.CTkLabel(
            scroll_frame,
            text="API Key Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = ctk.CTkLabel(
            scroll_frame,
            text="Configure API keys to enable additional job sources",
            wraplength=600
        )
        desc_label.pack(pady=(0, 20))

        # Load current env values from CWD .env (don't search filesystem)
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)

        # Store API field references for saving
        self._api_fields = {}
        self._api_status_labels = {}
        self._quota_labels = {}

        # JSearch section
        self._add_api_section(
            scroll_frame,
            "JSearch API (LinkedIn, Indeed, Glassdoor)",
            [("JSEARCH_API_KEY", "JSearch API Key", "jsearch")],
            "Get your key from RapidAPI: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch"
        )

        # USAJobs section
        self._add_api_section(
            scroll_frame,
            "USAJobs (Federal Government Jobs)",
            [
                ("USAJOBS_EMAIL", "Email (User-Agent)", "usajobs_email"),
                ("USAJOBS_API_KEY", "API Key", "usajobs")
            ],
            "Register at: https://developer.usajobs.gov/"
        )

        # Adzuna section
        self._add_api_section(
            scroll_frame,
            "Adzuna API",
            [
                ("ADZUNA_APP_ID", "App ID", "adzuna_id"),
                ("ADZUNA_APP_KEY", "App Key", "adzuna_key")
            ],
            "Sign up at: https://developer.adzuna.com/"
        )

        # Authentic Jobs section
        self._add_api_section(
            scroll_frame,
            "Authentic Jobs",
            [("AUTHENTIC_JOBS_API_KEY", "API Key", "authentic_jobs")],
            "Get your key from: https://authenticjobs.com/api/"
        )

        # SerpAPI section
        self._add_api_section(
            scroll_frame,
            "SerpAPI (Google Jobs)",
            [("SERPAPI_API_KEY", "API Key", "serpapi")],
            "Sign up at: https://serpapi.com/ (100 searches/month free)"
        )

        # Jobicy section (no API key, just info and enable status)
        jobicy_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        jobicy_frame.pack(fill="x", pady=(10, 20), padx=10)

        jobicy_title = ctk.CTkLabel(
            jobicy_frame,
            text="Jobicy (Remote Jobs)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        jobicy_title.pack(anchor="w", pady=(0, 5))

        jobicy_info = ctk.CTkLabel(
            jobicy_frame,
            text="Public API - no key required (rate limited to 1 request/hour)",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        jobicy_info.pack(anchor="w", pady=(0, 5))

        jobicy_status = ctk.CTkLabel(
            jobicy_frame,
            text="✓ Always available",
            text_color="green"
        )
        jobicy_status.pack(anchor="w")

        # Jobicy quota label
        jobicy_quota = ctk.CTkLabel(
            jobicy_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        jobicy_quota.pack(anchor="w", pady=(5, 0))
        self._quota_labels["jobicy"] = jobicy_quota

        # Tip for JSearch
        jsearch_key = os.getenv("JSEARCH_API_KEY", "").strip()
        if not jsearch_key:
            tip_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent", border_width=2, border_color="#5DADE2")
            tip_frame.pack(fill="x", pady=(20, 10), padx=10)

            tip_label = ctk.CTkLabel(
                tip_frame,
                text="💡 Tip: Set up JSearch API key to search LinkedIn, Indeed, and Glassdoor",
                font=ctk.CTkFont(size=12),
                text_color="#5DADE2",
                wraplength=600
            )
            tip_label.pack(pady=10, padx=10)

        # Save button
        save_btn = ctk.CTkButton(
            scroll_frame,
            text="Save API Keys",
            height=40,
            width=200,
            command=self._save_api_keys
        )
        save_btn.pack(pady=(20, 10))

        # Separator between API settings and scoring config
        separator = ctk.CTkFrame(scroll_frame, height=2, fg_color="gray70")
        separator.pack(fill="x", pady=(20, 10), padx=10)

        # === Storage Maintenance Section ===
        storage_title = ctk.CTkLabel(
            scroll_frame,
            text="Storage Maintenance",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        storage_title.pack(pady=(10, 10), anchor="w", padx=10)

        storage_desc = ctk.CTkLabel(
            scroll_frame,
            text="Cached job-board responses are temporary and can be cleared without removing your profile, reports, or application status.",
            wraplength=600,
            justify="left",
            text_color="gray"
        )
        storage_desc.pack(pady=(0, 10), anchor="w", padx=10)

        clear_cache_btn = ctk.CTkButton(
            scroll_frame,
            text="Clear HTTP Cache",
            width=180,
            fg_color="transparent",
            border_width=1,
            command=self._on_clear_cache
        )
        clear_cache_btn.pack(pady=(0, 5), anchor="w", padx=10)

        self._cache_status_label = ctk.CTkLabel(
            scroll_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self._cache_status_label.pack(pady=(0, 10), anchor="w", padx=10)

        diagnostics_title = ctk.CTkLabel(
            scroll_frame,
            text="Performance Diagnostics",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        diagnostics_title.pack(pady=(10, 8), anchor="w", padx=10)

        self._source_diagnostics_textbox = ctk.CTkTextbox(
            scroll_frame,
            width=620,
            height=130,
            state="normal"
        )
        self._source_diagnostics_textbox.insert("end", self._source_diagnostics_text())
        self._source_diagnostics_textbox.configure(state="disabled")
        self._source_diagnostics_textbox.pack(pady=(0, 8), anchor="w", padx=10)

        refresh_diagnostics_btn = ctk.CTkButton(
            scroll_frame,
            text="Refresh Diagnostics",
            width=180,
            fg_color="transparent",
            border_width=1,
            command=self._refresh_source_diagnostics
        )
        refresh_diagnostics_btn.pack(pady=(0, 10), anchor="w", padx=10)

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

        # Danger Zone section
        danger_section = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        danger_section.pack(fill="x", pady=(10, 20), padx=10)

        # Section title
        danger_title = ctk.CTkLabel(
            danger_section,
            text="Danger Zone",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="red"
        )
        danger_title.pack(anchor="w", pady=(0, 5))

        # Description
        danger_desc = ctk.CTkLabel(
            danger_section,
            text="Remove Job Radar and all associated data from your system",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        danger_desc.pack(anchor="w", pady=(0, 10))

        # Uninstall button
        uninstall_btn = ctk.CTkButton(
            danger_section,
            text="Uninstall Job Radar",
            height=40,
            width=200,
            fg_color="red",
            hover_color="darkred",
            command=self._start_uninstall
        )
        uninstall_btn.pack(anchor="w", pady=(10, 0))

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
        # Section frame
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=(10, 20), padx=10)

        # Title
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 5))

        # Signup URL
        url_label = ctk.CTkLabel(
            section_frame,
            text=signup_url,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        url_label.pack(anchor="w", pady=(0, 10))

        # Fields
        for env_var, label, field_id in fields:
            field_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=5)

            # Label
            lbl = ctk.CTkLabel(
                field_frame,
                text=f"{label}:",
                width=180,
                anchor="w"
            )
            lbl.pack(side="left", padx=(0, 10))

            # Entry field (masked by default)
            current_value = os.getenv(env_var, "")
            entry = ctk.CTkEntry(
                field_frame,
                width=300,
                show="*" if "KEY" in env_var or "PASSWORD" in env_var else ""
            )
            entry.insert(0, current_value)
            entry.pack(side="left", padx=(0, 10))

            self._api_fields[field_id] = (entry, env_var)

            # Show/Hide toggle for masked fields
            if "KEY" in env_var or "PASSWORD" in env_var:
                show_var = ctk.BooleanVar(value=False)

                def toggle_visibility(e=entry, v=show_var):
                    if v.get():
                        e.configure(show="")
                    else:
                        e.configure(show="*")

                show_btn = ctk.CTkButton(
                    field_frame,
                    text="Show",
                    width=60,
                    command=lambda: (show_var.set(not show_var.get()), toggle_visibility())
                )
                show_btn.pack(side="left")

        # Test button and status
        test_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        test_frame.pack(fill="x", pady=(10, 0))

        test_btn = ctk.CTkButton(
            test_frame,
            text="Test API Key",
            width=120,
            command=lambda: self._test_api_keys(fields)
        )
        test_btn.pack(side="left", padx=(0, 10))

        status_label = ctk.CTkLabel(
            test_frame,
            text="",
            anchor="w"
        )
        status_label.pack(side="left")

        # Quota usage label
        quota_label = ctk.CTkLabel(
            test_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        quota_label.pack(side="left", padx=(10, 0))

        # Store quota label reference using first field's backend API name
        # Map field_id to backend API for quota lookup
        backend_api_map = {
            "jsearch": "jsearch",
            "usajobs": "usajobs",
            "adzuna_id": "adzuna",
            "authentic_jobs": "authentic_jobs",
            "serpapi": "serpapi",
        }
        first_field_id = fields[0][2]
        backend_api = backend_api_map.get(first_field_id)
        if backend_api:
            self._quota_labels[backend_api] = quota_label

        # Store status label reference (use first field's ID as section ID)
        self._api_status_labels[fields[0][2]] = status_label

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

        status_label.configure(text="Testing...", text_color="gray")
        threading.Thread(target=test_thread, daemon=True).start()

    def _test_jsearch(self, api_key, status_label):
        """Test JSearch API key."""
        if not api_key:
            self.after(0, lambda: status_label.configure(text="⚠ No API key provided", text_color="orange"))
            return

        try:
            url = "https://jsearch.p.rapidapi.com/search"
            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            params = {"query": "test", "num_pages": "1"}
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                self.after(0, lambda: status_label.configure(text="✓ Valid", text_color="green"))
            elif response.status_code in (401, 403):
                self.after(0, lambda: status_label.configure(text="✗ Invalid key", text_color="red"))
            else:
                self.after(0, lambda: status_label.configure(text=f"⚠ Unexpected status {response.status_code}", text_color="orange"))
        except (requests.Timeout, requests.RequestException) as e:
            self.after(0, lambda: status_label.configure(text="⚠ Network error", text_color="orange"))

    def _test_usajobs(self, email, api_key, status_label):
        """Test USAJobs API credentials."""
        if not email or not api_key:
            self.after(0, lambda: status_label.configure(text="⚠ Both email and API key required", text_color="orange"))
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

            if response.status_code == 200:
                self.after(0, lambda: status_label.configure(text="✓ Valid", text_color="green"))
            elif response.status_code in (401, 403):
                self.after(0, lambda: status_label.configure(text="✗ Invalid credentials", text_color="red"))
            else:
                self.after(0, lambda: status_label.configure(text=f"⚠ Unexpected status {response.status_code}", text_color="orange"))
        except (requests.Timeout, requests.RequestException) as e:
            self.after(0, lambda: status_label.configure(text="⚠ Network error", text_color="orange"))

    def _test_adzuna(self, app_id, app_key, status_label):
        """Test Adzuna API credentials."""
        if not app_id or not app_key:
            self.after(0, lambda: status_label.configure(text="⚠ Both App ID and App Key required", text_color="orange"))
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

            if response.status_code == 200:
                self.after(0, lambda: status_label.configure(text="✓ Valid", text_color="green"))
            elif response.status_code in (401, 403):
                self.after(0, lambda: status_label.configure(text="✗ Invalid credentials", text_color="red"))
            else:
                self.after(0, lambda: status_label.configure(text=f"⚠ Unexpected status {response.status_code}", text_color="orange"))
        except (requests.Timeout, requests.RequestException) as e:
            self.after(0, lambda: status_label.configure(text="⚠ Network error", text_color="orange"))

    def _test_authentic_jobs(self, api_key, status_label):
        """Test Authentic Jobs API key."""
        if not api_key:
            self.after(0, lambda: status_label.configure(text="⚠ No API key provided", text_color="orange"))
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

            if response.status_code == 200:
                self.after(0, lambda: status_label.configure(text="✓ Valid", text_color="green"))
            elif response.status_code in (401, 403):
                self.after(0, lambda: status_label.configure(text="✗ Invalid key", text_color="red"))
            else:
                self.after(0, lambda: status_label.configure(text=f"⚠ Unexpected status {response.status_code}", text_color="orange"))
        except (requests.Timeout, requests.RequestException) as e:
            self.after(0, lambda: status_label.configure(text="⚠ Network error", text_color="orange"))

    def _test_serpapi(self, api_key, status_label):
        """Test SerpAPI key."""
        if not api_key:
            self.after(0, lambda: status_label.configure(text="⚠ No API key provided", text_color="orange"))
            return

        try:
            url = f"https://serpapi.com/search?engine=google_jobs&q=test&api_key={api_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                self.after(0, lambda: status_label.configure(text="✓ Valid", text_color="green"))
            elif response.status_code in (401, 403):
                self.after(0, lambda: status_label.configure(text="✗ Invalid key", text_color="red"))
            else:
                self.after(0, lambda: status_label.configure(
                    text=f"⚠ HTTP {response.status_code}", text_color="orange"))

        except requests.Timeout:
            self.after(0, lambda: status_label.configure(text="⚠ Timeout", text_color="orange"))
        except requests.RequestException as e:
            self.after(0, lambda: status_label.configure(text=f"⚠ Error: {e}", text_color="orange"))

    def _save_api_keys(self):
        """Save API keys to .env file atomically."""
        # Collect all field values
        env_vars = {}
        for field_id, (entry, env_var) in self._api_fields.items():
            value = entry.get().strip()
            if value:  # Only save non-empty values
                env_vars[env_var] = value

        # Find or create .env path
        dotenv_path = find_dotenv(usecwd=True)
        if not dotenv_path:
            dotenv_path = os.path.join(os.getcwd(), ".env")

        # Read existing .env content
        existing_vars = {}
        if os.path.exists(dotenv_path):
            with open(dotenv_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        existing_vars[key.strip()] = value.strip()

        # Merge with new values
        existing_vars.update(env_vars)

        # Build .env content
        content_lines = ["# Job Radar API Configuration\n"]

        # JSearch section
        content_lines.append("\n# JSearch API (LinkedIn, Indeed, Glassdoor aggregator)")
        content_lines.append("# Get your key from RapidAPI: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
        if "JSEARCH_API_KEY" in existing_vars:
            content_lines.append(f"JSEARCH_API_KEY={existing_vars['JSEARCH_API_KEY']}")
        else:
            content_lines.append("JSEARCH_API_KEY=")

        # USAJobs section
        content_lines.append("\n# USAJobs API (Federal Government Jobs)")
        content_lines.append("# Register at: https://developer.usajobs.gov/")
        if "USAJOBS_EMAIL" in existing_vars:
            content_lines.append(f"USAJOBS_EMAIL={existing_vars['USAJOBS_EMAIL']}")
        else:
            content_lines.append("USAJOBS_EMAIL=")
        if "USAJOBS_API_KEY" in existing_vars:
            content_lines.append(f"USAJOBS_API_KEY={existing_vars['USAJOBS_API_KEY']}")
        else:
            content_lines.append("USAJOBS_API_KEY=")

        # Adzuna section
        content_lines.append("\n# Adzuna API")
        content_lines.append("# Sign up at: https://developer.adzuna.com/")
        if "ADZUNA_APP_ID" in existing_vars:
            content_lines.append(f"ADZUNA_APP_ID={existing_vars['ADZUNA_APP_ID']}")
        else:
            content_lines.append("ADZUNA_APP_ID=")
        if "ADZUNA_APP_KEY" in existing_vars:
            content_lines.append(f"ADZUNA_APP_KEY={existing_vars['ADZUNA_APP_KEY']}")
        else:
            content_lines.append("ADZUNA_APP_KEY=")

        # Authentic Jobs section
        content_lines.append("\n# Authentic Jobs API")
        content_lines.append("# Get your key from: https://authenticjobs.com/api/")
        if "AUTHENTIC_JOBS_API_KEY" in existing_vars:
            content_lines.append(f"AUTHENTIC_JOBS_API_KEY={existing_vars['AUTHENTIC_JOBS_API_KEY']}")
        else:
            content_lines.append("AUTHENTIC_JOBS_API_KEY=")

        # SerpAPI section
        content_lines.append("\n# SerpAPI (Google Jobs)")
        content_lines.append("# Sign up at: https://serpapi.com/")
        if "SERPAPI_API_KEY" in existing_vars:
            content_lines.append(f"SERPAPI_API_KEY={existing_vars['SERPAPI_API_KEY']}")
        else:
            content_lines.append("SERPAPI_API_KEY=")

        content = "\n".join(content_lines) + "\n"

        # Atomic write using tempfile + replace
        try:
            fd, temp_path = tempfile.mkstemp(mode="w", encoding="utf-8", dir=os.path.dirname(dotenv_path) or ".")
            try:
                os.write(fd, content.encode("utf-8"))
                os.close(fd)
                Path(temp_path).replace(dotenv_path)

                # Reload environment variables
                load_dotenv(dotenv_path, override=True)

                # Show success message
                self._show_info_dialog("API keys saved successfully!")

            except Exception as e:
                os.close(fd)
                os.unlink(temp_path)
                raise
        except Exception as e:
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
        # Create modal dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Success")
        dialog.geometry("400x150")

        # Make modal
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Info message
        info_label = ctk.CTkLabel(
            dialog,
            text=message,
            wraplength=350,
            font=ctk.CTkFont(size=13),
            text_color="green"
        )
        info_label.pack(pady=30, padx=20)

        # OK button
        ok_btn = ctk.CTkButton(
            dialog,
            text="OK",
            width=100,
            command=dialog.destroy
        )
        ok_btn.pack(pady=(0, 20))


def launch_gui():
    """Create and run the main GUI window."""
    app = MainWindow()
    app.mainloop()
