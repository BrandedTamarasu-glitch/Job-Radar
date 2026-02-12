# Feature Research: CLI Profile Management

**Domain:** CLI developer tools (configuration management)
**Researched:** 2026-02-11
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| View current profile | Standard in all CLI config tools (git config list, gh config list, aws configure list) | LOW | Display all fields in human-readable format |
| Get single field value | Common pattern for scripting (git config get, gh config get, aws configure get) | LOW | Return just the value, no formatting for pipe-ability |
| Set single field value | Essential for quick updates without wizard (aws configure set, git config set, gh config set) | LOW | Update one value, persist immediately |
| Edit in $EDITOR | Power user expectation (git config --edit) | MEDIUM | Open config JSON in editor, validate on save |
| Field validation | Config tools reject invalid values immediately | MEDIUM | Validate data types, required fields, format constraints |
| --help for config commands | CLI standard - users expect help text | LOW | Document all flags and subcommands |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Preview on startup | Shows current settings without extra command - reduces friction | LOW | 2-3 line summary before main action runs |
| Diff preview before save | Confidence in changes (kubectl diff, terraform plan pattern) | MEDIUM | Show old vs new values before confirming |
| Interactive edit mode | Guided updates without full wizard (npm init, aws configure) | MEDIUM | Prompt only for fields user wants to change |
| Validation with helpful errors | Better than generic "invalid value" messages | MEDIUM | Context-specific guidance (e.g., "min_score must be 0-100") |
| Undo last change | Safety net for mistakes | MEDIUM | Store previous version, allow rollback |
| Multiple profiles support | Context switching (aws --profile, git config --local) | HIGH | Load different configs for different use cases |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| GUI config editor | "Easier than CLI" | Scope creep, maintenance burden, defeats CLI purpose | Use --edit to open in user's preferred editor |
| Auto-update profile during run | "Convenience" | Hidden side effects, unclear when changes happen | Explicit --set flags only, require confirmation |
| Unlimited config history | "Track all changes" | Storage bloat, complexity | Store only last version for undo, not full history |
| Profile templates/presets | "Common configurations" | Premature optimization, unknown use cases | Wait for user feedback on common patterns |
| Real-time validation during typing | "Immediate feedback" | Complex for CLI, not expected behavior | Validate on save/submit only |

## Feature Dependencies

```
[View Profile] ──────────────> [No dependencies]
    │
    └──enhances──> [Preview on Startup]

[Set Single Field]
    ├──requires──> [Field Validation]
    └──enhances──> [Diff Preview]

[Edit in $EDITOR]
    ├──requires──> [Field Validation]
    └──enhances──> [Diff Preview]

[Interactive Edit Mode]
    ├──requires──> [Field Validation]
    ├──requires──> [View Profile] (to show current values)
    └──conflicts──> [Non-interactive/scripting use]

[Undo Last Change]
    └──requires──> [Version Storage] (simple: just previous version)
```

### Dependency Notes

- **Preview on Startup enhances View Profile:** Automatically shows profile without explicit command
- **Field Validation required by Set/Edit:** Both modes need validation to prevent bad data
- **Diff Preview enhances Set/Edit:** Shows changes before applying them
- **Interactive Edit conflicts with scripting:** Must detect TTY and disable prompts in non-interactive environments

## MVP Definition

### Launch With (v1 - This Milestone)

Minimum viable profile management — what's needed to reduce friction vs manual JSON editing.

- [x] **View profile** (`--show-profile` or `profile show`) — Users need to see current settings without opening JSON
- [x] **Set single field** (`--set-field key=value`) — Core use case: update 1-2 fields without full wizard
- [x] **Field validation** — Prevent invalid data (wrong types, out of range values)
- [x] **Preview on startup** (optional, 2-3 lines) — Awareness of current profile state
- [ ] **Basic help text** — Document new flags/commands

**Rationale:** These 4-5 features solve the core friction: "I want to update my min_score without re-running the wizard or editing JSON manually."

### Add After Validation (v1.x)

Features to add once core profile updates are working.

- [ ] **Interactive edit mode** (`--edit-profile` interactive prompts) — Better UX than --set-field for multiple changes, trigger: users request easier multi-field updates
- [ ] **Diff preview** (show old→new before save) — Safety feature, trigger: users make mistakes and want confidence
- [ ] **Edit in $EDITOR** (`--edit-profile` opens JSON) — Power user feature, trigger: advanced users request direct access
- [ ] **Get single field** (`--get-field key`) — Scripting support, trigger: users want to script against profile values

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Undo last change** — Nice safety net, defer: complexity doesn't justify v1, wait for actual mistakes in wild
- [ ] **Multiple profiles** (`--profile name`) — Advanced feature, defer: unclear if users need context switching for job search
- [ ] **Profile export/import** — Sharing configs, defer: wait for collaboration use case validation

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| View profile | HIGH | LOW | P1 |
| Set single field | HIGH | LOW | P1 |
| Field validation | HIGH | MEDIUM | P1 |
| Preview on startup | MEDIUM | LOW | P1 |
| Help text | HIGH | LOW | P1 |
| Interactive edit mode | MEDIUM | MEDIUM | P2 |
| Diff preview | MEDIUM | MEDIUM | P2 |
| Edit in $EDITOR | MEDIUM | LOW | P2 |
| Get single field | LOW | LOW | P2 |
| Undo last change | LOW | MEDIUM | P3 |
| Multiple profiles | LOW | HIGH | P3 |
| Profile export/import | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch (solves core friction)
- P2: Should have, add when possible (enhances UX)
- P3: Nice to have, future consideration (unclear demand)

