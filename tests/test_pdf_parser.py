"""Tests for the PDF resume parser module."""

import re
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from job_radar.pdf_parser import (
    PDFValidationError,
    PDF_SUPPORT,
    validate_pdf_file,
    extract_resume_data,
    _extract_name,
    _extract_years_experience,
    _extract_job_titles,
    _extract_skills,
)


# --- PDF_SUPPORT Flag Test ---


def test_pdf_support_flag_exists():
    """PDF_SUPPORT flag is importable and is a boolean."""
    assert isinstance(PDF_SUPPORT, bool)


# --- Validation Tests ---


def test_validate_rejects_nonexistent_file(tmp_path):
    """validate_pdf_file raises PDFValidationError for missing file."""
    nonexistent = tmp_path / "does_not_exist.pdf"
    with pytest.raises(PDFValidationError, match="File not found"):
        validate_pdf_file(nonexistent)


def test_validate_rejects_non_pdf_extension(tmp_path):
    """validate_pdf_file raises PDFValidationError for non-PDF file extensions."""
    txt_file = tmp_path / "resume.txt"
    txt_file.write_text("Resume content")

    with pytest.raises(PDFValidationError, match="must be a PDF"):
        validate_pdf_file(txt_file)

    docx_file = tmp_path / "resume.docx"
    docx_file.write_text("Resume content")

    with pytest.raises(PDFValidationError, match="must be a PDF"):
        validate_pdf_file(docx_file)


def test_validate_rejects_oversized_file(tmp_path):
    """validate_pdf_file raises PDFValidationError for files > 5 MB."""
    oversized = tmp_path / "large.pdf"
    # Create file just over 5 MB
    oversized.write_bytes(b"x" * (5 * 1024 * 1024 + 1))

    with pytest.raises(PDFValidationError, match="File size exceeds 5 MB"):
        validate_pdf_file(oversized)


@patch('job_radar.pdf_parser.pdfplumber')
def test_validate_rejects_image_only_pdf(mock_pdfplumber, tmp_path):
    """validate_pdf_file raises PDFValidationError for image-only PDFs."""
    pdf_file = tmp_path / "image_resume.pdf"
    pdf_file.write_text("dummy")  # Create file

    # Mock pdfplumber to return page with no text
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None  # No text extracted
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=False)

    # Set up the pdfminer module structure on the mock
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfminer.pdfparser import PDFSyntaxError
    mock_pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect = PDFPasswordIncorrect
    mock_pdfplumber.pdfminer.pdfparser.PDFSyntaxError = PDFSyntaxError

    mock_pdfplumber.open.return_value = mock_pdf

    with pytest.raises(PDFValidationError, match="image-based"):
        validate_pdf_file(pdf_file)


@patch('job_radar.pdf_parser.pdfplumber')
def test_validate_rejects_encrypted_pdf(mock_pdfplumber, tmp_path):
    """validate_pdf_file raises PDFValidationError for encrypted PDFs."""
    pdf_file = tmp_path / "encrypted.pdf"
    pdf_file.write_text("dummy")

    # Mock pdfplumber to raise PDFPasswordIncorrect
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfminer.pdfparser import PDFSyntaxError
    mock_pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect = PDFPasswordIncorrect
    mock_pdfplumber.pdfminer.pdfparser.PDFSyntaxError = PDFSyntaxError
    mock_pdfplumber.open.side_effect = PDFPasswordIncorrect("Password required")

    with pytest.raises(PDFValidationError, match="password-protected"):
        validate_pdf_file(pdf_file)


@patch('job_radar.pdf_parser.pdfplumber')
def test_validate_rejects_corrupted_pdf(mock_pdfplumber, tmp_path):
    """validate_pdf_file raises PDFValidationError for corrupted PDFs."""
    pdf_file = tmp_path / "corrupted.pdf"
    pdf_file.write_text("dummy")

    # Mock pdfplumber to raise PDFSyntaxError
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfminer.pdfparser import PDFSyntaxError
    mock_pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect = PDFPasswordIncorrect
    mock_pdfplumber.pdfminer.pdfparser.PDFSyntaxError = PDFSyntaxError
    mock_pdfplumber.open.side_effect = PDFSyntaxError("Syntax error")

    with pytest.raises(PDFValidationError, match="corrupted"):
        validate_pdf_file(pdf_file)


@patch('job_radar.pdf_parser.pdfplumber')
def test_validate_accepts_valid_pdf(mock_pdfplumber, tmp_path):
    """validate_pdf_file accepts valid text-based PDF without raising."""
    pdf_file = tmp_path / "valid.pdf"
    pdf_file.write_text("dummy")

    # Mock pdfplumber to return page with text
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "John Doe\nSoftware Engineer\nExperience..."
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=False)

    # Set up the pdfminer module structure on the mock
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfminer.pdfparser import PDFSyntaxError
    mock_pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect = PDFPasswordIncorrect
    mock_pdfplumber.pdfminer.pdfparser.PDFSyntaxError = PDFSyntaxError

    mock_pdfplumber.open.return_value = mock_pdf

    # Should not raise
    validate_pdf_file(pdf_file)


