"""Update notification banner widget for Job Radar.

Displays full-width banner when newer version is available, with Download,
Remind Later, and Dismiss (X) buttons. Supports multiple states: notification,
progress, complete, and failure.
"""

import logging
import customtkinter as ctk
from customtkinter import CTkFont

logger = logging.getLogger(__name__)


class UpdateBanner(ctk.CTkFrame):
    """Full-width update notification banner with multi-state support.

    VS Code-style banner displayed above main content when update available.
    Supports four states: notification, progress, complete, failure.
    """

    def __init__(
        self,
        parent,
        version: str,
        release_url: str,
        on_dismiss: callable,
        on_remind: callable,
        on_download: callable
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
        on_download : callable
            Callback when user confirms download - called with version string
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
        self.on_download = on_download

        # Callbacks set by MainWindow
        self._on_cancel = None
        self._on_install = None
        self._dest_path = None

        # Grid column configuration for expanded layout
        self.grid_columnconfigure(0, weight=1)  # Message (expands)
        self.grid_columnconfigure(1, weight=0)  # Progress bar or button
        self.grid_columnconfigure(2, weight=0)  # Info label or button
        self.grid_columnconfigure(3, weight=0)  # Action button

        # Create ALL state widgets upfront (not gridded yet)
        self._create_notification_widgets()
        self._create_progress_widgets()
        self._create_complete_widgets()
        self._create_failure_widgets()

        # Start in notification state
        self.show_notification()

    def _create_notification_widgets(self):
        """Create widgets for notification state."""
        self.message_label = ctk.CTkLabel(
            self,
            text=f"Version {self.version} available",
            text_color="white",
            font=CTkFont(size=13),
            anchor="w"
        )

        self.download_btn = ctk.CTkButton(
            self,
            text="Download",
            width=100,
            command=self._on_download_click
        )

        self.remind_btn = ctk.CTkButton(
            self,
            text="Remind Later",
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color="white",
            command=self._on_remind_click
        )

        self.x_btn = ctk.CTkButton(
            self,
            text="x",
            width=30,
            command=self._on_x_click
        )

    def _create_progress_widgets(self):
        """Create widgets for progress state."""
        self.progress_message = ctk.CTkLabel(
            self,
            text=f"Downloading v{self.version}...",
            text_color="white",
            font=CTkFont(size=13),
            anchor="w"
        )

        self.progress_bar = ctk.CTkProgressBar(
            self,
            width=200,
            progress_color="white",
            fg_color=("#2980B9", "#1A5276")
        )
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            self,
            text="0%",
            text_color="white",
            font=CTkFont(size=12)
        )

        self.cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            width=80,
            fg_color="transparent",
            border_width=1,
            border_color="white",
            command=self._on_cancel_click
        )

    def _create_complete_widgets(self):
        """Create widgets for complete state."""
        self.complete_message = ctk.CTkLabel(
            self,
            text="Download complete!",
            text_color="white",
            font=CTkFont(size=13, weight="bold"),
            anchor="w"
        )

        self.install_btn = ctk.CTkButton(
            self,
            text="Install Now",
            width=100,
            command=self._on_install_click
        )

        self.complete_x_btn = ctk.CTkButton(
            self,
            text="x",
            width=30,
            command=self._on_complete_dismiss
        )

    def _create_failure_widgets(self):
        """Create widgets for failure state."""
        self.failure_message = ctk.CTkLabel(
            self,
            text="Download failed",
            text_color="white",
            font=CTkFont(size=13),
            anchor="w"
        )

        self.retry_btn = ctk.CTkButton(
            self,
            text="Retry",
            width=80,
            command=self._on_retry_click
        )

        self.dismiss_btn = ctk.CTkButton(
            self,
            text="Dismiss",
            width=80,
            fg_color="transparent",
            border_width=1,
            border_color="white",
            command=self._on_dismiss_click
        )

    def _hide_all(self):
        """Hide all state-specific widgets."""
        # Notification state
        self.message_label.grid_remove()
        self.download_btn.grid_remove()
        self.remind_btn.grid_remove()
        self.x_btn.grid_remove()

        # Progress state
        self.progress_message.grid_remove()
        self.progress_bar.grid_remove()
        self.progress_label.grid_remove()
        self.cancel_btn.grid_remove()

        # Complete state
        self.complete_message.grid_remove()
        self.install_btn.grid_remove()
        self.complete_x_btn.grid_remove()

        # Failure state
        self.failure_message.grid_remove()
        self.retry_btn.grid_remove()
        self.dismiss_btn.grid_remove()

    def show_notification(self):
        """Show notification state."""
        self._hide_all()
        self.message_label.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)
        self.download_btn.grid(row=0, column=1, padx=(0, 10), pady=10)
        self.remind_btn.grid(row=0, column=2, padx=(0, 10), pady=10)
        self.x_btn.grid(row=0, column=3, padx=(0, 20), pady=10)

    def show_progress(self):
        """Show progress state."""
        self._hide_all()
        self.progress_message.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        self.progress_label.grid(row=0, column=2, padx=(0, 10), pady=10)
        self.cancel_btn.grid(row=0, column=3, padx=(0, 20), pady=10)
        # Configure column 1 weight=1 so progress bar expands
        self.grid_columnconfigure(1, weight=1)

    def update_progress(self, downloaded: int, total: int):
        """Update progress bar and label.

        Parameters
        ----------
        downloaded : int
            Bytes downloaded
        total : int
            Total bytes
        """
        progress = downloaded / total if total > 0 else 0
        self.progress_bar.set(progress)  # CTkProgressBar expects 0.0-1.0

        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        pct = int(progress * 100)

        self.progress_label.configure(
            text=f"{pct}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)"
        )

    def show_complete(self, dest_path: str):
        """Show complete state.

        Parameters
        ----------
        dest_path : str
            Path to downloaded installer file
        """
        self._dest_path = dest_path
        self._hide_all()
        # Reset column 1 weight for complete state
        self.grid_columnconfigure(1, weight=0)
        self.complete_message.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)
        self.install_btn.grid(row=0, column=1, padx=(0, 10), pady=10)
        self.complete_x_btn.grid(row=0, column=2, padx=(0, 20), pady=10)

    def show_failure(self, error: str):
        """Show failure state.

        Parameters
        ----------
        error : str
            Error message
        """
        self._hide_all()
        # Reset column 1 weight for failure state
        self.grid_columnconfigure(1, weight=0)
        # Truncate error message if too long
        error_display = error[:60] + "..." if len(error) > 60 else error
        self.failure_message.configure(text=f"Download failed: {error_display}")
        self.failure_message.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)
        self.retry_btn.grid(row=0, column=1, padx=(0, 10), pady=10)
        self.dismiss_btn.grid(row=0, column=2, padx=(0, 20), pady=10)

    def _on_download_click(self):
        """Handle Download button click - show confirmation dialog."""
        # Trigger download flow in MainWindow
        self.on_download(self.version)

    def _on_remind_click(self):
        """Handle Remind Later button click - dismiss for 7 days."""
        self.on_remind(self.version)

    def _on_x_click(self):
        """Handle X button click - dismiss for 24 hours."""
        self.on_dismiss(self.version)

    def _on_cancel_click(self):
        """Handle Cancel button click - cancel download."""
        if self._on_cancel:
            self._on_cancel()

    def _on_retry_click(self):
        """Handle Retry button click - restart download from scratch."""
        self.on_download(self.version)

    def _on_dismiss_click(self):
        """Handle Dismiss button click - same as X button."""
        self.on_dismiss(self.version)

    def _on_install_click(self):
        """Handle Install Now button click - stub for Phase 40."""
        logger.info("Install clicked - will be implemented in Phase 40")
        if self._on_install:
            self._on_install()

    def _on_complete_dismiss(self):
        """Handle X button click in complete state - remove banner."""
        self.destroy()

    def set_cancel_callback(self, callback):
        """Set cancel callback.

        Parameters
        ----------
        callback : callable
            Callback to invoke when cancel button clicked
        """
        self._on_cancel = callback

    def set_install_callback(self, callback):
        """Set install callback.

        Parameters
        ----------
        callback : callable
            Callback to invoke when install button clicked
        """
        self._on_install = callback


