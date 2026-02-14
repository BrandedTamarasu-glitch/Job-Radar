# Phase 37: Platform-Native Installers - Research

**Researched:** 2026-02-14
**Domain:** Cross-platform installer creation (macOS DMG, Windows NSIS)
**Confidence:** HIGH

## Summary

Platform-native installers transform PyInstaller-built executables into professional distribution packages for end users. For macOS, this means creating DMG (disk image) files with custom branded backgrounds and drag-to-Applications workflows. For Windows, this involves NSIS (Nullsoft Scriptable Install System) installers with Modern UI wizards, Add/Remove Programs integration, and optional shortcuts.

Both platforms have mature, well-documented toolchains. The macOS workflow centers on `create-dmg`, a shell script that automates DMG creation with custom layouts. The Windows workflow uses NSIS with Modern UI macros for professional wizard-style installers. Both can be fully automated in CI/CD (GitHub Actions already builds PyInstaller executables across platforms).

Code signing certificates are expensive ($100-400/year per platform) and now limited to 460-day validity (industry change effective March 1, 2026). Best practice is to ship unsigned initially with clear user documentation about security warnings, and prepare build scripts with conditional signing steps (skip if certificates not present, sign automatically when added). Unsigned installers trigger macOS Gatekeeper and Windows SmartScreen warnings, but users can bypass: right-click → Open (macOS) or "More info" → "Run anyway" (Windows).

**Primary recommendation:** Use `create-dmg` shell script for macOS DMG automation and NSIS with Modern UI for Windows installers. Implement conditional code signing infrastructure (environment variables for certificates, skip if not present) and automate builds in GitHub Actions matrix workflow (already present in `.github/workflows/release.yml`).

## Standard Stack

The established libraries/tools for this domain:

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| create-dmg | 1.2+ | macOS DMG creation | Shell script standard, no dependencies beyond macOS tools (hdiutil, AppleScript), supports custom backgrounds/layouts, 3.5k+ GitHub stars |
| NSIS | 3.x | Windows installer creation | Industry standard for Windows installers (used by Firefox, VLC, 7-Zip), scriptable, Modern UI built-in, free/open source |
| PyInstaller | 6.x | Python → executable bundler | Already in use (job-radar.spec exists), creates standalone executables that installers package |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| NSIS Modern UI 2 | Built-in with NSIS 3.x | Professional wizard interface | Every NSIS installer should use Modern UI for consistent Windows UX |
| hdiutil | macOS built-in | DMG conversion/manipulation | Used by create-dmg internally; direct use for advanced DMG customization |
| appdmg | npm package | Alternative DMG tool (Node.js) | If Node.js already in toolchain; requires JSON config vs shell script |
| signtool.exe | Windows SDK | Windows code signing | When code signing certificate obtained (future phase) |
| codesign | macOS built-in | macOS code signing | When Apple Developer cert obtained (future phase) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| create-dmg | appdmg (npm) | appdmg requires Node.js dependency and JSON config files; create-dmg is pure shell script with no runtime dependencies |
| create-dmg | DMG Canvas ($20) | GUI tool, not scriptable/automatable; good for one-off designs but not CI/CD |
| NSIS | Inno Setup | Similar capabilities but different scripting syntax; NSIS has larger community and more examples |
| NSIS | WiX Toolset | MSI-based (more complex), requires XML configs; NSIS simpler for straightforward installers |
| NSIS | Advanced Installer | Commercial ($500+/year); NSIS free and sufficient for standard installers |

**Installation:**

```bash
# macOS DMG tool (run on macOS only)
brew install create-dmg

# NSIS (run on Windows, or use GitHub Actions windows-latest runner)
# Download from https://nsis.sourceforge.io/Download
# Or via Chocolatey: choco install nsis

# PyInstaller (already installed per job-radar.spec)
pip install pyinstaller
```

## Architecture Patterns

### Recommended Project Structure

```
.
├── installers/
│   ├── macos/
│   │   ├── dmg-background.png        # 800x500px background with arrow
│   │   ├── build-dmg.sh              # create-dmg automation script
│   │   └── dmg-icon.icns             # Custom DMG volume icon (optional)
│   ├── windows/
│   │   ├── installer.nsi             # NSIS script with Modern UI
│   │   ├── license.txt               # License agreement text
│   │   ├── header.bmp                # 150x57px wizard header
│   │   └── sidebar.bmp               # 164x314px welcome/finish panel
│   └── README.md                     # Security warnings for unsigned installers
├── job-radar.spec                    # PyInstaller spec (already exists)
├── icon.icns                         # macOS app icon (already exists)
├── icon.png                          # Source icon (already exists)
└── .github/workflows/release.yml     # CI/CD automation (already exists)
```

