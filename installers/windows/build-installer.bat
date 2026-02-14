@echo off
setlocal enabledelayedexpansion

set VERSION=%1
if "%VERSION%"=="" set VERSION=dev

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

echo === Job Radar Windows Installer Build ===
echo Version: %VERSION%

:: Check NSIS is available
where makensis >nul 2>&1
if errorlevel 1 (
    echo ERROR: NSIS not found. Install from https://nsis.sourceforge.io/Download
    echo   Or run: choco install nsis -y
    exit /b 1
)

:: Check PyInstaller output exists
if not exist "%PROJECT_ROOT%\dist\job-radar\job-radar.exe" (
    echo ERROR: dist\job-radar\ not found. Run PyInstaller first.
    exit /b 1
)

:: Generate branding assets if not present
if not exist "%SCRIPT_DIR%header.bmp" (
    echo Generating branding assets...
    python "%SCRIPT_DIR%generate-assets.py"
)

:: Build installer
echo Building NSIS installer...
makensis /DVERSION=%VERSION% "%SCRIPT_DIR%installer.nsi"

if errorlevel 1 (
    echo ERROR: NSIS build failed
    exit /b 1
)

echo.
set INSTALLER_NAME=Job-Radar-Setup-%VERSION%.exe
echo Installer created: %INSTALLER_NAME%

:: Conditional code signing
if defined WINDOWS_CERT_BASE64 (
    echo Signing installer with code signing certificate...

    :: Decode certificate
    powershell -Command "[IO.File]::WriteAllBytes('%TEMP%\certificate.pfx', [Convert]::FromBase64String($env:WINDOWS_CERT_BASE64))"

    :: Find signtool
    set SIGNTOOL=
    for /f "delims=" %%i in ('where signtool 2^>nul') do set SIGNTOOL=%%i
    if "!SIGNTOOL!"=="" (
        for /f "delims=" %%i in ('dir /s /b "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe" 2^>nul') do set SIGNTOOL=%%i
    )

    if "!SIGNTOOL!"=="" (
        echo WARNING: signtool.exe not found. Skipping code signing.
    ) else (
        "!SIGNTOOL!" sign /f "%TEMP%\certificate.pfx" /p "%WINDOWS_CERT_PASSWORD%" /tr http://timestamp.digicert.com /td sha256 /fd sha256 "%INSTALLER_NAME%"
        if errorlevel 1 (
            echo ERROR: Code signing failed
            del "%TEMP%\certificate.pfx"
            exit /b 1
        )
        "!SIGNTOOL!" verify /pa "%INSTALLER_NAME%"
        echo Installer signed successfully
    )
    del "%TEMP%\certificate.pfx"
) else (
    echo NOTE: No signing certificate found ^(WINDOWS_CERT_BASE64 not set^)
    echo   Installer is unsigned - users will see SmartScreen warning
    echo   See installers\README.md for bypass instructions
)

echo.
echo Build complete!
