"""Search controls widget for job search configuration.

Provides date range filtering, minimum score threshold, and new-only mode toggle.
Date filter is opt-in (checkbox) to match CLI default behavior (no date filter).
"""

import re
from typing import Optional

import customtkinter as ctk

from job_radar.config import load_config


# Try to import CTkDatePicker, fall back to manual entry if unavailable
try:
    from tkcalendar import DateEntry
    HAS_DATE_PICKER = True
except ImportError:
    HAS_DATE_PICKER = False


class SearchControls(ctk.CTkFrame):
    """Search configuration widget with date pickers, min score, and new-only toggle.

    Provides search parameters via get_config() API. Validates inputs and loads
    defaults from config.json. Date filter is opt-in (unchecked by default) to
    match CLI behavior of no --from/--to flags.
    """

    def __init__(self, parent, **kwargs):
        """Initialize search controls widget.

        Args:
            parent: Parent widget
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(parent, **kwargs)

        # Load config defaults
        self._config = load_config()

        # Validation state
        self._score_error_label = None

        # Build layout
        self._create_widgets()
        self._set_default_values()

    def _create_widgets(self):
        """Create and layout all control widgets."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # Date range section
        date_section = ctk.CTkFrame(self, fg_color="transparent")
        date_section.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        date_section.grid_columnconfigure(1, weight=1)

        # Date filter checkbox
        self._date_enabled = ctk.CTkCheckBox(
            date_section,
            text="Apply date filter",
            command=self._toggle_date_filter
        )
        self._date_enabled.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # From date
        ctk.CTkLabel(date_section, text="From:").grid(row=1, column=0, sticky="w", padx=(20, 10))
        self._from_date = ctk.CTkEntry(
            date_section,
            placeholder_text="YYYY-MM-DD",
            state="disabled"
        )
        self._from_date.grid(row=1, column=1, sticky="ew", pady=5)

        # To date
        ctk.CTkLabel(date_section, text="To:").grid(row=2, column=0, sticky="w", padx=(20, 10))
        self._to_date = ctk.CTkEntry(
            date_section,
            placeholder_text="YYYY-MM-DD",
            state="disabled"
        )
        self._to_date.grid(row=2, column=1, sticky="ew", pady=5)

        # Min score section
        score_section = ctk.CTkFrame(self, fg_color="transparent")
        score_section.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        score_section.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(score_section, text="Minimum Score:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self._min_score = ctk.CTkEntry(score_section, width=100)
        self._min_score.grid(row=0, column=1, sticky="w")
        self._min_score.bind("<FocusOut>", self._validate_score)

        # Score error label (hidden initially)
        self._score_error_label = ctk.CTkLabel(
            score_section,
            text="",
            text_color="red",
            font=ctk.CTkFont(size=11)
        )
        self._score_error_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # New only section
        new_section = ctk.CTkFrame(self, fg_color="transparent")
        new_section.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        self._new_only = ctk.CTkSwitch(new_section, text="New jobs only")
        self._new_only.pack(anchor="w")

    def _set_default_values(self):
        """Set default values from config.json or fallback defaults."""
        # Min score: config > 2.8 fallback
        min_score = self._config.get("min_score", 2.8)
        self._min_score.delete(0, "end")
        self._min_score.insert(0, str(min_score))

        # New only: config > False fallback
        new_only = self._config.get("new_only", False)
        if new_only:
            self._new_only.select()
        else:
            self._new_only.deselect()

        # Date filter: unchecked by default (matches CLI behavior)
        self._date_enabled.deselect()

    def _toggle_date_filter(self):
        """Enable/disable date entry fields based on checkbox state."""
        if self._date_enabled.get():
            self._from_date.configure(state="normal")
            self._to_date.configure(state="normal")
        else:
            self._from_date.configure(state="disabled")
            self._to_date.configure(state="disabled")

    def _validate_score(self, event=None):
        """Validate min_score on FocusOut event.

        Checks that value is a float in range 0.0-5.0. Displays inline error
        if invalid. Follows same validation pattern as ProfileForm.
        """
        value = self._min_score.get().strip()

        # Clear previous error
        self._score_error_label.configure(text="")

        if not value:
            self._score_error_label.configure(text="Score is required")
            return False

        try:
            score = float(value)
            if score < 0.0 or score > 5.0:
                self._score_error_label.configure(text="Score must be between 0.0 and 5.0")
                return False
        except ValueError:
            self._score_error_label.configure(text="Score must be a number")
            return False

        return True

    def validate(self) -> tuple[bool, str]:
        """Validate all controls.

        Returns:
            Tuple of (is_valid, error_message). error_message is empty if valid.
        """
        # Validate min score
        if not self._validate_score():
            return False, "Invalid minimum score"

        # Validate date format if date filter is enabled
        if self._date_enabled.get():
            from_date = self._from_date.get().strip()
            to_date = self._to_date.get().strip()

            date_pattern = r"^\d{4}-\d{2}-\d{2}$"

            if from_date and not re.match(date_pattern, from_date):
                return False, "From date must be in YYYY-MM-DD format"

            if to_date and not re.match(date_pattern, to_date):
                return False, "To date must be in YYYY-MM-DD format"

        return True, ""

    def get_config(self) -> dict:
        """Get current search configuration.

        Returns:
            Dict with keys:
                - from_date: str|None (None if date filter disabled or empty)
                - to_date: str|None (None if date filter disabled or empty)
                - min_score: float
                - new_only: bool
        """
        # Date filter: None if checkbox unchecked
        if self._date_enabled.get():
            from_date = self._from_date.get().strip() or None
            to_date = self._to_date.get().strip() or None
        else:
            from_date = None
            to_date = None

        # Min score: always present (validated)
        min_score = float(self._min_score.get().strip())

        # New only: boolean
        new_only = self._new_only.get() == 1

        return {
            "from_date": from_date,
            "to_date": to_date,
            "min_score": min_score,
            "new_only": new_only
        }

    def set_defaults(self, config: dict):
        """Set control values from a config dict.

        Args:
            config: Dict with optional keys: from_date, to_date, min_score, new_only
        """
        if "min_score" in config:
            self._min_score.delete(0, "end")
            self._min_score.insert(0, str(config["min_score"]))

        if "new_only" in config:
            if config["new_only"]:
                self._new_only.select()
            else:
                self._new_only.deselect()

        if "from_date" in config and config["from_date"]:
            self._date_enabled.select()
            self._toggle_date_filter()
            self._from_date.delete(0, "end")
            self._from_date.insert(0, config["from_date"])

        if "to_date" in config and config["to_date"]:
            self._date_enabled.select()
            self._toggle_date_filter()
            self._to_date.delete(0, "end")
            self._to_date.insert(0, config["to_date"])
