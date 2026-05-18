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
