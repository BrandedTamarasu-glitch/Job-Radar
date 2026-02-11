# Phase 14: Wellfound URLs - Research

**Researched:** 2026-02-10
**Domain:** URL generation for manual job browsing
**Confidence:** HIGH

## Summary

Wellfound (formerly AngelList Talent) is a startup-focused job board that doesn't provide a public API, making manual URL generation the appropriate integration strategy. Research confirms a clean, predictable URL structure for job searches with role and location parameters.

The standard approach for this phase is to generate formatted URLs using Wellfound's `/role/l/{role}/{location}` pattern (or `/role/r/{role}` for remote-only roles), with job titles converted to URL-friendly slugs (lowercase, hyphens replacing spaces). This follows the same pattern successfully used for Indeed, LinkedIn, and Glassdoor manual URLs in the existing codebase.

Wellfound specializes in startup jobs, early-stage companies, and equity-heavy compensation packages, making it a valuable complement to traditional job boards and the recently added API sources (Adzuna, Authentic Jobs).

**Primary recommendation:** Generate Wellfound URLs using the `/role/l/{role}/{location}` pattern with hyphenated slugs, detect remote preferences to use `/role/r/{role}` variant, and integrate into existing manual URL infrastructure alongside Indeed/LinkedIn/Glassdoor.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| urllib.parse | stdlib (3.14+) | URL encoding and formatting | Python standard library, already used in codebase for Indeed/LinkedIn URLs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | 2.x | HEAD request for URL validation | Optional validation check (already in project dependencies) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| urllib.parse.quote | Manual string replacement | urllib.parse handles edge cases (international characters, special chars) correctly and is battle-tested |
| No validation | Validate all URLs with HEAD requests | HEAD requests add latency and can fail due to rate limits; better to generate URLs optimistically and document that they may need manual verification |

**Installation:**
```bash
# No additional dependencies needed - urllib.parse is stdlib
# requests already in requirements.txt from existing features
```

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── sources.py              # Add generate_wellfound_url() here (alongside existing generators)
└── report.py               # Already handles manual URLs - no changes needed
```

### Pattern 1: URL Slug Generation
**What:** Convert job titles to Wellfound-compatible URL slugs
**When to use:** For all Wellfound role-based URLs
**Example:**
```python
# Source: Wellfound URL analysis + Python urllib best practices
import urllib.parse

def _slugify_title(title: str) -> str:
    """Convert job title to Wellfound URL slug format.

    Examples:
        "Software Engineer" -> "software-engineer"
        "Backend Developer" -> "backend-developer"
        "Senior Frontend Engineer" -> "senior-frontend-engineer"
    """
    # Wellfound uses lowercase, hyphen-separated slugs
    # No need for urllib.parse.quote - Wellfound URLs use raw slugs
    slug = title.lower().strip()
    slug = slug.replace(" ", "-")
    # Remove special characters that aren't hyphens or alphanumeric
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Remove consecutive hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")
```

### Pattern 2: Location-Based URL Construction
**What:** Build URLs with role and location, or remote-only variant
**When to use:** For generating Wellfound search URLs from profile data
**Example:**
```python
# Source: Existing Indeed/LinkedIn pattern in sources.py + Wellfound URL research
def generate_wellfound_url(title: str, location: str) -> str:
    """Generate a Wellfound search URL with role and optional location.

    Args:
        title: Job title (e.g., "Software Engineer")
        location: Location string (e.g., "San Francisco, CA", "Remote", or "New York")

    Returns:
        Wellfound search URL
    """
    role_slug = _slugify_title(title)

    # Remote detection (case-insensitive)
    if "remote" in location.lower():
        # Use remote-specific URL pattern
        return f"https://wellfound.com/role/r/{role_slug}"

    # Location-specific URL pattern
    # Wellfound uses location slugs similar to role slugs
    location_slug = location.lower().strip().replace(" ", "-").replace(",", "")
    location_slug = "".join(c for c in location_slug if c.isalnum() or c == "-")
    while "--" in location_slug:
        location_slug = location_slug.replace("--", "-")
    location_slug = location_slug.strip("-")

    return f"https://wellfound.com/role/l/{role_slug}/{location_slug}"
```

### Pattern 3: Integration with Existing Manual URL Infrastructure
**What:** Add Wellfound to the manual URL generation list
**When to use:** In generate_manual_urls() function
**Example:**
```python
# Source: Existing pattern in sources.py lines 990-1020
def generate_manual_urls(profile: dict) -> list[dict]:
    """Generate manual-check URLs for a candidate profile, sorted by source."""
    urls = []
    titles = profile.get("target_titles", [])[:3]
    location = profile.get("target_market", profile.get("location", ""))

    generators = [
        ("Wellfound", generate_wellfound_url),  # ADD THIS
        ("Indeed", generate_indeed_url),
        ("LinkedIn", generate_linkedin_url),
        ("Glassdoor", generate_glassdoor_url),
    ]

    for source_name, gen_fn in generators:
        for title in titles:
            url = gen_fn(title, location)
            urls.append({
                "source": source_name,
                "title": title,
                "url": url,
            })

    # WWR continues after generators list...
    return urls
