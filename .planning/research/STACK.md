# Stack Research

**Domain:** Python Desktop GUI Launcher for CLI Application
**Researched:** 2026-02-12
**Confidence:** HIGH

## Recommended Stack

### Core GUI Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| CustomTkinter | 5.2.2 | Modern GUI framework | Built on tkinter with modern flat design, dark/light themes, high-DPI support. Works seamlessly with PyInstaller. Zero licensing concerns. Minimal bundle size increase. [CustomTkinter is the easiest modern GUI option](https://www.pythonguis.com/faq/which-python-gui-library/) with consistent cross-platform appearance. |
| tkinter | Built-in | Base GUI toolkit | Included with Python 3.10+. No installation needed. Native file dialogs, proven cross-platform stability. [CustomTkinter extends tkinter](https://github.com/TomSchimansky/CustomTkinter) while maintaining compatibility. |

### Packaging & Distribution

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| PyInstaller | 6.18.0 | Bundler for executables | [Latest version (Jan 2026)](https://pyinstaller.org/en/stable/) with Python 3.8-3.14 support. Works [out-of-the-box with CustomTkinter](https://customtkinter.tomschimansky.com/documentation/packaging/) using onedir mode. You already use this successfully for CLI distribution. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| threading | Built-in | Background task execution | Run job searches without freezing GUI. [Use for I/O-bound operations](https://www.infoworld.com/article/2257425/python-threading-and-subprocesses-explained.html) like web scraping. |
| webbrowser | Built-in | Launch HTML reports | [Open generated reports](https://docs.python.org/3/library/webbrowser.html) in default browser. Already generating HTML, just need to open it. |
| queue | Built-in | Thread-safe communication | Pass progress updates from worker threads to GUI thread for progress bar updates. |

## Installation

```bash
# GUI framework (only new dependency)
pip install customtkinter==5.2.2

# Packaging (already have this)
pip install pyinstaller==6.18.0

# All other libraries are Python built-ins
```

## PyInstaller Integration

### CustomTkinter Data Files

CustomTkinter requires explicit data inclusion in PyInstaller:

```bash
pyinstaller --name="JobRadar" \
    --onedir \
    --windowed \
    --add-data "venv/lib/python3.10/site-packages/customtkinter:customtkinter" \
    launcher.py
```

**Rationale:** [PyInstaller doesn't automatically include .json theme files](https://github.com/TomSchimansky/CustomTkinter/discussions/939) from CustomTkinter library. Must use `--add-data` flag.

### Platform-Specific Flags

**Windows:**
```bash
--windowed  # No console window
--icon=icon.ico
```

**macOS:**
```bash
--windowed  # .app bundle without terminal
--icon=icon.icns
--osx-bundle-identifier=com.jobradar.launcher
```

**Linux:**
```bash
--windowed  # No terminal on launch
```

### Build Mode

**Use onedir mode** (already doing this):
- [Easier debugging](https://pyinstaller.org/en/stable/operating-mode.html) - see exactly what files are included
- CustomTkinter [works best with onedir](https://github.com/TomSchimansky/CustomTkinter/discussions/423)
- Can update executable without redistributing entire bundle
- [Recommended for GUI applications](https://pyinstaller.org/en/stable/usage.html)

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| CustomTkinter | PyQt6/PySide6 | If you need advanced widgets (charts, complex tables, rich text editor). [PyQt6 requires commercial license](https://www.pythonguis.com/faq/pyqt6-vs-pyside6/) for proprietary apps. [PySide6 is LGPL-free](https://doc.qt.io/qtforpython-6/commercial/index.html) but adds 80-120MB to bundle vs tkinter's ~5MB. Overkill for form-based launcher. |
| CustomTkinter | wxPython | If you need truly native widgets. [wxPython has platform quirks](https://charleswan111.medium.com/choosing-the-best-python-gui-library-comparing-tkinter-pyqt-and-wxpython-1c835746586a) and doesn't abstract cross-platform differences as well. Smaller community than tkinter. |
| CustomTkinter | Plain tkinter | If you want absolute minimal dependencies (zero new installs). But [tkinter looks dated](https://www.pythonguis.com/faq/which-python-gui-library/) without significant custom styling work. CustomTkinter provides modern appearance with minimal effort. |
| CustomTkinter | Kivy/BeeWare | If targeting mobile or need touch-first UI. Not suitable for traditional desktop applications. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| PySimpleGUI | [Changed to proprietary license](https://www.pythonguis.com/faq/which-python-gui-library/) requiring commercial purchase (2022). Previously free versions deprecated. Community abandoned it. | CustomTkinter (similar simplicity, MIT license) |
| customtkinter-pyinstaller | [Modified fork for onefile mode](https://pypi.org/project/customtkinter-pyinstaller/). Hasn't been updated in 12+ months. Onedir mode works fine with official CustomTkinter. | Official CustomTkinter + onedir mode |
| Tkinter Boostrap/ttkbootstrap | Alternative modern tkinter wrapper. Less mature than CustomTkinter, smaller community, fewer examples for PyInstaller packaging. | CustomTkinter (better documentation, proven PyInstaller integration) |
| Electron/Tauri with Python | Massive bundle sizes (150-300MB minimum). Separate web stack to learn. Python would run as subprocess, adding complexity. | CustomTkinter (5-15MB total increase, pure Python) |

## Stack Patterns by Use Case

**For simple launcher UI (your use case):**
- CustomTkinter + threading + built-in file dialogs
- Total new dependencies: 1 (customtkinter)
- Bundle size increase: ~5-10MB
- Development time: Minimal (familiar Python, simple API)

**If you needed database browser in GUI:**
- Add SQLite browser widget from CustomTkinter examples
- Still no additional dependencies (sqlite3 is built-in)

**If you needed real-time data visualization:**
- Reconsider stack - would need PyQt6/PySide6 with QtCharts
- Or keep CustomTkinter for UI, generate charts in HTML reports

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| customtkinter 5.2.2 | Python 3.7-3.14 | [Requires Python >=3.7](https://pypi.org/project/customtkinter/). Python 3.10+ gets [dark window headers on macOS](https://github.com/TomSchimansky/CustomTkinter/discussions/311) (Tcl/Tk 8.6.9+). |
| PyInstaller 6.18.0 | Python 3.8-3.14 | [Avoid Python 3.10.0 specifically](https://github.com/pyinstaller/pyinstaller/issues/5693) (has bug). Use 3.10.1+ instead. |
| CustomTkinter | PyInstaller 6.x | [Well-documented integration](https://customtkinter.tomschimansky.com/documentation/packaging/). Requires `--add-data` flag for theme files. |

## Cross-Platform Rendering

**Windows:**
- [High-DPI scaling automatic](https://github.com/TomSchimansky/CustomTkinter/wiki/Scaling) in CustomTkinter
- No blurry text on 125%/150% display scaling
- Dark/light mode matches Windows 10/11 theme

**macOS:**
- Python 3.10+ enables [dark title bars](https://github.com/TomSchimansky/CustomTkinter/discussions/311)
- Retina display support built-in
- System appearance mode integration (dark/light auto-detection)

**Linux:**
- Consistent appearance across Ubuntu/Fedora/Debian
- No dependency on specific desktop environment (works in GNOME/KDE/XFCE)
- [Theme colors adapt](https://customtkinter.tomschimansky.com/) to system or manual setting

## Threading Architecture for GUI

**Pattern for long-running tasks:**

```python
import threading
import queue
import customtkinter as ctk

class JobRadarGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()

    def run_search(self):
        # Start background thread
        thread = threading.Thread(target=self.search_worker)
        thread.daemon = True
        thread.start()

        # Check queue for updates
        self.after(100, self.check_queue)

    def search_worker(self):
        # Run existing CLI search code
        # Post updates: self.queue.put(("progress", 0.5))
        pass

    def check_queue(self):
        try:
            msg_type, data = self.queue.get_nowait()
            if msg_type == "progress":
                self.progress_bar.set(data)
        except queue.Empty:
            pass
        self.after(100, self.check_queue)
```

**Rationale:**
- [Never call GUI methods from worker threads](https://docs.pysimplegui.com/en/latest/documentation/module/multithreading/) directly (not thread-safe)
- [Use queue for thread communication](https://www.nurmatova.com/subprocesses-and-multithreading.html)
- [`.after()` method polls queue](https://www.pythontutorial.net/tkinter/tkinter-thread-progressbar/) from main thread
- Prevents GUI freezing during web scraping

## File Dialog Usage

```python
from tkinter import filedialog
import customtkinter as ctk

# PDF file selection
pdf_path = filedialog.askopenfilename(
    title="Select Resume",
    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
)
```

**Rationale:**
- [tkinter.filedialog uses native OS dialogs](https://docs.python.org/3/library/dialog.html)
- Windows: Uses Win32 file picker
- macOS: Uses Cocoa file picker
- Linux: Uses GTK file picker
- No CustomTkinter equivalent needed - native dialogs look better

## Browser Integration

```python
import webbrowser
import os

# Open generated HTML report
report_path = os.path.abspath("reports/job_results.html")
webbrowser.open(f"file://{report_path}")
```

**Rationale:**
- [webbrowser module is cross-platform](https://docs.python.org/3/library/webbrowser.html)
- Opens default browser automatically
- Handles file:// URLs correctly
- No additional dependencies

## Development Workflow

1. **GUI development:** Test with `python launcher.py` (fast iteration)
2. **Packaging test:** `pyinstaller launcher.spec` (verify bundle)
3. **Distribution:** Copy onedir folder to target platform

**No changes needed** to existing PyInstaller build process beyond:
- Adding `--add-data` for CustomTkinter theme files
- Using `--windowed` flag to hide console

## Bundle Size Impact

Based on [framework comparison research](https://charleswan111.medium.com/choosing-the-best-python-gui-library-comparing-tkinter-pyqt-and-wxpython-1c835746586a):

| Framework | Typical Bundle Size Increase |
|-----------|------------------------------|
| CustomTkinter (tkinter-based) | +5-10 MB |
| PyQt6/PySide6 | +80-120 MB |
| wxPython | +40-60 MB |

**Current CLI bundle size:** ~50-80MB (estimated with PyInstaller onedir)
**With GUI launcher:** ~60-90MB total

Minimal impact because [tkinter is included with Python](https://www.pythonguis.com/faq/which-python-gui-library/) - CustomTkinter only adds theme JSON files and Python code.

## Sources

- [CustomTkinter GitHub Repository](https://github.com/TomSchimansky/CustomTkinter) - Official source, packaging documentation
- [CustomTkinter Official Documentation](https://customtkinter.tomschimansky.com/) - API reference, widget examples
- [PyInstaller 6.18.0 Documentation](https://pyinstaller.org/en/stable/) - Latest packaging guidelines (Jan 2026)
- [Python GUI Library Comparison 2026](https://www.pythonguis.com/faq/which-python-gui-library/) - Framework selection analysis
- [PyQt6 vs PySide6 Licensing](https://www.pythonguis.com/faq/pyqt6-vs-pyside6/) - Commercial use constraints
- [CustomTkinter PyInstaller Integration](https://customtkinter.tomschimansky.com/documentation/packaging/) - Bundling best practices
- [Python Threading Best Practices](https://www.infoworld.com/article/2257425/python-threading-and-subprocesses-explained.html) - GUI threading patterns
- [Tkinter File Dialogs](https://docs.python.org/3/library/dialog.html) - Python 3.14 official documentation
- [Webbrowser Module](https://docs.python.org/3/library/webbrowser.html) - Cross-platform browser launching
- [CustomTkinter DPI Scaling](https://github.com/TomSchimansky/CustomTkinter/wiki/Scaling) - High-resolution display support

---
*Stack research for: Job Radar Desktop GUI Launcher*
*Researched: 2026-02-12*
*Confidence: HIGH - All recommendations verified with official documentation and 2026 sources*
