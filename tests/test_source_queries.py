"""Tests for automated source query construction."""

from collections import Counter

from job_radar.source_queries import build_search_queries


def test_build_search_queries_includes_all_automated_sources():
    queries = build_search_queries({
        "target_titles": ["Software Engineer"],
        "target_market": "Remote",
        "core_skills": ["Python"],
    })

    assert {query["source"] for query in queries} == {
        "dice",
        "hn_hiring",
        "remoteok",
        "weworkremotely",
        "adzuna",
        "authentic_jobs",
        "jsearch",
        "usajobs",
        "serpapi",
        "jobicy",
        "hiringcafe",
    }


def test_build_search_queries_deduplicates_hn_skill_slugs():
    queries = build_search_queries({
        "target_titles": ["Software Engineer"],
        "core_skills": ["Node.js", "Node", "React"],
        "secondary_skills": ["React"],
    })

    hn_queries = [
        query["query"]
        for query in queries
        if query["source"] == "hn_hiring"
    ]
    assert hn_queries == ["node", "react"]


def test_build_search_queries_limits_title_fanout():
    queries = build_search_queries({
        "target_titles": [
            "Staff Engineer",
            "Backend Engineer",
            "Platform Engineer",
            "Python Engineer",
            "Data Engineer",
        ],
        "target_market": "Austin, TX",
    })
    counts = Counter(query["source"] for query in queries)

    assert counts["dice"] == 4
    assert counts["adzuna"] == 4
    assert counts["remoteok"] == 2
    assert counts["authentic_jobs"] == 2


def test_build_search_queries_maps_remote_arrangement_for_jsearch():
    queries = build_search_queries({
        "target_titles": ["Software Engineer"],
        "target_market": "Austin, TX",
        "arrangement": ["Remote"],
    })

    jsearch_query = next(query for query in queries if query["source"] == "jsearch")
    assert jsearch_query["location"] == "remote"
