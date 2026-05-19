"""Shared profile field parsing and schema helpers."""

MIN_YEARS_EXPERIENCE = 0
MAX_YEARS_EXPERIENCE = 50
MAX_COMPENSATION_FLOOR = 1_000_000

YEARS_INVALID_MESSAGE = "Please enter a whole number (e.g., 3, 5, 10)"
YEARS_NEGATIVE_MESSAGE = "Years must be 0 or greater"
YEARS_TOO_HIGH_MESSAGE = "Please enter a realistic number of years (0-50)"

COMPENSATION_INVALID_MESSAGE = "Enter a number (e.g., 120000 or 120k)"
COMPENSATION_NEGATIVE_MESSAGE = "Compensation must be positive"
COMPENSATION_TOO_HIGH_MESSAGE = "Please enter a realistic compensation (under $1M)"


def parse_years_experience(text: str) -> int:
    """Parse and validate years of experience from user input."""
    try:
        years = int(str(text).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(YEARS_INVALID_MESSAGE) from exc

    if years < MIN_YEARS_EXPERIENCE:
        raise ValueError(YEARS_NEGATIVE_MESSAGE)
    if years > MAX_YEARS_EXPERIENCE:
        raise ValueError(YEARS_TOO_HIGH_MESSAGE)

    return years


def derive_level(years_experience: int) -> str:
    """Derive profile seniority level from years of experience."""
    if years_experience < 2:
        return "junior"
    if years_experience < 5:
        return "mid"
    if years_experience < 10:
        return "senior"
    return "principal"


def parse_compensation_floor(text: str) -> int | None:
    """Parse and validate an optional compensation floor from user input."""
    cleaned = str(text).strip()
    if not cleaned:
        return None

    cleaned = cleaned.replace(",", "").replace("$", "").strip()
    try:
        value = (
            float(cleaned[:-1]) * 1000
            if cleaned.lower().endswith("k")
            else float(cleaned)
        )
    except ValueError as exc:
        raise ValueError(COMPENSATION_INVALID_MESSAGE) from exc

    if value < 0:
        raise ValueError(COMPENSATION_NEGATIVE_MESSAGE)
    if value > MAX_COMPENSATION_FLOOR:
        raise ValueError(COMPENSATION_TOO_HIGH_MESSAGE)

    return int(value)
