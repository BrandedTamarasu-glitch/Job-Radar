# Job Radar

A job search tool that searches multiple job boards, scores listings against your profile, and generates ranked reports. Features include multi-source search (6 API sources: Dice, HN Hiring, RemoteOK, We Work Remotely, Adzuna, Authentic Jobs + 4 manual URLs: Wellfound, Indeed, LinkedIn, Glassdoor), PDF resume import, fuzzy skill matching, cross-source deduplication, an interactive setup wizard, and dual-format HTML and Markdown reports with one-click URL copying, keyboard shortcuts, application status tracking, and WCAG 2.1 Level AA accessibility.

## Installation

### Download

Download the latest release for your platform from the [GitHub Releases page](https://github.com/BrandedTamarasu-glitch/Job-Radar/releases/latest):

- **Windows:** `job-radar-vX.X.X-windows.zip`
- **macOS:** `job-radar-vX.X.X-macos.zip`
- **Linux:** `job-radar-vX.X.X-linux.tar.gz`

> **IMPORTANT: Security Warnings**
>
> These are unsigned executables because code signing certificates cost $300-500/year. This is normal for open-source tools distributed as standalone applications.
>
> **You will see security warnings:**
> - **Windows SmartScreen:** Click "More info" then click "Run anyway"
> - **macOS Gatekeeper:** Right-click the app and select "Open" (first launch only)
> - **Antivirus software:** May flag the executable as suspicious - this is a false positive common with PyInstaller-packaged applications
>
> These warnings do NOT mean the software is malicious. The source code is publicly available in this repository for inspection.

### Windows

1. Download `job-radar-vX.X.X-windows.zip` from the Releases page
2. Right-click the ZIP file and select "Extract All"
3. Open the extracted `job-radar` folder
4. Double-click `job-radar.exe`
5. When Windows SmartScreen appears, click "More info" then "Run anyway"
6. The setup wizard will guide you through creating your profile

### macOS

1. Download `job-radar-vX.X.X-macos.zip` from the Releases page
2. Double-click the ZIP file to extract it
3. Drag `JobRadar.app` to your Applications folder (optional but recommended)
4. Remove the quarantine attribute (required for unsigned apps):
   ```bash
   xattr -d com.apple.quarantine /Applications/JobRadar.app
   ```
5. **Double-click `JobRadar.app`** to launch it

The app will open a Terminal window and run the interactive setup wizard.

**Alternative: Run from Terminal directly**

For advanced users or to create an alias:
```bash
# Run directly
/Applications/JobRadar.app/Contents/MacOS/job-radar-cli

# Or create an alias
echo 'alias job-radar="/Applications/JobRadar.app/Contents/MacOS/job-radar-cli"' >> ~/.zshrc
source ~/.zshrc
```

### Linux

1. Download `job-radar-vX.X.X-linux.tar.gz` from the Releases page
2. Extract the archive:
   ```bash
   tar -xzf job-radar-vX.X.X-linux.tar.gz
   ```
3. Run the executable:
   ```bash
   ./job-radar/job-radar
   ```
4. If you see "Permission denied", make the file executable:
   ```bash
   chmod +x job-radar/job-radar
   ```
5. The setup wizard will guide you through creating your profile

## Quick Start

On first launch, Job Radar runs an interactive setup wizard that guides you through creating your profile:

1. **Launch the app** using the instructions above for your platform
2. **Choose your setup method:**
   - **Upload PDF resume** (recommended) — automatically extracts name, skills, titles, and experience
   - **Fill manually** — guided prompts for each field
3. **Follow the wizard prompts** to enter or review:
   - Your name
   - Your core skills (technologies you know)
   - Target job titles (roles you're searching for)
   - Years of experience
   - Preferred location (optional)
   - Dealbreakers (requirements that disqualify a job)
   - Search preferences (minimum score, new-only mode)
4. **Search runs automatically** after the wizard completes
5. **View your results** in the HTML report that opens in your browser

On subsequent launches, the search runs directly with your saved profile (no wizard). A profile preview shows your current settings before the search begins.

### Updating Your Profile

After initial setup, you can update your profile without re-running the full wizard:

```bash
# View your current profile
job-radar --view-profile

# Interactive editor — select a field, change it, see diff, confirm
job-radar --edit-profile

# Quick CLI updates for scripted workflows
job-radar --update-skills "python,react,typescript"
job-radar --set-min-score 3.5
job-radar --set-titles "Backend Developer,SRE"
```

All profile updates use atomic writes (no corruption risk) and create automatic backups.

### Using Your Report

The HTML report includes interactive features and visual hierarchy to help you scan results quickly:

**Visual Hierarchy:**
- **Hero Jobs (4.0+):** Top matches appear in an elevated section at the top with distinct styling and "Top Match" badges
- **Color-coded tiers:** Green (4.0+), Cyan (3.5-3.9), Indigo (2.8-3.4) with colorblind-safe indicators
- **Responsive design:** Adapts from desktop (11 columns) → tablet (7 columns) → mobile (stacked cards)

**Interactive Features:**
- **Copy URL** buttons on each job listing for quick clipboard access
- **Copy All Recommended** button to batch-copy all high-scoring job URLs
- **Keyboard shortcuts:** Press `C` to copy a focused job's URL, `A` to copy all recommended URLs
- **Status tracking:** Mark jobs as Applied, Interviewing, Rejected, or Offer — status persists across sessions
- **Filtering:** Hide jobs by status (Applied, Rejected, Interviewing, Offer) with filter state persistence
- **CSV Export:** Download all visible job results as a spreadsheet (UTF-8, Excel-compatible)
- **Print-optimized:** Press Cmd+P/Ctrl+P for clean offline output with preserved tier colors

### Optional: API Credentials

To use Adzuna and Authentic Jobs API sources, set up API keys:

```bash
job-radar --setup-apis
```

The wizard will guide you through obtaining and configuring API credentials. API keys are optional — the tool works without them using the 4 scraper-based sources.

For advanced usage and all available options, run:
```bash
job-radar --help
```

## Uninstalling

### Windows

1. Delete the `job-radar` folder (wherever you extracted it)
2. Delete the configuration directory:
   - Press `Win+R`, type `%USERPROFILE%\.job-radar`, press Enter
   - Delete the entire `.job-radar` folder

### macOS

**For unsigned apps like Job Radar, you cannot simply drag to Trash. Follow these steps:**

1. **Remove the app bundle:**
   ```bash
   sudo rm -rf /Applications/JobRadar.app
   ```
   Enter your password when prompted.

2. **Delete configuration files:**
   ```bash
   rm -rf ~/.job-radar
   ```

3. **Clear rate limit database (if using API sources):**
   ```bash
   rm -rf ~/.rate_limits
   ```

**Why sudo is needed:** macOS prevents unsigned apps from being deleted normally as a security measure. The `sudo rm` command bypasses this restriction.

### Linux

1. Delete the extracted `job-radar` directory
2. Delete configuration files:
   ```bash
   rm -rf ~/.job-radar
   ```
3. If you used API sources, also delete:
   ```bash
   rm -rf ~/.rate_limits
   ```

## Score Ratings

| Score | Rating | Action |
|---|---|---|
| 4.0+ | Strong Recommend | Apply immediately |
| 3.5-3.9 | Recommend | Worth applying |
| 2.8-3.4 | Worth Reviewing | Read the full posting first |
| < 2.8 | Excluded from report | |

## Command Reference

### Search Options

| Flag | Description |
|---|---|
| `--min-score N` | Minimum match score (1.0-5.0, default: 2.8) |
| `--new-only` / `--no-new-only` | Only show new (unseen) results (default: false) |
| `--from YYYY-MM-DD` | Start date for job postings (default: 48 hours ago) |
| `--to YYYY-MM-DD` | End date for job postings (default: today) |

### Output Options

| Flag | Description |
|---|---|
| `--output DIR` | Output directory for reports (default: `results/`) |
| `--no-open` | Don't auto-open report in browser after generation |

### Profile Options

| Flag | Description |
|---|---|
| `--profile PATH` | Path to candidate profile JSON file |
| `--config PATH` | Path to config file (default: auto-detect) |
| `--view-profile` | Display your current profile settings and exit |
| `--edit-profile` | Launch interactive profile editor |
| `--update-skills "a,b,c"` | Replace skills list and exit (comma-separated) |
| `--set-min-score N` | Set minimum score threshold (0.0-5.0) and exit |
| `--set-titles "a,b"` | Replace target titles and exit (comma-separated) |
| `--validate-profile PATH` | Validate a profile JSON file and exit |

### Accessibility Options

| Flag | Description |
|---|---|
| `--no-color` | Disable all terminal colors (also respects `NO_COLOR` env var) |

### Developer Options

| Flag | Description |
|---|---|
| `--dry-run` | Show search queries without fetching data |
| `--verbose` / `-v` | Enable debug logging |
| `--no-cache` | Disable HTTP response caching (force fresh fetches) |
| `--no-wizard` | Skip setup wizard (for automated testing) |
| `--version` | Show version number and exit |

### Examples

```bash
# Basic search (uses saved profile from wizard)
job-radar

# Search with higher quality threshold
job-radar --min-score 3.5

# Only show new listings from the last week
job-radar --from 2026-02-01 --new-only

# Search a specific date range
job-radar --from 2026-02-01 --to 2026-02-06

# Use a specific profile file
job-radar --profile path/to/profile.json

# Fresh fetch with debug logging
job-radar --no-cache -v

# Preview queries without running them
job-radar --dry-run
```

## Development

### From Source

If you're a developer who wants to run from source or contribute to the project:

```bash
# Clone the repository
git clone https://github.com/BrandedTamarasu-glitch/Job-Radar.git
cd Job-Radar

# Install in development mode
pip install -e .

# Run the tool
python -m job_radar
```

**Requirements:** Python 3.10+ (macOS, Linux, or Windows)

### Running Tests

The project includes a comprehensive test suite with 450+ automated tests:

```bash
# Install dev dependencies
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_scoring.py
```

**Test coverage:**
- Scoring functions (37 tests) - validates all `_score_*` functions with parametrized edge cases
- Tracker functions (11 tests) - validates deduplication and stats aggregation with tmp_path isolation
- Config module (23 tests) - validates config file parsing, CLI override, defaults, validation
- Wizard (38 tests) - validates setup flow, PDF integration, navigation, error handling
- API integration (45 tests) - validates Adzuna/Authentic Jobs mappers, rate limiting, deduplication
- PDF parser (34 tests) - validates extraction, validation, Unicode support, error handling
- Report generation (34 tests) - validates HTML/Markdown output, clipboard UI, status tracking, accessibility
- UX polish (68 tests) - validates banner, help text, progress messages, error handling
- Profile manager (22 tests) - validates atomic writes, backups, rotation, schema migration, validation
- Profile display (16 tests) - validates formatted output, field filtering, NO_COLOR compliance
- Profile editor (23 tests) - validates field menu, diff preview, editing, validator reuse
- CLI update flags (40 tests) - validates validators, handlers, mutual exclusion, integration

### Building Executables

To build standalone executables for distribution:

```bash
# Windows
scripts\build.bat

# macOS and Linux
./scripts/build.sh
```

Build artifacts are created in the `dist/` directory.

## Further Reading

- [WORKFLOW.md](WORKFLOW.md) - Full documentation: profile field reference, scoring rubric breakdown, source details, customization options, and daily workflow tips
- [CHANGELOG.md](CHANGELOG.md) - Version history
