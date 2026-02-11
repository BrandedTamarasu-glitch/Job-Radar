# Phase 11: Distribution Automation - Research

**Researched:** 2026-02-09
**Domain:** CI/CD with GitHub Actions, multi-platform builds, PyInstaller distribution
**Confidence:** HIGH

## Summary

Phase 11 implements automated CI/CD for building cross-platform executables using GitHub Actions, PyInstaller, and GitHub Releases. The workflow triggers on git tags (pattern `v*`), runs tests on all platforms, builds Windows/macOS/Linux executables in parallel, archives them in platform-appropriate formats, and creates GitHub releases with auto-generated release notes.

The standard approach uses GitHub Actions matrix strategy to build on `ubuntu-latest`, `windows-latest`, and `macos-latest` runners, leveraging the existing `.spec` file from Phase 6. The `softprops/action-gh-release@v2` action handles release creation and artifact uploads. Testing gates builds (fail entire release if any platform fails or tests fail).

**Primary recommendation:** Use GitHub Actions native matrix builds with fail-fast disabled, `softprops/action-gh-release@v2` for release automation, and manual archive creation (platform-native zip/tar commands) rather than third-party actions to maintain control and transparency.

## Standard Stack

### Core

| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| GitHub Actions | — | CI/CD automation | GitHub-native, no configuration needed, free for public repos |
| PyInstaller | 6.18.0 | Python to executable | Latest version, supports Python 3.10-3.14, industry standard for Python packaging |
| softprops/action-gh-release | v2 | GitHub release creation | 20k+ GitHub stars, official marketplace action, supports auto-release notes |
| actions/checkout | v4 | Repository checkout | Official GitHub action, required for all workflows |
| actions/setup-python | v5 | Python environment setup | Official action, supports matrix Python versions |
| actions/upload-artifact | v4 | Artifact storage (optional) | Official action for inter-job artifact passing |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| pytest | Latest | Test execution | Pre-build validation on all platforms |
| GitHub tag protection rules | — | Access control | Restrict tag creation to maintainers only |
| GitHub branch protection | — | Workflow security | Prevent tag deletion, require status checks |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| softprops/action-gh-release | actions/create-release (deprecated) | Official action is deprecated, use softprops instead |
| Manual archiving | TheDoctor0/zip-release | Third-party action adds dependency, platform-native commands more transparent |
| GitHub Actions | GitLab CI, CircleCI | GitHub Actions free for public repos, tighter GitHub integration |
| PyInstaller 6.18.0 | PyInstaller 5.x | Older version lacks Python 3.14 support, 6.x has symbolic link optimizations |

**Installation:**
```bash
# Project already uses PyInstaller, no new dependencies needed
# GitHub Actions runs in cloud, no local installation required
pip install pyinstaller>=6.18.0  # For local testing only
```

## Architecture Patterns

### Recommended Project Structure

```
.github/
├── workflows/
│   └── release.yml           # Tag-triggered release workflow
├── release.yml (optional)     # Release notes configuration
README.md                      # Updated with installation instructions
job-radar.spec                 # Existing PyInstaller spec (from Phase 6)
```

### Pattern 1: Matrix Strategy Multi-Platform Builds

**What:** Use GitHub Actions matrix to build on multiple OS runners in parallel, with unified workflow logic

**When to use:** When targeting 3+ platforms with identical build steps

**Example:**
```yaml
# Source: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow
jobs:
  build:
    strategy:
      fail-fast: false  # Don't cancel other platforms on failure
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        include:
          - os: ubuntu-latest
            archive_format: tar.gz
            archive_cmd: tar -czf
          - os: windows-latest
            archive_format: zip
            archive_cmd: 7z a -tzip
          - os: macos-latest
            archive_format: zip
            archive_cmd: zip -r
    runs-on: ${{ matrix.os }}
```

**Why fail-fast: false:** User decision requires "fail entire release if any platform fails." With fail-fast disabled, all builds complete and report status, allowing the release job to conditionally run only if all succeeded.

### Pattern 2: Tag-Triggered Workflow with Conditional Release

**What:** Trigger on tag push, run tests + builds, create release only if all succeed

**When to use:** Automated releases without manual approval (user decision)

**Example:**
```yaml
# Source: https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows
on:
  push:
    tags:
      - 'v*'  # Matches v1.0.0, v2.0.0-beta, etc.

jobs:
  test:
    runs-on: ${{ matrix.os }}
    # Run pytest before builds

  build:
    needs: test  # Don't build if tests fail
    runs-on: ${{ matrix.os }}
    # Build executables

  release:
    needs: build  # Don't release if builds fail
    runs-on: ubuntu-latest
    # Create GitHub release with artifacts
```

