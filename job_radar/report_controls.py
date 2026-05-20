"""Shared interactive control rendering for generated reports."""

from __future__ import annotations

import html


_KEYBOARD_HINT = (
    "Keyboard: <kbd>J</kbd>/<kbd>K</kbd> = navigate, "
    "<kbd>C</kbd> = copy focused, <kbd>A</kbd> = copy all"
)


def html_copy_action_bar(section: str) -> str:
    """Generate copy/export action controls for report job sections."""
    if section == "hero":
        copy_label = "Copy All Top Match URLs"
        copy_handler = "copyAllHeroUrls(this)"
        export_button = ""
    elif section == "recommended":
        copy_label = "Copy All Recommended URLs"
        copy_handler = "copyAllRecommendedUrls(this)"
        export_button = """
      <button class="btn btn-sm btn-outline-info export-status-btn no-print"
              onclick="exportPendingStatusUpdates()">
        Export Status Updates
      </button>"""
        status_sync_note = """
    <p class="text-muted small mt-1 mb-3">
      Status edits stay in this browser until you export JSON and import it from the Applications tab.
    </p>"""
    else:
        raise ValueError(f"Unknown copy action bar section: {section}")

    return f"""
    <div class="d-flex align-items-center mb-3">
      <button class="btn btn-primary copy-all-btn" onclick="{copy_handler}">
        {copy_label}
      </button>{export_button}
      <span class="shortcut-hint ms-2">{_KEYBOARD_HINT}</span>
    </div>
    {status_sync_note if section == "recommended" else ""}
    """


def html_filter_controls() -> str:
    """Generate status filtering and export controls for the all-results table."""
    return """
    <div class="mb-4 no-print" role="region" aria-labelledby="filter-heading">
      <h3 id="filter-heading" class="h5">Filter by Status</h3>
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <div class="btn-group" role="group" aria-label="Status filter checkboxes">
          <input type="checkbox" class="btn-check" id="filter-applied" autocomplete="off">
          <label class="btn btn-outline-secondary btn-sm" for="filter-applied">Hide Applied</label>

          <input type="checkbox" class="btn-check" id="filter-rejected" autocomplete="off">
          <label class="btn btn-outline-secondary btn-sm" for="filter-rejected">Hide Rejected</label>

          <input type="checkbox" class="btn-check" id="filter-interviewing" autocomplete="off">
          <label class="btn btn-outline-secondary btn-sm" for="filter-interviewing">Hide Interviewing</label>

          <input type="checkbox" class="btn-check" id="filter-offer" autocomplete="off">
          <label class="btn btn-outline-secondary btn-sm" for="filter-offer">Hide Offer</label>

          <input type="checkbox" class="btn-check" id="filter-shortlist" autocomplete="off">
          <label class="btn btn-outline-warning btn-sm" for="filter-shortlist">Show Shortlist</label>
        </div>

        <button class="btn btn-outline-primary btn-sm" id="clear-filters" aria-label="Clear all filters and show all jobs">Show All</button>

        <button class="btn btn-outline-success btn-sm no-print" id="export-csv-btn" onclick="exportVisibleJobsToCSV()" aria-label="Export visible jobs to CSV file">Export CSV</button>

        <button class="btn btn-outline-secondary btn-sm" id="view-mode-toggle" type="button" aria-pressed="false" aria-label="Toggle compact report view">Compact View</button>

        <span id="filter-count" class="text-muted small ms-2" aria-hidden="true"></span>
      </div>
      <p class="text-muted small mt-2 mb-0">Filter applies to jobs with status set. Unset jobs are always visible.</p>
      <p class="text-muted small mt-1 mb-0">This report works offline after generation. Status edits stay in this browser until you export JSON and import it from the Applications tab.</p>
    </div>
    """


def html_shortlist_button(job_key_val: str, *, compact: bool = False) -> str:
    """Generate accessible review-state controls."""
    margin_class = " mt-1" if compact else ""
    escaped_key = html.escape(job_key_val)
    return (
        f'<span class="review-state-controls{margin_class}">'
        f'<button type="button" class="btn btn-sm btn-outline-warning shortlist-btn" '
        f'data-shortlist-key="{escaped_key}" data-review-state="shortlisted" '
        'aria-pressed="false" aria-label="Toggle shortlist for this job">Shortlist</button> '
        f'<button type="button" class="btn btn-sm btn-outline-secondary review-state-btn" '
        f'data-review-key="{escaped_key}" data-review-state="maybe_later" '
        'aria-pressed="false" aria-label="Mark this job as maybe later">Maybe Later</button> '
        f'<button type="button" class="btn btn-sm btn-outline-danger review-state-btn" '
        f'data-review-key="{escaped_key}" data-review-state="dismissed" '
        'aria-pressed="false" aria-label="Dismiss this job from review">Dismiss</button>'
        '</span>'
    )


def html_status_dropdown(*, extra_classes: str = "") -> str:
    """Generate the application status dropdown control."""
    class_suffix = f" {extra_classes.strip()}" if extra_classes.strip() else ""
    return f"""
      <div class="dropdown d-inline-block{class_suffix}">
        <button class="btn btn-sm btn-outline-secondary dropdown-toggle status-dropdown"
                type="button" data-bs-toggle="dropdown"
                aria-label="Change application status">
          Status
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
          <li><a class="dropdown-item" href="#" data-status="applied">Applied</a></li>
          <li><a class="dropdown-item" href="#" data-status="interviewing">Interviewing</a></li>
          <li><a class="dropdown-item" href="#" data-status="rejected">Rejected</a></li>
          <li><a class="dropdown-item" href="#" data-status="offer">Offer</a></li>
          <li><hr class="dropdown-divider"></li>
          <li><a class="dropdown-item" href="#" data-status="">Clear Status</a></li>
        </ul>
      </div>
    """
