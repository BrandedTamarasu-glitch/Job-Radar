# Job Radar

A job search tool that searches multiple job boards, scores listings against your profile, and generates ranked reports. Features include multi-source search (Dice, HN Hiring, RemoteOK, We Work Remotely), fuzzy skill matching, an interactive setup wizard, and dual-format HTML and Markdown reports.

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

**Bypassing Gatekeeper (required for unsigned apps):**

macOS will block the app because it's unsigned. Choose **either** method:

**Remove quarantine attribute:**
```bash
xattr -d com.apple.quarantine /Applications/JobRadar.app
```

**Run from Terminal:**

Job Radar is a command-line tool, so it needs to run in Terminal:

```bash
/Applications/JobRadar.app/Contents/MacOS/JobRadar
```

**Optional: Create an alias** for easier access:
```bash
echo 'alias job-radar="/Applications/JobRadar.app/Contents/MacOS/JobRadar"' >> ~/.zshrc
source ~/.zshrc
```

Then you can just type `job-radar` to run it.

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
2. **Follow the wizard prompts** to enter:
   - Your name
   - Your core skills (technologies you know)
   - Target job titles (roles you're searching for)
   - Preferred location (optional)
   - Dealbreakers (requirements that disqualify a job)
   - Search preferences (minimum score, new-only mode)
3. **Search runs automatically** after the wizard completes
4. **View your results** in the HTML report that opens in your browser

On subsequent launches, the search runs directly with your saved profile (no wizard).

For advanced usage and all available options, run:
```bash
job-radar --help
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
| `--validate-profile PATH` | Validate a profile JSON file and exit |

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

The project includes a comprehensive test suite with 48+ automated tests:

```bash
# Install dev dependencies
pip install pytest

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
- UX polish (integration tests) - validates banner, help text, progress messages, and error handling

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
