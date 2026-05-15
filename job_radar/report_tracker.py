"""Tracker summary rendering for generated reports."""

from __future__ import annotations


def html_tracker_stats(tracker_stats: dict) -> str:
    """Generate HTML for tracker statistics."""
    return f"""
    <div class="alert alert-secondary">
      <strong>Lifetime stats:</strong> {tracker_stats['total_unique_jobs_seen']} unique jobs seen
      across {tracker_stats['total_runs']} runs |
      Avg {tracker_stats['avg_new_per_run_last_7']} new/run (last 7)
    </div>
    """
