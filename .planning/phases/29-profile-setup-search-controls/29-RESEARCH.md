# Phase 29: Profile Setup & Search Controls - Research

**Researched:** 2026-02-13
**Domain:** CustomTkinter GUI forms, file handling, threading integration, search orchestration
**Confidence:** HIGH

## Summary

Phase 29 builds on Phase 28's GUI shell and threading infrastructure to deliver complete feature parity with the CLI. The core challenge is mapping existing CLI business logic (wizard.py validators, profile_manager.py CRUD, sources.py fetch orchestration) into a responsive GUI without code duplication. CustomTkinter provides the widget foundation (CTkEntry, CTkSwitch, file dialogs) but lacks native tag-chip inputs and date pickers — third-party CTkDatePicker fills the gap. The critical architectural pattern is separation: GUI widgets capture input, existing modules validate/execute, worker threads prevent freezing, and queue messages update the UI safely.

The existing codebase already contains all business logic needed: wizard.py has field validators (NonEmptyValidator, ScoreValidator, YearsExperienceValidator, CompensationValidator), profile_manager.py handles atomic saves with backups, pdf_parser.py extracts resume data, and sources.py provides fetch_all() with progress callbacks. Phase 29's job is purely GUI integration — no new business logic required.

**Primary recommendation:** Use existing validators from wizard.py directly via programmatic calls (not questionary prompts), reuse profile_manager save/load for all CRUD, integrate CTkDatePicker for date range controls, implement tag-chip pattern as Entry widget with Enter-key binding that creates/destroys CTkLabel "chips", and wire search execution through existing worker_thread.py pattern replacing MockSearchWorker with real sources.fetch_all().

## User Constraints (from CONTEXT.md)

<user_constraints>
### Locked Decisions

**Profile form layout:**
- Form replaces Profile tab content in-place (same window, same tab) when editing or creating
- Fields organized in grouped sections with headers (e.g., "Identity", "Skills", "Preferences") — one scrollable page
- Resume PDF upload offered as a choice before showing the form: "Upload resume or fill manually?" (mirrors CLI wizard flow)
- List-type fields (skills, titles, dealbreakers) use tag-style chips: type a value, press Enter to add as chip, click X to remove

**Search controls design:**
- Two date picker widgets for From/To date range (calendar popups or spinner-style)
- Default values match current CLI defaults (no date filter, min score from config file)
- "New only" uses a toggle switch (on/off, modern look)
- Run Search button placement and controls layout at Claude's discretion

**Progress & completion flow:**
- Immediate visual feedback: switch to progress view with "Starting search..." before first source name appears
- Enhanced source progress: show source name + job count as each completes (e.g., "Dice: 12 jobs found") building a running tally
- On completion: show "Search complete! X jobs found" with an "Open Report" button — user clicks to open (not auto-open)
- Partial source failures: silent success — open report with whatever succeeded, don't mention failures (consistent with Phase 28 context decision)

**Form validation & editing:**
- Validation fires on field blur (when user leaves a field) — immediate inline feedback per field
- Edit mode accessed via "Edit Profile" button on the profile summary view — switches to form pre-filled with current values
- After saving/creating profile: navigate to Search tab with success message (profile created, ready to search)
- Cancel button with confirmation dialog if fields were modified ("Discard changes?")

### Claude's Discretion

- Search controls layout (above button vs sidebar)
- Date picker widget choice (calendar popup vs spinner — whatever CustomTkinter supports well)
- Exact form section names and field ordering
- Tag chip visual styling
- Success/error message styling
- Window resizing behavior during form display

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| customtkinter | 5.x+ | Modern tkinter widgets with system theme | Already used in Phase 28, provides CTkEntry, CTkButton, CTkSwitch, CTkScrollableFrame |
| tkinter (stdlib) | 3.10+ | File dialogs, event binding, base GUI | Standard library, filedialog.askopenfilename() works with CustomTkinter |
| CTkDatePicker | Latest | Date range picker widgets | Third-party CustomTkinter extension for calendar popups, integrates seamlessly |
| queue (stdlib) | 3.10+ | Thread-safe GUI updates | Already used in Phase 28 worker pattern, mandatory for tkinter threading |
| threading (stdlib) | 3.10+ | Non-blocking search execution | Already used in Phase 28, worker threads + Event-based cancellation |
| webbrowser (stdlib) | 3.10+ | Open HTML reports in default browser | Standard library, cross-platform, file:// URI support |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib (stdlib) | 3.10+ | File path handling for PDF uploads | Already used throughout codebase |
| json (stdlib) | 3.10+ | Profile/config serialization | Already used in profile_manager.py |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CTkDatePicker | tkcalendar | CTkDatePicker matches CustomTkinter theming, tkcalendar looks dated |
| Tag chips (custom) | ttk.Combobox with autocomplete | Combobox doesn't show multiple selections as visual chips |
| webbrowser.open() | subprocess with platform-specific browser paths | webbrowser is cross-platform and respects user's default |

