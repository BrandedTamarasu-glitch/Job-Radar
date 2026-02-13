---
phase: 29-profile-setup-search-controls
plan: 01
subsystem: gui
tags: [profile-form, tag-widget, validation, pdf-upload, dirty-tracking]

dependency_graph:
  requires: [profile_manager, pdf_parser, wizard]
  provides: [TagChipWidget, ProfileForm]
  affects: [main_window]

tech_stack:
  added: [tag-chip-widget, profile-form-validation]
  patterns: [blur-validation, dirty-tracking, modal-dialogs]

key_files:
  created:
    - job_radar/gui/tag_chip_widget.py
    - job_radar/gui/profile_form.py
  modified: []

decisions:
  - Reused wizard.py validation logic via extracted functions (validate_name, validate_years, validate_compensation) - zero duplication
  - TagChipWidget uses scrollable container for vertical chip stacking instead of horizontal scroll
  - ProfileForm shows upload choice view in create mode, skips directly to form in edit mode
  - Dirty tracking compares full form snapshot (all fields) against original values at load time
  - Cancel confirmation dialog is modal with transient grab_set() behavior
  - PDF upload errors show dedicated error view with manual fallback option
  - Validation fires on FocusOut for entry fields, on Save for TagChipWidgets
  - Level derived from years_experience using same thresholds as wizard.py (junior<2, mid<5, senior<10, principal>=10)

metrics:
  duration: 195
  completed: 2026-02-13
---

# Phase 29 Plan 01: Tag-Chip Widget and Profile Form

**One-liner:** Reusable tag-chip input widget and complete profile form with inline validation, PDF upload, dirty tracking, and edit mode pre-fill

## Tasks Completed

### Task 1: Create reusable TagChipWidget for list-type form fields

**Status:** Complete
**Commit:** 3467783
**Files:** job_radar/gui/tag_chip_widget.py

Created CustomTkinter widget `TagChipWidget(ctk.CTkFrame)` with:
- Enter-to-add chip behavior (press Enter in entry field)
- X-to-remove chip behavior (click X button on chip)
- Backspace-to-remove-last chip (Backspace on empty entry field)
- Duplicate prevention (case-insensitive comparison)
- Whitespace stripping and empty value rejection
- Scrollable container for vertical chip stacking
- Public API: `get_values()`, `set_values(values)`, `clear()`

Each chip is a small CTkFrame with fg_color for visual distinction, containing a CTkLabel (value text) and CTkButton ("×" remove button) packed side-by-side. Internal state tracks chips as `[{"value": str, "frame": CTkFrame}]` for easy removal by reference.

### Task 2: Create ProfileForm widget with validation, PDF upload, and dirty tracking

**Status:** Complete
**Commit:** e97c14f
**Files:** job_radar/gui/profile_form.py

Created CustomTkinter widget `ProfileForm(ctk.CTkFrame)` with:

**Layout:**
- One scrollable page using CTkScrollableFrame
- Grouped sections with headers: Identity, Skills & Titles, Preferences, Filters
- Fields: Name (entry), Years Experience (entry), Target Titles (TagChipWidget), Core Skills (TagChipWidget), Secondary Skills (TagChipWidget, optional), Location (entry, optional), Work Arrangement (TagChipWidget, optional), Domain Expertise (TagChipWidget, optional), Compensation Floor (entry, optional), Dealbreakers (TagChipWidget, optional)

**Resume PDF upload:**
- Upload choice view shown before form in create mode (Upload Resume PDF vs Fill Manually)
- Upload button opens tkinter.filedialog.askopenfilename with PDF filter
- On successful parse: shows success view with extracted fields list, then pre-fills form
- On parse error: shows error view with message and manual fallback option
- Edit mode skips upload choice entirely and goes straight to form

