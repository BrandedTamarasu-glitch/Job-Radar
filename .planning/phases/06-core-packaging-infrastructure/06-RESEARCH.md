# Phase 6: Core Packaging Infrastructure - Research

**Researched:** 2026-02-09
**Domain:** PyInstaller packaging, cross-platform executable distribution
**Confidence:** HIGH

## Summary

PyInstaller is the established standard for creating standalone Python executables across Windows, macOS, and Linux. The onedir mode (default) is strongly recommended over onefile mode for faster startup (<10 seconds), better macOS notarization compatibility, and simpler debugging. The core pattern involves creating a .spec file that explicitly declares hidden imports, bundles data files using `--add-data`, and accesses resources via `sys._MEIPASS` or `__file__`-relative paths.

For cross-platform data directory handling, **platformdirs** is the modern standard library (successor to appdirs), automatically mapping to Windows APPDATA, macOS Application Support, and Linux XDG directories. Resources bundled with PyInstaller are read-only by design and should be verified on-demand rather than at startup to minimize initialization overhead.

**Primary recommendation:** Use PyInstaller 6.18+ in onedir mode with console=True, platformdirs for user data directories, explicit hidden imports in .spec file, and sys._MEIPASS-aware resource loading. Distribute as ZIP (Windows), DMG (macOS), and tar.gz (Linux).

## Standard Stack

The established libraries/tools for Python executable packaging:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyInstaller | 6.18+ | Convert Python scripts to standalone executables | Industry standard, cross-platform, active maintenance |
| platformdirs | 4.x | Cross-platform user directory paths | Modern replacement for appdirs, active ecosystem adoption |
| pyfiglet | 1.x | ASCII art banner generation | Standard CLI banner tool, lightweight |
| certifi | 2026.1+ | Mozilla CA certificates bundle | Required for SSL/TLS with requests library |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| colorama | 0.4+ | Cross-platform colored terminal output | Console formatting and colors |
| requests | 2.x | HTTP library (already in project) | SSL certificate bundling considerations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyInstaller | Nuitka | Compiles to native C code, reduces antivirus false positives, but slower build times and steeper learning curve |
| PyInstaller | cx_Freeze | Alternative freezer, but less mature ecosystem and fewer hooks |
| platformdirs | appdirs | Deprecated, use platformdirs instead |
| onedir mode | onefile mode | Onefile slower startup (unpacks each run), incompatible with macOS notarization, harder to debug |

**Installation:**
```bash
pip install pyinstaller platformdirs pyfiglet colorama certifi
```

## Architecture Patterns

### Recommended Project Structure
```
project-root/
├── src/
│   ├── main.py              # Entry point
│   ├── resources/           # Bundled resources (templates, data)
│   │   └── banner.txt
│   └── utils/
│       ├── resource_loader.py  # sys._MEIPASS handling
│       └── config.py           # platformdirs integration
├── job-radar.spec           # PyInstaller specification
└── dist/                    # Output folder (onedir bundles)
    ├── job-radar/           # Windows/Linux bundle
    └── JobRadar.app/        # macOS app bundle
```

### Pattern 1: Resource Path Resolution with sys._MEIPASS
**What:** Helper function to locate bundled resources in both development and frozen states
**When to use:** All resource file access (templates, data files, images)
**Example:**
```python
# Source: https://pyinstaller.org/en/stable/runtime-information.html
import sys
import os
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent

    return base_path / relative_path

# Usage
banner_path = get_resource_path('resources/banner.txt')
with open(banner_path, 'r') as f:
    banner_content = f.read()
```

### Pattern 2: Cross-Platform User Data Directory
**What:** Use platformdirs to get platform-appropriate user data directories
**When to use:** Storing user configuration, logs, application data
**Example:**
```python
# Source: https://github.com/tox-dev/platformdirs
from platformdirs import user_data_dir, user_log_dir
from pathlib import Path

APP_NAME = "JobRadar"
APP_AUTHOR = "JobRadar"  # Windows only

def get_data_dir():
    """Get platform-specific data directory.

    Windows: %APPDATA%\JobRadar
    macOS: ~/Library/Application Support/JobRadar
    Linux: ~/.local/share/JobRadar
    """
    data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_log_file():
    """Get platform-specific error log path."""
    # For user home directory error log as specified
    return Path.home() / 'job-radar-error.log'

# Usage
config_path = get_data_dir() / 'config.json'
error_log = get_log_file()
```

