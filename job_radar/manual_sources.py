"""Manual job board URL generators and registry helpers."""

import urllib.parse

from .source_registry import (
    ManualSourceDefinition,
    selected_manual_source_display_names,
)


def _slugify_for_wellfound(text: str) -> str:
    """Convert text to Wellfound URL slug format."""
    slug = text.lower().strip()
    slug = slug.replace(",", "")
    slug = slug.replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def generate_wellfound_url(title: str, location: str) -> str:
    """Generate a Wellfound search URL with role and optional location."""
    role_slug = _slugify_for_wellfound(title)

    if "remote" in location.lower():
        return f"https://wellfound.com/role/r/{role_slug}"

    location_slug = _slugify_for_wellfound(location)
    return f"https://wellfound.com/role/l/{role_slug}/{location_slug}"


def generate_indeed_url(title: str, location: str, from_days: int = 3) -> str:
    """Generate an Indeed search URL with filters."""
    params = {
        "q": title,
        "l": location,
        "fromage": str(from_days),
        "sort": "date",
    }
    return "https://www.indeed.com/jobs?" + urllib.parse.urlencode(params)


def generate_linkedin_url(title: str, location: str) -> str:
    """Generate a LinkedIn job search URL."""
    params = {
        "keywords": title,
        "location": location,
        "f_TPR": "r604800",
        "sortBy": "DD",
    }
    return "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(params)


def generate_glassdoor_url(title: str, location: str) -> str:
    """Generate a Glassdoor job search URL."""
    params = {
        "sc.keyword": title,
        "locT": "",
        "locId": "",
        "locKeyword": location,
        "fromAge": "3",
        "sortBy": "date",
    }
    return "https://www.glassdoor.com/Job/jobs.htm?" + urllib.parse.urlencode(params)


def generate_weworkremotely_url(query: str) -> str:
    """Generate a We Work Remotely search URL."""
    return f"https://weworkremotely.com/remote-jobs/search?term={urllib.parse.quote_plus(query)}"


def _generate_weworkremotely_manual_url(title: str, location: str) -> str:
    """Generate a WWR manual URL with the same signature as location-aware sources."""
    return generate_weworkremotely_url(title)


MANUAL_SOURCE_REGISTRY = {
    "wellfound": ManualSourceDefinition("wellfound", "Wellfound", generate_wellfound_url),
    "indeed": ManualSourceDefinition("indeed", "Indeed", generate_indeed_url),
    "linkedin": ManualSourceDefinition("linkedin", "LinkedIn", generate_linkedin_url),
    "glassdoor": ManualSourceDefinition("glassdoor", "Glassdoor", generate_glassdoor_url),
    "weworkremotely": ManualSourceDefinition(
        "weworkremotely",
        "We Work Remotely",
        _generate_weworkremotely_manual_url,
    ),
}


def get_manual_source_display_names(selected_sources: list[str] | None = None) -> list[str]:
    """Return manual source display names for selected source keys."""
    return selected_manual_source_display_names(MANUAL_SOURCE_REGISTRY, selected_sources)


def generate_manual_urls(
    profile: dict,
    selected_manual_sources: list[str] | None = None,
) -> list[dict]:
    """Generate manual-check URLs for a candidate profile, sorted by source."""
    urls = []
    titles = profile.get("target_titles", [])[:3]
    location = profile.get("target_market", profile.get("location", ""))
    selected = set(selected_manual_sources) if selected_manual_sources is not None else None

    for source in MANUAL_SOURCE_REGISTRY.values():
        if selected is not None and source.key not in selected:
            continue
        for title in titles:
            url = source.generator(title, location)
            urls.append({
                "source": source.display_name,
                "title": title,
                "url": url,
            })

    return urls
