"""Update notification banner widget for Job Radar.

Displays full-width banner when newer version is available, with Download,
Remind Later, and Dismiss (X) buttons.
"""

import webbrowser

import customtkinter as ctk


class UpdateBanner(ctk.CTkFrame):
    """Full-width update notification banner with action buttons.

    VS Code-style banner displayed above main content when update available.
    """

    def __init__(
        self,
        parent,
        version: str,
        release_url: str,
        on_dismiss: callable,
        on_remind: callable
    ):
        """Initialize update banner.

        Parameters
        ----------
        parent
            Parent widget
        version : str
            Version string of available update (e.g., "2.2.0")
        release_url : str
            GitHub Releases URL to open in browser
        on_dismiss : callable
            Callback for X button - called with version string
        on_remind : callable
            Callback for Remind Later button - called with version string
        """
        # Blue/teal accent color for light/dark mode, no corner radius (full-width banner)
        super().__init__(
            parent,
            fg_color=("#3498DB", "#2874A6"),
            corner_radius=0
        )

        self.version = version
        self.release_url = release_url
        self.on_dismiss = on_dismiss
        self.on_remind = on_remind

        # Grid layout: message (expands) + 3 buttons (fixed)
        self.grid_columnconfigure(0, weight=1)  # Message expands
        self.grid_columnconfigure(1, weight=0)  # Download button
        self.grid_columnconfigure(2, weight=0)  # Remind Later button
        self.grid_columnconfigure(3, weight=0)  # X button

        # Message label (left-aligned, white text)
        self.message_label = ctk.CTkLabel(
            self,
            text=f"Version {version} available",
            text_color="white",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        self.message_label.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)

        # Download button (solid)
        self.download_btn = ctk.CTkButton(
            self,
            text="Download",
            width=100,
            command=self._on_download_click
        )
        self.download_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        # Remind Later button (transparent with border)
        self.remind_btn = ctk.CTkButton(
            self,
            text="Remind Later",
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color="white",
            command=self._on_remind_click
        )
        self.remind_btn.grid(row=0, column=2, padx=(0, 10), pady=10)

        # X button (small, dismiss)
        self.x_btn = ctk.CTkButton(
            self,
            text="x",
            width=30,
            command=self._on_x_click
        )
        self.x_btn.grid(row=0, column=3, padx=(0, 20), pady=10)

    def _on_download_click(self):
        """Handle Download button click - open GitHub Releases page in browser."""
        webbrowser.open(self.release_url)

    def _on_remind_click(self):
        """Handle Remind Later button click - dismiss for 7 days."""
        self.on_remind(self.version)

    def _on_x_click(self):
        """Handle X button click - dismiss for 24 hours."""
        self.on_dismiss(self.version)
