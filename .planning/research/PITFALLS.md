# Pitfalls Research

**Domain:** Adding job aggregator APIs, configurable scoring, GUI uninstall, and platform-native installers to existing Python desktop app
**Researched:** 2026-02-13
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Scoring Weight Migration Without Schema Version Bump

**What goes wrong:**
Users who upgrade from v2.0 to v2.1 suddenly see all their job results re-scored with different weights. Old reports become incomparable to new ones. Worse, if a user configured custom weights but the schema didn't increment, old profiles lack the new weights structure, causing KeyError crashes when scoring.py expects `profile["scoring_weights"]["skill_match"]` but finds only hardcoded floats.

**Why it happens:**
Developers think "it's just adding optional fields" and don't bump `CURRENT_SCHEMA_VERSION` from 1 to 2. The existing auto-migration code (profile_manager.py:267-271) only handles v0→v1. Adding configurable weights is a **breaking schema change** because scoring.py changes from reading hardcoded values (0.25, 0.15, etc.) to reading `profile.get("scoring_weights", {}).get("skill_match", 0.25)`. Without migration, old profiles missing this structure break.

**How to avoid:**
1. Bump `CURRENT_SCHEMA_VERSION = 2` in profile_manager.py
2. Add v1→v2 migration in `load_profile()`:
   ```python
   if schema_version == 1:
       # Add default scoring weights if missing
       profile.setdefault("scoring_weights", {
           "skill_match": 0.25,
           "title_relevance": 0.15,
           "seniority": 0.15,
           "location": 0.15,
           "domain": 0.10,
           "response_likelihood": 0.20,
       })
       profile["schema_version"] = 2
       save_profile(profile, profile_path)  # Auto-migrate and save
   ```
3. Update _template.json to include `scoring_weights` for new users
4. Add test: `test_load_v1_profile_auto_migrates_to_v2()` mirroring test_profile_manager.py:226

**Warning signs:**
- Tests pass but GUI crashes on "Search" with `KeyError: 'scoring_weights'`
- Old profiles load fine but scoring.py fails with AttributeError
- Reports generated before/after upgrade show different scores for identical jobs

**Phase to address:**
Phase 1 (Configurable Scoring Architecture) — migration MUST ship atomically with the feature

---

### Pitfall 2: Rate Limiter State Corruption Across New API Sources

**What goes wrong:**
Adding 4 new job aggregator APIs means 4 new SQLite databases in `.rate_limits/`. If two sources share an API backend (e.g., "JobAPI" and "JobAPI Premium" both hit `api.jobapi.com`), they create separate rate limit databases (`jobapi.db` and `jobapi_premium.db`) but hit the same rate limit pool. User burns through quota twice as fast, gets 429s, and both sources fail silently because `check_rate_limit()` returns False but doesn't explain WHY.

Worse: SQLite connections in `_connections` dict (rate_limits.py:39) aren't closed on exit. Adding 4 sources means 10 total SQLite connections staying open. On Windows, this causes "database is locked" errors if user tries to manually inspect `.rate_limits/*.db` while app runs.

**Why it happens:**
Current rate_limits.py was designed for 2 API sources (Adzuna, Authentic Jobs). Scaling to 6+ sources surfaces architectural flaws:
- No connection pooling or cleanup
- No shared rate limiter for sources using same backend API
- `RATE_LIMITS` dict (rate_limits.py:27) hardcodes source names, making dynamic aggregator addition brittle

**How to avoid:**
1. **Connection cleanup**: Add `atexit` handler to close all SQLite connections:
   ```python
   import atexit

   def _cleanup_connections():
       for conn in _connections.values():
           conn.close()

   atexit.register(_cleanup_connections)
   ```
2. **Shared rate limiters**: Map sources to API backends in api_config.py:
   ```python
   API_BACKEND_MAP = {
       "jobapi": ["jobapi", "jobapi_premium"],  # Share rate limiter
       "careerjet": ["careerjet"],
   }
   ```
   Modify `get_rate_limiter(source)` to use backend key instead of source name
