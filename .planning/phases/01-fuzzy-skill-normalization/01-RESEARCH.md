# Phase 1: Fuzzy Skill Normalization - Research

**Researched:** 2026-02-07
**Domain:** Python string normalization inside `scoring.py` pure functions
**Confidence:** HIGH

## Summary

Phase 1 adds a `_normalize_skill()` helper to `scoring.py` and wires it into the existing `_skill_in_text()` function so that punctuation and casing variants of skill names match correctly. The root cause of the bug is that `_skill_in_text()` calls `_SKILL_VARIANTS.get(skill.lower(), [])` — if the user's profile has `"NodeJS"` and the dict key is `"node.js"`, the lookup returns an empty list because `"nodejs" != "node.js"`. Normalizing the lookup key (strip punctuation, lowercase, collapse whitespace) before the dict lookup resolves this without any new runtime dependencies.

The change is fully contained within `scoring.py`. No other module is affected. The `_BOUNDARY_SKILLS` set (protecting short skills like `"go"`, `"r"`, `"c"` from substring false-positives) must continue to use word-boundary regex regardless of normalization — this is guarded by the existing `len(skill) <= 2` check and the explicit `_BOUNDARY_SKILLS` membership test in `_build_skill_pattern()`. The normalization path applies on top of the existing architecture without replacing any logic.

A secondary deliverable (FUZZ-05) is expanding `_SKILL_VARIANTS` with common missing tech aliases that normalization alone cannot cover (semantic gaps like abbreviations, full names vs. shorthand).

**Primary recommendation:** Add `_normalize_skill()` as a single pure function, call it on both the lookup key and the job text inside `_skill_in_text()`, and extend `_SKILL_VARIANTS` for semantic gaps normalization cannot bridge.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `re` (stdlib) | built-in | Regex for punctuation stripping and boundary patterns | Already used throughout `scoring.py` |
| `string` (stdlib) | built-in | Optionally use `string.punctuation` as reference | Zero-dep, documents intent clearly |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None required | — | Pure string normalization needs no external library | The problem is punctuation/casing, not Levenshtein distance |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure normalization | `rapidfuzz` or `thefuzz` | Fuzzy distance matching causes false positives ("Java" ~ "JavaScript") and adds a runtime dependency; explicitly rejected in REQUIREMENTS.md |
| Pure normalization | `difflib.SequenceMatcher` | Stdlib but still similarity-ratio based; overkill for a deterministic punctuation problem |

**Installation:**
```bash
# No new packages required — pure stdlib
```

## Architecture Patterns

### Recommended Project Structure
No structural changes. All changes live inside:
```
job_radar/
└── scoring.py   # add _normalize_skill(), update _skill_in_text(), expand _SKILL_VARIANTS
```

### Pattern 1: Normalize-Before-Lookup

**What:** Apply `_normalize_skill()` to the skill string before using it as a `_SKILL_VARIANTS` dict key, and also apply it to the job text before pattern matching.

**When to use:** Every time a skill is compared against job text or looked up in `_SKILL_VARIANTS`.

**Example:**
```python
# Pure normalization function — no side effects, testable in isolation
_NORM_RE = re.compile(r'[\.\-\s]+')

def _normalize_skill(s: str) -> str:
    """Strip punctuation separators, lowercase, collapse whitespace.

    Examples:
        "Node.js" -> "nodejs"
        "C#"      -> "c#"  (# is kept — not a word separator)
        ".NET"    -> "net"
        "node js" -> "nodejs"
    """
    s = s.lower()
    s = _NORM_RE.sub('', s)
    return s.strip()
```

**Key design decision:** Only strip separators (`.`, `-`, spaces). Do NOT strip all punctuation — `#` in `c#` and `+` in `c++` are meaningful. The `re` pattern targets only characters that appear as word separators between tech name components.

### Pattern 2: Dual Normalization in _skill_in_text()

**What:** Normalize both the query skill and the lookup key when checking `_SKILL_VARIANTS`.

**When to use:** Inside `_skill_in_text()` only — `_build_skill_pattern()` already handles the regex matching side.

**Example:**
```python
def _skill_in_text(skill: str, text: str) -> bool:
    """Check if a skill (or any of its variants) appears in text."""
    # Direct match (unchanged — _build_skill_pattern handles boundary logic)
    pattern = _build_skill_pattern(skill)
    if pattern.search(text):
        return True

    # Variant lookup: normalize the skill key to find the right variant group
    normalized_key = _normalize_skill(skill)
    variants = _SKILL_VARIANTS.get(normalized_key, [])

    # Also try original lowercase key for backward compatibility
    if not variants:
        variants = _SKILL_VARIANTS.get(skill.lower(), [])

    for v in variants:
        v_pattern = _build_skill_pattern(v)
        if v_pattern.search(text):
            return True

    return False
```

