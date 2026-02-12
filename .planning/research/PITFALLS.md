# Pitfalls Research

**Domain:** Adding Desktop GUI to Existing Python CLI Application
**Researched:** 2026-02-12
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: UI Thread Blocking During Long Operations

**What goes wrong:**
The GUI completely freezes when existing CLI job search operations run, making the application appear crashed. Users cannot interact with the window, see progress updates, or cancel operations. This is particularly critical for Job Radar's job fetching operations that use ThreadPoolExecutor.

**Why it happens:**
Tkinter applications are single-threaded by default. All GUI updates and event handling occur in the main thread. When you directly call long-running CLI functions (job searching, PDF parsing) from the GUI event handlers, the main thread becomes blocked processing the task and cannot respond to user interactions or update the progress bar.

**How to avoid:**
1. **Never directly modify Tkinter widgets from worker threads** - Use `root.after()` to schedule GUI updates in the main thread
2. **Use queue-based communication** - Worker threads put results in `queue.Queue`, main thread polls with `root.after(100, check_queue)`
3. **Integrate existing ThreadPoolExecutor carefully** - Submit tasks to executor, use callbacks with `future.add_done_callback()` that schedule GUI updates via `root.after(0, update_function)`
4. **Example pattern:**
   ```python
   def on_search_clicked():
       self.executor.submit(search_jobs).add_done_callback(
           lambda future: root.after(0, self.display_results, future.result())
       )
   ```

**Warning signs:**
- GUI becomes unresponsive during operations
- Progress bar doesn't update
- Window shows "Not Responding" in task manager
- Users report application appears to hang

**Phase to address:**
Phase 1 (GUI Foundation) - Establish thread-safe GUI update patterns from the start. Test with actual job search operations to verify responsiveness.

---

### Pitfall 2: PyInstaller Missing Hidden Imports for GUI Framework

**What goes wrong:**
The bundled executable launches but crashes immediately with ImportError or displays blank window because PyInstaller didn't detect and bundle required GUI framework data files (.json, .otf fonts for CustomTkinter) or dynamic imports.

**Why it happens:**
PyInstaller uses static analysis to detect imports. GUI frameworks often use dynamic imports (`__import__()`, `importlib.import_module()`) or include non-.py assets (JSON configs, fonts, themes) that PyInstaller doesn't automatically detect. Job Radar already has hidden import complexity with pdfplumber and questionary - adding a GUI framework multiplies this risk.

**How to avoid:**
1. **Use --onedir mode for GUI frameworks** - Cannot use --onefile with CustomTkinter because it includes .json and .otf files that cannot be packed into single executable
2. **Add explicit hidden imports in spec file:**
   ```python
   hiddenimports=[
       'customtkinter',  # or tkinter.ttk for themed widgets
       'PIL._tkinter_finder',  # if using images
   ]
   ```
3. **Include data files with --add-data:**
   ```python
   datas=[
       ('path/to/customtkinter', 'customtkinter'),  # entire directory
   ]
   ```
4. **Test with --debug=imports flag** - Build with debug, run executable, examine output for missing imports
5. **Verify on clean machine** - Test bundled executable on machine without Python installed

**Warning signs:**
- Executable builds successfully but crashes on launch
- "ModuleNotFoundError" in bundled app but works in development
- GUI window appears but has no styling/theme
- Fonts missing or widgets display incorrectly

**Phase to address:**
Phase 2 (GUI Implementation) - Configure PyInstaller spec file with GUI framework requirements before building first prototype. Document in build scripts (build.sh, build.bat).

---

### Pitfall 3: Cross-Platform File Path Handling in Bundled Executable

**What goes wrong:**
File dialogs, browser launching with local files, and resource loading (icons, images) fail on bundled executable or work on one platform but break on others. Critical for Job Radar's browser launch functionality and any GUI icons/assets.