**Installation:**
```bash
pip install customtkinter tkctkdatepicker
# tkinter, queue, threading, webbrowser, pathlib, json are stdlib
```

## Architecture Patterns

### Recommended Project Structure
```
job_radar/gui/
├── main_window.py           # Phase 28: window shell, tabs, routing
├── worker_thread.py         # Phase 28: threading pattern
├── profile_form.py          # NEW: profile create/edit form widget
├── search_controls.py       # NEW: date pickers, min score, new-only toggle
└── tag_chip_widget.py       # NEW: reusable tag-chip input for skills/titles/dealbreakers
```

### Pattern 1: Reuse Existing Validators Programmatically
**What:** Phase 27's wizard.py validators (NonEmptyValidator, YearsExperienceValidator, etc.) are questionary-specific but their .validate() logic is reusable.

**When to use:** On field blur (FocusOut event) in GUI forms

**Example:**
```python
# From wizard.py - existing validator
class YearsExperienceValidator(Validator):
    def validate(self, document):
        text = document.text.strip()
        try:
            years = int(text)
            if years < 0:
                raise ValidationError(message="Years must be 0 or greater", cursor_position=len(document.text))
            if years > 50:
                raise ValidationError(message="Please enter a realistic number of years (0-50)", cursor_position=len(document.text))
        except ValueError:
            raise ValidationError(message="Please enter a whole number (e.g., 3, 5, 10)", cursor_position=len(document.text))

# GUI adaptation - extract validation logic
def validate_years_experience(text: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message)"""
    text = text.strip()
    try:
        years = int(text)
        if years < 0:
            return False, "Years must be 0 or greater"
        if years > 50:
            return False, "Please enter a realistic number of years (0-50)"
        return True, ""
    except ValueError:
        return False, "Please enter a whole number (e.g., 3, 5, 10)"

# Bind to entry widget
def on_years_blur(event):
    is_valid, error_msg = validate_years_experience(years_entry.get())
    if not is_valid:
        error_label.configure(text=error_msg, text_color="red")
    else:
        error_label.configure(text="")

years_entry.bind("<FocusOut>", on_years_blur)
```

### Pattern 2: Tag-Chip Input Widget
**What:** Entry field where pressing Enter converts typed text into a visual "chip" (CTkLabel with delete button), backspace removes last chip.

**When to use:** Skills, target titles, dealbreakers (any comma-separated list field)

**Example:**
```python
class TagChipWidget(ctk.CTkFrame):
    def __init__(self, parent, placeholder="Type and press Enter", **kwargs):
        super().__init__(parent, **kwargs)

        self.chips = []  # List of chip values
        self.chip_frames = []  # List of CTkFrame widgets

        # Chips container (wraps horizontally)
        self.chips_container = ctk.CTkFrame(self)
        self.chips_container.pack(fill="both", expand=True, pady=(0, 5))

        # Entry field
        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<BackSpace>", self._on_backspace)

    def _on_enter(self, event):
        value = self.entry.get().strip()
        if value and value not in self.chips:
            self._add_chip(value)
            self.entry.delete(0, "end")

    def _add_chip(self, value):
        chip_frame = ctk.CTkFrame(self.chips_container)
        chip_frame.pack(side="left", padx=2, pady=2)

        label = ctk.CTkLabel(chip_frame, text=value)
        label.pack(side="left", padx=(5, 2))

        delete_btn = ctk.CTkButton(
            chip_frame, text="×", width=20, height=20,
            command=lambda: self._remove_chip(value, chip_frame)
        )
        delete_btn.pack(side="left", padx=(0, 5))

        self.chips.append(value)
        self.chip_frames.append(chip_frame)

    def _remove_chip(self, value, frame):
        self.chips.remove(value)
        self.chip_frames.remove(frame)
        frame.destroy()

    def _on_backspace(self, event):
        # If entry is empty and backspace pressed, remove last chip
        if not self.entry.get() and self.chips:
            last_value = self.chips[-1]
            last_frame = self.chip_frames[-1]
            self._remove_chip(last_value, last_frame)

    def get_values(self) -> list[str]:
        return self.chips.copy()

    def set_values(self, values: list[str]):
        self.clear()
        for value in values:
            self._add_chip(value)

    def clear(self):
        for frame in self.chip_frames:
            frame.destroy()
        self.chips.clear()
        self.chip_frames.clear()
```