### Pattern 3: Console Banner with Error Handling
**What:** Display ASCII banner on startup with graceful error handling
**When to use:** Application initialization, console applications
**Example:**
```python
# Source: https://www.devdungeon.com/content/create-ascii-art-text-banners-python
import pyfiglet
import sys
from pathlib import Path

def display_banner(version="1.1"):
    """Display startup banner with error handling."""
    try:
        banner = pyfiglet.figlet_format("Job Radar", font="slant")
        print(banner)
        print(f"Version {version}\n")
    except Exception as e:
        # Fallback to simple text banner if pyfiglet fails
        print("=" * 50)
        print(f"Job Radar v{version}")
        print("=" * 50)
        print()

def log_error_and_exit(error_message, exception=None):
    """Log error to file and display brief console message."""
    error_log = Path.home() / 'job-radar-error.log'

    try:
        with open(error_log, 'a') as f:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {error_message}\n")
            if exception:
                f.write(f"Exception: {str(exception)}\n")
    except Exception:
        pass  # Fail silently if can't write log

    print(f"Error: {error_message}")
    print(f"Details logged to: {error_log}")
    sys.exit(1)
```

### Pattern 4: PyInstaller .spec File for Onedir Console Application
**What:** Complete .spec file configuration for cross-platform onedir bundle
**When to use:** Customizing PyInstaller build beyond command-line options
**Example:**
```python
# Source: https://pyinstaller.org/en/stable/spec-files.html
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Define project paths
project_root = Path('.').resolve()
src_dir = project_root / 'src'

# Data files to bundle (source, destination)
added_files = [
    (str(src_dir / 'resources' / '*.txt'), 'resources'),
    (str(src_dir / 'resources' / 'templates'), 'resources/templates'),
]

# Hidden imports that PyInstaller might miss
hidden_imports = [
    'requests',
    'bs4',
    'questionary',
    'prompt_toolkit',  # questionary dependency
    'platformdirs',
    'pyfiglet',
    'colorama',
]

a = Analysis(
    ['src/main.py'],
    pathex=[str(src_dir)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy'],  # Exclude unused heavy packages
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # True for onedir mode
    name='job-radar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid antivirus false positives
    console=True,  # Show console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT creates onedir bundle
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='job-radar',
)

# macOS app bundle (only when building on macOS)
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='JobRadar.app',
        icon=None,  # Add .icns file path if available
        bundle_identifier='com.jobradar.app',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',  # Show in dock
        },
    )
```

### Anti-Patterns to Avoid
- **Don't use onefile mode:** Slower startup (unpacks each run), incompatible with macOS sandbox/notarization, harder to debug
- **Don't rely on __file__ for entry point:** Use sys._MEIPASS for main script resources
- **Don't enable UPX compression:** Triggers antivirus false positives
- **Don't bundle tkinter/matplotlib/numpy unless needed:** Massive size increase for unused GUI frameworks
- **Don't hardcode paths:** Use pathlib and platformdirs for cross-platform compatibility
- **Don't modify bundled resources at runtime:** They are read-only in frozen apps

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-platform data directories | Manual os.path + platform detection | platformdirs | Handles XDG dirs, Windows roaming vs local, macOS versions, 20+ edge cases |
| SSL certificate bundling | Custom CA bundle management | certifi + PyInstaller auto-bundling | Mozilla curated certificates, automatic updates, requests integration |
| Resource path resolution | String concatenation with __file__ | sys._MEIPASS helper function | Handles frozen vs unfrozen, one-folder vs one-file, temp directories |
| ASCII banner generation | Manual string art | pyfiglet | 100+ fonts, handles spacing/alignment, widely tested |
| Hidden import detection | Manual testing on each platform | PyInstaller --debug=imports | Generates import graph, shows missing modules, cross-references dependencies |
| Console colors | ANSI escape codes manually | colorama | Auto-initializes Windows ANSI support, cross-platform color codes |