3. **Dynamic rate limit configs**: Move `RATE_LIMITS` to .env or config.json so new sources don't require code changes
4. **Better error messages**: When rate limited, log the backend API and ALL sources affected

**Warning signs:**
- `.rate_limits/` directory grows to 10+ databases
- "Database is locked" errors in logs
- User reports "some APIs randomly stop working"
- 429 errors appearing despite conservative rate limits

**Phase to address:**
Phase 2 (API Source Infrastructure) — BEFORE adding actual API integrations in Phase 3

---

### Pitfall 3: macOS Code Signing Breaks PyInstaller Executables

**What goes wrong:**
Adding DMG installer requires code signing for Gatekeeper. Developers sign `JobRadar.app` with `codesign --deep -s "Developer ID" JobRadar.app`, but macOS refuses to open it: "JobRadar is damaged and can't be opened." Running `codesign --verify --verbose JobRadar.app` shows "bundle format unrecognized."

Root cause: PyInstaller appends Python bytecode to the end of the executable, breaking Mach-O format. The `--deep` flag signs all binaries in one pass, but LINKEDIT segment must be last. PyInstaller expects a magic number at EOF. Signing breaks this.

On Windows, NSIS installer built with default settings triggers Windows Defender SmartScreen: "Windows protected your PC" because .exe isn't signed. Signing requires $400/year code signing certificate + hardware token.

**Why it happens:**
Current job-radar.spec sets `codesign_identity=None` and `entitlements_file='entitlements.plist'` (line 108) but doesn't actually sign. Adding DMG/MSI installers exposes this gap. Per PyInstaller docs and GitHub issues (#7937, #2198), signing PyInstaller apps requires:
- Sign each binary separately, inside-out (dependencies first, main executable last)
- Use BUNDLE build type, not COLLECT (job-radar.spec uses BUNDLE for macOS already, good)
- Apply hardened runtime entitlements
- Notarize with `notarytool` (not deprecated `altool`)

**How to avoid:**
1. **macOS signing script** (post-build step in CI):
   ```bash
   # Sign all .dylib and .so files first
   find dist/JobRadar.app -name "*.dylib" -o -name "*.so" | xargs -I {} codesign -s "Developer ID" --options runtime --entitlements entitlements.plist {}

   # Sign main executables
   codesign -s "Developer ID" --options runtime --entitlements entitlements.plist dist/JobRadar.app/Contents/MacOS/job-radar-cli
   codesign -s "Developer ID" --options runtime --entitlements entitlements.plist dist/JobRadar.app/Contents/MacOS/job-radar

   # Sign app bundle (not --deep!)
   codesign -s "Developer ID" --options runtime --entitlements entitlements.plist dist/JobRadar.app

   # Verify
   codesign --verify --verbose dist/JobRadar.app
   ```
2. **Notarization**: Submit to Apple for scanning:
   ```bash
   xcrun notarytool submit job-radar.dmg --keychain-profile "notarization" --wait
   xcrun stapler staple dist/JobRadar.app
   ```
3. **Windows**: Document that unsigned installer shows SmartScreen warning. Add "How to bypass" instructions for users. Enterprise signing ($400/year) deferred to future milestone.
4. **Test on CLEAN machine**: CI builds succeed but real users have Gatekeeper. GitHub Actions can't test this fully.

**Warning signs:**
- "codesign --verify" fails with "bundle format unrecognized"
- Users report "App is damaged" on macOS 10.15+
- Windows installer triggers SmartScreen on every download
- Entitlements file exists but isn't applied (`codesign -d --entitlements - JobRadar.app` shows none)

**Phase to address:**
Phase 5 (Platform Installers) — signing MUST be tested on real hardware, not just CI

---

### Pitfall 4: GUI Uninstall Deletes Running App Files (Windows)

**What goes wrong:**
User clicks "Uninstall" button in GUI → confirmation dialog → app runs `shutil.rmtree()` on its own install directory → Windows locks error: "The process cannot access the file because it is being used by another process." On macOS, `rm -rf JobRadar.app` succeeds but app keeps running from memory, completing the uninstall but leaving zombie process.