```

### Anti-Patterns to Avoid
- **Double encoding:** Don't use urllib.parse.quote() on Wellfound slugs - they expect raw hyphenated strings, not percent-encoded values
- **Over-validation:** Don't require HEAD request success to show URLs - Wellfound may rate-limit or block automated checks, but the URLs still work for manual browsing
- **Location transformation attempts:** Don't try to normalize locations to specific formats - Wellfound handles various location formats flexibly (city names, states, countries, "Remote")

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| URL encoding | Custom string replacement for special chars | urllib.parse.quote() (but not needed for Wellfound slugs) | Handles UTF-8, international characters, edge cases |
| String normalization | Regex-heavy slug generation | Simple lowercase + replace + filter (as shown above) | Wellfound uses simple slug format, no need for complex parsing |
| URL validation | Full scraper to verify search results | Optional HEAD request, or skip validation entirely | Wellfound blocks automated access (403), manual URLs work fine for users |

**Key insight:** This is a URL generator, not a scraper. The goal is to create clickable links for users, not to programmatically verify or fetch results. Keep it simple and follow Wellfound's URL patterns directly.

## Common Pitfalls

### Pitfall 1: Using URL-encoded slugs
**What goes wrong:** Generating URLs like `https://wellfound.com/role/l/software%20engineer/san%20francisco` instead of `https://wellfound.com/role/l/software-engineer/san-francisco`
**Why it happens:** Overuse of urllib.parse.quote() for all URL parts
**How to avoid:** Only use raw slugification (lowercase, hyphen replacement) for Wellfound role/location parts
**Warning signs:** URLs contain `%20` or other percent-encoded characters in the path (not query params)

### Pitfall 2: Validation blocking URL output
**What goes wrong:** HEAD requests to Wellfound fail (403 Forbidden), causing URLs not to be generated
**Why it happens:** Wellfound uses bot protection, blocks automated requests
**How to avoid:** Make validation optional and non-blocking, or skip it entirely for Wellfound
**Warning signs:** Manual URLs section missing Wellfound entries, 403 errors in logs

### Pitfall 3: Using all target titles
**What goes wrong:** Generating 5+ Wellfound URLs when user has many target titles, cluttering the report
**Why it happens:** Not following the existing pattern (Indeed/LinkedIn use first 3 titles only)
**How to avoid:** Match existing pattern: `titles = profile.get("target_titles", [])[:3]`
**Warning signs:** Manual URL section becomes excessively long

### Pitfall 4: Incorrect remote URL pattern
**What goes wrong:** Using `/role/l/software-engineer/remote` instead of `/role/r/software-engineer`
**Why it happens:** Not detecting remote preference and using location-based pattern
**How to avoid:** Check for "remote" in location string (case-insensitive) and use `/role/r/` pattern
**Warning signs:** Remote job searches don't return results or show wrong location filter

## Code Examples

Verified patterns from official sources:

### Wellfound URL Formats (Observed)
```python
# Source: Web search results showing live Wellfound URLs
# https://wellfound.com/role/software-engineer
# https://wellfound.com/role/backend-engineer
# https://wellfound.com/role/r/software-engineer (remote)
# https://wellfound.com/role/r/backend-developer (remote)
# https://wellfound.com/role/l/software-engineer/san-francisco

# These confirm the URL patterns:
# 1. Role only: /role/{role-slug}
# 2. Remote role: /role/r/{role-slug}
# 3. Role + location: /role/l/{role-slug}/{location-slug}
```

### Complete Implementation
```python
# Source: Combining Wellfound URL research with existing codebase patterns

def _slugify_title(title: str) -> str:
    """Convert job title to Wellfound URL slug format."""
    slug = title.lower().strip().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")

def _slugify_location(location: str) -> str:
    """Convert location to Wellfound URL slug format."""
    # Remove commas (e.g., "San Francisco, CA" -> "san-francisco-ca")
    slug = location.lower().strip().replace(",", "").replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")

def generate_wellfound_url(title: str, location: str) -> str:
    """Generate a Wellfound search URL with role and optional location.

    Wellfound URL patterns:
    - Remote only: https://wellfound.com/role/r/{role-slug}
    - Role + location: https://wellfound.com/role/l/{role-slug}/{location-slug}

    Examples:
        generate_wellfound_url("Software Engineer", "Remote")
        -> "https://wellfound.com/role/r/software-engineer"

        generate_wellfound_url("Backend Developer", "San Francisco, CA")
        -> "https://wellfound.com/role/l/backend-developer/san-francisco-ca"

    Args:
        title: Job title (e.g., "Software Engineer")
        location: Location string (e.g., "San Francisco, CA" or "Remote")

    Returns:
        Wellfound search URL (no validation performed)
    """
    role_slug = _slugify_title(title)

    # Remote detection (case-insensitive)
    if "remote" in location.lower():
        return f"https://wellfound.com/role/r/{role_slug}"

    # Location-specific URL
    location_slug = _slugify_location(location)
    return f"https://wellfound.com/role/l/{role_slug}/{location_slug}"
```

