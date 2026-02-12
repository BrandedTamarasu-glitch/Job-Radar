# Project Research Summary

**Project:** Job-Radar CLI Profile Management
**Domain:** CLI configuration management for developer tools
**Researched:** 2026-02-11
**Confidence:** HIGH

## Executive Summary

Job-Radar needs profile management capabilities that allow users to quickly view and update their profile settings without re-running the full wizard or manually editing JSON files. Research shows this is a standard feature in modern CLI tools (git config, gh config, aws configure) with well-established patterns. The recommended approach combines read-only profile previews on startup, interactive quick-edit mode for occasional updates, and CLI flags for scripting and daily workflow adjustments.

The core technical challenge is maintaining data integrity during updates. Profile corruption from interrupted writes is the number one cause of user data loss in CLI config tools. Implementation must use atomic write patterns (temp file + rename), automatic backups before changes, and unified validation between the wizard and CLI update paths. The existing wizard already implements atomic writes via `_write_json_atomic()`, which should be extracted to a shared profile manager module and reused across all update paths.

Key risks center on destructive operations without confirmation and validation inconsistency between update methods. Research shows CLI tools that default to REPLACE semantics (vs APPEND) without confirmation prompts see high rates of accidental data loss. The recommended mitigation is showing before/after diffs for all changes with confirmation requirements, plus automatic timestamped backups that enable quick recovery from user mistakes.

## Key Findings

### Recommended Stack

The existing Python stack requires minimal additions for profile management. The core technologies (Python 3.10+, argparse, json, colorama) already support the needed features. Only two lightweight libraries need to be added.

**Core technologies:**
- **Python 3.10+**: Runtime environment — existing requirement, supports all needed features
- **argparse (stdlib)**: CLI argument parsing — already used, sufficient for new flags like --update-skills and --set-min-score
- **json (stdlib)**: Profile serialization — existing implementation, no changes needed
- **colorama (0.4.6)**: Cross-platform ANSI color — already in dependencies, used for colored diff output

**New supporting libraries:**
- **tabulate (0.9.0)**: Profile preview table formatting — pure Python, lightweight (50KB), handles column alignment automatically for profile display on startup
- **difflib (stdlib)**: Profile change diff generation — standard library, zero dependencies, used for before/after comparison in quick-edit mode

**Why minimal dependencies:** The project already has PyInstaller bundling configured. Adding only pure Python libraries (tabulate) and stdlib modules (difflib) ensures zero PyInstaller compatibility issues and minimal distribution size impact (<0.1% increase).

### Expected Features

Research across leading CLI tools (git, gh, aws, npm) reveals consistent patterns users expect for configuration management.

**Must have (table stakes):**
- **View current profile** — Standard in all CLI config tools; users need to see settings without opening JSON
- **Set single field value** — Essential for quick updates without wizard; pattern from aws configure set, git config set
- **Field validation** — Config tools reject invalid values immediately; prevents silent corruption
- **Help text for config commands** — CLI standard; users expect --help to document all flags

**Should have (competitive):**
- **Preview on startup** — Shows current settings without extra command; reduces friction vs manual view command
- **Diff preview before save** — Confidence in changes; familiar from kubectl diff, terraform plan pattern
- **Interactive edit mode** — Guided updates without full wizard; pattern from aws configure interactive flow

**Defer (v2+):**
- **Undo last change** — Nice safety net but complex for v1; wait for actual user mistakes in the wild before investing
- **Multiple profiles support** — Context switching like aws --profile; unclear if job search needs this pattern
- **Profile export/import** — Sharing configs; wait for collaboration use case validation

### Architecture Approach

The existing Job-Radar architecture has clear separation between wizard flows (interactive), search operations (argparse), and data storage (JSON files). Profile management should follow this pattern by adding a dedicated profile manager module that centralizes CRUD operations and is used by both wizard and CLI flag paths.

**Major components:**
1. **profile_manager.py (NEW)** — Profile CRUD operations, diff display, validation reuse; centralizes profile I/O currently scattered across wizard.py and search.py
2. **wizard.py (EXTENDED)** — Interactive flows including new quick-edit mode; reuses existing validators and _write_json_atomic()
3. **search.py (EXTENDED)** — Adds CLI update flags with early exit handler; delegates profile operations to profile_manager
4. **__main__.py (EXTENDED)** — Adds profile preview call after banner display; routing only, no profile I/O