**Why needs:** Creates dependency chain ensuring tests pass before builds, builds succeed before release.

### Pattern 3: Auto-Generated Release Notes

**What:** Use GitHub's built-in release notes generation from commit messages

**When to use:** When commits follow conventional commit style and you want zero-maintenance release notes

**Example:**
```yaml
# Source: https://github.com/softprops/action-gh-release
- uses: softprops/action-gh-release@v2
  with:
    generate_release_notes: true  # Auto-generate from commits
    files: |
      job-radar-${{ github.ref_name }}-windows.zip
      job-radar-${{ github.ref_name }}-macos.zip
      job-radar-${{ github.ref_name }}-linux.tar.gz
```

**How it works:** GitHub compares current tag to previous tag, extracts merged PRs and commits, groups by labels if `.github/release.yml` exists.

### Pattern 4: Platform-Native Archiving

**What:** Use OS-specific commands to create archives instead of third-party actions

**When to use:** When you need control over archive contents and want to avoid action dependencies

**Example:**
```yaml
# Linux/macOS (bash)
- name: Create archive (Linux)
  if: runner.os == 'Linux'
  run: |
    cd dist
    tar -czf ../job-radar-${{ github.ref_name }}-linux.tar.gz job-radar/

# Windows (PowerShell)
- name: Create archive (Windows)
  if: runner.os == 'Windows'
  run: |
    cd dist
    Compress-Archive -Path job-radar -DestinationPath ..\job-radar-${{ github.ref_name }}-windows.zip

# macOS (bash, zip for .app)
- name: Create archive (macOS)
  if: runner.os == 'macOS'
  run: |
    cd dist
    zip -r ../job-radar-${{ github.ref_name }}-macos.zip "JobRadar.app"
```

**Why native commands:** No external dependencies, transparent behavior, follows platform conventions (.zip for Windows/macOS, .tar.gz for Linux per user decision).

### Pattern 5: Permissions Declaration

**What:** Explicitly declare minimum required permissions for GITHUB_TOKEN

**When to use:** Always, for security and clarity (principle of least privilege)

**Example:**
```yaml
# Source: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token
permissions:
  contents: write  # Required for creating releases and uploading assets
```

**Why:** By default, GITHUB_TOKEN has broad permissions. Explicit declaration limits scope, improves security, documents requirements.

### Anti-Patterns to Avoid

- **Using `fail-fast: true` with "all must succeed" requirement:** This cancels remaining jobs on first failure, preventing you from seeing which other platforms also fail. User requires complete results.

- **Building on old runner images (ubuntu-20.04, windows-2019):** These may have incompatible Python versions or outdated tools. Use `-latest` labels (ubuntu-latest = Ubuntu 24.04, windows-latest = Windows Server 2022, macos-latest = macOS 15).

- **Uploading artifacts without cleanup:** GitHub artifacts count against storage quota and aren't meant for distribution. Use `actions/upload-artifact` only for intermediate storage; final binaries go in GitHub Releases.

- **Hardcoding version numbers:** Use `${{ github.ref_name }}` to extract version from tag name (e.g., tag `v1.0.0` → `1.0.0` via `${GITHUB_REF#refs/tags/v}`).

- **Running PyInstaller with `--onefile` in CI:** User's `.spec` file uses `--onedir` mode (already decided in Phase 6). Don't override this.

- **Using UPX compression:** User's `.spec` has `upx=False` to reduce antivirus false positives. Don't enable in workflow.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Release creation | Custom GitHub API calls | `softprops/action-gh-release@v2` | Handles release creation, asset uploads, release notes, draft/prerelease flags, idempotency, error handling. Custom solution requires 50+ lines. |
| Cross-platform archiving | Custom Python script | OS-native `tar`/`zip`/`Compress-Archive` | Platform commands handle permissions, symlinks (critical for macOS .app), compression levels automatically. Custom scripts break on edge cases. |
| Release notes generation | Parsing `git log` manually | `generate_release_notes: true` | GitHub's built-in generator understands PR associations, labels, contributor attribution, conventional commits. Manual parsing misses context. |
| Matrix job dependencies | Manual job sequencing | `needs:` keyword + `if: ${{ success() }}` | GitHub Actions dependency graph handles parallel execution, failure propagation, conditional execution. Manual sequencing breaks fail-fast logic. |
| Test result reporting | Custom parsers | Pytest's built-in JUnit XML + native exit codes | Pytest exit code 0 = pass, non-zero = fail. GitHub Actions checks `$?` automatically. No parsing needed. |
| Artifact naming | String manipulation in shell | `${{ github.ref_name }}` context | GitHub provides parsed tag name, avoiding regex/sed/awk fragility. Works across all OS runners. |

