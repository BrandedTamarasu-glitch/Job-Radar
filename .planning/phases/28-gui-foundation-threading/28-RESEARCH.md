# Phase 28: GUI Foundation & Threading - Research

**Researched:** 2026-02-12
**Domain:** Desktop GUI with CustomTkinter, Threading Infrastructure, Dual CLI/GUI Entry Points
**Confidence:** MEDIUM-HIGH

## Summary

Phase 28 establishes the GUI foundation using CustomTkinter (a modern Tkinter wrapper), implements thread-safe non-blocking operations, and creates a single executable with dual entry points (auto-detects GUI vs CLI mode). The core challenge is maintaining thread safety when updating the GUI from worker threads—solved via queue-based communication and Tkinter's `.after()` method for scheduled updates from the main thread.

CustomTkinter 5.2.2 (latest, released Jan 2024) provides modern dark/light theme support with automatic system appearance detection. The library is essentially discontinued but stable and production-ready. Threading follows the standard pattern: worker threads execute long operations, communicate via `queue.Queue`, and the main GUI thread polls the queue using `.after()` to schedule thread-safe updates.

Entry point detection uses `len(sys.argv) > 1` to distinguish CLI mode (flags present) from GUI mode (no arguments, double-click launch). PyInstaller's limitation—console window is compile-time, not runtime—means we build with `console=True` and rely on `--verbose` flag to control output visibility, accepting that GUI mode shows a console window by default per user decision.

**Primary recommendation:** Use CustomTkinter with queue-based threading, `.after()` for GUI updates, `threading.Event` for cancellation, and `len(sys.argv) > 1` for mode detection. Build mock 10+ second operations in this phase to validate the threading pattern before Phase 29 integrates real search execution.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Window appearance:**
- Medium window size (700x500) on launch
- Follow system theme automatically (dark/light) — CustomTkinter handles this
- Tabbed sections for organization (Profile / Search tabs at minimum)
- Header area with app name and icon/logo placeholder at top of window

**Entry point behavior:**
- Single executable with auto-detection: opens GUI when double-clicked (no flags), uses CLI when run with flags from terminal
- First launch (no profile): welcome screen explaining what Job Radar does, "Get Started" button leads to profile form
- Returning user (profile exists): profile summary shown as default view, user navigates to search tab
- No console window by default; console visible in verbose mode (--verbose flag)

**Progress display:**
- Progress indicator replaces the search area (center of window) while running
- Shows source name: "Fetching Dice..." as each source runs
- Cancel button available during search to stop the operation
- Claude's discretion on determinate bar vs indeterminate spinner (pick based on existing on_progress callback feasibility)

**Error presentation:**
- Errors shown as popup dialog boxes (modal)
- Partial source failures: show results silently — open the report with whatever succeeded, don't mention failures (CLI already handles graceful degradation)
- No profile state: Run Search button disabled (grayed out) with tooltip "Profile required" until profile exists
- Profile form validation: inline red text under each specific field that has an error

### Claude's Discretion
- Progress indicator type (determinate bar vs indeterminate spinner)
- Exact tab names and ordering
- Welcome screen layout and copy
- Icon/logo design (placeholder is fine)
- Window resizing behavior (fixed vs resizable)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope

</user_constraints>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| customtkinter | 5.2.2 | Modern Tkinter wrapper with theme support | Most popular modern Tkinter alternative, automatic dark/light themes, drop-in CTk replacements for Tk widgets |
| tkinter | stdlib | Base GUI framework | Built into Python, zero-install dependency, cross-platform |
| threading | stdlib | Non-blocking operations | Python standard library, battle-tested concurrency primitive |
| queue | stdlib | Thread-safe communication | Standard pattern for worker-to-GUI thread messaging |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| CTkToolTip | latest | Tooltip extension for CustomTkinter | Showing "Profile required" tooltip on disabled Run Search button |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CustomTkinter | tkinter.ttk | TTK is built-in with better OS integration, but lacks modern dark/light auto-theming and requires manual styling |
| CustomTkinter | PyQt/PySide | More powerful, professional look, but massive dependency (50+ MB), steeper learning curve, GPL/commercial licensing |
| CustomTkinter | Kivy/PySimpleGUI | Kivy is mobile-first (overkill), PySimpleGUI has licensing restrictions since v5 |

**Installation:**
```bash
pip install customtkinter
```

**Note:** CustomTkinter 5.2.2 (Jan 2024) is the latest version. The library appears discontinued but is stable and production-ready for Python 3.7+.

