#!/bin/bash
set -euo pipefail

VERSION="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_PATH="${PROJECT_ROOT}/dist/JobRadar.app"
DMG_NAME="Job-Radar-${VERSION}-macos.dmg"

# Validate app exists
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: $APP_PATH not found. Run PyInstaller first."
    exit 1
fi

# Generate background if not present
if [ ! -f "$SCRIPT_DIR/dmg-background.png" ]; then
    echo "Generating DMG background..."
    python3 "$SCRIPT_DIR/generate-background.py"
fi

# Remove stale DMG if exists (create-dmg fails otherwise)
rm -f "$DMG_NAME"

# Build DMG with create-dmg
create-dmg \
  --volname "Job Radar Installer" \
  --background "$SCRIPT_DIR/dmg-background.png" \
  --window-pos 200 120 \
  --window-size 800 500 \
  --icon-size 128 \
  --text-size 12 \
  --icon "JobRadar.app" 200 190 \
  --hide-extension "JobRadar.app" \
  --app-drop-link 600 190 \
  --format UDZO \
  "$DMG_NAME" \
  "$APP_PATH"

echo "DMG created: $DMG_NAME"

# Conditional code signing
if [ -n "${MACOS_CERT_BASE64:-}" ]; then
    echo "Signing DMG with Apple Developer certificate..."
    KEYCHAIN_PASSWORD="${KEYCHAIN_PASSWORD:-build123}"
    echo "$MACOS_CERT_BASE64" | base64 --decode > /tmp/certificate.p12
    security create-keychain -p "$KEYCHAIN_PASSWORD" build.keychain || true
    security default-keychain -s build.keychain
    security unlock-keychain -p "$KEYCHAIN_PASSWORD" build.keychain
    security import /tmp/certificate.p12 -k build.keychain \
        -P "${MACOS_CERT_PASSWORD:-}" -T /usr/bin/codesign
    security set-key-partition-list -S apple-tool:,apple:,codesign: \
        -s -k "$KEYCHAIN_PASSWORD" build.keychain
    codesign --force --sign "${MACOS_SIGNING_IDENTITY:-Developer ID Application}" \
        --timestamp --options runtime "$DMG_NAME"
    codesign --verify --verbose=2 "$DMG_NAME"
    security delete-keychain build.keychain
    rm /tmp/certificate.p12
    echo "DMG signed successfully"
else
    echo "NOTE: No signing certificate found (MACOS_CERT_BASE64 not set)"
    echo "  DMG is unsigned - users will see Gatekeeper warning"
    echo "  See installers/README.md for bypass instructions"
fi
