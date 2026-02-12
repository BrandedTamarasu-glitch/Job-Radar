# Feature Research: Desktop GUI Launcher

**Domain:** Desktop GUI wrapper for CLI job search tool
**Researched:** 2026-02-12
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Profile creation form | GUI users expect forms, not CLI wizards | LOW | Replace questionary prompts with labeled input fields |
| File upload dialog for resume | Standard desktop pattern for file selection | LOW | Use native OS file picker (tkinter.filedialog.askopenfilename) |
| Search configuration panel | Users expect to set parameters before running | LOW | Date pickers, numeric input, checkboxes for flags |
| Run/Start button | Primary action must be obvious and single-click | LOW | Clear CTA, disabled state while running |
| Progress feedback | Visual indication during long operations (6 sources queried) | MEDIUM | Determinate or indeterminate progress bar with status text |
| Auto-open results in browser | CLI already does this, users expect same behavior | LOW | Use webbrowser.open() after search completes |
| View current profile | See existing settings without editing | LOW | Read-only display or pre-filled form |
| Edit profile without wizard | Update settings after initial creation | MEDIUM | Same form as creation, pre-populated with current values |
| Input validation | Prevent invalid data before submission | MEDIUM | Client-side validation with helpful error messages |
| Window state persistence | Remember size, position across sessions | MEDIUM | Save to config file on close, restore on open |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Live CLI output display | Show real-time progress from underlying CLI | MEDIUM | ScrolledText widget with threading, captures stdout/stderr |
| Quick re-run with last settings | One-click to repeat previous search | LOW | Remember last search params, "Run Again" button |
| Date range presets | Common filters (Today, Last 7 Days, Last 30 Days) | LOW | Dropdown or button group for quick selection |
| Validation preview | Show what will be searched before running | LOW | Summary panel: "Searching 6 sources from X to Y with score >= Z" |
| Resume path indicator | Show currently uploaded resume filename | LOW | Label showing basename, change button to re-upload |
| Search history | View past searches and their parameters | MEDIUM | Store search metadata, display in list/table |
| Keyboard shortcuts | Power users expect Ctrl+Enter to run, Esc to cancel | LOW | Bind accelerators to primary actions |
| Minimal UI mode | Hide advanced options by default, show on expand | MEDIUM | Collapsible sections or tabbed interface |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Inline results display | "Why leave the app?" | Duplicates existing HTML report, high complexity, defeats purpose of launcher | Keep auto-open browser behavior, GUI is launcher not viewer |
| Real-time job filtering UI | "Filter without re-running" | Requires parsing HTML output, couples GUI to report format | Use HTML report's built-in interactive filtering |
| Custom browser selection | "I use Firefox not Chrome" | OS already handles default browser, unnecessary config | Use webbrowser.open() which respects OS default |
| Advanced CLI flag exposure | "Power users want all flags" | GUI becomes cluttered, defeats simplicity | Keep CLI for power users, GUI for common workflows |
| Profile templates/presets | "Job types: SWE, DevOps, etc." | Premature optimization, unclear patterns | Wait for user feedback, manual profile copy for now |
| Minimize to system tray | "Keep running in background" | Search is one-shot operation, not daemon | Close after opening results, no background process |
| Multi-profile switching | "Different searches for different roles" | High complexity, unclear demand for GUI users | Single profile, CLI supports --profile for advanced use |

## Feature Dependencies

```
[Profile Creation Form]
    ├──requires──> [Input Validation]
    └──requires──> [File Upload Dialog] (optional resume)

[Search Configuration Panel]
    ├──requires──> [Input Validation]
    └──enhances──> [Validation Preview]

[Run Button]
    ├──requires──> [Profile Creation Form] (must exist first)
    ├──triggers──> [Progress Feedback]
    └──triggers──> [Auto-open Browser]

[Progress Feedback]
    ├──requires──> [Run Button] (initiates process)
    └──enhances──> [Live CLI Output Display]

[Live CLI Output Display]
    ├──requires──> [Progress Feedback] (base requirement)
    └──requires──> [Threading] (non-blocking UI)

[Edit Profile]
    ├──requires──> [Profile Creation Form] (reuses same form)
    ├──requires──> [View Current Profile] (load existing data)
    └──conflicts──> [Multiple Profile Switching] (single profile model)

[Window State Persistence]
    └──no dependencies (independent feature)

[Search History]
    └──enhances──> [Quick Re-run] (populate from history)

[Keyboard Shortcuts]
    └──enhances──> [Run Button] (alternate trigger)
```

