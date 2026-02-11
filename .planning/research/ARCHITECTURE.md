# Architecture Research: v1.2.0 Job Sources and PDF Parsing

**Domain:** Job aggregation CLI with resume parsing
**Researched:** 2026-02-09
**Confidence:** HIGH

## Executive Summary

v1.2.0 adds 3 new job sources (Wellfound, Adzuna, Authentic Jobs) and PDF resume import to the existing Job Radar architecture. The integration follows established patterns: new sources implement the same `fetch_*() -> JobResult[]` contract as existing sources, and PDF parsing integrates as an optional first step in the wizard flow. Both additions preserve backward compatibility and require minimal changes to core modules.

**Key architectural insight:** The current single-file `sources.py` pattern and dataclass-based `JobResult` contract make adding sources trivial (3 functions + dispatcher update). The wizard's sequential prompt architecture naturally accommodates PDF pre-filling by setting default values on existing prompts.

## Standard Architecture

### Current System Overview (v1.1.0)

```
┌─────────────────────────────────────────────────────────────┐
│                       CLI Entry Point                        │
│                  (job_radar/search.py)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Wizard (first run)                      │   │
│  │         (job_radar/wizard.py)                        │   │
│  │   - Questionary prompts                              │   │
│  │   - Writes profile.json + config.json                │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Fetch → Score → Report                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Dice    │  │ HN      │  │RemoteOK │  │  WWR    │        │
│  │fetch()  │  │fetch()  │  │fetch()  │  │fetch()  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                        │                                     │
│                   JobResult[]                                │
│                        │                                     │
├───────────────────────┼─────────────────────────────────────┤
│              Scoring (scoring.py)                            │
│              - score_job(job, profile)                       │
├───────────────────────┼─────────────────────────────────────┤
│              Tracking (tracker.py)                           │
│              - mark_seen() / get_stats()                     │
├───────────────────────┼─────────────────────────────────────┤
│              Report Generation (report.py)                   │
│              - generate_report() → HTML + Markdown          │
└─────────────────────────────────────────────────────────────┘
```

### v1.2.0 Architecture (Proposed)

