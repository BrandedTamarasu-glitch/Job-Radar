# Feature Research: Job Radar v1.2.0

**Domain:** Job aggregator with profile-driven scoring — v1.2.0 job sources and PDF import
**Researched:** 2026-02-09
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Job Source APIs**||||
| Adzuna API integration | Public API with documented endpoints | LOW | app_id + app_key authentication, JSON responses, no documented rate limits |
| Authentic Jobs API integration | Public API for design/creative jobs | LOW | API key required via developer signup, standard REST endpoints |
| Wellfound (AngelList) data access | Startup/tech-focused job source | HIGH | No official API — requires scraping (GraphQL endpoint reverse-engineering) or third-party service |
| Error handling for API failures | APIs can be down, rate-limited, or change | MEDIUM | Graceful degradation like existing WWR Cloudflare detection |
| Deduplication across sources | Same job posted on multiple platforms | LOW | Existing pattern: hash by (title, company) — extend to include new sources |
| **PDF Resume Import**||||
| PDF to text extraction | Pre-fill wizard from resume | MEDIUM | Use PyMuPDF or pdfminer.six for text extraction |
| Name extraction | First field in wizard | MEDIUM | SpaCy NER for PERSON entities — 80-90% accuracy on standard resumes |
| Years of experience detection | Calculate from employment dates | HIGH | Pattern matching for date ranges — fragile, expect 60-70% accuracy |
| Job title extraction | Map to wizard's `titles` field | MEDIUM | SpaCy + regex patterns for common titles — 70-80% accuracy |
| Skills extraction | Map to wizard's `skills` field | MEDIUM | Keyword matching against skill database — 60-70% accuracy, many false negatives |
| Fallback UI for corrections | Parser accuracy is 60-90%, not 100% | LOW | Pre-populate wizard fields but keep all editable (already the case) |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Job Source Selection**||||
| Wellfound integration | Unique startup/tech job pipeline competitors lack | HIGH | Adds 150K+ startup jobs; requires scraping infrastructure or Apify/Coresignal API |
| Multi-confidence PDF parsing | Show users which fields are uncertain | MEDIUM | Return confidence scores per field (high/medium/low) so users know what to verify |
| Skill taxonomy enrichment | Map resume skills to standardized taxonomy | MEDIUM | Build skill database (e.g., "React" → "React.js", "node" → "Node.js") to improve matching |
| **Enhanced Data Quality**||||
| Adzuna salary data | Broad market with salary_min/salary_max fields | LOW | Most existing sources lack salary — Adzuna provides predicted salaries |
| Location normalization across sources | Standardize "SF", "San Francisco", "San Francisco, CA" | MEDIUM | Improves deduplication and profile matching |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| 100% accurate PDF parsing | Users expect "smart" resume import | Modern parsers only achieve 60-90% accuracy; international formats, creative layouts, and soft skills extraction fail systematically | Show confidence scores, pre-populate wizard with editable fields, set expectations |
| Real-time job source scraping | "Fresh results every time" sounds good | APIs have rate limits; Wellfound GraphQL may block; adds latency to wizard | Cache results per session, refresh in background |
| Automatic skill categorization (core vs secondary) | Reduces manual work | Resume parsers struggle with skill prioritization — "Python" in a 2019 job vs current role | Extract all skills as flat list, let user categorize in wizard |
| Parsing compensation expectations from resume | Pre-fill `comp_floor` | Resumes rarely include comp expectations; parsing salary from job history is misleading | Require manual input for comp_floor |

## Feature Dependencies

```
[Adzuna API integration]
    └──requires──> [API key registration]
    └──requires──> [Error handling for API failures]

[Authentic Jobs API integration]
    └──requires──> [API key registration]
    └──requires──> [Error handling for API failures]

[Wellfound data access]
    └──requires──> [Scraping infrastructure OR third-party service]
    └──requires──> [Error handling for scraping failures]
    └──conflicts with──> [Real-time job source scraping] (anti-feature)

[PDF Resume Import]
    └──requires──> [PDF to text extraction]
    └──requires──> [SpaCy NER model]
    └──requires──> [Fallback UI for corrections]

[Name extraction]
    └──requires──> [PDF to text extraction]

[Years of experience detection]
    └──requires──> [PDF to text extraction]
    └──enhances──> [Multi-confidence PDF parsing] (show low confidence for this field)

[Job title extraction]
    └──requires──> [PDF to text extraction]

[Skills extraction]
    └──requires──> [PDF to text extraction]
    └──enhances──> [Skill taxonomy enrichment]

[Multi-confidence PDF parsing]
    └──requires──> [All extraction features]
    └──requires──> [Fallback UI for corrections]
```