### Dependency Notes

- **Profile Creation must precede Search:** User must have profile before running search
- **Threading required for Live Output:** UI must remain responsive during subprocess execution
- **Form reuse for Edit:** Same form component serves creation and editing modes
- **History enhances Re-run:** History provides source of previous searches to restore
- **CLI output depends on Progress:** Base progress indicator must exist before adding live output

## MVP Definition

### Launch With (GUI v1 - This Milestone)

Minimum viable GUI launcher — what's needed for basic users to avoid CLI entirely.

- [ ] **Profile creation form** — GUI replacement for questionary wizard (name, email, location, skills, titles, min_score)
- [ ] **File upload dialog** — Native file picker for optional resume PDF
- [ ] **Search configuration panel** — Date range (from/to), min score override, new-only checkbox
- [ ] **Run search button** — Primary action, clear visual state (enabled/disabled/running)
- [ ] **Progress indicator** — Indeterminate progress bar with "Searching 6 sources..." text
- [ ] **Auto-open browser** — Launch HTML report when complete (existing behavior)
- [ ] **Edit profile access** — Button/menu to modify existing profile
- [ ] **Input validation** — Client-side checks for required fields, valid formats, range limits
- [ ] **Basic window layout** — Organized sections, clear visual hierarchy

**Rationale:** These 9 features provide complete parity with CLI for basic workflows. User never needs terminal for standard job searches.

### Add After Validation (v1.x)

Features to add once core GUI functionality is working.

- [ ] **Live CLI output display** — ScrolledText showing real-time progress from underlying CLI, trigger: users want visibility into what's happening
- [ ] **Date range presets** — Quick buttons for common ranges (Today, Last 7 Days, Last 30 Days), trigger: repetitive date entry frustration
- [ ] **Quick re-run button** — One-click repeat with last parameters, trigger: users run same search multiple times
- [ ] **Validation preview** — Summary of search before running, trigger: users want confirmation of settings
- [ ] **Resume path indicator** — Show current resume filename if uploaded, trigger: users forget if they uploaded resume
- [ ] **Window state persistence** — Remember size/position, trigger: users annoyed by reset layout
- [ ] **Keyboard shortcuts** — Ctrl+Enter to run, Esc to close dialogs, trigger: power users request efficiency

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Search history** — View and restore past searches, defer: unclear if GUI users need history vs just re-running
- [ ] **Minimal UI mode** — Collapsible advanced options, defer: wait to see if UI feels cluttered first
- [ ] **Profile export/import** — Share profiles across machines, defer: wait for collaboration use case validation
- [ ] **Custom theming** — Dark mode, color schemes, defer: nice-to-have, not core functionality
- [ ] **Notification on completion** — OS notification when search finishes, defer: searches are fast (<1 min), unclear value

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Profile creation form | HIGH | MEDIUM | P1 |
| File upload dialog | HIGH | LOW | P1 |
| Search config panel | HIGH | MEDIUM | P1 |
| Run button | HIGH | LOW | P1 |
| Progress indicator | HIGH | MEDIUM | P1 |
| Auto-open browser | HIGH | LOW | P1 |
| Edit profile access | HIGH | LOW | P1 |
| Input validation | HIGH | MEDIUM | P1 |
| Basic window layout | HIGH | MEDIUM | P1 |
| Live CLI output | MEDIUM | MEDIUM | P2 |
| Date range presets | MEDIUM | LOW | P2 |
| Quick re-run | MEDIUM | LOW | P2 |
| Validation preview | MEDIUM | LOW | P2 |
| Resume path indicator | LOW | LOW | P2 |
| Window state persistence | MEDIUM | MEDIUM | P2 |
| Keyboard shortcuts | LOW | LOW | P2 |
| Search history | LOW | MEDIUM | P3 |
| Minimal UI mode | LOW | MEDIUM | P3 |
| Profile export/import | LOW | MEDIUM | P3 |
| Custom theming | LOW | MEDIUM | P3 |
| Completion notifications | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for launch (core GUI functionality)
- P2: Should have, add when possible (enhances UX)
- P3: Nice to have, future consideration (unclear demand)