class DownloadConfirmDialog(ctk.CTkToplevel):
    """Download confirmation dialog showing version and file size."""

    def __init__(self, parent, version: str, size_bytes: int, on_confirm: callable):
        """Initialize confirmation dialog.

        Parameters
        ----------
        parent
            Parent widget
        version : str
            Version string (e.g., "2.2.0")
        size_bytes : int
            File size in bytes
        on_confirm : callable
            Callback to invoke when user confirms download
        """
        super().__init__(parent)

        self.title("Download Update")
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self.on_confirm = on_confirm

        # Message
        size_mb = size_bytes / (1024 * 1024)
        message = ctk.CTkLabel(
            self,
            text=f"Download v{version}?\n~{size_mb:.1f} MB",
            font=CTkFont(size=14)
        )
        message.pack(pady=(30, 20))

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        download_btn = ctk.CTkButton(
            button_frame,
            text="Download",
            width=120,
            command=self._on_confirm_click
        )
        download_btn.pack(side="left")

        # Center dialog on parent window after it's mapped
        self.after(10, self._center_on_parent)

    def _on_confirm_click(self):
        """Handle Download button click - invoke callback and close."""
        self.on_confirm()
        self.destroy()

    def _center_on_parent(self):
        """Center dialog on parent window."""
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
