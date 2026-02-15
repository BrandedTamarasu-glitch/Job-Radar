"""Profile creation and editing form with validation, PDF upload, and dirty tracking.

Provides a complete GUI form for profile setup with:
- Grouped sections for identity, skills/titles, preferences, and filters
- Inline validation on field blur with error messages
- PDF resume upload for auto-fill (optional)
- Dirty tracking with confirmation dialog on cancel
- Edit mode pre-fill from existing profile
- Save via profile_manager.save_profile()
"""

import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog

from job_radar.profile_manager import save_profile, ProfileValidationError
from job_radar.paths import get_data_dir
from job_radar.gui.tag_chip_widget import TagChipWidget


# Validation functions extracted from wizard.py logic
def validate_name(text: str) -> tuple[bool, str]:
    """Validate name field (non-empty).

    Parameters
    ----------
    text : str
        Input text to validate

    Returns
    -------
    tuple[bool, str]
        (is_valid, error_message) - error_message is empty if valid
    """
    if not text.strip():
        return (False, "This field cannot be empty")
    return (True, "")


def validate_years(text: str) -> tuple[bool, str]:
    """Validate years of experience (integer 0-50).

    Parameters
    ----------
    text : str
        Input text to validate

    Returns
    -------
    tuple[bool, str]
        (is_valid, error_message) - error_message is empty if valid
    """
    text = text.strip()
    try:
        years = int(text)
        if years < 0:
            return (False, "Years must be 0 or greater")
        if years > 50:
            return (False, "Please enter a realistic number of years (0-50)")
        return (True, "")
    except ValueError:
        return (False, "Please enter a whole number (e.g., 3, 5, 10)")


def validate_compensation(text: str) -> tuple[bool, str]:
    """Validate compensation floor (optional, but if provided must be valid number).

    Parameters
    ----------
    text : str
        Input text to validate

    Returns
    -------
    tuple[bool, str]
        (is_valid, error_message) - error_message is empty if valid
    """
    text = text.strip()
    if not text:  # Empty is OK (optional field)
        return (True, "")

    # Remove common formatting (commas, dollar signs, 'k')
    cleaned = text.replace(',', '').replace('$', '').strip()

    # Handle 'k' suffix (e.g., "120k" -> "120000")
    if cleaned.lower().endswith('k'):
        try:
            value = float(cleaned[:-1]) * 1000
        except ValueError:
            return (False, "Enter a number (e.g., 120000 or 120k)")
    else:
        try:
            value = float(cleaned)
        except ValueError:
            return (False, "Enter a number (e.g., 120000 or 120k)")

    if value < 0:
        return (False, "Compensation must be positive")
    if value > 1000000:
        return (False, "Please enter a realistic compensation (under $1M)")

    return (True, "")


