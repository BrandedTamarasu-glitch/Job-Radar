"""Shared result-table rendering for generated reports."""

from __future__ import annotations

import html


def html_zero_results_section(tips: list[str]) -> str:
    """Generate the all-results empty-state guidance section."""
    tip_items = "".join(f"<li>{html.escape(tip)}</li>" for tip in tips)
    return """
        <section aria-labelledby="results-heading">
          <div class="mb-4">
            <h2 id="results-heading" class="h4 mb-3">All Results (sorted by score)</h2>
            <p class="text-muted"><em>No results found.</em></p>
            <h3 class="h5 mt-3">Try next</h3>
            <ul>
              """ + tip_items + """
            </ul>
          </div>
        </section>
        """


def html_results_table_header(caption: str) -> str:
    """Generate the common results table caption and header."""
    return f"""
              <caption class="visually-hidden">{html.escape(caption)}</caption>
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col">Score</th>
                  <th scope="col" class="col-new">New</th>
                  <th scope="col">Status</th>
                  <th scope="col">Title</th>
                  <th scope="col">Company</th>
                  <th scope="col" class="col-salary">Salary</th>
                  <th scope="col" class="col-type">Type</th>
                  <th scope="col">Location</th>
                  <th scope="col" class="col-snippet">Snippet</th>
                  <th scope="col">Link</th>
                </tr>
              </thead>
    """
