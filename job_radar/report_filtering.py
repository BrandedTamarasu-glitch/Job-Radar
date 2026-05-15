"""Filtering data helpers for generated reports."""

from __future__ import annotations

import html


def filtered_out_results(scored_results: list[dict], min_score: float) -> list[dict]:
    """Return jobs rejected by dealbreaker or minimum score threshold."""
    return [
        result for result in scored_results
        if result.get("score", {}).get("overall", 0.0) < min_score
    ]


def filter_explanation_text(result: dict, min_score: float) -> str:
    """Build a concise explanation for why a job was filtered out."""
    score = result.get("score", {})
    dealbreaker = score.get("dealbreaker")
    if dealbreaker:
        return f"Rejected by dealbreaker: {dealbreaker}"

    overall = score.get("overall", 0.0)
    components = score.get("components", {})
    reasons = []

    skill = components.get("skill_match", {})
    missing_core = skill.get("missing_core") or []
    if missing_core:
        reasons.append(f"missing core skills: {', '.join(missing_core[:3])}")
    elif skill.get("ratio"):
        reasons.append(f"{skill['ratio']} core skills")

    title = components.get("title_relevance", {})
    if title.get("reason"):
        reasons.append(f"title: {title['reason']}")

    seniority = components.get("seniority", {})
    if seniority.get("reason"):
        reasons.append(f"seniority: {seniority['reason']}")

    location = components.get("location", {})
    if location.get("score", 5.0) < 3.0 and location.get("reason"):
        reasons.append(f"location: {location['reason']}")

    if not reasons:
        reasons.append("score below the selected threshold")

    return f"Below {min_score:g} threshold at {overall}/5.0: " + "; ".join(reasons[:3])


def html_filtered_out_section(filtered_out: list[dict], min_score: float) -> str:
    """Generate HTML for rejected and below-threshold jobs."""
    if not filtered_out:
        return ""

    rows = []
    for result in filtered_out[:10]:
        job = result["job"]
        score = result.get("score", {}).get("overall", 0.0)
        rows.append(f"""
        <tr>
          <td data-label="Title"><strong>{html.escape(job.title)}</strong></td>
          <td data-label="Company">{html.escape(job.company)}</td>
          <td data-label="Score">{score}/5.0</td>
          <td data-label="Why">{html.escape(filter_explanation_text(result, min_score))}</td>
        </tr>
        """)

    omitted = ""
    if len(filtered_out) > 10:
        omitted = (
            f'<p class="text-muted small mb-0">'
            f'{len(filtered_out) - 10} more filtered jobs omitted.</p>'
        )

    return f"""
    <section aria-labelledby="filtered-heading">
      <div class="mb-4">
        <h2 id="filtered-heading" class="h4 mb-3">Filtered Out</h2>
        <p class="text-muted">These jobs were hidden by dealbreakers or the selected minimum score.</p>
        <div class="table-responsive">
          <table class="table table-sm table-striped">
            <caption class="visually-hidden">Jobs filtered out with concise rejection reasons</caption>
            <thead>
              <tr>
                <th scope="col">Title</th>
                <th scope="col">Company</th>
                <th scope="col">Score</th>
                <th scope="col">Why</th>
              </tr>
            </thead>
            <tbody>
              {"".join(rows)}
            </tbody>
          </table>
        </div>
        {omitted}
      </div>
    </section>
    """
