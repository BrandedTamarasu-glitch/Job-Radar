# Phase 30: Packaging & Distribution - Research

**Researched:** 2026-02-13
**Domain:** PyInstaller GUI packaging, CustomTkinter bundling, cross-platform distribution, code signing
**Confidence:** HIGH

## Summary

Phase 30 builds production-ready executables for the dual-mode (CLI/GUI) Job Radar application using PyInstaller. The project already has infrastructure in place from Phase 8: a working spec file (`job-radar.spec`) with dual executables (CLI with console, GUI without), and a GitHub Actions CI/CD workflow (`release.yml`) that builds for all three platforms on tag triggers.

The primary challenge is CustomTkinter asset bundling. PyInstaller's static analysis cannot automatically detect data files (JSON themes, OTF fonts), requiring explicit `--add-data` configuration. The existing spec file already includes CustomTkinter assets collection logic, but verification is needed to ensure all theme files and fonts are bundled correctly. macOS code signing requires the `com.apple.security.cs.allow-unsigned-executable-memory` entitlement because Python JIT compilation creates writable and executable memory at runtime.

**Primary recommendation:** Build on existing infrastructure. Verify CustomTkinter assets bundle correctly (theme JSON files, shape fonts). Test executables on clean machines without Python. Add entitlements file for macOS code signing. Keep onedir mode (already configured) for better performance and macOS compatibility.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyInstaller | 6.14.2+ | Bundle Python apps into executables | Industry standard, active development, supports Python 3.10-3.13 |
| CustomTkinter | 5.2.2 | GUI framework (already in project) | Modern Tkinter wrapper, but requires manual asset bundling |
| certifi | latest | SSL certificate bundle for HTTPS | Required for frozen builds to resolve SSL certificates |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pillow | latest | Icon conversion (.png to .ico/.icns) | Already in `[build]` dependencies for Windows icon support |
| PyInstaller hooks | built-in | Automatic dependency detection | Most dependencies work automatically, CustomTkinter requires manual config |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyInstaller | Nuitka | Nuitka compiles to C but has longer build times and less ecosystem support |
| PyInstaller | py2exe (Windows only) | Platform-specific, doesn't support cross-platform builds |
| onedir mode | onefile mode | onefile has slower startup, breaks macOS signing/notarization, deprecated for .app bundles in PyInstaller 7.0 |

**Installation:**
```bash
pip install -e .[build]  # Already configured in pyproject.toml
```

## Architecture Patterns

### Recommended Project Structure
```
dist/
├── job-radar/              # Linux/Windows onedir bundle
│   ├── job-radar           # CLI executable (console=True)
│   ├── job-radar-gui       # GUI executable (console=False)
│   ├── customtkinter/      # Bundled theme assets
│   │   └── assets/
│   │       ├── themes/
│   │       │   ├── blue.json
│   │       │   ├── dark-blue.json
│   │       │   └── green.json
│   │       └── fonts/
│   │           └── CustomTkinter_shapes_font.otf
│   ├── profiles/
│   │   └── _template.json
│   └── _internal/          # Python runtime and dependencies
└── JobRadar.app/           # macOS app bundle
    └── Contents/
        ├── MacOS/
        │   ├── job-radar-cli    # CLI executable
        │   ├── job-radar-gui    # GUI executable
        │   └── job-radar        # Terminal launcher script
        ├── Info.plist
        └── Resources/
```

### Pattern 1: Dual Executable Mode (CLI + GUI)
**What:** Two executables from the same codebase - one with console window (CLI), one without (GUI)
**When to use:** Applications that support both GUI and CLI interfaces
**Example:**
```python
# Source: job-radar.spec (already implemented)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='job-radar',
    console=True,              # CLI mode: show console
)

gui_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='job-radar-gui',
    console=False,             # GUI mode: hide console
)

coll = COLLECT(
    exe,
    gui_exe,                   # Both executables in same bundle
    a.binaries,
    a.zipfiles,
    a.datas,
)
```