Worse case: Uninstall succeeds in deleting `~/.local/share/JobRadar/` (all user data, reports, tracker) but FAILS to delete app itself. User thinks uninstall completed, but binary remains. Partial state.

**Why it happens:**
GUI uninstall runs IN THE SAME PROCESS that needs to be deleted. On Windows, you can't delete a running .exe. On macOS, you can delete the .app bundle but the process stays in memory. The current codebase uses CustomTkinter (job_radar/gui/main_window.py) but has no uninstall feature yet — developers won't discover this until testing Phase 6.

**How to avoid:**
1. **Two-stage uninstall**:
   - Stage 1 (running app): Delete user data (`~/.local/share/JobRadar/`, `~/.job-radar/`), create uninstall script, schedule script to run after exit
   - Stage 2 (external script): Wait for process to exit, delete app bundle, delete self

   ```python
   # In GUI uninstall handler
   def uninstall_and_exit():
       # Delete user data
       shutil.rmtree(get_data_dir())
       shutil.rmtree(Path.home() / ".job-radar")

       # Create platform-specific cleanup script
       if sys.platform == "darwin":
           script = Path("/tmp/job-radar-cleanup.sh")
           script.write_text(f"""#!/bin/bash
   sleep 2
   rm -rf {sys.executable.parent.parent.parent}  # JobRadar.app
   rm -f /tmp/job-radar-cleanup.sh
   """)
           os.chmod(script, 0o755)
           subprocess.Popen(["/bin/bash", str(script)])
       elif sys.platform == "win32":
           script = Path(tempfile.gettempdir()) / "job-radar-cleanup.bat"
           exe_path = Path(sys.executable).parent.parent  # onedir root
           script.write_text(f"""timeout /t 2
   rmdir /s /q "{exe_path}"
   del "%~f0"
   """)
           subprocess.Popen([str(script)], creationflags=subprocess.CREATE_NO_WINDOW)

       # Exit immediately
       sys.exit(0)
   ```

2. **Detect running app before uninstall**: Check if another Job Radar process is running (find PIDs, compare to current), warn user to close it first

3. **Uninstall confirmation shows EXACTLY what will be deleted**:
   - App binary: /Applications/JobRadar.app
   - User data: ~/Library/Application Support/JobRadar (X MB)
   - Profiles: ~/.job-radar/
   - Reports: ~/job-radar-output/

4. **Backup before uninstall**: Auto-create `.job-radar-backup.zip` on Desktop before deletion (escape hatch)

**Warning signs:**
- Windows uninstall fails with "file in use" error
- User data deleted but app still launchable
- Uninstall completes but old reports remain in `~/job-radar-output/`
- macOS app bundle deleted but process still visible in Activity Monitor

**Phase to address:**
Phase 6 (GUI Uninstall Feature) — requires cross-platform testing on real installs, not dev mode

---

### Pitfall 5: GitHub Actions Matrix Explodes CI Time with Multiple Installers

**What goes wrong:**
Current .github/workflows/release.yml builds 3 platforms (Linux, Windows, macOS) serially in ~15 minutes. Adding DMG (macOS), MSI (Windows), DEB (Linux), AppImage (Linux) means:
- macOS job now runs: PyInstaller build → sign binaries → create DMG → sign DMG → notarize → wait 5-10min for Apple → staple
- Windows job now runs: PyInstaller build → create MSI → create NSIS installer → sign both (if cert available)

Total CI time balloons to 45+ minutes. GitHub Actions free tier = 2000 min/month. Current 15min × 2 releases/month = 30min. New 45min × 2 = 90min. Still fine, BUT... if signing fails, entire matrix re-runs. One bad notarization = 45min wasted.

Worse: macOS runners are 10× more expensive than Linux (GitHub pricing). Building DMG on macOS-latest burns through quota fast.

**Why it happens:**
Current release.yml uses simple matrix strategy (lines 14-52). Each OS builds once. Adding multiple installer formats per OS without refactoring makes jobs sequential. Notarization is SLOW (Apple's servers, not GitHub's) and can't be parallelized.

Per web research, "distributing platform-specific builds across multiple runners using a matrix strategy can drastically reduce build durations." But Job Radar already uses matrix — the issue is DEPTH (multiple artifacts per platform) not WIDTH (multiple platforms).