**Key insight:** PyInstaller's freezing process changes filesystem assumptions (paths, imports, temporary files). Use established patterns rather than assuming standard Python behavior works in frozen apps.

## Common Pitfalls

### Pitfall 1: Missing Hidden Imports for Dynamic Imports
**What goes wrong:** Application runs fine in development but crashes with `ModuleNotFoundError` in frozen executable
**Why it happens:** PyInstaller static analysis cannot detect imports via `__import__()`, `importlib.import_module()`, or runtime string evaluation. Libraries like questionary use prompt_toolkit internally, bs4 dynamically imports parsers (lxml, html5lib), requests uses certifi for SSL certificates.
**How to avoid:**
1. Build with `--debug=imports` flag to see import trace
2. Add all dynamically imported modules to `hiddenimports` in .spec file
3. Use `--collect-submodules package_name` for packages with many submodules
4. Check build/warn-*.txt for import warnings
**Warning signs:**
- ImportError or ModuleNotFoundError only in frozen executable
- "No module named X" errors at runtime
- Features work in dev but fail in packaged app

### Pitfall 2: Antivirus False Positives on Windows
**What goes wrong:** Windows Defender or other antivirus software quarantines/deletes the .exe as malware
**Why it happens:** PyInstaller executables use bootloader patterns similar to malware packers. UPX compression triggers heuristic detection. Unsigned executables are automatically suspicious.
**How to avoid:**
1. **Disable UPX compression:** Set `upx=False` in .spec file
2. **Use onedir instead of onefile:** Folder distributions are less suspicious
3. **Document workaround for users:** Include instructions to add exception in antivirus
4. **Consider code signing:** Costs money but eliminates "Unknown Publisher" warnings
5. **Alternative: Use Nuitka:** Compiles to native C code, fewer false positives
**Warning signs:**
- Executable deleted immediately after build
- Windows SmartScreen blocks execution
- VirusTotal shows multiple false positives (especially with PyInstaller 5.13.2+)

### Pitfall 3: Resource Files Not Found in Frozen App
**What goes wrong:** Application cannot load templates, data files, or configuration that exist in development
**Why it happens:** Frozen apps run from temporary directory (onefile) or bundle directory (onedir). Using `__file__` or relative paths from entry point fails because current working directory differs from bundle location.
**How to avoid:**
1. Always use `sys._MEIPASS` helper function for resource paths
2. Add resources to .spec file `datas` parameter: `[('src/resources', 'resources')]`
3. Verify resource structure matches expected paths in bundle
4. Test with frozen executable, not just development environment
**Warning signs:**
- FileNotFoundError for files that exist in source tree
- Works when running `python main.py` but fails with packaged exe
- Paths work on developer machine but fail on clean test environment

### Pitfall 4: Slow Startup Time with Onefile Mode
**What goes wrong:** Application takes 10-30 seconds to start, or exceeds 10-second requirement
**Why it happens:** Onefile mode unpacks entire bundle to temporary directory on every launch. Large dependencies (numpy, pandas, GUI frameworks) multiply extraction time. Antivirus scans extracted files in temp directory.
**How to avoid:**
1. **Use onedir mode:** No extraction overhead, starts in <2 seconds typically
2. **Exclude unused packages:** Add to `excludes` in Analysis (tkinter, matplotlib if not used)
3. **Use virtual environment for building:** Prevents bundling system-wide packages
4. **Profile import time:** Use `--debug=imports` to identify slow imports
**Warning signs:**
- First launch much slower than subsequent launches (OS caching)
- Temp directory fills with multiple _MEIxxxxx folders
- Startup time increases with bundle size