## GUI Wrapper Pattern Analysis

### How GUI Wrappers Typically Work

Based on research into CLI wrapper tools and desktop GUI patterns:

**Architecture Pattern:**
- GUI is separate layer, calls CLI as subprocess
- Settings managed in config files, not hardcoded in GUI
- Output captured via stdout/stderr streaming
- Browser launch via OS default handler

**User Flow:**
1. **First run:** Profile creation form (one-time setup)
2. **Subsequent runs:** Search config → Run → Progress → Results in browser
3. **Profile updates:** Edit form (same as creation, pre-filled)

**Progress Feedback:**
- Indeterminate progress (spinning/pulsing) when duration unknown
- Determinate progress (0-100%) when endpoint measurable
- Status text describing current operation
- Best practice: Show what's happening ("Querying Indeed...") not just "Please wait"

**File Upload:**
- Native OS file picker dialog
- Filter by file type (.pdf for resumes)
- Display selected filename after upload
- Validation: check file exists, readable, correct type

**Browser Launch:**
- Use `webbrowser.open()` in Python (respects OS default)
- Security: Validate file paths to prevent injection
- Best practice: Confirm action with user if from external data

### Wizard vs Form Design

**Traditional Wizard (Multi-step):**
- Used when process is unfamiliar or complex
- Progress indicator showing steps
- Back/Next navigation
- Best for: Infrequent operations, learning curve

**Single Form (All-at-once):**
- Used when fields are familiar or few
- All inputs visible at once
- Single Submit button
- Best for: Frequent operations, power users

**Recommendation for Job-Radar:**
- **Profile creation (first run):** Single form with clear sections, not multi-step wizard
  - Rationale: Only ~6-8 fields, users familiar with job applications, no complex branching
  - Use visual grouping: "Personal Info" section, "Preferences" section
  - Optional fields clearly marked
- **Search config:** Simple panel, 3-4 controls max
  - Date range, score override, new-only toggle
  - Always visible, not hidden in wizard

### State Persistence Patterns

**What to persist:**
- Window size and position (UX continuity)
- Last search parameters (quick re-run)
- Profile location if non-default (rare)

**Where to store:**
- Per-user config directory (e.g., `~/.job-radar/gui-settings.json`)
- NOT in registry (cross-platform issues)
- NOT in same file as profile (separation of concerns)

**When to save:**
- On window close (size/position)
- On successful search (parameters)
- NOT continuously (performance, file wear)

**Validation on load:**
- Check values are in valid range (prevent crash)
- Fall back to defaults if corrupted
- Critical: Malformed settings shouldn't prevent startup

## GUI Framework Feature Comparison

| Feature | Tkinter | PyQt5/6 | wxPython | PySimpleGUI |
|---------|---------|---------|----------|-------------|
| **File dialog** | filedialog.askopenfilename() | QFileDialog.getOpenFileName() | wx.FileDialog | sg.popup_get_file() |
| **Progress bar** | ttk.Progressbar | QProgressBar | wx.Gauge | sg.ProgressBar |
| **Forms** | Manual grid/pack layout | QFormLayout | wx.FlexGridSizer | Auto-layout columns |
| **Threading** | threading.Thread | QThread | wx.CallAfter | Works with threading |
| **Native look** | Basic (themed with ttk) | Full native | Full native | Themed |
| **Browser launch** | webbrowser.open() | webbrowser.open() | webbrowser.open() | webbrowser.open() |

**Note:** All frameworks support the core features needed. Choice is based on other factors (dependencies, complexity, maintenance).

## Workflow Examples

### Current CLI Workflow

```bash
# First run: Terminal wizard
python job_radar.py
# 10+ questions in terminal

# Run search with flags
python job_radar.py --from 2026-02-01 --to 2026-02-12 --min-score 75 --new-only

# Update profile: Manual JSON edit or re-run wizard
nano ~/.job-radar/profile.json
```

### Proposed GUI Workflow