**How to avoid:**
1. **Separate signing from building**:
   - Build job: PyInstaller only, upload unsigned artifacts
   - Sign job (macOS only): Download artifact, sign, notarize, upload signed DMG
   - This allows build failures to fail fast without burning notarization quota

2. **Conditional installer types**:
   - DMG: Required (macOS default)
   - MSI: Optional (defer to future milestone, ship ZIP only for v2.1)
   - DEB/AppImage: Optional (defer, ship .tar.gz only)
   - Document: "Installing from ZIP is supported, native installers coming in v2.2"

3. **Cache notarization credentials**:
   ```yaml
   - name: Restore notarization cache
     uses: actions/cache@v4
     with:
       path: ~/Library/MobileDevice/Provisioning Profiles
       key: ${{ runner.os }}-notarization-${{ hashFiles('entitlements.plist') }}
   ```

4. **Smoke test BEFORE signing**:
   Current smoke test (release.yml:75-94) runs AFTER build but could catch PyInstaller issues before wasting 10min on notarization

5. **Local testing script**:
   ```bash
   # scripts/test-installers.sh
   # Builds all formats locally to catch issues pre-commit
   pyinstaller job-radar.spec --clean
   cd dist && zip -r job-radar-test.zip JobRadar.app
   ```

**Warning signs:**
- Release workflow takes >30 minutes
- Notarization step times out (10min default GitHub timeout)
- "macOS runner minutes depleted" email from GitHub
- Release fails at signing step, whole matrix re-runs from scratch

