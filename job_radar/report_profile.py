"""Profile summary rendering for generated reports."""

from __future__ import annotations

import html


def html_profile_section(profile: dict) -> str:
    """Generate HTML for candidate profile summary."""
    level = html.escape(profile.get("level", "N/A"))
    years = profile.get("years_experience", "N/A")
    target_titles = html.escape(", ".join(profile.get("target_titles", []))) or "N/A"
    core_skills = html.escape(", ".join(profile.get("core_skills", []))) or "N/A"
    location = html.escape(profile.get("location", "N/A"))
    arrangement = html.escape(", ".join(profile.get("arrangement", []))) or "N/A"
    target_market = html.escape(profile.get("target_market", "N/A"))

    cert_row = ""
    if profile.get("certifications"):
        certs = html.escape(", ".join(profile["certifications"]))
        cert_row = f"<li><strong>Certifications:</strong> {certs}</li>"

    comp_row = ""
    if profile.get("comp_floor"):
        comp_floor = profile["comp_floor"]
        comp_row = f"<li><strong>Comp floor:</strong> ${comp_floor:,.0f}</li>"

    dealbreaker_row = ""
    if profile.get("dealbreakers"):
        dealbreakers = html.escape(", ".join(profile["dealbreakers"]))
        dealbreaker_row = f"<li><strong>Dealbreakers:</strong> {dealbreakers}</li>"

    return f"""
    <section aria-labelledby="profile-heading">
      <div class="card mb-4">
        <div class="card-header">
          <h2 id="profile-heading" class="h4 mb-0">Candidate Profile Summary</h2>
        </div>
        <div class="card-body">
          <ul class="list-unstyled mb-0">
            <li><strong>Level:</strong> {level}</li>
            <li><strong>Experience:</strong> {years} years</li>
            <li><strong>Target titles:</strong> {target_titles}</li>
            <li><strong>Core skills:</strong> {core_skills}</li>
            <li><strong>Location:</strong> {location}</li>
            <li><strong>Arrangement:</strong> {arrangement}</li>
            <li><strong>Target market:</strong> {target_market}</li>
            {cert_row}
            {comp_row}
            {dealbreaker_row}
          </ul>
        </div>
      </div>
    </section>
    """
