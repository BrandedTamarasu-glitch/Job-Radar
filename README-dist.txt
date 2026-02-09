Job Radar v1.1
==============

A job search tool that scores listings against your candidate profile.

GETTING STARTED
---------------

1. Extract this folder to a location on your computer
2. Open a terminal/command prompt in this folder
3. Run the executable:
   - Windows: job-radar.exe --help
   - macOS:   ./job-radar --help  (or open JobRadar.app)
   - Linux:   ./job-radar --help

4. Create your profile:
   - Copy profiles/_template.json to profiles/your_name.json
   - Edit the file with your details (name, skills, target job titles)

5. Run a search:
   - Windows: job-radar.exe --profile profiles/your_name.json
   - macOS:   ./job-radar --profile profiles/your_name.json
   - Linux:   ./job-radar --profile profiles/your_name.json

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
