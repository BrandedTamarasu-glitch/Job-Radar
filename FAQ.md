# Job Radar — Frequently Asked Questions

**Version 2.8.1** | [Changelog](CHANGELOG.md) | [README](README.md) | [Full Documentation](WORKFLOW.md)

## Installation & Setup

### Why am I seeing security warnings when I try to run Job Radar?

Job Radar is distributed as an unsigned executable. Code signing certificates cost $300-500/year, which is prohibitive for open-source projects. This is normal and does NOT mean the software is malicious.

**Windows SmartScreen:**
1. Click "More info"
2. Click "Run anyway"

**macOS Gatekeeper:**
1. Right-click the app and select "Open", or
2. Go to System Settings → Privacy & Security → "Open Anyway"

The source code is publicly available on GitHub for inspection.

### Which installer should I download?

**Windows:**
- **Recommended:** `Job-Radar-Setup-vX.X.X.exe` (NSIS installer with Start Menu shortcuts)
- **Portable:** `job-radar-vX.X.X-windows.zip` (no installation required)

**macOS:**
- **Recommended:** `Job-Radar-vX.X.X-macos.dmg` (drag-to-Applications installer)
- **Portable:** `job-radar-vX.X.X-macos.zip` (no installation required)

**Linux:**
- `job-radar-vX.X.X-linux.tar.gz` (extract and run)

### Do I need Python installed to use Job Radar?

No. The standalone executables include all dependencies bundled via PyInstaller. Python is only required if you're running from source code.

### Where are my configuration files stored?

Job Radar stores user data in the platform app data directory:

| Data | Location |
|---|---|
| Profile | app data `profile.json` |
| Config | app data `config.json` |
| Reports | app data `results/` by default, or your custom `--output` directory |
| Tracker | app data `results/tracker.json`; existing launch-directory trackers are read as a legacy fallback |
| HTTP cache | app data `cache/` |
| Rate limits | app data `rate_limits/` |
| Backups | app data `backups/` |
| Error log | home directory `job-radar-error.log` |

Common app data locations:
- **Windows:** `%APPDATA%\JobRadar\`
- **macOS:** `~/Library/Application Support/JobRadar/`
- **Linux:** `~/.local/share/JobRadar/`

### What does Storage Maintenance show?

The Settings tab summarizes local app data size, HTTP cache file counts, tracker history, review-state counts, and saved-search counts. This is a local-only inspection of the Job Radar app data directory. Clearing HTTP cache removes temporary job-board responses, but does not remove your profile, reports, application tracker, review state, or saved searches.

### Can I use Job Radar without API keys?

Yes. Job Radar works out-of-the-box with 6 no-key automated sources:
- Dice.com (scraper)
- HN Hiring (scraper)
- RemoteOK (public API)
- We Work Remotely (scraper)
- Jobicy (public API, rate limited to 1/hour)
- hiring.cafe (public API, rate limited to 60/hour)

It also creates 5 manual URL builders you can open yourself: Wellfound, Indeed, LinkedIn, Glassdoor, and We Work Remotely.

API keys for Adzuna, Authentic Jobs, JSearch, USAJobs, and SerpAPI expand coverage but are optional.

## API Configuration

### How do I get API keys?

**Via GUI (Recommended):**
1. Open Job Radar GUI → Settings tab
2. Scroll to API Configuration
3. Click the documentation links for each API to sign up
4. Enter your API keys and click **Test** to validate
5. Click **Save** to persist

**Via CLI:**
```bash
job-radar --setup-apis
```

The wizard guides you through obtaining and configuring API keys for each source.

### What are the API rate limits?

| API | Free Tier Limit | Job Radar Rate Limit |
|-----|----------------|---------------------|
| Adzuna | 250/month, 5000/month with app ID | 60/min, 1000/day |
| Authentic Jobs | 100/day | 60/min |
| JSearch | Varies by plan | 60/min |
| USAJobs | No documented limit | 60/min |
| SerpAPI | 100 searches/month | 50/min (conservative) |
| Jobicy | 1/hour (public API) | 1/hour |
| hiring.cafe | No documented limit | 60/hour |

Job Radar automatically respects these limits using SQLite-backed rate limiting. The GUI Settings tab shows real-time quota usage with color-coded warnings.

### Why is my API key validation failing?

**Common issues:**
1. **Typo in API key** — Copy-paste from the API provider carefully
2. **Network issues** — Check your internet connection
3. **API quota exhausted** — Wait for quota reset or upgrade plan
4. **API endpoint down** — Try again later

Job Radar stores keys even on validation failure (graceful degradation) so network issues don't block setup. Invalid keys simply won't fetch results.

### How do I view my API quota usage?

**GUI:** Settings tab → API Configuration shows real-time quota (e.g., "15/100 daily searches used") with color-coded warnings:
- Gray: Normal usage
- Orange: 80%+ of quota used
- Red: 100% quota exhausted

**CLI:** Quota is tracked automatically but not displayed. Use GUI to monitor usage.

## Profile Management

### How do I update my profile after initial setup?

**GUI:** Profile tab → Edit your profile fields → Save

**CLI:**
```bash
# View current profile
job-radar --view-profile

