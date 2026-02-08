# Feature Landscape

**Domain:** Python CLI tool — job search aggregation with scoring, fuzzy matching, and config support
**Researched:** 2026-02-07
**Confidence notes:** HIGH for pytest/testing patterns (verified against known Python ecosystem); HIGH for fuzzy matching libraries (rapidfuzz is dominant 2024+); MEDIUM for config file conventions (TOML is standard but implementation patterns vary)

## Context

This milestone adds three specific features to an existing, working tool:

1. **Test suite** — pytest covering scoring, caching, and tracking (zero coverage today)
2. **Fuzzy skill matching** — normalize "NodeJS" ↔ "node.js", "Python" ↔ "python3"
3. **Config file support** — persist default CLI options so `--min-score 3.5 --new-only` don't need retyping

The scoring engine is composed of pure functions (`score_job`, component scorers, `_skill_in_text`). The tracker and cache modules perform I/O but have clear seams for mocking. This is an unusually testable codebase for having zero tests.

---

## Table Stakes

Features users expect from a quality Python CLI tool. Missing = tool feels unfinished or fragile.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| pytest suite with parametrize | Python community standard; scoring has pure functions begging for it | Low | `_score_skill_match`, `_score_title_relevance`, `_check_dealbreakers` are side-effect-free |
| Fixture-based test data | Avoids hardcoded job dicts repeated across tests | Low | One `@pytest.fixture` for a minimal `JobResult` object covers most tests |
| Edge case coverage | Empty profile, empty skill list, malformed job data | Low | Already handled by code (`if not core_skills: ratio = 0.0`), just needs assertions |
| Normalized skill lookup | "NodeJS" vs "node.js" is the exact problem `_SKILL_VARIANTS` was meant to solve | Low | `_SKILL_VARIANTS` already has the entry; the gap is that lookup only checks exact key, not normalized form |
| Config file for persistent defaults | Any tool run daily with the same flags needs this; rekeying `--min-score 3.5 --new-only` every run is friction | Low-Med | Standard pattern: `~/.job-radar.toml` or `config.toml` in profile dir |
| Graceful config-not-found | Tool must work without a config file (zero-config guarantee from PROJECT.md) | Low | Return empty dict if config absent; no error |
| CLI flags override config | Standard precedence: CLI > config > default | Low | Apply config first, then `parser.set_defaults()` or post-parse override |

---

## Differentiators

Features that make the tool stand out. Not universally expected, but add meaningful value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Canonicalized skill normalization (not just variants dict) | Handles new skill spellings automatically: "react.js", "ReactJS", "React JS" all map to "react" | Low-Med | Normalize both query skill and job text to lowercase + strip `.js`/`js` suffix pattern before match; no external library needed |
| rapidfuzz token_set_ratio for title matching | "Senior Software Engineer" matches "Staff Engineer / Senior SWE" better than substring search | Med | Requires `rapidfuzz` dependency; opt-in only since deps are constrained; significant improvement for title relevance scoring |
| Test coverage CI badge / coverage report | Shows scoring reliability; important for a tool where wrong scores mean missed jobs | Low | `pytest-cov` + `coverage.py`; no CI required, just local `coverage run` |
| Parametrized fuzzy threshold tests | Prove that normalization doesn't cause false positives (e.g., "go" doesn't match "golang") | Low | Direct extension of the existing `_BOUNDARY_SKILLS` set with test assertions |
| Profile-specific config override | `--profile cory.json` could auto-load `cory.config.toml` for per-profile defaults | Low | Useful if multiple people use the tool with different `--min-score` preferences |
| Config validation on load | Catch typos in config keys early with helpful error messages | Low | Simple dict key check against known options |

---

## Anti-Features