**Why dual lookup:** The `_SKILL_VARIANTS` keys currently use canonical forms like `"node.js"`. After normalization, `"node.js"` becomes `"nodejs"`. If only the query is normalized but not the dict keys, lookups still fail. The fallback to `skill.lower()` ensures backward compatibility during the transition; alternatively, the dict keys themselves can be re-keyed to normalized forms.

**Recommended approach:** Re-key `_SKILL_VARIANTS` so all keys are normalized. This is cleaner than dual lookup:

```python
# At module level, build a normalized lookup table once
_SKILL_VARIANTS_NORMALIZED = {
    _normalize_skill(k): v for k, v in _SKILL_VARIANTS.items()
}
```

Then `_skill_in_text()` uses `_SKILL_VARIANTS_NORMALIZED.get(_normalize_skill(skill), [])`.

### Pattern 3: _BOUNDARY_SKILLS Preservation

**What:** The `_BOUNDARY_SKILLS` set and `len(skill) <= 2` guard in `_build_skill_pattern()` must remain active regardless of normalization path.

**When to use:** Always — this is a safety invariant.

**Example:**
```python
def _build_skill_pattern(skill: str) -> re.Pattern:
    """Word-boundary pattern for short/ambiguous skills."""
    escaped = re.escape(skill.lower())
    if skill.lower() in _BOUNDARY_SKILLS or len(skill) <= 2:
        return re.compile(rf'\b{escaped}\b', re.IGNORECASE)
    return re.compile(re.escape(skill.lower()), re.IGNORECASE)
```

This function is unchanged. Normalization happens upstream in `_skill_in_text()` before calling `_build_skill_pattern()`. The boundary check operates on the variant strings, which are already short and intentionally preserved.

### Pattern 4: _SKILL_VARIANTS Expansion (FUZZ-05)

**What:** Add missing common tech name variants that normalization cannot bridge (semantic gaps, abbreviations, full names).

**When to use:** Any technology with commonly used alternate names that differ in meaning, not just punctuation.

**Gaps identified from current dict inspection:**

| Missing | Should be under | Notes |
|---------|----------------|-------|
| `"vue.js"`, `"vuejs"` | `"vue"` | Commonly listed as "Vue.js" |
| `"angular.js"`, `"angularjs"` | `"angular"` | Legacy name still appears |
| `"k8s"` | `"kubernetes"` | Common abbreviation |
| `"js"` | Not needed | Already in `_BOUNDARY_SKILLS` as boundary-only |
| `"python3"`, `"py"` | `"python"` | Common shorthand |
| `"golang"` | `"go"` | Already in `_HN_SKILL_SLUGS` but not `_SKILL_VARIANTS` |
| `"aws"` | absent entirely | Amazon Web Services is extremely common |
| `"gcp"` | absent entirely | Google Cloud Platform |
| `"azure"` | absent entirely | Microsoft Azure |
| `"ci/cd"` | absent | CI/CD pipeline skills |
| `"sql"` | absent | Core data skill |
| `"nosql"` | absent | Common requirement |
| `"rest"`, `"restful"` | absent | API pattern ubiquitous in job listings |
| `"graphql"` | absent | Widely listed |
| `"docker"` | absent | Container skill |
| `"terraform"` | absent | Infrastructure as code |

### Anti-Patterns to Avoid

- **Stripping all punctuation:** `re.sub(r'[^\w]', '', s)` would strip `#` from `c#` and `+` from `c++`, making them unrecognizable. Only strip separator characters (`.`, `-`, whitespace).
- **Normalizing inside `_build_skill_pattern()`:** The pattern builder receives variant strings that may intentionally include spaces (e.g., `"node js"`). Normalizing there would break the regex escape logic.
- **Replacing `_SKILL_VARIANTS` entirely with normalization:** Normalization handles punctuation/casing only. Semantic aliases ("RPA" → "Robotic Process Automation") require explicit `_SKILL_VARIANTS` entries.
- **Double-normalizing:** If `_SKILL_VARIANTS` keys are re-keyed to normalized form, don't also apply a dual-lookup fallback — it adds complexity and masks bugs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Punctuation stripping | Custom character-by-character scanner | `re.sub()` with a targeted pattern | One line, readable, already used in module |
| Case folding | Manual `.lower()` + case tables | Python's built-in `.lower()` | Already used everywhere in codebase |
| Semantic similarity | Custom distance function | Explicit `_SKILL_VARIANTS` table | Deterministic, auditable, no false positives |

