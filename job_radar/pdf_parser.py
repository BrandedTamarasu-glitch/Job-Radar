"""Resume PDF parsing and data extraction.

Validates PDFs, extracts text via pdfplumber, parses structured fields
using regex patterns, and returns dict for wizard pre-population.
"""

import re
from pathlib import Path
from datetime import datetime

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from dateutil import parser as dateutil_parser
except ImportError:
    dateutil_parser = None


class PDFValidationError(Exception):
    """Raised when PDF validation fails (encrypted, image-only, corrupted)."""
    pass


def validate_pdf_file(pdf_path: Path) -> None:
    """Validate PDF file before parsing.

    Checks:
    - pdfplumber is installed
    - File exists and has .pdf extension
    - File size <= 5 MB
    - PDF is text-extractable (not image-only)
    - PDF is not encrypted/password-protected

    Parameters
    ----------
    pdf_path : Path
        Path to PDF file

    Raises
    ------
    PDFValidationError
        If validation fails with actionable error message
    """
    if not PDF_SUPPORT:
        raise PDFValidationError(
            "pdfplumber not installed. Install with: pip install pdfplumber"
        )

    # Check file exists
    if not pdf_path.exists():
        raise PDFValidationError(
            f"File not found: {pdf_path}"
        )

    # Check extension
    if pdf_path.suffix.lower() != '.pdf':
        raise PDFValidationError(
            "File must be a PDF (.pdf extension required)"
        )

    # Check file size (5 MB limit per CONTEXT.md decision)
    file_size_bytes = pdf_path.stat().st_size
    max_size_bytes = 5 * 1024 * 1024  # 5 MB
    if file_size_bytes > max_size_bytes:
        raise PDFValidationError(
            "File size exceeds 5 MB limit. Please use a smaller PDF or fill manually."
        )

    # Check if PDF is text-extractable (not image-only)
    # Open PDF with pdfplumber to check for encryption and text content
    try:
        with pdfplumber.open(pdf_path, strict_metadata=False) as pdf:
            if len(pdf.pages) == 0:
                raise PDFValidationError(
                    "PDF has no pages. The file may be corrupted."
                )

            # Try to extract text from first page
            first_page_text = pdf.pages[0].extract_text()

            # If extract_text() returns None or empty string, PDF is image-only
            if not first_page_text or not first_page_text.strip():
                raise PDFValidationError(
                    "This PDF appears to be image-based. Please use a text-based resume or fill manually."
                )

    except pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect:
        # Encrypted PDF detected
        raise PDFValidationError(
            "This PDF is password-protected. Please use an unencrypted resume or fill manually."
        )

    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError:
        # Corrupted or malformed PDF
        raise PDFValidationError(
            "Unable to read PDF file. The file may be corrupted. Try a different file or fill manually."
        )

    except Exception as e:
        # Catch-all for unexpected pdfplumber errors
        raise PDFValidationError(
            f"Unable to read PDF file: {str(e)}. Try a different file or fill manually."
        )


def extract_resume_data(pdf_path: str | Path) -> dict:
    """Extract structured data from a resume PDF.

    Validates PDF, extracts text via pdfplumber, and parses fields using
    regex patterns. Returns dict with extracted data for wizard pre-fill.

    Parameters
    ----------
    pdf_path : str | Path
        Path to resume PDF file

    Returns
    -------
    dict
        Extracted data with keys: name, years_experience, titles, skills
        Only includes keys where extraction succeeded. Empty dict if all fail.

    Raises
    ------
    PDFValidationError
        If PDF validation fails (encryption, image-only, corrupted, size limit)
    """
    pdf_path = Path(pdf_path)

    # Validate PDF before parsing
    validate_pdf_file(pdf_path)

    # Extract text from all pages with Unicode normalization
    text = ""
    try:
        with pdfplumber.open(pdf_path, unicode_norm='NFKC') as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise PDFValidationError(f"Failed to extract text from PDF: {e}")

    if not text.strip():
        raise PDFValidationError("PDF contains no extractable text")

    # Parse extracted text
    extracted = {}

    # Extract name (heuristic: first non-contact line at top of document)
    name = _extract_name(text)
    if name:
        extracted['name'] = name

    # Extract years of experience
    years = _extract_years_experience(text)
    if years is not None:
        extracted['years_experience'] = years

    # Extract job titles
    titles = _extract_job_titles(text)
    if titles:
        extracted['titles'] = titles

    # Extract skills
    skills = _extract_skills(text)
    if skills:
        extracted['skills'] = skills

    return extracted


