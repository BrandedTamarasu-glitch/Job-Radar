# Pitfalls Research: v1.2.0 Job Board APIs & PDF Parsing

**Domain:** Python CLI job aggregator with API integration and PDF resume parsing
**Researched:** 2026-02-09
**Confidence:** HIGH

---

## Critical Pitfalls

### Pitfall 1: API Rate Limit Bypass Through Cache Confusion

**What goes wrong:**
Cache hits counting against rate limits because API requests happen before checking cache, or cache misses triggering rapid successive API calls that exceed rate limits.

**Why it happens:**
Job Radar's existing `fetch_with_retry()` checks cache but doesn't enforce rate limiting. When adding 3 new API-based sources (Wellfound, Adzuna, Authentic Jobs), parallel fetching of multiple job pages can quickly exceed API rate limits (Adzuna: generous but unspecified, Wellfound/Authentic Jobs: unknown limits).

**Consequences:**
- 429 Too Many Requests errors block job fetching
- Temporary IP bans from job boards
- Users see incomplete job listings without understanding why
- Existing 4-hour cache doesn't help if initial fetch exceeds limits

**Prevention:**
```python
# Use requests-ratelimiter (drop-in replacement for requests.Session)
from requests_ratelimiter import LimiterSession
from requests_cache import CacheMixin
from pyrate_limiter import Duration, RequestRate, Limiter

# Combine caching + rate limiting
class CachedLimiterSession(CacheMixin, LimiterSession):
    pass

session = CachedLimiterSession(
    limiter=Limiter(RequestRate(5, Duration.SECOND)),  # 5 req/sec per source
    backend='sqlite',
    expire_after=14400  # 4 hours (existing TTL)
)
```

**Warning signs:**
- HTTP 429 status codes in logs
- Incomplete job listings (some sources work, others fail)
- Retry attempts exhausted without 200 response
- Different results when running search minutes apart

**Phase to address:**
Phase 1: API Integration Foundation — implement rate limiting before connecting any APIs

