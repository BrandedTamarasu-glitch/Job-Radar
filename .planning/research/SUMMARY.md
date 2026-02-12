# Project Research Summary

**Project:** Job-Radar Desktop GUI Launcher
**Domain:** Desktop GUI wrapper for Python CLI application
**Researched:** 2026-02-12
**Confidence:** HIGH

## Executive Summary

Job-Radar is adding a desktop GUI launcher to complement its existing CLI tool, providing a simpler interface for casual users while maintaining the CLI for power users and scripting. Research reveals this is a standard GUI-wrapper-for-CLI pattern used by many developer tools, with well-established architectural approaches. The key insight: this is a **launcher** (configure-run-handoff-to-browser), not a full application requiring complex UI components. This scoping decision drives the entire stack and architecture.

The recommended approach is **CustomTkinter** for the GUI framework (5-10MB overhead vs PyQt6's 80-120MB), threading-based concurrency using Python's built-in queue/threading modules, and a presenter pattern to keep existing business logic unchanged. Critical success factors include: (1) non-blocking GUI operations from the start (threading pattern must be correct in Phase 1), (2) PyInstaller configuration including CustomTkinter's data files and dual CLI/GUI executables, and (3) macOS code signing with proper entitlements for notarization.

The primary risk is UI thread blocking during job searches (10-30 second operations). This must be solved architecturally in Phase 1 using threading + queue-based communication — retrofitting later is expensive. Secondary risks include PyInstaller bundling failures (mitigated by explicit --add-data flags for CustomTkinter themes) and macOS Gatekeeper warnings (requires code signing with entitlements for unsigned executable memory, needed for Python's runtime). High-DPI rendering and multi-monitor positioning are handled automatically by CustomTkinter but require testing on diverse hardware.

## Key Findings

### Recommended Stack

**Framework Resolution:** Research reveals a disagreement between STACK.md (recommends CustomTkinter) and ARCHITECTURE.md (recommends PyQt6/PySide6). After synthesis, **CustomTkinter is strongly recommended** for this project based on three decisive factors:

1. **Bundle size matters:** Current executables are ~50MB. CustomTkinter adds 5-10MB vs PyQt6's 80-120MB overhead. For a launcher (not a full application), doubling bundle size for unused features is unjustifiable.

2. **PyInstaller compatibility:** CustomTkinter has documented integration with PyInstaller using --onedir + --add-data flags. PyQt6 works but adds complexity and size. Current build process already uses PyInstaller successfully for CLI.

3. **Scope alignment:** This is a launcher (forms + progress bar + file dialog), not a complex application requiring PyQt6's advanced widgets (charts, rich text editors, complex tables). CustomTkinter provides modern flat design with dark/light themes sufficient for the use case.

**Core technologies:**
- **CustomTkinter 5.2.2:** Modern GUI framework built on tkinter — MIT licensed, minimal dependencies, high-DPI support automatic, dark/light themes included, PyInstaller-friendly with documented integration
- **Python threading + queue (built-in):** Background task execution — non-blocking GUI during 10-30 second job searches, thread-safe communication via queue, integrates with existing ThreadPoolExecutor in sources.py
- **PyInstaller 6.18.0 (existing):** Bundler for executables — already in use for CLI distribution, requires --add-data flag for CustomTkinter theme files, separate executables for CLI (console=True) and GUI (console=False)
- **tkinter.filedialog (built-in):** Native OS file pickers — uses Win32/Cocoa/GTK dialogs natively, no CustomTkinter equivalent needed
- **webbrowser module (built-in):** Cross-platform browser launching — opens generated HTML reports in default browser

**Version compatibility notes:**
- CustomTkinter 5.2.2 compatible with Python 3.7-3.14 (current project likely 3.10+)
- Avoid Python 3.10.0 specifically (PyInstaller bug), use 3.10.1+
- Python 3.10+ enables dark title bars on macOS (Tcl/Tk 8.6.9+)

**PyInstaller configuration required:**
```bash
pyinstaller --name="JobRadar" \
    --onedir \
    --windowed \
    --add-data "venv/lib/python3.10/site-packages/customtkinter:customtkinter" \
    launcher.py
```

### Expected Features

Research identifies 9 table-stakes features for GUI v1, 7 enhancement features for v1.x, and 5 future considerations for v2+.

**Must have (table stakes — GUI v1):**
- **Profile creation form:** Replace questionary CLI wizard with labeled input fields (name, email, location, skills, titles, min_score) — users expect GUI forms, not terminal prompts
- **File upload dialog for resume:** Native OS file picker for optional PDF resume — standard desktop pattern, LOW complexity
- **Search configuration panel:** Date pickers, numeric input, checkboxes for search parameters — users expect to set parameters before running
- **Run/Start button:** Primary action, clear visual state (enabled/disabled/running) — single-click job search trigger
- **Progress feedback:** Progress bar with status text during 6-source query — visual indication during 10-30 second operations, MEDIUM complexity
- **Auto-open results in browser:** Use webbrowser.open() after search completes — CLI already does this, users expect same behavior
- **Edit profile access:** Button to modify existing profile without re-running wizard — update settings after initial creation
- **Input validation:** Client-side checks for required fields, valid formats, range limits — prevent invalid data before submission
- **Basic window layout:** Organized sections, clear visual hierarchy — professional appearance with dark/light theme support

**Should have (competitive — v1.x):**
- **Live CLI output display:** ScrolledText widget showing real-time progress from underlying CLI (stdout/stderr) — users want visibility during search
- **Date range presets:** Quick buttons for common filters (Today, Last 7 Days, Last 30 Days) — reduce repetitive date entry
- **Quick re-run with last settings:** One-click repeat with last parameters — common workflow optimization
- **Validation preview:** Summary panel showing what will be searched before running — "Searching 6 sources from X to Y with score >= Z"
- **Resume path indicator:** Label showing current resume filename if uploaded — users forget if they uploaded resume
- **Window state persistence:** Remember size/position across sessions — standard desktop UX
- **Keyboard shortcuts:** Ctrl+Enter to run, Esc to cancel — power user efficiency

**Defer (v2+ — future consideration):**
- **Search history:** View past searches and parameters — unclear if GUI users need history vs just re-running
- **Minimal UI mode:** Collapsible advanced options — wait to see if UI feels cluttered first
- **Profile export/import:** Share profiles across machines — wait for collaboration use case validation
- **Custom theming:** Additional color schemes beyond default dark/light — nice-to-have, not core functionality
- **Notification on completion:** OS notification when search finishes — searches are fast (<1 min), unclear value

**Anti-features (commonly requested but problematic):**
- **Inline results display:** Duplicates existing HTML report functionality, high complexity, defeats purpose of launcher (GUI is launcher not viewer)
- **Custom browser selection:** OS already handles default browser, unnecessary config burden
- **Advanced CLI flag exposure:** GUI becomes cluttered, defeats simplicity (keep CLI for power users)
- **Multi-profile switching:** High complexity, unclear demand for GUI users (single profile sufficient, CLI supports --profile for advanced use)

### Architecture Approach

The standard pattern for GUI wrappers is **separate presentation layer with shared business logic**. Job-Radar's existing modules (sources.py, scoring.py, report.py, profile_manager.py, config.py, cache.py) remain completely unchanged — both CLI and GUI call the same functions. This is enabled by the **MVP (Model-View-Presenter)** pattern where a Presenter layer coordinates between GUI events and business logic, passing GUI-specific callbacks (progress signal emitters) as parameters.

**Project structure:**
```
job_radar/
├── __main__.py              # CLI entry point (unchanged)
├── gui_main.py              # NEW: GUI entry point (separate from CLI)
├── search.py                # CLI frontend (unchanged)
├── gui/                     # NEW: GUI components
│   ├── main_window.py       # Main GUI window
│   ├── presenter.py         # Business logic coordinator
│   ├── workers.py           # Threading wrappers
│   └── widgets/             # Reusable components
├── sources.py               # Business logic (unchanged)
├── scoring.py               # Business logic (unchanged)
├── report.py                # Business logic (unchanged)
├── profile_manager.py       # Data layer (unchanged)
└── [other existing modules unchanged]
```

**Major components:**
1. **Entry Point Dispatcher:** Separate entry points for CLI (__main__.py) and GUI (gui_main.py) to avoid console window on Windows, prevent import overhead, and enable different PyInstaller configurations
2. **GUI Frontend (main_window.py):** Window management, widgets, event handling, visual feedback — calls Presenter for business logic, never calls sources/scoring directly
3. **Presenter Layer (presenter.py):** Bridges GUI events to business logic calls — wraps existing modules, enables unit testing without GUI, keeps business logic UI-agnostic
4. **Worker Threads (workers.py):** Background execution wrappers using threading.Thread + queue.Queue — fetches run in worker threads, communicate progress via queue, GUI polls queue with root.after(100, check_queue) to update UI
5. **Business Logic (unchanged):** Existing modules remain CLI-agnostic — accept optional callbacks for progress updates, return same data structures as before

**Threading model (critical for responsiveness):**
- **Rule:** Never block GUI main thread. Operations >100ms must run in worker threads.
- **Pattern:** Button click creates threading.Thread targeting worker function, worker calls presenter.run_search() which calls existing sources.fetch_all(), progress updates sent via queue.put(), main thread polls queue with root.after(100, check_queue) and updates progress bar
- **Integration with existing code:** sources.py already uses ThreadPoolExecutor internally for parallel source queries — this is compatible with GUI threading (Qt worker can spawn its own thread pool)

**Data flow (GUI mode):**
```
[User clicks "Search"]
  → [MainWindow creates threading.Thread]
  → [Thread runs in background]
  → [Presenter.run_search(profile)]
  → [fetch_all() from sources.py]
  → [Progress updates via queue.put()]
  → [GUI polls queue with root.after(100, check_queue)]
  → [Update progress bar in main thread]
  → [score_job() for each result]
  → [Results via queue.put()]
  → [Display results + open browser]
```

**Dual entry points strategy:**
- Separate executable scripts (job-radar for CLI with console=True, job-radar-gui for GUI with console=False)
- PyInstaller spec file with multiple Analysis/EXE objects sharing binaries
- Prevents console window appearing with GUI on Windows
- Prevents CLI startup slowdown from GUI imports
- Enables separate testing and packaging

### Critical Pitfalls

Based on comprehensive pitfall research across PyInstaller, GUI threading, and cross-platform distribution:

1. **UI Thread Blocking During Long Operations** — Job searches take 10-30 seconds (network I/O). Never call blocking functions directly in GUI event handlers or the window freezes. **Prevention:** Use threading.Thread + queue.Queue from Phase 1 (cannot retrofit later). Worker thread calls existing business logic, puts progress updates in queue, main thread polls with root.after(100, check_queue) and updates widgets only in main thread. **Warning signs:** GUI unresponsive during search, progress bar doesn't update, "Not Responding" in task manager. **Address in Phase 1 (GUI Foundation).**

2. **PyInstaller Missing Hidden Imports for GUI Framework** — CustomTkinter includes .json theme files and .otf fonts that PyInstaller doesn't automatically detect. Bundled executable crashes or displays blank/unstyled window. **Prevention:** Add --add-data flag explicitly for CustomTkinter directory in spec file, use --onedir mode (cannot use --onefile with CustomTkinter data files), test on clean machine without Python installed. **Warning signs:** Works in dev but crashes in bundle, missing styling/fonts in executable. **Address in Phase 2 (GUI Implementation).**

3. **Cross-Platform File Path Handling in Bundled Executable** — PyInstaller extracts files to temporary sys._MEIPASS directory at runtime. Hardcoded relative paths like "./icons/app.png" fail. Browser launching with file:// URLs doesn't work reliably across platforms. **Prevention:** Implement resource_path() helper function that checks sys._MEIPASS, always use absolute paths with file:// URLs, use platform-specific browser launch (open/xdg-open/os.startfile). **Warning signs:** Icons missing in bundle, browser doesn't open report, works on one platform but fails on another. **Address in Phase 2 (GUI Implementation).**

4. **macOS Code Signing and Notarization Failures** — Unsigned .app bundles get "App is damaged" Gatekeeper warnings. Hardened Runtime (required for notarization) causes "killed: 9" crashes with Python/NumPy/pdfplumber. **Prevention:** Enable com.apple.security.cs.allow-unsigned-executable-memory entitlement, sign with --options runtime and timestamp, notarize with xcrun notarytool, test on fresh macOS machine. Requires $99/year Apple Developer account. **Warning signs:** "App is damaged" on macOS, crashes immediately after launch with kill signal. **Address in Phase 3 (Packaging & Distribution).**

5. **Dual CLI/GUI Entry Point Conflicts** — Single entry point causes console window to appear with GUI on Windows (unprofessional), slow CLI startup from GUI imports, and argument parsing conflicts. **Prevention:** Separate gui_main.py and __main__.py entry points, PyInstaller spec file with multiple Analysis/EXE objects, lazy import GUI dependencies only in gui_main.py. **Warning signs:** Console window with GUI, GUI crashes on --help, only one executable produced. **Address in Phase 2 (GUI Implementation).**

6. **High DPI and Multi-Monitor Rendering Issues** — GUI blurry on Windows 150%+ scaling, text cut off on 4K monitors, window opens off-screen on multi-monitor setups. **Prevention:** CustomTkinter handles DPI automatically on Windows/macOS (sets SetProcessDpiAwareness), implement safe_window_geometry() with bounds checking for saved positions, test on high-DPI displays. **Warning signs:** Blurry text on Windows, widgets cut off on 4K, window off-screen after monitor change. **Address in Phase 2 (GUI Implementation).**

7. **GUI Testing Strategy Gaps** — Existing 452 pytest tests use mocking for CLI, don't cover GUI code. GUI tests fail in CI/CD without display. Manual testing doesn't catch cross-platform issues. **Prevention:** Three-tier strategy (80% unit tests for business logic, 15% integration tests with xvfb, 5% manual visual testing), set up xvfb in GitHub Actions with pytest-xvfb or GabrielBB/xvfb-action, extract testable logic from GUI handlers. **Warning signs:** GUI has 0% coverage, tests pass but GUI broken in release. **Address in Phase 2 (GUI Implementation) before first PR merge.**

## Implications for Roadmap

Based on research, suggested 3-phase structure optimized for rapid GUI delivery while maintaining CLI stability:

### Phase 1: GUI Foundation & Threading
**Rationale:** Must establish non-blocking UI pattern from the start — retrofitting threading is expensive. This phase builds the skeleton with correct architectural patterns before adding features.

**Delivers:** Empty GUI window that launches separately from CLI, basic threading infrastructure proven with mock long-running operations, entry point dispatcher working correctly.

**Addresses features:**
- Entry point separation (prevents console window with GUI)
- Threading pattern established (prevents UI freezing)
- Basic window layout (provides canvas for Phase 2)

**Avoids pitfalls:**
- Pitfall 1 (UI thread blocking) — threading pattern correct from start
- Pitfall 5 (dual entry point conflicts) — separate gui_main.py established
- Pitfall 10 (thread-unsafe GUI updates) — root.after() pattern enforced

**Implementation notes:**
- Install CustomTkinter 5.2.2
- Create gui_main.py with empty CTk window + "Test" button
- Implement threading.Thread + queue.Queue pattern with mock 10-second operation
- Modify pyproject.toml/setup.py to add gui-scripts entry point
- Test: GUI launches without console, button doesn't freeze window during mock operation

**Research flags:** None — standard patterns, well-documented.

---

### Phase 2: GUI Implementation
**Rationale:** Build complete feature set with threading foundation in place. Group all GUI features in one phase because they share components (forms reused for create/edit, progress bar used by search, file dialog integrated with form).

**Delivers:** Fully functional GUI launcher matching CLI feature parity — users never need terminal for standard workflows.

**Addresses features (all 9 table stakes):**
- Profile creation form (text fields, dropdowns)
- File upload dialog for resume (native OS picker)
- Search configuration panel (date range, min score, new-only checkbox)
- Run button with state management (enabled/disabled/running)
- Progress feedback (progress bar + status text "Querying LinkedIn...")
- Auto-open browser (webbrowser.open for HTML report)
- Edit profile access (reuses creation form, pre-populated)
- Input validation (client-side checks before submission)

**Uses stack elements:**
- CustomTkinter for all widgets (CTkEntry, CTkButton, CTkProgressBar)
- tkinter.filedialog for native file picker
- threading.Thread + queue.Queue (foundation from Phase 1)
- webbrowser module for browser launch
- Existing business logic modules unchanged (sources.py, scoring.py, report.py)

**Implements architecture components:**
- gui/main_window.py (complete window layout)
- gui/presenter.py (bridges GUI events to business logic)
- gui/workers.py (SearchWorker wrapping existing search operations)
- gui/widgets/ (ProfileForm, SearchPanel, ProgressIndicator)

**Avoids pitfalls:**
- Pitfall 2 (PyInstaller imports) — configure spec file with --add-data for CustomTkinter
- Pitfall 3 (file paths) — implement resource_path() helper for icons/assets
- Pitfall 6 (GUI testing) — set up xvfb in CI, write integration tests for critical paths
- Pitfall 7 (high DPI) — test on 4K/Retina displays, verify CustomTkinter auto-scaling works
- Pitfall UX (console window) — verify gui-scripts entry point works on Windows

**Implementation notes:**
- Create profile_form.py widget (reused for create and edit modes)
- Wire form to profile_manager.load_profile() and profile_manager.save_profile()
- Implement SearchWorker that calls presenter.run_search() in thread, emits progress via queue
- Add progress bar update logic in check_queue() callback
- Test browser launch on Windows, macOS, Linux with local HTML files
- Configure GitHub Actions with xvfb-action for GUI tests
- Test on high-DPI Windows machine (150%+ scaling) and macOS Retina display

**Research flags:** None — GUI wrapper patterns well-documented, CustomTkinter examples available for all required widgets.

---

### Phase 3: Packaging & Distribution
**Rationale:** Production-ready executables with proper code signing and cross-platform testing. Separated from implementation to allow GUI feature stabilization before tackling platform-specific packaging complexities.

**Delivers:** Distributable executables for Windows (.exe), macOS (.app bundle), and Linux (AppImage or .deb), with code signing for macOS, installer scripts, and release automation.

**Addresses:**
- PyInstaller spec file configuration for dual executables (job-radar CLI, job-radar-gui GUI)
- macOS code signing with entitlements.plist (unsigned executable memory for Python)
- Notarization workflow with xcrun notarytool
- Windows installer (optional, can use onedir distribution)
- Cross-platform testing checklist (Windows 10/11, macOS 12+, Ubuntu/Fedora)
- CI/CD integration for automated builds on all platforms

**Avoids pitfalls:**
- Pitfall 4 (macOS code signing) — implement signing workflow with proper entitlements
- Pitfall 2 (PyInstaller imports) — verify CustomTkinter data files included correctly
- Pitfall 3 (file paths) — test resource_path() in bundled executables
- Pitfall 7 (high DPI) — test on various display scaling factors

**Implementation notes:**
- Create job-radar.spec with two EXE objects (CLI console=True, GUI console=False)
- Add CustomTkinter to --add-data in spec file
- Create entitlements.plist with com.apple.security.cs.allow-unsigned-executable-memory
- Set up codesign and notarytool in build scripts (macOS-specific)
- Test bundled executables on clean machines (no Python installed)
- Document distribution process in DISTRIBUTION.md (upload to GitHub Releases, Homebrew/Chocolatey/apt instructions)

**Research flags:**
- **macOS code signing:** May need deeper research if notarization fails — Apple's requirements change frequently, need to verify current 2026 workflow.
- **Linux packaging:** Standard patterns exist but distribution format choice (AppImage vs .deb vs Flatpak) may need user feedback validation.

---

### Phase Ordering Rationale

- **Threading first (Phase 1):** Cannot add threading to a synchronous GUI later without rewriting event handlers. Must establish correct patterns before adding features.
- **All GUI features together (Phase 2):** Features share components (forms, progress bar, validation logic), grouping avoids partial GUI states. Users need complete feature set for CLI parity.
- **Packaging last (Phase 3):** GUI must be stable before tackling platform-specific distribution. Code signing requires functional app to test. Separating allows feature iteration without build script churn.

**Dependency chain:**
1. Phase 1 threading → enables Phase 2 non-blocking search
2. Phase 2 GUI implementation → provides artifact for Phase 3 packaging
3. Phase 3 packaging → delivers distributable executables

**Pitfall avoidance strategy:**
- Critical pitfalls (1, 5, 10) addressed in Phase 1 foundation
- Implementation pitfalls (2, 3, 6, 7) addressed during Phase 2 feature development
- Distribution pitfalls (4) addressed in Phase 3 packaging

**Alternative orderings considered:**
- ❌ Packaging before GUI complete: Wastes effort on bundling incomplete features
- ❌ Features across multiple phases: Creates partial GUI states, harder to test, unclear when "GUI is ready"
- ❌ Threading deferred: Frozen GUI forces architectural rework later

### Research Flags

**Phases with standard patterns (skip /gsd:research-phase):**
- **Phase 1 (GUI Foundation):** Threading with GUI is well-documented, CustomTkinter docs cover setup, entry point separation standard pattern
- **Phase 2 (GUI Implementation):** GUI wrapper architecture extensively documented, CustomTkinter examples exist for all required widgets, existing business logic unchanged

**Phases likely needing targeted research:**
- **Phase 3 (Packaging - macOS only):** Code signing and notarization requirements change frequently with macOS updates. May need verification of 2026-specific entitlements and notarization workflow if Apple has introduced new requirements. Initial research shows com.apple.security.cs.allow-unsigned-executable-memory entitlement required for Python, but this should be validated against current macOS 14/15 Gatekeeper requirements.
- **Phase 3 (Packaging - Linux distribution format):** Multiple options exist (AppImage, .deb, Flatpak, Snap) with different trade-offs. May need user feedback or competitive analysis to choose distribution format. Initial research suggests AppImage for universal compatibility, but desktop integration quality varies.

**When to trigger research-phase:**
- Phase 3 macOS: If first code signing attempt fails notarization, trigger `/gsd:research-phase "macOS notarization failures for Python PyInstaller apps 2026"` to debug Apple's current requirements
- Phase 3 Linux: If team unsure about distribution format, trigger `/gsd:research-phase "Linux desktop app distribution formats comparison 2026"` to evaluate AppImage vs alternatives

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | CustomTkinter recommendation based on official docs, PyInstaller integration documented, existing project already uses PyInstaller successfully. Framework choice resolves disagreement with clear rationale based on project context (launcher, bundle size, PyInstaller compatibility). |
| Features | **MEDIUM** | Table stakes features well-established from GUI wrapper research and job search app patterns. Feature prioritization based on reasonable assumptions but actual user preferences not validated. Anti-features list is opinionated — some users may want inline results display despite complexity. |
| Architecture | **HIGH** | MVP pattern for GUI wrappers is well-documented standard approach. Threading pattern proven in many Tkinter applications. Integration with existing business logic straightforward (callback parameters, no module changes). Project structure follows established Python package layouts. |
| Pitfalls | **HIGH** | All critical pitfalls sourced from official documentation (PyInstaller, Apple Developer), Stack Overflow canonical answers, and real-world issue reports. Threading pitfall extensively documented in GUI framework guides. macOS code signing process verified with 2026 sources. Testing strategies validated against pytest-xvfb documentation. |

**Overall confidence:** **HIGH**

### Gaps to Address

**During planning/execution:**

1. **Feature prioritization validation:** Feature list is research-based but not user-validated. Consider quick user survey or feedback session after Phase 2 MVP to validate which v1.x features to prioritize (live CLI output vs date presets vs quick re-run). **Mitigation:** Ship Phase 2 as beta, collect feedback, adjust v1.x priorities.

2. **macOS code signing account:** Research assumes Apple Developer account available ($99/year). If team doesn't have account, Phase 3 will need to defer macOS distribution or accept Gatekeeper warnings. **Mitigation:** Verify account status before starting Phase 3, budget for account if needed.

3. **Linux distribution format choice:** Research identifies multiple options (AppImage, .deb, Flatpak) but doesn't commit to one. Each has trade-offs (AppImage = portable but large, .deb = smaller but Ubuntu-specific, Flatpak = sandboxed but desktop integration issues). **Mitigation:** Start with AppImage (most universal), add .deb later if Ubuntu users request it.

4. **CustomTkinter long-term maintenance:** CustomTkinter is maintained by single developer (TomSchimansky on GitHub). Not a large foundation-backed project like PyQt. Repository is active (2026 commits) but bus-factor risk exists. **Mitigation:** CustomTkinter is thin wrapper over tkinter (which is Python stdlib, maintained indefinitely). If abandoned, can migrate to tkinter or fork CustomTkinter. Risk is acceptable for project scope.

5. **High-DPI testing hardware access:** Research shows CustomTkinter handles DPI automatically but requires testing on 4K Windows (150%+ scaling) and macOS Retina displays. Team may not have access to diverse hardware. **Mitigation:** Use virtual machines or cloud desktops (AWS WorkSpaces, Azure Virtual Desktop) for cross-platform testing. Add to Phase 2 testing checklist.

6. **CI/CD platform for multi-platform builds:** Phase 3 requires building on Windows, macOS, and Linux. GitHub Actions supports all three (windows-latest, macos-latest, ubuntu-latest runners). Research assumes GitHub Actions — if using different CI (GitLab, Jenkins), configuration will differ. **Mitigation:** Document GitHub Actions workflow in Phase 3, adapt to other CI if needed.

**No validation required (HIGH confidence):**
- Threading pattern (extensively documented, proven in production)
- PyInstaller bundling (existing project already uses it successfully)
- MVP architecture (standard pattern, well-documented)
- CustomTkinter integration (official documentation covers PyInstaller setup)

## Sources

### Primary (HIGH confidence)

**Stack & Framework Selection:**
- [CustomTkinter Official Documentation](https://customtkinter.tomschimansky.com/) — API reference, PyInstaller packaging guide, widget examples
- [CustomTkinter GitHub Repository](https://github.com/TomSchimansky/CustomTkinter) — Official source, issue tracker for PyInstaller integration
- [PyInstaller 6.18.0 Documentation](https://pyinstaller.org/en/stable/) — Latest bundling guidelines (Jan 2026)
- [Python Tkinter Documentation](https://docs.python.org/3/library/tkinter.html) — Official Python stdlib docs for base toolkit
- [Python GUI Library Comparison 2026](https://www.pythonguis.com/faq/which-python-gui-library/) — Framework selection analysis
- [PyQt6 vs PySide6 Licensing](https://www.pythonguis.com/faq/pyqt6-vs-pyside6/) — Commercial use constraints for Qt frameworks

**Architecture & Threading:**
- [Multithreading PyQt6 applications with QThreadPool](https://www.pythonguis.com/tutorials/multithreading-pyqt6-applications-qthreadpool/) — Complete working examples (Qt patterns)
- [Use PyQt's QThread to Prevent Freezing GUIs](https://realpython.com/python-pyqt-qthread/) — Best practices for non-blocking GUI
- [Tkinter and Threading: Building Responsive Python GUI Applications](https://medium.com/tomtalkspython/tkinter-and-threading-building-responsive-python-gui-applications-02eed0e9b0a7) — Tkinter-specific threading patterns
- [A Clean Architecture for a PyQT GUI Using the MVP Pattern](https://medium.com/@mark_huber/a-clean-architecture-for-a-pyqt-gui-using-the-mvp-pattern-78ecbc8321c0) — Presenter pattern implementation
- [Model-View-ViewModel (MVVM) Pattern in Python](https://softwarepatternslexicon.com/patterns-python/4/9/) — Alternative architectural pattern comparison

**Pitfalls & Cross-Platform:**
- [Packaging with PyInstaller - CustomTkinter Discussion #939](https://github.com/TomSchimansky/CustomTkinter/discussions/939) — Hidden imports and data files
- [PyInstaller on macOS frustration](https://www.pythonguis.com/faq/pyinstaller-on-macos-frustration/) — macOS-specific packaging issues
- [Signing and notarizing a Python macOS UI application](https://haim.dev/posts/2020-08-08-python-macos-app/) — Complete code signing workflow
- [Gatekeeper and runtime protection in macOS](https://support.apple.com/guide/security/gatekeeper-and-runtime-protection-sec5599b66df/web) — Apple's official security documentation
- [When Things Go Wrong - PyInstaller Documentation](https://pyinstaller.org/en/stable/when-things-go-wrong.html) — Official debugging guide

**Testing:**
- [5 Effective Methods for Functional Testing a Python Tkinter Application](https://blog.finxter.com/5-effective-methods-for-functional-testing-a-python-tkinter-application/) — Tkinter testing strategies
- [How to run headless unit tests for GUIs on GitHub actions](https://arbitrary-but-fixed.net/2022/01/21/headless-gui-github-actions.html) — xvfb setup for CI
- [GabrielBB/xvfb-action](https://github.com/marketplace/actions/gabrielbb-xvfb-action) — GitHub Actions integration for GUI tests
- [pytest-qt Troubleshooting](https://pytest-qt.readthedocs.io/en/latest/troubleshooting.html) — Qt-specific test configuration (patterns applicable to tkinter)

### Secondary (MEDIUM confidence)

**Feature Patterns:**
- [Command Line Interface Guidelines](https://clig.dev/) — Best practices for CLI design that inform wrapper behavior
- [Microsoft: Progress Controls Guidelines](https://learn.microsoft.com/en-us/windows/apps/design/controls/progress-controls) — Determinate vs indeterminate progress patterns
- [NN/G: Wizards Design Recommendations](https://www.nngroup.com/articles/wizards/) — When to use wizards vs forms
- [Wizard UI Pattern Best Practices 2026](https://lollypop.design/blog/2026/january/wizard-ui-design/) — Step structure, progress indicators
- [Best Job Board Aggregators Guide](https://www.chiefjobs.com/the-best-job-board-aggregators-in-the-us-a-comprehensive-guide/) — Common features in job aggregation tools (2026)
- [Top Job Search Apps 2026](https://www.eztrackr.app/blog/best-job-search-apps) — Feature comparison of leading apps

**Implementation Patterns:**
- [Run Process with Realtime Output to Tkinter](https://www.tutorialspoint.com/run-process-with-realtime-output-to-a-tkinter-gui) — Threading + subprocess for live output
- [Using Tkinter With ThreadPoolExecutor Class](https://python-forum.io/thread-38963.html) — Integration with existing executor
- [Python File Upload Dialog Patterns](https://pythonguides.com/upload-a-file-in-python-tkinter/) — Tkinter file selection implementation
- [Entry points specification](https://packaging.python.org/specifications/entry-points/) — console_scripts vs gui_scripts
- [Using PyInstaller Spec Files](https://pyinstaller.org/en/stable/spec-files.html) — Advanced configuration

**UX & Design:**
- [Minimalist UI Design Principles](https://www.stan.vision/journal/minimalist-ui-design-how-less-is-more-in-web-design) — Simplicity, whitespace, clarity
- [IxDF: UI Form Design 2026](https://www.interaction-design.org/literature/article/ui-form-design) — Modern form design best practices
- [User Interface Anti-Patterns](https://ui-patterns.com/blog/User-Interface-AntiPatterns) — Bloated UI, hide-and-hover pitfalls
- [UX Patterns for CLI Tools](https://lucasfcosta.com/2022/06/01/ux-patterns-cli-tools.html) — What to avoid when wrapping CLI tools

**High DPI & Multi-Monitor:**
- [Scaling - CustomTkinter Wiki](https://github.com/TomSchimansky/CustomTkinter/wiki/Scaling) — DPI handling in CustomTkinter
- [How to improve Tkinter window resolution](https://coderslegacy.com/python/problem-solving/improve-tkinter-resolution/) — DPI awareness configuration
- [Python Tkinter: Multi-Monitor Display 2026](https://copyprogramming.com/howto/how-to-open-tkinter-gui-on-second-monitor-display-windows) — Multi-monitor positioning

### Tertiary (LOW confidence)

**Distribution & Packaging:**
- [2026 Showdown: PyInstaller vs. cx_Freeze vs. Nuitka](https://ahmedsyntax.com/2026-comparison-pyinstaller-vs-cx-freeze-vs-nui/) — Bundler comparison (biased toward Nuitka)
- [How to Create a GUI/CLI Standalone App with Gooey and PyInstaller](https://medium.com/analytics-vidhya/how-to-create-a-gui-cli-standalone-app-in-python-with-gooey-and-pyinstaller-1a21d0914124) — Gooey framework (not recommended for this project but dual-mode pattern useful)

**General Patterns:**
- [Software Bloat - Wikipedia](https://en.wikipedia.org/wiki/Software_bloat) — Feature creep characteristics (general software engineering, not GUI-specific)
- [UX Anti-Patterns of User Experience Design](https://www.ics.com/blog/anti-patterns-user-experience-design) — General UX mistakes (not desktop app specific)

---
*Research completed: 2026-02-12*
*Ready for roadmap: yes*
