# Architecture Research

**Domain:** Desktop GUI Integration for Python CLI Application
**Researched:** 2026-02-12
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐                        ┌──────────┐           │
│  │   CLI    │                        │   GUI    │           │
│  │ (search. │                        │ (main    │           │
│  │  py)     │                        │  window) │           │
│  └────┬─────┘                        └────┬─────┘           │
│       │                                   │                 │
│       └────────────┬──────────────────────┘                 │
├────────────────────┴─────────────────────────────────────────┤
│                   Business Logic Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Sources │  │ Scoring │  │ Report  │  │ Tracker │        │
│  │ Fetcher │  │ Engine  │  │ Gen     │  │         │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
├───────┴────────────┴────────────┴────────────┴──────────────┤
│                    Data Layer                                │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌─────────────┐  ┌────────────┐     │
│  │  Profile I/O     │  │  Config I/O │  │  Cache     │     │
│  │ (profile_manager)│  │  (config)   │  │  (cache)   │     │
│  └──────────────────┘  └─────────────┘  └────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Entry Point Dispatcher** | Detect CLI vs GUI mode and route to appropriate frontend | Single `__main__.py` checking `sys.argv` |
| **CLI Frontend** | Argument parsing, terminal output, progress display | argparse + print statements (existing `search.py`) |
| **GUI Frontend** | Window management, widgets, event handling, visual feedback | PyQt6/PySide6 main window + worker threads |
| **Business Logic** | Data fetching, scoring, report generation (unchanged) | Existing modules (sources.py, scoring.py, report.py) |
| **Data Layer** | File I/O, caching, persistence (unchanged) | Existing modules (profile_manager.py, config.py, cache.py) |

## Recommended Project Structure

```
job_radar/
├── __init__.py
├── __main__.py              # Dispatcher: CLI vs GUI entry point
├── search.py                # CLI frontend (existing, unchanged)
├── gui/                     # NEW: GUI components
│   ├── __init__.py
│   ├── main_window.py       # Main GUI window (MVP View)
│   ├── presenter.py         # Business logic coordinator (MVP Presenter)
│   ├── workers.py           # QRunnable workers for async tasks
│   ├── signals.py           # Custom Qt signals for thread communication
│   └── widgets/             # Reusable GUI components
│       ├── __init__.py
│       ├── profile_form.py  # Profile editing form
│       ├── results_table.py # Job results display
│       └── progress_bar.py  # Search progress indicator
├── sources.py               # Business logic (existing, unchanged)
├── scoring.py               # Business logic (existing, unchanged)
├── report.py                # Business logic (existing, unchanged)
├── tracker.py               # Business logic (existing, unchanged)
├── profile_manager.py       # Data layer (existing, unchanged)
├── config.py                # Data layer (existing, unchanged)
└── cache.py                 # Data layer (existing, unchanged)
```

### Structure Rationale

- **gui/ subfolder:** Isolates GUI code from business logic, making it easy to exclude from CLI builds or test business logic independently.
- **Presenter pattern:** Separates GUI event handling (view) from business logic coordination (presenter), allowing the same business modules to serve both CLI and GUI without modification.
- **workers.py:** Encapsulates threading logic in one place, making it easier to maintain and test non-blocking execution.
- **Existing modules untouched:** No changes to sources.py, scoring.py, report.py, etc. — they remain CLI-agnostic and callable from either frontend.

## Architectural Patterns

### Pattern 1: Entry Point Dispatch (CLI vs GUI Detection)

**What:** Single `__main__.py` that detects whether to launch CLI or GUI mode based on command-line arguments.

**When to use:** Desktop applications that support both GUI (double-click) and CLI (terminal with flags) modes.

**Trade-offs:**
- **Pro:** Single executable, single codebase, users choose interface style.
- **Pro:** Allows power users to script with CLI while casual users use GUI.
- **Con:** Requires careful argument parsing to distinguish "no args = GUI" from "no args = CLI with defaults".

