# Phase 41: Auto-Update Polish - Research

**Researched:** 2026-02-16
**Domain:** Update UX enhancements, GitHub API integration, markdown rendering
**Confidence:** HIGH

## Summary

Phase 41 builds two polish features on the existing update system (Phases 38-40): "Skip This Version" to permanently dismiss specific versions, and a "What's new?" changelog preview from GitHub Releases. The existing infrastructure already handles version tracking, API calls, and config persistence atomically. This phase extends the `suppressed_versions` pattern (time-based dismissal) to support permanent skips, adds GitHub release notes fetching to the existing `fetch_release_assets` pattern, and implements basic markdown display in CustomTkinter dialogs.

**Primary recommendation:** Use existing update_state config structure for skipped versions list (no expiry timestamp = permanent skip), fetch release notes body from GitHub Releases API alongside asset fetching, implement dropdown menu with CTkOptionMenu or "..." button pattern, and use CTkTextbox with basic regex-based markdown stripping for changelog display (no external markdown library needed).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Skip Version behavior:**
- "Skip This Version" button lives in a dropdown/menu (not alongside main banner buttons) — keeps banner clean since skipping is less common
- After skipping: brief "v{version} skipped" confirmation message, then banner dismisses
- If the only available version is skipped: no banner on launch, but Settings tab shows "v{version} available (skipped)" status
- Skip is only available in the notification state — once download starts, Skip is no longer offered (user committed)

**Changelog presentation:**
- Release notes displayed in a separate dialog (not inline in banner) — more room for content
- Show summary only: first paragraph or first ~5 bullet points, with link to full notes on GitHub
- Basic formatting: bold headings, bullet points — no images or complex markdown
- Empty release notes: show "No release notes available for this version. View on GitHub →"

**"What's new?" trigger:**
- Version number in the banner is clickable — clicking opens the changelog dialog (no separate "What's new?" button)
- On demand only — user clicks to see notes, banner stays clean by default
- Dialog is view-only: shows notes + Close button. User goes back to banner to download.
- Settings Updates section also shows "View release notes" link when update is available

**Persistence & state:**
- No limit on skipped versions — list grows unbounded
- Manual check in Settings: shows skipped version but marked as "(skipped)" — user knows they chose to skip
- "Clear skipped versions" button in Settings to un-skip all
- Release notes cached with update state (stored alongside version info) — one fetch per version, avoids re-fetching

### Claude's Discretion

- Dropdown/menu implementation (CTk option menu, right-click context, or "..." button)
- Exact summary extraction logic (first paragraph vs first N bullets)
- Basic markdown rendering approach in CustomTkinter
- "Skipped" confirmation message timing and animation
- How to style the clickable version number to look like a link
- Release notes cache expiry/invalidation strategy

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.32+ | GitHub API calls | Already used in update_checker.py for releases API |
| packaging.version | Stdlib | Version comparison | Already used for semantic versioning in update_checker.py |
| customtkinter | 5.2+ | GUI dialogs, widgets | Project's GUI framework, used for all UI components |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re | Stdlib | Markdown stripping | Extract first paragraph/bullets from release body text |
| webbrowser | Stdlib | Open GitHub URLs | Used in update_banner.py for manual download links |
| json | Stdlib | Config persistence | Already used for update_state in config.json |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Regex markdown stripping | mistune (markdown parser) | mistune v3.2.0 has no dependencies and excellent performance, but adds ~30KB for rendering we don't need. Regex sufficient for "first N bullets" extraction. |
| CTkOptionMenu dropdown | Right-click context menu | Context menus require tkinter.Menu (not CustomTkinter styled), less discoverable for users. CTkOptionMenu or "..." button is cleaner. |
| Clickable CTkLabel | CTkButton with fg_color=transparent | Button gives proper hover/cursor feedback, better accessibility than label .bind() approach |