**Why it happens:**
PyInstaller extracts bundled files to temporary directory (`sys._MEIPASS`) at runtime. Hardcoded relative paths like `"./icons/app.png"` fail because working directory != bundle location. Additionally, `webbrowser.open()` with `file://` URLs doesn't work reliably across platforms - macOS uses `open`, Linux uses `xdg-open`, Windows uses `os.startfile()`, and all have different behaviors with file URLs.

**How to avoid:**
1. **Use resource_path helper function:**
   ```python
   def resource_path(relative_path):
       """Get absolute path to resource, works for dev and PyInstaller."""
       if hasattr(sys, '_MEIPASS'):
           return os.path.join(sys._MEIPASS, relative_path)
       return os.path.join(os.path.abspath('.'), relative_path)

   icon = resource_path('resources/icon.png')
   ```
2. **For browser launching, use platform-specific approach:**
   ```python
   import platform
   if platform.system() == 'Darwin':  # macOS
       subprocess.run(['open', file_path])
   elif platform.system() == 'Windows':
       os.startfile(file_path)
   else:  # Linux
       subprocess.run(['xdg-open', file_path])
   ```
3. **Always use absolute paths with file:// URLs:** Use `os.path.realpath()` not relative paths
4. **Add resources to spec file datas section:**
   ```python
   datas=[
       ('resources', 'resources'),  # source:dest
   ]
   ```

**Warning signs:**
- FileNotFoundError for icons/images in bundled executable
- Browser doesn't open or opens wrong file
- Works in development but fails in .exe/.app bundle
- Different behavior on Windows vs macOS vs Linux

**Phase to address:**
Phase 2 (GUI Implementation) - Establish resource path patterns when adding first GUI assets. Test browser launch functionality on all target platforms early.

---

### Pitfall 4: macOS Code Signing and Notarization Failures

**What goes wrong:**
macOS Gatekeeper blocks unsigned .app bundle with "App is damaged and can't be opened" or users must right-click > Open to bypass security warnings. Hardened Runtime causes crashes with "killed: 9" when importing NumPy or other scientific libraries. App bundle structure violations fail notarization.

**Why it happens:**
macOS requires code signing for distribution. Unsigned apps get quarantine attribute and Gatekeeper warnings. Hardened Runtime (required for notarization) restricts memory operations that PyInstaller and libraries like NumPy/pdfplumber rely on. Incorrect bundle structure (e.g., putting .pkg files in Contents/Helpers instead of Contents/Resources) causes signing validation failures.

**How to avoid:**
1. **Enable unsigned executable memory entitlement for Python apps:**
   ```xml
   <!-- entitlements.plist -->
   <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
   <true/>
   ```
2. **Sign with timestamp and hardened runtime:**
   ```bash
   codesign --deep --force --options runtime --timestamp \
     --entitlements entitlements.plist \
     --sign "Developer ID Application: Your Name" \
     dist/YourApp.app
   ```
3. **Notarize before distribution:**
   ```bash
   # Zip, submit, wait for approval
   xcrun notarytool submit YourApp.zip --wait
   # Staple ticket to bundle
   xcrun stapler staple YourApp.app
   ```
4. **Place all data files in Contents/Resources** - NOT Contents/Helpers (code only)
5. **Test unsigned flow first** - Use `xattr -dr com.apple.quarantine YourApp.app` to remove quarantine for testing
6. **Budget for $99/year Apple Developer account** - Required for signing certificates

**Warning signs:**
- "App is damaged" message on macOS
- App crashes with "killed: 9" immediately after launch
- Notarization submission rejected
- Different behavior between signed and unsigned builds
- Works on your Mac but not on users' Macs

**Phase to address:**
Phase 3 (Packaging & Distribution) - Set up code signing workflow after GUI is stable. Start with unsigned testing, then add signing, finally notarization. Document in build scripts.

---

### Pitfall 5: Dual CLI/GUI Entry Point Conflicts

