# External Integrations

**Analysis Date:** 2026-02-07

## APIs & External Services

**Job Board Aggregators:**

1. **Dice.com** - Technical job board scraping
   - Endpoint: `https://www.dice.com/jobs?q={query}&location={location}`
   - Implementation: HTML scraper (`fetch_dice()` in `job_radar/sources.py` lines 98-186)
   - Selector: `div.rounded-lg.border` for job cards
   - Auth: None (public web scraping)
   - Details extracted: Title, company, location, salary, date posted, employment type
   - Parser confidence: High to medium depending on page structure

2. **HN Hiring (hnhiring.com)** - Hacker News job postings
   - Endpoint: `https://hnhiring.com/technologies/{slug}` (technology-based filtering)
   - Implementation: HTML scraper with freeform fallback (`fetch_hn_hiring()` in `job_radar/sources.py` lines 193-290)
   - Selector: `ul.jobs > li.job` for job items
   - Auth: None (public web scraping)
   - Format: Pipe-separated fields (Company | Title | Location) or freeform text
   - Details extracted: Company, title, location, salary, employment type, posting date
   - Parser confidence: High (standard format) or low (freeform)
   - Special handling: Email extraction for apply info (regex pattern: `[\w.+-]+@[\w.-]+\.\w+`)

3. **RemoteOK** - Remote job listings via JSON API
   - Endpoint: `https://remoteok.com/api` (public JSON endpoint)
   - Implementation: JSON parser (`fetch_remoteok()` in `job_radar/sources.py` lines 415-493)
   - Auth: None (public API)
   - Response format: JSON array of job objects
   - Details extracted: Position, company, location, salary (min/max), job type, description, URL
   - Filtering: Skill-based matching on tags and position title
   - Parser confidence: High

4. **We Work Remotely (weworkremotely.com)** - Remote-first job board
   - Endpoint: `https://weworkremotely.com/remote-jobs/search?term={query}`
   - Implementation: HTML scraper with Cloudflare detection (`fetch_weworkremotely()` in `job_radar/sources.py` lines 505-585)
   - Auth: None (public web scraping)
   - Selector: `section.jobs li`, `section.jobs article` (flexible selectors)
   - Cloudflare Protection: Detected by "Just a moment" or "cf-browser-verification" in response (lines 521-524)
   - When blocked: Returns empty results; user directed to manual URLs instead
   - Details extracted: Title, company, location, URL
   - Parser confidence: High when accessible

**Manual Search URL Generators:**

- **Indeed** - `https://www.indeed.com/jobs?` (parameters: q, l, fromage, sort)
- **LinkedIn** - `https://www.linkedin.com/jobs/search/?` (parameters: keywords, location, f_TPR, sortBy)
- **Glassdoor** - `https://www.glassdoor.com/Job/jobs.htm?` (parameters: sc.keyword, locKeyword, fromAge, sortBy)
- All generated in `job_radar/sources.py` (`generate_*_url()` functions lines 592-630)

## Data Storage

**Databases:**
- Not applicable; uses local JSON file storage

**File Storage:**
- Local filesystem
  - `.cache/` directory: HTTP response caching (SHA256-hashed filenames)
  - `results/` directory: Generated Markdown reports and tracker data

**Persistent Storage:**
- `results/tracker.json` (JSON file)
  - Stores: seen_jobs (dedup), applications (status tracking), run_history (statistics)
  - Format: Flat JSON with job key (`title||company` lowercase) mapping to metadata
  - Retention: Run history limited to last 90 days
  - Purpose: Cross-run deduplication and application status management

**Caching:**
- HTTP response caching in `.cache/` with 4-hour TTL
- Configurable via `_CACHE_MAX_AGE_SECONDS` in `job_radar/cache.py`
- Client: `requests` library with custom retry logic (3 attempts, 2.0x exponential backoff)

## Authentication & Identity

**Auth Provider:**
- None required - all job board data is public
- No API keys or credentials needed
- HTTP User-Agent header spoofing: `Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0`

## Monitoring & Observability

**Error Tracking:**
- Not detected; no external error tracking service

**Logs:**
- Python `logging` module (built-in)
- Log level: INFO (default), DEBUG (with `--verbose` flag)
- Logger names: "search", "sources", "cache" (configured in `job_radar/search.py` lines 264-272)
- Suppression: urllib3, requests loggers set to WARNING to reduce noise
- Output: Console via `logging.StreamHandler()`

**Debug Output:**
- Progress reporting during fetch phase (carriage return line update: `\r`)
- Summary statistics: Total results, new/seen split, dealbreakers, top matches (color-coded)
- Confidence notes: "Low parse confidence (freeform listing)" when parser confidence is low

## CI/CD & Deployment

**Hosting:**
- Not applicable; CLI tool for local/desktop use

**CI Pipeline:**
- Not detected

**Distribution:**
- PyPI via setuptools (entry point: `job-radar` command)
- Manual installation: `pip install -e .`
- Editable install for development: `pip install -e .`

## Environment Configuration

**Required env vars:**
- None

**Candidate Profile Configuration:**
- JSON file format (no environment variables required)
- Location specified via CLI `--profile` flag
- Required fields: `name`, `target_titles`, `core_skills`
- Optional fields: `level`, `years_experience`, `location`, `target_market`, `arrangement`, `domain_expertise`, `secondary_skills`, `certifications`, `comp_floor`, `dealbreakers`, `highlights`

## Webhooks & Callbacks

**Incoming:**
- Not applicable

**Outgoing:**
- Not applicable

## External Data Sources

**Job Source Configuration:**
- Skill-to-source mapping for HN Hiring in `job_radar/sources.py` (lines 669-700)
  - Maps skill names (e.g., "python", "react") to hnhiring.com technology slugs
  - Example: `"react": "react"`, `"node.js": "node"`, `"typescript": "typescript"`

**Staffing Firm Detection:**
- Known staffing firms list in `job_radar/staffing_firms.py`
  - Used to boost "response likelihood" score for applications to staffing firms
  - Contains 45+ firm names: Randstad, Robert Half, TekSystems, Accenture, Cognizant, etc.
  - Matching: Case-insensitive substring match

---

*Integration audit: 2026-02-07*