```
┌─────────────────────────────────────────────────────────────┐
│                       CLI Entry Point                        │
│                  (job_radar/search.py)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Enhanced Wizard                         │   │
│  │         (job_radar/wizard.py)                        │   │
│  │                                                      │   │
│  │   [1] PDF Import (OPTIONAL)                          │   │
│  │       - File path prompt                             │   │
│  │       - Extract via pdf_parser.py                    │   │
│  │       - Pre-fill profile fields                      │   │
│  │                                                      │   │
│  │   [2] Questionary prompts                            │   │
│  │       - Pre-filled if PDF provided                   │   │
│  │       - Allow editing all fields                     │   │
│  │                                                      │   │
│  │   [3] Write profile.json + config.json               │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Fetch → Score → Report                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌──────┐ ┌──────┐ ┌─────┐ │
│  │Dice │ │ HN  │ │RemOK│ │ WWR │ │Wllfnd│ │Adzuna│ │Auth │ │
│  │     │ │     │ │     │ │     │ │      │ │      │ │Jobs │ │
│  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └───┬──┘ └───┬──┘ └──┬──┘ │
│     │       │       │       │        │        │       │    │
│     └───────┴───────┴───────┴────────┴────────┴───────┘    │
│                           │                                  │
│                      JobResult[]                             │
│                           │                                  │
├──────────────────────────┼──────────────────────────────────┤
│              Scoring (scoring.py)                            │
├──────────────────────────┼──────────────────────────────────┤
│              Tracking (tracker.py)                           │
├──────────────────────────┼──────────────────────────────────┤
│              Report Generation (report.py)                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **sources.py** | Job board integrations - each with `fetch_*()` function | Web scraping (BeautifulSoup) or API calls (requests) returning `JobResult[]` |
| **wizard.py** | Interactive profile creation via Questionary prompts | Sequential prompts → validation → atomic JSON write |
| **pdf_parser.py** (NEW) | Extract structured data from resume PDF | pdfplumber text extraction → regex parsing → dict |
| **scoring.py** | Match jobs against profile | Keyword matching, weighted scoring algorithm |
| **tracker.py** | Deduplication across runs | Hash-based seen tracking in SQLite |
| **report.py** | Generate HTML/Markdown reports | Jinja2 templates with scored results |

## Recommended Project Structure

**Current structure:**
```
job_radar/
├── __init__.py
├── __main__.py
├── search.py           # CLI entry point
├── wizard.py           # Profile creation wizard
├── sources.py          # All job board fetchers in one file
├── scoring.py          # Job scoring logic
├── tracker.py          # Deduplication
├── report.py           # Report generation
├── cache.py            # HTTP cache
├── config.py           # Config loading
├── paths.py            # Platform dirs
└── browser.py          # Auto-open HTML
```

**Proposed v1.2.0 structure:**
```
job_radar/
├── __init__.py
├── __main__.py
├── search.py           # CLI entry point (minimal changes)
├── wizard.py           # Enhanced with PDF import step
├── pdf_parser.py       # NEW: Resume parsing module
├── sources.py          # Enhanced with 3 new fetchers
├── scoring.py          # (no changes)
├── tracker.py          # (no changes)
├── report.py           # (no changes)
├── cache.py            # (no changes)
├── config.py           # (no changes)
├── paths.py            # (no changes)
└── browser.py          # (no changes)
```

### Structure Rationale

- **Single sources.py file preserved:** Current pattern works well - all fetchers return same `JobResult` dataclass, making parallel execution simple
- **pdf_parser.py as separate module:** Isolates PDF dependencies (pdfplumber) and parsing logic from wizard flow
- **wizard.py enhanced, not replaced:** Maintain existing Questionary flow, add PDF import as optional first step
- **No breaking changes to core:** search.py, scoring.py, tracker.py, report.py remain untouched

## Architectural Patterns

### Pattern 1: Uniform Job Source Interface

**What:** All job board fetchers implement same contract: `fetch_*(query, location) -> list[JobResult]`

**When to use:** When adding new job sources (Wellfound, Adzuna, Authentic Jobs)

**Trade-offs:**
- ✅ Parallel execution via ThreadPoolExecutor works out-of-box
- ✅ Easy to add/remove sources without touching orchestration
- ✅ Consistent error handling and caching
- ⚠️ Forces all sources to return same dataclass (may lose source-specific fields)
- ⚠️ No per-source configuration (API keys must be global or env vars)

**Example:**
```python
# In sources.py

def fetch_wellfound(query: str, location: str = "") -> list[JobResult]:
    """Fetch job listings from Wellfound (AngelList) by web scraping."""
    results = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://wellfound.com/jobs?q={encoded_q}"
    if location:
        url += f"&l={urllib.parse.quote_plus(location)}"

    body = fetch_with_retry(url, headers=HEADERS)
    if body is None:
        log.warning("[Wellfound] Fetch failed for '%s'", query)
        return results

    try:
        soup = BeautifulSoup(body, "html.parser")
        # Parse job cards...
        for card in soup.select("div.job-card"):
            results.append(JobResult(
                title=card.select_one(".title").text.strip(),
                company=card.select_one(".company").text.strip(),
                location=card.select_one(".location").text.strip(),
                arrangement=_parse_arrangement(card.text),
                salary="Not listed",
                date_posted=card.select_one(".posted").text.strip(),
                description=card.select_one(".description").text.strip()[:200],
                url=card.select_one("a")["href"],
                source="Wellfound",
            ))
    except Exception as e:
        log.error("[Wellfound] Parse error: %s", e)

    return results


def fetch_adzuna(query: str, location: str = "") -> list[JobResult]:
    """Fetch job listings from Adzuna API."""
    results = []

    # Adzuna requires API credentials
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        log.warning("[Adzuna] Missing API credentials (ADZUNA_APP_ID, ADZUNA_APP_KEY)")
        return results

    # Adzuna API endpoint
    country = "us"
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "where": location,
        "results_per_page": 50,
        "sort_by": "date",
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for job in data.get("results", []):
            results.append(JobResult(
                title=job.get("title", "Unknown"),
                company=job.get("company", {}).get("display_name", "Unknown"),
                location=job.get("location", {}).get("display_name", location or "Unknown"),
                arrangement=_parse_arrangement(job.get("description", "")),
                salary=job.get("salary_min", "Not listed"),
                date_posted=job.get("created", "Unknown"),
                description=job.get("description", "")[:200],
                url=job.get("redirect_url", ""),
                source="Adzuna",
            ))
    except Exception as e:
        log.error("[Adzuna] API error: %s", e)

    return results


