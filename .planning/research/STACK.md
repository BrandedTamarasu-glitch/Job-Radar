# Stack Research: v1.2.0 Additions

**Domain:** Job aggregation CLI with PDF parsing
**Researched:** 2026-02-09
**Confidence:** HIGH

## Recommended Stack Additions

### PDF Parsing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pdfplumber | 0.11.9+ | Extract text from PDF resumes | Industry standard for structured PDF text extraction. Built on pdfminer.six with superior table/layout handling. Well-maintained with Python 3.8-3.14 support. Actively developed (latest release Jan 5, 2026). |
| Pillow | 11.0.0+ | Image processing for pdfplumber | Optional dependency for pdfplumber's visual debugging features (.to_image()). Already in project as build dependency. |

### API Authentication & Configuration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| python-dotenv | 1.0.1+ | Manage API keys via .env files | De facto standard for environment variable management in Python. Follows 12-factor app principles. Prevents hardcoded credentials. Simple load/access pattern fits CLI use case. |

### HTTP Client (No Change)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| requests | Current (2.x) | HTTP for all API calls | Already in stack. Works perfectly for Adzuna REST API, Authentic Jobs API, and Wellfound scraping. No need to add complexity. |

## Integration with Existing Stack

### Leverage Existing Infrastructure

**Cache module** (`job_radar/cache.py`):
- Adzuna and Authentic Jobs API responses can use existing `fetch_with_retry()` function
- Maintains 4-hour TTL consistency across all sources
- No new caching infrastructure needed

**BeautifulSoup** (already installed):
- Continue using for Wellfound scraping (no public API available)
- Reuse existing `HEADERS` pattern from `sources.py`
- Follows same scraping architecture as Dice, HN Hiring, RemoteOK, WWR

**Error handling patterns**:
- Reuse existing `JobResult` dataclass structure
- Maintain `parse_confidence` field for API vs scrape quality
- Follow established logging patterns in `sources.py`

### New Dependencies Only

Add to `pyproject.toml` dependencies:
```toml
dependencies = [
    "requests",
    "beautifulsoup4",
    "platformdirs>=4.0",
    "pyfiglet",
    "colorama",
    "certifi",
    "questionary",
    "pdfplumber>=0.11.9",      # NEW: PDF parsing
    "python-dotenv>=1.0.0"     # NEW: API key management
]
```

Pillow already exists in `[project.optional-dependencies].build` - no change needed.

## Installation

```bash
# Install new dependencies
pip install pdfplumber>=0.11.9 python-dotenv>=1.0.0

# Or update from pyproject.toml
pip install -e .
```

## API Authentication Patterns

### Adzuna API

**Authentication:** Query parameters (app_id, app_key)
**Implementation:**
```python
# Load from .env file
from dotenv import load_dotenv
import os

load_dotenv()
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Use in request
url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}&results_per_page=50&what={query}"
response = fetch_with_retry(url, headers=HEADERS)  # Reuse existing cache
```

**Setup:** User registers at https://developer.adzuna.com/ to get credentials.
**Rate limits:** Not publicly documented - implement defensive retry logic (already have `fetch_with_retry`).

### Authentic Jobs API

**Authentication:** API key parameter
**Implementation:**
```python
# Load from .env file
AUTHENTIC_JOBS_API_KEY = os.getenv("AUTHENTIC_JOBS_API_KEY")

# Use in request
url = f"https://authenticjobs.com/api/?api_key={AUTHENTIC_JOBS_API_KEY}&method=aj.jobs.search&keywords={query}"
response = fetch_with_retry(url, headers=HEADERS)
```

**Setup:** User signs up for Authentic Jobs developer program at https://authenticjobs.com/
**Endpoints:** Categories, tags, job listings, search by keyword/location/category.

### Wellfound (AngelList)

**Authentication:** None (web scraping)
**Status:** No public API available as of Feb 2026. API Tracker confirms no documented API endpoints.
**Implementation:**
- Continue using BeautifulSoup scraping pattern like existing sources
- Use existing `HEADERS` and `fetch_with_retry()` infrastructure
- Target search results pages: `https://wellfound.com/jobs?query={query}`
- Parse HTML structure (similar to Dice implementation)

**Risk:** Scraping may break if site redesigns. Mark with `parse_confidence="medium"` in JobResult.

## PDF Parsing Implementation Pattern

### Text Extraction

```python
import pdfplumber

def extract_resume_text(pdf_path: str) -> str:
    """Extract all text from PDF resume."""
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text
```

### Basic Field Extraction (NLP-free approach)

For v1.2.0 MVP, use regex patterns to extract common resume fields:
- Name (top of document)
- Email (email regex)
- Phone (phone regex)
- Skills (keyword matching against tech stack list)
- Experience (section heading detection)