**Phase to address:**
Phase 5 (Platform Installers) — optimize workflow BEFORE adding all formats, not after

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip schema version bump for "optional" scoring weights | No migration code needed, ships faster | KeyError crashes for old profiles, incomparable reports, data corruption | Never — scoring weights ARE breaking change |
| Use `--deep` for macOS code signing | One command signs everything | App won't open on user machines, "damaged" error | Never — official PyInstaller docs say don't use --deep |
| Hardcode new API rate limits in Python code | No config migration needed | Every new source requires code deploy, can't adjust limits without release | Early prototyping only, not production |
| Store scoring weights in config.json instead of profile.json | Easier to edit, no schema migration | Breaks multi-profile workflows, user can't have different weights per profile | Only if single-profile assumption is acceptable (unlikely for job search) |
| Ship unsigned Windows installer | Saves $400/year certificate cost | Users see SmartScreen warning, enterprise firewalls block | Acceptable for v2.1 if documented, mandatory for v3.0 |
| Delete user data synchronously in GUI thread | Simple implementation, less code | GUI freezes during `rmtree()` on large directories, appears hung | Never — deleting 1GB of reports takes 10+ seconds |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Job aggregator APIs | Treating each API as independent source, creating separate rate limiters | Map multiple sources to shared backend API, pool rate limits |
| PyInstaller + new dependencies | Adding `requests` variant library (httpx, aiohttp) without hidden import | Add to `hidden_imports` in job-radar.spec, test frozen build |
| SQLite rate limiters | Opening connection per API call, not closing | Cache connections in module-level dict, close with atexit |
| Platform-specific installers | Building DMG/MSI in same job as PyInstaller | Separate build job from signing/packaging job for faster failures |
| Schema migration | Loading old profile, modifying in-place, not saving | Auto-save after migration so next load is fast (current code does this, KEEP IT) |
| GUI uninstall | Deleting app directory from within running app | Two-stage: delete data + schedule cleanup script, then exit |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Opening 10 SQLite connections for rate limiters without closing | "Database is locked" errors, high file descriptor count | Connection pooling + atexit cleanup | >6 simultaneous API sources |
| Synchronous DELETE of large user data directory in GUI thread | GUI freezes for 10-30 seconds during uninstall | Background thread with progress dialog OR fast exit + cleanup script | User has >1GB of cached reports |
| Notarization blocking GitHub Actions workflow | Release workflow times out at 10 minutes | Submit to Apple, poll asynchronously, fail fast if rejected | Every macOS release (Apple's servers, not our code) |
| Recomputing all scores after weight change without cache invalidation | Changing skill_match weight from 0.25→0.30 doesn't update old reports | Bump schema version, mark old reports as "scored with v1 weights" | Reports with 100+ jobs |
| Loading all API credentials from .env on every search | Redundant file I/O, slow startup | Load once at module import, cache in memory (current code does this, KEEP IT) | Not a trap with current implementation |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing API keys in profile.json instead of .env | Keys committed to git, exposed in reports | Keep existing .env pattern, never serialize keys to user-visible files |
| Uninstall script doesn't verify paths before deletion | Malicious profile could set data_dir to "/", deletes entire system | Whitelist allowed deletion paths, require paths contain "JobRadar" or ".job-radar" |
| Downloading installer scripts from CDN without hash verification | MITM attack injects malicious code | Pin installer dependencies, use subresource integrity (SRI) if fetching from web |
| macOS uninstall script with sudo without user prompt | Privilege escalation vulnerability | Never require sudo for uninstall, app data is user-owned |
| Exposing internal API keys in error messages | User screenshots leak credentials | Redact API keys in logs: `ADZUNA_APP_ID=abc***xyz` |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback when configurable scoring weight validation fails | User sets skill_match=2.0, weights sum to >1.0, app silently clamps or crashes | Real-time validation in CustomTkinter form: show error tooltip, disable Save button |
| Uninstall button deletes data immediately without confirmation | Accidental click destroys 6 months of job tracking | Two-step confirmation: "This will delete X profiles, Y reports. Type DELETE to confirm." |
| Old reports show different scores than current for same job | User confused why "Python Developer @ Acme" was 4.2 last week, now 3.8 | Display scoring weights version in report header: "Scored with v1 weights (skill:0.25)" |
| API rate limit errors show technical "429 Too Many Requests" | User doesn't know if it's temporary or permanent | User-friendly: "JobAPI is rate limiting requests. Retrying at 2:35pm. Try fewer sources or wait." |
| macOS installer warns "damaged app" if unsigned | User thinks download is corrupted, deletes and re-downloads | Pre-release instructions: "Right-click → Open" to bypass Gatekeeper, or sign properly |
| GUI uninstall doesn't offer backup option | Users uninstall to "start fresh", lose valuable data | "Uninstalling? Export your data first" with one-click backup to Desktop |

## "Looks Done But Isn't" Checklist

- [ ] **Configurable scoring weights:** Often missing validation that weights sum to 1.0 — verify edge cases like all zeros, negative numbers, weights > 1.0
- [ ] **API source integration:** Often missing rate limit exhaustion handling — verify behavior when 429 persists for hours (should skip source gracefully)
- [ ] **Schema migration:** Often missing backward compatibility test — verify v1 profile loads in v2 code, auto-migrates, and saves successfully
- [ ] **macOS code signing:** Often missing notarization step — verify `spctl --assess --verbose JobRadar.app` passes on clean macOS 13+ machine
- [ ] **GUI uninstall:** Often missing check for running processes — verify uninstall detects and warns about other Job Radar instances
- [ ] **Platform installers:** Often missing smoke test on REAL installs — verify DMG/MSI install on clean VM, app launches, search works, uninstall completes
- [ ] **Multi-platform CI:** Often missing failure isolation — verify single platform failure doesn't block other platforms from releasing
- [ ] **Rate limiter cleanup:** Often missing connection closure — verify `.rate_limits/*.db` files aren't locked after app exit

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Released v2.1 without schema version bump, users get KeyError | HIGH — requires hotfix release | 1. Hotfix: Bump schema to v2, add migration. 2. Add fallback: `profile.get("scoring_weights", DEFAULT_WEIGHTS)` in scoring.py. 3. Docs: "v2.1.0 users, re-run setup wizard to fix crashes." |
| macOS app signed with `--deep`, users can't open it | HIGH — requires re-release | 1. Pull release from GitHub. 2. Re-sign correctly (inside-out, no --deep). 3. Re-notarize. 4. Re-release as v2.1.1 with "Fixed macOS installation" notes. |
| SQLite rate limiter connections not closed, database locked | LOW — restart fixes it | 1. Add atexit handler in patch release. 2. Docs: "If you see 'database is locked', restart Job Radar." |
| GUI uninstall deleted data but failed to delete app | MEDIUM — manual cleanup required | 1. User Instructions: "Delete app manually from /Applications or Program Files." 2. Next release: Add two-stage uninstall. |
| GitHub Actions times out during notarization | LOW — re-run workflow | 1. Cancel workflow. 2. Re-trigger. 3. If persists, skip notarization for this release (ship ZIP only). 4. Fix: Separate signing into dedicated job. |
| User sets scoring weights that sum to 0.8, all scores skewed low | LOW — user can re-adjust | 1. Detect in validation, show warning. 2. Offer "Normalize weights to sum to 1.0?" button. 3. Save normalized version. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Scoring weight migration without schema bump | Phase 1: Configurable Scoring Architecture | Test: Load v1 profile, verify auto-migration to v2, compare scores |
| Rate limiter state corruption across new sources | Phase 2: API Source Infrastructure | Test: Add 6 sources, check `.rate_limits/` has <6 databases, no locked errors |
| macOS code signing breaks executables | Phase 5: Platform Installers | Test: `codesign --verify JobRadar.app` + `spctl --assess` on clean macOS |
| GUI uninstall deletes running app files | Phase 6: GUI Uninstall Feature | Test: Click uninstall, verify data deleted + app exits + binary removed |
| GitHub Actions matrix explodes CI time | Phase 5: Platform Installers | Test: Measure workflow duration pre/post installer additions, optimize if >30min |

## Sources

### macOS Code Signing & Notarization
- [OS X Code Signing Pyinstaller.md · GitHub](https://gist.github.com/txoof/0636835d3cc65245c6288b2374799c43)
- [Recipe OSX Code Signing · pyinstaller/pyinstaller Wiki](https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OSX-Code-Signing)
- [Pyinstaller exe fails when signed following apple notarization process · Issue #7937](https://github.com/pyinstaller/pyinstaller/issues/7937)

### API Rate Limiting
- [API Rate Limit Exceeded: Complete Guide to Fix 429 Errors](https://dataprixa.com/api-rate-limit-exceeded/)
- [Rate Limiting Without the Rage: A 2026 Guide | Zuplo Learning Center](https://zuplo.com/learning-center/rate-limiting-without-the-rage-a-2026-guide)

### NSIS Windows Installers
- [pynsist · PyPI](https://pypi.org/project/pynsist/)
- [NSIS vs Python Experience | ISD](https://isd-soft.com/tech_blog/nsis-vs-python-experience/)

### Configuration Migration
- [What's the best way to do backwards compatibility for existing configs? · Issue #479](https://github.com/omni-us/jsonargparse/issues/479)
- [GitHub - dreverri/evolve: JSON based schema migration tool](https://github.com/dreverri/evolve)

### GitHub Actions Multi-Platform Builds
- [GitHub Actions: Complete CI/CD Guide for Developers](https://dasroot.net/posts/2026/01/github-actions-complete-ci-cd-guide/)
- [Cross-platform release builds with Github Actions - Electric UI](https://electricui.com/blog/github-actions)

### PyInstaller Hidden Imports
- [When Things Go Wrong — PyInstaller 6.18.0 documentation](https://pyinstaller.org/en/stable/when-things-go-wrong.html)
- [how to include multiple hidden imports in pyinstaller inside spec file · Issue #4588](https://github.com/pyinstaller/pyinstaller/issues/4588)

### Desktop App Uninstallation
- [How to Uninstall Software Using Python (Windows, macOS, Linux) – TheLinuxCode](https://thelinuxcode.com/how-to-uninstall-software-using-python-windows-macos-linux/)

### Python Configuration Patterns
- [Python Constants in 2026: Practical Patterns – TheLinuxCode](https://thelinuxcode.com/python-constants-in-2026-practical-patterns-immutability-and-realworld-usage/)

---
*Pitfalls research for: Job Radar v2.1.0 Source Expansion & Polish*
*Researched: 2026-02-13*