### Pattern 1: DMG Creation Workflow

**What:** Build DMG from PyInstaller .app bundle with custom background and layout
**When to use:** macOS releases (automated in CI/CD on macOS runner)
**Example:**

```bash
#!/bin/bash
# installers/macos/build-dmg.sh

VERSION="${1:-dev}"
APP_PATH="../../dist/JobRadar.app"
DMG_NAME="Job-Radar-${VERSION}.dmg"
VOLUME_NAME="Job Radar Installer"

# create-dmg handles: background, window size, icon positions, Applications symlink
create-dmg \
  --volname "$VOLUME_NAME" \
  --volicon "dmg-icon.icns" \
  --background "dmg-background.png" \
  --window-pos 200 120 \
  --window-size 800 500 \
  --icon-size 128 \
  --icon "JobRadar.app" 200 190 \
  --hide-extension "JobRadar.app" \
  --app-drop-link 600 190 \
  "$DMG_NAME" \
  "$APP_PATH"

echo "✓ DMG created: $DMG_NAME"
```

**Key parameters:**
- `--window-size 800 500` - Larger than standard 600x400 for visibility (user decision)
- `--icon "JobRadar.app" 200 190` - App icon on left side
- `--app-drop-link 600 190` - Applications folder on right (creates symlink)
- `--background` - Custom branded background image showing drag arrow
- `--hide-extension` - Cleaner look (`.app` extension hidden)

### Pattern 2: NSIS Installer Script Structure

**What:** Modern UI wizard installer with license, shortcuts, registry integration
**When to use:** Windows releases (automated in CI/CD on Windows runner)
**Example:**

```nsis
# installers/windows/installer.nsi

# Includes
!include "MUI2.nsh"
!include "FileFunc.nsh"

# Installer metadata
Name "Job Radar"
OutFile "Job-Radar-Setup-${VERSION}.exe"
InstallDir "$PROGRAMFILES\Job Radar"
RequestExecutionLevel admin

# Modern UI configuration
!define MUI_ICON "..\..\icon.png"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "sidebar.bmp"
!define MUI_ABORTWARNING

# Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
Page custom InstallOptionsPage  # Custom: Advanced install location
!insertmacro MUI_PAGE_DIRECTORY
Page custom ShortcutsPage        # Custom: Checkbox for Desktop shortcut
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

# Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

# Languages (must come after page macros)
!insertmacro MUI_LANGUAGE "English"

# Installation section
Section "Install"
  SetOutPath "$INSTDIR"

  # Copy PyInstaller output directory
  File /r "..\..\dist\job-radar\*.*"

  # Create Start Menu shortcut (always)
  CreateDirectory "$SMPROGRAMS\Job Radar"
  CreateShortcut "$SMPROGRAMS\Job Radar\Job Radar.lnk" "$INSTDIR\job-radar.exe"
  CreateShortcut "$SMPROGRAMS\Job Radar\Job Radar (GUI).lnk" "$INSTDIR\job-radar-gui.exe"

  # Desktop shortcut (if user checked option)
  ${If} $DesktopShortcut == "1"
    CreateShortcut "$DESKTOP\Job Radar.lnk" "$INSTDIR\job-radar-gui.exe"
  ${EndIf}

  # File association: .jobprofile extension
  WriteRegStr HKCR ".jobprofile" "" "JobRadarProfile"
  WriteRegStr HKCR "JobRadarProfile" "" "Job Radar Profile"
  WriteRegStr HKCR "JobRadarProfile\DefaultIcon" "" "$INSTDIR\job-radar.exe,0"
  WriteRegStr HKCR "JobRadarProfile\shell\open\command" "" '"$INSTDIR\job-radar.exe" "%1"'

  # Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  # Add/Remove Programs registry entries
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "DisplayName" "Job Radar"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "Publisher" "Job Radar"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "URLInfoAbout" "https://github.com/coryebert/Job-Radar"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "DisplayIcon" "$INSTDIR\job-radar.exe,0"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "NoRepair" 1

  # Estimate install size (in KB)
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "EstimatedSize" "$0"
SectionEnd

# Uninstaller section
Section "Uninstall"
  # Remove files
  RMDir /r "$INSTDIR"

  # Remove shortcuts
  Delete "$DESKTOP\Job Radar.lnk"
  RMDir /r "$SMPROGRAMS\Job Radar"

  # Remove file association
  DeleteRegKey HKCR ".jobprofile"
  DeleteRegKey HKCR "JobRadarProfile"

  # Remove from Add/Remove Programs
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar"
SectionEnd
```