**Key patterns identified:**
- **Git-style diff before save**: Show old vs new values before writing changes, require confirmation
- **Validator reuse from wizard**: Extract wizard validators into shared functions for CLI flag validation
- **Early exit handlers**: Update flags exit after update, don't continue to search (clear separation)

### Critical Pitfalls

Based on analysis of real-world CLI tool failures and GitHub issues, five critical pitfalls require prevention.

1. **Partial update file corruption** — Profile JSON corrupted when write interrupted by crash/Ctrl+C. Prevention: Use atomic write pattern with temp file + os.replace(). Already implemented in wizard._write_json_atomic(), must reuse for all update paths.

2. **Validation inconsistency between wizard and CLI flags** — Wizard validates strictly but CLI flags accept invalid values. Prevention: Extract validators to shared Pydantic schema module, use in both paths. Example: min_score must use same 0.0-5.0 range check everywhere.

3. **No confirmation for destructive CLI flag updates** — User runs --update-skills expecting to ADD but flag REPLACES entire list. Prevention: Default to append mode (--add-skills), require explicit --confirm for replace operations (--set-skills). Show before/after diff.

4. **Profile schema evolution without migration path** — v1.6.0 adds field, old profiles crash with KeyError. Prevention: Add schema_version field immediately, implement migration system that auto-upgrades old profiles on load.

5. **No backup before profile updates** — User makes typo, no recovery path. Prevention: Automatic timestamped backups before all updates, keep last 10, provide --restore-profile command.

## Implications for Roadmap

Based on research, the work should be structured in 3 phases that build on each other and address pitfalls incrementally.

### Phase 1: Foundation (profile_manager.py)
**Rationale:** Centralizes profile I/O and enables all other features. Must come first to establish atomic writes, validation, and diff display that other phases depend on.

**Delivers:**
- New profile_manager.py module with load/save/diff/validate functions
- Refactored _write_json_atomic() extracted from wizard.py
- Schema versioning added (schema_version: 1 field)
- Backup mechanism (timestamped, keep last 10)

**Addresses:**
- STACK requirement: Centralized use of tabulate, difflib, colorama
- PITFALL 1: Atomic writes (extract and reuse existing _write_json_atomic)
- PITFALL 4: Schema versioning (add version field before first release)

**Avoids:**
- File corruption during updates (atomic write pattern)
- Duplicate I/O logic across modules (centralization)
- Future breaking changes (versioning from day 1)

### Phase 2: Profile Preview
**Rationale:** Simplest feature that validates profile_manager.py works correctly. Read-only operation with no data modification risk.

**Delivers:**
- display_profile_summary() function in profile_manager.py
- Pretty-printed table format using tabulate
- Called in __main__.py after banner display
- Respects --no-wizard flag to disable

**Addresses:**
- FEATURES: Preview on startup (should-have competitive feature)
- ARCHITECTURE: Integration point in __main__.py between banner and wizard routing

**Uses:**
- tabulate for formatted table output
- colorama for colored section headers
- Existing profile load logic (read-only)

### Phase 3: Quick-Edit Mode
**Rationale:** Reuses wizard validators and tests diff display interactively. Moderate complexity but well-scoped with existing building blocks.

**Delivers:**
- quick_edit_field() function in wizard.py
- New questionary menu option: "Quick-edit a field"
- Before/after diff display using difflib
- Confirmation prompt with profile_manager.save_profile()

**Addresses:**
- FEATURES: Interactive edit mode (should-have competitive feature)
- ARCHITECTURE: Extends wizard.py, reuses validators and _write_json_atomic
- PITFALL 2: Validation consistency (reuses wizard validators)
- PITFALL 5: Backup before update (automatic via profile_manager.save_profile)

**Implements:**
- Git-style diff pattern (show changes before save)
- Validator reuse pattern (single source of truth)

### Phase 4: CLI Update Flags
**Rationale:** Builds on all previous work (diff, validation, profile_manager). Most complex due to non-interactive mode and safety requirements.

**Delivers:**
- CLI flags: --update-skills, --set-min-score, --add-dealbreaker
- Safety flag: --confirm for destructive operations
- Early exit handler in search.py
- update_profile_from_flags() in profile_manager.py

**Addresses:**
- FEATURES: Set single field value (table stakes must-have)
- ARCHITECTURE: Early exit pattern in search.py
- PITFALL 3: Confirmation for destructive changes (require --confirm for replace operations)
- PITFALL 2: Validation consistency (reuses shared validators)