```
# First run: GUI form
[Launch Job-Radar GUI]
┌─────────────────────────────────────┐
│ Create Your Job Search Profile     │
├─────────────────────────────────────┤
│ Name:        [Jane Doe            ] │
│ Email:       [jane@example.com    ] │
│ Location:    [San Francisco, CA   ] │
│                                     │
│ Skills:      [Python, Django, React]│
│              (comma-separated)      │
│                                     │
│ Job Titles:  [Software Engineer,   ]│
│              [Senior Developer     ]│
│                                     │
│ Min Score:   [75] (0-100)          │
│                                     │
│ Resume (opt): [Choose File]         │
│               resume.pdf            │
│                                     │
│          [Create Profile]           │
└─────────────────────────────────────┘

# Subsequent runs: Search panel
┌─────────────────────────────────────┐
│ Job Search Configuration            │
├─────────────────────────────────────┤
│ Date Range:                         │
│   From: [2026-02-01] To: [2026-02-12]│
│   Presets: [Today][Last 7d][Last 30d]│
│                                     │
│ Min Score: [75] (default: 75)       │
│                                     │
│ [✓] New listings only               │
│ [✓] Skip cache                      │
│                                     │
│          [Run Search]               │
│      [Edit Profile]                 │
└─────────────────────────────────────┘

# During search: Progress
┌─────────────────────────────────────┐
│ Searching Job Boards...             │
├─────────────────────────────────────┤
│ [=====>                    ] 25%    │
│ Querying LinkedIn...                │
│                                     │
│ Sources: Indeed ✓, LinkedIn ⏳      │
│          Dice ⏳, GitHub ⏳         │
│          RemoteOK ⏳, Otta ⏳       │
│                                     │
│          [Cancel]                   │
└─────────────────────────────────────┘

# After search: Auto-open browser
[Browser opens with HTML report]
[GUI shows success message]
┌─────────────────────────────────────┐
│ Search Complete!                    │
├─────────────────────────────────────┤
│ Found 47 jobs matching your profile │
│ Report opened in browser            │
│                                     │
│     [Run Again] [Edit Profile]      │
│              [Close]                │
└─────────────────────────────────────┘
```

### Edit Profile Workflow

```
# Click "Edit Profile" button
[Reuses creation form, pre-filled with current values]
┌─────────────────────────────────────┐
│ Edit Your Job Search Profile       │
├─────────────────────────────────────┤
│ Name:        [Jane Doe            ] │
│ Email:       [jane@example.com    ] │
│ Location:    [San Francisco, CA   ] │
│                                     │
│ Skills:      [Python, Django, React,]│
│              [FastAPI             ] │ ← Modified
│                                     │
│ Job Titles:  [Software Engineer,   ]│
│              [Senior Developer     ]│
│                                     │
│ Min Score:   [80]                  │ ← Modified
│                                     │
│ Resume:      [resume.pdf          ] │
│              [Change File]          │
│                                     │
│     [Save Changes] [Cancel]         │
└─────────────────────────────────────┘
```

## Desktop GUI Job Search Tools Comparison

| Feature | Our Approach | Typical Job Apps | Rationale |
|---------|-------------|------------------|-----------|
| **Results display** | Browser (external) | In-app list/grid | We're a launcher, not full app; HTML report already rich |
| **Search config** | Simple panel (dates, score) | Complex filters (salary, remote, etc.) | Filtering done in HTML report, not pre-search |
| **Profile management** | Single profile, edit form | Multiple profiles, switching | Simplicity; CLI handles multi-profile for power users |
| **Progress feedback** | Progress bar + status text | Spinning loader | 6 sources = measurable progress (0%, 17%, 33%...) |
| **Resume upload** | Optional, file picker | Often required, paste or upload | We extract from PDF, not required for search |
| **Application tracking** | N/A | Built-in feature | Out of scope; we aggregate, not track applications |
| **Saved searches** | Quick re-run with last params | Named saved searches | Simpler; most users have one search pattern |

**Key Insight:** Commercial job search apps are full-featured platforms (search, apply, track, network). Job-Radar GUI is a launcher — it configures and runs the CLI tool, then hands off to the browser. This scoping prevents feature bloat and maintains the tool's core value: aggregation and scoring.

## UX Principles for Minimal Launchers

Based on minimalist GUI design research:

**Simplicity:**
- Show only essential controls
- Hide advanced options (or defer to CLI)
- Use whitespace, don't cram UI

**Clarity:**
- Clear labels, no jargon
- Visual hierarchy (primary action prominent)
- Helpful validation messages