**Key features:**
- Modern UI 2 with branded header/sidebar images
- License agreement screen (required per user decisions)
- Advanced install location (default Program Files, customizable)
- Desktop shortcut optional (checkbox during install)
- Start Menu shortcuts always created
- .jobprofile file association for future profile sharing
- Full Add/Remove Programs integration with all standard fields
- QuietUninstallString for silent uninstall option

### Pattern 3: GitHub Actions Matrix Build

**What:** Automated installer builds on push to version tags
**When to use:** Every release (triggered by `git push origin v2.x.x`)
**Example:**

```yaml
# .github/workflows/release.yml (extend existing workflow)

jobs:
  build-installers:
    name: Build installer on ${{ matrix.os }}
    needs: build  # Depends on existing PyInstaller build job
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: macos-latest
            platform: macos
            script: installers/macos/build-dmg.sh
            artifact: "*.dmg"
          - os: windows-latest
            platform: windows
            script: installers/windows/build-installer.bat
            artifact: "*.exe"
    steps:
      - uses: actions/checkout@v4

      - name: Download PyInstaller artifacts
        uses: actions/download-artifact@v4
        with:
          name: job-radar-${{ matrix.platform }}

      # macOS: Install create-dmg
      - name: Install create-dmg (macOS)
        if: runner.os == 'macOS'
        run: brew install create-dmg

      # Windows: Install NSIS
      - name: Install NSIS (Windows)
        if: runner.os == 'Windows'
        run: choco install nsis -y

      # Build installer
      - name: Build installer
        run: ${{ matrix.script }} ${{ github.ref_name }}

      # Code signing (conditional - skip if certs not present)
      - name: Code sign (macOS)
        if: runner.os == 'macOS' && env.MACOS_CERT_BASE64 != ''
        env:
          MACOS_CERT_BASE64: ${{ secrets.MACOS_CERT_BASE64 }}
          MACOS_CERT_PASSWORD: ${{ secrets.MACOS_CERT_PASSWORD }}
        run: |
          # Decode cert, import to keychain, sign DMG
          echo "Code signing would run here (cert present)"

      - name: Code sign (Windows)
        if: runner.os == 'Windows' && env.WINDOWS_CERT_BASE64 != ''
        env:
          WINDOWS_CERT_BASE64: ${{ secrets.WINDOWS_CERT_BASE64 }}
          WINDOWS_CERT_PASSWORD: ${{ secrets.WINDOWS_CERT_PASSWORD }}
        run: |
          # Decode cert, sign EXE with signtool
          echo "Code signing would run here (cert present)"

      - name: Upload installer artifact
        uses: actions/upload-artifact@v4
        with:
          name: installer-${{ matrix.platform }}
          path: ${{ matrix.artifact }}
```

