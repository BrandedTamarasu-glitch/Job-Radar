"""Uninstall dialogs for Job Radar GUI.

Provides modal dialogs for the complete uninstall flow: backup offer, path preview,
final confirmation, and deletion progress.
"""

import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from ..uninstaller import create_backup


class BackupOfferDialog(ctk.CTkToplevel):
    """Modal dialog offering backup before uninstall.

    Presents three options:
    - Create Backup (opens file picker)
    - Skip Backup (proceed without backup)
    - Cancel (abort uninstall)

    Attributes
    ----------
    result : str or None
        Set to "backup_done", "skip", or "cancel" before destroy()
    """

    def __init__(self, parent):
        """Initialize backup offer dialog.

        Parameters
        ----------
        parent
            Parent window
        """
        super().__init__(parent)
        self.title("Uninstall Job Radar")
        self.geometry("450x250")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Result attribute
        self.result = None

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Body text
        message = ctk.CTkLabel(
            self,
            text="Would you like to create a backup of your profile and config before uninstalling?",
            wraplength=400,
            font=ctk.CTkFont(size=13)
        )
        message.pack(pady=30, padx=20)

        # Status label (for success/error messages)
        self._status_label = ctk.CTkLabel(
            self,
            text="",
            wraplength=400,
            font=ctk.CTkFont(size=12)
        )
        self._status_label.pack(pady=(0, 10))

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(10, 20))

        # Create Backup button
        backup_btn = ctk.CTkButton(
            button_frame,
            text="Create Backup",
            width=130,
            command=self._create_backup
        )
        backup_btn.pack(side="left", padx=5)

        # Skip Backup button
        skip_btn = ctk.CTkButton(
            button_frame,
            text="Skip Backup",
            width=130,
            command=self._skip_backup
        )
        skip_btn.pack(side="left", padx=5)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            command=self._cancel
        )
        cancel_btn.pack(side="left", padx=5)

    def _create_backup(self):
        """Open file picker and create backup ZIP."""
        save_path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".zip",
            initialfile="job-radar-backup.zip",
            filetypes=[("ZIP files", "*.zip")]
        )

        if not save_path:
            # User cancelled file picker - return to dialog
            return

        try:
            create_backup(save_path)
            self._status_label.configure(text="Backup saved!", text_color="green")
            self.update()
            self.after(1000, self._finish_backup)
        except Exception as e:
            self._status_label.configure(
                text=f"Error creating backup: {e}\n\nYou can continue without backup or cancel.",
                text_color="red"
            )

    def _finish_backup(self):
        """Finish backup flow after success message."""
        self.result = "backup_done"
        self.destroy()

    def _skip_backup(self):
        """Skip backup and proceed."""
        self.result = "skip"
        self.destroy()

    def _cancel(self):
        """Cancel uninstall."""
        self.result = "cancel"
        self.destroy()


class PathPreviewDialog(ctk.CTkToplevel):
    """Modal dialog showing paths that will be deleted.

    Displays a scrollable list of files/directories with descriptions.
    User can continue or cancel.

    Attributes
    ----------
    result : bool
        True if user clicked Continue, False if cancelled
    """

    def __init__(self, parent, paths: list[tuple[str, str]]):
        """Initialize path preview dialog.

        Parameters
        ----------
        parent
            Parent window
        paths : list[tuple[str, str]]
            List of (path, description) tuples from get_uninstall_paths()
        """
        super().__init__(parent)
        self.title("Files to be removed")
        self.geometry("500x400")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Result attribute
        self.result = False

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Header
        header = ctk.CTkLabel(
            self,
            text="The following files and directories will be permanently deleted:",
            wraplength=460,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        header.pack(pady=(20, 10), padx=20)

        # Scrollable frame for paths
        scroll_frame = ctk.CTkScrollableFrame(self, width=460, height=220)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Add path entries
        for path, description in paths:
            # Entry frame
            entry_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            entry_frame.pack(fill="x", pady=5)

            # Path (bold/monospace)
            path_label = ctk.CTkLabel(
                entry_frame,
                text=path,
                font=ctk.CTkFont(family="Courier", size=11, weight="bold"),
                anchor="w"
            )
            path_label.pack(fill="x", padx=5)

            # Description (gray)
            desc_label = ctk.CTkLabel(
                entry_frame,
                text=description,
                font=ctk.CTkFont(size=10),
                text_color="gray",
                anchor="w"
            )
            desc_label.pack(fill="x", padx=5)

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(10, 20))

        # Continue button
        continue_btn = ctk.CTkButton(
            button_frame,
            text="Continue",
            width=120,
            command=self._continue
        )
        continue_btn.pack(side="left", padx=5)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            command=self._cancel
        )
        cancel_btn.pack(side="left", padx=5)

    def _continue(self):
        """User confirmed - proceed to final confirmation."""
        self.result = True
        self.destroy()

    def _cancel(self):
        """User cancelled - abort uninstall."""
        self.result = False
        self.destroy()