**Key insight:** This is a dictionary lookup problem disguised as a fuzzy matching problem. The fix is normalization of keys, not probabilistic matching.

## Common Pitfalls

### Pitfall 1: Stripping Meaningful Punctuation

**What goes wrong:** Stripping `#` from `c#` produces `"c"`, which is in `_BOUNDARY_SKILLS`. Then `"c"` matches `"c"` in words like "service", "architecture", "specific" if the boundary regex is not applied. Since `"c"` is only 1 character, `_build_skill_pattern` will apply `\b` boundaries — but `\bc\b` still matches standalone `c` which is a valid letter in many contexts.

**Why it happens:** Over-aggressive punctuation stripping.

**How to avoid:** Only strip separator characters: `[.\-\s]`. Keep `#`, `+`, `/` intact.

**Warning signs:** Test `_normalize_skill("c#")` and verify it returns `"c#"` not `"c"`.

### Pitfall 2: Variant Lookup Key Mismatch After Normalization

**What goes wrong:** `_SKILL_VARIANTS` has key `"node.js"`. After `_normalize_skill("NodeJS")` → `"nodejs"`, the lookup `_SKILL_VARIANTS.get("nodejs")` returns `None` because the key in the dict is still `"node.js"` → normalizes to `"nodejs"` but was never re-keyed.

**Why it happens:** Normalizing the query without normalizing the dict keys.

**How to avoid:** Build `_SKILL_VARIANTS_NORMALIZED` at module load time by applying `_normalize_skill` to all dict keys. This is a one-liner comprehension.

**Warning signs:** `_skill_in_text("nodejs", "node.js developer")` returns `False` after the change.

### Pitfall 3: _BOUNDARY_SKILLS Bypassed

**What goes wrong:** Short skills like `"go"`, `"r"` get normalized (no change in these cases) but then matched without word boundaries because the path goes through the variant lookup rather than `_build_skill_pattern()`.

**Why it happens:** Variant list items are passed directly to `_build_skill_pattern()`, which applies boundary rules — so this should not happen if the existing pattern is preserved. The risk is if someone changes the loop to use raw string matching instead of `_build_skill_pattern()`.

**How to avoid:** Always route variant matches through `_build_skill_pattern(v)` as the existing code does.

**Warning signs:** Searching for skill `"go"` matches "algorithm", "google", "cargo" without word boundaries.

### Pitfall 4: _SKILL_VARIANTS Regression via Key Re-keying

**What goes wrong:** Some `_SKILL_VARIANTS` keys contain spaces (e.g., `"business analysis"`, `"blue prism"`, `"vertex tax engine"`). After `_normalize_skill()`, spaces are stripped: `"businessanalysis"`. If the variant list items are also normalized, entries like `"business analyst"` → `"businessanalyst"` which is a different key and the match may never occur.

**Why it happens:** Normalizing variant values as well as keys.

**How to avoid:** Normalize keys only for the lookup table. Keep variant values in their original form so `_build_skill_pattern()` can build correct regex patterns (including handling spaces as literal substrings in multi-word variants).

**Warning signs:** `_skill_in_text("business analysis", "business analyst needed")` returns `False` after the change.

## Code Examples

Verified patterns — these work with the existing `scoring.py` structure:

### _normalize_skill() Implementation

```python
# Source: derived from scoring.py's existing re usage + requirements FUZZ-01
import re

_NORM_RE = re.compile(r'[\.\-\s]+')

def _normalize_skill(s: str) -> str:
    """Strip separator punctuation, lowercase, collapse whitespace.

    Only strips characters that serve as separators in tech names
    (dots, hyphens, spaces). Preserves meaningful punctuation like
    # in C# and + in C++.

    Examples:
        "Node.js"   -> "nodejs"
        "node js"   -> "nodejs"
        "node-js"   -> "nodejs"
        ".NET"      -> "net"
        "C#"        -> "c#"
        "C++"       -> "c++"
        "React.js"  -> "reactjs"
    """
    return _NORM_RE.sub('', s.lower())
```

### _SKILL_VARIANTS_NORMALIZED Build Pattern

```python
# Source: derived from scoring.py module structure
# Build normalized lookup table once at module load
_SKILL_VARIANTS_NORMALIZED: dict[str, list[str]] = {
    _normalize_skill(k): v for k, v in _SKILL_VARIANTS.items()
}
```

### Updated _skill_in_text()

