# Phase 15: PDF Resume Parser - Context

**Gathered:** 2026-02-10
**Phase Goal:** Users can upload PDF resume during wizard setup to pre-fill profile fields

This document captures implementation decisions from `/gsd:discuss-phase 15`. These decisions guide the researcher (what to investigate) and planner (what to build).

---

## File Selection & Upload Flow

### Decisions (LOCKED — must implement exactly as specified)

**Upload timing:**
- PDF upload offered FIRST THING in wizard flow
- Opening choice: "Upload resume or fill manually?" before any manual prompts
- Rationale: Establishes user's preferred input method upfront

**File formats:**
- PDF only (.pdf extension required)
- No DOCX, TXT, or other formats supported in this phase
- Rationale: Focused scope - PDF is universal for resumes, pdfplumber already researched

**File size limit:**
- 5 MB maximum file size enforced
- Reject files larger than 5 MB with clear error message
- Rationale: Generous for text resumes (1-3 pages typically <500 KB), blocks accidentally uploaded portfolios

**Upload failure handling:**
- Retry with clear error on file read failures (not found, permissions, corrupted)
- Show specific error message explaining what went wrong
- Offer two options: try different file OR skip to manual entry
- Rationale: User-friendly recovery - doesn't force restart, gives clear path forward

### Claude's Discretion

- File picker UI implementation (questionary.path vs. questionary.text with validation)
- Specific file extension validation logic (.pdf vs .PDF case handling)
- File read buffer size and error detection strategy
- Progress indicator during file read (for large PDFs near 5 MB limit)

---

## Extraction Accuracy & Feedback

### Decisions (LOCKED — must implement exactly as specified)

**Data presentation:**
- Pre-fill wizard prompts with extracted data as default values
- User proceeds through normal wizard flow with values already populated
- No separate review screen or side-by-side comparison
- Rationale: Seamless integration - extracted data feels like part of wizard, not separate step

**Disclaimer placement:**
- Show once after parsing: "Please review - extraction may contain errors"
- Display immediately after PDF is successfully parsed, before wizard prompts begin
- Do NOT repeat on every field or at final save step
- Rationale: Not intrusive - informs user once without nagging

**Pre-display validation:**
- Basic sanity checks before showing extracted data
- Validate data types: years of experience must be numeric, strings non-empty
- Skip clearly invalid extractions (negative years, empty names, etc.)
- Do NOT enforce strict format patterns or confidence scoring
- Rationale: Pragmatic - catches obvious errors without over-filtering

**Field indicators:**
- No visual distinction between extracted fields and manual entry fields
- Treat all wizard prompts the same way regardless of data source
- Do NOT show icons, highlights, or confidence scores
- Rationale: Clean UI - extracted data is just a default value like any other

### Claude's Discretion

- Exact wording of accuracy disclaimer message
- Visual styling of disclaimer (color, emphasis, placement)
- Specific validation rules for each field type (name patterns, skill formats, etc.)
- Logging of validation failures for debugging

---

## User Control & Skip Behavior

### Decisions (LOCKED — must implement exactly as specified)

**Skip mechanism:**
- Choice at upload prompt using questionary.select
- Options: "Upload resume" OR "Fill manually" as equal choices
- If user selects "Fill manually", proceed directly to wizard prompts with no PDF parsing
- Rationale: Clear UX - two equal paths, user chooses upfront

**Edit flexibility:**
- Fully editable - user can modify any pre-filled field inline
- Extracted data is just a starting point, not locked-in values
- No "accept or reject per field" flow - wizard works normally with editable defaults
- Rationale: Maximum user control - trust user to review and correct as needed

**Partial extraction:**
- Pre-fill what worked, prompt for rest
- If name extracted but skills failed: show name as default, leave skills empty for manual entry
- Do NOT require minimum fields or warn about gaps
- Do NOT discard all data if some fields fail
- Rationale: Graceful degradation - partial success is better than complete failure

**Back navigation:**
- No back navigation - PDF upload is one-way
- Once wizard flow starts (after parsing), user can only:
  - Edit fields inline
  - Restart wizard entirely (exit and re-run)
- Do NOT add "Upload different resume" option during wizard
- Rationale: Keeps flow simple - avoids state management complexity of re-uploading mid-wizard

### Claude's Discretion

- Specific questionary widget for "Upload resume" vs "Fill manually" choice
- Restart wizard mechanism (Ctrl+C handling, explicit restart option, etc.)
- Empty field placeholder text for fields that failed extraction
- Wizard prompt ordering and transitions

---

## Error Handling & Validation

### Decisions (LOCKED — must implement exactly as specified)

**PDF validation:**
- "Text-extractable" definition: pdfplumber.extract_text() returns non-empty string
- Technical check - if pdfplumber can extract any text, PDF is valid
- Do NOT require minimum character threshold (100+ chars)
- Do NOT require structured text detection (headings, bullets)
- Do NOT require named entity detection
- Rationale: Simple technical check - avoids false negatives from strict rules

