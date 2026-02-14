# Job Radar — Frequently Asked Questions

**Version 2.1.0** | [Changelog](CHANGELOG.md) | [README](README.md) | [Full Documentation](WORKFLOW.md)

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

- **Windows:** `%USERPROFILE%\.job-radar\`
- **macOS/Linux:** `~/.job-radar/`

This directory contains:
- `profile.json` — Your candidate profile
- `config.json` — Optional persistent defaults
- `.env` — API keys (if configured)
- `backups/` — Automatic profile backups (last 10)

Rate limit databases are stored separately in:
- **Windows:** `%USERPROFILE%\.rate_limits\`
- **macOS/Linux:** `~/.rate_limits/`

### Can I use Job Radar without API keys?

Yes! Job Radar works out-of-the-box with 6 free sources:
- Dice.com (scraper)
- HN Hiring (scraper)
- RemoteOK (public API)
- We Work Remotely (scraper)
- Jobicy (public API, rate limited to 1/hour)
- 4 manual URL builders (Wellfound, Indeed, LinkedIn, Glassdoor)

API keys for Adzuna, Authentic Jobs, JSearch, USAJobs, and SerpAPI expand coverage but are entirely optional.

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

**Automatic:** Job Radar creates timestamped backups before every profile update in `~/.job-radar/backups/` (keeps last 10).

**Manual:**
- GUI Settings tab → Uninstall section → "Create Backup" button (creates ZIP with profile and config)
- Or copy `~/.job-radar/profile.json` manually

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
| Skills match | 30% | Core + secondary skills found in description |
| Seniority alignment | 20% | Level and years of experience match |
| Job type alignment | 15% | Target titles, preferences |
| Salary alignment | 15% | Compensation vs. your floor |
| Response likelihood | 10% | Direct email, company size |
| Description quality | 10% | Structured data, confidence |

After scoring, adjustments are applied:
- **Staffing firm preference** — Boost (+30%), Neutral (0%), or Penalize (-80%)
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

- **Boost (+30%)** — Prefer staffing firms (higher callback rates, more opportunities)
- **Neutral (0%)** — No preference (default for new profiles)
- **Penalize (-80%)** — Avoid staffing firms (prefer direct employers)

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

Job Radar maintains a `results/tracker.json` file that tracks all jobs seen across runs. Jobs appearing for the first time are marked "NEW". Previously seen jobs show as "seen" to help you focus on fresh listings.

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

Click the status dropdown on any job card to mark it as Applied, Interviewing, Rejected, or Offer. Status is saved to:
1. **Browser localStorage** — Persists across sessions in the same browser
2. **results/tracker.json** — Embedded in the tracker file for long-term storage

Status data syncs bidirectionally between localStorage and tracker.json on report load.

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

All reports are saved to `results/` (or your custom `--output` directory) with timestamped filenames:

```
results/
├── job-search-2026-02-14T143522.html
├── job-search-2026-02-14T143522.md
└── tracker.json
```

Open any `.html` file in your browser. Status tracking data is embedded in tracker.json, so statuses persist across all reports.

## Troubleshooting

### The search is taking a very long time

Job Radar queries 10 API sources plus 4 manual URL builders. Some sources (especially scrapers) can be slow. Typical search duration: 30-90 seconds.

**If it takes longer:**
1. Check your internet connection
2. Some sources may be rate-limited or down
3. Use `--verbose` to see which source is slow: `job-radar -v`
4. Consider removing slow sources by not configuring their API keys

### I'm getting "database is locked" errors

This was fixed in v2.1.0. Update to the latest version. Job Radar now uses an `atexit` handler to clean up SQLite rate limiter connections on exit.

If you're on v2.1.0+ and still seeing this:
1. Close all Job Radar instances
2. Delete `~/.rate_limits/*.db`
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
1. Remove quarantine attribute: `xattr -d com.apple.quarantine /Applications/JobRadar.app`
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

Job Radar uses exact-match URL deduplication. If jobs appear from multiple sources (e.g., JSearch vs Direct), it's because they have different URLs even though they're the same posting.

The deduplication algorithm checks:
1. Exact URL match
2. Job ID extraction from URL

Fuzzy matching (e.g., Levenshtein distance) is planned for a future release.

## Uninstalling

### How do I uninstall Job Radar?

**GUI Method (Recommended):**
1. Launch Job Radar GUI → Settings tab
2. Scroll to Uninstall section
3. Optional: Click "Create Backup" to save profile/config
4. Check "I understand this will delete all Job Radar data"
5. Click red "Uninstall" button
6. Confirm in the dialog

The GUI uninstaller removes:
- Application files
- Configuration (`~/.job-radar`)
- Rate limit databases (`~/.rate_limits`)
- Cached data
- Windows: Add/Remove Programs entry
- macOS: App bundle moved to Trash

**Manual Uninstall:** See README.md for platform-specific instructions.

### Will uninstalling delete my job search results?

No. Generated reports in `results/` are NOT deleted by the uninstaller. Only configuration, profile, and app files are removed.

If you want to delete reports too, manually delete the `results/` directory.

### Can I reinstall Job Radar after uninstalling?

Yes! Download the installer again and run it. You'll start with a fresh setup wizard. If you created a backup before uninstalling, you can restore your old profile from the ZIP file.

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

1. Add fetcher function in `job_radar/sources.py` (scraper) or `job_radar/api_sources.py` (API)
2. Map response to standard `JobListing` dict
3. Add to `SOURCES` list in `job_radar/search.py`
4. Add rate limit config in `job_radar/rate_limits.py`
5. Write tests in `tests/test_sources_api.py`
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