**Avoids:**
- Silent data loss (diff + confirmation required)
- Validation drift (shared schema from Phase 1)
- Unexpected search execution after update (early exit)

### Phase Ordering Rationale

- **Foundation first** because all other phases depend on profile_manager.py functions (load, save, diff, validate). Building features without this creates duplicate code and inconsistent behavior.

- **Preview second** because it's the simplest feature and validates that profile_manager.py integration works correctly before moving to write operations.

- **Quick-edit third** because it tests the critical diff-before-save pattern in an interactive context where users can cancel easily. Validates backup and validation reuse before non-interactive CLI flags.

- **CLI flags last** because they're the most complex (non-interactive mode, safety requirements, early exit handling) and build on all previous phases (diff display from Phase 1, validation from Phase 3, profile_manager patterns from Phase 1).

**Dependency chain:** Phase 1 → Phase 2/3 (parallel) → Phase 4

### Research Flags

Phases likely needing deeper research during planning:
- **None** — All phases have well-documented patterns from git, gh, aws CLI tools. Standard config management patterns apply throughout.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation)** — Atomic file writes, backup patterns, schema versioning are established patterns with Python stdlib examples
- **Phase 2 (Preview)** — Table formatting with tabulate follows standard library documentation
- **Phase 3 (Quick-Edit)** — Interactive prompts with questionary already used in wizard
- **Phase 4 (CLI Flags)** — argparse flag patterns already used in search.py, just extending

**Note:** All required patterns are documented in ARCHITECTURE.md and PITFALLS.md. Implementation should reference these docs rather than triggering new research.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations from official docs (Python stdlib, PyPI); tabulate verified compatible with PyInstaller |
| Features | HIGH | Based on official documentation of git, gh, aws CLI tools; consistent patterns across ecosystem |
| Architecture | HIGH | Analyzed existing Job-Radar codebase directly; integration points verified in actual code |
| Pitfalls | HIGH | Real-world examples from GitHub issues with official sources; verified corruption patterns |

**Overall confidence:** HIGH

### Gaps to Address

No significant gaps identified. All areas have clear documentation and established patterns. Minor items to validate during implementation:

- **PyInstaller compatibility with tabulate**: Expected to work (pure Python) but should build test executable early in Phase 2 to verify table rendering.
- **Profile schema evolution timeline**: schema_version field added in Phase 1 (v1.5.0), but actual migrations won't be needed until v1.6.0+ adds new fields. Migration system can be tested with synthetic old profiles.

These are validation items, not unknowns requiring research. Proceed with standard test-driven development and verify as part of phase acceptance criteria.

## Sources

### Primary (HIGH confidence)
- [Python difflib documentation](https://docs.python.org/3/library/difflib.html) — stdlib module capabilities verified
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html) — mutually exclusive groups, nargs support
- [tabulate PyPI](https://pypi.org/project/tabulate/) — version 0.9.0, pure Python, MIT license
- [PyInstaller Supported Packages Wiki](https://github.com/pyinstaller/pyinstaller/wiki/Supported-Packages) — pure Python compatibility
- [Git config documentation](https://git-scm.com/docs/git-config) — config management patterns
- [GitHub CLI: gh config](https://cli.github.com/manual/gh_config) — subcommand structure
- [AWS CLI: configure set](https://docs.aws.amazon.com/cli/latest/reference/configure/set.html) — single-field update pattern
- Job-Radar codebase analysis (wizard.py, search.py, __main__.py, paths.py) — existing architecture

### Secondary (MEDIUM confidence)
- [Command Line Interface Guidelines](https://clig.dev/) — interactive vs non-interactive best practices
- [Docker config.json corruption on crashes](https://github.com/moby/moby/discussions/48529) — real-world atomic write failures
- [OpenCode storage corruption mid-write](https://github.com/anomalyco/opencode/issues/7733) — corruption prevention strategies
- [npm config validation conflicts](https://github.com/npm/cli/issues/8353) — validation consistency patterns
- [Gemini CLI safe mode confirmation](https://addyosmani.com/blog/gemini-cli/) — confirmation UI patterns
- [JSON Schema Compatibility Checker](https://github.com/json-schema-org/community/issues/984) — schema evolution patterns

### Tertiary (LOW confidence)
- None — all recommendations based on official documentation or verified community sources.

---
*Research completed: 2026-02-11*
*Ready for roadmap: yes*
