"""Scoring configuration widget for customizing job scoring weights and staffing preference.

Provides interactive sliders for 6 scoring components, staffing preference dropdown,
live score preview, and validation with normalize/reset helpers.
"""

from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

from job_radar.profile_manager import (
    DEFAULT_SCORING_WEIGHTS,
    save_profile,
    load_profile,
    ProfileValidationError,
)
from job_radar.paths import get_data_dir

# Sample component scores for live preview (well-matched job example)
SAMPLE_SCORES = {
    "skill_match": 4.5,
    "title_relevance": 4.0,
    "seniority": 3.8,
    "location": 5.0,
    "domain": 3.5,
    "response_likelihood": 3.2,
}

# Staffing preference mappings
STAFFING_DISPLAY_MAP = {
    "Boost (+0.5)": "boost",
    "Neutral (no change)": "neutral",
    "Penalize (-1.0)": "penalize",
}

STAFFING_INTERNAL_MAP = {
    "boost": "Boost (+0.5)",
    "neutral": "Neutral (no change)",
    "penalize": "Penalize (-1.0)",
}


def normalize_weights(weights):
    """Proportionally adjust weights to sum to 1.0.

    Args:
        weights: Dict of component -> weight value

    Returns:
        Dict with normalized weights (rounded to 2 decimals)
    """
    total = sum(weights.values())

    if total == 0:
        # Avoid division by zero - set all to equal weight
        n = len(weights)
        return {k: round(1.0 / n, 2) for k in weights}

    # Proportionally scale each weight
    return {k: round(v / total, 2) for k, v in weights.items()}