**Installation:**
No new dependencies needed — all features use existing libraries.

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── update_checker.py        # Add skip_version(), fetch_release_notes(), clear_skipped_versions()
├── gui/
│   ├── update_banner.py     # Add dropdown widget, clickable version label
│   └── changelog_dialog.py  # NEW: CTkToplevel for release notes display
```

### Pattern 1: Extend suppressed_versions for Permanent Skips
**What:** The existing `suppressed_versions` dict maps version → expiry timestamp for dismissal. Permanent skips store `None` or sentinel value instead of timestamp.
**When to use:** Distinguishes between temporary dismissal (24h, 7d) and permanent skip.
**Example:**
```python
# From existing dismiss_version pattern in update_checker.py
suppressed_versions = {
    "2.1.0": "2026-02-15T10:30:00+00:00",  # Dismissed until date
    "2.2.0": None  # Skipped permanently (sentinel)
}

def skip_version(self, version: str) -> None:
    """Permanently skip a version (no expiry)."""
    config = self._load_config()
    update_state = config.setdefault("update_state", {})
    suppressed = update_state.setdefault("suppressed_versions", {})
    suppressed[version] = None  # None = permanent skip
    self._save_config(config)

def should_show_banner(self, version: str) -> bool:
    """Check if banner should show (modified to handle None expiry)."""
    state = self._get_update_state()
    suppressed = state.get("suppressed_versions", {})

    if version not in suppressed:
        return True

    expiry = suppressed[version]
    if expiry is None:  # Permanent skip
        return False

    # Time-based check for dismissals (existing logic)
    try:
        expiry_dt = datetime.fromisoformat(expiry)
        return datetime.now(timezone.utc) >= expiry_dt
    except (ValueError, TypeError):
        return True
```

### Pattern 2: GitHub Releases API Body Field
**What:** GitHub Releases API returns `body` field with markdown-formatted release notes. Fetch alongside assets.
**When to use:** When version is newer, fetch both installer assets and release notes.
**Example:**
```python
# Source: https://docs.github.com/en/rest/releases/releases
# API response structure:
{
  "tag_name": "v2.2.0",
  "name": "Version 2.2.0",
  "body": "## What's New\n\n- Feature A\n- Feature B\n\n...",
  "html_url": "https://github.com/.../releases/v2.2.0",
  "assets": [...],
  "published_at": "2026-02-15T10:00:00Z"
}