**What goes wrong:**
Both CLI and GUI entry points try to parse command-line arguments, causing conflicts. GUI launches with unwanted console window on Windows or CLI breaks when GUI dependencies are imported. Build scripts produce only one executable instead of both.

**Why it happens:**
Single entry point means shared initialization code. On Windows, `console_scripts` attach to console (shows terminal), `gui_scripts` don't (no terminal). PyInstaller spec files typically define one entry point. Importing GUI frameworks in CLI code adds unnecessary dependencies and startup time.

**How to avoid:**
1. **Separate entry point modules:**
   ```
   job_radar/
     __main__.py       # CLI entry point
     gui_main.py       # GUI entry point
     cli/              # CLI-specific code
     gui/              # GUI-specific code
     core/             # Shared business logic
   ```
2. **Configure separate scripts in pyproject.toml:**
   ```toml
   [project.scripts]
   job-radar = "job_radar.__main__:main"  # CLI

   [project.gui-scripts]
   job-radar-gui = "job_radar.gui_main:main"  # GUI (no console on Windows)
   ```
3. **PyInstaller spec file with multiple executables:**
   ```python
   # Create separate Analysis objects
   cli_a = Analysis(['job_radar/__main__.py'], ...)
   gui_a = Analysis(['job_radar/gui_main.py'], ...)

   # Separate EXE objects
   cli_exe = EXE(PYZ(cli_a.pure), cli_a.scripts, name='job-radar', console=True)
   gui_exe = EXE(PYZ(gui_a.pure), gui_a.scripts, name='job-radar-gui', console=False)

   # Single COLLECT with both
   COLLECT(cli_exe, gui_exe, ...)
   ```
4. **Lazy import GUI dependencies** - Only import tkinter/customtkinter in gui_main.py, not in shared core
5. **Conditional argument parsing:**
   ```python
   # CLI entry
   if __name__ == '__main__':
       args = parse_cli_args()
       run_cli(args)

   # GUI entry - no argparse
   if __name__ == '__main__':
       launch_gui()
   ```

**Warning signs:**
- Console window appears when launching GUI on Windows
- GUI crashes on CLI arguments like `--help`
- Only one executable produced by build script
- CLI becomes slower after adding GUI dependencies
- Import errors when running CLI without GUI dependencies installed

**Phase to address:**
Phase 2 (GUI Implementation) - Design separation immediately when creating gui_main.py. Update build scripts to produce both executables.

---

### Pitfall 6: GUI Testing Strategy Gaps

**What goes wrong:**
Existing 452 pytest tests all use mocking and don't cover GUI code. GUI tests fail in CI/CD because no display available. Manual testing doesn't catch cross-platform visual differences. Regression testing becomes manual and incomplete.

**Why it happens:**
GUI testing requires different strategies than CLI testing. Tkinter expects display (headless CI fails). Heavy mocking of GUI widgets tests nothing useful. Visual layout differences across platforms aren't caught by unit tests. Team's existing pytest expertise focuses on I/O mocking, not GUI interaction patterns.

**How to avoid:**
1. **Three-tier testing strategy:**
   - **Unit tests (80%):** Test GUI-independent logic (validators, formatters, business rules) with existing pytest/mock approach
   - **Integration tests (15%):** Test GUI event handlers with minimal widget mocking using pytest with xvfb
   - **Manual tests (5%):** Platform-specific visual verification checklist

2. **Headless CI setup for GitHub Actions:**
   ```yaml
   - name: Install xvfb for GUI tests
     run: sudo apt-get install -y xvfb libxkbcommon-x11-0

   - name: Run GUI tests headless
     run: xvfb-run python -m pytest tests/gui/
     env:
       DISPLAY: :99
   ```
   Or use `pytest-xvfb` plugin which handles setup automatically

3. **Use GabrielBB/xvfb-action for simpler setup:**
   ```yaml
   - uses: GabrielBB/xvfb-action@v1
     with:
       run: pytest tests/gui/
   ```