**Key features:**
- Matrix builds installers on native platforms (can't cross-compile DMG/NSIS)
- Depends on existing PyInstaller build job (reuses dist/ artifacts)
- Conditional code signing checks for secret presence before running
- Environment variables for certificates allow adding signing later without workflow changes

### Pattern 4: Conditional Code Signing Infrastructure

**What:** Prepare build scripts to support code signing without requiring certificates immediately
**When to use:** All build scripts (installers/macos/build-dmg.sh, windows build script)
**Example:**

```bash
#!/bin/bash
# installers/macos/build-dmg.sh with conditional signing

VERSION="${1:-dev}"
DMG_PATH="Job-Radar-${VERSION}.dmg"

# 1. Build unsigned DMG first
create-dmg \
  --volname "Job Radar Installer" \
  # ... other options ...
  "$DMG_PATH" \
  "../../dist/JobRadar.app"

# 2. Sign DMG if certificate available (checks for env var)
if [ -n "$MACOS_CERT_BASE64" ]; then
  echo "Signing DMG with Apple Developer certificate..."

  # Decode certificate from base64
  echo "$MACOS_CERT_BASE64" | base64 --decode > certificate.p12

  # Create temporary keychain
  security create-keychain -p "$KEYCHAIN_PASSWORD" build.keychain
  security default-keychain -s build.keychain
  security unlock-keychain -p "$KEYCHAIN_PASSWORD" build.keychain

  # Import certificate
  security import certificate.p12 -k build.keychain \
    -P "$MACOS_CERT_PASSWORD" -T /usr/bin/codesign

  # Sign the DMG
  codesign --force --sign "$MACOS_SIGNING_IDENTITY" \
    --timestamp --options runtime "$DMG_PATH"

  # Clean up
  security delete-keychain build.keychain
  rm certificate.p12

  echo "✓ DMG signed"
else
  echo "⚠ No signing certificate found (MACOS_CERT_BASE64 not set)"
  echo "  DMG is unsigned - users will see Gatekeeper warning"
fi
```

**Windows equivalent (PowerShell in build-installer.bat):**

```powershell
# installers/windows/build-installer.bat

# 1. Build unsigned installer
makensis installer.nsi

# 2. Sign EXE if certificate available
if ($env:WINDOWS_CERT_BASE64) {
  Write-Host "Signing installer with code signing certificate..."

  # Decode certificate
  $certBytes = [Convert]::FromBase64String($env:WINDOWS_CERT_BASE64)
  [IO.File]::WriteAllBytes("certificate.pfx", $certBytes)

  # Sign with signtool.exe
  & "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" sign `
    /f certificate.pfx `
    /p $env:WINDOWS_CERT_PASSWORD `
    /tr http://timestamp.digicert.com `
    /td sha256 `
    /fd sha256 `
    "Job-Radar-Setup-${env:VERSION}.exe"

  Remove-Item certificate.pfx
  Write-Host "✓ Installer signed"
} else {
  Write-Host "⚠ No signing certificate found (WINDOWS_CERT_BASE64 not set)"
  Write-Host "  Installer is unsigned - users will see SmartScreen warning"
}
```

### Anti-Patterns to Avoid

- **Hardcoding version numbers** - Extract from git tags (${{ github.ref_name }} in CI) or VERSION file
- **Manual DMG creation** - Automating with create-dmg eliminates inconsistency and human error
- **Skipping QuietUninstallString** - Add/Remove Programs can't offer silent uninstall without this registry key
- **Creating uninstaller shortcuts** - Windows guidelines explicitly forbid; user goes through Add/Remove Programs
- **Blocking install on unsigned warnings** - Document bypass steps instead; signing comes later
- **Storing certificates in repository** - Use GitHub Secrets (base64-encoded) for CI/CD automation
- **Same certificate for macOS and Windows** - Requires separate certs from Apple ($99/year) and Windows CA ($100-400/year)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DMG background/layout automation | AppleScript + hdiutil commands manually | create-dmg shell script | Handles edge cases: window positioning on different macOS versions, icon grid alignment (16x16 default), symlink creation to /Applications, volume icon setting, dark mode text color (always black on bg images) |
| Windows Add/Remove Programs integration | Manual registry writes in custom script | NSIS with Modern UI | Provides macros for all required registry keys (DisplayName, UninstallString, EstimatedSize, etc.), automatic cleanup on uninstall, proper handling of NoModify/NoRepair flags |
| File association registration (Windows) | Custom HKCR registry writes | NSIS FileAssociation.nsh macros | Backs up existing associations before overwriting, restores previous association on uninstall, calls SHChangeNotify to refresh shell icons (Windows won't recognize association without this) |
| GitHub Actions matrix builds | Separate workflow files per platform | Single workflow with strategy.matrix | DRY principle: single source of truth for build steps, parallel execution, artifact naming consistency |
| Code signing certificate handling | Store .pfx/.p12 files in repo | Base64-encode to GitHub Secrets, decode at build time | Secrets never touch repository history, can rotate certificates without code changes, supports password-protected certs via separate secret |
| DMG window size for macOS versions | Hardcode 600x400 standard size | Use 800x500 with bottom padding | macOS 11.0+ window title bar intrudes 7 extra points; path bar (if shown) consumes 59 points from bottom; larger size ensures background fully visible across versions |

**Key insight:** Installer creation involves dozens of OS-specific quirks (registry keys, icon refresh calls, symlink types, window positioning, file permissions). Using mature tools (create-dmg, NSIS Modern UI) means these edge cases are already solved. Custom scripting inevitably rediscovers these issues one installer at a time.

## Common Pitfalls

### Pitfall 1: Unsigned Installer User Experience

**What goes wrong:** Users download installer, try to run it, see scary security warnings (macOS: "cannot be opened because developer cannot be verified"; Windows: "Windows protected your PC"), abandon installation thinking it's malware.

**Why it happens:** Code signing certificates cost $100-400/year per platform and now expire after 460 days (industry change March 1, 2026). Many projects ship unsigned initially to validate market fit before investing in certificates.

**How to avoid:**
1. Create prominent README section "Installing Unsigned Software" with screenshots of warnings
2. Document bypass steps: macOS right-click → Open (shows "Open anyway" button), Windows "More info" → "Run anyway"
3. Add warning banner to GitHub Releases page linking to README section
4. Prepare signing infrastructure upfront (conditional in build scripts) so adding certs is configuration change, not code change

**Warning signs:** High installer download counts but low actual installations suggest security warnings are blocking users. GitHub Issues with "can't open" or "virus warning" indicate documentation needs improvement.

### Pitfall 2: DMG Background Image Not Visible

**What goes wrong:** DMG opens, user sees generic white background instead of custom branded background with arrow. Icons positioned randomly instead of app-on-left, Applications-on-right.

**Why it happens:**
- Finder view settings not saved in DMG metadata (requires AppleScript to set `.DS_Store`)
- Background image path not relative to DMG root (must be `.background/image.png`)
- macOS version differences: Big Sur+ changed title bar height, path bar visibility
- .DS_Store file corrupted or not created during DMG build

**How to avoid:**
1. Use create-dmg which handles all AppleScript + .DS_Store generation automatically
2. Test DMG on multiple macOS versions (GitHub Actions matrix: macos-12, macos-13, macos-14)
3. Design background with 59pt bottom padding to account for path bar
4. Use icon size 128px minimum (readable on Retina displays)
5. Verify with: mount DMG, open in Finder, check "View" → "as Icons" is active

**Warning signs:** Users reporting "I don't see where to drag the app" or "background is blank" indicate layout issues.

### Pitfall 3: Windows Installer Missing from Add/Remove Programs

**What goes wrong:** User installs successfully, but app doesn't appear in Add/Remove Programs (Settings → Apps → Installed apps on Windows 11). User can't uninstall without manually deleting Program Files folder.

**Why it happens:**
- Missing or incorrect registry key: `HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\[AppName]`
- UninstallString not pointing to valid uninstaller executable
- Writing to HKCU instead of HKLM (per-user installs don't show in system-wide Add/Remove Programs)
- Uninstaller section deleted registry key during installation (premature cleanup)

**How to avoid:**
1. Use NSIS Modern UI which includes example Add/Remove Programs scripts
2. Write all required registry values: DisplayName, UninstallString, DisplayVersion, Publisher, DisplayIcon, EstimatedSize
3. Add QuietUninstallString for silent uninstall option (increasingly required by enterprise IT)
4. In uninstaller section, delete the registry key LAST (after all cleanup completes)
5. Test on Windows 10 AND Windows 11 (UI changed between versions)

**Warning signs:** Users asking "how do I uninstall?" when docs say "use Add/Remove Programs" indicates registry issue.

### Pitfall 4: File Association Not Recognized

**What goes wrong:** User double-clicks .jobprofile file, Windows shows "How do you want to open this file?" instead of launching Job Radar. macOS shows "There is no application set to open the document."

**Why it happens:**
- Registry writes succeeded but shell not refreshed (Windows caches associations)
- Missing `SHChangeNotify` call after registry modification (Windows)
- Incorrect command syntax: missing `"%1"` parameter in shell\open\command
- Association written to wrong registry hive (HKCU vs HKCR)
- macOS: Info.plist missing CFBundleDocumentTypes (must be in .app bundle before DMG creation)

**How to avoid:**
1. Windows: Use NSIS FileAssociation.nsh macros (includes SHChangeNotify call)
2. Windows: Always include `"%1"` in command string to pass file path to app
3. Test by creating test file with extension, double-clicking (don't just check registry)
4. macOS: Add CFBundleDocumentTypes to Info.plist in PyInstaller .spec file
5. Verify icon shows for file type (indicates association registered)

**Warning signs:** Users reporting "file won't open" or "asks me to choose app" for your custom file extension.

### Pitfall 5: GitHub Actions Signing Fails Silently

**What goes wrong:** CI/CD workflow completes successfully (green check), but downloaded installer is unsigned. Users still see security warnings despite thinking it's signed.

**Why it happens:**
- Conditional signing check (`if [ -n "$CERT_BASE64" ]`) silently skips when secret not set
- Build script exits 0 even when signing fails (masks error)
- Certificate password wrong but script doesn't validate before continuing
- Signing succeeded but timestamp server unreachable (sig invalid without timestamp)

**How to avoid:**
1. Add explicit logging: "⚠ Skipping code signing (certificate not configured)" vs "✓ Code signing complete"
2. When certificate IS present, fail loudly on signing errors (exit 1)
3. Verify signed artifact before upload: `codesign --verify --verbose` (macOS) or `signtool verify` (Windows)
4. Use multiple timestamp servers with fallback (DigiCert, Sectigo, GlobalSign)
5. Add signing status to release notes: "unsigned" or "signed with cert XYZ"

**Warning signs:** GitHub Releases show "signed installer" in notes but users still report security warnings.

### Pitfall 6: NSIS Installer Size Bloat

**What goes wrong:** Installer .exe grows to 200MB+ when PyInstaller dist/ is only 80MB. Slow downloads, users suspect bloatware.

**Why it happens:**
- NSIS default compression not optimal (LZMA vs zlib)
- Including unnecessary files from dist/ (PyInstaller debug files, .pyc caches)
- Not using solid compression (compresses each file separately)
- Including multiple copies of same DLLs (PyInstaller bug with some libraries)

**How to avoid:**
1. Set compression in NSIS script: `SetCompressor /SOLID lzma` (best ratio, slower build)
2. Clean dist/ before packaging: remove `*.pyc`, `__pycache__`, `.pyi` files
3. Use `File /r /x` to exclude patterns: `/x *.pyc /x __pycache__`
4. Compare installer size to dist/ size (should be 60-80% after compression)
5. Test installer extraction time (ultra compression = slow extraction)

**Warning signs:** Installer .exe significantly larger than .zip/.tar.gz for same platform.

## Code Examples

Verified patterns from official sources:

### DMG Creation with Custom Background (macOS)

```bash
#!/bin/bash
# Source: create-dmg documentation (https://github.com/create-dmg/create-dmg)