### Pitfall 5: macOS Gatekeeper and Notarization Issues
**What goes wrong:** macOS users see "App is damaged and can't be opened" or Gatekeeper blocks execution
**Why it happens:** macOS requires notarization for downloaded apps (Catalina+). Onefile mode incompatible with sandbox-enabled notarization. Unsigned .app bundles trigger Gatekeeper.
**How to avoid:**
1. **Use onedir mode:** Required for notarization with sandbox
2. **Create .app bundle:** Use BUNDLE in .spec file (macOS only)
3. **Distribute via DMG:** Professional distribution format, signals intent
4. **Document user workaround:** Right-click > Open (first launch only) bypasses Gatekeeper
5. **Consider Apple Developer signing:** Requires $99/year developer account
**Warning signs:**
- App works on build machine but not on other Macs
- Error: "macOS cannot verify that this app is free from malware"
- App bounces in dock once then quits silently

### Pitfall 6: SSL Certificate Errors with Requests Library
**What goes wrong:** HTTPS requests fail with `SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]` in frozen executable
**Why it happens:** PyInstaller bundles certifi CA certificates, but requests may not find them in frozen environment. The `REQUESTS_CA_BUNDLE` environment variable not set correctly.
**How to avoid:**
1. **Verify certifi is bundled:** Should happen automatically with requests
2. **Check for runtime hook:** PyInstaller includes hook to set certificate path
3. **Explicitly set certificate path if needed:**
   ```python
   import os
   import sys
   if getattr(sys, 'frozen', False):
       import certifi
       os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
   ```
4. **Add certifi to hidden imports:** Ensures it's bundled even if not directly imported
**Warning signs:**
- HTTPS requests work in development but fail in frozen app
- SSL certificate verification errors only in packaged executable
- HTTP (non-SSL) requests work but HTTPS fail

## Code Examples

Verified patterns from official sources:

### Complete Main Entry Point with Error Handling
```python
# Source: Combined patterns from PyInstaller docs and platformdirs
import sys
import logging
from pathlib import Path

def setup_logging():
    """Configure logging to both console and file."""
    log_file = Path.home() / 'job-radar-error.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main entry point with startup banner and error handling."""
    logger = setup_logging()

    try:
        # Display startup banner
        from utils.banner import display_banner
        display_banner(version="1.1")

        # Initialize application
        logger.info("Job Radar starting...")

        # Your application logic here
        from app import run_application
        run_application()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error during startup")
        print(f"\nA fatal error occurred. Details logged to: {Path.home() / 'job-radar-error.log'}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Build Script for Cross-Platform Distribution
```bash
# Source: PyInstaller documentation patterns
#!/bin/bash
# build.sh - Cross-platform build script

set -e  # Exit on error

echo "Cleaning previous builds..."
rm -rf build/ dist/

echo "Building PyInstaller executable..."
pyinstaller job-radar.spec --clean

# Platform-specific distribution
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Creating macOS DMG..."
    # Requires create-dmg: brew install create-dmg
    create-dmg \
        --volname "Job Radar" \
        --window-size 600 400 \
        --icon-size 100 \
        --app-drop-link 400 200 \
        "dist/JobRadar-1.1.dmg" \
        "dist/JobRadar.app"

elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Creating Windows ZIP..."
    cd dist
    powershell Compress-Archive -Path job-radar -DestinationPath job-radar-1.1-windows.zip
    cd ..

else
    echo "Creating Linux tar.gz..."
    cd dist
    tar -czf job-radar-1.1-linux.tar.gz job-radar/
    cd ..
fi

echo "Build complete!"
```

### Testing Frozen Executable Detection
```python
# Source: https://pyinstaller.org/en/stable/runtime-information.html
import sys

