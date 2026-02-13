"""Reusable tag-chip input widget for list-type form fields.

Provides a CustomTkinter widget that displays values as removable chips
with Enter-to-add, X-to-remove, and Backspace-to-remove-last functionality.
"""

import customtkinter as ctk


class TagChipWidget(ctk.CTkFrame):
    """Tag-style chip input widget for list fields (skills, titles, dealbreakers).

    Features:
    - Type a value and press Enter to add as a chip
    - Click X button on chip to remove it
    - Backspace on empty entry field removes the last chip
    - Prevents duplicate values (case-insensitive)
    - Strips whitespace and rejects empty values

    Attributes
    ----------
    _chips : list[dict]
        Internal list of chips, each with {"value": str, "frame": CTkFrame}
    _entry : CTkEntry
        Input field for adding new chips
    _chips_container : CTkFrame
        Container frame that holds all chip widgets
    """

    def __init__(
        self,
        parent,
        placeholder: str = "Type and press Enter",
        **kwargs
    ):
        """Initialize the TagChipWidget.

        Parameters
        ----------
        parent
            Parent widget
        placeholder : str, optional
            Placeholder text for the entry field (default: "Type and press Enter")
        **kwargs
            Additional arguments passed to CTkFrame
        """
        super().__init__(parent, **kwargs)

        # Internal state
        self._chips: list[dict] = []

        # Layout: chips container at top, entry at bottom
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Chips container - scrollable frame for vertical stacking
        self._chips_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=100
        )
        self._chips_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 0))

        # Entry field at bottom
        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder
        )
        self._entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Bind events
        self._entry.bind("<Return>", self._on_enter)
        self._entry.bind("<BackSpace>", self._on_backspace)

    def _on_enter(self, event) -> None:
        """Handle Enter key press to add a new chip."""
        value = self._entry.get().strip()

        # Reject empty values
        if not value:
            return

        # Reject duplicates (case-insensitive)
        if any(chip["value"].lower() == value.lower() for chip in self._chips):
            # Clear entry but don't add
            self._entry.delete(0, "end")
            return

        # Add chip
        self._add_chip(value)

        # Clear entry
        self._entry.delete(0, "end")

    def _on_backspace(self, event) -> None:
        """Handle Backspace key to remove last chip when entry is empty."""
        # Only trigger if entry field is empty
        if self._entry.get() == "" and self._chips:
            # Remove last chip
            last_chip = self._chips[-1]
            self._remove_chip(last_chip)

            # Prevent default backspace behavior
            return "break"

    def _add_chip(self, value: str) -> None:
        """Add a chip to the container.

        Parameters
        ----------
        value : str
            The chip value to add
        """
        # Create chip frame
        chip_frame = ctk.CTkFrame(
            self._chips_container,
            fg_color=("gray80", "gray30"),
            corner_radius=15,
            height=30
        )
        chip_frame.pack(side="left", padx=3, pady=3)

        # Value label
        label = ctk.CTkLabel(
            chip_frame,
            text=value,
            padx=10,
            pady=5
        )
        label.pack(side="left")

        # Remove button (X)
        remove_btn = ctk.CTkButton(
            chip_frame,
            text="×",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=("gray70", "gray40"),
            command=lambda: self._remove_chip({"value": value, "frame": chip_frame})
        )
        remove_btn.pack(side="left", padx=(0, 5))

        # Store chip
        chip_data = {"value": value, "frame": chip_frame}
        self._chips.append(chip_data)

    def _remove_chip(self, chip: dict) -> None:
        """Remove a chip from the container.

        Parameters
        ----------
        chip : dict
            Chip data dict with "value" and "frame" keys
        """
        if chip in self._chips:
            # Destroy widget
            chip["frame"].destroy()

            # Remove from internal list
            self._chips.remove(chip)

    def get_values(self) -> list[str]:
        """Get current chip values.

        Returns
        -------
        list[str]
            List of current chip values
        """
        return [chip["value"] for chip in self._chips]

    def set_values(self, values: list[str]) -> None:
        """Set chip values (clears existing chips first).

        Parameters
        ----------
        values : list[str]
            List of values to set as chips
        """
        # Clear existing chips
        self.clear()

        # Add new chips
        for value in values:
            if value and value.strip():
                self._add_chip(value.strip())

    def clear(self) -> None:
        """Remove all chips."""
        # Destroy all chip frames
        for chip in self._chips[:]:  # Use slice to avoid modification during iteration
            chip["frame"].destroy()

        # Clear internal list
        self._chips.clear()
