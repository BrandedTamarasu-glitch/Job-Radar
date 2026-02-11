# Phase 11: Distribution Automation - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Automated CI/CD pipeline for building Windows, macOS, and Linux executables and publishing GitHub releases. Triggered by git tags. Includes installation documentation for non-technical users. Code signing and update mechanisms are deferred to v2.

</domain>

<decisions>
## Implementation Decisions

### Build trigger strategy
- **Trigger:** Git tags only — pushing a tag starting with 'v' triggers builds (v1.1.0, v2.0.0-beta, etc.)
- **Tag pattern:** Any tag starting with 'v' (flexible for releases and pre-releases)
- **Release creation:** Fully automated — tag triggers build, then creates GitHub release with binaries attached
- **Release notes:** Auto-generated from commit messages since last tag (GitHub's auto-generation)

### Artifact naming and versioning
- **Naming format:** `job-radar-{version}-{platform}` (e.g., job-radar-v1.1.0-windows.zip)
- **Archive formats:** .zip for Windows/macOS, .tar.gz for Linux (standard platform conventions)
- **Version source:** Git tag is source of truth (tag v1.1.0 creates v1.1.0 binaries)
- **Archive contents:** Just the executable/app (Windows: job-radar.exe, macOS: Job Radar.app, Linux: job-radar binary)

### README and documentation
- **Location:** Main README.md with sections for each platform (visible on GitHub)
- **Detail level:** Step-by-step installation with screenshots for non-technical users (download, extract, double-click, first-run wizard)
- **Antivirus warning:** Prominent callout box at top of Installation section (users see it before downloading)
- **Additional content:** Quick start guide + usage examples (what it does, how to run, example searches)

### Release workflow and approval
- **Access control:** Repository owner/maintainers only can push tags (restrict via branch protection)
- **Approval:** Fully automated, no manual approval step (tag → build → publish)
- **Build failure handling:** Fail entire release if any platform fails (no partial releases with 2/3 platforms)
- **Testing:** Run full pytest suite on all platforms BEFORE building binaries (builds only proceed if tests pass)

### Claude's Discretion
- Exact GitHub Actions workflow syntax and job structure
- Build matrix configuration details
- PyInstaller flags and optimization settings (already defined in Phase 6 .spec files)
- Specific wording of README sections (as long as matches detail/tone decisions above)

</decisions>

<specifics>
## Specific Ideas

- Installation instructions should assume zero technical background — "download this file", "double-click to extract", "open the app"
- Antivirus warning should explain WHY it happens (unsigned binary) and HOW to proceed (click "More info" → "Run anyway")
- Quick start should show the wizard-first flow as primary path (matches Phase 10 help text)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-distribution-automation*
*Context gathered: 2026-02-09*