# Add to UpdateChecker class:
def fetch_release_notes(self, tag: str) -> str:
    """Fetch release notes body from GitHub for a specific tag.

    Returns markdown string or empty string on error.
    """
    url = GITHUB_RELEASES_TAG_URL.format(tag=tag)
    try:
        response = requests.get(
            url,
            headers={"User-Agent": f"Job-Radar/{__version__}"},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return data.get("body", "")
    except requests.RequestException as e:
        log.error("Failed to fetch release notes for %s: %s", tag, e)
        return ""
```

### Pattern 3: CTkOptionMenu for Dropdown
**What:** CTkOptionMenu provides styled dropdown menu for "Skip This Version" alongside Download/Remind buttons.
**When to use:** When multiple actions available but one is less common (skip is rarer than download).
**Example:**
```python
# Source: https://github.com/TomSchimansky/CustomTkinter/wiki/CTkOptionMenu
# In UpdateBanner._create_notification_widgets():

# Instead of direct "Skip" button, use "..." menu button:
self.actions_menu = ctk.CTkOptionMenu(
    self,
    values=["Skip This Version"],
    command=self._on_menu_action,
    width=40,
    fg_color="transparent",
    button_color="white",
    button_hover_color="#E0E0E0"
)
# Position after Remind Later button

def _on_menu_action(self, choice: str):
    if choice == "Skip This Version":
        self._on_skip_click()
```

**Alternative: "..." Button with Dropdown:**
```python
# More discoverable, follows VS Code pattern:
self.more_btn = ctk.CTkButton(
    self,
    text="⋯",  # Three dots
    width=30,
    command=self._show_skip_menu
)

def _show_skip_menu(self):
    # Show CTkOptionMenu programmatically or custom popup
    pass
```

### Pattern 4: Clickable Label for Version Number
**What:** Make version text in banner clickable to open changelog dialog.
**When to use:** Subtle interaction point that doesn't clutter UI.
**Example:**
```python
# In UpdateBanner.__init__():
self.version_label = ctk.CTkButton(
    self,
    text=f"v{self.version}",
    fg_color="transparent",
    hover_color=("#D0E8F5", "#1A5276"),  # Slight hover tint
    text_color="white",
    font=CTkFont(size=13, underline=True),  # Underline like hyperlink
    width=60,
    command=self._on_version_click,
    cursor="hand2"  # Pointer cursor
)

# Update message layout:
# "Version" [clickable v2.2.0] "available"
```

### Pattern 5: CTkTextbox for Changelog Display
**What:** CTkTextbox in disabled state for read-only markdown display with basic formatting.
**When to use:** Showing multi-line formatted text (release notes) in dialog.
**Example:**
```python
# Source: https://github.com/TomSchimansky/CustomTkinter/wiki/CTkTextbox
class ChangelogDialog(ctk.CTkToplevel):
    def __init__(self, parent, version: str, release_notes: str, github_url: str):
        super().__init__(parent)
        self.title(f"What's New in v{version}")
        self.geometry("500x400")

        # Textbox for notes
        self.textbox = ctk.CTkTextbox(self, height=300, width=460)
        self.textbox.pack(pady=(20, 10), padx=20)

        # Insert formatted notes
        summary = self._extract_summary(release_notes)
        self.textbox.insert("1.0", summary)

        # Set read-only
        self.textbox.configure(state="disabled")

        # View full notes link button
        link_btn = ctk.CTkButton(
            self, text="View Full Release Notes on GitHub",
            command=lambda: webbrowser.open(github_url)
        )
        link_btn.pack(pady=(0, 10))

        # Close button
        close_btn = ctk.CTkButton(self, text="Close", command=self.destroy)
        close_btn.pack(pady=(0, 20))

    def _extract_summary(self, markdown: str) -> str:
        """Extract first paragraph or first 5 bullet points from markdown."""
        if not markdown.strip():
            return "No release notes available for this version."

        # Split into paragraphs
        paragraphs = markdown.split("\n\n")

        # Find first paragraph or list
        for para in paragraphs:
            # If it's a list, extract up to 5 bullets
            if para.strip().startswith(("-", "*", "+")):
                bullets = [line for line in para.split("\n")
                          if line.strip().startswith(("-", "*", "+"))]
                return "\n".join(bullets[:5])
            # If it's text (not heading), return first paragraph
            elif not para.strip().startswith("#"):
                return para.strip()

        # Fallback: return first 300 chars
        return markdown[:300] + "..." if len(markdown) > 300 else markdown
```

### Pattern 6: Release Notes Caching in update_state
**What:** Store fetched release notes in update_state alongside version info to avoid re-fetching.
**When to use:** After fetching notes from GitHub, cache for future banner displays.
**Example:**
```python
# Add to UpdateChecker._update_state:
update_state = {
    "last_check": "2026-02-16T10:00:00+00:00",
    "check_success": True,
    "suppressed_versions": {...},
    "release_notes_cache": {
        "2.2.0": {
            "body": "## What's New\n\n- Feature A\n...",
            "fetched_at": "2026-02-16T10:00:00+00:00"
        }
    }
}

def get_cached_release_notes(self, version: str) -> str | None:
    """Get cached release notes for version, or None if not cached."""
    state = self._get_update_state()
    cache = state.get("release_notes_cache", {})
    version_cache = cache.get(version)

    if version_cache:
        # Optional: validate cache age (e.g., 7 days)
        return version_cache.get("body")
    return None

def cache_release_notes(self, version: str, body: str) -> None:
    """Cache release notes for version."""
    config = self._load_config()
    update_state = config.setdefault("update_state", {})
    cache = update_state.setdefault("release_notes_cache", {})
    cache[version] = {
        "body": body,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }
    self._save_config(config)
```

### Anti-Patterns to Avoid
- **Fetching release notes on every banner display:** GitHub API has rate limits. Fetch once when version detected, cache in update_state.
- **Complex markdown parsing for "basic formatting":** User decision specifies "bold headings, bullet points" only. Don't add full markdown library for this. Regex or simple string processing sufficient.
- **Blocking UI thread for GitHub API calls:** Release notes fetch should be async (use worker thread pattern from existing download flow).
- **Allowing skip after download starts:** User constraint says skip only available in notification state. Once progress state active, skip option hidden.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Semantic version comparison | Custom string parsing | packaging.version.Version (already in use) | Handles pre-releases, build metadata, PEP 440 edge cases |
| Config file atomic writes | Direct json.dump() | tempfile + rename pattern (already in use) | Prevents corruption on crash/power loss, already implemented in UpdateChecker._save_config() |
| Markdown rendering to HTML | Regex replacements for every element | Skip: show plain text with minimal formatting | User decision: "basic formatting" only. Don't need full renderer. |
| Modal dialog centering | Manual geometry calculations | Follow existing pattern in installer_dialogs.py | Already solved with _center_on_parent() method |

**Key insight:** The existing update_checker.py already solves all the hard problems (atomic config, GitHub API, version comparison, per-version tracking). This phase extends existing patterns rather than building new infrastructure.

## Common Pitfalls

### Pitfall 1: GitHub API Rate Limits
**What goes wrong:** Fetching release notes on every manual check or banner display hits rate limits.
**Why it happens:** GitHub API allows 60 requests/hour for unauthenticated requests.
**How to avoid:**
- Fetch release notes only once when new version detected
- Cache in update_state.release_notes_cache
- Don't re-fetch if cache exists for that version
**Warning signs:** HTTP 403 responses with "rate limit exceeded" message

### Pitfall 2: CTkTextbox Disabled State Rendering
**What goes wrong:** Setting textbox to "disabled" may make text invisible or hard to read.
**Why it happens:** Disabled state in CustomTkinter changes text color to gray/faded.
**How to avoid:** Test read-only display with `state="disabled"` in both light/dark modes. If text unreadable, use alternative approach (keep state="normal" but unbind editing keys).
**Warning signs:** User reports in GitHub issues mention textbox not showing anything when disabled.

### Pitfall 3: Clickable Label vs Button for Version
**What goes wrong:** Using CTkLabel with .bind("<Button-1>", ...) doesn't provide hover feedback or cursor change.
**Why it happens:** CTkLabel is display-only widget, doesn't have interactive states.
**How to avoid:** Use CTkButton with fg_color="transparent" and underline font for hyperlink appearance. Provides hover, focus, accessibility.
**Warning signs:** Version text looks clickable but doesn't show pointer cursor or hover state.

### Pitfall 4: Skipped Version Still Shows in Settings
**What goes wrong:** User skips v2.2.0, but Settings tab doesn't indicate it's skipped.
**Why it happens:** Settings status display checks for suppressed_versions but doesn't distinguish skip (None) from dismissal (timestamp).
**How to avoid:** Modify _refresh_update_status() to check if expiry is None and display "(skipped)" label.
**Warning signs:** User confused why banner doesn't show but Settings says update available.

### Pitfall 5: Release Notes Cache Grows Unbounded
**What goes wrong:** release_notes_cache accumulates entries for every version ever released.
**Why it happens:** No cache eviction policy.
**How to avoid:** User constraint says "no limit on skipped versions" but doesn't mention cache. Options:
- Keep only last 3 versions in cache
- Evict cache entries older than 30 days
- Don't implement cache eviction (notes are typically <10KB, few versions cached)
**Warning signs:** config.json file grows beyond 100KB over time.

## Code Examples

Verified patterns from official sources:

### GitHub Releases API - Fetch Release Body
```python
# Source: https://docs.github.com/en/rest/releases/releases
# GET /repos/{owner}/{repo}/releases/tags/{tag}

def fetch_release_notes(self, tag: str) -> str:
    """Fetch release notes body from GitHub.

    Args:
        tag: Release tag (e.g., "v2.2.0")

    Returns:
        Markdown string of release body, or empty string on error
    """
    url = f"https://api.github.com/repos/BrandedTamarasu-glitch/Job-Radar/releases/tags/{tag}"

    try:
        response = requests.get(
            url,
            headers={"User-Agent": f"Job-Radar/{__version__}"},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        return data.get("body", "")

    except requests.RequestException as e:
        log.error("Failed to fetch release notes for tag %s: %s", tag, e)
        return ""
```

### CTkOptionMenu for Skip Dropdown
```python
# Source: https://github.com/TomSchimansky/CustomTkinter/wiki/CTkOptionMenu
# Create dropdown menu in UpdateBanner

self.actions_menu_var = ctk.StringVar(value="...")
self.actions_menu = ctk.CTkOptionMenu(
    self,
    values=["Skip This Version"],
    command=self._on_action_selected,
    variable=self.actions_menu_var,
    width=40,
    fg_color="transparent",
    button_color="white",
    button_hover_color=("#E0E0E0", "#404040")
)
self.actions_menu.grid(row=0, column=4, padx=(0, 10), pady=10)

def _on_action_selected(self, choice: str):
    if choice == "Skip This Version":
        # Call skip callback
        self.on_skip(self.version)
        # Reset dropdown to "..."
        self.actions_menu_var.set("...")
```

### Clickable Version Label Pattern
```python
# Use CTkButton styled as hyperlink
self.version_btn = ctk.CTkButton(
    self,
    text=f"v{self.version}",
    fg_color="transparent",
    hover_color=("#D6EAF8", "#1A4D6B"),  # Slight blue tint on hover
    text_color="white",
    font=CTkFont(size=13, underline=True),
    width=60,
    height=20,
    command=self._on_version_click,
    cursor="hand2"  # Pointer cursor
)

def _on_version_click(self):
    """Open changelog dialog when version clicked."""
    # Callback set by MainWindow to show ChangelogDialog
    if self.on_view_changelog:
        self.on_view_changelog(self.version)
```

### Extract First Paragraph/Bullets from Markdown
```python
# Regex-based extraction (no external library)
import re

def extract_summary(markdown: str, max_bullets: int = 5) -> str:
    """Extract first paragraph or first N bullet points from markdown.

    Args:
        markdown: Raw markdown string
        max_bullets: Maximum bullet points to include

    Returns:
        Formatted summary text
    """
    if not markdown.strip():
        return "No release notes available for this version."

    # Split into sections by double newline
    sections = markdown.split("\n\n")

    for section in sections:
        section = section.strip()

        # Skip headings
        if section.startswith("#"):
            continue

        # Check if section contains bullets
        bullet_pattern = r"^\s*[-*+]\s+(.+)$"
        bullets = re.findall(bullet_pattern, section, re.MULTILINE)

        if bullets:
            # Return first N bullets
            summary_bullets = bullets[:max_bullets]
            return "\n".join(f"• {b}" for b in summary_bullets)

        # Otherwise, return first text paragraph
        if section and not section.startswith("|"):  # Skip tables
            # Truncate if too long
            if len(section) > 400:
                return section[:400] + "..."
            return section

    # Fallback: return first 300 chars
    return markdown[:300] + "..." if len(markdown) > 300 else markdown
```

### Settings UI - Display Skipped Status
```python
# Modify _refresh_update_status() in main_window.py
def _refresh_update_status(self):
    """Refresh update status label to show skipped versions."""
    state = self._update_checker._get_update_state()
    suppressed = state.get("suppressed_versions", {})

    # Check for skipped versions (expiry = None)
    skipped = [v for v, expiry in suppressed.items() if expiry is None]

    status_text = "..."  # Existing logic

    if skipped:
        # Show skipped versions
        skipped_str = ", ".join(f"v{v}" for v in skipped)
        status_text += f" ({skipped_str} skipped)"

    self._update_status_label.configure(text=status_text)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single "Don't show again" flag | Per-version suppress tracking | Phase 38 (v2.2.0) | New version notifications show even if old dismissed |
| Blocking HTTP calls in main thread | Queue-based async with worker threads | Phase 38 (v2.2.0) | UI stays responsive during update checks |
| Inline release notes in banner | Separate dialog on-demand | Phase 41 (this phase) | Banner stays clean, power users discover changelog |
| Manual config.json writes | Atomic temp-file-rename pattern | Phase 38 (v2.2.0) | Prevents corruption on crash |

**Deprecated/outdated:**
- Using mistune/markdown library for simple text extraction: Overkill for "first paragraph" use case. Regex sufficient and avoids dependency.
- Right-click context menus in CustomTkinter: Not well-supported, requires tkinter.Menu (not styled). CTkOptionMenu is native solution.

## Open Questions

1. **Should release notes cache have expiry?**
   - What we know: User constraint says "one fetch per version, avoids re-fetching"
   - What's unclear: If release notes change after publish (rare but possible with edited releases)
   - Recommendation: No expiry for v1. Notes rarely change post-publish. If needed later, add 7-day expiry with re-fetch option.

2. **Confirmation message timing after skip?**
   - What we know: User constraint says "brief 'v{version} skipped' message, then banner dismisses"
   - What's unclear: How long "brief" is (1 second? 2 seconds?)
   - Recommendation: 1.5 seconds, similar to "Copied!" feedback in installer_dialogs.py (_copy_to_clipboard method uses 2 seconds)

3. **Should "Clear skipped versions" require confirmation?**
   - What we know: User constraint mentions button in Settings
   - What's unclear: Should it be destructive action with confirmation dialog?
   - Recommendation: No confirmation. Skipping is reversible, and clearing is intentional action in Settings. If user regrets, they can skip again on next launch.

## Sources

### Primary (HIGH confidence)
- GitHub REST API Documentation - Releases endpoints: [https://docs.github.com/en/rest/releases/releases](https://docs.github.com/en/rest/releases/releases)
- CustomTkinter Wiki - CTkOptionMenu: [https://github.com/TomSchimansky/CustomTkinter/wiki/CTkOptionMenu](https://github.com/TomSchimansky/CustomTkinter/wiki/CTkOptionMenu)
- CustomTkinter Wiki - CTkTextbox: [https://github.com/TomSchimansky/CustomTkinter/wiki/CTkTextbox](https://github.com/TomSchimansky/CustomTkinter/wiki/CTkTextbox)
- Existing codebase patterns: job_radar/update_checker.py, job_radar/gui/update_banner.py, job_radar/gui/installer_dialogs.py

### Secondary (MEDIUM confidence)
- Mistune performance benchmarks: [https://github.com/lepture/mistune](https://github.com/lepture/mistune) - Fast markdown parser but not needed for this phase
- CustomTkinter popup menu patterns: [https://www.akascape.com/coding/how-to-make-a-popup-menu-in-customtkinter](https://www.akascape.com/coding/how-to-make-a-popup-menu-in-customtkinter)
- Tkinter clickable label patterns: [https://www.tutorialspoint.com/how-do-you-create-a-clickable-tkinter-label](https://www.tutorialspoint.com/how-do-you-create-a-clickable-tkinter-label)

### Tertiary (LOW confidence)
- Python regex for markdown extraction - general patterns from community examples (need validation in implementation)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use (requests, packaging, customtkinter, stdlib)
- Architecture: HIGH - Extends proven patterns from Phases 38-40 (suppress tracking, GitHub API, atomic config)
- Pitfalls: MEDIUM - CTkTextbox disabled state issue reported in GitHub but not tested in Job Radar codebase yet

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (30 days - stable domain, GitHub API stable)