### Pattern 2: CustomTkinter Asset Bundling
**What:** Manually collect CustomTkinter's data files (JSON themes, OTF fonts)
**When to use:** Any PyInstaller build using CustomTkinter
**Example:**
```python
# Source: job-radar.spec (already implemented)
try:
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent
    added_files.append((str(ctk_path / 'assets'), 'customtkinter/assets'))
except ImportError:
    pass  # CustomTkinter not installed - skip bundling
```

### Pattern 3: macOS Code Signing with Entitlements
**What:** Sign macOS executables with required entitlements for Python runtime
**When to use:** All macOS builds (mandatory on Apple Silicon, recommended for Intel)
**Example:**
```python
# Source: https://pyinstaller.org/en/stable/feature-notes.html
app = BUNDLE(
    coll,
    name='JobRadar.app',
    icon='icon.icns',
    bundle_identifier='com.jobradar.app',
    codesign_identity='Apple Development: Your Name (TEAMID)',
    entitlements_file='entitlements.plist',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
    },
)
```

**entitlements.plist:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
</dict>
</plist>
```

### Pattern 4: SSL Certificate Bundling
**What:** Fix HTTPS in frozen builds by setting REQUESTS_CA_BUNDLE to certifi bundle
**When to use:** All PyInstaller builds that make HTTPS requests
**Example:**
```python
# Source: job_radar/__main__.py (already implemented)
def _fix_ssl_for_frozen():
    """Set REQUESTS_CA_BUNDLE for frozen builds so HTTPS works."""
    if getattr(sys, 'frozen', False):
        try:
            import certifi
            os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        except ImportError:
            pass
```

### Anti-Patterns to Avoid
- **Hard-coding file paths:** Use `sys._MEIPASS` for runtime resource access in frozen builds
- **Using onefile for macOS .app bundles:** Deprecated in PyInstaller 7.0, slower, breaks signing/notarization
- **Forgetting multiprocessing.freeze_support():** Causes infinite spawn loops on Windows
- **Not testing on clean machines:** Executables may work on dev machine but fail in production
- **Assuming automatic dependency detection:** CustomTkinter, PIL, and data files require manual configuration

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Asset bundling for frozen builds | Custom resource loader with file copying | PyInstaller's `--add-data` and `sys._MEIPASS` | Handles temp extraction, cross-platform paths, cleanup |
| SSL certificates in frozen apps | Bundling custom CA bundle | certifi + REQUESTS_CA_BUNDLE environment variable | Official certificate bundle, auto-updates, trusted by requests library |
| Code signing automation | Custom shell scripts with codesign | PyInstaller's built-in signing (`codesign_identity`, `entitlements_file`) | Deep signs all binaries, handles hardened runtime, integrates with build |
| Cross-platform icon conversion | Manual conversion tools | Pillow (already in build dependencies) | PyInstaller auto-converts PNG to .ico/.icns on each platform |
| GitHub Actions multi-platform builds | Self-hosted runners | GitHub-hosted runners (ubuntu-latest, windows-latest, macos-latest) | Maintained by GitHub, clean environments, parallel builds |

**Key insight:** PyInstaller has mature, battle-tested solutions for most packaging problems. CustomTkinter is the exception - it's a newer library and requires manual asset configuration. Resist the urge to "fix" PyInstaller's behavior with custom scripts; work with its architecture.

## Common Pitfalls

### Pitfall 1: CustomTkinter Theme Files Not Bundled
**What goes wrong:** GUI executable launches but shows default theme or crashes with FileNotFoundError for 'blue.json'
**Why it happens:** PyInstaller's static analysis only detects Python imports, not JSON/OTF data files loaded at runtime
**How to avoid:** Add CustomTkinter assets directory with `--add-data` or in spec file `datas` parameter
**Warning signs:**
- GUI works in dev but not in frozen build
- Error message mentions missing .json or .otf files
- Theme looks different (fallback to default Tkinter theme)

**Verification:**
```bash
# Check if theme files are bundled (Linux/macOS)
ls dist/job-radar/customtkinter/assets/themes/