**Sources:**
- [Python Request Optimization: Caching and Rate Limiting](https://medium.com/neural-engineer/python-request-optimization-caching-and-rate-limiting-79ceb5e6eb1e)
- [requests-ratelimiter on PyPI](https://pypi.org/project/requests-ratelimiter/)

---

### Pitfall 2: API Keys Hardcoded or Committed to Repository

**What goes wrong:**
Developer hardcodes API keys (Adzuna requires app_id + app_key, Wellfound/Authentic Jobs require keys) for testing, commits to Git, and keys appear in public repository or are exposed in PyInstaller executable.

**Why it happens:**
Project constraint: "No API keys required for basic usage" conflicts with reality that Adzuna, Wellfound, and Authentic Jobs all require authentication. Developer stores keys in code for convenience during development.

**Consequences:**
- API keys exposed in version control history (even after removal)
- Keys extracted from PyInstaller bundle via `pyinstaller-extractor` + decompile
- Malicious actors abuse exposed keys, exhausting rate limits
- API providers revoke keys, breaking the application for all users

**Prevention:**
```python
# Use keyring for cross-platform secure storage
import keyring

# First run: prompt user for API keys (optional flow)
def get_api_key(service: str) -> Optional[str]:
    """Retrieve API key from keyring, prompt if missing."""
    key = keyring.get_password("job-radar", service)
    if key is None and input(f"Enable {service}? (y/n): ").lower() == 'y':
        key = input(f"Enter {service} API key: ")
        keyring.set_password("job-radar", service, key)
    return key

# Use in fetchers
adzuna_key = get_api_key("adzuna") or None  # Falls back to None for no-key mode
```

**Warning signs:**
- API keys visible in `git log --all -S "app_key"`
- Config files (profile.json, config.json) contain keys
- .env files tracked in Git
- PyInstaller .toc file shows plaintext key strings

**Phase to address:**
Phase 1: API Integration Foundation — establish secure key management before any API implementation

**Sources:**
- [Securely Storing Credentials in Python with Keyring](https://medium.com/@forsytheryan/securely-storing-credentials-in-python-with-keyring-d8972c3bd25f)
- [Securing Sensitive Data in Python: Best Practices](https://systemweakness.com/securing-sensitive-data-in-python-best-practices-for-storing-api-keys-and-credentials-2bee9ede57ee)

---

### Pitfall 3: PDF Image Resumes Fail Silently with No Text Extracted

**What goes wrong:**
User uploads a PDF resume that's actually a scanned image or screenshot, parser returns empty strings for name/skills/experience, wizard pre-fill shows blank fields, user doesn't understand why.

**Why it happens:**
Text-based PDF parsers (pypdf, pdfplumber) can only extract highlightable text. Scanned PDFs or PDFs created from images (common from print-to-PDF workflows) have no text layer. pypdf's `extract_text()` succeeds but returns empty/whitespace strings.

**Consequences:**
- Silent failure: no error message, just blank wizard fields
- User wastes time manually entering everything (defeats purpose of PDF import)
- User blames the tool, not their PDF format
- Support burden: "PDF import doesn't work"

**Prevention:**
```python
import pypdf

def validate_pdf_has_text(pdf_path: str) -> tuple[bool, str]:
    """Check if PDF contains extractable text (not image-only)."""
    try:
        reader = pypdf.PdfReader(pdf_path)
        total_chars = sum(len(page.extract_text()) for page in reader.pages[:3])  # Check first 3 pages

        if total_chars < 50:  # Arbitrary threshold for "empty"
            return False, "This PDF appears to be a scanned image. Please use a text-based PDF."
        return True, ""
    except Exception as e:
        return False, f"Could not read PDF: {e}"

# In wizard flow
is_valid, error = validate_pdf_has_text(pdf_path)
if not is_valid:
    print(f"❌ {error}")
    print("💡 Export your resume as PDF from Word/Google Docs instead of scanning.")
    # Fall back to manual entry
```

**Warning signs:**
- All extracted fields empty despite non-zero PDF file size
- User reports "PDF has content but nothing imported"
- File size > 1MB for a 2-page resume (images are large)
- PDF opens fine in viewer but extract_text() returns ""

**Phase to address:**
Phase 2: PDF Resume Parser — validate PDF format before attempting extraction

**Sources:**
- [Why PDF Resumes Sometimes Fail in Online Submissions](https://www.resumly.ai/blog/why-pdf-resumes-sometimes-fail-in-online-submissions)
- [How to Fix OCR Errors in Scanned PDF Resumes](https://www.resumemakeroffer.com/en/blog/post/95162)

---

### Pitfall 4: Non-ASCII Encoding Errors in PDF Text Extraction

**What goes wrong:**
Resume contains non-ASCII characters (accented names like "José García", em-dashes, smart quotes), `extract_text()` raises UnicodeEncodeError or returns garbled text like "Jos� Garc�a".

**Why it happens:**
PDF fonts use custom encodings that pypdf may not decode correctly. When writing extracted text to profile.json (UTF-8), encoding mismatches cause errors. Legacy Python 2 code or Windows console defaults exacerbate this.

**Consequences:**
- Parser crashes with UnicodeEncodeError, no profile created
- Garbled text in profile.json breaks skill matching (José's "Python" becomes "Pýthon")
- International users disproportionately affected
- Wizard fails to save profile due to JSON encoding error

**Prevention:**
```python
import pypdf

def extract_text_safe(pdf_path: str) -> str:
    """Extract PDF text with encoding error handling."""
    try:
        reader = pypdf.PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            # pypdf 6.x handles encoding better, but still normalize
            text_parts.append(text)

        full_text = "\n".join(text_parts)
        # Normalize common issues
        full_text = full_text.encode('utf-8', errors='replace').decode('utf-8')
        return full_text
    except Exception as e:
        log.error(f"PDF extraction failed: {e}")
        return ""

# When writing to JSON
import json
with open("profile.json", "w", encoding="utf-8") as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)  # Preserve Unicode
```

**Warning signs:**
- `UnicodeEncodeError: 'charmap' codec can't encode character`
- Garbled characters in profile.json or terminal output
- Parser works on English resumes, fails on international names
- Windows users report more encoding issues than macOS/Linux

**Phase to address:**
Phase 2: PDF Resume Parser — handle encoding during extraction and JSON serialization

**Sources:**
- [Encoding issue in extract_text() - pypdf GitHub](https://github.com/mstamy2/PyPDF2/issues/235)
- [Extract Text from PDF pypdf Documentation](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)

---

### Pitfall 5: PyInstaller Missing PDF Library Dependencies

**What goes wrong:**
PyInstaller bundle includes pypdf code but misses binary dependencies or data files, executable crashes with `ModuleNotFoundError: No module named 'Crypto'` or `FileNotFoundError` for font mappings.

**Why it happens:**
pypdf has optional dependencies (PyCryptodome for encrypted PDFs) that PyInstaller doesn't auto-detect. pdfplumber uses pdfminer.six with font data files not collected by default. PyInstaller's static analysis misses runtime imports.

**Consequences:**
- Executable works in dev environment, crashes in production
- "PDF import" feature unavailable in standalone .exe/.app
- Users can't use key v1.2.0 feature on Windows/macOS builds
- Rollback required, milestone fails

**Prevention:**
```python
# In .spec file
a = Analysis(
    ['job_radar/cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        # pdfminer.six font mappings (if using pdfplumber)
        (os.path.join(site_packages, 'pdfminer', 'cmap'), 'pdfminer/cmap'),
    ],
    hiddenimports=[
        'pypdf',           # Ensure pypdf is collected
        'Crypto',          # PyCryptodome for encrypted PDFs (optional)
        'pdfplumber',      # If using pdfplumber
        'pdfminer',        # pdfplumber dependency
        'pdfminer.six',
    ],
    hookspath=[],
    ...
)

# Test before release
# 1. Build executable with PyInstaller
# 2. Test PDF import on clean VM (no Python installed)
# 3. Try encrypted PDF, image PDF, multi-page PDF
```

**Warning signs:**
- `ModuleNotFoundError` only in bundled executable, not in source
- PDF import works locally (pip install) but not in .exe
- `import pypdf` succeeds but `pypdf.PdfReader()` fails
- Different behavior on Windows vs macOS builds

**Phase to address:**
Phase 2: PDF Resume Parser — configure PyInstaller hidden imports during implementation, test in CI

**Sources:**
- [PyInstaller Common Issues and Pitfalls](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html)
- [PyMuPDF with PyInstaller ModuleNotFoundError](https://github.com/pymupdf/PyMuPDF/issues/712)

---

## Moderate Pitfalls

### Pitfall 6: Cache-Only Mode Breaks with API Sources

**What goes wrong:**
User relies on cache-only mode (4-hour TTL) but new API sources (Wellfound, Adzuna, Authentic Jobs) have different data freshness patterns than scraped sources. Cached API responses become stale but aren't refreshed because user assumes cache is sufficient.

**Why it happens:**
BeautifulSoup scrapers fetch HTML which changes when new jobs posted. APIs return paginated JSON that may include `posted_date` fields allowing client-side freshness checks. Current cache uses URL hash, doesn't inspect response content for staleness.

**Prevention:**
```python
# Extend cache metadata to track API response timestamps
def _write_cache(url: str, body: str, response_headers: dict = None):
    """Write response to cache with API metadata."""
    entry = {
        "url": url,
        "ts": time.time(),
        "body": body,
    }
    # Store API rate limit headers for intelligent retry
    if response_headers:
        entry["rate_limit_remaining"] = response_headers.get("X-RateLimit-Remaining")
        entry["rate_limit_reset"] = response_headers.get("X-RateLimit-Reset")

    with open(_cache_path(url), "w", encoding="utf-8") as f:
        json.dump(entry, f)

# Check rate limits before refresh
def should_refresh_cache(url: str) -> bool:
    """Decide if cache should be refreshed based on rate limits."""
    entry = _read_cache_entry(url)
    if entry and entry.get("rate_limit_remaining") == "0":
        reset_time = int(entry.get("rate_limit_reset", 0))
        if time.time() < reset_time:
            return False  # Wait until rate limit resets
    return True
```

**Phase to address:**
Phase 1: API Integration Foundation — extend cache to store API response headers

---

### Pitfall 7: PDF Parser Over-Extracts (Noise in Skills)

**What goes wrong:**
Parser extracts body text including headers/footers ("Page 1 of 2"), URLs ("github.com/username"), email signatures, and treats them as skills. Profile ends up with junk: `["Page", "of", "2", "github.com"]`.

**Why it happens:**
Rule-based extraction scans entire PDF text for skill keywords without context awareness. Resume formatting (headers, footers, contact info) isn't filtered out. pypdf's `extract_text()` returns all text in reading order, including non-content.

**Prevention:**
```python
# Filter extracted text to remove noise
import re

def clean_resume_text(text: str) -> str:
    """Remove headers, footers, URLs from resume text."""
    # Remove page numbers
    text = re.sub(r'\bPage\s+\d+\s+of\s+\d+\b', '', text, flags=re.IGNORECASE)
    # Remove URLs
    text = re.sub(r'https?://[^\s]+', '', text)
    # Remove email addresses
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    # Remove phone numbers
    text = re.sub(r'\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', '', text)
    return text

# Extract skills from known sections only
def extract_skills_from_section(text: str) -> list[str]:
    """Find skills section and extract from that region only."""
    # Look for "Skills", "Technical Skills", "Technologies" headers
    skills_pattern = r'(?:Technical\s+)?Skills.*?(?=\n[A-Z][a-z]+:|\Z)'
    match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return parse_skills(match.group())
    return parse_skills(text)  # Fallback to full text
```

**Phase to address:**
Phase 2: PDF Resume Parser — implement section detection and text cleaning

---

### Pitfall 8: API Response Schema Changes Break Parsing

**What goes wrong:**
Adzuna or Wellfound changes JSON response structure (adds nesting, renames field `location` → `location.display_name`), parser expects old schema, raises `KeyError`, job source fails silently.

**Why it happens:**
Third-party APIs evolve without versioning or deprecation notices. Job Radar's parsers assume fixed schema. Current scraper pattern uses broad `except Exception` for crash tolerance, which hides schema changes.

**Prevention:**
```python
# Defensive parsing with schema validation
def parse_adzuna_job(data: dict) -> Optional[dict]:
    """Parse Adzuna API response with defensive key access."""
    try:
        return {
            "title": data.get("title", "Unknown Title"),
            "company": data.get("company", {}).get("display_name", "Unknown Company"),
            "location": data.get("location", {}).get("display_name", "Remote"),
            "url": data.get("redirect_url", ""),
            "description": data.get("description", ""),
            "salary": data.get("salary_min"),  # May be None
        }
    except (KeyError, TypeError, AttributeError) as e:
        log.warning(f"Failed to parse Adzuna job: {e} | Data: {data}")
        return None  # Skip this job, continue with others

# Log schema mismatches for debugging
def validate_response_schema(data: dict, source: str):
    """Check if API response matches expected schema."""
    expected_keys = {"title", "company", "location", "url"}
    missing = expected_keys - set(data.keys())
    if missing:
        log.warning(f"{source} API response missing keys: {missing}")
```

**Phase to address:**
Phase 3: Individual Source Integration — implement defensive parsing for each API

---

### Pitfall 9: PDF Tables Extracted Out of Order

**What goes wrong:**
Resume uses tables for skills (3-column layout: "Python | Java | JavaScript"), `extract_text()` reads left-to-right, top-to-bottom, resulting in garbled order: "Python React Django Java Node.js Express JavaScript".

**Why it happens:**
pypdf extracts text in PDF rendering order, which for tables is often horizontal (entire first column, then second column). Skill categories split across columns become interleaved.

**Prevention:**
```python
# Use pypdf's layout mode (v4.0+) for better table handling
from pypdf import PdfReader

def extract_text_with_layout(pdf_path: str) -> str:
    """Extract PDF text preserving layout structure."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        # layout mode preserves spatial positioning
        text = page.extract_text(extraction_mode="layout")
        pages_text.append(text)
    return "\n\n".join(pages_text)

# Alternative: use pdfplumber for table detection
import pdfplumber

def extract_tables(pdf_path: str) -> list[list[str]]:
    """Extract tables from PDF as structured data."""
    with pdfplumber.open(pdf_path) as pdf:
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            all_tables.extend(tables)
    return all_tables
```

**Phase to address:**
Phase 2: PDF Resume Parser — test with table-heavy resumes, use layout mode

**Sources:**
- [pypdf Text Extraction Improvements](https://github.com/py-pdf/pypdf/discussions/2038)

---

### Pitfall 10: Authentication Token Expiry Not Handled

**What goes wrong:**
Job board API uses short-lived tokens (1-hour expiry), Job Radar caches token at startup, after 1 hour all API requests return 401 Unauthorized, job fetching fails for remainder of search.

**Why it happens:**
OAuth/JWT tokens expire but caching doesn't account for token lifecycle. Wellfound/Authentic Jobs may use token-based auth. Current implementation assumes API keys are permanent.

**Prevention:**
```python
# Token refresh logic
class TokenManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.token = None
        self.token_expiry = 0

    def get_valid_token(self) -> str:
        """Return valid token, refreshing if needed."""
        if time.time() >= self.token_expiry - 60:  # Refresh 1min before expiry
            self.token, self.token_expiry = self._refresh_token()
        return self.token

    def _refresh_token(self) -> tuple[str, int]:
        """Fetch new token from API."""
        resp = requests.post(
            "https://api.example.com/auth/token",
            json={"api_key": self.api_key}
        )
        data = resp.json()
        return data["access_token"], time.time() + data["expires_in"]

# Use in API calls
token_manager = TokenManager(api_key)
headers = {"Authorization": f"Bearer {token_manager.get_valid_token()}"}
```

**Phase to address:**
Phase 3: Individual Source Integration — implement token refresh for sources that require it

---

## Minor Pitfalls

### Pitfall 11: PDF Password Protection Blocks Extraction

**What goes wrong:**
User uploads password-protected PDF (common for resumes sent to recruiters), `PdfReader()` raises `pypdf.errors.FileNotDecryptedError`, wizard crashes.

**Prevention:**
```python
def extract_with_password_prompt(pdf_path: str) -> str:
    """Handle password-protected PDFs gracefully."""
    try:
        reader = pypdf.PdfReader(pdf_path)
        if reader.is_encrypted:
            password = input("This PDF is password-protected. Enter password: ")
            if not reader.decrypt(password):
                print("❌ Incorrect password. Using manual entry instead.")
                return ""
        return extract_text_safe(reader)
    except pypdf.errors.FileNotDecryptedError:
        print("❌ Could not decrypt PDF. Using manual entry instead.")
        return ""
```

**Phase to address:**
Phase 2: PDF Resume Parser — add password handling in wizard PDF import flow

---

### Pitfall 12: API Documentation Lies About No-Auth Access

**What goes wrong:**
Documentation claims "public job listings don't require authentication," developer implements no-auth flow, API returns 401 or rate limits aggressively (10 req/hour vs 1000 req/hour for authenticated users).

**Why it happens:**
Job board APIs have tiered access: unauthenticated (severely limited), API key (standard), OAuth (full access). Docs don't clarify which tier is practical for production use.

**Prevention:**
- Test both authenticated and unauthenticated modes during Phase 3
- Measure rate limits empirically (make 20 test requests, check headers)
- Document actual limits in code comments
- Provide graceful degradation: "Adzuna requires API key for reliable access. Get yours at developer.adzuna.com"

**Phase to address:**
Phase 3: Individual Source Integration — validate authentication requirements for each API

---

### Pitfall 13: PDF Font Embedding Issues in PyInstaller

**What goes wrong:**
PyInstaller bundle works locally but fails on user machines with `FileNotFoundError: pdfminer/cmap/...` because font mapping files weren't included in bundle.

**Prevention:**
See Pitfall 5 for PyInstaller datas configuration. Test on clean VM.

**Phase to address:**
Phase 4: Testing & Polish — add CI test for PDF import in bundled executable

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip rate limit handling initially | Faster MVP, fewer dependencies | 429 errors in production, IP bans | Never — rate limiting is critical for API integrations |
| Use only pypdf (not pdfplumber) | Smaller bundle size (1 dependency) | Poor table extraction, layout issues | Acceptable for MVP if tables are rare in target resumes |
| Store API keys in plain text config | Zero friction setup | Security risk, keys exposed in repo/bundle | Never — use keyring from day 1 |
| Hardcode job board response schemas | Less code, no validation overhead | Silent failures when APIs change | Never — defensive parsing is table stakes |
| Skip PDF format validation | Simpler code path | Silent failures with image PDFs | Never — validation prevents 80% of support issues |
| Use broad `except Exception` in PDF parser | Crash tolerance | Hides bugs, unclear error messages | Acceptable in scrapers, NOT acceptable in PDF parser |
| Cache API responses indefinitely | Reduces API calls | Stale job listings, out-of-date data | Only if combined with manual refresh option |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Adzuna API | Assuming free tier has no limits | Check `X-RateLimit-*` headers, implement exponential backoff on 429 |
| Wellfound | Using legacy AngelList endpoints | Verify current API base URL, Wellfound rebrand may have changed domains |
| Authentic Jobs | Passing `api_key` as header instead of query param | Use `?api_key=${key}` in URL per docs |
| pypdf | Using `PyPDF2` import (deprecated since 2023) | Import `pypdf` (lowercase), all new development on pypdf |
| requests cache | Caching 429 rate limit responses | Check status code before caching: `if resp.status_code == 200: cache(resp)` |
| PyInstaller + pypdf | Importing `fitz` instead of `pymupdf` | Use `import pymupdf` to avoid conflict with unrelated `fitz` package |
| keyring | Assuming Windows Credential Manager always available | Fallback to encrypted file storage if `keyring.get_keyring()` returns None |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Sequential API requests for paginated results | 3-5 minutes for full search, users complain of slowness | Use `concurrent.futures.ThreadPoolExecutor` to fetch pages in parallel | 50+ results across 3 sources |
| Re-parsing same PDF multiple times | Wizard lag when user edits profile | Cache parsed PDF data in memory during wizard session | 10+ page resumes |
| No request timeout on API calls | Hanging indefinitely on slow API, user kills process | Set `timeout=15` on all requests.get() calls (already done in cache.py) | First flaky API encountered |
| Loading entire PDF into memory | 100MB+ memory usage for 5-page resume | Stream PDF reading page-by-page with pypdf's page iterator | 20+ page resumes |
| Cache directory unbounded growth | 1GB+ .cache directory after weeks of use | Implement cache size limit + LRU eviction (not just TTL) | After 100+ searches |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging API keys in debug mode | Keys appear in log files, exposed if logs shared for debugging | Use `log.debug(f"API key: {'*' * len(api_key)}")` for logging |
| Storing API keys in PyInstaller bundle | Extractable with `pyinstaller-extractor` + decompile | Always use keyring, fail if key not found rather than bundling default |
| Not validating PDF file size before extraction | DoS via 500MB "resume" PDF | Reject PDFs > 10MB before calling `PdfReader()` |
| SSRF via user-provided PDF URLs | User inputs `file:///etc/passwd`, parser reads local files | Only accept file uploads, never URLs to PDF locations |
| Trusting API response without sanitization | XSS in HTML report if job description contains `<script>` | Escape HTML in templates, use Jinja2 autoescaping (already in v1.1) |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback during PDF parsing | User sees blank wizard screen for 10s, assumes crash | Show progress: "Extracting text from resume..." spinner |
| Error message: "Failed to parse PDF" | User doesn't know why or how to fix | Specific error: "PDF is password-protected. Please upload unlocked version." |
| API key required but not explained | User hits rate limit, sees "Failed to fetch Adzuna jobs" | Show: "Adzuna requires free API key. Get yours at: [URL] (optional but recommended)" |
| All job sources fail silently | Report shows 0 jobs, user doesn't know if search worked | Summary: "Fetched 45 jobs (Dice: 20, RemoteOK: 15, HN: 10, Adzuna: 0 [rate limited])" |
| PDF import pre-fills wrong data | Wizard shows "Page 1" as name | Show preview: "Extracted name: 'Page 1' — Edit below if incorrect" |

---

## "Looks Done But Isn't" Checklist

- [ ] **API Integration:** Rate limiting implemented and tested with rapid requests (not just happy path)
- [ ] **API Integration:** 429 response handling includes exponential backoff and doesn't exhaust retries immediately
- [ ] **API Integration:** Cache doesn't store rate limit error responses as valid data
- [ ] **API Key Storage:** Keys never appear in Git history (`git log -S "api_key"` returns nothing)
- [ ] **API Key Storage:** `.gitignore` includes any config files that might contain keys
- [ ] **PDF Parser:** Image-only PDFs detected and rejected with helpful error message
- [ ] **PDF Parser:** Non-ASCII characters (José, München) preserved through extraction → JSON → display
- [ ] **PDF Parser:** Password-protected PDFs handled gracefully (prompt or skip, not crash)
- [ ] **PDF Parser:** Table-based resume layouts extract in correct reading order
- [ ] **PyInstaller:** Hidden imports configured for pypdf and any dependencies
- [ ] **PyInstaller:** PDF import tested in bundled .exe/.app on clean VM (no dev environment)
- [ ] **Error Handling:** Each API source fails independently (one broken API doesn't crash entire search)
- [ ] **Testing:** CI tests include rate limit simulation (mock 429 response)
- [ ] **Testing:** CI tests include malformed PDF (empty, corrupted, image-only)
- [ ] **Documentation:** README explains how to get API keys for Adzuna/Wellfound/Authentic Jobs

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| API rate limited mid-search | LOW | Use cached results, show partial data, retry next run (cache will be fresh) |
| Hardcoded API key leaked | MEDIUM | Revoke old key via API provider dashboard, generate new key, update keyring storage, push hotfix release |
| PyInstaller missing PDF deps | HIGH | Add hidden imports to .spec, rebuild, re-release executables, notify users to download new version |
| PDF encoding corruption in profile.json | LOW | Delete profile.json, re-run wizard (with manual entry as fallback) |
| Cache directory corrupted | LOW | Run `job-radar --clear-cache` (existing command), next search rebuilds cache |
| Authentication token expired | LOW | Token manager auto-refreshes on next request (if implemented), no user action needed |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| API Rate Limit Bypass Through Cache Confusion | Phase 1: API Integration Foundation | Load test: 100 rapid requests don't trigger 429s due to rate limiter |
| API Keys Hardcoded or Committed | Phase 1: API Integration Foundation | `git log --all -S "app_key"` returns no commits, keyring stores all keys |
| PDF Image Resumes Fail Silently | Phase 2: PDF Resume Parser | Test with scanned PDF, verify error message shown |
| Non-ASCII Encoding Errors | Phase 2: PDF Resume Parser | Test with resume containing "José García", verify profile.json preserves UTF-8 |
| PyInstaller Missing PDF Dependencies | Phase 2: PDF Resume Parser | CI builds executable, tests PDF import on Ubuntu/Windows/macOS VMs |
| Cache-Only Mode Breaks with API Sources | Phase 1: API Integration Foundation | Verify cache stores API rate limit headers |
| PDF Parser Over-Extracts | Phase 2: PDF Resume Parser | Test with resume containing "Page 1 of 2" footer, verify not in skills list |
| API Response Schema Changes | Phase 3: Individual Source Integration | Mock API returns old schema, verify defensive parsing doesn't crash |
| PDF Tables Extracted Out of Order | Phase 2: PDF Resume Parser | Test with 3-column skills table, verify skills list is coherent |
| Authentication Token Expiry | Phase 3: Individual Source Integration | Sleep 61min in test, verify token auto-refreshes (if applicable) |
| PDF Password Protection | Phase 2: PDF Resume Parser | Test with encrypted PDF, verify password prompt or graceful skip |
| API Documentation Lies About No-Auth | Phase 3: Individual Source Integration | Test unauthenticated requests, measure rate limits, document findings |
| PDF Font Embedding Issues | Phase 4: Testing & Polish | Test bundled executable on clean VM with multi-font PDF |

---

## Sources

**API Rate Limiting:**
- [Implementing Effective API Rate Limiting in Python](https://medium.com/neural-engineer/implementing-effective-api-rate-limiting-in-python-6147fdd7d516)
- [Python Request Optimization: Caching and Rate Limiting](https://medium.com/neural-engineer/python-request-optimization-caching-and-rate-limiting-79ceb5e6eb1e)
- [requests-ratelimiter on PyPI](https://pypi.org/project/requests-ratelimiter/)
- [Best Practices for Avoiding Rate Limiting | Zendesk](https://developer.zendesk.com/documentation/ticketing/using-the-zendesk-api/best-practices-for-avoiding-rate-limiting/)

**PDF Parsing:**
- [Why PDF Resumes Sometimes Fail in Online Submissions](https://www.resumly.ai/blog/why-pdf-resumes-sometimes-fail-in-online-submissions)
- [Top 10 ATS Resume Mistakes to Avoid in 2026](https://www.careerflow.ai/blog/ats-resume-mistakes-to-avoid)
- [pypdf Text Extraction Documentation](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- [Encoding issue in extract_text() - pypdf GitHub](https://github.com/py-pdf/pypdf/issues/260)
- [Text Extraction Improvements Discussion](https://github.com/py-pdf/pypdf/discussions/2038)

**PyInstaller:**
- [PyInstaller Common Issues and Pitfalls](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html)
- [PyMuPDF ModuleNotFoundError with PyInstaller](https://github.com/pymupdf/PyMuPDF/issues/712)

**Security:**
- [Securely Storing Credentials in Python with Keyring](https://medium.com/@forsytheryan/securely-storing-credentials-in-python-with-keyring-d8972c3bd25f)
- [Securing Sensitive Data in Python: Best Practices](https://systemweakness.com/securing-sensitive-data-in-python-best-practices-for-storing-api-keys-and-credentials-2bee9ede57ee)

**Job Board APIs:**
- [Adzuna API Overview](https://developer.adzuna.com/overview)
- [AngelList API Documentation](https://docs.angellist.com/docs/overview)
- [Authentic Jobs API](https://publicapis.io/authentic-jobs-api)

---

*Research completed for Job Radar v1.2.0 milestone: Enhanced Sources & Onboarding*
*Focus: API integration pitfalls (rate limiting, authentication, schema changes) and PDF parsing pitfalls (encoding, format detection, PyInstaller bundling)*
