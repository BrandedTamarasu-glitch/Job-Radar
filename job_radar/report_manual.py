"""Manual-check URL rendering for generated reports."""

from __future__ import annotations

import html

from .report_safety import safe_external_url


def html_manual_urls_section(manual_urls: list[dict]) -> str:
    """Generate HTML for manual check URLs section."""
    if not manual_urls:
        return ""

    groups = {}
    for manual_url in manual_urls:
        source = manual_url["source"]
        if source not in groups:
            groups[source] = []
        groups[source].append(manual_url)

    sections = []
    for source, urls in groups.items():
        links = []
        for manual_url in urls:
            safe_url = safe_external_url(manual_url.get("url"))
            title = html.escape(manual_url["title"])
            source_name = html.escape(manual_url["source"])
            if safe_url:
                links.append(
                    f'<li>{title}: <a href="{html.escape(safe_url)}" '
                    f'target="_blank" rel="noopener" '
                    f'aria-label="{title} on {source_name}, opens in new tab">'
                    f'{source_name} Search</a></li>'
                )
            else:
                links.append(f"<li>{title}: {source_name} Search URL unavailable</li>")
        links_html = "".join(links)
        sections.append(f"""
        <div class="mb-3">
          <h4 class="h6"><strong>{html.escape(source)}:</strong></h4>
          <ul>
            {links_html}
          </ul>
        </div>
        """)

    sections_html = "".join(sections)
    return f"""
    <section aria-labelledby="manual-heading">
      <div class="card mb-4">
        <div class="card-header">
          <h2 id="manual-heading" class="h4 mb-0">Manual Check URLs</h2>
        </div>
        <div class="card-body">
          <p class="text-muted"><em>Open these in your browser to check sources that block automated access.</em></p>
          {sections_html}
        </div>
      </div>
    </section>
    """
