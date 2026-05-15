@echo off
REM Build Job Radar standalone executable for Windows.
REM Usage: scripts\build.bat
REM Output: dist\job-radar\ (executable bundle) + ZIP archive

setlocal
for /f "usebackq delims=" %%V in (`python -c "from job_radar import __version__; print(__version__)"`) do set VERSION=%%V
set RELEASE_VERSION=v%VERSION:v=%

echo === Job Radar Build Script ===
echo Version: %RELEASE_VERSION%
echo Platform: Windows
echo.

REM Step 1: Clean
echo Step 1: Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Step 2: Install PyInstaller if needed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Step 3: Build
echo Step 2: Building with PyInstaller...
pyinstaller job-radar.spec --clean

REM Step 4: Copy README
echo Step 3: Adding README...
copy README-dist.txt dist\job-radar\README.txt >nul 2>&1

REM Step 5: Create ZIP
echo Step 4: Creating distribution ZIP...
cd dist
powershell -NoProfile -Command "Compress-Archive -Path 'job-radar' -DestinationPath '..\job-radar-%RELEASE_VERSION%-windows.zip' -Force"
cd ..

python -m job_radar.release_verification --platform windows --version "%RELEASE_VERSION%" --checksum-manifest "job-radar-%RELEASE_VERSION%-windows.sha256"

echo.
echo === Build Complete ===
echo Executable: dist\job-radar\job-radar.exe
echo Archive: job-radar-%RELEASE_VERSION%-windows.zip
echo Checksum: job-radar-%RELEASE_VERSION%-windows.sha256
echo.
echo Quick test: dist\job-radar\job-radar.exe --help
