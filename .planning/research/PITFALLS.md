# Pitfalls Research

**Domain:** Auto-Update and hiring.cafe Integration for Python Desktop App
**Researched:** 2026-02-15
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Version Comparison with String Sorting

**What goes wrong:**
Version strings compared lexicographically produce incorrect results. "1.9" sorts after "1.10" in string comparison, causing the app to think 1.9 is newer than 1.10. This breaks update detection entirely. Users on v1.10+ receive prompts to "update" to v1.9, breaking the update mechanism.

**Why it happens:**
Python's default string comparison treats version numbers as text, not semantic versions. Developers reach for simple `if new_version > current_version` without considering that "1.10.0" < "1.9.0" lexicographically. Electron's auto-updater had this exact bug when `allowPrerelease` reverted to lexical sort instead of semantic version sort.

**How to avoid:**
Use the `packaging` module's `Version` class for all version comparisons:
```python
from packaging.version import Version

if Version(remote_version) > Version(current_version):
    # Update available
```

Each version segment is compared numerically: `2.10 > 2.1` and `1.10 > 1.9`. The `packaging` module handles pre-release versions, dev tags, and epoch correctly per PEP 440.

**Warning signs:**
- Tests that check "1.9" vs "1.10" comparisons pass with wrong results
- Users on v1.10+ see update prompts for v1.9
- Update logic uses string operators (`>`, `<`, `==`) directly on version strings

**Phase to address:**
Phase 1 (Version Detection Infrastructure) — implement version comparison correctly from the start, include explicit test cases for 1.9 vs 1.10 comparison.

---

### Pitfall 2: macOS Gatekeeper Quarantine Blocks Downloaded Installers

**What goes wrong:**
Downloaded DMG files receive the `com.apple.quarantine` extended attribute. When the user double-clicks the downloaded installer, macOS Gatekeeper blocks it with "cannot be opened because the developer cannot be verified" unless the app is notarized. Auto-downloaded installers appear broken to users.

**Why it happens:**
Browser downloads automatically tag files with quarantine attributes. Python's `urllib` or `requests` downloads also trigger quarantine. Without Apple notarization, Gatekeeper refuses to open quarantined files even if they're code-signed. The quarantine attribute is inherited by all files within the DMG.

**How to avoid:**
1. **Notarize releases:** Submit DMG to Apple's notarization service during CI/CD. Ad-hoc signing is insufficient for quarantined downloads.
2. **Inform users:** If notarization isn't feasible, provide clear instructions: "Right-click → Open" bypasses Gatekeeper for first launch.
3. **Test quarantine behavior:** Download installer via Python `requests` (not direct file copy) to verify quarantine attribute handling.
4. **Verify notarization:** Use `spctl --assess --verbose JobRadar.app` on clean macOS to ensure Gatekeeper accepts it.

**Warning signs:**
- Installer works when copied locally but fails when downloaded via browser
- `xattr -l installer.dmg` shows `com.apple.quarantine` attribute
- macOS users report "unidentified developer" errors despite valid code signature
- `codesign --verify` passes but app still won't open

**Phase to address:**
Phase 2 (Cross-Platform Download) and Phase 4 (Security & Verification) — notarization must be part of the release pipeline, test quarantine scenarios before shipping.

---

### Pitfall 3: Race Condition During Application Shutdown

**What goes wrong:**
User closes the app while update download is in progress. Download thread continues after main app exits, leaving partial installer files or corrupted downloads. Next launch detects partial installer, tries to run it, and fails. Or: download thread blocks on network I/O, preventing clean shutdown for 30+ seconds.

**Why it happens:**
Non-daemon threads continue running after `sys.exit()` unless explicitly joined. Download operations don't check cancellation flags during long network transfers. Python's `requests` library blocks without timeout, making graceful cancellation difficult. Job Radar already uses cooperative cancellation with `threading.Event` for search workers, but adding auto-update introduces a new thread.

**How to avoid:**
1. **Cooperative cancellation:** Use `threading.Event` to signal download thread to stop. Check flag frequently during download (per-chunk in streaming downloads):
   ```python
   cancel_event = threading.Event()

   response = requests.get(url, stream=True, timeout=30)
   with open(tmp_file, 'wb') as f:
       for chunk in response.iter_content(chunk_size=8192):
           if cancel_event.is_set():
               break
           f.write(chunk)
   ```

2. **Cleanup on exit:** Register `atexit` handler to cancel downloads and delete partial files.

3. **Atomic downloads:** Download to `.tmp` file, rename only on completion. Verify file hash before rename.

4. **Short timeouts:** Use `requests` with `timeout=30` to prevent infinite hangs during cancellation.

**Warning signs:**
- Partial `.dmg`, `.exe`, or `.tar.gz` files in downloads folder after app crash
- App hangs for 30+ seconds on quit when download is active
- Download thread doesn't stop when main window closes
- `.tmp` files accumulate in download directory

