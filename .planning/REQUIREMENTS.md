# Requirements: Job Radar

**Defined:** 2026-02-07
**Core Value:** Accurate job-candidate scoring -- if the scoring is wrong, nothing else matters.

## v1 Requirements

### Testing

- [ ] **TEST-01**: Scoring unit tests cover all `_score_*` functions with parametrized edge cases
- [ ] **TEST-02**: Dealbreaker detection tests verify exact match, substring, and case-insensitive behavior
- [ ] **TEST-03**: Salary parsing tests cover formats: "$120k", "$60/hr", "$120,000", ranges, and "Not listed"
- [ ] **TEST-04**: Tracker `job_key()` tests verify stable dedup key generation
- [ ] **TEST-05**: Tracker `mark_seen()` tests verify new/seen annotation with tmp_path isolation
- [ ] **TEST-06**: Tracker `get_stats()` tests verify aggregation logic
- [ ] **TEST-07**: Shared conftest.py with sample profile and JobResult fixtures

### Fuzzy Matching

- [ ] **FUZZ-01**: `_normalize_skill()` function strips punctuation, lowercases, and collapses whitespace
- [ ] **FUZZ-02**: Normalized lookup in `_skill_in_text()` so "NodeJS" matches "node.js"
- [ ] **FUZZ-03**: `_BOUNDARY_SKILLS` protection preserved — short skills (go, r, c) use word-boundary matching only
- [ ] **FUZZ-04**: No regressions on existing `_SKILL_VARIANTS` matches
- [ ] **FUZZ-05**: Expanded `_SKILL_VARIANTS` dict with missing common tech variants

### Config

- [ ] **CONF-01**: JSON config file at `~/.job-radar/config.json` for persistent CLI defaults
- [ ] **CONF-02**: CLI flags always override config values (set_defaults pattern)
- [ ] **CONF-03**: Graceful behavior when no config file exists — tool works identically to today
- [ ] **CONF-04**: `--config` flag to specify custom config file path
- [ ] **CONF-05**: Config validation catches unknown keys with helpful error messages

## v2 Requirements

### Testing Expansion

- **TEST-V2-01**: Cache module tests (read/write, TTL expiry) with tmp_path isolation
- **TEST-V2-02**: pytest-cov integration for coverage tracking
- **TEST-V2-03**: Source parser tests with HTML fixture snapshots

### Job Data Aggregation

- **DATA-01**: JSearch (RapidAPI) or SerpAPI integration for LinkedIn/Indeed coverage
- **DATA-02**: API key configuration via config file
- **DATA-03**: Source-specific cache TTL settings

### Application Tracking CLI

- **TRACK-01**: `job-radar apply <title> <company>` command to track application status
- **TRACK-02**: `job-radar status` command to view application pipeline

## Out of Scope

| Feature | Reason |
|---------|--------|
| LinkedIn/Indeed direct scraping | Both sites aggressively block automation; unreliable |
| Web UI or email digest | CLI + Markdown report is the current workflow |
| rapidfuzz dependency | Normalization-based approach covers the problem without new runtime deps |
| TOML config format | Requires tomli backport for Python 3.10; JSON is zero-dep and already used |
| Mobile app | Desktop CLI tool |
| Scoring weight customization | Deferred -- current weights work; tune after test suite validates them |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FUZZ-01 | Phase 1 | Pending |
| FUZZ-02 | Phase 1 | Pending |
| FUZZ-03 | Phase 1 | Pending |
| FUZZ-04 | Phase 1 | Pending |
| FUZZ-05 | Phase 1 | Pending |
| CONF-01 | Phase 2 | Pending |
| CONF-02 | Phase 2 | Pending |
| CONF-03 | Phase 2 | Pending |
| CONF-04 | Phase 2 | Pending |
| CONF-05 | Phase 2 | Pending |
| TEST-01 | Phase 3 | Pending |
| TEST-02 | Phase 3 | Pending |
| TEST-03 | Phase 3 | Pending |
| TEST-04 | Phase 3 | Pending |
| TEST-05 | Phase 3 | Pending |
| TEST-06 | Phase 3 | Pending |
| TEST-07 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0

---
*Requirements defined: 2026-02-07*
*Last updated: 2026-02-07 after roadmap creation*