4. **Minimal GUI mocking approach:**
   ```python
   # Good: Test logic extracted from GUI
   def test_validate_search_params():
       assert validate_query("Python Developer") == True
       assert validate_query("") == False

   # Acceptable: Test handler behavior
   def test_search_button_handler(mocker):
       mock_search = mocker.patch('job_radar.core.search_jobs')
       handler = SearchHandler()
       handler.on_search_clicked("Python")
       mock_search.assert_called_once_with("Python")

   # Avoid: Deep widget hierarchy mocking (brittle, low value)
   ```

5. **Cross-platform visual testing checklist (manual):**
   - [ ] Font rendering (Windows vs macOS vs Linux)
   - [ ] High DPI scaling (4K, Retina displays)
   - [ ] Window sizing on different screen resolutions
   - [ ] Dark mode appearance (if supported)
   - [ ] Dialog button order (OK/Cancel varies by platform)

6. **Add smoke test for GUI importability:**
   ```python
   def test_gui_imports():
       """Ensure GUI module can be imported without display."""
       import sys
       sys.modules['tkinter'] = MagicMock()  # Mock before import
       from job_radar import gui_main  # Should not crash
   ```

**Warning signs:**
- GUI code has 0% test coverage
- Tests pass in CI but GUI broken in release
- Regressions caught only by users
- "Works on my machine" syndrome
- Team avoids touching GUI code due to fear of breaking

**Phase to address:**
Phase 2 (GUI Implementation) - Extract testable logic from start. Set up xvfb in CI before first GUI PR. Phase 3 (Packaging) - Add cross-platform visual testing checklist to release process.

---

### Pitfall 7: High DPI and Multi-Monitor Rendering Issues

**What goes wrong:**
GUI looks blurry on Windows with 150%+ scaling. Text cut off on 4K monitors. App opens on wrong monitor or off-screen on multi-monitor setups. Layout breaks on macOS Retina displays. Job Radar's progress bar and form layout become unusable.

**Why it happens:**
Windows requires DPI awareness flag or apps default to bitmap scaling (blurry). Tkinter has inconsistent DPI handling across platforms. CustomTkinter auto-handles DPI on Windows but requires manual configuration for custom scaling. Window geometry restoration saves screen coordinates that become invalid when monitor setup changes. macOS handles Retina automatically, but Windows and Linux don't.

**How to avoid:**
1. **CustomTkinter handles DPI automatically on Windows and macOS:**
   - Windows: Sets `windll.shcore.SetProcessDpiAwareness(2)` automatically
   - macOS: Tk handles Retina scaling automatically
   - Both platforms detect scaling factor and scale widgets

2. **For manual control (if needed):**
   ```python
   import customtkinter as ctk

   # Set widget scaling (affects dimensions and text)
   ctk.set_widget_scaling(1.0)  # 1.0 = 100%, 1.5 = 150%

   # Set window scaling (affects geometry)
   ctk.set_window_scaling(1.0)
   ```

3. **Don't disable DPI awareness** - Causes blurriness on Windows >100% scaling

4. **Window positioning with multi-monitor safety:**
   ```python
   def safe_window_geometry(self, saved_geometry):
       """Restore geometry with bounds checking."""
       try:
           # Parse saved geometry: "800x600+100+50"
           self.geometry(saved_geometry)

           # Check if window is visible on any screen
           self.update_idletasks()
           x = self.winfo_x()
           y = self.winfo_y()
           screen_width = self.winfo_screenwidth()
           screen_height = self.winfo_screenheight()

           # If off-screen, center instead
           if x < 0 or y < 0 or x > screen_width or y > screen_height:
               self.center_window()
       except:
           self.center_window()  # Fallback to centered

   def center_window(self):
       """Center window on screen."""
       self.update_idletasks()
       width = self.winfo_width()
       height = self.winfo_height()
       screen_width = self.winfo_screenwidth()
       screen_height = self.winfo_screenheight()
       x = (screen_width - width) // 2
       y = (screen_height - height) // 2
       self.geometry(f"{width}x{height}+{x}+{y}")
   ```

