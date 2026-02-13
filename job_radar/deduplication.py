"""Cross-source fuzzy deduplication for job listings."""

import logging
from collections import defaultdict
from rapidfuzz import fuzz

log = logging.getLogger(__name__)


def deduplicate_cross_source(results: list, threshold: int = 85) -> dict:
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
        dict with keys:
          - "results": Deduplicated list of JobResult objects
          - "stats": Dict with dedup statistics:
              - "original_count": total before dedup
              - "deduped_count": total after dedup
              - "duplicates_removed": number removed
              - "sources_involved": number of unique sources with duplicates
          - "multi_source": Dict mapping job key -> list of source names
              (only for jobs found on 2+ sources)
    """
    if not results:
        return {
            "results": [],
            "stats": {
                "original_count": 0,
                "deduped_count": 0,
                "duplicates_removed": 0,
                "sources_involved": 0,
            },
            "multi_source": {}
        }

    if len(results) == 1:
        return {
            "results": results,
            "stats": {
                "original_count": 1,
                "deduped_count": 1,
                "duplicates_removed": 0,
                "sources_involved": 0,
            },
            "multi_source": {}
        }

    # Track multi-source matches
    multi_source_map = {}  # (title, company) -> [source1, source2, ...]
    original_count = len(results)

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
                # Record multi-source for exact duplicate
                seen_key = (job.title.lower(), job.company.lower())
                if seen_key not in multi_source_map:
                    # Find the original job and initialize with its source
                    for seen_job in seen:
                        if seen_job.title.lower() == seen_key[0] and seen_job.company.lower() == seen_key[1]:
                            multi_source_map[seen_key] = [seen_job.source]
                            break
                if job.source not in multi_source_map[seen_key]:
                    multi_source_map[seen_key].append(job.source)
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
                    # Record multi-source for fuzzy duplicate
                    seen_key = (seen_job.title.lower(), seen_job.company.lower())
                    if seen_key not in multi_source_map:
                        multi_source_map[seen_key] = [seen_job.source]
                    if job.source not in multi_source_map[seen_key]:
                        multi_source_map[seen_key].append(job.source)
                    break

            if not is_duplicate:
                seen.append(job)
                seen_keys.add(key)

    deduped_count = len(seen)

    # Build stats
    sources_with_dupes = set()
    for key, sources in multi_source_map.items():
        if len(sources) > 1:
            sources_with_dupes.update(sources)

    stats = {
        "original_count": original_count,
        "deduped_count": deduped_count,
        "duplicates_removed": original_count - deduped_count,
        "sources_involved": len(sources_with_dupes),
    }

    if original_count > deduped_count:
        log.info(
            f"Deduplication: {original_count} -> {deduped_count} jobs "
            f"({original_count - deduped_count} duplicates removed)"
        )

    return {"results": seen, "stats": stats, "multi_source": multi_source_map}