---

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── gui/
│   ├── __init__.py
│   ├── main_window.py       # CTk main window, tab setup, entry point logic
│   ├── profile_tab.py       # Profile view/edit UI (Phase 29)
│   ├── search_tab.py        # Search controls, progress display (Phase 29)
│   ├── worker_thread.py     # Background task execution
│   └── queue_handler.py     # Queue polling, thread-safe GUI updates
├── search.py                # Existing CLI entry point
└── __main__.py              # Dual-mode entry point detection
```

### Pattern 1: Queue-Based Thread Communication

**What:** Worker threads communicate results/progress to GUI via `queue.Queue`, main thread polls queue with `.after()`.

**When to use:** Any long-running operation that must not block the GUI main loop.

**Example:**
```python
import queue
import threading
import customtkinter as ctk

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.check_queue()  # Start polling

    def start_long_operation(self):
        # Launch worker thread
        thread = threading.Thread(target=self.worker_task, daemon=True)
        thread.start()

    def worker_task(self):
        # Runs in background thread
        for i in range(10):
            time.sleep(1)
            self.queue.put(("progress", i + 1))  # Send to GUI thread
        self.queue.put(("complete", "Done!"))

    def check_queue(self):
        # Runs in main GUI thread
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == "progress":
                    self.update_progress(data)
                elif msg_type == "complete":
                    self.show_completion(data)
        except queue.Empty:
            pass
        finally:
            # Re-schedule check in 100ms
            self.after(100, self.check_queue)
```

**Source:** [Python queue module](https://docs.python.org/3/library/queue.html), [Tkinter threading pattern](https://medium.com/tomtalkspython/tkinter-and-threading-building-responsive-python-gui-applications-02eed0e9b0a7)

### Pattern 2: Cancellable Operations with threading.Event

**What:** Use `threading.Event` to signal worker threads to stop gracefully.

**When to use:** Operations that need a Cancel button (search execution).

**Example:**
```python
class SearchWorker:
    def __init__(self, result_queue):
        self.result_queue = result_queue
        self.stop_event = threading.Event()

    def run(self):
        for source in sources:
            if self.stop_event.is_set():
                self.result_queue.put(("cancelled", None))
                return
            # Fetch source
            results = fetch_source(source)
            self.result_queue.put(("progress", source, results))
        self.result_queue.put(("complete", all_results))

    def cancel(self):
        self.stop_event.set()

# In GUI:
def on_cancel_button():
    self.worker.cancel()
```

**Source:** [Python threading.Event](https://docs.python.org/3/library/threading.html), [Cancellation pattern](https://superfastpython.com/stop-a-thread-in-python/)

### Pattern 3: Dual Entry Point Detection

**What:** Single executable detects CLI vs GUI mode based on `sys.argv` length.

**When to use:** Applications supporting both CLI and GUI interfaces from one entry point.

**Example:**
```python
# job_radar/__main__.py
import sys

def main():
    # CLI mode: any arguments present (--profile, --help, etc.)
    if len(sys.argv) > 1:
        from job_radar.search import main as cli_main
        cli_main()
    else:
        # GUI mode: no arguments (double-click)
        from job_radar.gui.main_window import launch_gui
        launch_gui()

if __name__ == "__main__":
    main()
```

**Source:** [Python sys.argv](https://docs.python.org/3/library/sys.html), [argparse documentation](https://docs.python.org/3/library/argparse.html)

### Pattern 4: CustomTkinter Tabbed Layout

**What:** Use `CTkTabview` to organize Profile and Search sections.

**When to use:** Multi-section interfaces with distinct workflows.

**Example:**
```python
class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Job Radar")
        self.geometry("700x500")

        # Header
        header = ctk.CTkLabel(self, text="Job Radar", font=("Arial", 24, "bold"))
        header.pack(pady=10)

        # Tabs
        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=20, pady=10)

        profile_tab = tabview.add("Profile")
        search_tab = tabview.add("Search")

        # Add widgets to tabs
        ctk.CTkLabel(profile_tab, text="Profile Summary").pack()
        ctk.CTkButton(search_tab, text="Run Search").pack()

        tabview.set("Profile")  # Default tab