# Windows
dir dist\job-radar\customtkinter\assets\themes\
```

### Pitfall 2: Windows Console Window Flashes on GUI Launch
**What goes wrong:** When launching the GUI executable, a console window briefly appears before the GUI opens
**Why it happens:** Using the CLI executable (console=True) instead of GUI executable (console=False)
**How to avoid:** Ensure users launch `job-radar-gui.exe` for GUI mode, not `job-radar.exe`
**Warning signs:**
- Console window visible when double-clicking GUI executable
- User reports "black window flashing"

**Note:** The project already has dual executables configured in spec file. This pitfall is about ensuring correct executable is used/distributed.

### Pitfall 3: macOS Gatekeeper Blocks Unsigned App
**What goes wrong:** Users see "App is damaged and can't be opened. You should move it to the Trash" or "App cannot be opened because the developer cannot be verified"
**Why it happens:** macOS requires code signing (ad-hoc minimum, Apple Developer ID for distribution)
**How to avoid:**
- PyInstaller performs ad-hoc signing automatically (enough for local testing)
- For distribution: sign with Apple Developer ID certificate
- Include `com.apple.security.cs.allow-unsigned-executable-memory` entitlement
**Warning signs:**
- Works on build machine but blocked on other Macs
- Gatekeeper warnings in Console.app
- App won't launch after download/unzip

### Pitfall 4: Symbolic Links Broken in Distribution Archive
**What goes wrong:** Linux/macOS onedir builds fail to run after extracting from archive
**Why it happens:** ZIP archives don't preserve symbolic links by default; symlinks become copies or break
**How to avoid:**
- Linux: Use `tar -czf` instead of zip (already in CI workflow)
- macOS: Use `zip -r --symlinks` or `tar -czf`
- When copying: `cp -fR` (macOS) or `cp -fr` (Linux)
**Warning signs:**
- Build works locally but fails after CI build
- Executable size balloons (symlinks became file copies)
- "File not found" errors for shared libraries

**Verification:**
```bash
# Check if symlinks are preserved
ls -la dist/job-radar/_internal/  # Look for -> arrows
```

### Pitfall 5: Testing Only on Dev Machine
**What goes wrong:** Executable works on build machine but fails on clean user machines
**Why it happens:** Dev machine has Python installed, system dependencies, environment variables that mask missing bundling
**How to avoid:**
- Test on VMs or clean Docker containers
- Use GitHub Actions artifacts for testing (built on clean runners)
- Check for Python-related environment variables in launcher
**Warning signs:**
- "Works on my machine"
- Users report missing dependencies
- ImportError or DLL errors in production

**Verification checklist:**
- [ ] Test on machine without Python installed
- [ ] Test on different OS version (e.g., Windows 10 vs 11)
- [ ] Test with different user account (not admin)
- [ ] Test from Downloads folder (common user workflow)

### Pitfall 6: Missing Hidden Imports for CustomTkinter Widgets
**What goes wrong:** GUI crashes with ModuleNotFoundError for `customtkinter.windows.widgets` submodules
**Why it happens:** PyInstaller's static analysis misses dynamic imports in CustomTkinter
**How to avoid:** Add all CustomTkinter submodules to `hiddenimports` in spec file
**Warning signs:**
- GUI works for basic elements but crashes when using specific widgets
- Error mentions `customtkinter.windows` or `customtkinter.widgets`

**Current spec file already includes:**
```python
hiddenimports = [
    'customtkinter',
    'customtkinter.windows',
    'customtkinter.windows.widgets',
]
```

### Pitfall 7: Environment Variable Conflicts in Spawned Processes
**What goes wrong:** Launching external programs from frozen app causes library conflicts or crashes
**Why it happens:** PyInstaller modifies LD_LIBRARY_PATH/PATH/DYLD_LIBRARY_PATH to load bundled dependencies
**How to avoid:** Sanitize environment before spawning external processes (not applicable to Job Radar - no external program spawning)
**Warning signs:**
- External programs crash when launched from frozen app
- Library version conflicts in error messages

## Code Examples

Verified patterns from official sources and existing implementation:

### Verifying CustomTkinter Assets in Frozen Build
```python
# Add to job_radar/gui/main_window.py for debugging
import sys
from pathlib import Path