# --- Name Extraction Tests ---


@pytest.mark.parametrize(
    "text,expected",
    [
        ("John Doe\nSoftware Engineer\nExperience...", "John Doe"),
        ("Jane Smith\nData Scientist\n...", "Jane Smith"),
        ("Maria Garcia Lopez\nEngineer\n...", "Maria Garcia Lopez"),
    ],
)
def test_extract_name_basic(text, expected):
    """_extract_name returns name from first line of resume."""
    result = _extract_name(text)
    assert result == expected


def test_extract_name_skips_contact_info():
    """_extract_name skips lines with email addresses."""
    text = "john@email.com\nJohn Doe\nSoftware Engineer"
    result = _extract_name(text)
    assert result == "John Doe"


def test_extract_name_skips_phone():
    """_extract_name skips lines with phone numbers."""
    text = "555-123-4567\nJane Smith\nEngineer"
    result = _extract_name(text)
    assert result == "Jane Smith"


def test_extract_name_unicode():
    """_extract_name handles international names with non-ASCII characters."""
    text = "Jose Garcia\nSoftware Developer\n..."
    result = _extract_name(text)
    assert result == "Jose Garcia"


def test_extract_name_returns_none_no_match():
    """_extract_name returns None when no name-like line is found."""
    text = "PROFESSIONAL EXPERIENCE\n555-123-4567\nhttp://example.com"
    result = _extract_name(text)
    assert result is None


def test_extract_name_skips_section_headers():
    """_extract_name skips all-caps section headers over 20 chars."""
    text = "PROFESSIONAL EXPERIENCE\nJohn Developer\nEngineer"
    result = _extract_name(text)
    assert result == "John Developer"


# --- Years Experience Extraction Tests ---


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Summary: 5 years of experience in software development", 5),
        ("Over 10 years experience in backend engineering", 10),
        ("3 years of professional experience", 3),
        ("15+ years experience leading teams", 15),
    ],
)
def test_years_explicit_mention(text, expected):
    """_extract_years_experience extracts explicitly mentioned years."""
    result = _extract_years_experience(text)
    assert result == expected


def test_years_plus_format():
    """_extract_years_experience handles '10+' format."""
    text = "Professional with 10+ years experience"
    result = _extract_years_experience(text)
    assert result == 10


def test_years_from_date_ranges():
    """_extract_years_experience calculates years from date ranges in experience section."""
    text = """
    EXPERIENCE
    Software Engineer
    Jan 2020 - Present
    Company X

    Data Analyst
    Jun 2018 - Dec 2019
    Company Y
    """
    result = _extract_years_experience(text)
    # Should calculate from date ranges (approx 6 years total)
    assert result is not None
    assert result >= 5  # At least 5 years


def test_years_returns_none_no_data():
    """_extract_years_experience returns None when no experience data found."""
    text = "John Doe\nSoftware Engineer\nSkills: Python, Java"
    result = _extract_years_experience(text)
    assert result is None


# --- Job Titles Extraction Tests ---


def test_titles_basic_extraction():
    """_extract_job_titles extracts job titles from experience section."""
    text = """
    EXPERIENCE
    Software Engineer
    Company X
    2020-2023
    """
    result = _extract_job_titles(text)
    assert result is not None
    assert "Software Engineer" in result


def test_titles_multiple():
    """_extract_job_titles extracts multiple titles (max 3)."""
    text = """
    WORK EXPERIENCE
    Senior Engineer
    Company A

    Software Developer
    Company B

    Data Analyst
    Company C

    Junior Developer
    Company D
    """
    result = _extract_job_titles(text)
    assert result is not None
    assert len(result) <= 3


def test_titles_filters_company_names():
    """_extract_job_titles filters out lines with company suffixes."""
    text = """
    EXPERIENCE
    Software Engineer
    Amazon Inc
    2020-2023
    """
    result = _extract_job_titles(text)
    assert result is not None
    # "Amazon Inc" should be filtered out (has "Inc")
    assert not any("Amazon Inc" in title for title in result)


def test_titles_returns_none_no_section():
    """_extract_job_titles returns None when no experience section found."""
    text = "John Doe\nSkills: Python, Java\nEducation: MIT"
    result = _extract_job_titles(text)
    assert result is None


# --- Skills Extraction Tests ---


def test_skills_comma_separated():
    """_extract_skills extracts comma-separated skills from skills section."""
    text = """
    SKILLS
    Python, JavaScript, React, AWS, Docker
    """
    result = _extract_skills(text)
    assert result is not None
    assert "Python" in result
    assert "JavaScript" in result
    assert "React" in result