### Dependency Notes

- **Adzuna/Authentic Jobs → API keys:** Must register for developer accounts before implementation starts
- **Wellfound → Scraping decision:** Choose between (a) Apify/Coresignal paid service, (b) reverse-engineering GraphQL endpoint, or (c) defer to post-v1.2.0
- **PDF parsing → SpaCy model:** Requires `en_core_web_sm` or similar — adds ~40MB to distribution
- **Multi-confidence parsing → All extraction:** Can't show confidence without extraction features implemented first
- **Skill taxonomy → Skills extraction:** Taxonomy is optional enhancement, not blocker

## v1.2.0 Scope Definition

### Launch With (v1.2.0 MVP)

Minimum features to call v1.2.0 complete.

- [ ] **Adzuna API integration** — Public API, low complexity, adds broad market coverage
- [ ] **Authentic Jobs API integration** — Public API, low complexity, adds design/creative niche
- [ ] **Wellfound scraping fallback** — If no official API access secured, provide manual URL generator (like existing WWR pattern)
- [ ] **PDF to text extraction** — Use PyMuPDF for cross-platform compatibility
- [ ] **Name extraction** — SpaCy NER for PERSON entities
- [ ] **Job title extraction** — Regex + SpaCy patterns for common titles
- [ ] **Skills extraction** — Keyword matching against basic skill list
- [ ] **Fallback UI for corrections** — Pre-populate wizard fields, keep all editable (no code change needed — already editable)
- [ ] **Error handling for new sources** — Graceful degradation like existing sources

### Defer to Post-v1.2.0 (v1.3+)

Features to add once core is validated.

- [ ] **Wellfound official integration** — If official API access or Apify subscription secured
- [ ] **Years of experience detection** — Complex pattern matching, low accuracy, not critical for MVP
- [ ] **Multi-confidence PDF parsing** — Nice UX enhancement, but wizard editing covers correction path
- [ ] **Skill taxonomy enrichment** — Improves matching quality, but manual skill entry works for MVP
- [ ] **Location normalization** — Improves deduplication, but (title, company) hash catches most duplicates
- [ ] **Adzuna salary integration into scoring** — Current scoring uses profile `comp_floor`; adding salary_min/max comparison requires scoring logic changes

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Adzuna API integration | HIGH | LOW | P1 |
| Authentic Jobs API integration | MEDIUM | LOW | P1 |
| PDF to text extraction | HIGH | MEDIUM | P1 |
| Name extraction | MEDIUM | MEDIUM | P1 |
| Job title extraction | MEDIUM | MEDIUM | P1 |
| Skills extraction | MEDIUM | MEDIUM | P1 |
| Error handling for new sources | HIGH | LOW | P1 |
| Fallback UI for corrections | HIGH | LOW (already exists) | P1 |
| Wellfound scraping fallback | MEDIUM | LOW | P1 |
| Wellfound official integration | HIGH | HIGH (requires service/API) | P2 |
| Years of experience detection | LOW | HIGH | P2 |
| Multi-confidence parsing | MEDIUM | MEDIUM | P2 |
| Skill taxonomy enrichment | MEDIUM | MEDIUM | P2 |
| Location normalization | LOW | MEDIUM | P3 |
| Salary scoring integration | MEDIUM | MEDIUM | P3 |

**Priority key:**
- P1: Must have for v1.2.0 launch
- P2: Should have, add when time permits
- P3: Nice to have, future consideration

## API Integration Details

### Adzuna API

**Authentication:**
- `app_id` and `app_key` obtained via registration at https://developer.adzuna.com/
- Passed as query parameters in all requests

**Endpoint Structure:**
```
GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
  ?app_id={YOUR_APP_ID}
  &app_key={YOUR_APP_KEY}
  &what={job_title}
  &where={location}
  &results_per_page=20
  &sort_by=salary
```

**Response Fields (mapped to JobResult):**
- `title` → title
- `company.display_name` → company
- `location.display_name` → location
- `description` → description (snippet only)
- `salary_min`, `salary_max` → salary
- `created` → date_posted
- `redirect_url` → url
- `contract_type` → employment_type (permanent, contract, etc.)
- `contract_time` → arrangement hint (full_time, part_time)

