"""Shared result-table rendering for generated reports."""

from __future__ import annotations

import html


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
