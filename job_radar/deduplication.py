"""Cross-source fuzzy deduplication for job listings."""

import logging
from collections import defaultdict
from rapidfuzz import fuzz

log = logging.getLogger(__name__)


def deduplicate_cross_source(results: list, threshold: int = 85) -> list:
    """Remove duplicate jobs across sources using fuzzy matching.

    Match criteria:
    - Title similarity (token_sort_ratio >= threshold)
    - Company similarity (token_sort_ratio >= threshold)
    - Location similarity (ratio >= 80)

    All three must match to be considered duplicate.
    Keeps first occurrence (preserves source priority).

    Optimization: Buckets by normalized company first word to reduce comparisons.

    Args:
        results: List of JobResult objects
        threshold: Similarity threshold (0-100), default 85

    Returns:
        Deduplicated list of JobResult objects
    """
    if not results:
        return []

    if len(results) == 1:
        return results

    # Bucket by normalized company name (optimization: reduces O(N²) to O(N*B))
    buckets = defaultdict(list)
    for job in results:
        # Use first word of company as bucket key (e.g., "Google Inc" → "google")
        bucket_key = job.company.split()[0].lower() if job.company else "unknown"
        buckets[bucket_key].append(job)

    seen = []
    seen_keys = set()  # Fast exact duplicate check

    for bucket in buckets.values():
        for job in bucket:
            # Fast path: exact duplicate check
            key = (job.title.lower(), job.company.lower(), job.location.lower())
            if key in seen_keys:
                log.debug(f"Exact duplicate: {job.title} at {job.company} ({job.source})")
                continue

            # Fuzzy duplicate check against seen jobs in same bucket
            is_duplicate = False
            for seen_job in seen:
                # Only compare within same bucket (optimization)
                seen_bucket_key = seen_job.company.split()[0].lower() if seen_job.company else "unknown"
                job_bucket_key = job.company.split()[0].lower() if job.company else "unknown"
                if seen_bucket_key != job_bucket_key:
                    continue

                # Compute similarity scores
                title_sim = fuzz.token_sort_ratio(job.title, seen_job.title)
                company_sim = fuzz.token_sort_ratio(job.company, seen_job.company)
                location_sim = fuzz.ratio(job.location, seen_job.location)

                # All three must match
                if title_sim >= threshold and company_sim >= threshold and location_sim >= 80:
                    log.debug(
                        f"Fuzzy duplicate: {job.title} at {job.company} ({job.source}) "
                        f"matches {seen_job.source} (title={title_sim}, company={company_sim}, location={location_sim})"
                    )
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen.append(job)
                seen_keys.add(key)

    original_count = len(results)
    deduped_count = len(seen)
    if original_count > deduped_count:
        log.info(
            f"Deduplication: {original_count} -> {deduped_count} jobs "
            f"({original_count - deduped_count} duplicates removed)"
        )

    return seen