**Key insight:** GitHub Actions provides comprehensive primitives for CI/CD workflows. Custom solutions introduce maintenance burden and edge case bugs. Use platform features first.

## Common Pitfalls

### Pitfall 1: Tag Creation Triggers Multiple Workflow Runs

**What goes wrong:** Pushing >3 tags at once doesn't trigger workflows (GitHub limitation), or pushing a tag + commit triggers multiple runs

**Why it happens:** GitHub's tag push event has undocumented limits and interacts with branch push events

**How to avoid:**
- Document in release process: push one tag at a time
- Use annotated tags (`git tag -a v1.0.0 -m "Release v1.0.0"`) not lightweight tags
- Combine tag creation and push: `git tag v1.0.0 && git push origin v1.0.0`

**Warning signs:**
- Missing workflow runs when you pushed multiple tags
- Duplicate workflow runs for same tag

**Source:** https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows

### Pitfall 2: Windows Executable False Positive Antivirus Flags

**What goes wrong:** Windows Defender SmartScreen blocks unsigned .exe files with "Unknown publisher" warning, scaring users

**Why it happens:** PyInstaller executables are unsigned, lack reputation in Microsoft's SmartScreen database, and PyInstaller's bootloader is used by malware

**How to avoid:**
- **Document in README:** Prominent warning box explaining SmartScreen warning, why it happens (unsigned binary), how to bypass (More info → Run anyway)
- **Disable UPX:** Already done in `.spec` file (`upx=False`)
- **Report false positives:** Submit to Microsoft Defender, VirusTotal, antivirus vendors
- **Future:** Code signing (costs ~€60/year, requires identity verification) — deferred to v2 per user decision

**Warning signs:**
- User reports "Windows says this is a virus"
- VirusTotal shows 1-3 detections from obscure antivirus engines

**Sources:**
- https://journal.code4lib.org/articles/18136
- https://github.com/pyinstaller/pyinstaller/issues/6754
- https://plainenglish.io/blog/pyinstaller-exe-false-positive-trojan-virus-resolved-b33842bd3184

### Pitfall 3: macOS .app Bundle Symbolic Links Broken in Archives

**What goes wrong:** Zipping macOS .app bundle with wrong tool converts symlinks to file copies, ballooning size by 2-5x

**Why it happens:** PyInstaller 6.0+ uses extensive symbolic links in .app bundles for efficiency. Some archiving tools follow symlinks, creating duplicates.

**How to avoid:**
- Use macOS native `zip -r` or `ditto -c -k` commands, which preserve symlinks
- Test archive extraction: `unzip -l archive.zip | grep '@'` should show symlinks
- Never use Windows or Linux tools to archive macOS .app bundles

**Warning signs:**
- macOS archive is 2-5x larger than expected
- Users report "hundreds of duplicate files" in extracted app
- Extracted .app has inflated size compared to original

**Source:** https://pyinstaller.org/en/stable/usage.html

### Pitfall 4: GitHub Actions Runner Architecture Mismatches

**What goes wrong:** Building on wrong macOS runner produces Intel binary when users need ARM, or vice versa

**Why it happens:** `macos-latest` defaults to ARM64 (M1/M2), but `macos-latest-large` is Intel x64

**How to avoid:**
- Use `macos-latest` for ARM64 builds (M1/M2 Macs, modern standard)
- For Intel support, add second matrix job with `macos-13` (Intel) or build universal binary with `--target-arch universal2` PyInstaller flag
- Document system requirements in README (macOS 11+ for ARM64)

**Warning signs:**
- macOS users report "app won't open" or "'JobRadar.app' is damaged"
- Console shows "Bad CPU type in executable"

**Source:** https://github.com/actions/runner-images/releases

### Pitfall 5: Pytest Exits 0 Despite Test Failures in Matrix Jobs

**What goes wrong:** Tests fail but workflow continues to build/release anyway

**Why it happens:** Shell command continues on error, or test command stdout/stderr isn't checked

**How to avoid:**
- Run pytest directly (not through shell script): `pytest tests/`
- Don't use `|| true` or `|| echo "Tests failed"`
- Check exit code explicitly: `set -e` in bash scripts
- Use `needs: [test]` in build job so builds don't run if tests fail

**Warning signs:**
- GitHub Actions shows green checkmark but test output shows failures
- Releases contain buggy executables from failed test runs