**Phase to address:**
Phase 2 (Cross-Platform Download) — build cancellation from the start, add explicit shutdown tests that kill the app mid-download.

---

### Pitfall 4: Update Loop from Bad Manifest or Failed Installs

**What goes wrong:**
App downloads installer, tries to launch it, launch fails (permissions, wrong path, etc.), but update state is marked "installed." Next launch checks version, sees same version, re-downloads installer, infinite loop. Or: manifest on GitHub has malformed JSON, version check fails, app retries immediately, hits GitHub API rate limit (60 req/hour unauthenticated). Users report update notification won't go away.

**Why it happens:**
State tracking doesn't distinguish "downloaded" from "user completed install." Transient failures (network timeout, rate limit) trigger immediate retry without backoff. Manifest parsing exceptions aren't caught, crash the update check, and get retried next launch. Real-world examples show update loops from unsatisfiable dependencies and manifest errors.

**How to avoid:**
1. **State machine:** Track `pending_download`, `downloaded`, `user_dismissed`. Don't re-prompt for same version after dismissal:
   ```python
   update_state = {
       "version": "1.10.0",
       "status": "user_dismissed",  # or "pending", "downloaded"
       "last_check": "2026-02-15T10:00:00Z",
       "retry_after": "2026-02-15T16:00:00Z"  # exponential backoff
   }
   ```

2. **Exponential backoff:** After failed manifest fetch, wait 1 hour → 6 hours → 24 hours before retry.

3. **Manifest validation:** Wrap JSON parsing in try/except, validate schema (version field exists, assets are URLs). Reject malformed manifests without retrying.

4. **Rate limit headers:** Check `X-RateLimit-Remaining` from GitHub API, stop checking when <5 requests remain.

5. **Never retry on 4xx errors:** HTTP 404, 401 are not transient. Log and stop checking.

**Warning signs:**
- Same version downloaded multiple times in logs
- High frequency of GitHub API calls (multiple per minute)
- Users report "update available" notification won't go away
- Manifest fetch returns 403 rate limit error
- Update state file grows with repeated failed attempts

**Phase to address:**
Phase 1 (Version Detection Infrastructure) — implement state machine and backoff immediately. Phase 3 (Update Workflow) — track user dismissal state.

---

### Pitfall 5: Certificate Validation Failures Behind Corporate Proxies

**What goes wrong:**
Enterprise users behind SSL-intercepting proxies get `SSLCertificateError` when downloading updates. Python's `requests` validates against system CA bundle, but proxy uses self-signed cert. Update fails silently or shows cryptic SSL error "certificate verify failed: unable to get local issuer certificate." Users assume app is broken.

**Why it happens:**
Corporate proxies intercept HTTPS, decrypt, inspect, and re-encrypt with their own certificate. Python's default CA bundle doesn't include corporate root certs. Windows uses system cert store, but Python doesn't unless explicitly configured. TLS 1.2 support is required but may not be negotiated correctly through proxy.

**How to avoid:**
1. **Use system certs on Windows:** Set `requests.get(..., verify=True)` — Python 3.10+ automatically uses Windows cert store via `certifi` fallback.

2. **Provide escape hatch:** Add `JOBRADAR_NO_SSL_VERIFY=1` env var to disable validation (document as insecure, last resort).

3. **Informative errors:** Catch `requests.exceptions.SSLError`, show user-friendly message:
   ```python
   try:
       response = requests.get(url, timeout=30)
   except requests.exceptions.SSLError as e:
       show_error("Update check failed: SSL certificate verification failed. "
                  "Are you behind a corporate proxy? "
                  "See docs/proxy-setup.md for workarounds.")
   ```

4. **Test with mitmproxy:** Simulate corporate proxy during testing to catch cert validation issues.

**Warning signs:**
- Update check works on home wifi but fails on corporate network
- `SSLCertificateError: certificate verify failed` in logs
- Windows users report failures, macOS users don't (Windows cert store integration missing)
- Error message shows "unable to get local issuer certificate"

**Phase to address:**
Phase 2 (Cross-Platform Download) — handle SSL errors gracefully from the start, test with proxy simulator.

---

### Pitfall 6: Installer Launch Permissions on Windows (UAC Elevation)

**What goes wrong:**
Downloaded `.exe` installer requires admin privileges (NSIS installs to Program Files). App launches installer via `subprocess.run(['installer.exe'])`, but UAC blocks it or shows "access denied." Silent installs (`/S` flag) write to wrong registry hive (HKCU instead of HKLM) when not elevated, breaking uninstaller lookup.

**Why it happens:**
NSIS installers for "all users" require UAC elevation. Python `subprocess` doesn't auto-elevate on Windows. `ShellExecute` with `runas` verb is needed, but not available in `subprocess` module. User runs Job Radar as non-admin, so child process inherits non-admin token. When elevated, `HKCU` points to administrator's registry, not the original user's.

