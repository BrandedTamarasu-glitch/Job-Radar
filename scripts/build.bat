@echo off
REM Build Job Radar standalone executable for Windows.
REM Usage: scripts\build.bat
REM Output: dist\job-radar\ (executable bundle) + ZIP archive

setlocal
set VERSION=1.1.0

echo === Job Radar Build Script ===
echo Version: %VERSION%
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
powershell -command "Compress-Archive -Path 'job-radar' -DestinationPath 'job-radar-%VERSION%-windows.zip'"
cd ..

echo.
echo === Build Complete ===
echo Executable: dist\job-radar\job-radar.exe
echo Archive: dist\job-radar-%VERSION%-windows.zip
echo.
echo Quick test: dist\job-radar\job-radar.exe --help