def verify_customtkinter_assets():
    """Debug helper: verify CustomTkinter assets are bundled."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        ctk_assets = base_path / 'customtkinter' / 'assets'

        print(f"Frozen build base path: {base_path}")
        print(f"CustomTkinter assets path: {ctk_assets}")
        print(f"Assets directory exists: {ctk_assets.exists()}")

        if ctk_assets.exists():
            themes = list((ctk_assets / 'themes').glob('*.json'))
            fonts = list((ctk_assets / 'fonts').glob('*.otf'))
            print(f"Theme files found: {len(themes)}")
            print(f"Font files found: {len(fonts)}")
```

### Testing Executable on Clean Machine (Manual Process)
```bash
# Linux: Test in Docker container
docker run -it --rm -v $(pwd)/dist/job-radar:/app ubuntu:22.04
cd /app
./job-radar-gui  # Should launch without Python installed

# Windows: Test in clean VM or use Windows Sandbox
# Copy dist/job-radar folder to sandbox
# Double-click job-radar-gui.exe

# macOS: Test on different Mac or clean user account
# Copy dist/JobRadar.app to Applications
# Launch from Applications folder
```

### GitHub Actions: Verify Build Artifacts
```yaml
# Add to .github/workflows/release.yml after build step
- name: Test executable (Linux)
  if: runner.os == 'Linux'
  run: |
    cd dist
    ./job-radar/job-radar --version
    # GUI requires X server - skip automated GUI test

- name: Test executable (Windows)
  if: runner.os == 'Windows'
  shell: pwsh
  run: |
    cd dist
    .\job-radar\job-radar.exe --version

- name: Test executable (macOS)
  if: runner.os == 'macOS'
  run: |
    cd dist/JobRadar.app/Contents/MacOS
    ./job-radar-cli --version
```

### Creating macOS Entitlements File
```bash
# Create entitlements.plist in project root
cat > entitlements.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
</dict>
</plist>
EOF
```

### Updating Spec File for Entitlements
```python
# Modify job-radar.spec BUNDLE section
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='JobRadar.app',
        icon='icon.icns',
        bundle_identifier='com.jobradar.app',
        # Add these two lines:
        codesign_identity=None,  # None = ad-hoc signing (sufficient for testing)
        entitlements_file='entitlements.plist',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
        },
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual asset bundling with `sys._MEIPASS` | PyInstaller hooks and `--collect-all` | PyInstaller 4.0+ (2020) | Easier for well-supported libraries, but CustomTkinter still needs manual config |
| onefile for all platforms | onedir for production, onefile for single-file distribution | PyInstaller 6.0 (2024) | Better startup performance, required for macOS .app bundles |
| altool for macOS notarization | notarytool | November 2023 (Apple deprecation) | Faster, more reliable, altool no longer works |
| Manual code signing scripts | PyInstaller's `codesign_identity` and `entitlements_file` | PyInstaller 5.0+ (2021) | Integrated into build process, handles deep signing automatically |
| Separate builds for Python 3.x versions | Single build supports Python 3.8-3.13 | PyInstaller 6.0+ (2024) | Simplified CI/CD, broader compatibility |

**Deprecated/outdated:**
- **onefile + macOS .app bundle:** Will be blocked in PyInstaller 7.0 (use onedir instead)
- **Windows XP support:** Dropped in PyInstaller 4.0+
- **Python 2.7 support:** Dropped in PyInstaller 4.0+
- **altool for notarization:** Apple deprecated November 2023, use notarytool

## Open Questions

1. **Does the existing CustomTkinter asset bundling work correctly?**
   - What we know: Spec file has logic to bundle `customtkinter/assets`
   - What's unclear: Whether this captures all theme JSON files and OTF fonts
   - Recommendation: Build and verify by inspecting `dist/job-radar/customtkinter/assets/` directory

2. **Should we add automated smoke tests to CI?**
   - What we know: Current CI builds executables but doesn't test them
   - What's unclear: Whether headless testing is feasible (GUI requires display server)
   - Recommendation: Add `--version` test for CLI, document manual GUI testing process

3. **Do we need real code signing certificates?**
   - What we know: Ad-hoc signing (PyInstaller default) works for testing
   - What's unclear: User's distribution goals (GitHub releases only, or App Store?)
   - Recommendation: Start with ad-hoc signing, upgrade to Developer ID if users report Gatekeeper issues

4. **Should we optimize bundle size?**
   - What we know: Spec file already excludes heavy modules (matplotlib, numpy, torch)
   - What's unclear: Whether current size is acceptable for distribution
   - Recommendation: Measure first, optimize if needed (typical Tkinter app: 50-150 MB)

## Sources

### Primary (HIGH confidence)
- [PyInstaller 6.18.0 Official Documentation](https://pyinstaller.org/en/stable/) - macOS features, common issues, spec file usage
- [PyInstaller Feature Notes](https://pyinstaller.org/en/stable/feature-notes.html) - macOS code signing, BUNDLE construct
- [PyInstaller Common Issues and Pitfalls](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html) - symbolic links, multiprocessing, windowed mode
- [PyInstaller Changelog](https://pyinstaller.org/en/latest/CHANGES.html) - version 6.0 changes, Python 3.13 support, deprecations
- [Apple Developer Documentation: Allow Unsigned Executable Memory](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.allow-unsigned-executable-memory) - entitlement purpose and usage

### Secondary (MEDIUM confidence)
- [CustomTkinter Discussion #939: Packaging with PyInstaller](https://github.com/TomSchimansky/CustomTkinter/discussions/939) - verified asset bundling approach
- [CustomTkinter Issue #1310: PyInstaller font error](https://github.com/TomSchimansky/CustomTkinter/issues/1310) - font bundling requirements
- [CustomTkinter Issue #2649: Loading CustomTkinter_shapes_font.otf](https://github.com/TomSchimansky/CustomTkinter/issues/2649) - font file path issues
- [PyInstaller Discussion #6266: Fonts in TKinter](https://github.com/orgs/pyinstaller/discussions/6266) - font packaging patterns
- [OS X Code Signing PyInstaller Gist](https://gist.github.com/txoof/0636835d3cc65245c6288b2374799c43) - comprehensive code signing guide
- [Python.org Discussion: onefile vs onedir](https://discuss.python.org/t/opinion-pyinstaller-onefile-or-onedir-for-program-distribution/106137) - community best practices

### Tertiary (LOW confidence)
- [Medium: PyInstaller CustomTkinter Guide](https://medium.com/@wahidsaeed1/create-executable-package-for-python3-scripts-using-pyinstaller-tkinter-customtkinter-4552d3d16af5) - practical walkthrough, unverified
- [Medium: Complete PyInstaller Guide 2025](https://lovnish.medium.com/from-python-script-to-windows-exe-complete-pyinstaller-guide-2025-4b22cd7461c5) - recent but not official
- [CodersLegacy: Solving PyInstaller Problems](https://coderslegacy.com/solving-common-problems-and-errors-pyinstaller/) - community troubleshooting

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyInstaller is industry standard, version 6.14.2+ verified via official docs
- Architecture: HIGH - Patterns verified in official docs and existing project spec file
- Pitfalls: HIGH - All pitfalls documented in official PyInstaller docs or verified CustomTkinter issues
- CustomTkinter bundling: MEDIUM - Approach verified in GitHub discussions, but specific to CustomTkinter version

**Research date:** 2026-02-13
**Valid until:** 2026-03-13 (30 days - PyInstaller is stable, monthly check recommended)

**Critical findings:**
1. Project already has 90% of infrastructure in place (spec file, CI workflow, dual executables)
2. CustomTkinter asset bundling is the highest risk area - requires verification
3. macOS code signing needs entitlements file added (simple addition)
4. Current onedir mode is correct approach (onefile deprecated for macOS in PyInstaller 7.0)
5. Testing on clean machines is critical - executables may work on dev machine but fail in production