Features to deliberately NOT build. These are common mistakes for tools in this category.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full fuzzy library for skill matching | `rapidfuzz` adds a runtime dep; the real problem is just normalization of known patterns (punctuation, case, common suffixes) | Enhance `_SKILL_VARIANTS` + add a normalize() helper that strips `.`, whitespace, common suffixes (`js`, `net`) |
| YAML config format | YAML has footguns (Norway problem, type coercion); overkill for 3-5 scalar options | Use TOML or JSON; TOML is Python standard since 3.11 (`tomllib`), JSON already used in project |
| Environment variables for config | Env vars are for secrets and deployment contexts, not user preferences | Config file at known path (`~/.job-radar.toml` or profile-adjacent) |
| Abstract config layer / plugin system | This is one user's daily CLI; over-engineering config is a trap | Flat dict from TOML file, read once at startup |
| 100% test coverage target | Cache and sources modules require network/filesystem mocking; diminishing returns | Cover the scoring engine (highest value, pure functions) and tracker key logic; skip network-dependent scrapers |
| Mock-heavy integration tests for scrapers | Brittle, tied to HTML structure that changes; false confidence | Test parsing helpers in isolation; use small fixture HTML snippets only if a parsing bug is confirmed |
| pytest plugins beyond pytest-cov | `pytest-mock`, `pytest-asyncio`, etc. add complexity with no current need | stdlib `unittest.mock` patches work fine for the few I/O seams |
| Config file migration/versioning | Current config will have 3-5 keys total | Add `# version = 1` comment but no migration logic; it's a personal tool |

---

## Feature Dependencies

```
Fuzzy skill matching
  └── Requires: Understanding of _SKILL_VARIANTS structure (already in scoring.py)
  └── Blocks: Nothing else; purely additive to _skill_in_text()

Test suite
  └── Requires: No production code changes
  └── Enables: Validates fuzzy matching correctness once implemented
  └── Enables: Validates config loading behavior (config → defaults → override)
  └── Blocks: Config file support ideally tested before shipping

Config file support
  └── Requires: Identify which CLI args are "persistent" vs "ephemeral"
  └── Depends on: Nothing else in this milestone
  └── Blocks: Nothing, but test suite should cover it

Recommended implementation order:
  1. Test suite first (no production risk, establishes baseline)
  2. Fuzzy skill matching (pure function change, tests verify immediately)
  3. Config file support (most integration surface, tests validate precedence)
```

---

## MVP Recommendation

For this milestone (quality improvements to existing tool), the MVP is all three features since they are the stated scope. Priority within the milestone:

**Ship in this order:**

1. **Test suite** — establishes correctness baseline before changing production code; pure value with zero risk
2. **Fuzzy skill matching** — pure function change to `_skill_in_text()` and `_SKILL_VARIANTS`; tests from step 1 immediately validate it
3. **Config file support** — has the most surface area (arg parsing, precedence, file location); tests from step 1 validate it

**Defer to post-milestone:**

- rapidfuzz integration for title matching — adds a dependency and requires threshold tuning; the skill normalization approach covers the stated problem (NodeJS/node.js) without any new deps
- Profile-specific config auto-loading — nice to have but zero users have asked for it yet
- Application tracking CLI commands — `tracker.py` has the functions but exposing them is explicitly out of scope per PROJECT.md

---

## Key Decisions This Research Supports

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Fuzzy library vs normalization | Normalization only (no new dep) | The NodeJS/node.js problem is punctuation/casing, not semantic fuzzy matching. `_SKILL_VARIANTS` already handles it; just needs a normalize step on lookup. |
| Config format | TOML via `tomllib` (stdlib, Python 3.11+) with JSON fallback for 3.10 | TOML is human-friendly, already Python standard. Project requires 3.10+; `tomllib` was added in 3.11, so need `tomli` backport for 3.10 OR use JSON (already used everywhere). **JSON is simpler given the constraint.** |
| Config location | Adjacent to profile or `~/.job-radar.json` | Tool is profile-driven; config next to profile makes multi-profile setups natural. Global `~/` location works for single-user. |
| Test scope | scoring.py, tracker.py key functions, cache module read/write | These have the highest correctness stakes (wrong score = missed job) and are already structured as pure/near-pure functions. |

---

## Sources

- Codebase analysis: `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/job_radar/` (direct inspection)
- PROJECT.md requirements: active items confirm scope
- Python ecosystem knowledge (HIGH confidence for pytest patterns, stdlib TOML, rapidfuzz dominance)
- Note: WebSearch unavailable during this research session; findings based on training knowledge through early 2025 plus codebase analysis. Python testing and config file patterns in this domain are stable and unlikely to have changed materially.