**Rate Limits:**
- Not documented in public API overview
- Assume conservative limit (1 req/sec) until testing reveals actual limits
- Implement exponential backoff for 429 responses

**Error Handling:**
- HTTP 401: Invalid API credentials
- HTTP 429: Rate limit exceeded (retry with backoff)
- HTTP 500: API error (log and skip source)

**Complexity:** LOW — Standard REST API with JSON responses

**Sources:**
- [Adzuna API Overview](https://developer.adzuna.com/overview)
- [Adzuna Job Search Endpoint](https://developer.adzuna.com/docs/search)

### Authentic Jobs API

**Authentication:**
- API key required via developer program signup at https://authenticjobs.com/
- Exact authentication method not documented in search results (verify during implementation)

**Endpoint Structure:**
```
GET https://authenticjobs.com/api/
  ?api_key={YOUR_API_KEY}
  &method=aj.jobs.search
  &keywords={query}
  &location={location}
  &category={category_id}
```

**Response Fields (expected, verify during implementation):**
- Job listings array with title, company, location, description, post_date, apply_url
- Categories endpoint for filtering by design/creative specializations

**Rate Limits:**
- Not documented in search results
- Assume conservative limit until testing

**Error Handling:**
- Similar to Adzuna (401, 429, 500)

**Complexity:** LOW — Standard REST API

**Sources:**
- [Authentic Jobs API - Public APIs](https://publicapis.io/authentic-jobs-api)
- [Authentic Jobs API - JobApis](https://jobapis.github.io/open-source/authentic/)

### Wellfound (AngelList) Data Access

**Problem:** No official public API available as of 2026.

**Options:**

**Option 1: Scraping via Apify/Coresignal (Recommended for MVP)**
- **Apify Wellfound Jobs Scraper:** Paid service, structured JSON output, handles anti-scraping
- **Coresignal Wellfound Dataset:** Pre-scraped dataset, fresh data, API access
- **Complexity:** LOW (API integration) but HIGH (requires budget approval)

**Option 2: GraphQL Endpoint Reverse Engineering**
- Wellfound uses `/graphql` endpoint for job searches
- Requires reverse-engineering query structure, auth tokens, headers
- **Complexity:** HIGH — fragile, may break with site changes, risk of IP blocking
- **Reference:** https://github.com/subbuwu/wellfound_graphqlscout

**Option 3: Manual URL Generator (Fallback for v1.2.0)**
- Like existing WWR pattern: generate search URLs, user clicks through manually
- **Complexity:** LOW
- **Downside:** No automated fetching, no scoring integration

**Recommendation for v1.2.0:**
- Implement **Option 3** (manual URL generator) for MVP
- Evaluate **Option 1** (Apify/Coresignal) if budget allows
- Defer **Option 2** (GraphQL scraping) to post-v1.2.0 unless no other option available

**Sources:**
- [Wellfound No Public API - API Tracker](https://apitracker.io/a/wellfound)
- [Apify Wellfound Jobs Scraper](https://apify.com/mscraper/wellfound-jobs-scraper)
- [Coresignal Wellfound Dataset](https://coresignal.com/data-sources/wellfound-data/)
- [GraphQL Scraper Example](https://github.com/subbuwu/wellfound_graphqlscout)

## PDF Resume Parsing Details

### Extraction Technology Stack

**PDF Text Extraction:**
- **Recommended:** PyMuPDF (fitz) — Fast, cross-platform, handles most PDF formats
- **Alternative:** pdfminer.six — More robust for complex layouts, slower
- **Complexity:** LOW — Both libraries well-documented

**NLP Processing:**
- **Recommended:** SpaCy with `en_core_web_sm` model
- **Why:** Fast NER, good PERSON entity recognition, used by most open-source parsers
- **Complexity:** MEDIUM — Requires model download, adds ~40MB to distribution

**Pattern Matching:**
- **Use cases:** Job titles, employment dates, phone/email extraction
- **Implementation:** Regex patterns + SpaCy pipeline
- **Complexity:** MEDIUM — Fragile across resume formats

### Expected Accuracy by Field

| Field | Method | Expected Accuracy | Confidence Level |
|-------|--------|-------------------|------------------|
| Name | SpaCy NER (PERSON) | 80-90% | HIGH for standard resumes, LOW for creative formats |
| Email | Regex pattern | 95%+ | HIGH |
| Phone | Regex pattern | 90%+ | HIGH |
| Job titles | SpaCy + regex + keyword matching | 70-80% | MEDIUM (misses non-standard titles) |
| Skills | Keyword matching vs skill database | 60-70% | LOW (many false negatives, struggles with soft skills) |
| Years of experience | Date range pattern matching | 60-70% | LOW (fragile, international date formats fail) |
| Location | NER (GPE) + pattern matching | 70-80% | MEDIUM |

**Key Insight:** No single field extraction exceeds 90% accuracy except email/phone. Users MUST review and correct all fields.

### Known Challenges and Mitigations

**Challenge 1: Format Variability**
- **Problem:** 37% of resumes fall outside "standard format" (creative layouts, tables, graphics)
- **Impact:** Text extraction order scrambled, section headers misidentified
- **Mitigation:** Show all extracted text in wizard notes section for manual reference

**Challenge 2: International Formats**
- **Problem:** German CVs with photos, right-to-left languages, scanned documents with OCR errors
- **Impact:** Character recognition errors cascade through NER pipeline
- **Mitigation:** Flag low confidence (fewer than 2 entities detected), prompt manual entry

**Challenge 3: Soft Skills**
- **Problem:** Parsers identify hard skills ("Python", "React") but fail on soft skills ("leadership", "communication")
- **Impact:** Extracted skill list incomplete
- **Mitigation:** Provide suggested skills based on job titles, let user add manually

**Challenge 4: Project Maintenance**
- **Problem:** PyResParser (most popular library) has inactive maintenance, dependency issues
- **Impact:** Can't rely on third-party library long-term
- **Mitigation:** Build custom extraction pipeline using SpaCy + PyMuPDF (both actively maintained)

### Implementation Pattern (Based on Existing Code)

Follow existing `JobResult` pattern for parsed resume data:

```python
@dataclass
class ResumeParseResult:
    """Parsed resume data with confidence scores."""
    name: str
    email: str
    phone: str
    titles: list[str]  # job titles extracted
    skills: list[str]
    years_experience: int
    location: str

    # Confidence per field
    name_confidence: str  # high, medium, low
    titles_confidence: str
    skills_confidence: str
    experience_confidence: str

    raw_text: str  # Full extracted text for manual review
```

Map to wizard fields:
- `name` → wizard name field
- `titles` → comma-separated `titles` field
- `skills` → comma-separated `skills` field
- `years_experience` → `years_experience` field (only if confidence > medium)
- `location` → `location` field

**Sources:**
- [PyResParser Accuracy Issues](https://github.com/OmkarPathak/pyresparser/issues)
- [Resume Parser Accuracy Expectations](https://secondary.ai/blog/recruitment/ai-resume-parsing-ocr-multi-format-extraction-reality-check)
- [Resume Parsing Challenges](https://www.recrew.ai/blog/top-7-resume-parsing-challenges-and-strategies-to-overcome)
- [SpaCy Resume Parsing Examples](https://github.com/topics/resume-parser)

## Competitor Feature Analysis

| Feature | Indeed | LinkedIn | Dice | Job Radar v1.1 | Job Radar v1.2.0 Target |
|---------|--------|----------|------|----------------|-------------------------|
| Startup jobs (Wellfound) | No | No | No | No | Yes (manual URLs minimum) |
| Design/creative jobs (Authentic Jobs) | Partial | Partial | No | No | Yes |
| Broad market (Adzuna) | Yes | Yes | Yes | No | Yes |
| PDF resume import | Yes | Yes | No | No | Yes |
| Profile-driven scoring | No | Partial | No | Yes | Yes (enhanced) |
| Multi-source aggregation | No | No | No | Yes | Yes (expanded) |

**Competitive Advantage:** Only job aggregator combining startup focus (Wellfound), creative niche (Authentic Jobs), broad market (Adzuna), AND profile-driven scoring with PDF import.

---

*Feature research for: Job Radar v1.2.0 — Job Sources + PDF Import*
*Researched: 2026-02-09*
*Confidence: MEDIUM (Adzuna/Authentic Jobs = HIGH; Wellfound = LOW; PDF parsing = MEDIUM)*