5. **Test on different scaling factors:**
   - Windows: 100%, 125%, 150%, 200%
   - macOS: Retina (2x) and non-Retina
   - Linux: Various desktop environments (GNOME, KDE)

6. **Use relative widget sizing, not absolute pixels:**
   ```python
   # Good: Relative to parent
   frame.pack(fill='both', expand=True)

   # Avoid: Hard-coded pixels
   frame.place(x=100, y=50, width=800, height=600)
   ```

**Warning signs:**
- Blurry text on Windows high-DPI displays
- Widgets cut off or overlapping on 4K monitors
- Window opens off-screen after monitor change
- Different layout on developer's monitor vs user's monitor
- Text too small on macOS Retina displays

**Phase to address:**
Phase 2 (GUI Implementation) - Use CustomTkinter (includes DPI handling), test on high-DPI display early. Phase 3 (Packaging) - Add multi-monitor and DPI testing to cross-platform checklist.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Blocking GUI calls to CLI functions | Fast to implement, reuses existing code | Frozen UI, poor UX, difficult to refactor | Never - always use threading from start |
| Hardcoded file paths instead of resource_path() | Works in development | Breaks in bundled executable | Never - set pattern in first prototype |
| Single entry point for CLI and GUI | One build script, simpler structure | Console window on GUI, slow CLI startup, harder to maintain | Never for this project - different execution contexts |
| Skipping xvfb CI setup "until GUI is complete" | Faster initial CI runs | No GUI test coverage, regressions slip through | Only if team commits to adding before Phase 2 merge |
| Using Tkinter instead of CustomTkinter | Built-in, no dependencies | Dated appearance, manual DPI handling, more platform-specific code | Small internal tools, but not user-facing apps in 2026 |
| Mocking entire GUI for tests | High test coverage number | Tests don't catch real issues, false confidence | Only for extracted business logic, not widget interactions |
| Manual code signing workflow | No upfront setup cost | Inconsistent releases, manual errors, unsigned builds slip out | Early prototypes only - automate before Phase 3 |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| PyInstaller + GUI framework | Using --onefile with CustomTkinter | Use --onedir, explicitly add data files with --add-data |
| PyInstaller + existing ThreadPoolExecutor | Assuming executor works identically in bundle | Test threading in bundled executable - some platforms need initialization changes |
| Browser launching from GUI | Using webbrowser.open() for local files | Platform-specific commands (open/xdg-open/startfile) with absolute paths |
| System file dialogs | Using tkinter.filedialog without parent window | Always pass parent: `filedialog.askopenfilename(parent=root)` |
| macOS .app bundle + data files | Putting resources in Contents/Helpers | Use Contents/Resources for data, Helpers for code only |
| GUI progress updates from threads | Directly updating tkinter widgets from worker thread | Use root.after(0, callback) to schedule updates in main thread |
| Window geometry persistence | Saving geometry without validation | Check bounds, handle multi-monitor changes, center if off-screen |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Updating GUI on every job fetch result | Progress bar thrashes, GUI sluggish | Batch updates: queue results, update GUI every 100ms with root.after() | >50 concurrent job fetches |
| Loading all job results into GUI at once | Slow rendering, memory spike | Implement pagination or virtual scrolling | >500 job results |
| Blocking GUI thread for PDF parsing | UI freeze during resume operations | Already have ThreadPoolExecutor - ensure GUI uses it properly | Any PDF parsing >100ms |
| Creating new ThreadPoolExecutor per GUI action | Thread explosion, resource exhaustion | Reuse existing application-wide executor | Not a scale issue - architectural |
| Polling queue too frequently | CPU usage spike | Use root.after(100, check_queue) not while True with sleep | Heavy GUI usage |
| Synchronous browser launches | GUI blocks waiting for browser | Use subprocess.Popen (async) not subprocess.run (blocking) | Not scale - UX issue |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Unsigned macOS distribution | Users bypass Gatekeeper, malware impersonation risk | Code sign and notarize all macOS releases |
| Storing credentials in GUI config files | Plaintext passwords in user directories | Use system keyring (keyring library), never plaintext |
| Allowing arbitrary file paths in file dialogs | Path traversal if processing user-selected files | Validate extensions, use pathlib to resolve safely |
| Including debug info in production builds | Exposes code structure, API keys in error messages | Strip debug symbols, use --strip in PyInstaller for production |
| Bundling .env or config files with secrets | API keys distributed to all users | Use environment variables, exclude sensitive files from bundle |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No visual feedback during long searches | Users think app crashed, force quit | Always show progress bar with cancel button |
| Console window alongside GUI on Windows | Looks unprofessional, confusing for users | Use gui_scripts entry point, set console=False in PyInstaller |
| Generic error messages "Search failed" | Users can't self-help, support burden | Show actionable errors: "No internet connection - check network settings" |
| Window opens in random position | Inconsistent experience, may open off-screen | Center on first launch, restore saved position with bounds checking |
| No keyboard shortcuts | Power users forced to use mouse | Add Cmd+N/Ctrl+N for new search, Enter to submit, Esc to cancel |
| Blocking during browser launch | Unnecessary wait, feels sluggish | Use async subprocess.Popen, don't wait for browser |
| Platform-inconsistent dialogs | Feels "wrong" on each platform | Use native file dialogs (tkinter.filedialog uses native) |
| No dark mode support | Jarring on systems with dark theme | CustomTkinter supports dark/light modes with set_appearance_mode() |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **GUI Tests:** Often missing headless CI setup - verify xvfb configured and tests run in GitHub Actions
- [ ] **Resource paths:** Often missing sys._MEIPASS handling - verify icons/images load in bundled executable, not just development
- [ ] **Cross-platform browser launch:** Often missing platform detection - verify file opening works on Windows, macOS, and Linux
- [ ] **Thread-safe GUI updates:** Often missing root.after() wrapper - verify no direct widget updates from threads
- [ ] **macOS code signing:** Often missing entitlements.plist - verify hardened runtime allows unsigned executable memory
- [ ] **PyInstaller hidden imports:** Often missing GUI framework data files - verify themed widgets render correctly in bundle
- [ ] **Dual entry points:** Often missing console=False flag - verify no console window with GUI on Windows
- [ ] **High DPI support:** Often missing DPI awareness - verify crisp rendering on 4K/Retina displays at various scaling factors
- [ ] **Multi-monitor handling:** Often missing bounds checking - verify window appears on-screen when monitor setup changes
- [ ] **Error handling in GUI:** Often missing user-friendly messages - verify errors show actionable guidance, not stack traces
- [ ] **Progress cancelation:** Often missing cancel implementation - verify long operations can be stopped mid-execution
- [ ] **Window state persistence:** Often missing geometry validation - verify saved position/size loads safely

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Frozen UI from blocking calls | MEDIUM | 1. Extract blocking code to function 2. Wrap in executor.submit() 3. Add GUI update via root.after() in callback 4. Test responsiveness |
| Missing PyInstaller imports | LOW | 1. Run with --debug=imports 2. Add missing modules to hiddenimports in spec 3. Rebuild and test 4. Document in build scripts |
| Broken resource paths in bundle | LOW | 1. Implement resource_path() helper 2. Replace all relative paths 3. Add resources to spec datas 4. Test bundled executable |
| macOS Gatekeeper rejection | HIGH | 1. Obtain Apple Developer certificate ($99) 2. Create entitlements.plist 3. Sign with --options runtime 4. Notarize with xcrun notarytool 5. Staple ticket |
| Dual entry point conflicts | MEDIUM | 1. Separate into gui_main.py and __main__.py 2. Update spec file with multiple Analysis/EXE 3. Reconfigure build scripts 4. Test both executables |
| No GUI test coverage | MEDIUM | 1. Install pytest-xvfb or setup GabrielBB/xvfb-action 2. Extract testable logic from handlers 3. Write integration tests for critical paths 4. Add to CI |
| High DPI rendering broken | LOW-MEDIUM | 1. Switch to CustomTkinter (handles automatically) or 2. Add DPI awareness manually 3. Test on high-DPI display 4. Adjust scaling if needed |
| Off-screen window positioning | LOW | 1. Add geometry validation function 2. Implement center_window() fallback 3. Call on geometry restoration 4. Test with monitor disconnection |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| UI thread blocking | Phase 1: GUI Foundation | Create test GUI with mock long operation, verify progress bar updates smoothly |
| PyInstaller hidden imports | Phase 2: GUI Implementation | Build executable after adding GUI framework, test on clean machine |
| Cross-platform file paths | Phase 2: GUI Implementation | Implement resource_path(), test bundled executable loads icons on all platforms |
| macOS code signing | Phase 3: Packaging & Distribution | Sign and notarize build, verify no Gatekeeper warnings on fresh macOS |
| Dual entry point conflicts | Phase 2: GUI Implementation | Build both executables, verify CLI has no GUI import overhead, GUI has no console |
| GUI testing gaps | Phase 2: GUI Implementation | Set up xvfb in CI before merging first GUI PR, verify tests run headless |
| High DPI rendering | Phase 2: GUI Implementation | Test on 4K monitor and Retina display, verify crisp text and layout |
| Browser launch failures | Phase 2: GUI Implementation | Test file opening on Windows, macOS, Linux with local and HTTP URLs |
| Window positioning issues | Phase 2: GUI Implementation | Test geometry save/restore, verify centering on first launch, off-screen detection |
| Thread-unsafe GUI updates | Phase 1: GUI Foundation | Code review for direct widget updates from threads, enforce root.after() pattern |

