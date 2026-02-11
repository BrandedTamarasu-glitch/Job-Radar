# UX Workflow Analysis: Job Radar

**Researched:** 2026-02-10
**Tool Version:** v1.2.0
**Confidence:** HIGH (based on code analysis + 2026 CLI/web UX best practices)

## Executive Summary

Job Radar's workflow flows smoothly through a well-structured wizard and automated search pipeline, but friction accumulates in the **report-to-application transition**—the critical moment when users must manually copy URLs from the HTML report to apply. Additional friction exists in profile iteration (re-running the entire wizard to update a single field) and result prioritization (scanning tables to find the best matches).

**Key strengths to preserve:**
- Clean wizard with inline validation and back navigation
- Automatic browser opening
- Dual-format reports (HTML + Markdown)
- NEW badge tracking across runs
- Cross-platform executables

**Primary friction areas:**
1. **High severity:** Manual copy-paste to apply (5-10 clicks per job × daily workflow)
2. **Medium severity:** Profile editing requires full wizard re-run
3. **Medium severity:** Report scannability—tables bury high-value jobs
4. **Low severity:** No quick profile preview or status tracking

---

## Current Workflow Assessment

### What Works Well (Preserve These)

#### 1. First-Run Wizard Experience
- **Sequential prompts with context:** Each field includes examples and instructions
- **Inline validation:** Errors caught immediately with clear messages
- **Back navigation:** `/back` command lets users correct mistakes
- **PDF resume upload:** Auto-extraction reduces manual entry
- **Post-summary editing:** Review-then-edit loop before save
- **Atomic file writes:** Temp file + rename prevents corruption

**Evidence from code:** wizard.py lines 200-801 implement comprehensive error handling, recovery paths, and the celebration summary with editing loop.

#### 2. Search Execution and Progress
- **Real-time progress feedback:** Source-by-source status updates (search.py:577-580)
- **Graceful error handling:** Network failures provide actionable messages
- **Fast execution:** Parallel fetching with progress callbacks
- **Date filtering:** Defaults to 48 hours (reasonable for daily searches)

#### 3. Report Generation
- **Automatic browser opening:** Works across platforms with headless detection
- **Dual formats:** HTML for browsing, Markdown for archival/LLM analysis
- **Cross-run tracking:** NEW badges highlight fresh opportunities
- **Statistics summary:** Lifetime stats provide trend context

#### 4. Technical Foundation
- **Cross-platform executables:** PyInstaller bundles work on Windows/macOS/Linux
- **Platform-appropriate data directories:** Uses platformdirs for config/profile storage
- **Color-aware terminal output:** Detects TTY and terminal capabilities
- **Comprehensive validation:** Profile schema validation with clear error messages

### Friction Points by Severity

---

## HIGH SEVERITY FRICTION

### F1: Manual Copy-Paste to Apply

**Problem:** After report generation, users must:
1. Read HTML report in browser
2. Identify interesting job
3. Click "View" button (opens new tab)
4. Copy URL from address bar (or right-click → Copy Link)
5. Paste into application tracker/browser
6. Repeat for each job

**Frequency:** 5-10 times per search (daily for active job seekers)
**Impact:** Adds 30-60 seconds per job. With 10 applications, that's 5-10 minutes of pure friction.

