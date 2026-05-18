"""Text parsing and normalization helpers for source adapters."""

import html
import re

from bs4 import BeautifulSoup


_MAX_TITLE = 100
_MAX_COMPANY = 80
_MAX_LOCATION = 60


def _clean_field(text: str, max_len: int) -> str:
    """Truncate and clean a parsed field."""
    text = text.strip()
    if len(text) > max_len:
        return text[:max_len - 3].rsplit(" ", 1)[0] + "..."
    return text


def strip_html_and_normalize(text: str) -> str:
    """Strip HTML tags, decode entities, normalize whitespace."""
    if not text:
        return ""
    text = html.unescape(text)
    soup = BeautifulSoup(text, "html.parser")
    plain_text = soup.get_text(separator=" ")
    normalized = re.sub(r'\s+', ' ', plain_text)
    return normalized.strip()


# Map US state names to abbreviations
_STATE_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}


def parse_location_to_city_state(location_str: str) -> str:
    """Parse location to 'City, State' format."""
    if not location_str:
        return "Unknown"

    if "remote" in location_str.lower():
        return "Remote"

    match = re.match(r'^([^,]+),\s*([A-Z]{2})(?:\s|,|$)', location_str)
    if match:
        city, state = match.groups()
        return f"{city.strip()}, {state.strip()}"

    match = re.match(r'^([^,]+),\s*([^,]+?)(?:\s|,|$)', location_str)
    if match:
        city, state_name = match.groups()
        state_lower = state_name.strip().lower()
        if state_lower in _STATE_ABBREV:
            return f"{city.strip()}, {_STATE_ABBREV[state_lower]}"
        remaining = location_str[match.end():].strip()
        if remaining and ',' not in remaining:
            return f"{city.strip()}, {state_name.strip()}"

    return location_str.strip()


def _parse_arrangement(text: str) -> str:
    """Infer work arrangement from text."""
    lower = text.lower()
    if "remote" in lower:
        return "remote"
    if "hybrid" in lower:
        return "hybrid"
    if "on-site" in lower or "onsite" in lower or "in-office" in lower:
        return "onsite"
    return "unknown"


_SALARY_RE = re.compile(
    r'\$[\d,]+(?:\.\d+)?(?:k|K)?(?:\s*[-–]\s*\$[\d,]+(?:\.\d+)?(?:k|K)?)?'
    r'(?:\s*/?\s*(?:yr|year|hr|hour|annually|monthly|weekly))?'
)
_DATE_RE = re.compile(
    r'(?:Today|Yesterday|\d+\s*d(?:ays?)?\s+ago|'
    r'(?:about\s+)?\d+\s*(?:hours?|minutes?)\s+ago|'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{4}|'
    r'\d{4}-\d{2}-\d{2})',
    re.IGNORECASE,
)
_EMPLOYMENT_TYPE_RE = re.compile(
    r'^(?:Full[ -]?time|Part[ -]?time|Contract|C2H|Contract to Hire|Temp|Freelance)$',
    re.IGNORECASE,
)
_SKIP_TOKENS = {"Easy Apply", "Apply Now", "\u2022", "•", ""}


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', ' ', text).strip()