**How to avoid:**
1. **Use `os.startfile()` instead of `subprocess`:** On Windows, `os.startfile('installer.exe')` triggers UAC prompt automatically if installer has `requestedExecutionLevel` manifest:
   ```python
   if sys.platform == "win32":
       os.startfile(str(installer_path))
   elif sys.platform == "darwin":
       subprocess.run(["open", str(installer_path)])
   else:  # Linux
       subprocess.run(["xdg-open", str(installer_path)])
   ```

2. **Don't auto-install:** Let user click through installer wizard. Silent installs (`/S`) are fragile with UAC — registry goes to wrong hive, shortcuts break.

3. **Verify installer manifest:** NSIS script must include `RequestExecutionLevel admin` to trigger UAC.

4. **Test as non-admin user:** Run Job Radar from non-admin account, verify UAC prompt appears when clicking "Install Update."

**Warning signs:**
- Installer launches but fails with "access denied" or silent errors
- Uninstaller can't find installation (written to HKCU, expected in HKLM)
- Windows users report "nothing happens" when clicking install button
- Installer runs but doesn't appear in Add/Remove Programs

**Phase to address:**
Phase 3 (Update Workflow) — implement correct installer launch method per platform, test as non-admin user.

---

### Pitfall 7: hiring.cafe Unofficial API Brittleness (HTML Structure Changes)

**What goes wrong:**
If hiring.cafe provides an unofficial API or requires scraping, HTML structure changes break parsing. Job title selector `.job-title` renamed to `.listing-title`, scraper returns empty results. No jobs from hiring.cafe, no error message, user assumes source is down. Or: unofficial API changes response schema, adding fields or renaming keys.

**Why it happens:**
Unofficial APIs and web scraping are inherently fragile. Sites change markup without notice. CSS class names, div nesting, and JSON response schemas evolve. No SLA or versioning like official APIs. hiring.cafe is an aggregator that scales to 1M+ users, so they iterate on frontend frequently.

**How to avoid:**
1. **Graceful degradation:** If hiring.cafe returns 0 jobs, log warning but don't crash. Show message in GUI: "hiring.cafe returned no results (site may have changed)."

2. **Validate structure:** After fetching, check if expected fields exist before parsing. Fail fast with clear error if structure changed:
   ```python
   def parse_hiring_cafe_job(job_data):
       required_fields = ["title", "company", "url"]
       missing = [f for f in required_fields if f not in job_data]
       if missing:
           logger.error(f"hiring.cafe schema changed: missing {missing}")
           return None
       # Continue parsing...
   ```

3. **Monitor for breakage:** Log success rate per source. Alert if hiring.cafe success rate drops from 90% to 0% (indicates site change).

4. **Fallback selectors:** Try multiple selectors: `[class*="title"]` as fallback if `.job-title` missing. Brittle, but buys time.

5. **Version scraper logic:** Treat scraper as versioned code, include `hiring_cafe_scraper_v1.py`. When site changes, ship `v2` quickly.

**Warning signs:**
- hiring.cafe returns 0 jobs across multiple searches
- Logs show HTTP 200 but parsing fails
- HTML response structure doesn't match expected schema
- Users report "hiring.cafe never works"
- Sudden 100% failure rate for source

**Phase to address:**
Phase 5 (hiring.cafe Integration) — build validation and fallback logic upfront, add monitoring/alerting for parsing success rate.

---

### Pitfall 8: Inconsistent or Missing Salary Data from hiring.cafe

**What goes wrong:**
Job listings have salary in different formats: "$100k-$120k", "$100000 - $120000", "100-120k", "Competitive", or missing entirely. Parser extracts wrong values, displays "$100 - $120" instead of "$100k - $120k". Or salary field is `null` for 60% of jobs, breaking HTML report rendering if template assumes salary exists.

**Why it happens:**
hiring.cafe aggregates from multiple sources with inconsistent compensation formats. Manual job posts use freeform text. Some employers never disclose salary. No standardized schema for salary representation across the job ecosystem. Survey data shows equity, benefits, and compensation bands are inconsistently reported.

**How to avoid:**
1. **Normalize during parsing:** Regex patterns for `$100k`, `$100000`, `100-120k`. Convert to standard format `$X - $Y` or `null`:
   ```python
   import re

   def parse_salary(salary_text):
       if not salary_text or salary_text.lower() in ["competitive", "not specified"]:
           return None

       # Match patterns like "100k-120k", "$100,000 - $120,000"
       pattern = r'(\d+)(?:,(\d+))?k?'
       matches = re.findall(pattern, salary_text, re.IGNORECASE)
       if len(matches) >= 2:
           min_sal = int(matches[0][0]) * (1000 if 'k' in salary_text else 1)
           max_sal = int(matches[1][0]) * (1000 if 'k' in salary_text else 1)
           return f"${min_sal:,} - ${max_sal:,}"
       return None
   ```