**Evidence from research:**
- Job search automation tools in 2026 emphasize reducing multi-step application flows ([How to Automate Job Applications](https://scale.jobs/blog/5-steps-to-automate-job-applications))
- Copy-paste hijacking research shows clipboard-related friction increases task completion time by 2.8× ([Copy-Paste Friction Research](https://lifetips.alibaba.com/tech-efficiency/how-to-disable-copy-and-paste-hijacking-web-sites))
- One-click apply systems achieve 25-47% callback rates vs 1-6% for manual ([AI Auto Apply Guide](https://careery.pro/blog/ai-auto-apply-for-jobs-guide))

**Current implementation:** HTML report (report.py:489-490) generates simple anchor tags:
```html
<a href="{url}" target="_blank" class="btn btn-sm btn-outline-primary">View</a>
```

**Solution 1: One-Click Copy URL Button** (LOW effort)

Add "Copy URL" button next to "View" button that copies job URL to clipboard:

```html
<a href="{url}" target="_blank" class="btn btn-sm btn-outline-primary me-1">View</a>
<button class="btn btn-sm btn-outline-secondary copy-btn" data-url="{url}" title="Copy job URL">
  <i class="bi bi-clipboard"></i> Copy
</button>
```

With JavaScript:
```javascript
document.querySelectorAll('.copy-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(btn.dataset.url);
      btn.innerHTML = '<i class="bi bi-check"></i> Copied!';
      setTimeout(() => btn.innerHTML = '<i class="bi bi-clipboard"></i> Copy', 2000);
    } catch (err) {
      btn.innerHTML = 'Failed';
    }
  });
});
```

**Benefit:** Reduces 4 clicks + selection to 1 click per job.

**Solution 2: "Copy All Top Jobs" Batch Action** (LOW effort)

Add button at top of Recommended section:
```html
<button class="btn btn-primary mb-3" id="copy-all-recommended">
  Copy All Recommended URLs (Markdown)
</button>
```

Copies to clipboard as:
```
## Job Applications - 2026-02-10

- [Senior Python Engineer — TechCo](https://example.com/job/123)
- [Backend Developer — StartupX](https://example.com/job/456)
- [Full Stack Engineer — BigCorp](https://example.com/job/789)
```

**Benefit:** Pastes directly into application tracker. One click for 5-10 jobs.

**Solution 3: Application Status Tracking UI** (MEDIUM effort)

Current tracker.py has status tracking infrastructure (lines 104-126) but no UI.

Add status buttons to each job card:
```html
<div class="btn-group btn-group-sm" role="group">
  <button class="status-btn" data-status="applied">Applied</button>
  <button class="status-btn" data-status="skipped">Skip</button>
  <button class="status-btn" data-status="interviewing">Interview</button>
</div>
```

With local storage persistence:
```javascript
// Store status in localStorage (survives page reload)
localStorage.setItem(`job-${jobKey}`, status);

// On next search, read statuses and update UI
const status = localStorage.getItem(`job-${jobKey}`);
if (status) {
  jobCard.classList.add(`status-${status}`);
  statusBadge.textContent = status.toUpperCase();
}
```

**Benefit:** Users can mark jobs as they process them, reducing mental load. Survives report regeneration.

**Recommendation:** Implement Solution 1 (Copy URL) + Solution 2 (Batch copy) immediately. Solution 3 requires more design but solves the "did I already apply?" problem.

---

## MEDIUM SEVERITY FRICTION

### F2: Profile Editing Requires Full Wizard Re-Run

**Problem:** User updates one skill → must navigate through all 11 wizard prompts again.

**Frequency:** Common during initial tuning (first 3-5 searches) as users refine dealbreakers, min_score, or skills.

**Impact:** 2-3 minutes per edit. Discourages iteration.

**Evidence from code:**
- wizard.py runs sequentially through all questions (lines 412-492)
- Post-summary editing exists (lines 557-790) but only available once at end
- No "quick edit" path for returning users

**Evidence from research:**
- CLI UX best practices emphasize minimizing repeated input ([CLI Guidelines](https://clig.dev/))
- Interactive CLIs should provide shortcuts for power users ([UX Patterns for CLI Tools](https://www.lucasfcosta.com/blog/ux-patterns-cli-tools))

**Current workaround:** Users can manually edit `~/.job-radar/profile.json`, but this:
1. Requires finding the file path
2. Risks JSON syntax errors
3. Loses wizard validation

**Solution 1: Quick Edit Menu** (MEDIUM effort)

When profile exists, add third option to main menu (\_\_main\_\_.py:88-98):
```python
choices=[
    "Run search with current profile",
    "Quick edit profile",
    "Full profile update"
]
```

Quick edit shows:
```
Current profile: John Doe (Senior Python Engineer)
What would you like to update?

1. Skills (10 core + 5 secondary)
2. Job titles (3 targets)
3. Location & arrangement
4. Dealbreakers (currently 2)
5. Search settings (min_score: 2.8, new_only: True)
6. Cancel (return to main menu)
```

Each option jumps directly to relevant questions, skips the rest.

**Solution 2: Profile Summary with Inline Edits** (LOW effort, partial solution)

Before "Run search" or "Update profile", show compact summary:
```
Profile: John Doe | 5 yrs | Senior | Python, Django, React
Targets: Backend Engineer, Python Developer, Full Stack
Location: Remote or Boston area
Min score: 2.8 | New only: Yes

Press Enter to search, or type 'edit' to update
```

If user types `edit`, show quick-edit menu (Solution 1).

**Solution 3: CLI Flags for Common Edits** (LOW effort)

Add flags for frequently-changed settings:
```bash
job-radar --update-skills "Python, Django, FastAPI, PostgreSQL, Redis"
job-radar --add-dealbreaker "clearance required"
job-radar --set-min-score 3.2
```

These update profile.json without wizard interaction.

**Recommendation:** Implement Solution 2 (profile preview) + Solution 1 (quick edit menu). Solution 3 is complementary for power users.

---

### F3: Report Scannability — High-Value Jobs Buried in Tables

**Problem:** The HTML report shows:
1. Statistics summary (good)
2. Profile summary (verbose, repeated from wizard)
3. Recommended roles (card format, good)
4. **All results table** (recommended + low-score jobs mixed together)

Users must scroll through the table to find jobs they haven't seen yet.

**Frequency:** Every search run, especially with 20+ results.

**Impact:** 30-60 seconds scanning table. Cognitive load increases with result volume.

**Evidence from research:**
- Users scan, not read—84% of visitors quickly scan for hook elements before deciding to dig deeper ([Scannability Best Practices](https://www.toptal.com/designers/web/ui-design-best-practices))
- Tables should use visual hierarchy to highlight important data ([10 Usability Findings](https://www.smashingmagazine.com/2009/09/10-useful-usability-findings-and-guidelines/))
- Optimal line length is 55-75 characters, 75-85 is popular ([Web Usability Guidelines](https://www.userfocus.co.uk/resources/guidelines.html))

**Current implementation:** report.py:529-602 generates a flat table. Score badges provide color, but layout doesn't surface top matches.

**Solution 1: Sticky Summary Bar with Quick Jump** (LOW effort)

Add fixed header at top of report (Bootstrap 5 supports this):
```html
<div class="sticky-top bg-light border-bottom py-2 px-3 d-flex justify-content-between">
  <div>
    <strong>5 NEW</strong> | <strong class="text-warning">3 Recommended</strong> |
    <strong class="text-success">1 Strong</strong>
  </div>
  <div>
    <a href="#recommended" class="btn btn-sm btn-outline-primary">Jump to Top Jobs</a>
    <button id="filter-new" class="btn btn-sm btn-outline-secondary">Show NEW Only</button>
  </div>
</div>
```

With JavaScript filter toggle:
```javascript
document.getElementById('filter-new').addEventListener('click', () => {
  document.querySelectorAll('tr:not(:has(.badge.bg-primary))').forEach(row => {
    row.style.display = row.style.display === 'none' ? '' : 'none';
  });
});
```

**Solution 2: Collapsible Table Sections** (LOW effort)

Group table by score ranges with collapse controls:
```html
<h3>
  Strong Matches (4.0+) — 2 jobs
  <button class="btn btn-sm btn-link" data-bs-toggle="collapse" data-bs-target="#strong-jobs">
    Show/Hide
  </button>
</h3>
<div id="strong-jobs" class="collapse show">
  <table><!-- 4.0+ jobs only --></table>
</div>

<h3>Recommended (3.5-3.9) — 5 jobs <button>...</button></h3>
<div id="recommended-jobs" class="collapse show">...</div>

<h3>Worth Reviewing (2.8-3.4) — 12 jobs <button>...</button></h3>
<div id="reviewing-jobs" class="collapse"><!-- Collapsed by default --></div>
```

**Solution 3: Card View Toggle** (MEDIUM effort)

Add view switcher:
```html
<div class="btn-group mb-3">
  <button class="btn btn-outline-primary active" data-view="cards">Cards</button>
  <button class="btn btn-outline-primary" data-view="table">Table</button>
</div>
```

Card view repeats the detailed format from Recommended section but for all results. Table is compact fallback.

**Recommendation:** Implement Solution 1 (sticky bar + filter) + Solution 2 (collapsible sections). These are low effort and provide immediate value.

---

### F4: No Quick Profile Preview Before Search

**Problem:** After first run, users can't quickly check what profile is active before running a search.

**Frequency:** Matters when user has multiple profiles or hasn't searched in a while.

**Impact:** Low severity (users remember their profile), but causes uncertainty.

**Solution:** Profile banner in CLI output (DONE—see \_\_main\_\_.py:62-67). Already implemented!

**Additional enhancement:** Show profile path:
```python
display_banner(version=__version__, profile_name=profile_name, profile_path=profile_path_str)
```

Banner becomes:
```
╔═══════════════════════════════════════╗
║         J O B   R A D A R             ║
║              v1.2.0                   ║
║                                       ║
║         Profile: John Doe             ║
║  ~/.job-radar/profile.json            ║
╚═══════════════════════════════════════╝
```

**Effort:** LOW (banner.py update)

---

## LOW SEVERITY FRICTION

### F5: Manual URL Section Lacks Context

**Problem:** Manual check URLs (Indeed, LinkedIn, Wellfound) are listed at bottom of report with minimal explanation.

**Current implementation:** report.py:605-643 lists URLs grouped by source.

**Solution:** Add helpful context:
```html
<div class="alert alert-info">
  <strong>Why manual checks?</strong> These sites block automated scraping.
  The URLs below use your profile to pre-fill search parameters.
  Open in private/incognito windows to avoid tracking.
</div>
```

**Effort:** LOW (one-line change to report.py)

---

### F6: No Visual Distinction Between Recommended and Lower-Scored Jobs in Table

**Problem:** The all-results table shows scores as badges, but rows don't have visual weight.

**Solution:** Add row background colors:
```html
<tr class="table-success"><!-- 4.0+ --></tr>
<tr class="table-warning"><!-- 3.5-3.9 --></tr>
<tr><!-- 2.8-3.4, default --></tr>
```

Or use Bootstrap's opacity utility:
```html
<tr class="opacity-50"><!-- Lower priority --></tr>
```

**Effort:** LOW (report.py table generation loop)

---

### F7: Wizard Lacks "Save and Search Later" Option

**Problem:** If user wants to create profile but not run search immediately (e.g., testing setup), they can't.

**Current flow:** Wizard completes → search runs automatically (\_\_main\_\_.py:86)

**Solution:** After wizard completes, ask:
```python
run_search = questionary.confirm(
    "Profile saved! Run search now?",
    default=True
).ask()

if not run_search:
    print("\nProfile saved. Run 'job-radar' anytime to search.")
    sys.exit(0)
```

**Effort:** LOW (\_\_main\_\_.py update)

---

### F8: No Export Option for Results

**Problem:** Users may want to import results into ATS (Applicant Tracking System) or spreadsheet.

**Current formats:** HTML + Markdown

**Solution:** Add CSV export option:
```bash
job-radar --export-csv results/jobs_2026-02-10.csv
```

CSV columns:
```
Score,New,Title,Company,Location,Arrangement,Salary,URL,Source,Date Posted
4.2,Yes,Senior Python Engineer,TechCo,Remote,remote,$150k-180k,https://...,Dice,2026-02-09
```

**Effort:** MEDIUM (new report format in report.py)

---

## Improvement Opportunities Summary

| ID | Problem | Impact | Solution | Effort | Priority |
|----|---------|--------|----------|--------|----------|
| F1 | Manual copy-paste to apply | HIGH | Copy URL button + batch copy | LOW | P0 |
| F2 | Profile editing requires full wizard | MEDIUM | Quick edit menu + preview | MEDIUM | P1 |
| F3 | Report scannability | MEDIUM | Sticky bar + collapsible sections | LOW | P1 |
| F4 | No profile preview | LOW | Enhanced banner | LOW | P2 |
| F5 | Manual URLs lack context | LOW | Add explanation | LOW | P2 |
| F6 | Table lacks visual hierarchy | LOW | Row background colors | LOW | P2 |
| F7 | No "save without search" | LOW | Post-wizard prompt | LOW | P3 |
| F8 | No CSV export | LOW | Export flag | MEDIUM | P3 |

---

## Priority Recommendations

### P0: Eliminate Application Friction (F1)
**Impact/Effort Ratio:** 10/10

**What to build:**
1. "Copy URL" button on each job card
2. "Copy All Recommended" batch action
3. Optional: Application status tracking UI

**Why prioritize:** Daily workflow friction. Active job seekers apply to 5-10 jobs per search. Current flow wastes 5-10 minutes per day on copy-paste. With 100 users searching daily, that's 500-1000 minutes saved **per day**.

**Implementation path:**
- Phase 1: Copy URL button (1-2 hours)
- Phase 2: Batch copy (1 hour)
- Phase 3: Status tracking UI (4-6 hours)

**Success metric:** User reports "I applied to 5 jobs in under 2 minutes."

---

### P1: Enable Profile Iteration (F2)
**Impact/Effort Ratio:** 8/10

**What to build:**
1. Profile preview on startup
2. Quick edit menu (jump to specific fields)
3. CLI flags for common updates

**Why prioritize:** Blocks users from refining their searches. During first week of use, users typically adjust dealbreakers, min_score, and skills 3-5 times. Current wizard friction discourages experimentation.

**Implementation path:**
- Phase 1: Profile preview banner (30 minutes)
- Phase 2: Quick edit menu (3-4 hours)
- Phase 3: CLI update flags (2-3 hours)

**Success metric:** Users edit profiles 2x more frequently (measured via tracker.json).

---

### P1: Improve Report Scannability (F3)
**Impact/Effort Ratio:** 7/10

**What to build:**
1. Sticky summary bar with quick navigation
2. "Show NEW only" filter toggle
3. Collapsible table sections by score range
4. Row background colors for visual hierarchy

**Why prioritize:** Every search run requires scanning the report. With 20+ results, users waste 30-60 seconds finding relevant jobs. Low implementation effort for immediate UX gain.

**Implementation path:**
- Phase 1: Sticky bar + filter (2 hours)
- Phase 2: Collapsible sections (2 hours)
- Phase 3: Row colors (1 hour)

**Success metric:** Time to identify top 3 jobs drops from 60s to 15s.

---

### P2: Polish and Context (F4, F5, F6)
**Impact/Effort Ratio:** 5/10

Low-effort improvements that remove minor confusion:
- Enhanced profile preview (30 min)
- Manual URL explanation (15 min)
- Table visual hierarchy (30 min)

**Why prioritize:** Quick wins. Bundle these into a "UX polish" sprint.

---

### P3: Advanced Features (F7, F8)
**Impact/Effort Ratio:** 3/10

Nice-to-have enhancements for specific use cases:
- Save without search (1 hour)
- CSV export (3-4 hours)

**Why defer:** Edge cases. F7 helps first-time users testing setup. F8 helps users with external ATS. Both are valuable but serve narrow audiences.

---

## Implementation Roadmap

### Sprint 1: Application Friction (2 weeks)
- **Goal:** Eliminate copy-paste overhead
- **Deliverables:**
  - Copy URL button on job cards
  - Batch copy for recommended jobs
  - Application status tracking (optional)
- **Success criteria:** 80% of users use copy buttons

### Sprint 2: Profile Iteration (1.5 weeks)
- **Goal:** Make profile editing fast
- **Deliverables:**
  - Profile preview on startup
  - Quick edit menu
  - CLI update flags
- **Success criteria:** Profile edits increase 2x

### Sprint 3: Report UX (1 week)
- **Goal:** Surface high-value jobs faster
- **Deliverables:**
  - Sticky summary bar
  - NEW-only filter
  - Collapsible sections
  - Visual hierarchy
- **Success criteria:** Time-to-top-3-jobs < 20s

### Sprint 4: Polish (3 days)
- **Goal:** Remove minor friction
- **Deliverables:**
  - Enhanced banner
  - Manual URL context
  - Table colors
- **Success criteria:** No user confusion in testing

---

## Design Patterns and Principles

### CLI UX Principles Applied
Based on [CLI Guidelines](https://clig.dev/) and [CLI UX Best Practices](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays):

1. **Provide feedback for long-running operations:** ✅ Already implemented (source-by-source progress)
2. **Validate early, fail fast:** ✅ Wizard has inline validation
3. **Enable recovery from errors:** ✅ Wizard has /back navigation
4. **Respect user's time:** ⚠️ Needs improvement (F2: profile editing)
5. **Make common tasks easy:** ⚠️ Needs improvement (F1: application flow)

### Web Report UX Principles
Based on [Scannability Best Practices](https://www.toptal.com/designers/web/ui-design-best-practices):

1. **Break up text into segments:** ✅ Cards for recommended, tables for all results
2. **Use visual hierarchy:** ⚠️ Needs improvement (F6: table lacks hierarchy)
3. **Place important info in visible zones:** ⚠️ Needs improvement (F3: buried in tables)
4. **Keep reports scannable:** ⚠️ Needs improvement (F3: requires scrolling)

### Job Search Workflow Principles
Based on [Job Application Automation](https://scale.jobs/blog/5-steps-to-automate-job-applications):

1. **Reduce multi-step flows:** ⚠️ Needs improvement (F1: 5 clicks per application)
2. **Batch actions where possible:** ⚠️ Needs improvement (F1: copy all URLs)
3. **Provide status tracking:** ❌ Not implemented (F1: status UI)
4. **Maintain quality controls:** ✅ Scoring system prevents spam

---

## Testing Strategy

### Usability Testing Protocol

**Test 1: First-Run Experience**
- Task: Complete wizard and run first search
- Metrics: Time to completion, error rate, back navigation usage
- Success: < 5 minutes, < 2 errors

**Test 2: Daily Search Workflow**
- Task: Run search, find top 3 jobs, copy URLs
- Metrics: Time to copy URLs, clicks required
- Success: < 2 minutes total, < 2 clicks per job

**Test 3: Profile Editing**
- Task: Update skills and dealbreakers
- Metrics: Time to update, steps required
- Success: < 1 minute, < 5 prompts

**Test 4: Report Scanning**
- Task: Find all NEW jobs with score 3.5+
- Metrics: Time to scan, accuracy
- Success: < 30 seconds, 100% accurate

### A/B Testing Opportunities

**Test: Copy Button Placement**
- Variant A: Button next to "View" link
- Variant B: Icon-only button below job title
- Variant C: Context menu (right-click)
- Metric: Usage rate

**Test: Profile Edit Entry Point**
- Variant A: Main menu option
- Variant B: CLI flag (--edit-profile)
- Variant C: Inline prompt during search
- Metric: Edit frequency

---

## Accessibility Considerations

### WCAG 2.1 Compliance for HTML Reports

**Current state:**
- ✅ Semantic HTML (cards, tables, headings)
- ✅ Color contrast (Bootstrap 5 defaults)
- ✅ Dark mode support (prefers-color-scheme)
- ⚠️ Missing: Focus indicators on interactive elements
- ⚠️ Missing: ARIA labels on copy buttons
- ⚠️ Missing: Keyboard navigation for filters

**Recommendations:**
1. Add `aria-label` to copy buttons: `<button aria-label="Copy job URL for {title}">`
2. Add focus styles: `.btn:focus { outline: 2px solid #0d6efd; }`
3. Add keyboard shortcuts: `Alt+C` for copy, `Alt+N` for show NEW only
4. Add skip links: `<a href="#recommended" class="sr-only sr-only-focusable">Skip to top jobs</a>`

### Terminal Accessibility

**Current state:**
- ✅ Color-aware output (detects TTY)
- ✅ Plain text fallback
- ✅ Screen reader compatible (no ASCII art overload)

**No changes needed**—wizard output is already accessible.

---

## Competitive Analysis

### Similar Tools Reviewed

**Tool:** Simplify Copilot ([Chrome Extension](https://chromewebstore.google.com/detail/simplify-copilot-autofill/pbanhockgagggenencehbnadejlgchfc))
- **Strength:** One-click apply with autofill
- **Weakness:** Browser-only, requires manual site visits
- **Learning:** Job Radar's report should enable one-click workflows

**Tool:** CLI job boards (hn-hiring-cli, remote-jobs-cli)
- **Strength:** Terminal-native browsing
- **Weakness:** No scoring, no profile matching
- **Learning:** Job Radar's scoring is a key differentiator—surface it better

**Tool:** LinkedIn Job Search
- **Strength:** Native application tracking, "Easy Apply" button
- **Weakness:** Walled garden, no cross-source aggregation
- **Learning:** Status tracking UI would match user expectations

---

## Technical Debt and Risks

### Risks of Copy Button Implementation

**Risk 1: Clipboard API browser support**
- **Mitigation:** Feature detection + fallback to "select and copy" instructions
- **Code:** `if (!navigator.clipboard) { /* show manual copy UI */ }`

**Risk 2: HTTPS requirement**
- **Issue:** Clipboard API requires HTTPS (or localhost)
- **Impact:** File:// URLs work on localhost, but report.py serves file:// directly
- **Mitigation:** None needed—Clipboard API works on file:// for local files

**Risk 3: User expects persistence**
- **Issue:** Copy button state doesn't persist across report regeneration
- **Mitigation:** Use localStorage to track "copied" state per job

### Risks of Status Tracking UI

**Risk 1: Data persistence**
- **Issue:** tracker.json tracks status, but UI reads localStorage
- **Mitigation:** Sync localStorage → tracker.json on status change (Python backend required)

**Risk 2: Multi-device sync**
- **Issue:** Status tracked locally doesn't sync across devices
- **Mitigation:** Document limitation, suggest cloud sync tools (Dropbox, iCloud)

---

## Appendix: UX Research Sources

### CLI Tool Best Practices
- [Command Line Interface Guidelines](https://clig.dev/) - Comprehensive CLI design guide
- [UX Patterns for CLI Tools](https://www.lucasfcosta.com/blog/ux-patterns-cli-tools) - Practical patterns
- [CLI UX Best Practices: Progress Displays](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays) - Progress feedback patterns

### Job Search Workflow Research
- [AI Auto Apply Guide (2026)](https://careery.pro/blog/ai-auto-apply-for-jobs-guide) - One-click apply analysis
- [How to Automate Job Applications](https://scale.jobs/blog/5-steps-to-automate-job-applications) - Best practices for automation
- [User Friction Guide (2025)](https://survicate.com/blog/user-friction/) - Friction identification

### Web UX and Scannability
- [UI Design Best Practices for Scannability](https://www.toptal.com/designers/web/ui-design-best-practices) - Visual hierarchy
- [10 Usability Findings](https://www.smashingmagazine.com/2009/09/10-useful-usability-findings-and-guidelines/) - Research-backed guidelines
- [Web Usability Guidelines](https://www.userfocus.co.uk/resources/guidelines.html) - 247 guidelines

### Copy-Paste Friction Research
- [Microsoft Word Paste-to-Link (2026)](https://www.webpronews.com/microsoft-word-2026-update-paste-to-link-feature-boosts-efficiency/) - Modern clipboard UX
- [Copy-Paste Hijacking](https://lifetips.alibaba.com/tech-efficiency/how-to-disable-copy-and-paste-hijacking-web-sites) - Friction analysis

### Questionary and Terminal Wizards
- [Questionary Library (GitHub)](https://github.com/tmbo/questionary) - Python CLI prompts
- [10+ Best Python CLI Libraries (2026)](https://medium.com/@wilson79/10-best-python-cli-libraries-for-developers-picking-the-right-one-for-your-project-cefb0bd41df1) - Library comparison

---

## Confidence Assessment

| Area | Level | Reasoning |
|------|-------|-----------|
| Code Analysis | HIGH | Reviewed wizard.py, report.py, search.py, tracker.py |
| CLI UX Patterns | HIGH | Research from CLI Guidelines, Evil Martians, clig.dev |
| Job Search Workflows | MEDIUM | Research from 2026 automation guides, but no direct Job Radar user interviews |
| Web Report UX | HIGH | Bootstrap 5 implementation + research-backed scannability principles |
| Frequency Estimates | MEDIUM | Based on typical job search cadence (5-10 applications/day) but not Job Radar-specific telemetry |

**No user interviews conducted**—recommendations based on code analysis + UX research. User testing would validate impact estimates.

---

## Conclusion

Job Radar has a solid technical foundation and smooth wizard experience. The primary UX opportunity is **reducing application friction**—the report-to-application transition is where users spend the most time. Implementing copy buttons and batch actions would eliminate 5-10 minutes of daily overhead for active job seekers.

Secondary opportunities in profile iteration and report scannability are lower effort and provide immediate quality-of-life improvements.

All recommendations maintain Job Radar's core strengths: offline-first operation, clean terminal UX, and privacy-focused design (no cloud sync, no tracking).