class ProfileForm(ctk.CTkFrame):
    """Profile create/edit form with validation, PDF upload, and dirty tracking.

    Features:
    - One scrollable page with grouped sections
    - Inline validation on field blur (FocusOut)
    - PDF resume upload for pre-fill (create mode only)
    - Dirty tracking with cancel confirmation
    - Edit mode pre-fill from existing profile dict
    - Save via profile_manager.save_profile()

    Attributes
    ----------
    _on_save_callback : callable
        Callback invoked on successful save with profile_data dict
    _on_cancel_callback : callable
        Callback invoked on cancel
    _existing_profile : dict | None
        Existing profile for edit mode (None = create mode)
    _original_values : dict
        Snapshot of form values at load time for dirty tracking
    _current_view : str
        Current view state: "upload_choice" | "form"
    """

    def __init__(
        self,
        parent,
        on_save_callback,
        on_cancel_callback,
        existing_profile: dict | None = None,
        **kwargs
    ):
        """Initialize the ProfileForm.

        Parameters
        ----------
        parent
            Parent widget
        on_save_callback : callable
            Callback(profile_data: dict) invoked when user saves successfully
        on_cancel_callback : callable
            Callback() invoked when user cancels
        existing_profile : dict | None, optional
            Existing profile dict for edit mode (None = create mode)
        **kwargs
            Additional arguments passed to CTkFrame
        """
        super().__init__(parent, **kwargs)

        self._on_save_callback = on_save_callback
        self._on_cancel_callback = on_cancel_callback
        self._existing_profile = existing_profile
        self._original_values = {}

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Container for current view (upload choice or form)
        self._content_container = ctk.CTkFrame(self, fg_color="transparent")
        self._content_container.grid(row=0, column=0, sticky="nsew")
        # Allow horizontal expansion only (no row weight - prevents click blocking)
        self._content_container.grid_columnconfigure(0, weight=1)

        # Determine initial view
        if existing_profile is None:
            # Create mode - show upload choice first
            self._current_view = "upload_choice"
            self._show_upload_choice()
        else:
            # Edit mode - go straight to form
            self._current_view = "form"
            self._show_form()

    def _show_upload_choice(self) -> None:
        """Display upload choice view: Upload PDF or Fill Manually."""
        # Clear container
        for widget in self._content_container.winfo_children():
            widget.destroy()

        # Center content frame
        content_frame = ctk.CTkFrame(self._content_container, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        # Title
        title = ctk.CTkLabel(
            content_frame,
            text="Create Your Profile",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))

        # Description
        desc = ctk.CTkLabel(
            content_frame,
            text="Upload your resume PDF to auto-fill fields, or fill manually.",
            wraplength=400,
            justify="center"
        )
        desc.pack(pady=(0, 30))

        # Upload Resume PDF button
        upload_btn = ctk.CTkButton(
            content_frame,
            text="Upload Resume PDF",
            height=40,
            width=200,
            command=self._on_upload_pdf
        )
        upload_btn.pack(pady=(0, 15))

        # Fill Manually button
        manual_btn = ctk.CTkButton(
            content_frame,
            text="Fill Manually",
            height=40,
            width=200,
            command=self._show_form,
            fg_color="transparent",
            border_width=2
        )
        manual_btn.pack()

    def _on_upload_pdf(self) -> None:
        """Handle Upload Resume PDF button click."""
        # Open file dialog
        pdf_path = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not pdf_path:
            # User cancelled
            return

        # Try to parse PDF
        try:
            from job_radar.pdf_parser import extract_resume_data, PDFValidationError

            extracted_data = extract_resume_data(pdf_path)

            # Show success message briefly
            self._show_upload_success(extracted_data)

        except PDFValidationError as e:
            # Show error and offer to continue manually
            self._show_upload_error(str(e))

        except Exception as e:
            # Catch-all for unexpected errors
            self._show_upload_error(f"PDF parsing encountered an error: {e}")

    def _show_upload_success(self, extracted_data: dict) -> None:
        """Show brief success message then show form with pre-filled data.

        Parameters
        ----------
        extracted_data : dict
            Extracted data from PDF
        """
        # Store extracted data for form pre-fill
        self._extracted_data = extracted_data

        # Clear container
        for widget in self._content_container.winfo_children():
            widget.destroy()

        # Center content frame
        content_frame = ctk.CTkFrame(self._content_container, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        # Success icon/title
        title = ctk.CTkLabel(
            content_frame,
            text="Resume Parsed Successfully!",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="green"
        )
        title.pack(pady=(0, 15))

        # Note
        note = ctk.CTkLabel(
            content_frame,
            text="Please review - extraction may contain errors",
            wraplength=400,
            justify="center"
        )
        note.pack(pady=(0, 20))

        # Show extracted fields
        if extracted_data:
            fields_label = ctk.CTkLabel(
                content_frame,
                text="Extracted fields:\n" + "\n".join(f"  • {key}" for key in extracted_data),
                justify="left"
            )
            fields_label.pack(pady=(0, 30))

        # Continue button
        continue_btn = ctk.CTkButton(
            content_frame,
            text="Continue to Form",
            height=40,
            width=200,
            command=self._show_form
        )
        continue_btn.pack()

    def _show_upload_error(self, error_message: str) -> None:
        """Show error message and offer to continue manually.

        Parameters
        ----------
        error_message : str
            Error message to display
        """
        # Clear container
        for widget in self._content_container.winfo_children():
            widget.destroy()

        # Center content frame
        content_frame = ctk.CTkFrame(self._content_container, fg_color="transparent")
        content_frame.grid(row=0, column=0)

        # Error title
        title = ctk.CTkLabel(
            content_frame,
            text="Upload Failed",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="red"
        )
        title.pack(pady=(0, 15))

        # Error message
        error_label = ctk.CTkLabel(
            content_frame,
            text=error_message,
            wraplength=400,
            justify="center"
        )
        error_label.pack(pady=(0, 30))

        # Continue Manually button
        continue_btn = ctk.CTkButton(
            content_frame,
            text="Fill Manually",
            height=40,
            width=200,
            command=self._show_form
        )
        continue_btn.pack(pady=(0, 10))

        # Back button
        back_btn = ctk.CTkButton(
            content_frame,
            text="Back",
            height=35,
            width=150,
            command=self._show_upload_choice,
            fg_color="transparent",
            border_width=2
        )
        back_btn.pack()

    def _show_form(self) -> None:
        """Display the profile form with all fields."""
        # Clear container
        for widget in self._content_container.winfo_children():
            widget.destroy()

        self._current_view = "form"

        # Create scrollable form frame
        form_frame = ctk.CTkScrollableFrame(self._content_container)
        form_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Linux mouse wheel scrolling fix — CTkScrollableFrame may not bind
        # Button-4/Button-5 (X11 scroll events) on all platforms
        import sys
        if sys.platform == "linux":
            def _on_linux_scroll(event):
                canvas = form_frame._parent_canvas
                if event.num == 4:
                    canvas.yview_scroll(-3, "units")
                elif event.num == 5:
                    canvas.yview_scroll(3, "units")
            form_frame.bind_all("<Button-4>", _on_linux_scroll)
            form_frame.bind_all("<Button-5>", _on_linux_scroll)

        # Store field references for validation and value extraction
        self._fields = {}
        self._error_labels = {}

        # --- Identity Section ---
        self._add_section_header(form_frame, "Identity")

        # Name field
        name_label = ctk.CTkLabel(form_frame, text="Name:", anchor="w")
        name_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["name"] = ctk.CTkEntry(form_frame, placeholder_text="e.g., John Doe")
        self._fields["name"].pack(fill="x", padx=10, pady=(5, 0))
        self._fields["name"].bind("<FocusOut>", lambda e: self._validate_field("name"))

        self._error_labels["name"] = ctk.CTkLabel(
            form_frame, text="", text_color="red", anchor="w"
        )
        self._error_labels["name"].pack(fill="x", padx=10, pady=(2, 0))

        # Years of Experience field
        years_label = ctk.CTkLabel(form_frame, text="Years of Experience:", anchor="w")
        years_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["years_experience"] = ctk.CTkEntry(
            form_frame, placeholder_text="e.g., 3, 5, 10"
        )
        self._fields["years_experience"].pack(fill="x", padx=10, pady=(5, 0))
        self._fields["years_experience"].bind(
            "<FocusOut>", lambda e: self._validate_field("years_experience")
        )

        self._error_labels["years_experience"] = ctk.CTkLabel(
            form_frame, text="", text_color="red", anchor="w"
        )
        self._error_labels["years_experience"].pack(fill="x", padx=10, pady=(2, 0))

        # --- Skills & Titles Section ---
        self._add_section_header(form_frame, "Skills & Titles")

        # Target Titles
        titles_label = ctk.CTkLabel(
            form_frame, text="Target Titles (required):", anchor="w"
        )
        titles_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["target_titles"] = TagChipWidget(
            form_frame, placeholder="e.g., Software Engineer, Full Stack Developer"
        )
        self._fields["target_titles"].pack(fill="x", padx=10, pady=(5, 0))

        self._error_labels["target_titles"] = ctk.CTkLabel(
            form_frame, text="", text_color="red", anchor="w"
        )
        self._error_labels["target_titles"].pack(fill="x", padx=10, pady=(2, 0))

        # Core Skills
        skills_label = ctk.CTkLabel(
            form_frame, text="Core Skills (required):", anchor="w"
        )
        skills_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["core_skills"] = TagChipWidget(
            form_frame, placeholder="e.g., Python, JavaScript, React, AWS"
        )
        self._fields["core_skills"].pack(fill="x", padx=10, pady=(5, 0))

        self._error_labels["core_skills"] = ctk.CTkLabel(
            form_frame, text="", text_color="red", anchor="w"
        )
        self._error_labels["core_skills"].pack(fill="x", padx=10, pady=(2, 0))

        # Secondary Skills (optional)
        secondary_label = ctk.CTkLabel(
            form_frame, text="Secondary Skills (optional):", anchor="w"
        )
        secondary_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["secondary_skills"] = TagChipWidget(
            form_frame, placeholder="Additional skills"
        )
        self._fields["secondary_skills"].pack(fill="x", padx=10, pady=(5, 0))

        # --- Preferences Section ---
        self._add_section_header(form_frame, "Preferences")

        # Location (optional)
        location_label = ctk.CTkLabel(
            form_frame, text="Location (optional):", anchor="w"
        )
        location_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["location"] = ctk.CTkEntry(
            form_frame, placeholder_text="e.g., Remote, New York, Boston area"
        )
        self._fields["location"].pack(fill="x", padx=10, pady=(5, 0))

        # Work Arrangement (optional)
        arrangement_label = ctk.CTkLabel(
            form_frame, text="Work Arrangement (optional):", anchor="w"
        )
        arrangement_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["arrangement"] = TagChipWidget(
            form_frame, placeholder="e.g., Remote, Hybrid, On-site"
        )
        self._fields["arrangement"].pack(fill="x", padx=10, pady=(5, 0))

        # Domain Expertise (optional)
        domain_label = ctk.CTkLabel(
            form_frame, text="Domain Expertise (optional):", anchor="w"
        )
        domain_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["domain_expertise"] = TagChipWidget(
            form_frame, placeholder="e.g., Healthcare, Fintech, E-commerce"
        )
        self._fields["domain_expertise"].pack(fill="x", padx=10, pady=(5, 0))

        # Compensation Floor (optional)
        comp_label = ctk.CTkLabel(
            form_frame, text="Minimum Compensation (optional):", anchor="w"
        )
        comp_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["comp_floor"] = ctk.CTkEntry(
            form_frame, placeholder_text="e.g., 120000, 150k"
        )
        self._fields["comp_floor"].pack(fill="x", padx=10, pady=(5, 0))
        self._fields["comp_floor"].bind(
            "<FocusOut>", lambda e: self._validate_field("comp_floor")
        )

        self._error_labels["comp_floor"] = ctk.CTkLabel(
            form_frame, text="", text_color="red", anchor="w"
        )
        self._error_labels["comp_floor"].pack(fill="x", padx=10, pady=(2, 0))

        # --- Filters Section ---
        self._add_section_header(form_frame, "Filters")

        # Dealbreakers (optional)
        dealbreakers_label = ctk.CTkLabel(
            form_frame, text="Dealbreakers (optional):", anchor="w"
        )
        dealbreakers_label.pack(fill="x", padx=10, pady=(10, 0))

        self._fields["dealbreakers"] = TagChipWidget(
            form_frame, placeholder="e.g., relocation required, on-site only"
        )
        self._fields["dealbreakers"].pack(fill="x", padx=10, pady=(5, 0))

        # --- Button Row ---
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(30, 10))

        # Cancel button (left)
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            height=40,
            width=150,
            command=self._on_cancel,
            fg_color="transparent",
            border_width=2
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        # Save button (right)
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Profile",
            height=40,
            width=150,
            command=self._on_save
        )
        save_btn.pack(side="right")

        # Pre-fill form if in edit mode or PDF data available
        self._prefill_form()

        # Capture original values for dirty tracking
        self._capture_original_values()

    def _add_section_header(self, parent, title: str) -> None:
        """Add a section header to the form.

        Parameters
        ----------
        parent
            Parent widget
        title : str
            Section title text
        """
        header = ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=10, pady=(20, 5))

    def _prefill_form(self) -> None:
        """Pre-fill form fields from existing profile or extracted PDF data."""
        # Edit mode - pre-fill from existing profile
        if self._existing_profile:
            profile = self._existing_profile

            self._fields["name"].insert(0, profile.get("name", ""))
            self._fields["years_experience"].insert(
                0, str(profile.get("years_experience", ""))
            )
            self._fields["target_titles"].set_values(profile.get("target_titles", []))
            self._fields["core_skills"].set_values(profile.get("core_skills", []))

            if "secondary_skills" in profile:
                self._fields["secondary_skills"].set_values(profile["secondary_skills"])

            if "location" in profile:
                self._fields["location"].insert(0, profile["location"])

            if "arrangement" in profile:
                self._fields["arrangement"].set_values(profile["arrangement"])

            if "domain_expertise" in profile:
                self._fields["domain_expertise"].set_values(profile["domain_expertise"])

            if "comp_floor" in profile:
                self._fields["comp_floor"].insert(0, str(profile["comp_floor"]))

            if "dealbreakers" in profile:
                self._fields["dealbreakers"].set_values(profile["dealbreakers"])

        # Create mode with PDF data - pre-fill from extracted data
        elif hasattr(self, "_extracted_data"):
            extracted = self._extracted_data

            if "name" in extracted:
                self._fields["name"].insert(0, extracted["name"])

            if "years_experience" in extracted:
                self._fields["years_experience"].insert(
                    0, str(extracted["years_experience"])
                )

            if "titles" in extracted:
                self._fields["target_titles"].set_values(extracted["titles"])

            if "skills" in extracted:
                self._fields["core_skills"].set_values(extracted["skills"])

    def _capture_original_values(self) -> None:
        """Capture current form values as original snapshot for dirty tracking."""
        self._original_values = {
            "name": self._fields["name"].get(),
            "years_experience": self._fields["years_experience"].get(),
            "target_titles": self._fields["target_titles"].get_values(),
            "core_skills": self._fields["core_skills"].get_values(),
            "secondary_skills": self._fields["secondary_skills"].get_values(),
            "location": self._fields["location"].get(),
            "arrangement": self._fields["arrangement"].get_values(),
            "domain_expertise": self._fields["domain_expertise"].get_values(),
            "comp_floor": self._fields["comp_floor"].get(),
            "dealbreakers": self._fields["dealbreakers"].get_values(),
        }

    def _validate_field(self, field_name: str) -> bool:
        """Validate a single field and show/hide error message.

        Parameters
        ----------
        field_name : str
            Field name to validate

        Returns
        -------
        bool
            True if valid, False otherwise
        """
        if field_name == "name":
            value = self._fields["name"].get()
            is_valid, error_msg = validate_name(value)
            self._error_labels["name"].configure(text=error_msg)
            return is_valid

        elif field_name == "years_experience":
            value = self._fields["years_experience"].get()
            is_valid, error_msg = validate_years(value)
            self._error_labels["years_experience"].configure(text=error_msg)
            return is_valid

        elif field_name == "comp_floor":
            value = self._fields["comp_floor"].get()
            is_valid, error_msg = validate_compensation(value)
            self._error_labels["comp_floor"].configure(text=error_msg)
            return is_valid

        return True

    def _validate_all_fields(self) -> bool:
        """Validate all fields and focus first invalid field.

        Returns
        -------
        bool
            True if all fields valid, False otherwise
        """
        all_valid = True
        first_invalid_field = None

        # Validate text fields
        for field_name in ["name", "years_experience", "comp_floor"]:
            if not self._validate_field(field_name):
                all_valid = False
                if first_invalid_field is None:
                    first_invalid_field = self._fields[field_name]

        # Validate required TagChipWidgets (target_titles, core_skills)
        if not self._fields["target_titles"].get_values():
            self._error_labels["target_titles"].configure(
                text="Please enter at least 1 target title"
            )
            all_valid = False
            if first_invalid_field is None:
                first_invalid_field = self._fields["target_titles"]
        else:
            self._error_labels["target_titles"].configure(text="")

        if not self._fields["core_skills"].get_values():
            self._error_labels["core_skills"].configure(
                text="Please enter at least 1 core skill"
            )
            all_valid = False
            if first_invalid_field is None:
                first_invalid_field = self._fields["core_skills"]
        else:
            self._error_labels["core_skills"].configure(text="")

        # Focus first invalid field
        if first_invalid_field:
            first_invalid_field.focus_set()

        return all_valid

    def _on_save(self) -> None:
        """Handle Save button click."""
        # Validate all fields
        if not self._validate_all_fields():
            return

        # Build profile data dict
        try:
            profile_data = self._build_profile_data()
        except Exception as e:
            # Show error in form (not a dialog)
            error_label = ctk.CTkLabel(
                self,
                text=f"Error building profile: {e}",
                text_color="red"
            )
            error_label.grid(row=1, column=0, pady=10)
            return

        # Save profile via profile_manager
        try:
            profile_path = get_data_dir() / "profile.json"
            save_profile(profile_data, profile_path)

            # Invoke success callback
            self._on_save_callback(profile_data)

        except ProfileValidationError as e:
            # Show validation error in form
            error_label = ctk.CTkLabel(
                self,
                text=f"Validation error: {e.message}",
                text_color="red"
            )
            error_label.grid(row=1, column=0, pady=10)

    def _build_profile_data(self) -> dict:
        """Build profile data dict from form values.

        Returns
        -------
        dict
            Profile data dict matching wizard.py output structure
        """
        # Extract values
        name = self._fields["name"].get().strip()
        years_experience = int(self._fields["years_experience"].get().strip())
        target_titles = self._fields["target_titles"].get_values()
        core_skills = self._fields["core_skills"].get_values()

        # Derive level from years_experience (same logic as wizard.py)
        if years_experience < 2:
            level = "junior"
        elif years_experience < 5:
            level = "mid"
        elif years_experience < 10:
            level = "senior"
        else:
            level = "principal"

        # Build base profile
        profile_data = {
            "name": name,
            "years_experience": years_experience,
            "level": level,
            "target_titles": target_titles,
            "core_skills": core_skills,
        }

        # Optional fields - only include if non-empty
        secondary_skills = self._fields["secondary_skills"].get_values()
        if secondary_skills:
            profile_data["secondary_skills"] = secondary_skills

        location = self._fields["location"].get().strip()
        if location:
            profile_data["location"] = location

        arrangement = self._fields["arrangement"].get_values()
        if arrangement:
            # Normalize to lowercase (matches wizard behavior)
            profile_data["arrangement"] = [a.lower() for a in arrangement]

        domain_expertise = self._fields["domain_expertise"].get_values()
        if domain_expertise:
            profile_data["domain_expertise"] = domain_expertise

        comp_floor_text = self._fields["comp_floor"].get().strip()
        if comp_floor_text:
            # Parse compensation (handle $, commas, k suffix)
            cleaned = comp_floor_text.replace(',', '').replace('$', '').strip()
            if cleaned.lower().endswith('k'):
                comp_value = int(float(cleaned[:-1]) * 1000)
            else:
                comp_value = int(float(cleaned))
            profile_data["comp_floor"] = comp_value

        dealbreakers = self._fields["dealbreakers"].get_values()
        if dealbreakers:
            profile_data["dealbreakers"] = dealbreakers

        return profile_data

    def _on_cancel(self) -> None:
        """Handle Cancel button click with dirty tracking."""
        if self._is_dirty():
            # Show confirmation dialog
            if self._confirm_discard_changes():
                self._on_cancel_callback()
        else:
            # Clean - cancel immediately
            self._on_cancel_callback()

    def _is_dirty(self) -> bool:
        """Check if form values differ from original snapshot.

        Returns
        -------
        bool
            True if form has unsaved changes, False otherwise
        """
        current_values = {
            "name": self._fields["name"].get(),
            "years_experience": self._fields["years_experience"].get(),
            "target_titles": self._fields["target_titles"].get_values(),
            "core_skills": self._fields["core_skills"].get_values(),
            "secondary_skills": self._fields["secondary_skills"].get_values(),
            "location": self._fields["location"].get(),
            "arrangement": self._fields["arrangement"].get_values(),
            "domain_expertise": self._fields["domain_expertise"].get_values(),
            "comp_floor": self._fields["comp_floor"].get(),
            "dealbreakers": self._fields["dealbreakers"].get_values(),
        }

        return current_values != self._original_values

    def _confirm_discard_changes(self) -> bool:
        """Show confirmation dialog for discarding changes.

        Returns
        -------
        bool
            True if user confirms, False otherwise
        """
        # Create modal dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Discard Changes?")
        dialog.geometry("350x150")

        # Make modal
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Track user choice
        user_choice = {"confirm": False}

        # Message
        message = ctk.CTkLabel(
            dialog,
            text="You have unsaved changes.\nDiscard them?",
            wraplength=300,
            font=ctk.CTkFont(size=13)
        )
        message.pack(pady=20, padx=20)

        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=(0, 10))

        # Cancel button (keep editing)
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Keep Editing",
            width=120,
            command=lambda: self._close_dialog(dialog, user_choice, False),
            fg_color="transparent",
            border_width=2
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        # Discard button
        discard_btn = ctk.CTkButton(
            button_frame,
            text="Discard",
            width=120,
            command=lambda: self._close_dialog(dialog, user_choice, True),
            fg_color="red",
            hover_color="darkred"
        )
        discard_btn.pack(side="left")

        # Wait for dialog to close
        dialog.wait_window()

        return user_choice["confirm"]

    def _close_dialog(self, dialog, user_choice: dict, confirm: bool) -> None:
        """Close confirmation dialog and set user choice.

        Parameters
        ----------
        dialog
            Dialog window to close
        user_choice : dict
            Dict to store user choice
        confirm : bool
            User's choice (True = discard, False = keep editing)
        """
        user_choice["confirm"] = confirm
        dialog.destroy()