2. **Handle missing data:** Make salary field optional in job schema. Display "Not specified" in HTML report if `null`.

3. **Don't break scoring:** If salary is a scoring factor, treat missing salary as neutral (0 points), not penalty. Don't crash if salary parse fails.

4. **Log unparseable formats:** Collect examples of salary text that doesn't match regex. Iterate on patterns over time.

5. **Test with real data:** Scrape 100 hiring.cafe jobs during development, verify salary parsing coverage before shipping.

**Warning signs:**
- Salary displayed as "$1" or "$100" (off by 1000x)
- HTML report rendering fails when salary is `null`
- 80%+ of hiring.cafe jobs show "Not specified" (parser is too strict or field doesn't exist)
- Salary ranges are backwards: "$120k - $100k"

**Phase to address:**
Phase 5 (hiring.cafe Integration) — implement flexible salary parsing with fallback, test against real scraped data before merging.

---

### Pitfall 9: Location Parsing Edge Cases (Remote/Hybrid/Multiple Locations)

**What goes wrong:**
Job location is "Remote (US)", "San Francisco or New York", "Hybrid - Seattle", or "Multiple Locations". Parser expects "City, State" format, fails to extract, stores `null` or first word ("Remote"). User filters for "Seattle" but hybrid Seattle jobs are missing because location is "Hybrid". Deduplication fails because same job has different location formats across sources.

**Why it happens:**
No standardized location schema across job boards. Remote work explosion introduced "Remote", "Remote (US)", "Remote - EST timezone" formats. Hybrid means "sometimes in office" but location field still needed. Multiple-office companies list all locations in one field. JobSpy library handles this with structured fields (`is_remote`, `country`, `city`).

**How to avoid:**
1. **Regex patterns for common formats:**
   ```python
   def parse_location(location_text):
       if not location_text:
           return {"cities": [], "remote": False, "hybrid": False, "raw": None}

       remote = bool(re.search(r'\bremote\b', location_text, re.I))
       hybrid = bool(re.search(r'\bhybrid\b', location_text, re.I))

       # Extract cities
       city_pattern = r'(?:Hybrid\s*-\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
       cities = re.findall(city_pattern, location_text)

       # Handle "City1 or City2"
       if ' or ' in location_text:
           cities = re.split(r'\s+or\s+', location_text.replace('Hybrid - ', ''))

       return {
           "cities": [c.strip() for c in cities],
           "remote": remote,
           "hybrid": hybrid,
           "raw": location_text
       }
   ```

2. **Store structured location:** JSON field: `{"cities": ["Seattle"], "remote": false, "hybrid": true}` instead of string.

3. **Fuzzy search:** User filters for "Seattle", match jobs with Seattle in `cities` array regardless of hybrid/remote flags.

4. **Fall back to raw text:** If parsing fails, store original location string. Better to show "Remote (US)" than `null`.

5. **Test against real data:** Scrape 100 jobs, catalog unique location formats, write tests for each.

**Warning signs:**
- Location field is `null` or "Remote" for most jobs
- User filters for city, gets 0 results despite jobs existing
- Location displayed as "Hybrid" with no city info
- Deduplication fails because same job has different location formats across sources

**Phase to address:**
Phase 5 (hiring.cafe Integration) — implement structured location parsing with fallback, test against diverse real-world location formats.

---

### Pitfall 10: Deduplication Failures Across hiring.cafe and Existing Sources

**What goes wrong:**
Same job appears in hiring.cafe and JSearch (both aggregators). Fuzzy dedup uses 85% title+company similarity, but hiring.cafe formats title as "Senior Engineer - Company" while JSearch uses "Senior Engineer at Company". Similarity is 82%, dedup fails, duplicate jobs in report. User marks job as "Applied" but sees it again as "New" from different source.

**Why it happens:**
Different sources format job titles inconsistently. Aggregators like JSearch and hiring.cafe may pull from same upstream source (LinkedIn) but transform data differently. Existing 85% threshold in Job Radar was tuned for current sources, may not work for hiring.cafe. Common pattern: same job appears on dozens of different sites.

**How to avoid:**
1. **Normalize before comparison:** Strip " - Company", " at Company", " | Company" suffixes before fuzzy matching. Compare just title:
   ```python
   def normalize_title(title, company):
       # Remove company name from title
       title = re.sub(rf'\s*[-|@]\s*{re.escape(company)}', '', title, flags=re.I)
       # Normalize whitespace
       title = ' '.join(title.split())
       return title.lower()
   ```

2. **Multi-field dedup:** Use title + company + location as dedup key. Two "Senior Engineer" jobs at different companies are not duplicates.

3. **URL-based dedup:** If hiring.cafe provides `apply_url`, check if URL matches existing job. Many aggregators preserve original URL:
   ```python
   # Exact URL match = definitely duplicate
   if new_job["url"] == existing_job["url"]:
       return True
   ```

4. **Tune threshold per source:** Lower threshold to 80% for hiring.cafe if it's consistently formatted differently.

5. **Log near-duplicates:** Record pairs with 80-84% similarity to analyze missed dedup cases. Iterate on normalization.

**Warning signs:**
- Same job appears twice in report with different sources
- User marks job as "Applied" but sees it again as "New" (different source)
- Dedup logs show many 82-84% matches (just under threshold)
- hiring.cafe jobs never deduplicate with other sources

**Phase to address:**
Phase 5 (hiring.cafe Integration) — test dedup against real hiring.cafe + existing sources, log near-misses, tune threshold and normalization.

---

### Pitfall 11: hiring.cafe Rate Limiting Without Backoff

**What goes wrong:**
Unofficial API or scraping has strict rate limits (1 req/sec). App fetches all job pages rapidly, gets IP banned or 429 errors. Next search fails silently because rate limiter assumes "no rate limit = unlimited." Or: no respect for `robots.txt`, violates site's terms of service.

**Why it happens:**
hiring.cafe scales to 1M+ users, so aggressive anti-scraping measures are likely. Unofficial tools need to be "respectful of servers" per scraper documentation. Job Radar has SQLite-backed rate limiting, but adding hiring.cafe means new rate limit configuration.

**How to avoid:**
1. **Conservative rate limits:** Start with 1 request per 2 seconds, monitor for 429 errors:
   ```python
   RATE_LIMITS = {
       "hiring_cafe": (30, 60),  # 30 requests per 60 seconds
   }
   ```

2. **Exponential backoff on 429:** If rate limited, wait 60s → 120s → 240s before retry.

3. **Respect robots.txt:** Check `https://hiring.cafe/robots.txt` before scraping, honor crawl delays.

4. **User-agent header:** Identify as Job Radar with contact: `Job-Radar/2.2.0 (+https://github.com/user/job-radar)`.

5. **Monitor for bans:** If hiring.cafe returns 403 errors consistently, log warning and disable source for 24 hours.

**Warning signs:**
- hiring.cafe returns 429 or 403 errors
- All hiring.cafe requests fail after first few succeed
- IP-based blocking (works on one network, fails on another)
- `robots.txt` disallows the user-agent or path

**Phase to address:**
Phase 5 (hiring.cafe Integration) — implement rate limiting from the start, test with realistic usage patterns.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip signature verification for GitHub releases | Faster to implement, works for official releases | Vulnerable to MITM attacks, compromised GitHub account could distribute malware | Never — signature verification is security-critical |
| Use simple string comparison for versions | 1 line of code, no dependencies | Breaks when version reaches 1.10+, requires rewrite | Never — `packaging` module is stdlib |
| Download installers to user-writable temp dir | Avoids permission issues | Race condition risk (other process modifies file), harder to debug failed downloads | Only if atomic rename used and temp file is random |
| Retry failed manifest fetch immediately | User sees update faster if transient error | GitHub API rate limit, battery drain from polling | Only with exponential backoff (1 retry max) |
| Store update state in memory only | No file I/O, simpler code | User dismisses update, sees prompt again next launch | Only for MVP — persist to disk by v1.0 |
| Hardcode hiring.cafe selectors in main code | Faster to ship | Site change breaks production, requires hotfix release | Only if selector patterns are abstracted to config dict |
| Ignore missing salary data (don't display field) | Avoids "Not specified" clutter | Users can't filter by "has salary", data loss | Only if salary is truly rare (<10% of jobs have it) |
| Store location as plain text string | Simple schema, easy to search | Can't filter by remote/hybrid, city extraction fails | Never — structured location needed for filtering |
| Skip notarization for macOS DMG | Saves time in CI/CD (10 min wait) | Users get Gatekeeper warnings, app appears "damaged" | Only for internal testing builds, never releases |
| Silent install with NSIS `/S` flag | No user interaction, faster | UAC issues, registry in wrong hive, hard to debug | Never — let user click through installer |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GitHub Releases API | Poll every app launch, hit rate limit (60/hour) | Cache version check result for 6+ hours, check `X-RateLimit-Remaining` header |
| GitHub Releases API | Use unauthenticated requests (60/hour limit) | Provide optional `GITHUB_TOKEN` env var for 5000/hour limit (power users) |
| hiring.cafe scraping | Assume HTML structure is stable | Validate structure on every fetch, fail gracefully if changed |
| hiring.cafe scraping | No rate limiting because it's unofficial | Respect `robots.txt`, add delays (1 req/2sec), or risk IP ban |
| HTTPS downloads | Trust all certificates if SSL error occurs | Catch `SSLError`, log helpful message, fail secure (don't disable verification) |
| Installer downloads | Assume content-type header is accurate | Verify downloaded file is valid (DMG magic bytes, EXE MZ header) before saving |
| Cross-platform installers | Launch installer with `subprocess.run()` on all platforms | Use `os.startfile()` on Windows (triggers UAC), `open` command on macOS |
| macOS DMG installers | Code sign with ad-hoc signature (`-`) | Notarize with Apple or users get Gatekeeper warnings on downloaded DMGs |
| Windows NSIS installers | Silent install with `/S` flag for auto-update | Let user click through wizard — silent install UAC issues are complex |
| Salary parsing | Regex assumes `$100,000` format | Handle `100k`, `$100-120k`, `Competitive`, and `null` gracefully |
| Version manifest | Parse JSON without error handling | Wrap in try/except, validate schema, log parse failures |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Download full installer into memory | Works for 50MB DMG | High RAM usage, OOM crash | 200MB+ Windows installer |
| Check for updates on every search | Fast with 6h cache | Slow app start if GitHub API is slow | API latency >2 seconds |
| Parse all hiring.cafe jobs in main thread | Responsive for 10 jobs | GUI freezes during parse | 500+ jobs in single fetch |
| Store all update state in JSON file | Simple, works fine | Corrupted JSON loses all state | User manually edits file |
| Retry manifest fetch on every error | Recovers from transient network blips | Battery drain, API rate limit | Network is flaky (mobile hotspot) |
| Download installer to user's `Downloads/` folder | Easy to find for user | Folder full of old installers | User never cleans up |
| Load entire DMG to verify checksum | Simple hashlib API | Slow on large files, high I/O | 500MB+ installer |
| No backoff for hiring.cafe rate limit | Works at low volume | IP ban after 1000 requests | Daily heavy use |
| Synchronous download in GUI thread | Simple implementation | GUI freezes during 200MB download | Large installers, slow connections |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Skip HTTPS for update manifest | MITM attacker serves malicious version | Always use `https://` for GitHub releases, reject HTTP redirects |
| Trust installer without signature check | Malware distributed as fake update | Verify code signature on macOS (codesign -v), Authenticode on Windows |
| Download installer to predictable path | Local privilege escalation (attacker swaps file) | Use `tempfile.mkdtemp()` for random download dir, verify hash before launch |
| No timeout on installer download | Slowloris attack causes infinite hang | Set `timeout=60` on all requests, show progress bar to user |
| Accept any certificate if system cert fails | MITM in corporate environment | Fail secure — show error message, don't disable verification |
| Run installer automatically after download | User doesn't consent, malicious installer runs | Always require user click "Install Now" button |
| Store GitHub token in code for higher rate limit | Token leaks in version control | Only accept token via env var, never commit |
| Disable Windows UAC for installer | Installs malware without user knowledge | Embrace UAC — use `os.startfile()` to trigger prompt |
| Parse hiring.cafe HTML with `eval()` or `exec()` | Code injection if site is compromised | Use BeautifulSoup or JSON parsing only, never dynamic code execution |
| Display raw job URLs without validation | Open redirect, XSS in HTML report | Validate URLs start with `http://` or `https://`, sanitize for HTML |
| Skip hash verification for downloaded installer | Corrupted or malicious installer runs | Verify SHA256 hash from release manifest before launching |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Show "Update available" on every launch | Notification fatigue, user ignores it | Show once per version, persist dismissal state |
| No progress indicator during download | User thinks app is frozen, force-quits | Show progress bar with MB downloaded / total MB |
| Auto-download 200MB installer on metered connection | User's mobile hotspot data is exhausted | Prompt "Download 200MB update?" with Yes/No |
| Show cryptic error "SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]" | User has no idea what to do | "Update check failed. Are you behind a corporate proxy? See help.md" |
| No way to skip version | User on stable v1.5 sees v1.6 beta prompt forever | "Remind me later" and "Skip this version" buttons |
| Installer download fails silently | User clicks "Install", nothing happens, no error | Show error dialog: "Download failed: network timeout. Retry?" |
| Update check blocks GUI thread | App unresponsive for 5 seconds on launch | Run version check in background thread, show notification when done |
| Downloaded installer auto-deletes after install | User wants to share installer with colleague, it's gone | Keep installer in `~/Downloads` or prompt "Delete installer?" |
| No indication of what's new in update | User doesn't know if update is worth installing | Fetch release notes from GitHub, show in update dialog |
| hiring.cafe jobs have no source attribution | User can't tell which jobs are from hiring.cafe | Show source badge: "via hiring.cafe" in job listing |
| Salary "Not specified" shown for all hiring.cafe jobs | User thinks hiring.cafe is useless | Only show salary field if >30% of jobs have data, otherwise hide column |
| Location shows "Hybrid" with no city | User has no idea where job is located | Always show raw location text if structured parsing fails |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Auto-update:** Version comparison works — verify with test case for "1.9" vs "1.10" comparison
- [ ] **Auto-update:** Installer downloads — verify downloaded file has correct magic bytes (MZ header for EXE, EDFE for Mach-O)
- [ ] **Auto-update:** Works on corporate network — verify with mitmproxy simulating SSL-intercepting proxy
- [ ] **Auto-update:** UAC prompt appears on Windows — verify by testing as non-admin user
- [ ] **Auto-update:** Gatekeeper allows DMG on macOS — verify by downloading via browser (quarantine attribute set)
- [ ] **Auto-update:** No update loop — verify app doesn't re-download after user dismisses
- [ ] **Auto-update:** Graceful shutdown during download — verify app quits cleanly if user closes mid-download
- [ ] **Auto-update:** Rate limit handling — verify app doesn't hit GitHub API >60 times/hour
- [ ] **Auto-update:** Downloaded installer is executable — verify on clean VM, not just dev machine
- [ ] **Auto-update:** Hash verification before launch — verify corrupted download is rejected
- [ ] **hiring.cafe:** HTML parsing resilient — verify with mock HTML response that has structure changes
- [ ] **hiring.cafe:** Salary parsing handles missing data — verify `null` salary doesn't crash report rendering
- [ ] **hiring.cafe:** Location parsing handles remote/hybrid — verify "Remote (US)" and "Hybrid - Seattle" extract correctly
- [ ] **hiring.cafe:** Deduplication works across sources — verify same job from hiring.cafe + JSearch is deduplicated
- [ ] **hiring.cafe:** Rate limiting respects site — verify no more than 1 request/2 seconds to hiring.cafe
- [ ] **hiring.cafe:** Graceful degradation — verify app doesn't crash if hiring.cafe returns 0 jobs
- [ ] **hiring.cafe:** Source attribution — verify jobs show "via hiring.cafe" badge in report

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Update loop from bad state | LOW | Delete persistent state file (`~/.job-radar/update_state.json`), restart app, re-check for updates |
| Corrupted installer download | LOW | Delete partial file, retry download with checksum verification |
| Version comparison bug shipped | MEDIUM | Hotfix release with correct comparison, bump to 1.10.1, notify users manually |
| Gatekeeper blocks DMG | MEDIUM | Document workaround (right-click → Open), submit to notarization, re-release |
| GitHub API rate limit hit | LOW | Wait 1 hour for limit reset, cache version check result for 24h in next release |
| hiring.cafe HTML structure changed | HIGH | Update scraper selectors, test against new HTML, release patch quickly (same day) |
| Salary parsing breaks reports | MEDIUM | Make salary field optional in next patch, display "Not specified" for unparsed values |
| Location parsing fails | MEDIUM | Fall back to raw location string, ship fix with updated regex patterns |
| Deduplication fails | LOW | Adjust threshold or normalization in config, re-run search to regenerate report |
| UAC elevation fails on Windows | MEDIUM | Document manual install process, switch from `subprocess` to `os.startfile()` in next release |
| Certificate validation fails for corporate users | LOW | Document `JOBRADAR_NO_SSL_VERIFY=1` workaround, investigate system cert store integration |
| hiring.cafe IP ban | HIGH | Wait 24 hours, reduce rate limits, add exponential backoff, contact site admin if persistent |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Version string comparison | Phase 1: Version Detection Infrastructure | Test case: assert Version("1.10") > Version("1.9") |
| macOS Gatekeeper quarantine | Phase 2: Cross-Platform Download + Phase 4: Security | Download via `requests` on macOS, verify quarantine attribute, launch DMG |
| Race condition on shutdown | Phase 2: Cross-Platform Download | Kill app mid-download, verify no partial files, next launch works |
| Update loop from bad state | Phase 1: Version Detection + Phase 3: Update Workflow | Dismiss update, restart app, verify no re-prompt for same version |
| Certificate validation failures | Phase 2: Cross-Platform Download | Test with mitmproxy, verify helpful error message shown |
| UAC elevation on Windows | Phase 3: Update Workflow | Test as non-admin user, verify UAC prompt appears, installer runs |
| hiring.cafe HTML brittleness | Phase 5: hiring.cafe Integration | Change mock HTML structure, verify graceful failure + helpful log |
| Inconsistent salary data | Phase 5: hiring.cafe Integration | Test with null/unparseable salary, verify report renders |
| Location parsing edge cases | Phase 5: hiring.cafe Integration | Test with "Remote (US)", "Hybrid - Seattle", verify extraction |
| Deduplication failures | Phase 5: hiring.cafe Integration | Same job from hiring.cafe + JSearch, verify only one in report |
| hiring.cafe rate limiting | Phase 5: hiring.cafe Integration | Make 100 requests, verify backoff on 429, no IP ban |

## Sources

**Auto-Update Research:**
- [Automatic updates for desktop apps - ToDesktop](https://www.todesktop.com/features/auto-updates)
- [Auto Update Desktop Applications - Harshith Gowda (Medium)](https://medium.com/whatfix-techblog/auto-update-desktop-applications-db8fd4cf4936)
- [Version comparison issues in electron-updater - GitHub Issue #1488](https://github.com/electron-userland/electron-builder/issues/1488)
- [AutoUpdater doesn't follow semantic version ordering - GitHub Issue #1625](https://github.com/electron-userland/electron-builder/issues/1625)
- [Semantic versioning in Python - PEP 440](https://peps.python.org/pep-0440/)
- [Python semantic version comparison - semver docs](https://python-semver.readthedocs.io/en/latest/usage/compare-versions.html)
- [Signature validation bypass in Electron-Updater - Doyensec](https://blog.doyensec.com/2020/02/24/electron-updater-update-signature-bypass.html)
- [Notepad++ 8.8.9 auto-update vulnerability patch - CyberSecureFox](https://cybersecurefox.com/en/notepad-plus-plus-auto-update-vulnerability-8-8-9/)
- [Secure, Proven Auto-Updates for Windows Applications - Advanced Installer](https://www.advancedinstaller.com/user-guide/secure-proven-auto-updates.html)
- [macOS Gatekeeper quarantine - Apple Support](https://support.apple.com/guide/security/gatekeeper-and-runtime-protection-sec5599b66df/web)
- [macOS Gatekeeper Bypass - Cedric Owens (Medium)](https://cedowens.medium.com/macos-gatekeeper-bypass-2021-edition-5256a2955508)
- [Windows NSIS UAC elevation - NSIS UAC plug-in](https://nsis.sourceforge.io/UAC_plug-in)
- [NSIS all users installation auto-update - GitHub Issue #2363](https://github.com/electron-userland/electron-builder/issues/2363)
- [GitHub API rate limits - GitHub Docs](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [Tips for avoiding GitHub API rate limit - GitHub Discussion #77255](https://github.com/orgs/community/discussions/77255)
- [PyUpdater - PyInstaller auto-update library - GitHub](https://github.com/Digital-Sapphire/PyUpdater)
- [Updater4Pyi documentation - ReadTheDocs](https://updater4pyi.readthedocs.io/en/latest/quickstart/)
- [SSL certificate verification with proxies - Microsoft Docs](https://learn.microsoft.com/en-us/azure/active-directory/app-proxy/application-proxy-connector-installation-problem)
- [Certificate Verification Error with proxy - GitHub Issue #1608](https://github.com/mitmproxy/mitmproxy/issues/1608)
- [Threading shutdown race conditions - Victor Stinner](https://vstinner.github.io/threading-shutdown-race-condition.html)
- [Infinite update loops - Munki Issue #346](https://github.com/munki/munki/issues/346)
- [Update loop - Visual Studio Issue #434144](https://developercommunity.visualstudio.com/content/problem/434144/update-loop.html)

**hiring.cafe Research:**
- [hiring.cafe job scraper - GitHub](https://github.com/umur957/hiring-cafe-job-scraper)
- [Scaling HiringCafe from 0 to 1M+ users - Ali Mir](https://blog.hiring.cafe/p/scaling-hiringcafe-from-0-to-1m-users)
- [JobSpy library for job scraping - GitHub](https://github.com/speedyapply/JobSpy)
- [Job board scraping guide - ScrapingBee](https://www.scrapingbee.com/blog/build-job-board-web-scraping/)
- [How to Scrape Job Postings in 2025 - Oxylabs](https://oxylabs.io/blog/web-scraping-job-postings)
- [Web scraping rate limit bypass - Scrape.do](https://scrape.do/blog/web-scraping-rate-limit/)
- [Rate Limit in Web Scraping - Scrape.do](https://scrape.do/blog/web-scraping-rate-limit/)
- [API Rate Limiting 2026 - Levo.ai](https://www.levo.ai/resources/blogs/api-rate-limiting-guide-2026)
- [Salary survey data unreliability - Ravio](https://ravio.com/blog/why-salary-surveys-are-an-unreliable-source-for-competitive-pay)
- [13 best free salary data sources in 2026 - Ravio](https://ravio.com/blog/free-salary-data)
- [Job scraping deduplication techniques - Octoparse](https://www.octoparse.com/blog/web-scraping-job-postings)

**Confidence Assessment:**
- **Auto-update pitfalls:** MEDIUM confidence — based on documented Electron/desktop app issues, Python-specific details extrapolated from web search + PyUpdater docs
- **hiring.cafe pitfalls:** MEDIUM-LOW confidence — limited information about unofficial API, extrapolated from general job scraping challenges and similar aggregators
- **Security pitfalls:** HIGH confidence — well-documented in Gatekeeper, UAC, SSL, and signature verification literature
- **Integration pitfalls:** MEDIUM confidence — based on GitHub API docs and common scraping anti-patterns

---
*Pitfalls research for: Job Radar v2.2.0 (Auto-Update & hiring.cafe Integration)*
*Researched: 2026-02-15*