**Example:**
```python
# job_radar/__main__.py
import sys

def main():
    # Detect mode
    if len(sys.argv) > 1:
        # CLI mode: arguments provided
        from job_radar.search import main as cli_main
        cli_main()
    else:
        # GUI mode: no arguments, double-clicked
        try:
            from job_radar.gui.main_window import run_gui
            run_gui()
        except ImportError:
            # GUI dependencies not installed, fall back to CLI
            print("GUI not available. Use --help for CLI options.")
            from job_radar.search import main as cli_main
            cli_main()

if __name__ == '__main__':
    main()
```

### Pattern 2: MVP (Model-View-Presenter) for GUI

**What:** Separate presentation (View = Qt widgets) from business logic (Model = existing modules) using a Presenter that coordinates between them.

**When to use:** GUI applications where business logic must remain testable and reusable independent of UI framework.

**Trade-offs:**
- **Pro:** Business logic remains UI-agnostic (same code serves CLI and GUI).
- **Pro:** Easy to test presenter logic without rendering actual GUI.
- **Pro:** Clean separation makes it easy to swap UI frameworks later.
- **Con:** More boilerplate (three layers instead of monolithic GUI).

**Example:**
```python
# job_radar/gui/presenter.py
from job_radar.sources import fetch_all
from job_radar.scoring import score_job
from job_radar.report import generate_report

class SearchPresenter:
    """Coordinates business logic for GUI, emitting signals for UI updates."""

    def __init__(self, view):
        self.view = view

    def run_search(self, profile, on_progress=None):
        """Execute search (called from worker thread)."""
        # Call existing business logic
        results = fetch_all(profile, on_source_progress=on_progress)
        scored = [{"job": r, "score": score_job(r, profile)} for r in results]
        scored.sort(key=lambda x: x["score"]["overall"], reverse=True)
        return scored

    def export_report(self, scored_results, profile):
        """Generate report files."""
        return generate_report(profile, scored_results)
```

**View interacts with Presenter, not business logic directly:**
```python
# job_radar/gui/main_window.py
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.presenter = SearchPresenter(self)
        # Presenter calls business logic, emits signals to update UI
```

### Pattern 3: QThreadPool + QRunnable for Non-Blocking Search

**What:** Use Qt's thread pool to run long-running fetches in worker threads, communicating progress via signals.

**When to use:** GUI operations that take >1 second (network requests, file I/O, CPU-heavy tasks).

**Trade-offs:**
- **Pro:** GUI stays responsive during long operations (no frozen window).
- **Pro:** Qt's signal/slot mechanism is thread-safe, no manual locking needed.
- **Pro:** Thread pool reuses threads efficiently (better than spawning new Thread per search).
- **Con:** Requires wrapping existing sync code in workers with signal emissions.

**Example:**
```python
# job_radar/gui/workers.py
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

class WorkerSignals(QObject):
    """Signals for worker thread -> GUI communication."""
    progress = pyqtSignal(str, int, int)  # (source_name, current, total)
    finished = pyqtSignal(list)           # (scored_results)
    error = pyqtSignal(str)               # (error_message)

class SearchWorker(QRunnable):
    """Runs job search in background thread."""

    def __init__(self, presenter, profile):
        super().__init__()
        self.presenter = presenter
        self.profile = profile
        self.signals = WorkerSignals()

    def run(self):
        """Execute search (runs in thread pool)."""
        try:
            def on_progress(source, count, total, status):
                # Emit signal to update GUI progress bar
                self.signals.progress.emit(source, count, total)

            results = self.presenter.run_search(self.profile, on_progress)
            self.signals.finished.emit(results)
        except Exception as e:
            self.signals.error.emit(str(e))

# Usage in main window:
worker = SearchWorker(self.presenter, profile)
worker.signals.progress.connect(self.update_progress)
worker.signals.finished.connect(self.display_results)
worker.signals.error.connect(self.show_error)
QThreadPool.globalInstance().start(worker)
```

## Data Flow

### Request Flow (GUI Mode)