def is_frozen():
    """Check if running in PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_bundle_dir():
    """Get bundle directory (onedir) or temporary extraction folder (onefile)."""
    if is_frozen():
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent

# Usage
if is_frozen():
    print(f"Running as frozen executable")
    print(f"Bundle directory: {sys._MEIPASS}")
else:
    print("Running as Python script")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| appdirs library | platformdirs | 2021+ | Active maintenance, wider platform support, adopted by pip/conda |
| Manual CA certificates | certifi with PyInstaller auto-bundle | PyInstaller 3.0+ | Automatic SSL certificate bundling for requests |
| UPX compression enabled | UPX disabled by default | PyInstaller 5.0+ | Reduce antivirus false positives |
| onefile recommended | onedir recommended | PyInstaller 4.0+ | Faster startup, macOS notarization support |
| Modifying __file__ at runtime | Modern PyInstaller sets __file__ correctly | PyInstaller 6.0+ | Prefer __file__ over sys._MEIPASS for module resources |

**Deprecated/outdated:**
- **appdirs:** Use platformdirs instead (actively maintained, broader support)
- **--onefile for macOS distribution:** Incompatible with notarization sandbox, use onedir + .app bundle
- **UPX compression:** Triggers antivirus false positives, disable with `upx=False`
- **Manual certificate path setting:** PyInstaller hooks handle this automatically for requests

## Open Questions

Things that couldn't be fully resolved:

1. **Questionary-specific hidden imports**
   - What we know: Questionary depends on prompt_toolkit, which has dynamic imports
   - What's unclear: Complete list of questionary hidden imports not documented in search results
   - Recommendation: Start with `hiddenimports=['questionary', 'prompt_toolkit']`, then use `--debug=imports` to identify missing modules. Check build warnings for specific missing imports.

2. **BeautifulSoup parser selection impact**
   - What we know: bs4 dynamically imports parsers (lxml, html5lib, html.parser). Job Radar uses which parser?
   - What's unclear: If Job Radar uses lxml parser, need `hiddenimports=['lxml', 'lxml.etree']`
   - Recommendation: Check current bs4 usage in codebase. If using default parser (html.parser), no hidden imports needed. If using lxml, add to hiddenimports.

3. **macOS DMG creation tooling**
   - What we know: DMG is professional standard for macOS distribution, requires file system permissions
   - What's unclear: Best tool for automated DMG creation (create-dmg vs appdmg vs hdiutil)
   - Recommendation: Use create-dmg (brew install create-dmg) for simple drag-and-drop DMG with custom background. Document manual creation fallback using Disk Utility.

4. **Optimal startup verification strategy**
   - What we know: Can verify resources at startup (fail fast) or on-demand (lazy loading)
   - What's unclear: Performance impact of startup verification vs risk of runtime failures
   - Recommendation: Verify critical resources only (entry point, main config) at startup. Verify optional resources (templates, data files) on-demand when first accessed. Log verification failures to error log.

## Sources

### Primary (HIGH confidence)
- [PyInstaller Official Documentation - Usage](https://pyinstaller.org/en/stable/usage.html) - Onedir/onefile modes, console options, .spec file structure
- [PyInstaller Official Documentation - Runtime Information](https://pyinstaller.org/en/stable/runtime-information.html) - sys._MEIPASS, sys.frozen, resource bundling patterns
- [PyInstaller Official Documentation - When Things Go Wrong](https://pyinstaller.org/en/stable/when-things-go-wrong.html) - Hidden imports, debugging, common issues
- [PyInstaller Official Documentation - Spec Files](https://pyinstaller.org/en/stable/spec-files.html) - Complete .spec file reference and examples
- [platformdirs GitHub Repository](https://github.com/tox-dev/platformdirs) - Cross-platform directory paths API
- [Python Official Logging Documentation](https://docs.python.org/3/howto/logging.html) - Logging to files, cross-platform patterns

### Secondary (MEDIUM confidence)
- [How to find platform-specific directories – alexwlchan](https://alexwlchan.net/til/2025/platform-specific-dirs/) - platformdirs vs appdirs comparison
- [Create ASCII Art Text Banners in Python | DevDungeon](https://www.devdungeon.com/content/create-ascii-art-text-banners-python) - pyfiglet usage examples
- [Why DMG Disk Images Are Used To Install Applications On macOS | Medium](https://medium.com/predict/why-dmg-disk-images-are-used-to-install-applications-on-macos-ff7b5cf104f4) - macOS DMG distribution best practices
- [PyInstaller EXE detected as Virus? (Solutions and Alternatives) - CodersLegacy](https://coderslegacy.com/pyinstaller-exe-detected-as-virus-solutions/) - Antivirus false positive solutions

### Tertiary (LOW confidence)
- [GitHub PyInstaller Issues - Antivirus False Positives](https://github.com/pyinstaller/pyinstaller/issues/6754) - Community reports of antivirus issues
- [PyInstaller Startup Time Discussion](https://github.com/orgs/pyinstaller/discussions/8970) - Onedir vs onefile performance
- [Stack Overflow - Bundling SSL Certificates](https://proxiesapi.com/articles/bundling-ssl-certificates-with-pyinstaller-and-aiohttp) - SSL certificate handling patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyInstaller official docs, platformdirs widely adopted
- Architecture: HIGH - Verified from official PyInstaller documentation and examples
- Pitfalls: HIGH - Official documentation and multiple community reports confirm issues
- Hidden imports: MEDIUM - General patterns verified, specific libraries (questionary, bs4 parsers) need testing
- macOS distribution: MEDIUM - DMG recommended by community sources, no official Apple guidance found
- Resource verification: LOW - No authoritative source on startup vs on-demand tradeoffs

**Research date:** 2026-02-09
**Valid until:** March 2026 (30 days - PyInstaller is stable, patterns change slowly)

## Recommendations for Claude's Discretion Areas

Based on research findings, here are specific recommendations for areas left to Claude's discretion:

### 1. Path Separator Handling
**Recommendation:** Use pathlib.Path exclusively, never os.sep or manual string concatenation.
**Rationale:** pathlib automatically handles platform differences. The `/` operator works cross-platform. Eliminates entire class of path separator bugs.
```python
# Recommended
path = Path('resources') / 'templates' / 'output.html'

# Not recommended
path = 'resources' + os.sep + 'templates' + os.sep + 'output.html'
```

### 2. Missing Resource Handling Strategy
**Recommendation:** Fail fast with detailed error logging for critical resources, use fallbacks for optional resources.
**Rationale:** Critical resources (main config, entry point data) should stop execution immediately with clear error message. Optional resources (templates, banners) can degrade gracefully. This balances reliability with user experience.
```python
# Critical resource - fail fast
banner_path = get_resource_path('resources/banner.txt')
if not banner_path.exists():
    log_error_and_exit(f"Critical resource missing: {banner_path}")

# Optional resource - fallback
try:
    template = load_template('custom_output.html')
except FileNotFoundError:
    logger.warning("Custom template not found, using default")
    template = load_template('default_output.html')
```

### 3. Resource Verification Timing
**Recommendation:** Verify critical resources at startup, verify optional resources on-demand.
**Rationale:** Startup verification ensures immediate failure for broken installations. On-demand verification minimizes startup overhead (important for <10 second requirement). Hybrid approach balances both concerns.
```python
def startup_verification():
    """Verify critical resources exist at startup."""
    critical_resources = [
        'config/default.json',
        'resources/error_messages.txt'
    ]
    for resource in critical_resources:
        path = get_resource_path(resource)
        if not path.exists():
            log_error_and_exit(f"Critical resource missing: {resource}")
```

### 4. sys._MEIPASS Path Detection
**Recommendation:** Use standard sys._MEIPASS pattern with getattr() fallback, as shown in Pattern 1.
**Rationale:** This is the PyInstaller-documented standard pattern. Using `getattr(sys, 'frozen', False)` safely checks for frozen state without AttributeError. The pattern works for onedir, onefile, and development environments.

### 5. macOS Distribution Format
**Recommendation:** Use DMG for primary distribution, provide ZIP as alternative.
**Rationale:** DMG is professional standard, provides better user experience (drag-to-Applications), includes integrity verification, and reduces support requests. ZIP as fallback for users without disk mounting capabilities or automated downloads.

**Distribution strategy:**
- **Primary:** JobRadar-1.1.dmg (for manual downloads)
- **Alternative:** JobRadar-1.1-macos.zip (for automation, CI/CD)
- **Include:** README.txt with installation instructions in both formats