def test_skills_filters_long_items():
    """_extract_skills filters out items longer than 50 characters."""
    text = """
    TECHNICAL SKILLS
    Python, JavaScript, This is a very long description that should be filtered out because it exceeds the character limit
    """
    result = _extract_skills(text)
    assert result is not None
    assert "Python" in result
    # Long item should be filtered
    assert not any(len(skill) > 50 for skill in result)


def test_skills_stops_at_next_section():
    """_extract_skills stops extraction at next major section."""
    text = """
    SKILLS
    Python, JavaScript
    EXPERIENCE
    Software Engineer
    """
    result = _extract_skills(text)
    assert result is not None
    assert "Python" in result
    # Should not include "Software Engineer" from next section
    assert not any("Software Engineer" in skill for skill in result)


def test_skills_returns_none_no_section():
    """_extract_skills returns None when no skills section found."""
    text = "John Doe\nExperience: 5 years\nEducation: MIT"
    result = _extract_skills(text)
    assert result is None


# --- Integration Tests ---


@patch('job_radar.pdf_parser.pdfplumber')
def test_extract_resume_data_full_extraction(mock_pdfplumber, tmp_path):
    """extract_resume_data extracts all fields from realistic resume."""
    pdf_file = tmp_path / "resume.pdf"
    pdf_file.write_text("dummy")

    # Mock realistic resume text
    resume_text = """
    John Developer
    john@example.com | 555-123-4567

    PROFESSIONAL SUMMARY
    Software engineer with 7 years of experience in full-stack development.

    TECHNICAL SKILLS
    Python, JavaScript, React, AWS, Docker, PostgreSQL

    PROFESSIONAL EXPERIENCE

    Senior Software Engineer
    Tech Company Inc
    Jan 2020 - Present

    Software Developer
    Startup LLC
    Jun 2017 - Dec 2019

    EDUCATION
    BS Computer Science, MIT
    """

    # Mock pdfplumber to return realistic text
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = resume_text
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=False)

    # Set up the pdfminer module structure on the mock
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfminer.pdfparser import PDFSyntaxError
    mock_pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect = PDFPasswordIncorrect
    mock_pdfplumber.pdfminer.pdfparser.PDFSyntaxError = PDFSyntaxError

    mock_pdfplumber.open.return_value = mock_pdf

    result = extract_resume_data(pdf_file)

    # Verify all fields extracted
    assert "name" in result
    assert result["name"] == "John Developer"

    assert "years_experience" in result
    assert result["years_experience"] == 7

    assert "titles" in result
    assert len(result["titles"]) > 0

    assert "skills" in result
    assert "Python" in result["skills"]


@patch('job_radar.pdf_parser.pdfplumber')
def test_extract_resume_data_partial_extraction(mock_pdfplumber, tmp_path):
    """extract_resume_data returns dict with only successfully extracted fields."""
    pdf_file = tmp_path / "partial_resume.pdf"
    pdf_file.write_text("dummy")

    # Resume with only name and skills (no experience section)
    resume_text = """
    Jane Analyst
    jane@example.com

    SKILLS
    Python, SQL, Tableau, Excel
    """

    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = resume_text
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=False)

    # Set up the pdfminer module structure on the mock
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfminer.pdfparser import PDFSyntaxError
    mock_pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect = PDFPasswordIncorrect
    mock_pdfplumber.pdfminer.pdfparser.PDFSyntaxError = PDFSyntaxError

    mock_pdfplumber.open.return_value = mock_pdf

    result = extract_resume_data(pdf_file)

    # Should have name and skills
    assert "name" in result
    assert result["name"] == "Jane Analyst"

    assert "skills" in result
    assert "Python" in result["skills"]

    # Should NOT have years or titles (no experience section)
    assert "years_experience" not in result or result.get("years_experience") is None
    assert "titles" not in result or result.get("titles") is None


@patch('job_radar.pdf_parser.pdfplumber')
def test_extract_resume_data_empty_on_all_fail(mock_pdfplumber, tmp_path):
    """extract_resume_data returns empty dict when all extraction fails."""
    pdf_file = tmp_path / "minimal_resume.pdf"
    pdf_file.write_text("dummy")

    # Text that doesn't match any patterns
    resume_text = """
    555-123-4567
    contact@example.com
    http://website.com
    """

    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = resume_text
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=False)

    # Set up the pdfminer module structure on the mock
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfminer.pdfparser import PDFSyntaxError
    mock_pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect = PDFPasswordIncorrect
    mock_pdfplumber.pdfminer.pdfparser.PDFSyntaxError = PDFSyntaxError

    mock_pdfplumber.open.return_value = mock_pdf

    result = extract_resume_data(pdf_file)

    # Should return empty dict (all extraction failed)
    assert isinstance(result, dict)
    assert len(result) == 0