class FinalConfirmationDialog(ctk.CTkToplevel):
    """Modal dialog with checkbox + red button final confirmation.

    User must check "I understand this cannot be undone" before the
    red "Uninstall" button becomes enabled.

    Attributes
    ----------
    result : bool
        True if user clicked Uninstall, False if cancelled
    """

    def __init__(self, parent):
        """Initialize final confirmation dialog.

        Parameters
        ----------
        parent
            Parent window
        """
        super().__init__(parent)
        self.title("Confirm Uninstall")
        self.geometry("450x250")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Result attribute
        self.result = False

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Warning text
        warning = ctk.CTkLabel(
            self,
            text="This will permanently delete all Job Radar data.\nThis action cannot be undone.",
            wraplength=400,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="red"
        )
        warning.pack(pady=(30, 20), padx=20)

        # Checkbox variable
        self._checkbox_var = tk.BooleanVar(value=False)

        # Checkbox
        checkbox = ctk.CTkCheckBox(
            self,
            text="I understand this cannot be undone",
            variable=self._checkbox_var,
            command=self._toggle_button
        )
        checkbox.pack(pady=10)

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(20, 20))

        # Uninstall button (red, initially disabled)
        self._uninstall_btn = ctk.CTkButton(
            button_frame,
            text="Uninstall",
            width=120,
            fg_color="red",
            hover_color="darkred",
            state="disabled",
            command=self._uninstall
        )
        self._uninstall_btn.pack(side="left", padx=5)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            command=self._cancel
        )
        cancel_btn.pack(side="left", padx=5)

    def _toggle_button(self):
        """Toggle Uninstall button state based on checkbox."""
        if self._checkbox_var.get():
            self._uninstall_btn.configure(state="normal")
        else:
            self._uninstall_btn.configure(state="disabled")

    def _uninstall(self):
        """User confirmed - proceed with deletion."""
        self.result = True
        self.destroy()

    def _cancel(self):
        """User cancelled - abort uninstall."""
        self.result = False
        self.destroy()


class DeletionProgressDialog(ctk.CTkToplevel):
    """Modal dialog with indeterminate progress bar during deletion.

    Shows status text and prevents window close until deletion completes.
    """

    def __init__(self, parent):
        """Initialize deletion progress dialog.

        Parameters
        ----------
        parent
            Parent window
        """
        super().__init__(parent)
        self.title("Uninstalling...")
        self.geometry("400x180")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Prevent window close
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Status label
        self._status_label = ctk.CTkLabel(
            self,
            text="Deleting application data...",
            font=ctk.CTkFont(size=13)
        )
        self._status_label.pack(pady=(30, 20))

        # Progress bar (indeterminate)
        self._progress_bar = ctk.CTkProgressBar(self, width=300, mode="indeterminate")
        self._progress_bar.pack(pady=10)
        self._progress_bar.start()

    def update_status(self, message: str):
        """Update status message.

        Parameters
        ----------
        message : str
            New status message to display
        """
        self._status_label.configure(text=message)
        self.update()

    def close(self):
        """Stop progress bar and close dialog."""
        self._progress_bar.stop()
        self.destroy()