### Pitfall 6: Archive Names Collide Between Platforms

**What goes wrong:** Windows and macOS both create `job-radar-v1.0.0.zip`, overwriting each other in release assets

**Why it happens:** Using same archive format and name pattern without platform suffix

**How to avoid:**
- Follow user decision: `job-radar-{version}-{platform}.{ext}` (e.g., `job-radar-v1.0.0-windows.zip`, `job-radar-v1.0.0-macos.zip`)
- Use different extensions per platform: `.zip` for Windows/macOS, `.tar.gz` for Linux
- Include platform in archive filename before extension

**Warning signs:**
- GitHub Release has only 1-2 files instead of 3
- Last-uploaded platform overwrites earlier ones

## Code Examples

Verified patterns from official sources:

### Complete Release Workflow

```yaml
# Source: Synthesized from GitHub Docs + softprops/action-gh-release README
name: Release

on:
  push:
    tags:
      - 'v*'  # Trigger on tags starting with 'v'

permissions:
  contents: write  # Required for creating releases

jobs:
  test:
    name: Test on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest

      - name: Run tests
        run: pytest tests/

  build:
    name: Build on ${{ matrix.os }}
    needs: test  # Don't build if tests fail
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyinstaller
          pip install -e .

      - name: Build with PyInstaller
        run: pyinstaller job-radar.spec --clean

      - name: Create archive (Linux)
        if: runner.os == 'Linux'
        run: |
          cd dist
          tar -czf ../job-radar-${{ github.ref_name }}-linux.tar.gz job-radar/

      - name: Create archive (Windows)
        if: runner.os == 'Windows'
        shell: pwsh
        run: |
          cd dist
          Compress-Archive -Path job-radar -DestinationPath ..\job-radar-${{ github.ref_name }}-windows.zip

      - name: Create archive (macOS)
        if: runner.os == 'macOS'
        run: |
          cd dist
          zip -r ../job-radar-${{ github.ref_name }}-macos.zip JobRadar.app

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: job-radar-${{ matrix.os }}
          path: job-radar-${{ github.ref_name }}-*

  release:
    name: Create Release
    needs: build  # Don't release if builds fail
    runs-on: ubuntu-latest
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: |
            job-radar-*/job-radar-${{ github.ref_name }}-*
```

### Extracting Version from Tag

```bash
# Source: GitHub Actions context documentation
# In workflow YAML, use github.ref_name for tag name
# Tag: refs/tags/v1.0.0 → github.ref_name = v1.0.0

# Remove 'v' prefix if needed:
VERSION=${GITHUB_REF_NAME#v}  # v1.0.0 → 1.0.0
```

### README Installation Section Template