### Pattern 3: Real Search Worker Replacing Mock
**What:** Replace Phase 28's MockSearchWorker with real sources.fetch_all() call, using existing on_source_progress callback.

**When to use:** "Run Search" button click in Search tab

**Example:**
```python
# In worker_thread.py - add real search worker
class SearchWorker:
    """Real search worker that calls sources.fetch_all()"""

    def __init__(self, result_queue: queue.Queue, stop_event: threading.Event, profile: dict, config: dict):
        self._queue = result_queue
        self._stop_event = stop_event
        self._profile = profile
        self._config = config

    def run(self):
        """Execute real search using sources.fetch_all()"""
        try:
            # Callback for source progress
            def on_source_progress(source_name: str, current: int, total: int, status: str):
                if self._stop_event.is_set():
                    return

                if status == "started":
                    self._queue.put(("source_started", source_name, current, total))
                elif status == "complete":
                    # Get job count from results (passed via closure)
                    self._queue.put(("source_complete", source_name, current, total, job_count))

            # Fetch all results
            results = fetch_all(self._profile, on_source_progress=on_source_progress)

            if self._stop_event.is_set():
                self._queue.put(("cancelled",))
                return

            # Score jobs
            scored = [score_job(r, self._profile) for r in results]

            # Filter by min_score and new_only
            filtered = [j for j in scored if j.score >= self._config.get('min_score', 0)]

            if self._config.get('new_only'):
                # Filter out previously seen jobs
                filtered = [j for j in filtered if not is_seen(j)]

            # Generate report
            report_path = generate_report(filtered, self._profile)

            # Mark jobs as seen
            mark_seen(filtered)

            # Send completion
            self._queue.put(("complete", len(filtered), str(report_path)))

        except Exception as e:
            self._queue.put(("error", str(e)))

    def cancel(self):
        self._stop_event.set()
```

### Pattern 4: File Dialog for PDF Upload
**What:** Use tkinter.filedialog.askopenfilename() with filetypes filter, then call existing pdf_parser.extract_resume_data().

**When to use:** "Upload resume" choice before profile form display

**Example:**
```python
from tkinter import filedialog
from job_radar.pdf_parser import extract_resume_data, PDFValidationError

def on_upload_resume_click(self):
    # Open file dialog
    pdf_path = filedialog.askopenfilename(
        title="Select resume PDF",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        parent=self  # Modal to current window
    )

    if not pdf_path:
        return  # User cancelled

    # Parse PDF using existing parser
    try:
        extracted_data = extract_resume_data(pdf_path)

        # Show success message
        self.show_info("Resume parsed successfully! Review extracted fields.")

        # Pre-fill form with extracted data
        self.pre_fill_form(extracted_data)

    except PDFValidationError as e:
        # Show actionable error dialog
        self.show_error_dialog(str(e))
    except Exception as e:
        self.show_error_dialog(f"PDF parsing failed: {e}\nContinue with manual entry.")
```

### Pattern 5: Open HTML Report with webbrowser
**What:** Convert report Path to file:// URI and call webbrowser.open().

**When to use:** "Open Report" button click after search completion

**Example:**
```python
import webbrowser
from pathlib import Path

def open_report(self, report_path: Path):
    # Convert to file:// URI (cross-platform)
    uri = report_path.as_uri()  # Path.as_uri() handles file:// formatting

    # Open in default browser
    webbrowser.open(uri)
```

