Job Radar v2.8.1
==============

A desktop and command-line job search tool that scores listings against your candidate profile.

GETTING STARTED
---------------

1. Extract this folder to a location on your computer
2. Open a terminal/command prompt in this folder
3. Run the executable:
   - Windows: job-radar.exe --help
   - macOS:   ./job-radar --help  (or open JobRadar.app)
   - Linux:   ./job-radar --help

4. Create your profile:
   - Launch the GUI for guided setup, including optional PDF resume import
   - Or run the CLI and follow the interactive profile wizard

5. Run a search:
   - Windows: job-radar.exe
   - macOS:   ./job-radar
   - Linux:   ./job-radar

REQUIREMENTS
------------

- Internet connection (for fetching job listings)
- No Python installation required

TROUBLESHOOTING
---------------

"App is damaged" (macOS):
  Right-click the app > Open (first launch only).
  macOS Gatekeeper blocks unsigned apps by default.

Antivirus warning (Windows):
  Some antivirus software may flag this executable as suspicious.
  This is a false positive common with PyInstaller-packaged apps.
  Add an exception for job-radar.exe in your antivirus settings.

Errors on launch:
  Check ~/job-radar-error.log for detailed error information.

SUPPORT
-------

Report issues at the project's GitHub repository.
