"""Job source fetchers and URL generators."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from .cache import fetch_with_retry, get_cache_stats, reset_cache_stats
from .api_config import get_api_key
from .rate_limits import check_rate_limit
from .deduplication import deduplicate_cross_source
from .manual_sources import (
    MANUAL_SOURCE_REGISTRY,
    _slugify_for_wellfound,
    generate_glassdoor_url,
    generate_indeed_url,
    generate_linkedin_url,
    generate_manual_urls,
    generate_weworkremotely_url,
    generate_wellfound_url,
    get_manual_source_display_names,
)
from .source_config import (
    resolve_max_workers,
    resolve_slow_query_threshold,
    source_cache_ttl,
)
from .source_execution import SourceExecutionState
from .source_api_fetchers import (
    fetch_adzuna as _fetch_adzuna_api,
    fetch_authenticjobs as _fetch_authenticjobs_api,
    fetch_hiringcafe as _fetch_hiringcafe_api,
    fetch_jobicy,
    fetch_jsearch as _fetch_jsearch_api,
    fetch_serpapi,
    fetch_usajobs as _fetch_usajobs_api,
)
from .source_mappers import (
    _format_hiringcafe_salary,
    _normalize_salary_to_annual,
    map_adzuna_to_job_result,
    map_authenticjobs_to_job_result,
    map_hiringcafe_to_job_result,
    map_jobicy_to_job_result,
    map_jsearch_to_job_result,
    map_serpapi_to_job_result,
    map_usajobs_to_job_result,
)
from .source_models import JobResult
from .source_parsing import (
    _DATE_RE,
    _EMPLOYMENT_TYPE_RE,
    _MAX_COMPANY,
    _MAX_LOCATION,
    _MAX_TITLE,
    _SALARY_RE,
    _SKIP_TOKENS,
    _clean_field,
    _parse_arrangement,
    parse_location_to_city_state,
    strip_html_and_normalize,
)
from .source_queries import build_search_queries
from .source_registry import (
    SourceDefinition,
    selected_automated_source_display_names,
    source_queries_by_phase,
    source_display_name,
)
from .source_scrapers import (
    fetch_dice as _fetch_dice_scraper,
    fetch_hn_hiring as _fetch_hn_hiring_scraper,
    fetch_remoteok as _fetch_remoteok_scraper,
    fetch_weworkremotely as _fetch_weworkremotely_scraper,
)

log = logging.getLogger(__name__)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ---------------------------------------------------------------------------
# Dice.com fetcher (improved field detection)
# ---------------------------------------------------------------------------


def fetch_dice(query: str, location: str = "") -> list[JobResult]:
    """Fetch job listings from Dice.com by scraping search results."""
    return _fetch_dice_scraper(query, location, fetch_with_retry_func=fetch_with_retry)


# ---------------------------------------------------------------------------
# HN Hiring (hnhiring.com) fetcher (improved parsing)
# ---------------------------------------------------------------------------

def fetch_hn_hiring(technology: str) -> list[JobResult]:
    """Fetch job listings from hnhiring.com by technology tag."""
    return _fetch_hn_hiring_scraper(technology, fetch_with_retry_func=fetch_with_retry)


# ---------------------------------------------------------------------------
# RemoteOK fetcher (JSON API)
# ---------------------------------------------------------------------------

def fetch_remoteok(query: str) -> list[JobResult]:
    """Fetch remote job listings from RemoteOK's JSON API."""
    return _fetch_remoteok_scraper(query, fetch_with_retry_func=fetch_with_retry)


# ---------------------------------------------------------------------------
# We Work Remotely fetcher
# ---------------------------------------------------------------------------