**Validation:**
- Blur validation (FocusOut event) for entry fields: name, years_experience, comp_floor
- Save validation for required TagChipWidgets: target_titles (>=1), core_skills (>=1)
- Error labels below each field show/hide red error text
- Validation functions extracted from wizard.py logic: `validate_name(text)`, `validate_years(text)`, `validate_compensation(text)`
- On Save: validates all fields, focuses first invalid field if any fail

**Save behavior:**
- Builds profile dict from form values (same structure as wizard.py output)
- Derives level from years_experience (junior/mid/senior/principal using wizard thresholds)
- Calls `profile_manager.save_profile(profile_data, profile_path)` for atomic write with backup
- On success: invokes `on_save_callback(profile_data)`
- On ProfileValidationError: shows error in form (not dialog)

**Edit mode:**
- Constructor parameter `existing_profile` (dict or None)
- Pre-fills all fields using set methods (set_values for TagChipWidgets, insert for entries)
- Skips upload choice view entirely

**Dirty tracking:**
- Captures original values snapshot at form load time via `_capture_original_values()`
- On cancel: compares current values to original using `_is_dirty()`
- If dirty: shows modal confirmation dialog "Discard changes?" with Keep Editing / Discard buttons
- If clean: cancels immediately without dialog
- Dialog uses transient + grab_set for modal behavior

**Integration surface:**
- Imports: `from job_radar.profile_manager import save_profile, ProfileValidationError`
- Imports: `from job_radar.gui.tag_chip_widget import TagChipWidget`
- Imports: `from job_radar.pdf_parser import extract_resume_data, PDFValidationError`
- Imports: `from tkinter import filedialog`

## Verification Results

All verifications passed:

1. Both files compile without syntax errors (py_compile)
2. No circular import issues (both import from job_radar modules, profile_form imports tag_chip_widget)
3. Integration confirmations:
   - `grep -c "from job_radar.profile_manager import"` → 1 (verified)
   - `grep -c "from job_radar.gui.tag_chip_widget import"` → 1 (verified)
   - `grep -c "FocusOut"` → 4 (verified - blur validation on name, years, comp_floor)
   - `grep -c "filedialog"` → 2 (verified - PDF upload integration)

## Deviations from Plan

None - plan executed exactly as written. Both modules follow codebase conventions (module docstrings, type hints, private underscore-prefixed methods, relative imports for job_radar modules).

## Integration Notes

**For Plan 03 (main_window.py integration):**

These modules are self-contained and ready for integration:

1. **Welcome screen "Get Started" button** should instantiate ProfileForm in create mode:
   ```python
   ProfileForm(
       parent=container,
       on_save_callback=self._on_profile_saved,
       on_cancel_callback=self._show_welcome_screen,
       existing_profile=None
   )
   ```

2. **Profile tab "Edit Profile" button** should instantiate ProfileForm in edit mode:
   ```python
   profile = load_profile(profile_path)
   ProfileForm(
       parent=container,
       on_save_callback=self._on_profile_saved,
       on_cancel_callback=self._show_profile_tab,
       existing_profile=profile
   )
   ```

3. **on_save_callback** should navigate to Search tab with success message (per plan requirement)

4. **TagChipWidget** is reusable for any future list-type fields

## Self-Check: PASSED

**Created files verified:**
```
FOUND: /home/corye/Claude/Job-Radar/job_radar/gui/tag_chip_widget.py
FOUND: /home/corye/Claude/Job-Radar/job_radar/gui/profile_form.py
```

**Commits verified:**
```
FOUND: 3467783 (Task 1 - TagChipWidget)
FOUND: e97c14f (Task 2 - ProfileForm)
```

**Key integrations verified:**
- profile_manager.save_profile() integration: ✓
- pdf_parser.extract_resume_data() integration: ✓
- TagChipWidget usage in ProfileForm: ✓
- FocusOut blur validation: ✓ (4 instances)
- filedialog PDF upload: ✓ (2 instances)

All claimed functionality exists and is committed to git.