**Error messages:**
- Specific actionable messages for common failures:
  - Image-only PDF: "This PDF appears to be image-based. Please use a text-based resume or fill manually."
  - Encrypted PDF: "This PDF is password-protected. Please use an unencrypted resume or fill manually."
  - Corrupted file: "Unable to read PDF file. The file may be corrupted. Try a different file or fill manually."
  - Size exceeded: "File size exceeds 5 MB limit. Please use a smaller PDF or fill manually."
- Do NOT use generic "Unable to read PDF" for all errors
- Do NOT show technical exception messages to user
- Do NOT use error code system (PDF-ERR-001, etc.)
- Rationale: User-friendly and helpful - tells user what went wrong and how to fix it

**Parse failures:**
- Fallback to manual entry if parsing logic fails
- "Parsing failure" = text extraction succeeds, but can't find name/dates/skills patterns
- Show friendly error: "We couldn't parse your resume. Let's fill your profile manually."
- Do NOT show raw extracted text to user
- Do NOT allow partial data (empty fields) when ALL fields fail to parse
- Do NOT retry with user hints
- Rationale: Clean error recovery - don't confuse user with unparseable data

**Fallback strategy:**
- Always offer manual entry on any failure (upload, validation, parsing)
- Every error path ends with: "Would you like to fill your profile manually?"
- Do NOT suggest retry first (already handled in upload failure decision)
- Do NOT exit wizard on error (forces restart)
- Do NOT use silent fallback (explain what happened)
- Rationale: Reliable recovery path - user always has way forward regardless of error

### Claude's Discretion

- Exact error message wording and formatting
- Logging strategy for errors (file paths, exception details for debugging)
- pdfplumber exception handling specifics (which exceptions map to which user messages)
- Manual entry transition flow after error (smooth or explicit restart)

---

## Deferred Ideas

These were discussed but are OUT OF SCOPE for Phase 15. Capture for potential future phases:

**Multi-format support:**
- DOCX resume parsing (requires python-docx)
- TXT plain text resumes
- Auto-detection of resume format (PDF vs DOCX vs TXT)
- Rationale: Defer to keep scope focused on PDF-only for v1.2

**Advanced extraction:**
- NLP-based skill extraction using SpaCy (covered in PDF-11 future requirement)
- Location/contact info extraction (covered in PDF-12 future requirement)
- Education/degree parsing (covered in PDF-13 future requirement)
- Rationale: Future requirements already define these as later work

**Enhanced UX:**
- Review screen showing all extracted data before wizard
- Confidence scoring for extracted fields
- "Revert to extracted" option for edited fields
- Re-upload during wizard flow
- Rationale: Not essential for v1.2 - can add based on user feedback

**Error recovery:**
- Retry with user hints ("where is your name?")
- Show raw extracted text on parse failure
- Partial parse with warnings (highlight missing fields)
- Rationale: Adds complexity without clear benefit - prefer clean fallback to manual

---

## Researcher Instructions

**What to research:**
- pdfplumber usage patterns and best practices for text extraction
- Common PDF resume structures (to inform parsing logic)
- Python libraries for name/date/skill extraction from text (regex, dateutil, etc.)
- questionary integration patterns for file selection
- File size validation and error handling in Python
- PDF encryption/protection detection methods
- PyInstaller bundling requirements for pdfplumber (fonts, dependencies)

**What NOT to research:**
- DOCX parsing (out of scope - PDF only)
- OCR libraries (image PDFs rejected, not processed)
- NLP/SpaCy (deferred to PDF-11 future requirement)
- Alternative PDF libraries (pdfplumber already decided per requirements research)
- Multi-resume support (out of scope - single profile per user)

**Focus areas:**
- Error detection patterns for image-only PDFs, encrypted PDFs, corrupted files
- Regex patterns for extracting name, years of experience, job titles, skills from text
- File picker best practices for CLI tools (questionary.path vs custom validation)
- Validation strategies for extracted data (sanity checks without over-filtering)
- PyInstaller compatibility with pdfplumber on macOS/Windows/Linux

---

## Planner Instructions

**Must honor:**
- All decisions in "Locked" sections above
- Requirement coverage: PDF-01 through PDF-10 must be addressed
- Success criteria from roadmap (6 observable truths)
- Existing wizard.py architecture (Questionary-based prompts)

**Freedom areas:**
- Implementation details in "Claude's Discretion" sections
- Task breakdown and wave structure
- File organization (new pdf_parser.py module vs. additions to wizard.py)
- Test coverage strategy and test case selection

**Integration points:**
- job_radar/wizard.py - modify first-run wizard flow to offer PDF upload
- New module: job_radar/pdf_parser.py (or similar) for extraction logic
- tests/test_wizard.py - extend wizard tests for PDF flow
- New test file: tests/test_pdf_parser.py for extraction logic tests

**Success criteria:**
- User can select PDF file during wizard first-run setup
- System validates PDF is text-extractable (reject image-only with clear error)
- Wizard prompts show extracted name, years of experience, job titles, skills as defaults
- User can edit any pre-filled field before saving to profile.json
- User sees accuracy disclaimer once after parsing
- User can skip PDF import and fill wizard manually without errors
- Non-ASCII characters in names display correctly without crashes
- PyInstaller executables include pdfplumber dependencies and work on clean systems

---

**Last updated:** 2026-02-10