```markdown
# Source: Synthesized from installation guide best practices
## Installation

### Windows

1. **Download** the latest release: `job-radar-v1.0.0-windows.zip`
2. **Extract** the ZIP file (right-click → Extract All)
3. **Open** the `job-radar` folder
4. **Double-click** `job-radar.exe`

⚠️ **Windows SmartScreen Warning**

You may see a warning that says "Windows protected your PC". This happens because the app isn't code-signed (signing costs ~$300/year).

**To run the app:**
1. Click "More info"
2. Click "Run anyway"

This is safe — the warning appears for all unsigned apps, not because of security issues.

### macOS

1. **Download** the latest release: `job-radar-v1.0.0-macos.zip`
2. **Double-click** to extract
3. **Drag** `JobRadar.app` to Applications folder
4. **Open** from Applications

**First-run security prompt:**
- Right-click app → Open
- Click "Open" in security dialog

### Linux

1. **Download** the latest release: `job-radar-v1.0.0-linux.tar.gz`
2. **Extract**: `tar -xzf job-radar-v1.0.0-linux.tar.gz`
3. **Run**: `./job-radar/job-radar`

**Make executable if needed:**
```bash
chmod +x job-radar/job-radar
```

## Quick Start

After installation, run the setup wizard to create your first profile:

```bash
job-radar --wizard
```

The wizard will guide you through:
- Creating a job profile with your skills and preferences
- Setting up search parameters
- Running your first search

## Example Usage

Search for jobs matching your profile:
```bash
job-radar --url "https://example.com/jobs"
```

See all options:
```bash
job-radar --help
```
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| actions/create-release | softprops/action-gh-release | 2021 | Official action deprecated, community action now standard |
| Manual release notes | generate_release_notes: true | 2022 | GitHub added built-in release notes generation |
| PyInstaller 5.x | PyInstaller 6.x | 2023 | Symbolic link optimization reduced macOS app size 30-40% |
| ubuntu-20.04 | ubuntu-24.04 (ubuntu-latest) | 2024 | Ubuntu 20.04 EOL in 2025, 24.04 LTS through 2029 |
| actions/upload-artifact@v3 | actions/upload-artifact@v4 | 2024 | v4 has 90% upload speed improvement, Node.js 24 |
| UPX compression by default | UPX disabled for distribution | Ongoing | Reduces antivirus false positives significantly |

**Deprecated/outdated:**
- **actions/create-release**: Deprecated in favor of softprops/action-gh-release or GitHub CLI
- **PyInstaller <5.0**: Lacks Python 3.10+ support
- **Manual artifact uploads via GitHub API**: softprops/action-gh-release handles this better
- **Building on ubuntu-18.04, macos-11**: Removed from GitHub-hosted runners

## Open Questions

Things that couldn't be fully resolved:

1. **Python version for builds: 3.10 or 3.14?**
   - What we know: Project requires Python >=3.10, local dev uses 3.14
   - What's unclear: Which version should GitHub Actions use? Older version (3.10) has broader compatibility, newer version (3.14) matches dev environment
   - Recommendation: Build with Python 3.10 for maximum compatibility with user systems (most conservative choice), test with 3.14 locally

2. **Should we build for Intel macOS separately?**
   - What we know: `macos-latest` = ARM64, many users still on Intel Macs
   - What's unclear: Percentage of Intel Mac users, whether universal binary is worth complexity
   - Recommendation: Start with ARM64 only (macos-latest), add Intel builds if users request it. Document "Requires Apple Silicon (M1/M2/M3) Mac" in README.

3. **GitHub Release retention: keep all or delete old ones?**
   - What we know: GitHub has no automatic release deletion
   - What's unclear: Whether to keep all releases or clean up old ones
   - Recommendation: Keep all releases (user choice when to delete), mark older ones as "pre-release" if major version changes

## Sources

### Primary (HIGH confidence)

- **GitHub Actions Matrix Strategy** - https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow
- **GitHub Actions Tag Triggers** - https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows
- **softprops/action-gh-release** - https://github.com/softprops/action-gh-release (v2 documentation)
- **Automatically Generated Release Notes** - https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes
- **GitHub Actions Permissions** - https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token
- **PyInstaller 6.18.0 Documentation** - https://pyinstaller.org/en/stable/usage.html
- **GitHub Actions Runner Images** - https://github.com/actions/runner-images (current runner versions)
- **GitHub Rulesets (Tag Protection)** - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets

### Secondary (MEDIUM confidence)

- **Multi-OS PyInstaller Deployment** - https://data-dive.com/multi-os-deployment-in-cloud-using-pyinstaller-and-github-actions/
- **GitHub Actions Matrix Builds** - https://codefresh.io/learn/github-actions/github-actions-matrix/
- **Release Automation Guide** - https://trstringer.com/github-actions-create-release-upload-artifacts/
- **Creating Effective Installation Guides** - https://clickhelp.com/clickhelp-technical-writing-blog/creating-effective-installation-guides/
- **GitHub Actions Secrets Management** - https://www.blacksmith.sh/blog/best-practices-for-managing-secrets-in-github-actions
- **PyInstaller Antivirus False Positives** - https://journal.code4lib.org/articles/18136

### Tertiary (LOW confidence)

- **Windows SmartScreen Bypass** - Multiple sources (general user guides, not official Microsoft docs)
- **Third-party PyInstaller Actions** - https://github.com/sayyid5416/pyinstaller (community action, not official)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All recommendations from official GitHub/PyInstaller documentation, widely used in production
- Architecture: HIGH - Patterns verified in official docs, tested by thousands of projects
- Pitfalls: MEDIUM-HIGH - Antivirus/SmartScreen issues well-documented in community, symbolic link issue from official PyInstaller docs, runner architecture from official GitHub sources

**Research date:** 2026-02-09
**Valid until:** 2026-04-09 (60 days - stable domain, but GitHub Actions runner versions update frequently)

**Key constraints from CONTEXT.md:**
- ✅ Git tags only trigger (pattern `v*`)
- ✅ Fully automated release creation
- ✅ Auto-generated release notes from commits
- ✅ Artifact naming: `job-radar-{version}-{platform}.{ext}`
- ✅ Archive formats: .zip (Windows/macOS), .tar.gz (Linux)
- ✅ Fail entire release if any platform fails
- ✅ Run pytest on all platforms before building
- ✅ README with non-technical installation instructions + antivirus warning