```

**Source:** [CTkTabview documentation](https://customtkinter.tomschimansky.com/documentation/widgets/tabview/)

### Anti-Patterns to Avoid

- **Updating GUI from worker thread:** NEVER call `.config()`, `.update()`, or any widget method from a background thread. Use `.after()` or queue-based messaging instead. Tkinter is single-threaded.
- **Blocking main loop:** Never call `time.sleep()`, `requests.get()`, or any blocking operation in the main thread. Use worker threads.
- **Global state for threading:** Avoid global variables for thread communication. Pass queue/event objects explicitly or store as instance attributes.
- **Polling with tight loops:** Don't use `while True` loops to check queue. Use `.after(100, check_queue)` to schedule periodic checks.
- **Acquiring locks in GUI callbacks:** Deadlock risk if worker thread holds lock while sending queue message. Use lock-free queue communication.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thread-safe GUI updates | Custom locking, manual state sync | `queue.Queue` + `.after()` | Edge cases: race conditions, deadlock, message ordering. Tkinter is single-threaded by design—queue + after() is the battle-tested pattern. |
| Modern themed widgets | Manual styling with tk.Button, ttk.Style | CustomTkinter `CTkButton`, `CTkLabel` | Dark/light theme detection, HighDPI scaling, consistent cross-platform appearance. CustomTkinter handles system appearance changes automatically. |
| Progress indicators | Animated canvas drawing | `CTkProgressBar` with `mode="indeterminate"` or `determinate` | Built-in animation, mode switching, standard widget methods. Manually animating canvas is 50+ LOC and brittle. |
| Thread cancellation | Thread.terminate() (doesn't exist), forced interrupts | `threading.Event` with periodic checks | Python threads cannot be killed externally. Cooperative cancellation with Event is the only safe pattern—worker checks `stop_event.is_set()`. |
| Entry point detection | Parsing sys.argv[0] for script name patterns | `len(sys.argv) > 1` | Robust across execution contexts (frozen exe, python -m, script.py). Detects presence of CLI flags, not script name. |

**Key insight:** Tkinter/CustomTkinter are single-threaded—attempts to update from worker threads cause crashes or data corruption. Queue-based communication with `.after()` polling is non-negotiable.

---

## Common Pitfalls

### Pitfall 1: Direct GUI Updates from Worker Thread

**What goes wrong:** Worker thread calls `label.configure(text="Done")` directly, causing "RuntimeError: main thread is not in main loop" or silent data corruption.

**Why it happens:** Tkinter's event loop runs in the main thread only. Widget methods are not thread-safe.

**How to avoid:** Always use `queue.put()` from worker thread, then `.after()` in main thread to process queue and update widgets.

**Warning signs:** Intermittent crashes, "can't invoke Tcl command from thread" errors, GUI freezing after background task completes.

**Source:** [Tkinter threading guide](https://medium.com/tomtalkspython/tkinter-and-threading-building-responsive-python-gui-applications-02eed0e9b0a7), [Python bug tracker issue 11077](https://bugs.python.org/issue11077)

### Pitfall 2: Blocking Operations in Main Thread

**What goes wrong:** Calling `time.sleep(10)` or `fetch_all()` in a button callback freezes the entire GUI—window can't redraw, buttons don't respond, OS marks app as "Not Responding".

**Why it happens:** Tkinter's main loop must continuously process events (redraws, clicks, key presses). Blocking the main thread blocks the event loop.

**How to avoid:** Move long operations to worker threads. Main thread only schedules work and updates UI.

**Warning signs:** Window becomes unresponsive, can't move/resize, spinner cursor, force-quit required.

**Source:** [Tkinter main loop](https://textbooks.cs.ksu.edu/cc410/ii-gui/13-event-driven-programming/07-tkinter-main-loop/)

### Pitfall 3: PyInstaller Console Window Confusion

**What goes wrong:** Building with `--noconsole` breaks CLI mode (no output visible in terminal). Building with `console=True` shows console window when double-clicking GUI mode.

**Why it happens:** Windows subsystem choice is compile-time, not runtime. Can't have both modes in one executable on Windows.

**How to avoid:** Accept console window visibility in GUI mode (user decision for Phase 28), or build two separate executables (launcher wrapper pattern for future phases).

**Warning signs:** CLI output disappears when using `--noconsole`. Console window shows in GUI mode with `console=True`.

**Source:** [PyInstaller issue 6244](https://github.com/pyinstaller/pyinstaller/issues/6244), [PyInstaller console documentation](https://pyinstaller.org/en/stable/usage.html)

### Pitfall 4: Race Conditions with Shared State

**What goes wrong:** Worker thread and GUI thread both access `self.results` list without locking, causing data corruption or missing items.

**Why it happens:** Python operations like `.append()` aren't atomic. Thread switching mid-operation corrupts shared data structures.

**How to avoid:** Use `queue.Queue` for thread communication (thread-safe by design). Avoid sharing mutable state between threads.

**Warning signs:** Intermittent bugs that only appear under load. Random missing/duplicate data. Non-reproducible crashes.

**Source:** [Python thread safety](https://realpython.com/python-thread-lock/), [Race conditions](https://labex.io/tutorials/python/how-to-ensure-thread-safety-and-avoid-race-conditions-in-python-398189)

### Pitfall 5: Forgetting Daemon Threads

**What goes wrong:** Application hangs on exit because non-daemon worker thread is still running, waiting for network timeout or long operation.

**Why it happens:** Python waits for all non-daemon threads to complete before exiting. Background threads should be daemons.

**How to avoid:** Set `daemon=True` when creating worker threads: `threading.Thread(target=worker, daemon=True)`.

**Warning signs:** Application window closes but process remains in task manager. Must force-kill to exit.

**Source:** [Python threading documentation](https://docs.python.org/3/library/threading.html)

---

## Code Examples

Verified patterns from official sources:

### CustomTkinter Basic Window Setup

```python
import customtkinter as ctk

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Job Radar")
        self.geometry("700x500")

        # Appearance mode (auto-detects system theme)
        ctk.set_appearance_mode("system")  # "light", "dark", or "system"
        ctk.set_default_color_theme("blue")  # "blue", "dark-blue", "green"

        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header row (fixed)
        self.grid_rowconfigure(1, weight=1)  # Content row (expands)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")

        title_label = ctk.CTkLabel(
            header_frame,
            text="Job Radar",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")

        # Content
        self.create_content()

    def create_content(self):
        # Implement tabs, widgets, etc.
        pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
```

**Source:** [CustomTkinter documentation](https://customtkinter.tomschimansky.com/documentation/), [Complex example](https://github.com/TomSchimansky/CustomTkinter/blob/master/examples/complex_example.py)

### Thread-Safe Progress Updates

```python
import queue
import threading
import time
import customtkinter as ctk

class SearchWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Search Demo")
        self.geometry("400x300")

        # Thread communication
        self.queue = queue.Queue()
        self.worker = None

        # UI elements
        self.progress_label = ctk.CTkLabel(self, text="Ready")
        self.progress_label.pack(pady=20)

        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.progress_bar.pack(pady=10, padx=40, fill="x")
        self.progress_bar.set(0)

        self.start_button = ctk.CTkButton(self, text="Start", command=self.start_search)
        self.start_button.pack(pady=10)

        self.cancel_button = ctk.CTkButton(self, text="Cancel", command=self.cancel_search, state="disabled")
        self.cancel_button.pack(pady=10)

        # Start queue polling
        self.check_queue()

    def start_search(self):
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress_bar.set(0)

        # Create and start worker thread
        stop_event = threading.Event()
        self.worker = SearchWorker(self.queue, stop_event)
        thread = threading.Thread(target=self.worker.run, daemon=True)
        thread.start()

    def cancel_search(self):
        if self.worker:
            self.worker.cancel()

    def check_queue(self):
        """Process messages from worker thread (runs in main thread)"""
        try:
            while True:
                msg = self.queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "progress":
                    source, current, total = msg[1], msg[2], msg[3]
                    self.progress_label.configure(text=f"Fetching {source}...")
                    self.progress_bar.set(current / total)

                elif msg_type == "complete":
                    self.progress_label.configure(text="Search complete!")
                    self.progress_bar.set(1.0)
                    self.start_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")

                elif msg_type == "cancelled":
                    self.progress_label.configure(text="Cancelled")
                    self.start_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")

                elif msg_type == "error":
                    error_msg = msg[1]
                    self.show_error(error_msg)
                    self.start_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")

        except queue.Empty:
            pass
        finally:
            # Re-schedule queue check in 100ms
            self.after(100, self.check_queue)

    def show_error(self, message):
        # Modal error dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("300x150")

        label = ctk.CTkLabel(dialog, text=message, wraplength=250)
        label.pack(pady=20, padx=20)

        button = ctk.CTkButton(dialog, text="OK", command=dialog.destroy)
        button.pack(pady=10)

        dialog.transient(self)  # Modal
        dialog.grab_set()       # Block parent window

class SearchWorker:
    def __init__(self, result_queue, stop_event):
        self.result_queue = result_queue
        self.stop_event = stop_event

    def run(self):
        """Simulates long-running search (runs in worker thread)"""
        sources = ["Dice", "HN Hiring", "RemoteOK", "WWR", "LinkedIn"]

        try:
            for i, source in enumerate(sources):
                # Check for cancellation
                if self.stop_event.is_set():
                    self.result_queue.put(("cancelled",))
                    return

                # Simulate fetching
                self.result_queue.put(("progress", source, i + 1, len(sources)))
                time.sleep(2)  # Mock network delay

            self.result_queue.put(("complete",))

        except Exception as e:
            self.result_queue.put(("error", str(e)))

    def cancel(self):
        self.stop_event.set()

if __name__ == "__main__":
    app = SearchWindow()
    app.mainloop()
```

**Source:** [Queue-based threading pattern](https://pymotw.com/2/Queue/), [Tkinter threading tutorial](https://www.pythontutorial.net/tkinter/tkinter-thread/)

### Entry Point Detection

```python
# job_radar/__main__.py
import sys

def main():
    """Single entry point with CLI/GUI auto-detection"""

    # Mode detection: CLI if any arguments present
    if len(sys.argv) > 1:
        # CLI mode: run existing argparse-based CLI
        from job_radar.search import main as cli_main
        cli_main()
    else:
        # GUI mode: launch CustomTkinter window
        from job_radar.gui.main_window import launch_gui
        launch_gui()

if __name__ == "__main__":
    main()
```

**Source:** [Python sys.argv](https://docs.python.org/3/library/sys.html), [Argparse documentation](https://docs.python.org/3/library/argparse.html)

### PyInstaller Runtime Detection

```python
import sys
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to resource (works for dev and PyInstaller bundle)"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running as normal Python script
        base_path = Path(__file__).parent

    return base_path / relative_path

# Usage:
icon_path = get_resource_path("assets/icon.png")
```

**Source:** [PyInstaller runtime information](https://pyinstaller.org/en/stable/runtime-information.html)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tkinter.Button with manual styling | CustomTkinter CTkButton | 2021 (CTk initial release) | Automatic dark/light themes, modern appearance, no manual style configuration |
| Thread.join() polling with sleep loops | queue.Queue + .after() polling | Established pattern (pre-2015) | Non-blocking, no busy-waiting, standard idiom for GUI threading |
| Multiple executables for CLI/GUI | Single executable with sys.argv detection | Common since Python 3.x argparse | Simpler distribution, single entry point, mode auto-detection |
| --noconsole for GUI apps | Accept console window or build separate binaries | PyInstaller limitation (Windows subsystem compile-time) | Windows OS restriction—no runtime toggle between subsystems |

**Deprecated/outdated:**
- **Manual Tkinter theming with ttk.Style:** CustomTkinter replaces this with automatic appearance mode and pre-styled widgets
- **tkMessageBox:** Use CustomTkinter modal dialogs (CTkToplevel with transient/grab_set)
- **Thread killing (thread.stop()):** Never existed in Python—use cooperative cancellation with threading.Event

---

## Open Questions

1. **Progress indicator type (determinate vs indeterminate)**
   - What we know: `sources.py` has `on_source_progress` callback with (source_name, count, total, status). Provides count/total for determinate bar.
   - What's unclear: Whether exact progress percentage is meaningful or if indeterminate spinner better matches user expectation (source durations vary wildly).
   - Recommendation: Use **determinate** CTkProgressBar—callback already provides count/total, users benefit from seeing "3 of 5 sources" progress. Reserve indeterminate for future unknown-duration tasks.

2. **Tooltip implementation for disabled button**
   - What we know: CTkToolTip is a third-party package (not built into CustomTkinter). CTkButton supports `state="disabled"`.
   - What's unclear: Whether CTkToolTip is stable/maintained, and if inline text warning is clearer than hover tooltip.
   - Recommendation: Use inline CTkLabel with red text ("Profile required to run search") below disabled button instead of tooltip—more accessible, clearer UX, no extra dependency.

3. **Window resizing behavior**
   - What we know: CustomTkinter grid layout supports weight configuration for flexible sizing. User hasn't specified preference.
   - What's unclear: Whether fixed or resizable better serves use case (minimal content in Phase 28, more in Phase 29).
   - Recommendation: **Resizable** with minimum size (700x500)—grid layout already configured, allows users to maximize for better readability. Easy to lock later if problematic.

4. **Console window visibility control**
   - What we know: PyInstaller `console=True` is required for CLI mode to work. `--noconsole` breaks CLI output.
   - What's unclear: Exact behavior of `--verbose` flag with GUI mode—does it suppress print() output, or just control logging level?
   - Recommendation: Keep `console=True` in .spec file per user decision ("No console window by default; console visible in verbose mode"). Document that GUI mode shows console when launched with --verbose. This is acceptable for Phase 28 skeleton.

---

## Sources

### Primary (HIGH confidence)
- [Python threading module](https://docs.python.org/3/library/threading.html) - Official documentation
- [Python queue module](https://docs.python.org/3/library/queue.html) - Official documentation
- [Python sys module](https://docs.python.org/3/library/sys.html) - Official documentation for sys.argv, sys.frozen
- [CustomTkinter official documentation](https://customtkinter.tomschimansky.com/documentation/) - Widgets, appearance mode, examples
- [CustomTkinter GitHub repository](https://github.com/TomSchimansky/CustomTkinter) - Source code, issues, examples
- [CustomTkinter PyPI page](https://pypi.org/project/customtkinter/) - Version 5.2.2, Python requirements
- [PyInstaller runtime information](https://pyinstaller.org/en/stable/runtime-information.html) - sys.frozen, sys._MEIPASS detection
- [PyInstaller usage documentation](https://pyinstaller.org/en/stable/usage.html) - Console flags, spec file options

### Secondary (MEDIUM confidence)
- [Tkinter and Threading: Building Responsive Python GUI Applications](https://medium.com/tomtalkspython/tkinter-and-threading-building-responsive-python-gui-applications-02eed0e9b0a7) - Queue pattern, .after() usage
- [How to Use Thread in Tkinter Applications](https://www.pythontutorial.net/tkinter/tkinter-thread/) - Thread-safe GUI updates
- [Python Thread Safety: Using a Lock and Other Techniques – Real Python](https://realpython.com/python-thread-lock/) - Race conditions, locking patterns
- [How to Stop a Thread in Python - Super Fast Python](https://superfastpython.com/stop-a-thread-in-python/) - threading.Event cancellation pattern
- [PyInstaller issue #6244: Support for GUI and CLI apps](https://github.com/pyinstaller/pyinstaller/issues/6244) - Console window limitation explanation
- [CTkTabview documentation](https://customtkinter.tomschimansky.com/documentation/widgets/tabview/) - Tab widget API
- [CTkProgressBar documentation](https://customtkinter.tomschimansky.com/documentation/widgets/progressbar/) - Determinate/indeterminate modes
- [Detecting TTYs and Terminals with Python's isatty()](https://thelinuxcode.com/python-file-isatty-method/) - sys.stdin.isatty() for terminal detection
- [From Tkinter to CustomTkinter: A Journey to Better UIs](https://medium.com/@VaishnavSabariGirish/from-tkinter-to-customtkinter-a-journey-to-better-uis-in-python-fd9ea6388fda) - TTK vs CustomTkinter comparison

### Tertiary (LOW confidence)
- [How to ensure thread safety and avoid race conditions in Python](https://labex.io/tutorials/python/how-to-ensure-thread-safety-and-avoid-race-conditions-in-python-398189) - General threading pitfalls
- [Advanced Python 9— Thread Synchronization and Deadlock](https://medium.com/@abhishekjainindore24/advanced-python-8-thread-synchronization-and-deadlock-21ece3722b1f) - Deadlock patterns
- [CTkToolTip PyPI page](https://pypi.org/project/CTkToolTip/) - Tooltip extension (not used in Phase 28 recommendation)

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - CustomTkinter 5.2.2 on PyPI, official docs verified, threading/queue are stdlib
- Architecture: **MEDIUM-HIGH** - Queue + .after() pattern verified in multiple sources, entry point detection is straightforward sys.argv check
- Pitfalls: **HIGH** - Thread safety issues well-documented in official Python docs and Real Python tutorials, PyInstaller console limitation confirmed by maintainers

**Research date:** 2026-02-12
**Valid until:** 30 days (stable technologies—Tkinter, stdlib threading patterns unlikely to change)

**Note on CustomTkinter status:** Library appears discontinued (last release Jan 2024, no activity in 12+ months), but is stable and production-ready. No breaking changes expected. If long-term maintenance becomes a concern, migration path to tkinter.ttk is straightforward (widget names map directly).