```
[User clicks "Search" button]
    ↓
[MainWindow creates SearchWorker]
    ↓
[QThreadPool.start(worker)] → [Worker.run() in background thread]
    ↓                              ↓
[GUI remains responsive]     [Presenter.run_search(profile)]
    ↓                              ↓
[Progress signals emitted]   [fetch_all() from sources.py]
    ↓                              ↓
[Update progress bar]        [score_job() for each result]
    ↓                              ↓
[Results signal emitted]     [Returns scored results]
    ↓
[Display results in table widget]
```

### Request Flow (CLI Mode)

```
[User runs: job-radar --profile me.json]
    ↓
[search.py parses arguments]
    ↓
[fetch_all() runs in main thread]
    ↓
[Print progress to terminal]
    ↓
[score_job() for each result]
    ↓
[generate_report() creates HTML/Markdown]
    ↓
[Print summary to terminal]
```

### Key Data Flows

1. **Profile Loading:** Both CLI and GUI use `profile_manager.load_profile()` — single source of truth for profile validation.
2. **Search Execution:** Both call `sources.fetch_all()` — business logic unchanged, only progress callback differs (print vs signal).
3. **Report Generation:** Both call `report.generate_report()` — GUI may display inline while CLI opens browser.

## Integration Points

### New Components Required