### Anti-Patterns to Avoid
- **Duplicating wizard validators:** Don't rewrite validation logic — extract and reuse from wizard.py
- **Direct widget updates from threads:** NEVER call widget.configure() from worker thread — always use queue messages
- **Auto-opening browser without confirmation:** Phase 28 context requires "Open Report" button, not auto-open on completion
- **Blocking GUI thread with search:** Search MUST run in worker thread via existing worker_thread.py pattern
- **Creating new profile save logic:** Use profile_manager.save_profile() — it handles validation, backups, atomic writes

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form field validation | Custom regex validators | wizard.py existing validators (NonEmptyValidator, ScoreValidator, etc.) | Already tested, matches CLI behavior, handles edge cases |
| Profile CRUD | Custom JSON write logic | profile_manager.save_profile(), load_profile() | Atomic writes, automatic backups, schema migration, corruption detection |
| PDF parsing | pypdf2/pdfplumber wrapper | pdf_parser.extract_resume_data() | Already handles encryption, image-only PDFs, field extraction heuristics |
| Search execution | Direct source calls | sources.fetch_all() with callbacks | Handles parallelization, deduplication, error recovery, progress tracking |
| Date pickers | Custom calendar widget | CTkDatePicker library | Native CustomTkinter theming, tested, handles locale/formatting |
| Threading safety | Manual locks/mutexes | queue.Queue + Event pattern from Phase 28 | Standard pattern, already proven in MockSearchWorker |
| Browser opening | Platform-specific subprocess calls | webbrowser.open() | Cross-platform, respects user's default browser, handles file:// URIs |

**Key insight:** This phase is 90% integration, 10% new code. The business logic already exists and is battle-tested through the CLI. GUI code should be thin glue between widgets and existing modules — resist the urge to reimplement validation, I/O, or orchestration logic.

## Common Pitfalls

### Pitfall 1: Thread Updates to Widgets
**What goes wrong:** Calling widget.configure() or widget.pack() from worker thread causes tkinter crashes or silent failures.

**Why it happens:** tkinter is not thread-safe — only the main GUI thread can modify widgets.

**How to avoid:** ALWAYS communicate via queue.put() from worker, process queue in main thread via .after() polling loop (already implemented in Phase 28 _check_queue()).

**Warning signs:** Intermittent crashes, widgets not updating, "RuntimeError: main thread is not in main loop" errors.

### Pitfall 2: Validation State Inconsistency
**What goes wrong:** User edits field A (makes it invalid), tabs to field B (valid), clicks Save — invalid field A is not caught.

**Why it happens:** Validation only fires on blur, but Save button doesn't validate all fields before submission.

**How to avoid:** On Save button click, iterate through all fields and call validation functions programmatically. Show first error and focus that field.

**Warning signs:** Invalid profiles saved to disk, profile_manager.validate_profile() raises exception after form says "saved successfully".

### Pitfall 3: File Path Encoding in webbrowser.open()
**What goes wrong:** Spaces or special characters in report path cause browser to fail opening or show 404.

**Why it happens:** webbrowser.open() expects URI format, not raw filesystem path.

**How to avoid:** Use pathlib.Path.as_uri() which handles file:// prefix and URL encoding automatically.

**Warning signs:** Browser opens but shows "file not found", paths with spaces fail while paths without spaces work.

### Pitfall 4: Date Picker State Not Saved to Config
**What goes wrong:** User sets date range, runs search, closes app, reopens — date range is reset to defaults.

**Why it happens:** Date picker values read from widgets are not persisted to config.json.

**How to avoid:** On search execution, save date range to config.json before starting search (same pattern as min_score and new_only which already persist).

**Warning signs:** Date filters apply during current session but disappear on app restart.

### Pitfall 5: Dirty Form Tracking False Positives
**What goes wrong:** User clicks Edit, doesn't change anything, clicks Cancel — "Discard changes?" dialog appears.

**Why it happens:** Form marked as "dirty" on edit mode entry, not on actual field changes.

**How to avoid:** Track original values dict on form load, bind <KeyRelease> to all Entry widgets to compare current vs original, only set dirty=True when values differ.

**Warning signs:** Users complain about unnecessary confirmation dialogs.

### Pitfall 6: Tag Chip Validation Timing
**What goes wrong:** User types skill name, presses Enter (chip created), but chip contains invalid value (empty string, whitespace-only).

**Why it happens:** _on_enter() doesn't validate before calling _add_chip().

**How to avoid:** In _on_enter(), strip whitespace and check for empty/duplicate before creating chip.

**Warning signs:** Empty chips appear, duplicate chips created, profile validation fails with "empty list" errors.

## Code Examples