# Map source identifiers to display names for progress messages
_SOURCE_DISPLAY_NAMES = {
    "dice": "Dice",
    "hn_hiring": "HN Hiring",
    "remoteok": "RemoteOK",
    "weworkremotely": "We Work Remotely",
    "adzuna": "Adzuna",
    "authentic_jobs": "Authentic Jobs",
    "linkedin": "LinkedIn",
    "indeed": "Indeed",
    "glassdoor": "Glassdoor",
    "jsearch": "JSearch",
    "jsearch_other": "JSearch (Other)",
    "usajobs": "USAJobs (Federal)",
    "serpapi": "SerpAPI (Google Jobs)",
    "jobicy": "Jobicy (Remote)",
    "hiringcafe": "hiring.cafe",
}


def fetch_weworkremotely(query: str) -> list[JobResult]:
    """Fetch remote job listings from We Work Remotely."""
    return _fetch_weworkremotely_scraper(query, fetch_with_retry_func=fetch_with_retry)


# ---------------------------------------------------------------------------
# Adzuna API fetcher
# ---------------------------------------------------------------------------

def fetch_adzuna(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from Adzuna API."""
    return _fetch_adzuna_api(
        query,
        location,
        verbose,
        get_api_key_func=get_api_key,
        check_rate_limit_func=check_rate_limit,
        fetch_with_retry_func=fetch_with_retry,
    )


# ---------------------------------------------------------------------------
# Authentic Jobs API fetcher
# ---------------------------------------------------------------------------

def fetch_authenticjobs(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from Authentic Jobs API."""
    return _fetch_authenticjobs_api(
        query,
        location,
        verbose,
        get_api_key_func=get_api_key,
        check_rate_limit_func=check_rate_limit,
        fetch_with_retry_func=fetch_with_retry,
    )


# ---------------------------------------------------------------------------
# JSearch API fetcher (LinkedIn, Indeed, Glassdoor aggregator)
# ---------------------------------------------------------------------------

def fetch_jsearch(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from JSearch API (aggregates LinkedIn, Indeed, Glassdoor)."""
    return _fetch_jsearch_api(
        query,
        location,
        verbose,
        get_api_key_func=get_api_key,
        check_rate_limit_func=check_rate_limit,
        fetch_with_retry_func=fetch_with_retry,
    )


# ---------------------------------------------------------------------------
# USAJobs API fetcher (Federal government jobs)
# ---------------------------------------------------------------------------

def fetch_usajobs(query: str, location: str = "", profile: dict = None, verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from USAJobs federal government API."""
    return _fetch_usajobs_api(
        query,
        location,
        profile,
        verbose,
        get_api_key_func=get_api_key,
        check_rate_limit_func=check_rate_limit,
        fetch_with_retry_func=fetch_with_retry,
    )


# ---------------------------------------------------------------------------
# SerpAPI Google Jobs fetcher
# ---------------------------------------------------------------------------

def fetch_hiringcafe(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from hiring.cafe."""
    return _fetch_hiringcafe_api(
        query,
        location,
        verbose,
        check_rate_limit_func=check_rate_limit,
        fetch_with_retry_func=fetch_with_retry,
        mapper_func=map_hiringcafe_to_job_result,
    )


# ---------------------------------------------------------------------------
# Parallel fetcher orchestration
# ---------------------------------------------------------------------------

def _fetch_dice_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_dice(query["query"], query.get("location", ""))


def _fetch_hn_hiring_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_hn_hiring(query["query"])


def _fetch_remoteok_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_remoteok(query["query"])


def _fetch_weworkremotely_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_weworkremotely(query["query"])


def _fetch_adzuna_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_adzuna(query["query"], query.get("location", ""))


def _fetch_authentic_jobs_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_authenticjobs(query["query"], query.get("location", ""))


def _fetch_jsearch_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_jsearch(query["query"], query.get("location", ""))


def _fetch_usajobs_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_usajobs(query["query"], query.get("location", ""), profile=profile)


def _fetch_serpapi_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_serpapi(query["query"], query.get("location", ""))


def _fetch_jobicy_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_jobicy(query["query"], query.get("location", ""))


def _fetch_hiringcafe_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_hiringcafe(query["query"], query.get("location", ""))


SOURCE_PHASE_ORDER = ("scraper", "api", "aggregator")


SOURCE_REGISTRY: dict[str, SourceDefinition] = {
    "dice": SourceDefinition("dice", "Dice", "scraper", _fetch_dice_query),
    "hn_hiring": SourceDefinition("hn_hiring", "HN Hiring", "scraper", _fetch_hn_hiring_query),
    "remoteok": SourceDefinition("remoteok", "RemoteOK", "scraper", _fetch_remoteok_query),
    "weworkremotely": SourceDefinition("weworkremotely", "We Work Remotely", "scraper", _fetch_weworkremotely_query),
    "adzuna": SourceDefinition("adzuna", "Adzuna", "api", _fetch_adzuna_query),
    "authentic_jobs": SourceDefinition("authentic_jobs", "Authentic Jobs", "api", _fetch_authentic_jobs_query),
    "usajobs": SourceDefinition("usajobs", "USAJobs (Federal)", "api", _fetch_usajobs_query),
    "jobicy": SourceDefinition("jobicy", "Jobicy (Remote)", "api", _fetch_jobicy_query),
    "hiringcafe": SourceDefinition("hiringcafe", "hiring.cafe", "api", _fetch_hiringcafe_query),
    "jsearch": SourceDefinition("jsearch", "JSearch", "aggregator", _fetch_jsearch_query),
    "serpapi": SourceDefinition("serpapi", "SerpAPI (Google Jobs)", "aggregator", _fetch_serpapi_query),
}


def get_automated_source_display_names() -> list[str]:
    """Return automated source names in execution order for reports."""
    return get_selected_source_display_names(None)


def get_selected_source_display_names(selected_sources: list[str] | None = None) -> list[str]:
    """Return automated source display names for selected source keys."""
    return selected_automated_source_display_names(
        SOURCE_REGISTRY,
        SOURCE_PHASE_ORDER,
        selected_sources,
    )


def _source_display_name(source: str) -> str:
    """Return a human-readable source name for query or result source keys."""
    return source_display_name(SOURCE_REGISTRY, _SOURCE_DISPLAY_NAMES, source)


def get_source_display_name(source: str) -> str:
    """Return a public human-readable source name for diagnostics."""
    return _source_display_name(source)


def fetch_all(
    profile: dict,
    on_progress=None,
    on_source_progress=None,
    max_workers: int | str | None = None,
    slow_query_seconds: int | float | str | None = None,
    selected_sources: list[str] | None = None,
    cancellation_event=None,
) -> list[JobResult]:
    """Fetch from all automated sources with three-phase source ordering.

    Runs scrapers first, native APIs second, and aggregators last so native
    sources win when cross-source deduplication keeps an equally rich listing.
    All results are deduplicated using cross-source fuzzy matching.

    Args:
        profile: Candidate profile dict.
        on_progress: Optional callback(completed, total, source_name) called
                     after each query finishes (backward compatibility).
        on_source_progress: Optional callback(source_name, count, total, status, job_count)
                           called when a source starts ('started') or finishes ('complete').
                           job_count is the number of deduplicated results from that source (0 for 'started').
        max_workers: Optional parallel query worker count. Defaults to JOB_RADAR_MAX_WORKERS or 6.
        slow_query_seconds: Optional threshold for slow-query warnings.
                            Defaults to JOB_RADAR_SLOW_QUERY_SECONDS or 8.
        selected_sources: Optional list of source keys to query. Defaults to all sources.
        cancellation_event: Optional threading.Event-like object. When set,
                            stops new query submission and skips later phases.
    """
    worker_count = resolve_max_workers(max_workers)
    slow_query_threshold = resolve_slow_query_threshold(slow_query_seconds)
    reset_cache_stats()
    queries = build_search_queries(profile)
    queries, queries_by_phase = source_queries_by_phase(
        queries,
        SOURCE_REGISTRY,
        SOURCE_PHASE_ORDER,
        selected_sources,
    )

    all_results = []
    run_state = SourceExecutionState(queries)

    def run_query(q):
        if cancellation_event is not None and cancellation_event.is_set():
            return []
        source = SOURCE_REGISTRY.get(q["source"])
        if source is None:
            log.warning("Unknown source skipped: %s", q["source"])
            return []
        return source.fetch(q, profile)

    def _run_queries_parallel(query_list, phase_name):
        """Helper to run queries in parallel and collect results."""
        phase_results = []

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            # Submit queries grouped by source — fire START callback before each source's queries
            futures = {}
            future_started_at = {}
            started_sources_in_phase = set()
            for q in query_list:
                if cancellation_event is not None and cancellation_event.is_set():
                    break
                source = q["source"]
                if source not in started_sources_in_phase:
                    started_sources_in_phase.add(source)
                    source_index = run_state.mark_source_started()
                    if on_source_progress:
                        display_name = _source_display_name(source)
                        on_source_progress(
                            display_name,
                            source_index,
                            run_state.total_sources,
                            "started",
                            0,
                        )
                future = executor.submit(run_query, q)
                futures[future] = q
                future_started_at[future] = time.perf_counter()

            # Process results as they complete — fire COMPLETE callback when source finishes
            for future in as_completed(futures):
                if cancellation_event is not None and cancellation_event.is_set():
                    for pending in futures:
                        if not pending.done():
                            pending.cancel()
                    break
                q = futures[future]
                completed = run_state.mark_query_complete()
                source = q["source"]
                elapsed = time.perf_counter() - future_started_at[future]
                if elapsed >= slow_query_threshold:
                    run_state.record_slow_query(q, elapsed, slow_query_threshold)
                try:
                    results = future.result()
                    for r in results:
                        if run_state.record_result(source, r):
                            phase_results.append(r)
                except Exception as e:
                    run_state.record_failure(q, e)
                    log.error("Query failed (%s): %s", q, e)
                if on_progress:
                    on_progress(completed, run_state.total_queries, source)

                # Source-level completion tracking
                if run_state.mark_source_query_complete(source):
                    if on_source_progress:
                        display_name = _source_display_name(source)
                        on_source_progress(
                            display_name,
                            run_state.completed_source_count(),
                            run_state.total_sources,
                            "complete",
                            run_state.job_count_for_source(source),
                        )

        return phase_results

    log.info("Running %d search queries in sequential phases with %d workers...", len(queries), worker_count)

    for phase in SOURCE_PHASE_ORDER:
        if cancellation_event is not None and cancellation_event.is_set():
            break
        phase_queries = queries_by_phase[phase]
        if phase_queries:
            log.debug("Running %d %s queries", len(phase_queries), phase)
            all_results.extend(_run_queries_parallel(phase_queries, phase))

    log.info("Total results before deduplication: %d", len(all_results))

    # Cross-source deduplication
    dedup_result = deduplicate_cross_source(all_results)
    all_results = dedup_result["results"]
    dedup_stats = dedup_result["stats"]
    dedup_stats["query_failures"] = len(run_state.query_failures)
    dedup_stats["failed_sources"] = sorted({f["source"] for f in run_state.query_failures})
    dedup_stats["query_failure_details"] = run_state.query_failures
    dedup_stats["slow_query_warnings"] = run_state.slow_query_warnings
    dedup_stats["slow_queries"] = len(run_state.slow_query_warnings)
    dedup_stats["max_workers"] = worker_count
    dedup_stats["slow_query_threshold_seconds"] = slow_query_threshold
    dedup_stats["cache_stats"] = get_cache_stats()
    dedup_stats["cancelled"] = bool(cancellation_event and cancellation_event.is_set())

    log.info("Total unique results after deduplication: %d", len(all_results))
    return all_results, dedup_stats