| Component | Purpose | Depends On |
|-----------|---------|------------|
| **gui/main_window.py** | Primary GUI window (search form, results display) | PyQt6 |
| **gui/presenter.py** | Bridges GUI events → business logic calls | Existing modules |
| **gui/workers.py** | Background thread wrappers for long operations | QThreadPool, QRunnable |
| **gui/signals.py** | Custom Qt signals for thread communication | QObject |
| **gui/widgets/** | Reusable UI components (forms, tables, progress) | PyQt6 widgets |

### Modified Components

| Component | Modification | Reason |
|-----------|--------------|--------|
| **__main__.py** | Add GUI detection and launch logic | Dispatch to GUI or CLI |
| **job-radar.spec** | Update to include GUI dependencies | PyInstaller bundling |
| **setup.py / pyproject.toml** | Add PyQt6 as optional dependency | `pip install job-radar[gui]` |

### Unchanged Components (Critical)

| Component | Why Unchanged | Integration Approach |
|-----------|---------------|----------------------|
| **sources.py** | Business logic must remain UI-agnostic | GUI calls `fetch_all()` with signal-emitting callback |
| **scoring.py** | Pure function, no UI coupling | GUI/CLI both call `score_job()` identically |
| **report.py** | Report generation independent of how it's triggered | GUI displays path or embeds HTML; CLI opens browser |
| **profile_manager.py** | File I/O logic doesn't care about caller | Both frontends use same load/save functions |
| **config.py** | Configuration loading UI-agnostic | Same config file format for both modes |

## Dual Entry Point Strategy

### Approach: Argument-Based Dispatch

**Implementation:**
1. `__main__.py` becomes the sole entry point (both `python -m job_radar` and PyInstaller executable).
2. Check `len(sys.argv)`: if > 1, launch CLI; else, launch GUI.
3. GUI frontend imports as `from job_radar.gui.main_window import run_gui`.
4. CLI frontend imports as `from job_radar.search import main as cli_main`.

**PyInstaller Configuration:**
```python
# job-radar.spec (modified)
exe = EXE(
    ...
    console=True,  # Keep console for CLI mode
    ...
)
# NOTE: console=True shows empty window when GUI runs, but necessary for CLI output.
# Alternative: Build two executables (job-radar-cli, job-radar-gui) from same codebase.
```

**Alternative: Two Executables (Recommended for Professional UX):**
```python
# job-radar.spec (dual executable version)
cli_exe = EXE(..., name='job-radar', console=True)
gui_exe = EXE(..., name='job-radar-gui', console=False)

coll = COLLECT(
    cli_exe, gui_exe,  # Both share the same binaries/data
    a.binaries,
    a.zipfiles,
    a.datas,
    ...
)
```

**Rationale:** Single executable with `console=True` works but shows empty terminal when GUI double-clicked. Two executables provide cleaner UX: `job-radar` for CLI, `job-radar-gui` for GUI (or `.app` bundle on macOS).

## Threading Model

### GUI Threading Requirements

**Rule:** Never block the GUI event loop. Operations >100ms must run in worker threads.

**Job Radar Specifics:**
- `fetch_all()` takes 10-30 seconds (network I/O).
- Must use `QThreadPool` + `QRunnable` to run fetches in background.
- Progress updates via signals (`progress.emit(source, count, total)`).
- Results delivered via signals (`finished.emit(scored_results)`).

**Existing Code Compatibility:**
- `sources.py` uses `ThreadPoolExecutor` internally — this is fine, Qt workers can spawn their own thread pools.
- No async/await needed — Qt signals handle cross-thread communication safely.

### Thread Safety Considerations

| Concern | Mitigation |
|---------|------------|
| **GUI updates from worker thread** | Use signals/slots only (Qt handles queuing to GUI thread) |
| **Shared profile data** | Profile is read-only during search — no locking needed |
| **Cache writes** | `cache.py` already uses filesystem atomic writes (safe) |
| **Tracker writes** | `tracker.py` uses JSON atomic writes (safe) |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single user, local execution | Current architecture sufficient — no backend needed |
| Multiple profiles | GUI adds profile selector dropdown — business logic unchanged |
| Resume parsing (future) | Add new module, integrate into scoring — no architecture changes |
| API rate limiting (existing) | Already handled in `sources.py` — GUI just displays status |

### Scaling Priorities

1. **First bottleneck:** GUI startup time if PyQt6 bundle is large.
   - **Fix:** Use PyInstaller onedir mode (already implemented), lazy-import GUI modules.
2. **Second bottleneck:** Search timeout if many sources added.
   - **Fix:** Already parallelized in `sources.py` — no changes needed.

## Anti-Patterns

### Anti-Pattern 1: Business Logic in GUI Event Handlers

**What people do:** Put `fetch_all()` and `score_job()` calls directly in button click handlers.

**Why it's wrong:** Freezes GUI for 10-30 seconds, no way to cancel, violates separation of concerns.

**Do this instead:** Use Presenter + Worker pattern. Button click creates `SearchWorker`, worker calls presenter, signals update GUI.

### Anti-Pattern 2: Modifying Existing Modules for GUI

**What people do:** Add `if GUI_MODE:` checks inside `sources.py` or `scoring.py`.

**Why it's wrong:** Couples business logic to UI, makes CLI mode fragile, hard to test.

**Do this instead:** Keep existing modules unchanged. Pass GUI-specific callbacks (e.g., progress signal emitter) as parameters.

### Anti-Pattern 3: Dual Import Paths for Same Module

**What people do:** Import `search.py` from GUI to reuse CLI logic, causing circular imports or duplicate state.

**Why it's wrong:** `search.py` is a CLI frontend, not a library. Has side effects (prints, sys.exit).

**Do this instead:** Extract shared logic into new module (e.g., `core.py` or use Presenter), let both CLI and GUI import from there.

### Anti-Pattern 4: console=False in PyInstaller for CLI Support

**What people do:** Build with `console=False` to hide terminal window for GUI, breaking CLI output.

**Why it's wrong:** CLI mode requires `console=True` to display output; `console=False` makes `print()` statements invisible.

**Do this instead:** Build two executables (one for CLI, one for GUI) sharing binaries, or accept empty terminal window for single executable.

## Build Order for Phases

### Phase 1: Minimal GUI Skeleton
1. Install PyQt6: `pip install PyQt6`
2. Create `gui/main_window.py` with empty window + "Search" button
3. Modify `__main__.py` to detect CLI vs GUI mode
4. Test: Double-click launches GUI, `job-radar --help` shows CLI

### Phase 2: Profile Form
1. Create `gui/widgets/profile_form.py` (text fields for skills, titles, locations)
2. Wire form to load/save via `profile_manager.py`
3. Test: GUI can load existing profile, edit, save

### Phase 3: Non-Blocking Search
1. Create `gui/workers.py` with `SearchWorker(QRunnable)`
2. Create `gui/signals.py` with progress/finished/error signals
3. Wire "Search" button → start worker in thread pool
4. Test: GUI doesn't freeze during search, progress bar updates

### Phase 4: Results Display
1. Create `gui/widgets/results_table.py` (QTableWidget for jobs)
2. Populate table when worker emits `finished` signal
3. Add double-click → open job URL in browser
4. Test: Search results display, clickable links work

### Phase 5: PyInstaller Integration
1. Add PyQt6 to `hiddenimports` in `job-radar.spec`
2. Build: `pyinstaller job-radar.spec --clean`
3. Test: Bundled executable runs GUI and CLI modes
4. Decide: Single exe (console=True) or dual exe (cli + gui)

## Sources

### GUI Framework Comparison
- [Which Python GUI library should you use in 2026?](https://www.pythonguis.com/faq/which-python-gui-library/) - PySide6 recommended for professional apps
- [PyQt vs. Tkinter: Which Should You Choose for Your Next Python GUI?](https://www.pythonguis.com/faq/pyqt-vs-tkinter/) - PyQt for professional quality
- [PyQt6 vs PySide6: What's the difference?](https://www.pythonguis.com/faq/pyqt6-vs-pyside6/) - 99.9% identical APIs, PySide6 LGPL licensed
- [Modern Python GUIs: The 2026 Definitive Guide](https://eathealthy365.com/the-ultimate-guide-to-modern-python-gui-frameworks/) - Comprehensive comparison

### Threading and Async Patterns
- [Multithreading PyQt6 applications with QThreadPool](https://www.pythonguis.com/tutorials/multithreading-pyqt6-applications-qthreadpool/) - Complete working examples
- [Use PyQt's QThread to Prevent Freezing GUIs](https://realpython.com/python-pyqt-qthread/) - Best practices for non-blocking GUI
- [How to use QThread correctly](https://www.haccks.com/posts/how-to-use-qthread-correctly-p1/) - Worker object pattern
- [Python asyncio: Complete Guide to Async Programming 2026](https://devtoolbox.dedyn.io/blog/python-asyncio-complete-guide) - Threading vs async comparison

### Architectural Patterns
- [A Clean Architecture for a PyQT GUI Using the MVP Pattern](https://medium.com/@mark_huber/a-clean-architecture-for-a-pyqt-gui-using-the-mvp-pattern-78ecbc8321c0) - Presenter pattern implementation
- [MVC vs MVP vs MVVM: Understanding Architectural Patterns](https://calmops.com/programming/python/mvc-mvp-mvvm-patterns/) - Pattern comparison
- [Model-View-ViewModel (MVVM) Pattern in Python](https://softwarepatternslexicon.com/patterns-python/4/9/) - MVVM for Python GUIs

### Entry Points and Packaging
- [Entry points specification](https://packaging.python.org/specifications/entry-points/) - console_scripts vs gui_scripts
- [Support for building .exe files that are both GUI and CLI apps](https://github.com/pyinstaller/pyinstaller/issues/6244) - PyInstaller GUI/CLI challenge
- [How to Create a GUI/CLI Standalone App with Gooey and PyInstaller](https://medium.com/analytics-vidhya/how-to-create-a-gui-cli-standalone-app-in-python-with-gooey-and-pyinstaller-1a21d0914124) - Dual mode example
- [Using PyInstaller](https://pyinstaller.org/en/stable/usage.html) - Official PyInstaller documentation

### Dual Entry Point Patterns
- [What Does if __name__ == "__main__" Do in Python?](https://realpython.com/if-name-main-python/) - Entry point basics
- [Check if running from shell or GUI](https://python-forum.io/thread-46038.html) - Detecting CLI vs GUI mode

---
*Architecture research for: Job Radar Desktop GUI Integration*
*Researched: 2026-02-12*
