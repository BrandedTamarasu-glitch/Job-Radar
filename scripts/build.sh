#!/bin/bash
# Build Job Radar standalone executable and create distribution archive.
# Usage: ./scripts/build.sh
# Output: dist/job-radar/ (executable bundle) + platform-specific archive

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

VERSION="1.1.0"

echo "=== Job Radar Build Script ==="
echo "Version: $VERSION"
echo "Platform: $(uname -s) $(uname -m)"
echo ""

# Step 1: Clean previous builds
echo "Step 1: Cleaning previous builds..."
rm -rf build/ dist/

# Step 2: Install PyInstaller if needed
if ! pip show pyinstaller > /dev/null 2>&1; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Step 3: Build
echo "Step 2: Building with PyInstaller..."
pyinstaller job-radar.spec --clean

# Step 4: Copy README into dist folder
echo "Step 3: Adding README..."
cp README-dist.txt dist/job-radar/README.txt 2>/dev/null || true

# Step 5: Platform-specific distribution packaging
echo "Step 4: Creating distribution archive..."

if [[ "$(uname -s)" == "Darwin" ]]; then
    # macOS: Create ZIP of .app bundle (DMG requires create-dmg tool)
    echo "  Packaging macOS .app as ZIP..."
    cd dist
    zip -r "JobRadar-${VERSION}-macos.zip" JobRadar.app/ job-radar/README.txt 2>/dev/null || \
    zip -r "JobRadar-${VERSION}-macos.zip" job-radar/
    cd ..
    echo "  Archive: dist/JobRadar-${VERSION}-macos.zip"
else
    # Linux: Create tar.gz
    echo "  Packaging Linux binary as tar.gz..."
    cd dist
    tar -czf "job-radar-${VERSION}-linux.tar.gz" job-radar/
    cd ..
    echo "  Archive: dist/job-radar-${VERSION}-linux.tar.gz"
fi

echo ""
echo "=== Build Complete ==="
echo "Executable: dist/job-radar/job-radar"
echo ""
echo "Quick test: ./dist/job-radar/job-radar --help"