## Sources

**PyInstaller and GUI Framework Packaging:**
- [Packaging with PyInstaller - CustomTkinter Discussion #939](https://github.com/TomSchimansky/CustomTkinter/discussions/939)
- [PyInstaller GUI packaging issues - GitHub Topics](https://github.com/topics/pyinstaller-gui)
- [PyInstaller on macOS frustration - Python GUIs](https://www.pythonguis.com/faq/pyinstaller-on-macos-frustration/)
- [2026 Showdown: PyInstaller vs. cx_Freeze vs. Nuitka](https://ahmedsyntax.com/2026-comparison-pyinstaller-vs-cx-freeze-vs-nui/)
- [Understanding PyInstaller Hooks - Official Documentation](https://pyinstaller.org/en/stable/hooks.html)
- [When Things Go Wrong - PyInstaller Documentation](https://pyinstaller.org/en/stable/when-things-go-wrong.html)

**Threading and GUI Responsiveness:**
- [Use PyQt's QThread to Prevent Freezing GUIs - Real Python](https://realpython.com/python-pyqt-qthread/)
- [Tkinter and Threading: Building Responsive Python GUI Applications - Medium](https://medium.com/tomtalkspython/tkinter-and-threading-building-responsive-python-gui-applications-02eed0e9b0a7)
- [Tkinter and Threading: Preventing Freezing GUIs - Pythoneo](https://pythoneo.com/tkinter-and-threading/)
- [Overcoming GUI Freezes in PyQt - Medium](https://foongminwong.medium.com/overcoming-gui-freezes-in-pyqt-from-threading-multiprocessing-to-zeromq-qprocess-9cac8101077e)
- [Using Tkinter With ThreadPoolExecutor Class - Python Forum](https://python-forum.io/thread-38963.html)

**macOS Code Signing and Notarization:**
- [Signing and notarizing a Python macOS UI application](https://haim.dev/posts/2020-08-08-python-macos-app/)
- [Code Signing a GUI python App for notarization on macOS - Apple Developer Forums](https://developer.apple.com/forums/thread/680719)
- [How to pass Gatekeeper checking - Apple Developer Forums](https://developer.apple.com/forums/thread/713051)
- [Gatekeeper and runtime protection in macOS - Apple Support](https://support.apple.com/guide/security/gatekeeper-and-runtime-protection-sec5599b66df/web)
- [Automatic Code-signing and Notarization for macOS apps using GitHub Actions](https://federicoterzi.com/blog/automatic-code-signing-and-notarization-for-macos-apps-using-github-actions/)

**PyInstaller Configuration:**
- [PyInstaller doesn't respect LSUIElement=1 in OS X - Issue #1917](https://github.com/pyinstaller/pyinstaller/issues/1917)
- [Using PyInstaller - Official Documentation](https://pyinstaller.org/en/stable/usage.html)
- [Using Spec Files - PyInstaller Documentation](https://pyinstaller.org/en/stable/spec-files.html)
- [Multiple entrypoint executables - PyInstaller Discussion #6634](https://github.com/orgs/pyinstaller/discussions/6634)
- [Run-time Information - PyInstaller Documentation](https://pyinstaller.org/en/stable/runtime-information.html)

**GUI Testing:**
- [5 Effective Methods for Functional Testing a Python Tkinter Application](https://blog.finxter.com/5-effective-methods-for-functional-testing-a-python-tkinter-application/)
- [How to do automated test of non-web GUI applications - GitHub Gist](https://gist.github.com/howardrotterdam/63c06754d9f7e1b1fa2c390be6319a44)
- [How to run headless unit tests for GUIs on GitHub actions](https://arbitrary-but-fixed.net/2022/01/21/headless-gui-github-actions.html)
- [GabrielBB/xvfb-action - GitHub Marketplace](https://github.com/marketplace/actions/gabrielbb-xvfb-action)
- [pytest-qt Troubleshooting - Official Documentation](https://pytest-qt.readthedocs.io/en/latest/troubleshooting.html)

**Cross-Platform Considerations:**
- [Which Python GUI library should you use in 2026? - Python GUIs](https://www.pythonguis.com/faq/which-python-gui-library/)
- [Writing cross-platform Tkinter - O'Reilly](https://www.oreilly.com/library/view/python-gui-programming/9781788835886/8b49ca9b-cf6c-4d22-bf9d-284543d3b298.xhtml)
- [Support for file:// urls in webbrowser.open - Python.org Discussions](https://discuss.python.org/t/support-for-file-urls-in-webbrowser-open/81612)
- [How to Make Python Automatically Open Chrome Instead of Edge: 2026 Best Practices](https://copyprogramming.com/howto/python-webbrowser-open-to-open-chrome-browser)

**High DPI and Scaling:**
- [Scaling - CustomTkinter Wiki](https://github.com/TomSchimansky/CustomTkinter/wiki/Scaling)
- [DPI scaling - CustomTkinter Issue #46](https://github.com/TomSchimansky/CustomTkinter/issues/46)
- [How to improve Tkinter window resolution - CodersLegacy](https://coderslegacy.com/python/problem-solving/improve-tkinter-resolution/)
- [Python Tkinter: Getting Window Rectangle, Multi-Monitor Display & 2026 Best Practices](https://copyprogramming.com/howto/how-to-open-tkinter-gui-on-second-monitor-display-windows)

**Entry Points and Packaging:**
- [Entry points specification - Python Packaging User Guide](https://packaging.python.org/specifications/entry-points/)
- [How to structure a python project with multiple entry points](https://blog.claude.nl/posts/how-to-structure-a-python-project-with-multiple-entry-points/)
- [Entry Points - setuptools Documentation](https://setuptools.pypa.io/en/latest/userguide/entry_point.html)

---
*Pitfalls research for: Adding Desktop GUI to Existing Python CLI Application (Job Radar)*
*Researched: 2026-02-12*