## CLI Tool Patterns Analysis

### How Leading Tools Handle Config

| Tool | View All | Get Single | Set Single | Edit | Interactive |
|------|----------|------------|------------|------|-------------|
| **git** | `config --list` | `config --get key` | `config --set key value` | `config --edit` | No (all explicit) |
| **gh** | `config list` | `config get key` | `config set key value` | Opens editor via `editor` setting | No |
| **aws** | `configure list` | `configure get key` | `configure set key value` | N/A | `configure` (wizard) |
| **npm** | `config list` | `config get key` | `config set key value` | `config edit` | `init` (separate) |

### Common Patterns Identified

**1. Verb-noun command structure:**
- Modern tools: `<tool> config <verb> [args]` (gh, aws)
- Classic tools: `<tool> config --<verb>` (git)
- **Recommendation:** Use subcommand style (`profile show`, `profile set`) - more discoverable with --help

**2. Interactive vs non-interactive:**
- **Best practice:** Support both, detect TTY
- Interactive for initial setup (wizard)
- Flags for daily updates and scripting
- **Never require prompts** when stdin is not TTY

**3. Configuration hierarchy:**
- Flags > Environment > Project config > User config > System
- **Job-Radar context:** Single user tool, so hierarchy is: Flags > Project-level profile
- `--profile path/to/profile.json` for override already exists

**4. Validation timing:**
- Validate immediately on set (don't persist bad data)
- Show clear error messages with guidance
- Example: "min_score must be 0-100, got 150"

**5. Preview/dry-run patterns:**
- Destructive operations show diff before applying
- Examples: `kubectl diff`, `terraform plan`, `pulumi preview --diff`
- **Job-Radar application:** Show old→new values before saving profile changes

## Workflow Examples

### Current Friction (Before Profile Management)

```bash
# User wants to update min_score from 75 to 80

# Option 1: Re-run wizard (tedious, 10+ questions)
python job_radar.py  # Goes through full wizard again

# Option 2: Manual JSON edit (error-prone)
nano ~/.job-radar/profile.json
# Find the field, edit carefully, save, hope it's valid JSON
```

### Proposed Workflow (After Profile Management)

```bash
# Quick single-field update
python job_radar.py profile set min_score=80
# Profile updated: min_score 75 → 80

# View current settings
python job_radar.py profile show
# Shows formatted profile

# Interactive multi-field edit (v1.x)
python job_radar.py profile edit
# Prompts:
# Update min_score? (75): 80
# Update skills? (Python, Django): Python, Django, FastAPI
# ... (only changed fields)
# Preview changes and confirm

# Power user: direct edit (v1.x)
python job_radar.py profile edit --open
# Opens ~/.job-radar/profile.json in $EDITOR
# Validates on save
```

## Sources

**Official Documentation (HIGH confidence):**
- [GitHub CLI: gh config](https://cli.github.com/manual/gh_config) - Config management subcommands (list, get, set)
- [AWS CLI: configure set](https://docs.aws.amazon.com/cli/latest/reference/configure/set.html) - Single-field update pattern
- [Git: git-config](https://git-scm.com/docs/git-config) - Classic CLI config tool patterns
- [Command Line Interface Guidelines](https://clig.dev/) - Interactive vs non-interactive best practices

**Community Best Practices (MEDIUM confidence):**
- [UX patterns for CLI tools](https://www.lucasfcosta.com/blog/ux-patterns-cli-tools) - Interactive wizard vs flags
- [CLI Design Best Practices](https://codyaray.com/2020/07/cli-design-best-practices) - Configuration hierarchy
- [CLI Tools Preview/Dry-run Patterns](https://nickjanetakis.com/blog/cli-tools-that-support-previews-dry-runs-or-non-destructive-actions) - Diff preview patterns

**2026 Ecosystem Research (MEDIUM confidence):**
- [kubectl diff preview](https://oneuptime.com/blog/post/2026-01-25-kubectl-diff-preview-changes/view) - Preview changes pattern
- [Azure CLI Configuration](https://learn.microsoft.com/en-us/cli/azure/azure-cli-configuration) - Modern config management

---
*Feature research for: CLI Profile Management (Job-Radar milestone)*
*Researched: 2026-02-11*
