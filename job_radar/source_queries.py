"""Search query construction for automated job sources."""

# Map skill names to hnhiring.com technology slugs.
_HN_SKILL_SLUGS = {
    "react": "react",
    "python": "python",
    "typescript": "typescript",
    "node.js": "node",
    "node": "node",
    "go": "go",
    "golang": "go",
    "javascript": "javascript",
    "kubernetes": "kubernetes",
    "ruby": "ruby",
    "java": "java",
    "rails": "rails",
    "rust": "rust",
    "vue": "vue",
    "angular": "angular",
    ".net": "dotnet",
    "c#": "csharp",
    "kotlin": "kotlin",
    "scala": "scala",
    "swift": "swift",
    "elixir": "elixir",
    "next.js": "nextjs",
    "nextjs": "nextjs",
    "clojure": "clojure",
    "php": "php",
    "django": "python",
    "flutter": "flutter",
    "svelte": "svelte",
    "react native": "react-native",
}


def build_search_queries(profile: dict) -> list[dict]:
    """Generate search queries from a candidate profile."""
    queries = []
    titles = profile.get("target_titles", [])[:4]
    location = profile.get("target_market", profile.get("location", ""))
    core_skills = profile.get("core_skills", [])
    secondary_skills = profile.get("secondary_skills", [])

    for title in titles:
        queries.append({
            "source": "dice",
            "query": title,
            "location": location,
        })

    hn_slugs_seen = set()
    for skill in core_skills + secondary_skills[:5]:
        slug = _HN_SKILL_SLUGS.get(skill.lower())
        if slug and slug not in hn_slugs_seen:
            hn_slugs_seen.add(slug)
            queries.append({
                "source": "hn_hiring",
                "query": slug,
            })

    for title in titles[:2]:
        queries.append({
            "source": "remoteok",
            "query": title,
        })

    for title in titles[:2]:
        queries.append({
            "source": "weworkremotely",
            "query": title,
        })

    for title in titles:
        queries.append({
            "source": "adzuna",
            "query": title,
            "location": location,
        })

    for title in titles[:2]:
        queries.append({
            "source": "authentic_jobs",
            "query": title,
            "location": location,
        })

    for title in titles:
        jsearch_query = {"source": "jsearch", "query": title}
        arrangement = profile.get("arrangement", [])
        if "remote" in [a.lower() for a in arrangement]:
            jsearch_query["location"] = "remote"
        elif location:
            jsearch_query["location"] = location
        queries.append(jsearch_query)

    for title in titles:
        usajobs_query = {"source": "usajobs", "query": title}
        if location:
            usajobs_query["location"] = location
        queries.append(usajobs_query)

    for title in titles:
        serpapi_query = {"source": "serpapi", "query": title}
        if location:
            serpapi_query["location"] = location
        queries.append(serpapi_query)

    for title in titles[:2]:
        queries.append({
            "source": "jobicy",
            "query": title,
            "location": location,
        })

    for title in titles:
        hiringcafe_query = {"source": "hiringcafe", "query": title}
        if location:
            hiringcafe_query["location"] = location
        queries.append(hiringcafe_query)

    return queries