### Terminal Output Integration
```python
# Source: Existing terminal output pattern in search.py lines 706-707
# Add to main() function after fetching results:

manual_urls = generate_manual_urls(profile)
print(f"  Manual check URLs generated: {len(manual_urls)}")
print(f"  Sources: Wellfound | Indeed | LinkedIn | Glassdoor | We Work Remotely")
```

### HTML Report Integration
```python
# Source: Existing HTML manual URLs section in report.py lines 605-643
# No code changes needed - generate_manual_urls() returns the same structure
# HTML generation already handles multiple sources with grouping

# The _html_manual_urls_section() function will automatically:
# 1. Group URLs by source
# 2. Generate Bootstrap-styled links
# 3. Display with consistent formatting
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N/A (new feature) | Path-based URLs with slugs | 2026 (current) | Wellfound redesigned from AngelList Talent brand |
| Query string URLs | Path-based clean URLs | ~2020-2022 (estimated) | Modern web pattern, better SEO, cleaner user experience |

**Deprecated/outdated:**
- **AngelList Talent URLs**: Wellfound rebrand means old `angellist.com/talent` URLs likely redirect or are deprecated
- **Query-string search**: Modern job boards prefer path-based URLs (e.g., `/role/l/X/Y`) over query strings (e.g., `?role=X&location=Y`)

## Open Questions

1. **Location slug format edge cases**
   - What we know: Wellfound accepts city names, states, countries, and "remote" as location slugs
   - What's unclear: How Wellfound handles ambiguous locations (e.g., "Portland" - OR vs ME?), international locations with special characters
   - Recommendation: Use simple slugification as shown above. Users can manually adjust URLs if needed. The goal is a good starting point, not perfect accuracy.

2. **Additional search filters**
   - What we know: Wellfound supports filters for experience level, company stage, equity compensation, etc.
   - What's unclear: How to encode these in URLs (may require query params, not path-based)
   - Recommendation: Start with role + location only (matches user decisions in CONTEXT.md). Additional filters can be Phase 15+ if needed.

3. **URL validation necessity**
   - What we know: HEAD requests to Wellfound return 403 (bot protection)
   - What's unclear: Whether validation adds any value given that users will click and verify manually anyway
   - Recommendation: Skip validation for Wellfound URLs. User decision was "test with HEAD request but don't let failures block output" - just skip the test entirely to avoid log noise.

4. **Skills in query string**
   - What we know: Wellfound role slugs are predefined categories, not arbitrary keywords
   - What's unclear: Whether adding `?keywords=python+django` would help narrow results
   - Recommendation: Start without skills in URL. Role-based search is Wellfound's primary pattern. Skills can be added in Phase 15+ if user requests it.

## Sources

### Primary (HIGH confidence)
- [Wellfound URL structure research](https://wellfound.com/role/software-engineer) - Direct observation of live URL patterns
- [Wellfound remote jobs pattern](https://wellfound.com/role/r/software-engineer) - Confirmed `/role/r/` pattern for remote-only roles
- [Wellfound role + location pattern](https://wellfound.com/role/l/software-engineer/san-francisco) - Confirmed `/role/l/{role}/{location}` combined search pattern
- [Python urllib.parse documentation](https://docs.python.org/3/library/urllib.parse.html) - Official Python docs for URL encoding
- Existing codebase patterns in `job_radar/sources.py` (lines 950-1020) - Verified manual URL generation patterns for Indeed, LinkedIn, Glassdoor

### Secondary (MEDIUM confidence)
- [Wellfound Help - Remote job search filters](https://help.wellfound.com/article/762-remote-job-search-filters) - Confirms remote filtering capabilities
- [Wellfound Help - Setting up a search](https://help.wellfound.com/article/777-setting-up-a-search) - General search documentation
- [URL slug best practices (Semrush)](https://www.semrush.com/blog/what-is-a-url-slug/) - Standard practices for hyphenated slugs
- [Python URL encoding best practices (ioflood.com)](https://ioflood.com/blog/python-url-encode/) - urllib.parse usage patterns

### Tertiary (LOW confidence)
- Third-party scraper documentation (Apify, Scrapfly) - Confirms URL structure but not authoritative for Wellfound's supported patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib, already used in codebase
- Architecture: HIGH - Direct observation of Wellfound URLs + existing codebase patterns
- Pitfalls: MEDIUM - Based on general web scraping/URL generation experience, not Wellfound-specific documentation

**Research date:** 2026-02-10
**Valid until:** ~90 days (March 2026) - URL patterns are stable, but Wellfound could redesign or change structure