VERSION="$1"
APP_NAME="JobRadar.app"
DMG_NAME="Job-Radar-${VERSION}.dmg"

create-dmg \
  --volname "Job Radar Installer" \
  --volicon "installers/macos/dmg-icon.icns" \
  --background "installers/macos/dmg-background.png" \
  --window-pos 200 120 \
  --window-size 800 500 \
  --icon-size 128 \
  --text-size 12 \
  --icon "$APP_NAME" 200 190 \
  --hide-extension "$APP_NAME" \
  --app-drop-link 600 190 \
  --eula "LICENSE" \
  --format UDZO \
  "$DMG_NAME" \
  "dist/$APP_NAME"
```

**Key options:**
- `--window-size 800 500` - Larger window per user decision (not standard 600x400)
- `--icon "$APP_NAME" 200 190` - App icon at x=200, y=190 (left side)
- `--app-drop-link 600 190` - Applications folder at x=600, y=190 (right side, aligned horizontally)
- `--format UDZO` - Compressed read-only (UDBZ = bzip2, slower but smaller)
- `--eula` - Attach license (shows on mount, optional)

### NSIS Modern UI with License and Shortcuts

```nsis
# Source: NSIS Modern UI documentation (https://nsis.sourceforge.io/Docs/Modern%20UI/Readme.html)

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "Job Radar"
OutFile "Job-Radar-Setup-${VERSION}.exe"
InstallDir "$PROGRAMFILES\Job Radar"
RequestExecutionLevel admin