### CTkEntry Blur Validation Pattern
```python
# Bind FocusOut event for inline validation
def setup_validation(self):
    self.name_entry.bind("<FocusOut>", self._validate_name)
    self.years_entry.bind("<FocusOut>", self._validate_years)
    self.skills_widget.entry.bind("<FocusOut>", self._validate_skills)

def _validate_name(self, event=None):
    name = self.name_entry.get().strip()
    if not name:
        self.name_error_label.configure(text="This field cannot be empty", text_color="red")
        return False
    else:
        self.name_error_label.configure(text="")
        return True

def _validate_years(self, event=None):
    is_valid, error_msg = validate_years_experience(self.years_entry.get())
    if not is_valid:
        self.years_error_label.configure(text=error_msg, text_color="red")
        return False
    else:
        self.years_error_label.configure(text="")
        return True
```

### CTkDatePicker Integration
```python
# Install: pip install tkctkdatepicker
from CTkDatePicker import CTkDatePicker
from datetime import datetime

# Create date range pickers
self.from_date_picker = CTkDatePicker(
    self.controls_frame,
    corner_radius=5,
    date_format="%Y-%m-%d"
)
self.from_date_picker.grid(row=0, column=1, padx=5)

self.to_date_picker = CTkDatePicker(
    self.controls_frame,
    corner_radius=5,
    date_format="%Y-%m-%d"
)
self.to_date_picker.grid(row=1, column=1, padx=5)

# Get selected dates
from_date_str = self.from_date_picker.get_date()  # Returns "2026-02-10"
to_date_str = self.to_date_picker.get_date()  # Returns "2026-02-13"

# Set default values (None = no filter, matches CLI behavior)
# Leave pickers empty or set to special sentinel value
```

### Form Pre-fill from Existing Profile
```python
def load_existing_profile(self, profile_path: Path):
    profile = load_profile(profile_path)

    # Pre-fill text fields
    self.name_entry.insert(0, profile['name'])
    self.years_entry.insert(0, str(profile['years_experience']))

    if 'location' in profile:
        self.location_entry.insert(0, profile['location'])

    if 'comp_floor' in profile:
        self.comp_floor_entry.insert(0, str(profile['comp_floor']))

    # Pre-fill tag chips
    self.titles_widget.set_values(profile['target_titles'])
    self.skills_widget.set_values(profile['core_skills'])

    if 'dealbreakers' in profile:
        self.dealbreakers_widget.set_values(profile['dealbreakers'])

    # Store original values for dirty tracking
    self.original_values = self.get_form_values()
```