# Interactive editor with diff preview
job-radar --edit-profile

# Quick CLI updates
job-radar --update-skills "python,react,typescript"
job-radar --set-min-score 3.5
job-radar --set-titles "Backend Developer,SRE"
```

All updates create automatic backups and use atomic writes to prevent corruption.

### What's the difference between core_skills and secondary_skills?

- **core_skills** — Your strongest 5-7 technologies. Counted at full weight in scoring.
- **secondary_skills** — Technologies you know but aren't your focus. Counted at half weight.

Example:
- **Core:** `["python", "django", "postgresql", "docker", "aws"]`
- **Secondary:** `["javascript", "react", "redis", "kubernetes"]`

### Can I import my resume to create a profile?

Yes! The GUI Profile tab includes a "Upload PDF Resume" button. Job Radar extracts:
- Name
- Skills (technology keywords)
- Job titles
- Years of experience

You can then review and edit the auto-filled fields before saving.

### How do I back up my profile?

**Automatic:** Job Radar creates timestamped backups before every profile update in the app data `backups/` directory (keeps last 10).

**Manual:**
- GUI Settings tab → Uninstall section → "Create Backup" button (creates ZIP with profile and config)
- Or copy app data `profile.json` manually

The uninstall backup ZIP does not include reports or tracker data. Copy app data `results/` separately if you want to keep generated reports or cross-run history.

### What are dealbreakers and how do they work?

Dealbreakers are keywords that automatically disqualify job listings. If a job description contains any dealbreaker keyword, it receives a score of 0 and is excluded from reports.

**Example:**
```json
"dealbreakers": ["clearance required", "C++", "on-site only"]
```

This excludes jobs mentioning security clearance, C++ development, or on-site-only roles.

**Tips:**
- Be specific to avoid false positives
- Case-insensitive matching
- Partial matches work (e.g., "clearance" matches "security clearance required")

## Scoring System

### How are jobs scored?

Jobs are scored on a 1.0-5.0 scale using 6 weighted components (default weights, customizable in GUI Settings):

| Component | Weight | What it measures |
|-----------|--------|------------------|
| Skills match | 25% | Core skills and secondary skills found in the title, company, and description |
| Title relevance | 15% | How closely the job title matches your target titles |
| Seniority alignment | 15% | Level and years of experience fit |
| Location/arrangement fit | 15% | Remote, hybrid, onsite, and location preferences |
| Domain relevance | 10% | Domain expertise keywords from your profile |
| Response likelihood | 20% | Source quality, directness, staffing signals, and listing quality |

After scoring, adjustments are applied:
- **Staffing firm preference** — Boost (+0.5 points), Neutral (0), or Penalize (-1.0 point)
- **Comp floor penalty** — Jobs below your floor lose 0.5-1.5 points
- **Parse confidence** — Low-confidence listings lose 0.3 points
- **Dealbreakers** — Hard disqualification (score 0, excluded)

### Can I customize the scoring weights?

Yes! (v2.1.0+) GUI Settings tab → Scoring Configuration:

1. Adjust the 6 component weights using sliders
2. See live preview of how changes affect a sample job
3. Click **Normalize** to auto-adjust weights to sum to 1.0
4. Click **Reset** to restore defaults
5. Click **Apply** to save changes

### What is staffing firm preference?

Some job listings come from staffing/consulting firms rather than direct employers. You can control how these are scored:

- **Boost (+0.5 points)** — Prefer staffing firms (higher callback rates, more opportunities)
- **Neutral (0%)** — No preference (default for new profiles)
- **Penalize (-1.0 point)** — Avoid staffing firms (prefer direct employers)

Set this in GUI Settings → Scoring Configuration.

### What do the score ratings mean?

| Score | Rating | Action |
|-------|--------|--------|
| 4.0+ | Strong Recommend | Apply immediately |
| 3.5-3.9 | Recommend | Worth applying |
| 2.8-3.4 | Worth Reviewing | Read full posting first |
| < 2.8 | Excluded | Not shown in report |

The `--min-score` flag (default: 2.8) controls the threshold for inclusion in reports.

### Why are some jobs marked "NEW" and others not?

Job Radar maintains an app data `results/tracker.json` file that tracks all jobs seen across runs. Jobs appearing for the first time are marked "NEW". Previously seen jobs show as "seen" to help you focus on fresh listings. Existing launch-directory `results/tracker.json` files are still read as a legacy fallback.

## Report Features

### How do I use the HTML report?

The HTML report opens automatically in your browser after each search. Features include:

**Visual Hierarchy:**
- Hero Jobs (4.0+) at the top with "Top Match" badges
- Color-coded tiers: Green (4.0+), Cyan (3.5-3.9), Indigo (2.8-3.4)

**Interactive Features:**
- **Copy URL** buttons on each job
- **Copy All Recommended** button for batch copying
- **Keyboard shortcuts** — `C` to copy focused URL, `A` to copy all recommended
- **Status tracking** — Mark jobs as Applied, Interviewing, Rejected, or Offer
- **Filtering** — Hide jobs by status
- **CSV Export** — Download results as spreadsheet
- **Print** — Cmd+P/Ctrl+P for clean offline output

### How does status tracking work?

Click the status dropdown on any job card to mark it as Applied, Interviewing, Rejected, or Offer. Status changes made inside a generated HTML report are saved to **browser localStorage** for that browser and report file. Use **Export Status Updates** in the report, then **Applications → Import Status JSON** in the desktop app to merge those pending updates into the app tracker.

The desktop app embeds known tracker status when it generates a report. Report-side changes remain local annotations until you export and import them through that workflow.

### Can I export results to a spreadsheet?

Yes! Click the **Export to CSV** button at the top of the HTML report. The CSV file:
- Includes all visible jobs (respects status filters)
- UTF-8 encoded with BOM for Excel compatibility
- RFC 4180 compliant (quoted fields, escaped quotes)
- Formula injection protected (=, +, -, @ prefix protection)

### What are "talking points" in the report?

For recommended roles (score ≥3.5), Job Radar generates cover letter talking points by matching your profile `highlights` against the job description. These are suggested conversation starters for applications or interviews.

**Example:**
If your profile includes:
```json
"highlights": [
  "Reduced API latency by 40% using Redis caching",
  "Led migration from monolith to microservices (Docker, Kubernetes)"
]
```

And a job mentions "microservices architecture", Job Radar suggests:
> "Led migration from monolith to microservices (Docker, Kubernetes)"

### How do I open old reports?

All reports are saved to app data `results/` by default, or your custom `--output` directory, with timestamped filenames:

```
results/
├── job-search-2026-02-14T143522.html
├── job-search-2026-02-14T143522.md
└── tracker.json
```

Open any generated `.html` report in your browser. Known tracker statuses are embedded when the report is generated. Status edits made inside the report stay in browser localStorage until you use **Export Status Updates** and then **Applications → Import Status JSON** in the desktop app.

## Troubleshooting

### The search is taking a very long time

Job Radar can query 11 automated sources plus 5 manual URL builders. Some automated sources, especially scrapers, can be slow. Typical search duration: 30-90 seconds.

**If it takes longer:**
1. Check your internet connection
2. Some sources may be rate-limited or down
3. Use `--verbose` to see which source is slow: `job-radar -v`
4. Consider removing slow sources by not configuring their API keys

### I'm getting "database is locked" errors

This was fixed in v2.1.0. Update to the latest version. Job Radar now uses an `atexit` handler to clean up SQLite rate limiter connections on exit.

If you're on v2.1.0+ and still seeing this:
1. Close all Job Radar instances
2. Delete the app data `rate_limits/` directory
3. Restart Job Radar

### No jobs are showing up in my report

**Possible causes:**
1. **Min score too high** — Lower the threshold: `job-radar --min-score 2.0`
2. **Date range too narrow** — Expand the range: `job-radar --from 2026-02-01`
3. **Dealbreakers too broad** — Review your `dealbreakers` list in the profile
4. **API keys invalid** — Check GUI Settings → API Configuration → Test buttons
5. **No jobs match your profile** — Broaden your `core_skills` or `target_titles`

Use `--dry-run` to preview queries without fetching:
```bash
job-radar --dry-run
```

### How do I enable debug logging?

```bash
job-radar --verbose
# or
job-radar -v
```

Debug logging shows:
- HTTP requests and responses
- Rate limiting decisions
- Scoring breakdowns
- Source-by-source progress

### The GUI won't launch

**macOS:**
1. Remove quarantine attribute from the app path you installed or extracted: `xattr -d com.apple.quarantine /path/to/JobRadar.app`
2. Right-click app → Open (not double-click)
3. Check Console.app for crash logs

**Windows:**
1. Run as Administrator (right-click → Run as administrator)
2. Check antivirus isn't blocking the executable
3. Try the portable ZIP instead of the NSIS installer

**Linux:**
1. Make executable: `chmod +x job-radar-gui`
2. Check dependencies: `ldd job-radar-gui`
3. Run from terminal to see error messages: `./job-radar-gui`

### Jobs are duplicated across sources

Job Radar uses cross-source fuzzy deduplication. It compares title, company, and location, then keeps the richest listing when multiple sources have the same role.

The deduplication algorithm checks:
1. Exact title, company, and location matches
2. Fuzzy title/company/location similarity
3. Listing richness, including salary, description length, structured salary, employment type, apply info, and date posted

If duplicates still appear, the listings likely differ enough in company, title, or location that automatic merging would risk hiding distinct roles.

## Uninstalling

### How do I uninstall Job Radar?

**GUI Method (Recommended):**
1. Launch Job Radar GUI → Settings tab
2. Scroll to Uninstall section
3. Optional: Click "Create Backup" to save profile/config. Reports and tracker data are not included in this ZIP.
4. Check "I understand this will delete all Job Radar data"
5. Click red "Uninstall" button
6. Confirm in the dialog

The GUI uninstaller removes:
- Application files
- Profile, config, reports, tracker data, and backups from app data
- Rate limit databases from app data `rate_limits/`
- Cached data
- Windows: Add/Remove Programs entry
- macOS: App bundle moved to Trash

**Manual Uninstall:** See README.md for platform-specific instructions.

### Will uninstalling delete my job search results?

Yes. The GUI uninstaller removes app data `results/`, including generated reports and tracker data. Create an external backup first if you want to keep profile/config, and manually copy reports you want to retain.

### Can I reinstall Job Radar after uninstalling?

Yes! Download the installer again and run it. You'll start with a fresh setup wizard. If you created a backup before uninstalling, you can restore your old profile from the ZIP file.

## Auto-Update

### How does auto-update work?

Job Radar checks for new versions on startup. When an update is available, you'll see a notification with the changelog preview. You can:
- **Download and install** — Downloads the update with a progress bar, verifies the SHA256 checksum, and launches the installer
- **Skip this version** — Dismisses the update for this specific version (you'll still be notified of future versions)
- **Remind me later** — Dismisses the notification for this session only

### How do I check for updates manually?

The auto-update check runs automatically on startup. If you skipped a version and want to check again, the next launch will check for any newer versions beyond the one you skipped.

### Is the update download safe?

Yes. Every download is verified with a SHA256 checksum before installation. If the checksum doesn't match, the download is rejected and you're notified.

## Advanced Usage

### Can I run Job Radar in a cron job or script?

Yes! Use CLI mode with `--no-wizard` and `--no-open`:

```bash
# Quiet search, don't open browser
job-radar --no-wizard --no-open