**Efficiency:**
- Minimize clicks to primary action (Run Search)
- Remember last settings for quick re-run
- Keyboard shortcuts for power users

**Feedback:**
- Always show what's happening (progress text)
- Confirm destructive actions (profile overwrite)
- Success/error states clearly visible

**Consistency:**
- Follow OS conventions (file dialogs, buttons)
- Consistent terminology (Profile, Search, Run)
- Predictable behavior (buttons do what they say)

## Sources

**Official Documentation (HIGH confidence):**
- [Python Tkinter Dialogs Documentation](https://docs.python.org/3/library/dialog.html) - Native file dialogs, standard GUI components
- [Microsoft: Progress Controls Guidelines](https://learn.microsoft.com/en-us/windows/apps/design/controls/progress-controls) - Determinate vs indeterminate progress patterns
- [Command Line Interface Guidelines](https://clig.dev/) - Best practices for CLI design that inform wrapper behavior

**GUI Wrapper Tools & Patterns (MEDIUM confidence):**
- [GUIwrapper - Cross-platform GUI wrapper](https://github.com/frodal/GUIwrapper) - Common patterns for CLI wrappers
- [UGUI: Universal GUI for CLI Applications](https://ugui.io/) - Approaches to wrapping CLI tools
- [Persistent Settings in Desktop Applications](https://info.erdosmiller.com/blog/persistent-settings-in-desktop-applications) - Configuration persistence patterns

**UX Design Patterns (MEDIUM confidence):**
- [NN/G: Wizards Design Recommendations](https://www.nngroup.com/articles/wizards/) - When to use wizards vs forms
- [Wizard UI Pattern Best Practices](https://lollypop.design/blog/2026/january/wizard-ui-design/) - Step structure, progress indicators (2026)
- [IxDF: UI Form Design 2026](https://www.interaction-design.org/literature/article/ui-form-design) - Modern form design best practices
- [Minimalist UI Design Principles](https://www.stan.vision/journal/minimalist-ui-design-how-less-is-more-in-web-design) - Simplicity, whitespace, clarity

**Job Aggregator Features (MEDIUM confidence):**
- [Best Job Board Aggregators Guide](https://www.chiefjobs.com/the-best-job-board-aggregators-in-the-us-a-comprehensive-guide/) - Common features in job aggregation tools (2026)
- [Top Job Search Apps 2026](https://www.eztrackr.app/blog/best-job-search-apps) - Feature comparison of leading apps

**Implementation Patterns (MEDIUM confidence):**
- [Run Process with Realtime Output to Tkinter](https://www.tutorialspoint.com/run-process-with-realtime-output-to-a-tkinter-gui) - Threading + subprocess for live output
- [PyQt External Programs with QProcess](https://www.pythonguis.com/tutorials/qprocess-external-programs/) - Streams and progress bars
- [Python File Upload Dialog Patterns](https://pythonguides.com/upload-a-file-in-python-tkinter/) - Tkinter file selection implementation

**Anti-Patterns & Pitfalls (MEDIUM-LOW confidence):**
- [User Interface Anti-Patterns](https://ui-patterns.com/blog/User-Interface-AntiPatterns) - Bloated UI, hide-and-hover pitfalls
- [UX Anti-Patterns of User Experience Design](https://www.ics.com/blog/anti-patterns-user-experience-design) - Common mistakes in desktop UX
- [Software Bloat - Wikipedia](https://en.wikipedia.org/wiki/Software_bloat) - Feature creep and bloat characteristics
- [UX Patterns for CLI Tools](https://lucasfcosta.com/2022/06/01/ux-patterns-cli-tools.html) - What to avoid when wrapping CLI tools

**Confidence Notes:**
- HIGH: Official Python/Microsoft documentation on GUI components and patterns
- MEDIUM: Recent (2026) articles on UX design, job aggregator features, established GUI wrapper projects
- MEDIUM-LOW: General anti-pattern articles (not GUI-specific), older sources

**Areas requiring phase-specific research:**
- Specific GUI framework choice (Tkinter vs PyQt vs wxPython) — needs architecture decision
- Threading implementation details — needs technical spike
- Cross-platform testing considerations — needs deployment planning

---
*Feature research for: Desktop GUI Launcher (Job-Radar milestone)*
*Researched: 2026-02-12*