# Update fetch_all() dispatcher:
def fetch_all(profile: dict, on_progress=None, on_source_progress=None):
    # ... existing setup ...

    def run_query(q):
        if q["source"] == "dice":
            return fetch_dice(q["query"], q.get("location", ""))
        elif q["source"] == "hn_hiring":
            return fetch_hn_hiring(q["query"])
        elif q["source"] == "remoteok":
            return fetch_remoteok(q["query"])
        elif q["source"] == "weworkremotely":
            return fetch_weworkremotely(q["query"])
        elif q["source"] == "wellfound":  # NEW
            return fetch_wellfound(q["query"], q.get("location", ""))
        elif q["source"] == "adzuna":  # NEW
            return fetch_adzuna(q["query"], q.get("location", ""))
        elif q["source"] == "authenticjobs":  # NEW
            return fetch_authenticjobs(q["query"])
        return []

    # ... rest unchanged ...
```

### Pattern 2: Wizard Pre-Fill Flow

**What:** PDF parsing as optional first step in wizard, pre-filling subsequent prompts

**When to use:** When extending existing wizard with resume import feature

**Trade-offs:**
- ✅ Maintains backward compatibility (wizard works without PDF)
- ✅ Users can edit all pre-filled values
- ✅ Clear separation: extraction → validation → storage
- ⚠️ PDF extraction errors don't block wizard (degrade gracefully)
- ⚠️ Adds dependency on pdfplumber (35MB+ with dependencies)

**Example:**
```python
# In wizard.py

def run_setup_wizard() -> bool:
    """Run interactive setup wizard with optional PDF import."""
    from .paths import get_data_dir

    # Wizard header
    print("\n" + "=" * 60)
    print("🎯 Job Radar - First Time Setup")
    print("=" * 60)

    # NEW: PDF import prompt (optional)
    print("\n💡 Tip: Upload your resume PDF to auto-fill your profile.\n")

    pdf_choice = questionary.select(
        "How would you like to create your profile?",
        choices=[
            "Import from resume PDF (recommended)",
            "Fill out manually",
        ],
        style=custom_style
    ).ask()

    # Extract data from PDF if provided
    extracted_data = {}
    if pdf_choice and "PDF" in pdf_choice:
        pdf_path_str = questionary.text(
            "Path to your resume PDF:",
            instruction="Enter full path (e.g., /Users/name/resume.pdf)",
            validate=lambda p: (p.endswith('.pdf') and Path(p).exists())
                or "Please enter a valid path to a PDF file",
            style=custom_style
        ).ask()

        if pdf_path_str:
            print(f"\n📄 Parsing resume PDF...")
            try:
                from .pdf_parser import extract_resume_data
                extracted_data = extract_resume_data(pdf_path_str)
                print(f"✅ Extracted: {', '.join(extracted_data.keys())}")
            except Exception as e:
                print(f"\n⚠️  PDF parsing failed: {e}")
                print("Continuing with manual entry...\n")
                extracted_data = {}

    print("\nTip: Type /back at any prompt to return to the previous question.\n")

    # Rest of wizard uses extracted_data to pre-fill defaults
    # Modify prompt_kwargs['default'] = extracted_data.get(key, '')
    # ... existing wizard code continues ...
```

### Pattern 3: PDF Parser Module

**What:** Standalone module for resume text extraction and field parsing

**When to use:** When adding PDF resume import to wizard

**Trade-offs:**
- ✅ Isolates PDF dependencies (easy to mock in tests)
- ✅ Single responsibility (extraction only, wizard handles validation)
- ✅ Graceful degradation if pdfplumber fails
- ⚠️ Regex parsing fragile across resume formats
- ⚠️ No NLP = lower accuracy for skills/titles extraction

**Example:**
```python
# New file: job_radar/pdf_parser.py

