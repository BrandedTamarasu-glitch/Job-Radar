"""Changelog dialog for displaying release notes in Job Radar GUI.

Shows extracted release notes summary with link to full GitHub release page.
"""

import webbrowser
import customtkinter as ctk
from customtkinter import CTkFont


class ChangelogDialog(ctk.CTkToplevel):
    """Modal dialog for displaying release notes summary.

    Shows extracted summary from release notes in a read-only textbox,
    with a link to view full release notes on GitHub and a Close button.

    Attributes
    ----------
    version : str
        Version string being displayed (e.g., "2.2.0")
    summary : str
        Extracted summary text from release notes
    github_url : str
        Full GitHub releases URL for this version
    """

    def __init__(self, parent, version: str, summary: str, github_url: str):
        """Initialize changelog dialog.

        Parameters
        ----------
        parent
            Parent window
        version : str
            Version string (e.g., "2.2.0")
        summary : str
            Extracted summary text from release notes
        github_url : str
            GitHub releases URL for full release notes
        """
        super().__init__(parent)
        self.title(f"What's New in v{version}")
        self.geometry("500x400")
        self.resizable(False, False)

        # Store parameters
        self.version = version
        self.summary = summary
        self.github_url = github_url

        # Make modal
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        # Summary textbox (read-only)
        self.summary_box = ctk.CTkTextbox(
            self,
            height=280,
            width=460,
            wrap="word"
        )
        self.summary_box.pack(pady=(20, 10), padx=20)

        # Populate summary
        self.summary_box.insert("1.0", summary)

        # Set to read-only
        self.summary_box.configure(state="disabled")

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        # GitHub link button (styled as link)
        github_btn = ctk.CTkButton(
            button_frame,
            text="View Full Release Notes on GitHub",
            width=240,
            fg_color="transparent",
            border_width=1,
            command=self._open_github
        )
        github_btn.pack(side="left", padx=5)

        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            width=100,
            command=self.destroy
        )
        close_btn.pack(side="left", padx=5)

        # Center on parent after dialog renders
        self.after(10, self._center_on_parent)

    def _center_on_parent(self):
        """Center dialog on parent window."""
        self.update_idletasks()

        parent_window = self.master.winfo_toplevel()
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()

        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.geometry(f"+{x}+{y}")

    def _open_github(self):
        """Open full release notes in browser."""
        webbrowser.open(self.github_url)
