# Phase 7: Interactive Setup Wizard - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

First-run wizard that collects user profile information (name, skills, job titles, location, dealbreakers) and preferences (minimum score, new-only filter) through interactive prompts, then auto-generates ~/.job-radar/profile.json and config.json files.

This wizard is triggered on first launch when profile.json doesn't exist. Subsequent launches skip the wizard and go directly to search.

</domain>

<decisions>
## Implementation Decisions

### Prompt Flow and Ordering
- **One question at a time** — user sees current question, answers, moves to next (cleaner, less overwhelming)
- **Question order (ease user in):** Name → Titles → Skills → Location → Dealbreakers → Score → Filter
- **Back button navigation** — user can press a key (Ctrl+B or arrow up) to go back and change previous answers
- Flow is sequential but allows editing previous responses before final submission

### Input Format and Examples
- **Comma-separated list** for multi-value inputs (skills, titles, dealbreakers) — "Python, JavaScript, React"
- **Examples on separate line** — prompt on one line, example on next line in different color for clear separation
- **No default values** — all fields start empty, user must provide everything (forces conscious choices)
- **Autocomplete:** Claude's discretion — decide based on technical feasibility and UX value for skill suggestions

### Validation and Errors
- **Validate after each answer** — user presses Enter, validation runs immediately (instant feedback)
- **On validation failure:** Offer to skip or retry — show error, ask "Try again or skip this field?"
- **Required fields:** Name, skills, titles required; location, dealbreakers optional (balanced approach)
- **Error styling:** Symbol + message — "❌ Name cannot be empty" or "⚠️  Name cannot be empty"

### Wizard Personality
- **Tone:** Friendly and conversational — "What's your name?" or "Let's start with your name." (warmer, approachable)
- **Emoji usage:** Emoji per section — use emoji to distinguish sections (👤 Profile, ⚙️ Preferences) for visual organization
- **Tips:** Tips for complex fields only — explain dealbreakers and score threshold where needed
- **Completion:** Celebration + summary — "✨ All set! Here's your profile:" + summary (rewarding experience)

### Claude's Discretion
- Autocomplete/suggestion implementation for skills (balance UX value vs complexity)
- Exact key binding for back button (Ctrl+B vs arrow keys vs other)
- Color scheme for examples and errors (ensure cross-platform compatibility)
- Specific wording for tips/explanations on complex fields

</decisions>

<specifics>
## Specific Ideas

- Question order intentionally starts friendly (name, titles) before technical (skills, score thresholds)
- Emoji sections create visual structure: 👤 Profile section, ⚙️ Preferences section
- Validation happens immediately after each answer to prevent cascading errors at the end
- Back button allows correction without restarting entire wizard
- Celebration at end ("✨ All set!") makes setup feel rewarding, not tedious

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-interactive-setup-wizard*
*Context gathered: 2026-02-09*