# Branding
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"           # 150x57px
!define MUI_WELCOMEFINISHPAGE_BITMAP "sidebar.bmp"    # 164x314px
!define MUI_BGCOLOR "FFFFFF"                          # White background
!define MUI_TEXTCOLOR "000000"                        # Black text

# Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "dist\job-radar\*.*"

  CreateDirectory "$SMPROGRAMS\Job Radar"
  CreateShortcut "$SMPROGRAMS\Job Radar\Job Radar.lnk" "$INSTDIR\job-radar.exe"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  # Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "DisplayName" "Job Radar"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "DisplayVersion" "${VERSION}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar" \
    "NoRepair" 1
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\Job Radar\Job Radar.lnk"
  RMDir "$SMPROGRAMS\Job Radar"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\JobRadar"
SectionEnd
```

### Windows File Association Registration

```nsis
# Source: NSIS File Association documentation (https://nsis.sourceforge.io/File_Association)

!include "FileFunc.nsh"

# In Install section
Section "Install"
  # ... other install steps ...

  # Register .jobprofile extension
  WriteRegStr HKCR ".jobprofile" "" "JobRadarProfile"
  WriteRegStr HKCR "JobRadarProfile" "" "Job Radar Profile"
  WriteRegStr HKCR "JobRadarProfile\DefaultIcon" "" "$INSTDIR\job-radar.exe,0"
  WriteRegStr HKCR "JobRadarProfile\shell\open\command" "" '"$INSTDIR\job-radar.exe" "%1"'

  # Refresh shell to recognize association
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'
SectionEnd

