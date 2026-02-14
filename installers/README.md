# Installing Job Radar

## Security Warnings for Unsigned Installers

Job Radar installers are currently **unsigned**. This means your operating system
will show security warnings when you try to run the installer. This is normal
for open-source software without paid code signing certificates.

### macOS: Gatekeeper Warning

When you open the DMG or try to run Job Radar, macOS may show:
> "JobRadar.app" cannot be opened because the developer cannot be verified.

**To bypass:**
1. Right-click (or Control-click) on JobRadar.app
2. Select "Open" from the context menu
3. Click "Open" in the dialog that appears
4. macOS will remember your choice for future launches

Alternatively:
1. Go to System Settings > Privacy & Security
2. Scroll down to the "Security" section
3. You'll see a message about JobRadar.app being blocked
4. Click "Open Anyway"

### Windows: SmartScreen Warning

When you run the installer, Windows may show:
> Windows protected your PC - Microsoft Defender SmartScreen prevented
> an unrecognized app from starting.

**To bypass:**
1. Click "More info" (text link below the warning message)
2. Click "Run anyway"
3. Proceed with installation normally

### Why Are Installers Unsigned?

Code signing certificates cost $100-400/year per platform. As an open-source
project, we prioritize features over certificates. Signed installers are planned
for a future release.

The source code is fully available at https://github.com/coryebert/Job-Radar
for verification.

## Building Installers Locally

### macOS DMG
```
# Requires: create-dmg (brew install create-dmg), Pillow (pip install Pillow)
pyinstaller job-radar.spec --clean
installers/macos/build-dmg.sh VERSION
```

### Windows NSIS
```
# Requires: NSIS (choco install nsis -y), Pillow (pip install Pillow)
pyinstaller job-radar.spec --clean
cd installers\windows
build-installer.bat VERSION
```

## Code Signing (CI/CD)

Installers are automatically signed when GitHub Secrets are configured:

### macOS
- `MACOS_CERT_BASE64`: Base64-encoded .p12 certificate
- `MACOS_CERT_PASSWORD`: Certificate password
- `MACOS_SIGNING_IDENTITY`: Signing identity (e.g., "Developer ID Application: Name")

### Windows
- `WINDOWS_CERT_BASE64`: Base64-encoded .pfx certificate
- `WINDOWS_CERT_PASSWORD`: Certificate password

When secrets are not set, installers build successfully but remain unsigned.