### Save Profile from Form
```python
def save_profile(self):
    # Validate all fields first
    if not self._validate_all_fields():
        return  # Focus is already on first invalid field

    # Build profile dict
    profile_data = {
        'name': self.name_entry.get().strip(),
        'years_experience': int(self.years_entry.get().strip()),
        'target_titles': self.titles_widget.get_values(),
        'core_skills': self.skills_widget.get_values(),
    }

    # Optional fields
    location = self.location_entry.get().strip()
    if location:
        profile_data['location'] = location

    comp_floor = self.comp_floor_entry.get().strip()
    if comp_floor:
        profile_data['comp_floor'] = int(comp_floor)

    dealbreakers = self.dealbreakers_widget.get_values()
    if dealbreakers:
        profile_data['dealbreakers'] = dealbreakers

    # Derive level from years
    years = profile_data['years_experience']
    if years < 2:
        profile_data['level'] = 'junior'
    elif years < 5:
        profile_data['level'] = 'mid'
    elif years < 10:
        profile_data['level'] = 'senior'
    else:
        profile_data['level'] = 'principal'

    # Use existing profile_manager for save
    from job_radar.paths import get_data_dir
    profile_path = get_data_dir() / "profile.json"

    try:
        save_profile(profile_data, profile_path)  # Atomic write, backup, validation
        self.show_success("Profile saved successfully!")
        self.navigate_to_search_tab()
    except ProfileValidationError as e:
        self.show_error_dialog(str(e))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual threading with locks | queue.Queue + Event pattern | Phase 28 | Simpler, safer, matches tkinter best practices |
| Direct file:// string concat | pathlib.Path.as_uri() | Python 3.4+ | Automatic URL encoding, cross-platform |
| Inline PDF parsing | Dedicated pdf_parser module with validation | Phase 27 | Centralized error handling, actionable errors |
| questionary validators | Programmatic validator functions | This phase | CLI and GUI share validation logic |

**Deprecated/outdated:**
- **tkinter.ttk widgets without theming:** CustomTkinter provides modern look with system theme integration
- **validatecommand for CTkEntry:** Inconsistent support across CustomTkinter versions — use FocusOut binding instead
- **Manual browser subprocess calls:** webbrowser.open() is standard library, cross-platform

## Open Questions

1. **CTkDatePicker nullable/optional dates**
   - What we know: Date pickers typically show a date by default (today)
   - What's unclear: How to represent "no date filter" (CLI default) in GUI — empty picker? Special "No filter" checkbox?
   - Recommendation: Add "Apply date filter" checkbox (unchecked by default) that enables/disables date pickers. When unchecked, ignore picker values.

2. **Window resize behavior during form display**
   - What we know: Phase 28 uses fixed 700x500 window with minsize
   - What's unclear: Should form view temporarily expand window to show all fields? Or keep fixed size and rely on scrolling?
   - Recommendation: Keep window size fixed, use CTkScrollableFrame for form (matches Profile tab pattern). Avoids disruptive window resizing.

3. **Tag chip visual limit**
   - What we know: Skills/titles can be long lists (10+ items)
   - What's unclear: Should chip container wrap or scroll horizontally?
   - Recommendation: Vertical wrapping with max height + scrollbar. Matches form scrolling pattern, more scannable than horizontal scroll.

## Sources

### Primary (HIGH confidence)
- Phase 28 codebase: /home/corye/Claude/Job-Radar/job_radar/gui/main_window.py (threading pattern, tab structure)
- Phase 28 codebase: /home/corye/Claude/Job-Radar/job_radar/gui/worker_thread.py (queue.Queue + Event pattern)
- Existing validators: /home/corye/Claude/Job-Radar/job_radar/wizard.py (reusable validation logic)
- Profile I/O: /home/corye/Claude/Job-Radar/job_radar/profile_manager.py (save/load/validate)
- PDF parsing: /home/corye/Claude/Job-Radar/job_radar/pdf_parser.py (extract_resume_data)
- Search orchestration: /home/corye/Claude/Job-Radar/job_radar/sources.py (fetch_all with callbacks)

### Secondary (MEDIUM confidence)
- [CustomTkinter CTkEntry Documentation](https://github.com/TomSchimansky/CustomTkinter/wiki/CTkEntry) - Widget parameters and methods
- [CustomTkinter CTkSwitch Documentation](https://customtkinter.tomschimansky.com/documentation/widgets/switch/) - Toggle state management
- [CTkDatePicker GitHub](https://github.com/maxverwiebe/CTkDatePicker) - Third-party date picker for CustomTkinter
- [Python webbrowser Documentation](https://docs.python.org/3/library/webbrowser.html) - Opening HTML files in browser
- [CustomTkinter Scrollable Frame Tutorial](https://customtkinter.tomschimansky.com/tutorial/scrollable-frames/) - Form layout patterns
- [CustomTkinter Grid System Tutorial](https://customtkinter.tomschimansky.com/tutorial/grid-system/) - Layout best practices

### Tertiary (LOW confidence, requires verification)
- [Tkinter Validation Tutorial](https://www.pythontutorial.net/tkinter/tkinter-validation/) - FocusOut event binding pattern
- [Tkinter Threading Best Practices](https://pythoneo.com/tkinter-and-threading/) - Queue-based communication
- [Tkinter File Dialog Tutorial](https://pythonbasics.org/tkinter-filedialog/) - askopenfilename usage

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use (Phase 28) or verified via official docs
- Architecture: HIGH - Patterns derived from existing Phase 28 code and verified official CustomTkinter docs
- Pitfalls: HIGH - Based on known tkinter threading issues (official docs) and codebase analysis

**Research date:** 2026-02-13
**Valid until:** 30 days (CustomTkinter is stable, tkinter patterns are established)

---

**Key Findings Summary:**
1. Business logic already exists — this is a pure integration phase
2. CustomTkinter provides all core widgets except date picker (use CTkDatePicker)
3. Tag-chip pattern is custom but simple (Entry + Label widgets)
4. Threading pattern from Phase 28 extends directly to real search worker
5. Existing validators, profile I/O, PDF parsing, search orchestration all reusable without modification
6. Main risks: thread safety (mitigated by Phase 28 queue pattern), validation timing (mitigated by blur binding + pre-save full validation), file path encoding (mitigated by Path.as_uri())