# In Uninstall section
Section "Uninstall"
  # ... other uninstall steps ...

  # Remove file association
  DeleteRegKey HKCR ".jobprofile"
  DeleteRegKey HKCR "JobRadarProfile"

  # Refresh shell
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'
SectionEnd
```

**Critical:** `SHChangeNotify` call required or Windows won't recognize association change until reboot.

### GitHub Actions Matrix Build with Conditional Signing

```yaml
# Source: PyInstaller GitHub Actions examples and code signing best practices

build-installers:
  name: Build ${{ matrix.platform }} installer
  runs-on: ${{ matrix.os }}
  strategy:
    fail-fast: false
    matrix:
      include:
        - os: macos-latest
          platform: macos
          installer: "*.dmg"
        - os: windows-latest
          platform: windows
          installer: "*.exe"

  steps:
    - uses: actions/checkout@v4

    - name: Install build tools (macOS)
      if: runner.os == 'macOS'
      run: brew install create-dmg

    - name: Install build tools (Windows)
      if: runner.os == 'Windows'
      run: choco install nsis -y

    - name: Build installer
      run: |
        cd installers/${{ matrix.platform }}
        ./build.sh ${{ github.ref_name }}

    # Conditional signing - only runs if secret exists
    - name: Code sign (macOS)
      if: runner.os == 'macOS' && secrets.MACOS_CERT_BASE64 != ''
      env:
        MACOS_CERT_BASE64: ${{ secrets.MACOS_CERT_BASE64 }}
        MACOS_CERT_PASSWORD: ${{ secrets.MACOS_CERT_PASSWORD }}
      run: |
        # Signing logic here
        echo "Signing DMG..."

    - name: Verify signature (macOS)
      if: runner.os == 'macOS' && secrets.MACOS_CERT_BASE64 != ''
      run: |
        codesign --verify --deep --verbose=2 *.dmg
        echo "✓ Signature verified"

    - name: Upload installer
      uses: actions/upload-artifact@v4
      with:
        name: installer-${{ matrix.platform }}
        path: installers/${{ matrix.platform }}/${{ matrix.installer }}