def validate_weights(weights, tolerance=0.01, min_value=0.05):
    """Validate that weights sum to 1.0 and meet minimum threshold.

    Args:
        weights: Dict of component -> weight value
        tolerance: Allowed deviation from 1.0 (default 0.01)
        min_value: Minimum value per component (default 0.05)

    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    total = sum(weights.values())

    # Check sum to 1.0
    if abs(total - 1.0) > tolerance:
        return False, f"Weights must sum to 1.0 (currently {total:.3f})"

    # Check minimum per component
    for key, value in weights.items():
        if value < min_value:
            display_name = key.replace("_", " ").title()
            return False, f"{display_name} must be at least {min_value} (currently {value:.2f})"

    return True, None


class ScoringConfigWidget(ctk.CTkFrame):
    """Self-contained widget for configuring scoring weights and staffing preference.

    Features:
    - 6 sliders for weight components (0.05-1.0 range, enforces min 0.05)
    - Staffing preference dropdown (Boost/Neutral/Penalize)
    - Live preview showing sample job score calculation
    - Normalize button (auto-adjusts to sum to 1.0)
    - Reset button (restore defaults with confirmation)
    - Save button (validates and persists to profile)
    - Sum-to-1.0 validation (inline warning during editing, blocking on save)
    - Collapsible section (toggle visibility)
    """

    def __init__(self, parent, profile=None, on_save_callback=None, **kwargs):
        """Initialize scoring configuration widget.

        Args:
            parent: Parent widget
            profile: Optional profile dict to initialize from
            on_save_callback: Optional callback to invoke after successful save
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(parent, **kwargs)

        self._on_save_callback = on_save_callback
        self._is_expanded = True

        # Use module-level staffing preference mappings
        self._staffing_display_to_internal = STAFFING_DISPLAY_MAP
        self._staffing_internal_to_display = STAFFING_INTERNAL_MAP

        # Widget references
        self._sliders = {}
        self._value_labels = {}
        self._staffing_dropdown = None
        self._validation_label = None
        self._preview_label = None
        self._save_status_label = None
        self._content_frame = None
        self._header_button = None

        # Build UI
        self._create_widgets()

        # Initialize from profile or defaults
        if profile:
            self.load_from_profile(profile)
        else:
            self._initialize_defaults()
            self._update_preview()

    def _create_widgets(self):
        """Create and layout all UI components."""
        # Configure main grid
        self.grid_columnconfigure(0, weight=1)

        # Collapsible header button
        self._header_button = ctk.CTkButton(
            self,
            text="▼ Scoring Configuration",
            command=self.toggle,
            fg_color="transparent",
            hover_color=("gray90", "gray20"),
            anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self._header_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Content frame (contains all controls)
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Two-column layout: 60% controls, 40% preview
        self._content_frame.grid_columnconfigure(0, weight=3)
        self._content_frame.grid_columnconfigure(1, weight=2)

        # Build left panel (controls)
        self._build_controls_panel()

        # Build right panel (preview)
        self._build_preview_panel()

    def _build_controls_panel(self):
        """Build left panel with sliders, dropdown, validation, and action buttons."""
        left_panel = ctk.CTkFrame(self._content_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        left_panel.grid_columnconfigure(0, weight=1)

        row = 0

        # Skills & Fit group
        skills_label = ctk.CTkLabel(
            left_panel,
            text="Skills & Fit",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        skills_label.grid(row=row, column=0, sticky="w", padx=10, pady=(10, 5))
        row += 1

        help_skills = ctk.CTkLabel(
            left_panel,
            text="How much weight to give your skills and experience match",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        help_skills.grid(row=row, column=0, sticky="w", padx=10, pady=(0, 10))
        row += 1

        # Skill match slider
        row = self._add_slider_row(left_panel, row, "skill_match", "Skill Match")

        # Title relevance slider
        row = self._add_slider_row(left_panel, row, "title_relevance", "Title Relevance")

        # Seniority slider
        row = self._add_slider_row(left_panel, row, "seniority", "Seniority")

        # Domain slider
        row = self._add_slider_row(left_panel, row, "domain", "Domain")

        # Context group
        context_label = ctk.CTkLabel(
            left_panel,
            text="Context",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        context_label.grid(row=row, column=0, sticky="w", padx=10, pady=(15, 5))
        row += 1

        help_context = ctk.CTkLabel(
            left_panel,
            text="How much weight to give location and response factors",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        help_context.grid(row=row, column=0, sticky="w", padx=10, pady=(0, 10))
        row += 1

        # Location slider
        row = self._add_slider_row(left_panel, row, "location", "Location")

        # Response likelihood slider
        row = self._add_slider_row(left_panel, row, "response_likelihood", "Response Likelihood")

        # Staffing preference dropdown
        staffing_label = ctk.CTkLabel(
            left_panel,
            text="Staffing Firm Preference:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        staffing_label.grid(row=row, column=0, sticky="w", padx=10, pady=(15, 5))
        row += 1

        staffing_help = ctk.CTkLabel(
            left_panel,
            text="Applied after scoring: boost favors, penalize discourages staffing firm jobs",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        staffing_help.grid(row=row, column=0, sticky="w", padx=10, pady=(0, 5))
        row += 1

        self._staffing_dropdown = ctk.CTkOptionMenu(
            left_panel,
            values=list(self._staffing_display_to_internal.keys()),
            command=self._on_staffing_changed,
        )
        self._staffing_dropdown.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 10))
        row += 1

        # Validation warning label (inline, non-blocking)
        self._validation_label = ctk.CTkLabel(
            left_panel,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="orange",
        )
        self._validation_label.grid(row=row, column=0, sticky="w", padx=10, pady=(5, 10))
        row += 1

        # Action buttons (horizontal row)
        button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=(10, 5))
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        normalize_btn = ctk.CTkButton(
            button_frame,
            text="Normalize",
            command=self._normalize_weights,
        )
        normalize_btn.grid(row=0, column=0, padx=5)

        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
            width=170,
        )
        reset_btn.grid(row=0, column=1, padx=5)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._save_scoring_config,
        )
        save_btn.grid(row=0, column=2, padx=5)
        row += 1

        # Save status label (shows "Saved!" feedback)
        self._save_status_label = ctk.CTkLabel(
            left_panel,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="green",
        )
        self._save_status_label.grid(row=row, column=0, sticky="w", padx=10, pady=(5, 0))

    def _add_slider_row(self, parent, row, key, label_text):
        """Add a slider row with label, slider, and value display.

        Args:
            parent: Parent widget
            row: Current grid row
            key: Weight key (e.g., "skill_match")
            label_text: Display label (e.g., "Skill Match")

        Returns:
            Next available row number
        """
        # Container frame for this row
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        row_frame.grid_columnconfigure(1, weight=1)

        # Label
        label = ctk.CTkLabel(row_frame, text=label_text, width=140, anchor="w")
        label.grid(row=0, column=0, sticky="w")

        # Slider (0.05-1.0, 19 steps = 0.05 increments)
        slider = ctk.CTkSlider(
            row_frame,
            from_=0.05,
            to=1.0,
            number_of_steps=19,
            command=lambda v, k=key: self._on_weight_changed(k, v),
        )
        slider.grid(row=0, column=1, sticky="ew", padx=10)
        self._sliders[key] = slider

        # Value display (e.g., "0.25 (25%)")
        value_label = ctk.CTkLabel(row_frame, text="", width=80, anchor="e")
        value_label.grid(row=0, column=2, sticky="e")
        self._value_labels[key] = value_label

        return row + 1

    def _build_preview_panel(self):
        """Build right panel with live score preview."""
        right_panel = ctk.CTkFrame(self._content_frame, fg_color=("gray95", "gray15"))
        right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        right_panel.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            right_panel,
            text="Score Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # Subtitle
        subtitle = ctk.CTkLabel(
            right_panel,
            text="Sample Job: Senior Python Developer",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 5))

        # Description
        desc = ctk.CTkLabel(
            right_panel,
            text="Remote | Python, Django, AWS | 5+ years",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        )
        desc.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 10))

        # Separator
        separator = ctk.CTkFrame(right_panel, height=1, fg_color=("gray80", "gray30"))
        separator.grid(row=3, column=0, sticky="ew", padx=15, pady=5)

        # Preview breakdown (updated dynamically)
        self._preview_label = ctk.CTkLabel(
            right_panel,
            text="",
            font=ctk.CTkFont(size=11, family="Courier"),
            justify="left",
            anchor="nw",
        )
        self._preview_label.grid(row=4, column=0, sticky="nw", padx=15, pady=(5, 15))

    def _initialize_defaults(self):
        """Initialize sliders and dropdown to default values."""
        for key, default_value in DEFAULT_SCORING_WEIGHTS.items():
            if key in self._sliders:
                self._sliders[key].set(default_value)
                self._update_value_label(key, default_value)

        self._staffing_dropdown.set("Neutral (no change)")
        self._check_sum_validation()

    def _on_weight_changed(self, key, value):
        """Callback when a slider moves.

        Args:
            key: Weight key
            value: New slider value
        """
        self._update_value_label(key, value)
        self._check_sum_validation()
        self._update_preview()

    def _update_value_label(self, key, value):
        """Update the value display label for a slider.

        Args:
            key: Weight key
            value: Slider value
        """
        percentage = int(value * 100)
        self._value_labels[key].configure(text=f"{value:.2f} ({percentage}%)")

    def _on_staffing_changed(self, choice):
        """Callback when staffing dropdown changes.

        Args:
            choice: Selected display text
        """
        self._update_preview()

    def _check_sum_validation(self):
        """Check if weights sum to 1.0 and update validation label."""
        total = sum(slider.get() for slider in self._sliders.values())

        # Tolerance of 0.01 for floating point comparison
        if abs(total - 1.0) > 0.01:
            self._validation_label.configure(
                text=f"⚠ Weights sum to {total:.2f} (must equal 1.0). Click Normalize to fix."
            )
        else:
            self._validation_label.configure(text="")

    def _update_preview(self):
        """Recalculate and update the live score preview."""
        # Get current weights
        weights = {key: slider.get() for key, slider in self._sliders.items()}

        # Calculate weighted components
        components = {}
        for key in SAMPLE_SCORES:
            # Map response_likelihood key for weight lookup
            weight_key = key if key != "response_likelihood" else "response_likelihood"
            weight = weights.get(weight_key, DEFAULT_SCORING_WEIGHTS.get(weight_key, 0.0))
            components[key] = SAMPLE_SCORES[key] * weight

        # Overall score (before staffing adjustment)
        overall = sum(components.values())

        # Build preview text
        lines = []

        # Component breakdown
        display_names = {
            "skill_match": "Skill Match",
            "title_relevance": "Title Relevance",
            "seniority": "Seniority",
            "location": "Location",
            "domain": "Domain",
            "response_likelihood": "Response Likelihood",
        }

        for key in SAMPLE_SCORES:
            weight_key = key if key != "response_likelihood" else "response_likelihood"
            weight = weights.get(weight_key, DEFAULT_SCORING_WEIGHTS.get(weight_key, 0.0))
            score = SAMPLE_SCORES[key]
            weighted = components[key]
            name = display_names.get(key, key)
            lines.append(f"{name:20s} {score:.1f} × {weight:.2f} = {weighted:.2f}")

        lines.append("-" * 42)
        lines.append(f"{'Overall Score:':20s} {overall:.2f} / 5.0")

        # Staffing adjustment
        staffing_display = self._staffing_dropdown.get()
        staffing_pref = self._staffing_display_to_internal[staffing_display]

        if staffing_pref == "boost":
            adjusted = min(5.0, overall + 0.5)
            lines.append(f"{'+ Staffing boost:':20s} +0.50")
            lines.append(f"{'Final Score:':20s} {adjusted:.2f} / 5.0")
        elif staffing_pref == "penalize":
            adjusted = max(1.0, overall - 1.0)
            lines.append(f"{'- Staffing penalty:':20s} -1.00")
            lines.append(f"{'Final Score:':20s} {adjusted:.2f} / 5.0")

        self._preview_label.configure(text="\n".join(lines))

    def _normalize_weights(self):
        """Proportionally adjust all weights to sum to 1.0."""
        # Gather current weights
        current_weights = {key: slider.get() for key, slider in self._sliders.items()}

        # Normalize using module function
        normalized = normalize_weights(current_weights)

        # Update sliders with normalized values
        for key, value in normalized.items():
            self._sliders[key].set(value)
            self._update_value_label(key, value)

        self._check_sum_validation()
        self._update_preview()

    def _reset_to_defaults(self):
        """Reset all weights and staffing preference to defaults (with confirmation)."""
        confirm = messagebox.askokcancel(
            "Reset Scoring?",
            "Reset all scoring weights to defaults?",
        )

        if confirm:
            self._initialize_defaults()
            self._update_preview()

    def _save_scoring_config(self):
        """Validate and save scoring configuration to profile."""
        # Clear previous save status
        self._save_status_label.configure(text="")

        # Gather weights (rounded to 2 decimals to avoid float artifacts)
        weights = {
            key: round(slider.get(), 2)
            for key, slider in self._sliders.items()
        }

        # Validate using module function
        is_valid, error_msg = validate_weights(weights)
        if not is_valid:
            messagebox.showerror("Invalid Configuration", error_msg)
            return

        # Get staffing preference
        staffing_display = self._staffing_dropdown.get()
        staffing_pref = self._staffing_display_to_internal[staffing_display]

        # Load profile
        try:
            profile_path = get_data_dir() / "profile.json"
            profile = load_profile(profile_path)
        except Exception as e:
            messagebox.showerror(
                "Load Error",
                f"Failed to load profile: {e}",
            )
            return

        # Update profile
        profile["scoring_weights"] = weights
        profile["staffing_preference"] = staffing_pref

        # Save profile
        try:
            save_profile(profile, profile_path)
        except ProfileValidationError as e:
            messagebox.showerror(
                "Save Error",
                f"Failed to save profile: {e.message}",
            )
            return
        except Exception as e:
            messagebox.showerror(
                "Save Error",
                f"Failed to save profile: {e}",
            )
            return

        # Show success feedback
        self._save_status_label.configure(text="✓ Saved!")
        self.after(2000, lambda: self._save_status_label.configure(text=""))

        # Invoke callback if provided
        if self._on_save_callback:
            self._on_save_callback()

    def toggle(self):
        """Toggle section visibility (expand/collapse)."""
        if self._is_expanded:
            # Collapse
            self._content_frame.grid_forget()
            self._header_button.configure(text="▶ Scoring Configuration")
            self._is_expanded = False
        else:
            # Expand
            self._content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
            self._header_button.configure(text="▼ Scoring Configuration")
            self._is_expanded = True

    def load_from_profile(self, profile):
        """Load weights and staffing preference from profile dict.

        Args:
            profile: Profile dict containing scoring_weights and staffing_preference
        """
        # Load weights
        weights = profile.get("scoring_weights", DEFAULT_SCORING_WEIGHTS)
        for key, value in weights.items():
            if key in self._sliders:
                self._sliders[key].set(value)
                self._update_value_label(key, value)

        # Load staffing preference
        staffing_pref = profile.get("staffing_preference", "neutral")
        staffing_display = self._staffing_internal_to_display.get(
            staffing_pref, "Neutral (no change)"
        )
        self._staffing_dropdown.set(staffing_display)

        # Update validation and preview
        self._check_sum_validation()
        self._update_preview()

    def set_weights(self, weights_dict):
        """Programmatically set weights.

        Args:
            weights_dict: Dict of weight key -> value
        """
        for key, value in weights_dict.items():
            if key in self._sliders:
                self._sliders[key].set(value)
                self._update_value_label(key, value)

        self._check_sum_validation()
        self._update_preview()
