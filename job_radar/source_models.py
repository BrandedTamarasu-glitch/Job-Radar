"""Data models shared by job source adapters."""

from dataclasses import dataclass


@dataclass
class JobResult:
    """A single job listing result."""

    title: str
    company: str
    location: str
    arrangement: str  # remote, hybrid, onsite, unknown
    salary: str
    date_posted: str
    description: str
    url: str
    source: str
    apply_info: str = ""
    employment_type: str = ""  # full-time, contract, C2H, part-time, etc.
    parse_confidence: str = "high"  # high, medium, low
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None

    def __hash__(self):
        return hash((self.title, self.company, self.source))
