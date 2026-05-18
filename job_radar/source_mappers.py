"""API response mappers for source adapters."""

import logging

from .source_models import JobResult
from .source_parsing import (
    _MAX_COMPANY,
    _MAX_LOCATION,
    _MAX_TITLE,
    _clean_field,
    _parse_arrangement,
    parse_location_to_city_state,
    strip_html_and_normalize,
)

log = logging.getLogger(__name__)

JSEARCH_KNOWN_SOURCES = {"LinkedIn", "Indeed", "Glassdoor"}


def map_adzuna_to_job_result(item: dict) -> JobResult | None:
    """Map Adzuna API response item to JobResult."""
    title = item.get("title", "").strip()
    company = item.get("company", {}).get("display_name", "").strip()
    url = item.get("redirect_url", "").strip()

    if not title or not company or not url:
        log.debug("[Adzuna] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                  bool(title), bool(company), bool(url))
        return None

    location_raw = item.get("location", {}).get("display_name", "")
    location = parse_location_to_city_state(location_raw)

    salary_min = item.get("salary_min")
    salary_max = item.get("salary_max")
    salary_currency = "USD"

    if salary_min and salary_max:
        salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
    elif salary_min:
        salary = f"${salary_min:,.0f}+"
    else:
        salary = "Not specified"

    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    arrangement = _parse_arrangement(f"{title} {description}")

    contract_type = item.get("contract_type", "").lower()
    contract_time = item.get("contract_time", "").lower()
    emp_type = ""
    if "permanent" in contract_type:
        emp_type = "Permanent"
    if "full_time" in contract_time or "full-time" in contract_time:
        emp_type = "Full-time" if not emp_type else f"{emp_type}, Full-time"

    date_posted = item.get("created", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="adzuna",
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
    )


def map_authenticjobs_to_job_result(item: dict) -> JobResult | None:
    """Map Authentic Jobs API response item to JobResult."""
    title = item.get("title", "").strip()

    company_raw = item.get("company", {})
    if isinstance(company_raw, dict):
        company = company_raw.get("name", "").strip()
    else:
        company = str(company_raw).strip() if company_raw else ""

    url = item.get("url", "").strip() or item.get("apply_url", "").strip()

    if not title or not company or not url:
        log.debug("[Authentic Jobs] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                  bool(title), bool(company), bool(url))
        return None

    location_raw = ""
    if isinstance(company_raw, dict):
        location_obj = company_raw.get("location", {})
        if isinstance(location_obj, dict):
            location_raw = location_obj.get("name", "")
        elif location_obj:
            location_raw = str(location_obj)
    location = parse_location_to_city_state(location_raw)

    salary = "Not specified"

    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    arrangement = _parse_arrangement(f"{title} {description}")

    emp_type_obj = item.get("type", {})
    if isinstance(emp_type_obj, dict):
        emp_type = emp_type_obj.get("name", "")
    else:
        emp_type = str(emp_type_obj) if emp_type_obj else ""

    date_posted = item.get("post_date", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="authentic_jobs",
        employment_type=emp_type,
        parse_confidence="high",
    )


def map_jsearch_to_job_result(item: dict) -> JobResult | None:
    """Map JSearch API response item to JobResult."""
    title = item.get("job_title", "").strip()
    company = item.get("employer_name", "").strip()
    url = item.get("job_apply_link", "").strip()

    if not title or not company or not url:
        log.debug("[JSearch] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                  bool(title), bool(company), bool(url))
        return None

    publisher = item.get("job_publisher", "")
    if publisher in JSEARCH_KNOWN_SOURCES:
        source = publisher.lower()
    else:
        source = "jsearch_other"
        if publisher:
            log.debug("[JSearch] Unknown publisher '%s' mapped to jsearch_other", publisher)

    is_remote = item.get("job_is_remote", False)
    if is_remote:
        location = "Remote"
    else:
        city = item.get("job_city", "")
        state = item.get("job_state", "")
        if city and state:
            location = f"{city}, {state}"
        else:
            location = item.get("job_country", "Unknown")

    salary_min = item.get("job_min_salary")
    salary_max = item.get("job_max_salary")

    if salary_min and salary_max:
        salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
    elif salary_min:
        salary = f"${salary_min:,.0f}+"
    else:
        salary = "Not specified"

    description_raw = item.get("job_description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    date_posted = item.get("job_posted_at_datetime_utc", "")
    if len(date_posted) >= 10:
        date_posted = date_posted[:10]

    arrangement = _parse_arrangement(f"{title} {description} {location}")

    emp_type = item.get("job_employment_type", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source=source,
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD" if salary_min or salary_max else None,
    )


def map_usajobs_to_job_result(item: dict) -> JobResult | None:
    """Map USAJobs API response item to JobResult."""
    descriptor = item.get("MatchedObjectDescriptor", {})

    title = descriptor.get("PositionTitle", "").strip()
    company = descriptor.get("OrganizationName", "").strip()
    url = descriptor.get("PositionURI", "").strip()

    if not title or not company or not url:
        log.debug("[USAJobs] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                  bool(title), bool(company), bool(url))
        return None

    location = descriptor.get("PositionLocationDisplay", "")
    if not location:
        locations = descriptor.get("PositionLocation", [])
        if locations and isinstance(locations, list):
            loc_obj = locations[0]
            city = loc_obj.get("LocationName", "")
            state = loc_obj.get("CountrySubDivisionCode", "")
            location = f"{city}, {state}" if city and state else (city or "Unknown")

    salary = "Not specified"
    salary_min = None
    salary_max = None
    remuneration = descriptor.get("PositionRemuneration", [])
    if remuneration and isinstance(remuneration, list):
        rem = remuneration[0]
        min_range = rem.get("MinimumRange")
        max_range = rem.get("MaximumRange")
        if min_range and max_range:
            try:
                salary_min = float(min_range)
                salary_max = float(max_range)
                salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
            except (ValueError, TypeError):
                pass

    user_area = descriptor.get("UserArea", {})
    details = user_area.get("Details", {}) if isinstance(user_area, dict) else {}
    description_raw = details.get("JobSummary", "") if isinstance(details, dict) else ""
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    date_posted = descriptor.get("PublicationStartDate", "")
    if len(date_posted) >= 10:
        date_posted = date_posted[:10]

    arrangement = _parse_arrangement(f"{title} {description}")

    emp_type = ""
    schedules = descriptor.get("PositionSchedule", [])
    if schedules and isinstance(schedules, list) and len(schedules) > 0:
        emp_type = schedules[0].get("Name", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="usajobs",
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD" if salary_min or salary_max else None,
    )


def map_serpapi_to_job_result(item: dict) -> JobResult | None:
    """Map SerpAPI Google Jobs response item to JobResult."""
    title = item.get("title", "").strip()
    company = item.get("company_name", "").strip()

    apply_options = item.get("apply_options", [])
    url = ""
    if apply_options and isinstance(apply_options, list):
        url = apply_options[0].get("link", "").strip()
    if not url:
        url = item.get("share_link", "").strip()

    if not title or not company or not url:
        log.debug("[SerpAPI] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                  bool(title), bool(company), bool(url))
        return None

    location_raw = item.get("location", "")
    location = parse_location_to_city_state(location_raw)

    extensions = item.get("detected_extensions", {})
    if extensions.get("work_from_home"):
        arrangement = "remote"
    else:
        arrangement = _parse_arrangement(f"{title} {item.get('description', '')}")

    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    emp_type = extensions.get("schedule_type", "")
    salary = "Not specified"
    date_posted = extensions.get("posted_at", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="serpapi",
        employment_type=emp_type,
        parse_confidence="high",
    )


def map_jobicy_to_job_result(item: dict) -> JobResult | None:
    """Map Jobicy API response item to JobResult."""
    title = item.get("jobTitle", "").strip()
    company = item.get("companyName", "").strip()
    url = item.get("url", "").strip()

    if not title or not company or not url:
        log.debug("[Jobicy] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                  bool(title), bool(company), bool(url))
        return None

    location_raw = item.get("jobGeo", "")
    location = location_raw if location_raw else "Remote"
    arrangement = "remote"

    description_raw = item.get("jobDescription", "")
    if not description_raw:
        description_raw = item.get("jobExcerpt", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    if not description:
        log.debug("[Jobicy] Skipping job with empty description: %s at %s", title, company)
        return None

    emp_type = item.get("jobType", "")

    salary_min_str = item.get("annualSalaryMin", "")
    salary_max_str = item.get("annualSalaryMax", "")
    salary_currency = item.get("salaryCurrency", "USD")
    salary_min = None
    salary_max = None

    if salary_min_str and salary_max_str:
        try:
            salary_min = float(salary_min_str)
            salary_max = float(salary_max_str)
            salary = f"{salary_currency} {int(salary_min):,}-{int(salary_max):,}/yr"
        except (ValueError, TypeError):
            salary = "Not specified"
    elif salary_min_str:
        try:
            salary_min = float(salary_min_str)
            salary = f"{salary_currency} {int(salary_min):,}+/yr"
        except (ValueError, TypeError):
            salary = "Not specified"
    else:
        salary = "Not specified"

    date_posted = item.get("pubDate", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="jobicy",
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
    )


def _normalize_salary_to_annual(value: float, period: str) -> float:
    """Convert salary to annual equivalent."""
    period_lower = period.lower()
    if period_lower in ("hour", "hourly"):
        return value * 2080
    elif period_lower in ("month", "monthly"):
        return value * 12
    elif period_lower in ("year", "yearly", "annual", "annually"):
        return value
    else:
        if value < 500:
            return value * 2080
        elif value < 20000:
            return value * 12
        return value


def _format_hiringcafe_salary(salary_min: float | None, salary_max: float | None) -> str:
    """Format salary to standardized $XXXK range per user decision."""
    if salary_min and salary_max:
        return f"${int(salary_min / 1000)}K - ${int(salary_max / 1000)}K"
    elif salary_min:
        return f"${int(salary_min / 1000)}K+"
    return "Not listed"


def map_hiringcafe_to_job_result(item: dict) -> JobResult | None:
    """Map hiring.cafe response item to JobResult."""
    title = item.get("title", "").strip()
    company = item.get("company", "").strip()
    url = item.get("url", "").strip()

    if not title or not company or not url:
        log.debug("[hiring.cafe] Skipping job with missing required fields: "
                  "title=%s, company=%s, url=%s",
                  bool(title), bool(company), bool(url))
        return None

    salary_min_raw = item.get("salary_min")
    salary_max_raw = item.get("salary_max")
    salary_period = item.get("salary_period", "yearly")

    salary_min = None
    salary_max = None
    if salary_min_raw is not None:
        try:
            salary_min = _normalize_salary_to_annual(float(salary_min_raw), salary_period)
        except (ValueError, TypeError):
            pass
    if salary_max_raw is not None:
        try:
            salary_max = _normalize_salary_to_annual(float(salary_max_raw), salary_period)
        except (ValueError, TypeError):
            pass

    salary = _format_hiringcafe_salary(salary_min, salary_max)

    location_raw = item.get("location", "")
    location = parse_location_to_city_state(location_raw)

    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    arrangement = _parse_arrangement(f"{title} {description} {location}")
    emp_type = item.get("employment_type", "")
    date_posted = item.get("date_posted", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="hiringcafe",
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD" if salary_min or salary_max else None,
    )