"""Resume PDF parsing and data extraction."""

import re
from pathlib import Path

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def extract_resume_data(pdf_path: str | Path) -> dict:
    """Extract structured data from a resume PDF.

    Parameters
    ----------
    pdf_path : str | Path
        Path to resume PDF file

    Returns
    -------
    dict
        Extracted data with keys: name, years_experience, titles, skills

    Raises
    ------
    ImportError
        If pdfplumber is not installed
    ValueError
        If PDF cannot be read or parsed
    """
    if not PDF_SUPPORT:
        raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise ValueError(f"PDF not found: {pdf_path}")

    # Extract text from all pages
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")

    if not text.strip():
        raise ValueError("PDF contains no extractable text")

    # Parse extracted text
    extracted = {}

    # Extract name (first non-empty line, heuristic)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        potential_name = lines[0]
        if not re.search(r'@|\.com|http|phone|tel|\d{3}[-.]?\d{3}', potential_name, re.I):
            extracted['name'] = potential_name

    # Extract years of experience
    exp_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience', text, re.I)
    if exp_match:
        extracted['years_experience'] = int(exp_match.group(1))

    # Extract skills (look for "Skills:" section)
    skills_section = re.search(
        r'(?:Skills?|Technical Skills?|Technologies?):\s*([^\n]+(?:\n[^\n]+)*)',
        text,
        re.I | re.M
    )
    if skills_section:
        skills_text = skills_section.group(1)
        skills = re.split(r'[,;•\|\n]+', skills_text)
        skills = [s.strip() for s in skills if s.strip() and len(s.strip()) > 1]
        if skills:
            extracted['skills'] = skills[:20]

    return extracted
```

## Data Flow

### PDF Import Flow (New)

```
[User runs job-radar (first time)]
    ↓
[wizard.py: run_setup_wizard()]
    ↓
[Prompt: Import PDF or manual?]
    │
    ├─[Import PDF]──────────────────────┐
    │   ↓                                │
    │  [questionary.text() → PDF path]   │
    │   ↓                                │
    │  [pdf_parser.extract_resume_data()]│
    │   ↓                                │
    │  [extracted_data dict]             │
    │   ↓                                │
    └─→[Pre-fill Questionary prompts]←──┘
        ↓
       [User edits/confirms each field]
        ↓
       [Atomic write: profile.json + config.json]
```

### Job Source Integration Flow (New)

```
[build_search_queries(profile)]
    ↓
[Generate queries for all sources including Wellfound, Adzuna, Authentic Jobs]
    ↓
[fetch_all() → ThreadPoolExecutor]
    ↓
[Parallel execution: fetch_wellfound(), fetch_adzuna(), fetch_authenticjobs()]
    ↓
[All return JobResult[] with same structure]
    ↓
[Deduplicate, score, report as normal]
```

## Anti-Patterns

### Anti-Pattern 1: Tightly Coupling PDF Parser to Wizard

**What people do:** Embed PDF extraction logic directly in wizard prompts loop

**Why it's wrong:**
- Impossible to test PDF parsing independently
- wizard.py becomes 2000+ lines (currently 700)
- Can't reuse PDF parser in other contexts
- pdfplumber dependency bleeds into wizard tests

**Do this instead:** Separate `pdf_parser.py` module that wizard imports. Parser returns dict, wizard consumes dict.

### Anti-Pattern 2: Modifying Existing Fetchers for New Sources

**What people do:** Add if/elif branches to existing `fetch_dice()` function

**Why it's wrong:**
- Violates single responsibility
- Breaks tests for existing sources
- Merge conflicts when multiple sources added in parallel

**Do this instead:** Add new `fetch_wellfound()`, `fetch_adzuna()`, `fetch_authenticjobs()` functions. Update dispatcher in `run_query()`.

### Anti-Pattern 3: Assuming PDF Extraction Always Succeeds

**What people do:** Make wizard crash if PDF parsing fails

**Why it's wrong:**
- Resume formats vary wildly (parsing accuracy <70%)
- Users can't recover without restarting wizard

**Do this instead:**
```python
try:
    extracted_data = extract_resume_data(pdf_path)
