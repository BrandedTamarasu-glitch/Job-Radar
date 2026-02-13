"""Main GUI window for Job Radar desktop application.

Integrates ProfileForm (create/edit), SearchControls (date/score/new-only),
and SearchWorker (full search pipeline) into a tabbed interface. Manages
navigation, progress display, and report opening.
"""

import os
import queue
import tempfile
import threading
import webbrowser
from pathlib import Path

import customtkinter as ctk
import requests

from job_radar import __version__
from job_radar.paths import get_data_dir
from job_radar.profile_manager import load_profile
from job_radar.config import load_config
from job_radar.gui.profile_form import ProfileForm
from job_radar.gui.search_controls import SearchControls
from job_radar.gui.worker_thread import create_search_worker
from dotenv import find_dotenv, load_dotenv


class MainWindow(ctk.CTk):
    """Main application window with system theme, header, tabs, and routing.

    Routes to welcome screen on first launch (no profile), or tabbed interface
    for users with existing profiles. Manages profile creation/editing flow,
    search execution with progress display, and report opening.
    """

    def __init__(self):
        super().__init__()

        # Set appearance and theme
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Configure window
        self.title("Job Radar")
        self.geometry("700x500")
        self.minsize(700, 500)

        # Grid layout: row 0 = header (fixed), row 1 = content (expands)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
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

        # Create header
        self._create_header()

        # Check if profile exists and route to appropriate view
        if not self._profile_exists:
            self._show_welcome_screen()
        else:
            self._show_main_tabs()

        # Start queue polling loop
        self._check_queue()

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
        # Clear row 1 content
        for widget in self.grid_slaves(row=1):
            widget.destroy()

        # Container frame for centered content
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Content frame (centered)
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        content_frame.grid(row=0, column=0)

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

    def _on_get_started(self):
        """Handle Get Started button click - show profile form in create mode."""
        # Clear row 1 content
        for widget in self.grid_slaves(row=1):
            widget.destroy()

        # Create container frame
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Create ProfileForm in create mode
        form = ProfileForm(
            parent=container,
            on_save_callback=self._on_profile_created,
            on_cancel_callback=self._show_welcome_screen,
            existing_profile=None
        )
        form.grid(row=0, column=0, sticky="nsew")

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
        # Clear row 1 content
        for widget in self.grid_slaves(row=1):
            widget.destroy()

        # Create tabview
        self._tabview = ctk.CTkTabview(self)
        self._tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        self._tabview.add("Profile")
        self._tabview.add("Search")
        self._tabview.add("Settings")

        # Set default to Profile tab
        self._tabview.set("Profile")

        # Build tab contents
        self._build_profile_tab(self._tabview.tab("Profile"))
        self._build_search_tab(self._tabview.tab("Search"))
        self._build_settings_tab(self._tabview.tab("Settings"))

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

            # Configure grid for label-value pairs
            scroll_frame.grid_columnconfigure(0, weight=0)  # Labels (left)
            scroll_frame.grid_columnconfigure(1, weight=1)  # Values (right)

            row = 0

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

        # Warning label (only visible when no profile)
        if not self._profile_exists:
            warning_label = ctk.CTkLabel(
                content_frame,
                text="Profile required to run search",
                text_color="red"
            )
            warning_label.pack()

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

    def _show_search_complete(self, job_count: int):
        """Display completion state with Open Report and New Search buttons.

        Parameters
        ----------
        job_count : int
            Total number of jobs found
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
            text=f"Search complete! {job_count} jobs found",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="green"
        )
        completion_label.pack(pady=(0, 30))

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
                        _, job_count, report_path = msg
                        self._on_search_complete(job_count, report_path)
                    elif msg_type == "cancelled":
                        self._on_search_cancelled()
                    elif msg_type == "error":
                        _, error_msg = msg
                        self._show_error_dialog(error_msg)
                        self._show_search_idle()
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

    def _start_real_search(self):
        """Start real search operation with full pipeline execution."""
        # Validate search controls
        is_valid, error_msg = self._search_controls.validate()
        if not is_valid:
            self._show_error_dialog(error_msg)
            return

        # Get search configuration
        search_config = self._search_controls.get_config()

        # Load profile
        try:
            profile_path = get_data_dir() / "profile.json"
            profile = load_profile(profile_path)
        except Exception as e:
            self._show_error_dialog(f"Failed to load profile: {e}")
            return

        # Show progress state
        self._show_search_progress()

        # Create and start real search worker
        self._worker, self._worker_thread = create_search_worker(
            self._queue,
            profile,
            search_config
        )
        self._worker_thread.start()

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

    def _on_search_complete(self, job_count: int, report_path: str):
        """Handle search completion.

        Parameters
        ----------
        job_count : int
            Total number of jobs found
        report_path : str
            Path to generated HTML report
        """
        self._report_path = report_path
        self._show_search_complete(job_count)

    def _on_search_cancelled(self):
        """Handle search cancellation."""
        # Show cancelled message briefly, then return to idle
        for widget in self._search_content.winfo_children():
            widget.destroy()

        content_frame = ctk.CTkFrame(self._search_content, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        cancel_label = ctk.CTkLabel(
            content_frame,
            text="Search cancelled",
            font=ctk.CTkFont(size=16),
            text_color="orange"
        )
        cancel_label.pack()

        # Reset to idle after 1.5 seconds
        self.after(1500, self._show_search_idle)

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
        """Build Settings tab with API key configuration.

        Parameters
        ----------
        parent
            Parent tab widget
        """
        # Create scrollable frame for settings content
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

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

        # Load current env values
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path, override=False)

        # Store API field references for saving
        self._api_fields = {}
        self._api_status_labels = {}

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

        # Tip for JSearch
        jsearch_key = os.getenv("JSEARCH_API_KEY", "").strip()
        if not jsearch_key:
            tip_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent", border_width=2, border_color="blue")
            tip_frame.pack(fill="x", pady=(20, 10), padx=10)

            tip_label = ctk.CTkLabel(
                tip_frame,
                text="💡 Tip: Set up JSearch API key to search LinkedIn, Indeed, and Glassdoor",
                font=ctk.CTkFont(size=12),
                text_color="blue",
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