def _extract_name(text: str) -> str | None:
    """Extract name from top of resume.

    Heuristic: First non-empty line that doesn't contain contact info
    (email, phone, URL) and is properly capitalized.

    Parameters
    ----------
    text : str
        Full resume text

    Returns
    -------
    str | None
        Extracted name or None if not found
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Regex pattern for contact info (email, phone, URL)
    contact_pattern = re.compile(
        r'@|\.com|\.edu|\.org|http|www\.|'
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|'  # Phone: 123-456-7890, 123.456.7890, etc.
        r'phone|tel|email|linkedin',
        re.IGNORECASE
    )

    # Check first 5 lines for name
    for line in lines[:5]:
        # Skip lines with contact info
        if contact_pattern.search(line):
            continue

        # Skip lines that are all caps (likely section headers)
        if line.isupper() and len(line) > 20:
            continue

        # Check if line looks like a name (2-5 words, proper capitalization)
        words = line.split()
        if 2 <= len(words) <= 5:
            # Check if words are capitalized (allow for middle initials, particles)
            if all(w[0].isupper() or w.lower() in ['von', 'van', 'de', 'la', 'del', 'di'] for w in words if w):
                return line

    return None


def _extract_years_experience(text: str) -> int | None:
    """Extract years of professional experience from resume.

    Strategies:
    1. Look for explicit mention: "X years of experience"
    2. Calculate from work history dates (sum of all employment periods)

    Parameters
    ----------
    text : str
        Full resume text

    Returns
    -------
    int | None
        Years of experience or None if not found
    """
    # Strategy 1: Explicit mention
    # Patterns: "5 years of experience", "5+ years experience", "5 yrs exp"
    exp_pattern = re.compile(
        r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?(?:work\s+)?experience',
        re.IGNORECASE
    )
    match = exp_pattern.search(text)
    if match:
        return int(match.group(1))

    # Strategy 2: Calculate from work history dates
    # Look for date ranges in work experience section
    # Common formats: "Jan 2020 - Present", "2020-2023", "03/2020 - 06/2023"

    # Find work experience section
    exp_section_start = None
    for pattern in [
        r'\b(?:work\s+)?experience\b',
        r'\b(?:employment\s+)?history\b',
        r'\bprofessional\s+experience\b'
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            exp_section_start = match.start()
            break

    if exp_section_start is None:
        return None

    # Extract text from experience section (next ~2000 chars)
    exp_text = text[exp_section_start:exp_section_start + 2000]

    # Find all date ranges
    # Pattern: Month YYYY - Month YYYY, YYYY-YYYY, MM/YYYY - MM/YYYY
    date_range_pattern = re.compile(
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\s*[-–—]\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|Present|Current)',
        re.IGNORECASE
    )

    date_ranges = date_range_pattern.findall(exp_text)

    if not date_ranges:
        # Try numeric format: 2020-2023, 03/2020 - 06/2023
        date_range_pattern = re.compile(r'\d{4}\s*[-–—]\s*(?:\d{4}|Present|Current)', re.IGNORECASE)
        date_ranges = date_range_pattern.findall(exp_text)

    if not date_ranges:
        return None

    # Calculate total years from date ranges
    if dateutil_parser is None:
        # Fallback: Count date ranges and estimate 2 years per job
        return len(date_ranges) * 2

    total_months = 0
    for date_range in date_ranges[:10]:  # Limit to first 10 jobs
        # Parse start and end dates
        parts = re.split(r'\s*[-–—]\s*', date_range)
        if len(parts) != 2:
            continue

        start_str, end_str = parts

        try:
            # Parse start date
            start_date = dateutil_parser.parse(start_str, fuzzy=True)

            # Parse end date (handle "Present" / "Current")
            if re.search(r'present|current', end_str, re.IGNORECASE):
                end_date = datetime.now()
            else:
                end_date = dateutil_parser.parse(end_str, fuzzy=True)

            # Calculate months difference
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            total_months += months

        except Exception:
            # Skip ranges that can't be parsed
            continue

    if total_months > 0:
        return round(total_months / 12)

    return None


def _extract_job_titles(text: str) -> list[str] | None:
    """Extract job titles from work experience section.

    Heuristic: Lines containing title keywords in experience section,
    filtering out company names and common section headers.

    Parameters
    ----------
    text : str
        Full resume text

    Returns
    -------
    list[str] | None
        Extracted job titles or None if not found
    """
    # Find work experience section
    exp_section_start = None
    for pattern in [
        r'\b(?:work\s+)?experience\b',
        r'\b(?:employment\s+)?history\b',
        r'\bprofessional\s+experience\b'
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            exp_section_start = match.start()
            break

    if exp_section_start is None:
        return None

    # Extract text from experience section
    exp_text = text[exp_section_start:exp_section_start + 2000]

    # Common job title patterns (based on Job Radar domain)
    title_keywords = [
        r'engineer', r'developer', r'architect', r'manager', r'analyst',
        r'designer', r'consultant', r'specialist', r'lead', r'senior',
        r'junior', r'principal', r'staff', r'director', r'coordinator'
    ]

    title_pattern = re.compile(
        r'\b(?:' + '|'.join(title_keywords) + r')\b',
        re.IGNORECASE
    )

    titles = []
    lines = exp_text.split('\n')

    for line in lines[:20]:  # First 20 lines of experience section
        line = line.strip()
        if not line:
            continue

        # Check if line contains job title keywords
        if title_pattern.search(line):
            # Filter out lines that look like company names
            if not re.search(r'\b(?:inc|llc|corp|ltd|company)\b', line, re.IGNORECASE):
                # Clean up title (remove date ranges, locations)
                clean_title = re.sub(r'\d{4}\s*[-–—]\s*(?:\d{4}|Present|Current)', '', line, flags=re.IGNORECASE)
                clean_title = re.sub(r'\|.*$', '', clean_title)  # Remove "| Company Name"
                clean_title = clean_title.strip()

                if clean_title and len(clean_title) < 80:  # Reasonable title length
                    titles.append(clean_title)

        if len(titles) >= 3:
            break

    return titles[:3] if titles else None


def _extract_skills(text: str) -> list[str] | None:
    """Extract skills from resume (technical skills, tools, languages).

    Strategies:
    1. Look for "Skills" section and parse as comma/bullet-separated list
    2. Filter out non-skill text (section headers, full sentences)

    Parameters
    ----------
    text : str
        Full resume text

    Returns
    -------
    list[str] | None
        Extracted skills or None if not found
    """
    # Find skills section
    skills_section_start = None
    for pattern in [
        r'\b(?:technical\s+)?skills?\b',
        r'\bcore\s+competencies\b',
        r'\btechnologies\b',
        r'\btools?\s+and\s+technologies\b'
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            skills_section_start = match.start()
            break

    if skills_section_start is None:
        return None

    # Extract text from skills section (next ~500 chars)
    skills_text = text[skills_section_start:skills_section_start + 500]

    # Stop at next major section header
    next_section = re.search(
        r'\n\s*\b(?:experience|education|projects|certifications)\b',
        skills_text,
        re.IGNORECASE
    )
    if next_section:
        skills_text = skills_text[:next_section.start()]

    # Parse skills as comma/bullet/pipe-separated list
    # Remove section header line
    skills_lines = skills_text.split('\n')[1:]
    skills_text = ' '.join(skills_lines)

    # Split by common separators
    skills = re.split(r'[,;•\|\n]+', skills_text)
    skills = [s.strip() for s in skills if s.strip()]

    # Filter out non-skill text (section headers, full sentences)
    filtered_skills = []
    for skill in skills:
        # Skip if too long (likely a sentence, not a skill)
        if len(skill) > 50:
            continue

        # Skip if contains common preamble phrases
        if re.search(r'\b(?:include|such as|proficient in|experience with)\b', skill, re.IGNORECASE):
            continue

        # Keep if looks like a skill (1-5 words, possibly with symbols)
        words = skill.split()
        if 1 <= len(words) <= 5:
            filtered_skills.append(skill)

    return filtered_skills[:20] if filtered_skills else None