except Exception as e:
    print(f"⚠️  PDF parsing failed: {e}")
    print("Continuing with manual entry...\n")
    extracted_data = {}
```

### Anti-Pattern 4: Hardcoding API Credentials in Source Code

**What people do:** Store Adzuna API keys directly in `fetch_adzuna()` function

**Why it's wrong:**
- Security risk (credentials in version control)
- Can't support multiple users with different API keys

**Do this instead:**
```python
app_id = os.environ.get("ADZUNA_APP_ID")
app_key = os.environ.get("ADZUNA_APP_KEY")
if not app_id or not app_key:
    log.warning("[Adzuna] Missing credentials (set ADZUNA_APP_ID, ADZUNA_APP_KEY)")
    return []
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Wellfound | Web scraping (BeautifulSoup) | No official API. Use same HEADERS as Dice. |
| Adzuna | REST API (requests) | Requires app_id + app_key. Rate limit: 1000 calls/month free tier. |
| Authentic Jobs | REST API (requests) | Requires API key. Basic auth (key as username). |
| pdfplumber | Library import | PDF text extraction. Falls back gracefully if not installed. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| wizard.py ↔ pdf_parser.py | Function call: `extract_resume_data(path) -> dict` | Wizard owns validation, parser only extracts |
| sources.py ↔ cache.py | Function call: `fetch_with_retry(url) -> str` | Cache layer transparent to sources |
| search.py ↔ wizard.py | Conditional import: `from .wizard import run_setup_wizard` | Only imported if profile missing |

## Build Order Recommendation

### Phase 1: Job Sources (Lower Risk)

**Add 3 new fetchers in sources.py:**
1. `fetch_wellfound()` - Web scraping
2. `fetch_adzuna()` - API call
3. `fetch_authenticjobs()` - API call

**Update orchestration:**
- Add source dispatching in `run_query()`
- Add query building in `build_search_queries()`

**Why first:** Lower risk, follows existing pattern exactly, no new dependencies.

### Phase 2: PDF Parser (Higher Risk)

**Create new pdf_parser.py module:**
- `extract_resume_data(pdf_path) -> dict`
- Regex-based field extraction

**Enhance wizard.py:**
- Add PDF import prompt before existing questions
- Pre-fill prompts with extracted_data

**Why second:** Higher complexity, new dependency, benefits from tested foundation.

## Sources

### PDF Parsing Libraries
- [pyresparser PyPI](https://pypi.org/project/pyresparser/) - Resume parser using spaCy and NLTK
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber) - Detailed PDF text extraction library
- [PyPDF2 PyPI](https://pypi.org/project/PyPDF2/) - PDF manipulation library
- [Affinda: Extract Skills from Resume](https://www.affinda.com/blog/extract-skills-from-a-resume-using-python) - Skills extraction guide

### Job Board APIs
- [Adzuna API Overview](https://developer.adzuna.com/overview) - Official Adzuna API documentation
- [Adzuna API Python Guide](https://www.omi.me/blogs/api-guides/how-to-fetch-job-listings-using-adzuna-api-in-python) - Python integration tutorial
- [Wellfound API Tracker](https://apitracker.io/a/wellfound) - API specifications and docs
- [Authentic Jobs API](https://publicapis.io/authentic-jobs-api) - API documentation and endpoints

### Python Architecture Patterns
- [Python Plugin Architecture](https://alysivji.com/simple-plugin-system.html) - Implementing extensible plugin systems
- [Creating Plugins Python Packaging Guide](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/) - Official Python plugin documentation
- [Questionary PyPI](https://pypi.org/project/questionary/) - Interactive CLI prompts library
- [Dataclasses Validation](https://medium.com/@2nick2patel2/dataclasses-that-do-more-42da2989f067) - Validators and pattern matching

---
*Architecture research for: Job Radar v1.2.0 (Job Sources + PDF Parsing)*
*Researched: 2026-02-09*
