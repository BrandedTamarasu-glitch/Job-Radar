"""Main GUI window for Job Radar desktop application."""

import queue
import threading

import customtkinter as ctk
from pathlib import Path

from job_radar import __version__
from job_radar.paths import get_data_dir
from job_radar.profile_manager import load_profile
from job_radar.gui.worker_thread import create_mock_worker


class MainWindow(ctk.CTk):
    """Main application window with system theme, header, tabs, and routing."""

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

        # Create header
        self._create_header()

        # Check if profile exists and route to appropriate view
        self._profile_exists = self._has_profile()

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
        """Handle Get Started button click (stub for Phase 29)."""
        print("Get Started clicked — profile form coming in Phase 29")

    def _show_main_tabs(self):
        """Display tabbed interface for users with existing profiles."""
        # Create tabview
        tabview = ctk.CTkTabview(self)
        tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add tabs
        tabview.add("Profile")
        tabview.add("Search")

        # Set default to Profile tab
        tabview.set("Profile")

        # Build tab contents
        self._build_profile_tab(tabview.tab("Profile"))
        self._build_search_tab(tabview.tab("Search"))

    def _build_profile_tab(self, parent):
        """Build Profile tab with profile summary display."""
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

        except Exception as e:
            # Error loading profile
            error_label = ctk.CTkLabel(
                scroll_frame,
                text="Could not load profile",
                text_color="red"
            )
            error_label.pack(pady=20)

    def _add_profile_field(self, parent, row, label_text, value_text):
        """Add a label-value pair to the profile grid."""
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
        """Build Search tab with threading integration."""
        # Create content frame that will hold either idle or progress state
        self._search_content = ctk.CTkFrame(parent, fg_color="transparent")
        self._search_content.pack(fill="both", expand=True, padx=10, pady=10)
        self._search_content.grid_rowconfigure(0, weight=1)
        self._search_content.grid_columnconfigure(0, weight=1)

        # Start with idle state
        self._show_search_idle()

    def _show_search_idle(self):
        """Display idle state with Run Search button."""
        # Clear current content
        for widget in self._search_content.winfo_children():
            widget.destroy()

        # Clear worker references
        self._worker = None
        self._worker_thread = None

        # Content frame (centered)
        content_frame = ctk.CTkFrame(self._search_content, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        # Run Search button
        self._search_button = ctk.CTkButton(
            content_frame,
            text="Run Search",
            height=40,
            width=200,
            state="normal" if self._profile_exists else "disabled",
            command=self._start_mock_search
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
        """Display progress state with progress bar and cancel button."""
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
        self._progress_count.pack(pady=(0, 20))

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

    def _check_queue(self):
        """Process messages from worker thread queue (runs in main GUI thread)."""
        try:
            # Process all pending messages
            while True:
                try:
                    msg = self._queue.get_nowait()
                    msg_type = msg[0]

                    if msg_type == "progress":
                        _, source, current, total = msg
                        self._update_progress(source, current, total)
                    elif msg_type == "complete":
                        _, total = msg
                        self._on_search_complete(total)
                    elif msg_type == "cancelled":
                        self._on_search_cancelled()
                    elif msg_type == "error":
                        _, error_msg = msg
                        self._show_error_dialog(error_msg)
                        self._show_search_idle()

                except queue.Empty:
                    break

        finally:
            # Re-schedule next check
            self.after(100, self._check_queue)

    def _start_mock_search(self):
        """Start mock search operation in worker thread."""
        # Show progress state
        self._show_search_progress()

        # Create and start worker
        self._worker, self._worker_thread = create_mock_worker(self._queue)
        self._worker_thread.start()

    def _cancel_search(self):
        """Cancel the currently running search operation."""
        if self._worker:
            self._worker.cancel()

    def _update_progress(self, source: str, current: int, total: int):
        """Update progress display with current source information."""
        self._progress_label.configure(text=f"Fetching {source}...")
        self._progress_bar.set(current / total)
        self._progress_count.configure(text=f"Source {current} of {total}")

    def _on_search_complete(self, total: int):
        """Handle search completion."""
        self._progress_label.configure(text="Search complete!")
        self._progress_bar.set(1.0)
        self._progress_count.configure(text=f"Completed {total} sources")

        # Reset to idle after 2 seconds
        self.after(2000, self._show_search_idle)

    def _on_search_cancelled(self):
        """Handle search cancellation."""
        self._progress_label.configure(text="Search cancelled")
        self._progress_bar.set(0)

        # Reset to idle after 1.5 seconds
        self.after(1500, self._show_search_idle)

    def _show_error_dialog(self, message: str):
        """Show modal error dialog."""
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


def launch_gui():
    """Create and run the main GUI window."""
    app = MainWindow()
    app.mainloop()