```python
# Source: derived from existing _skill_in_text() in scoring.py
def _skill_in_text(skill: str, text: str) -> bool:
    """Check if a skill (or any of its variants) appears in text."""
    # Direct match — unchanged, _build_skill_pattern handles boundary logic
    pattern = _build_skill_pattern(skill)
    if pattern.search(text):
        return True

    # Normalize skill key for variant lookup
    normalized_key = _normalize_skill(skill)
    variants = _SKILL_VARIANTS_NORMALIZED.get(normalized_key, [])
    for v in variants:
        v_pattern = _build_skill_pattern(v)
        if v_pattern.search(text):
            return True

    return False
```

### Expanded _SKILL_VARIANTS Additions

```python
# Additions for FUZZ-05 — common tech variants missing from current dict
# Source: direct inspection of _SKILL_VARIANTS gaps
    "python": ["python", "python3", "py3"],
    "go": ["go", "golang"],
    "vue": ["vue", "vue.js", "vuejs"],
    "angular": ["angular", "angular.js", "angularjs"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud"],
    "azure": ["azure", "microsoft azure"],
    "docker": ["docker", "docker container"],
    "terraform": ["terraform", "tf"],
    "sql": ["sql"],
    "nosql": ["nosql", "no-sql"],
    "rest": ["rest", "restful", "rest api"],
    "graphql": ["graphql", "graph ql"],
    "ci/cd": ["ci/cd", "ci cd", "cicd"],
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `_SKILL_VARIANTS.get(skill.lower(), [])` | `_SKILL_VARIANTS_NORMALIZED.get(_normalize_skill(skill), [])` | Phase 1 | Fixes "NodeJS" vs "node.js" lookup miss |
| No normalization on either side | Normalize query key before lookup | Phase 1 | Catches all punctuation/casing variants |

**Deprecated/outdated after this phase:**
- Manual variant entries for punctuation-only differences (e.g., `"node.js"` and `"nodejs"` in the same list) become redundant — normalization handles them. However, keeping them is harmless and maintains readability.

## Open Questions

1. **Normalized key collision risk**
   - What we know: `_normalize_skill("node.js")` → `"nodejs"` and `_normalize_skill("node js")` → `"nodejs"` — same normalized key, no collision here.
   - What's unclear: Are there any two distinct `_SKILL_VARIANTS` keys that would normalize to the same string and represent *different* technologies?
   - Recommendation: Inspect all current keys after normalization. Likely no collision given the domain, but verify with a quick dict comprehension check.

2. **Text normalization scope**
   - What we know: The `text` argument to `_skill_in_text()` is `(job.title + " " + job.description + " " + job.company).lower()` — already lowercased.
   - What's unclear: Should `_normalize_skill()` also be applied to the full job text? If so, `"node.js"` in the job text becomes `"nodejs"` before the regex runs, meaning the existing `_SKILL_VARIANTS` list item `"node.js"` would no longer match.
   - Recommendation: Do NOT normalize the full text. Normalize only the lookup key. The direct pattern match via `_build_skill_pattern()` handles the text side already through `re.IGNORECASE`. Normalizing text would break the variant regex patterns.

3. **_SKILL_VARIANTS key migration**
   - What we know: Current keys include multi-word keys with spaces and dots.
   - What's unclear: Whether normalized keys should replace originals in the source dict, or if the normalized lookup table should exist only as a derived constant.
   - Recommendation: Keep `_SKILL_VARIANTS` with human-readable keys (easier to maintain). Derive `_SKILL_VARIANTS_NORMALIZED` as a module-level constant built from `_SKILL_VARIANTS`.

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `/Users/coryebert/Documents/Job Hunt Python/Project Folder/Job-Radar/job_radar/scoring.py` — full `_SKILL_VARIANTS`, `_BOUNDARY_SKILLS`, `_skill_in_text()`, `_build_skill_pattern()` reviewed
- `.planning/research/SUMMARY.md` — prior research confirming pure normalization approach
- `.planning/research/ARCHITECTURE.md` — architecture patterns confirmed
- `.planning/REQUIREMENTS.md` — FUZZ-01 through FUZZ-05 requirements
- Python stdlib `re` module — used directly throughout `scoring.py`

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY.md` confirmed: `_BOUNDARY_SKILLS` protection mechanism and its rationale

### Tertiary (LOW confidence)
- None — all findings derive from direct source code inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; `re` stdlib already in module
- Architecture: HIGH — change is fully contained within `scoring.py`; exact integration points identified from source
- Pitfalls: HIGH — derived from direct inspection of `_BOUNDARY_SKILLS`, `_SKILL_VARIANTS`, and `_skill_in_text()` logic paths

**Research date:** 2026-02-07
**Valid until:** Indefinite — stable stdlib pattern; no external dependency changes