# Email the results
job-radar --no-wizard --no-open && mail -s "Daily Job Report" me@example.com < results/job-search-*.html
```

### How do I use a different profile file?

```bash
job-radar --profile /path/to/profile.json
```

Useful for testing different configurations or searching for multiple roles.

### Can I contribute to Job Radar?

Yes! Job Radar is open source. Contributions are welcome:
1. Fork the repository on GitHub
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

See WORKFLOW.md for development setup instructions.

### How do I add a new job source?

1. Add a focused fetcher/mapper module or extend the existing source fetcher/mapper modules.
2. Map response data to the standard `JobResult` dataclass.
3. Add the source metadata to the source registry and query construction.
4. Add rate limit config when the source needs request throttling.
5. Write focused source tests and update documentation.
6. Submit a pull request!

See existing fetchers for examples.

## Support

### Where can I report bugs or request features?

GitHub Issues: https://github.com/BrandedTamarasu-glitch/Job-Radar/issues

Please include:
- Job Radar version (`job-radar --version`)
- Operating system and version
- Steps to reproduce the issue
- Error messages or logs (use `--verbose`)

### Is there a community forum or chat?

Not yet. For now, use GitHub Discussions or Issues for support and feature requests.

### Can I hire you to customize Job Radar for my use case?

Job Radar is an open-source project maintained by volunteers. For commercial customization inquiries, open an issue on GitHub to discuss.