```

**Key pattern:** Conditional `if: secrets.CERT != ''` allows workflow to work unsigned, then automatically sign when secrets added (no code changes).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Code signing certs valid 39 months | Maximum 460 days validity | March 1, 2026 | Must renew certificates 3x more often; automation becomes critical vs manual renewal |
| File-based code signing (local .pfx/.p12) | HSM-based signing (FIPS 140-2 Level 2+) | June 1, 2023 | Cloud-based signing services (DigiCert KeyLocker, Azure Trusted Signing) now required for new certs |
| DMG creation via Disk Utility GUI | create-dmg shell script automation | ~2015 (tool matured) | CI/CD-friendly; reproducible builds; version control for DMG layout |
| NSIS Classic UI | NSIS Modern UI 2 | NSIS 2.0 (2004) | Modern wizard UX; but still actively maintained, current standard |
| Manual AppleScript for DMG layout | create-dmg --icon and --window-size flags | create-dmg 1.0+ | Declarative syntax vs imperative AppleScript; fewer edge cases |
| Separate installers for 32-bit/64-bit Windows | 64-bit only installers | ~2020 (Windows 10 mainstream) | Job Radar targets Python 3.10+ (64-bit default); no 32-bit support needed |

**Deprecated/outdated:**
- **InstallShield**: Commercial tool ($3000+), overkill for simple installers; NSIS free and sufficient
- **appdmg (npm)**: Still works but Node.js dependency unnecessary when create-dmg is shell-only
- **StartSSL/WoSign code signing**: Certificate authorities distrusted 2016-2017; use DigiCert/Sectigo/GlobalSign
- **PackageMaker (macOS)**: Deprecated by Apple in 2016; use DMG or .pkg with pkgbuild command-line tool
- **Windows XP/Vista targeting**: Python 3.10+ requires Windows 8.1+; ignore old installer compatibility

## Open Questions

Things that couldn't be fully resolved:

1. **Auto-update infrastructure URL format**
   - What we know: User wants update check URL in config, prepared for future auto-update feature
   - What's unclear: Specific JSON schema for update manifest (version, download URL, changelog URL, min version for update)
   - Recommendation: Use simple JSON on GitHub Pages: `{"version": "2.1.0", "macos_dmg_url": "...", "windows_exe_url": "...", "min_version": "2.0.0"}`. App fetches JSON, compares version strings, shows "Update available" in GUI. Defer actual download/install mechanism to future phase.

2. **Dual uninstall approach implementation**
   - What we know: User wants both GUI uninstall (via app) and Add/Remove Programs support
   - What's unclear: How to trigger in-app uninstall from Add/Remove Programs (UninstallString points to NSIS uninstaller, not app)
   - Recommendation: Add/Remove Programs shows two entries: "Job Radar (Application)" with UninstallString pointing to job-radar.exe --uninstall-gui, and "Job Radar (Quick Remove)" with standard NSIS uninstaller. Allows user choice between full GUI with backup or quick silent remove.

3. **macOS Gatekeeper notarization timeline**
   - What we know: Notarization requires Apple Developer account ($99/year), not same as code signing
   - What's unclear: Whether notarization will become mandatory for non-App Store distribution (currently "recommended")
   - Recommendation: Plan for notarization in same phase as code signing (future), but document as separate requirement. Apple increasingly blocks un-notarized apps on new macOS versions.

4. **Windows SmartScreen reputation building**
   - What we know: EV code signing certs no longer instantly bypass SmartScreen (policy change March 2024)
   - What's unclear: How many downloads/installs needed to build "reputation" and remove warnings
   - Recommendation: Expect 2-4 weeks of warnings even with valid cert. Encourage early adopters to click "Run anyway" to build telemetry. No way to bypass this waiting period.

## Sources

### Primary (HIGH confidence)

- [create-dmg GitHub repository](https://github.com/create-dmg/create-dmg) - Official documentation and examples
- [NSIS Modern UI Documentation](https://nsis.sourceforge.io/Docs/Modern%20UI/Readme.html) - Official NSIS Modern UI 2 reference
- [PyInstaller Usage Documentation](https://pyinstaller.org/en/stable/usage.html) - Official PyInstaller 6.x docs
- [NSIS Add/Remove Programs Integration](https://nsis.sourceforge.io/Add_uninstall_information_to_Add/Remove_Programs) - Registry keys reference
- [NSIS File Association](https://nsis.sourceforge.io/File_Association) - FileAssociation.nsh macros documentation
- [DigiCert Code Signing Certificate Validity Change](https://www.digicert.com/blog/understanding-the-new-code-signing-certificate-validity-change) - 460-day limit announcement

### Secondary (MEDIUM confidence)

- [GitHub Actions PyInstaller Multi-OS](https://github.com/NotCookey/Pyinstaller-Github-Actions) - Community workflow examples verified with official GitHub Actions docs
- [NSIS Best Practices](https://nsis.sourceforge.io/Best_practices) - Official NSIS wiki, community-edited
- [DropDMG Manual: Layouts](https://c-command.com/dropdmg/help/layouts) - Commercial tool docs showing DMG design best practices
- [macOS DMG Background Guidelines](https://v2.tauri.app/distribute/dmg/) - Tauri framework docs (cross-verified with Apple HIG)

### Tertiary (LOW confidence)

- WebSearch results on code signing SmartScreen reputation building (no official Microsoft documentation found, based on developer reports)
- Medium articles on DMG creation workflow (cross-verified techniques with official create-dmg docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - create-dmg and NSIS are industry-standard tools with 10+ years maturity, official documentation comprehensive
- Architecture: HIGH - Patterns verified with official docs and working examples from PyInstaller/NSIS communities
- Pitfalls: MEDIUM - Based on NSIS forums, GitHub Issues, and community articles; cross-verified where possible but some edge cases anecdotal

**Research date:** 2026-02-14
**Valid until:** 2026-04-14 (60 days - installer tooling stable, but code signing policies evolving)

**Notes:**
- Code signing certificate validity change (460 days) is recent (March 2026); monitor CA/Browser Forum for further policy updates
- macOS notarization requirements may tighten with future macOS releases; revalidate when macOS 15+ launches
- Windows 11 UI for Add/Remove Programs differs from Windows 10; test on both versions