No need for heavy NLP libraries (spaCy, pyresparser) in MVP. Keep it simple - extract text, let user verify/edit in wizard.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| PDF parsing | pdfplumber 0.11.9 | PyPDF2 3.0.1 | PyPDF2 officially deprecated. Development moved to `pypdf` as of 2023. Last release Dec 2022. |
| PDF parsing | pdfplumber 0.11.9 | pypdf 6.7.0 | pypdf is successor to PyPDF2, but focused on manipulation (merge/split). pdfplumber excels at structured text extraction and layout analysis - better fit for resume parsing. |
| PDF parsing | pdfplumber 0.11.9 | PyMuPDF | Faster but requires non-Python MuPDF installation. Adds complexity to PyInstaller builds. pdfplumber is pure Python (via pdfminer.six). |
| Resume parsing | Simple regex | pyresparser | pyresparser adds spaCy dependency (large model downloads). Overkill for v1.2.0 - just need text extraction, not full NLP parsing. User verifies fields in wizard anyway. |
| Env management | python-dotenv | environs | environs adds validation/type-casting. Unnecessary complexity for simple API key storage. dotenv is simpler, widely adopted. |
| HTTP client | requests | httpx | requests already in stack, works perfectly for REST APIs. No async needed in CLI. Don't fix what isn't broken. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| PyPDF2 | Officially deprecated since 2023. Last release Dec 2022. Development moved to pypdf. | pdfplumber (for text extraction) or pypdf (for manipulation) |
| oauth2 / authlib | Wellfound has no public API. Adzuna/Authentic Jobs use simple key-based auth, not OAuth. | python-dotenv for key management |
| spaCy / NLTK | Heavy dependencies (100MB+ models) for minimal gain. Resume text extraction doesn't need NLP in v1.2.0 - user verifies fields in wizard. | Simple regex + pdfplumber text extraction |
| pyresparser | Depends on spaCy, NLTK, pdfminer. Extraction accuracy varies. Adds complexity to build (model files, dependencies). | Direct pdfplumber + regex (simpler, predictable) |

## Stack Patterns by Use Case

**If API has authentication:**
- Store credentials in `.env` file (add to .gitignore)
- Load via `python-dotenv` at module import
- Pass as query params or headers per API spec
- Use existing `fetch_with_retry()` for caching + resilience

**If source requires scraping:**
- Use BeautifulSoup (already in stack)
- Reuse existing `HEADERS` constant
- Leverage `fetch_with_retry()` caching
- Set `parse_confidence="medium"` in JobResult
- Follow pattern from existing scrapers (Dice, HN Hiring, etc.)

**If parsing PDF resumes:**
- Use pdfplumber for text extraction
- Apply regex patterns for field detection
- Return structured dict for wizard pre-population
- Let user verify/correct in interactive wizard

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| pdfplumber 0.11.9+ | Python 3.8-3.14 | Tested on 3.10, 3.11, 3.12, 3.13, 3.14. Current project requires 3.10+. Fully compatible. |
| python-dotenv 1.0.0+ | Python 3.8+ | No known conflicts with existing dependencies. |
| Pillow 11.0.0+ | pdfplumber (optional) | Already in project as build dependency. Used for .to_image() debugging - not required for text extraction. |

## Environment Variable Configuration

Create `.env` file in project root (add to .gitignore):

```bash
# Adzuna API credentials (get from https://developer.adzuna.com/)
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here

# Authentic Jobs API key (get from https://authenticjobs.com/)
AUTHENTIC_JOBS_API_KEY=your_api_key_here
```

Load in `job_radar/sources.py`:

```python
from dotenv import load_dotenv
import os

# Load environment variables once at module import
load_dotenv()

# Access in fetcher functions
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
AUTHENTIC_JOBS_API_KEY = os.getenv("AUTHENTIC_JOBS_API_KEY")
```

**Fallback for missing keys:** Check for None and skip source with warning message, don't crash.

## Sources

### High Confidence (Official Documentation)

- [pdfplumber PyPI](https://pypi.org/project/pdfplumber/) - Version 0.11.9, Python requirements
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber) - Installation, dependencies, usage
- [pypdf PyPI](https://pypi.org/project/pypdf/) - Version 6.7.0, successor to PyPDF2
- [PyPDF2 PyPI](https://pypi.org/project/PyPDF2/) - Deprecation notice, version 3.0.1
- [Adzuna Developer Docs](https://developer.adzuna.com/overview) - Authentication, API structure
- [Wellfound API Tracker](https://apitracker.io/a/wellfound) - Confirms no public API
- [python-dotenv GitHub](https://github.com/theskumar/python-dotenv) - Official repository
- [python-dotenv PyPI](https://pypi.org/project/python-dotenv/) - Package info

### Medium Confidence (Community Sources Verified)

- [PyPDF2 vs pypdf Discussion](https://github.com/py-pdf/pypdf/discussions/2198) - Official project discussion on deprecation
- [pypdf vs X Comparisons](https://pypdf.readthedocs.io/en/stable/meta/comparisons.html) - Official comparison docs
- [I Tested 7 Python PDF Extractors](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257) - 2025 comparison
- [Authentic Jobs API - Public APIs Directory](https://publicapis.io/authentic-jobs-api) - API overview
- [python-dotenv Best Practices](https://oneuptime.com/blog/post/2026-01-26-work-with-environment-variables-python/view) - Recent guide

### Low Confidence (WebSearch Only)

- Resume parsing libraries (pyresparser, SpaCy approaches) - Not verified with official docs, community tools vary widely in quality

---

*Stack research for: Job Radar v1.2.0*
*Researched: 2026-02-09*
*Scope: PDF parsing and new job source API integration*
