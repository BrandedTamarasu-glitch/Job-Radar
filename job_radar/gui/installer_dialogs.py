"""Installer confirmation and instruction dialogs for Job Radar GUI.

Provides modal dialogs for the install confirmation flow and Linux-specific
installation instructions.
"""

from pathlib import Path
import subprocess

import customtkinter as ctk
from customtkinter import CTkFont


class InstallConfirmDialog(ctk.CTkToplevel):
    """Modal confirmation dialog before launching installer and closing app.

    Shows version-specific message with platform-specific hint about what will happen.
    Presents "Install Now" and "Cancel" buttons.

    Attributes
    ----------
    result : bool or None
        True if user clicked Install Now, None if cancelled
    """

    def __init__(self, parent, version: str, platform_message: str, on_confirm: callable):
        """Initialize install confirmation dialog.

        Parameters
        ----------
        parent
            Parent window
        version : str
            Version string to display (e.g., "2.2.0")
        platform_message : str
            Platform-specific message explaining what will happen
            (e.g., "Opening installer DMG...")
        on_confirm : callable
            Callback to invoke when user clicks Install Now
        """
        super().__init__(parent)
        self.title("Install Update")
        self.geometry("420x180")
        self.resizable(False, False)

        # Store parameters
        self.version = version
        self.platform_message = platform_message
        self._on_confirm = on_confirm

        # Make modal
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        # Result attribute
        self.result = None

        # Main message
        message = ctk.CTkLabel(
            self,
            text=f"Ready to install v{version}?\nThe app will close and restart.",
            wraplength=380,
            font=CTkFont(size=14),
        )
        message.pack(pady=(30, 10), padx=20)

        # Platform-specific hint (gray, smaller font)
        platform_hint = ctk.CTkLabel(
            self,
            text=platform_message,
            wraplength=380,
            font=CTkFont(size=11),
            text_color="gray",
        )
        platform_hint.pack(pady=(0, 20), padx=20)

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        # Cancel button
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=120, command=self._cancel)
        cancel_btn.pack(side="left", padx=5)

        # Install Now button
        install_btn = ctk.CTkButton(button_frame, text="Install Now", width=120, command=self._install_now)
        install_btn.pack(side="left", padx=5)

        # Handle window close as cancel
        self.protocol("WM_DELETE_WINDOW", self._cancel)

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

    def _install_now(self):
        """Handle Install Now button click."""
        self.result = True
        self._on_confirm()
        self.destroy()

    def _cancel(self):
        """Handle Cancel button or window close."""
        self.result = None
        self.destroy()


class LinuxInstallInstructionsDialog(ctk.CTkToplevel):
    """Instructions dialog for Linux users showing tar extraction commands.

    Displays extraction commands in a read-only textbox with "Copy Command"
    button (using tkinter clipboard) and "Open Folder" button (xdg-open).

    Attributes
    ----------
    tar_path : Path
        Path to the downloaded tar.gz file
    version : str
        Version string being installed
    """

    def __init__(self, parent, tar_path: Path, version: str):
        """Initialize Linux installation instructions dialog.

        Parameters
        ----------
        parent
            Parent window
        tar_path : Path
            Path to downloaded tar.gz installer
        version : str
            Version string (e.g., "2.2.0")
        """
        super().__init__(parent)
        self.title("Installation Instructions")
        self.geometry("560x350")
        self.resizable(False, False)

        # Store parameters
        self.tar_path = tar_path
        self.version = version

        # Make modal
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        # Title
        title_label = ctk.CTkLabel(
            self, text=f"Job Radar v{version} Downloaded", font=CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 10))

        # Instructions textbox (read-only)
        instructions_box = ctk.CTkTextbox(self, height=140, width=520)
        instructions_box.pack(pady=(0, 15), padx=20)

        # Populate instructions
        instructions_box.insert("1.0", "Extract and install:\n\n")
        instructions_box.insert("end", f"tar -xzf {tar_path.name} -C ~/Applications/\n\n")
        instructions_box.insert("end", "Or extract to a custom location:\n\n")
        instructions_box.insert("end", f"tar -xzf {tar_path.name} -C /path/to/destination/\n")

        # Set to read-only
        instructions_box.configure(state="disabled")

        # Store command for clipboard
        self._copy_command = f"tar -xzf {tar_path.name} -C ~/Applications/"

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        # Copy Command button
        self._copy_btn = ctk.CTkButton(button_frame, text="Copy Command", width=140, command=self._copy_to_clipboard)
        self._copy_btn.pack(side="left", padx=5)

        # Open Folder button
        open_folder_btn = ctk.CTkButton(button_frame, text="Open Folder", width=140, command=self._open_folder)
        open_folder_btn.pack(side="left", padx=5)

        # Close button
        close_btn = ctk.CTkButton(
            button_frame, text="Close", width=100, fg_color="transparent", border_width=1, command=self.destroy
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

    def _copy_to_clipboard(self):
        """Copy extraction command to clipboard using tkinter."""
        self.clipboard_clear()
        self.clipboard_append(self._copy_command)
        self.update()  # Required for clipboard to persist

        # Show feedback
        original_text = self._copy_btn.cget("text")
        self._copy_btn.configure(text="Copied!")
        self.after(2000, lambda: self._copy_btn.configure(text=original_text))

    def _open_folder(self):
        """Open containing folder in file manager using xdg-open."""
        try:
            subprocess.Popen(["xdg-open", str(self.tar_path.parent)])
        except FileNotFoundError:
            # xdg-open not installed - ignore gracefully
            # Could show path in button text, but just log for now
            pass
        except Exception as e:
            # Other errors - log but don't crash
            import logging

            logging.getLogger(__name__).debug("Could not open folder: %s", e)
