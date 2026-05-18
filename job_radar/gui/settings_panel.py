"""Settings tab panel construction helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import os
from typing import Any

import customtkinter as ctk

from job_radar.gui.scoring_config import ScoringConfigWidget


@dataclass(frozen=True)
class MaintenancePanelWidgets:
    """Widgets MainWindow updates after maintenance actions."""

    cache_status_label: ctk.CTkLabel
    source_diagnostics_textbox: ctk.CTkTextbox


@dataclass(frozen=True)
class ApiSectionWidgets:
    """Widgets and references created for one API credential section."""

    api_fields: dict[str, tuple[ctk.CTkEntry, str]]
    status_labels: dict[str, ctk.CTkLabel]
    quota_labels: dict[str, ctk.CTkLabel]


@dataclass(frozen=True)
class UpdatePanelWidgets:
    """Widgets MainWindow updates for Settings update controls."""

    update_status_label: ctk.CTkLabel
    manual_check_button: ctk.CTkButton
    auto_check_var: ctk.BooleanVar
    release_notes_label: ctk.CTkButton
    skipped_status_label: ctk.CTkLabel
    clear_skipped_button: ctk.CTkButton


BACKEND_API_BY_FIELD_ID = {
    "jsearch": "jsearch",
    "usajobs": "usajobs",
    "adzuna_id": "adzuna",
    "authentic_jobs": "authentic_jobs",
    "serpapi": "serpapi",
}


API_CREDENTIAL_SECTIONS = (
    (
        "JSearch API (LinkedIn, Indeed, Glassdoor)",
        [("JSEARCH_API_KEY", "JSearch API Key", "jsearch")],
        "Get your key from RapidAPI: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch",
    ),
    (
        "USAJobs (Federal Government Jobs)",
        [
            ("USAJOBS_EMAIL", "Email (User-Agent)", "usajobs_email"),
            ("USAJOBS_API_KEY", "API Key", "usajobs"),
        ],
        "Register at: https://developer.usajobs.gov/",
    ),
    (
        "Adzuna API",
        [
            ("ADZUNA_APP_ID", "App ID", "adzuna_id"),
            ("ADZUNA_APP_KEY", "App Key", "adzuna_key"),
        ],
        "Sign up at: https://developer.adzuna.com/",
    ),
    (
        "Authentic Jobs",
        [("AUTHENTIC_JOBS_API_KEY", "API Key", "authentic_jobs")],
        "Get your key from: https://authenticjobs.com/api/",
    ),
    (
        "SerpAPI (Google Jobs)",
        [("SERPAPI_API_KEY", "API Key", "serpapi")],
        "Sign up at: https://serpapi.com/ (100 searches/month free)",
    ),
)


def add_api_credentials_panel(
    parent,
    *,
    on_add_api_section: Callable[[object, str, list[tuple[str, str, str]], str], None],
    on_save: Callable[[], None],
    show_jsearch_tip: bool,
):
    """Add API credential sections and return the Jobicy quota label."""
    ctk.CTkLabel(
        parent,
        text="API Key Settings",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(pady=(0, 10))

    ctk.CTkLabel(
        parent,
        text="Configure API keys to enable additional job sources",
        wraplength=600,
    ).pack(pady=(0, 20))

    for title, fields, signup_url in API_CREDENTIAL_SECTIONS:
        on_add_api_section(parent, title, fields, signup_url)

    jobicy_quota_label = add_jobicy_api_status(parent)

    if show_jsearch_tip:
        add_jsearch_setup_tip(parent)

    ctk.CTkButton(
        parent,
        text="Save API Keys",
        height=40,
        width=200,
        command=on_save,
    ).pack(pady=(20, 10))

    return jobicy_quota_label


def add_update_settings_panel(
    parent,
    *,
    update_status_text: str,
    update_status_color: str,
    auto_check_enabled: bool,
    update_available: bool,
    has_skipped_versions: bool,
    on_manual_check: Callable[[], None],
    on_auto_check_toggle: Callable[[], None],
    on_view_release_notes: Callable[[], None],
    on_clear_skipped: Callable[[], None],
) -> UpdatePanelWidgets:
    """Add Settings update controls and return mutable widget references."""
    ctk.CTkLabel(
        parent,
        text="Updates",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(pady=(0, 10), anchor="w", padx=10)

    update_status_label = ctk.CTkLabel(
        parent,
        text=update_status_text,
        text_color=update_status_color,
        font=ctk.CTkFont(size=12),
    )
    update_status_label.pack(pady=(0, 5), anchor="w", padx=10)

    manual_check_button = ctk.CTkButton(
        parent,
        text="Check for Updates",
        width=150,
        command=on_manual_check,
    )
    manual_check_button.pack(pady=(10, 10), anchor="w", padx=10)

    auto_check_var = ctk.BooleanVar(value=auto_check_enabled)
    ctk.CTkSwitch(
        parent,
        text="Check for updates automatically on launch",
        variable=auto_check_var,
        command=on_auto_check_toggle,
    ).pack(pady=(0, 10), anchor="w", padx=10)

    release_notes_label = ctk.CTkButton(
        parent,
        text="View release notes",
        fg_color="transparent",
        text_color=("#3498DB", "#5DADE2"),
        hover_color=("gray90", "gray20"),
        font=ctk.CTkFont(size=12, underline=True),
        anchor="w",
        width=150,
        height=25,
        cursor="hand2",
        command=on_view_release_notes,
    )
    if update_available:
        release_notes_label.pack(anchor="w", padx=10)

    skipped_status_label = ctk.CTkLabel(
        parent,
        text="",
        font=ctk.CTkFont(size=12),
        text_color="gray",
    )
    skipped_status_label.pack(anchor="w", padx=10)

    clear_skipped_button = ctk.CTkButton(
        parent,
        text="Clear skipped versions",
        width=180,
        fg_color="transparent",
        border_width=1,
        command=on_clear_skipped,
    )
    if has_skipped_versions:
        clear_skipped_button.pack(anchor="w", padx=10, pady=(5, 10))

    return UpdatePanelWidgets(
        update_status_label=update_status_label,
        manual_check_button=manual_check_button,
        auto_check_var=auto_check_var,
        release_notes_label=release_notes_label,
        skipped_status_label=skipped_status_label,
        clear_skipped_button=clear_skipped_button,
    )


def add_api_key_section(
    parent,
    title: str,
    fields: list[tuple[str, str, str]],
    signup_url: str,
    *,
    on_test: Callable[[list[tuple[str, str, str]]], None],
) -> ApiSectionWidgets:
    """Add an API configuration section with fields and test button."""
    section_frame = ctk.CTkFrame(parent, fg_color="transparent")
    section_frame.pack(fill="x", pady=(10, 20), padx=10)

    ctk.CTkLabel(
        section_frame,
        text=title,
        font=ctk.CTkFont(size=14, weight="bold"),
    ).pack(anchor="w", pady=(0, 5))

    ctk.CTkLabel(
        section_frame,
        text=signup_url,
        font=ctk.CTkFont(size=10),
        text_color="gray",
    ).pack(anchor="w", pady=(0, 10))

    api_fields: dict[str, tuple[ctk.CTkEntry, str]] = {}
    for env_var, label, field_id in fields:
        field_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        field_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            field_frame,
            text=f"{label}:",
            width=180,
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        entry = ctk.CTkEntry(
            field_frame,
            width=300,
            show="*" if _is_secret_field(env_var) else "",
        )
        entry.insert(0, os.getenv(env_var, ""))
        entry.pack(side="left", padx=(0, 10))
        api_fields[field_id] = (entry, env_var)

        if _is_secret_field(env_var):
            show_var = ctk.BooleanVar(value=False)

            def toggle_visibility(e=entry, v=show_var):
                e.configure(show="" if v.get() else "*")

            ctk.CTkButton(
                field_frame,
                text="Show",
                width=60,
                command=lambda v=show_var: (v.set(not v.get()), toggle_visibility()),
            ).pack(side="left")

    test_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
    test_frame.pack(fill="x", pady=(10, 0))

    ctk.CTkButton(
        test_frame,
        text="Test API Key",
        width=120,
        command=lambda: on_test(fields),
    ).pack(side="left", padx=(0, 10))

    status_label = ctk.CTkLabel(
        test_frame,
        text="",
        anchor="w",
    )
    status_label.pack(side="left")

    quota_label = ctk.CTkLabel(
        test_frame,
        text="",
        font=ctk.CTkFont(size=10),
        text_color="gray",
    )
    quota_label.pack(side="left", padx=(10, 0))

    first_field_id = fields[0][2]
    quota_labels = {}
    backend_api = BACKEND_API_BY_FIELD_ID.get(first_field_id)
    if backend_api:
        quota_labels[backend_api] = quota_label

    return ApiSectionWidgets(
        api_fields=api_fields,
        status_labels={first_field_id: status_label},
        quota_labels=quota_labels,
    )


def _is_secret_field(env_var: str) -> bool:
    return "KEY" in env_var or "PASSWORD" in env_var


def add_storage_maintenance_panel(
    parent,
    *,
    maintenance_text: str,
    feedback_diagnostics_text: str,
    source_diagnostics_text: str,
    on_clear_cache: Callable[[], None],
    on_clear_dismissed_reviews: Callable[[], None],
    on_export_app_data: Callable[[], None],
    on_validate_app_data_bundle: Callable[[], None],
    on_copy_feedback_diagnostics: Callable[[], None],
    on_refresh_source_diagnostics: Callable[[], None],
) -> MaintenancePanelWidgets:
    """Add storage and diagnostics controls to the settings tab."""
    ctk.CTkLabel(
        parent,
        text="Storage Maintenance",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(pady=(10, 10), anchor="w", padx=10)

    ctk.CTkLabel(
        parent,
        text="Cached job-board responses are temporary and can be cleared without removing your profile, reports, or application status.",
        wraplength=600,
        justify="left",
        text_color="gray",
    ).pack(pady=(0, 10), anchor="w", padx=10)

    maintenance_box = ctk.CTkTextbox(
        parent,
        width=620,
        height=120,
        state="normal",
    )
    maintenance_box.insert("end", maintenance_text)
    maintenance_box.configure(state="disabled")
    maintenance_box.pack(pady=(0, 10), anchor="w", padx=10)

    ctk.CTkButton(
        parent,
        text="Clear HTTP Cache",
        width=180,
        fg_color="transparent",
        border_width=1,
        command=on_clear_cache,
    ).pack(pady=(0, 5), anchor="w", padx=10)

    ctk.CTkButton(
        parent,
        text="Clear Dismissed Reviews",
        width=210,
        fg_color="transparent",
        border_width=1,
        command=on_clear_dismissed_reviews,
    ).pack(pady=(0, 5), anchor="w", padx=10)

    ctk.CTkButton(
        parent,
        text="Export App Data",
        width=180,
        fg_color="transparent",
        border_width=1,
        command=on_export_app_data,
    ).pack(pady=(0, 5), anchor="w", padx=10)

    ctk.CTkButton(
        parent,
        text="Validate App Data Bundle",
        width=220,
        fg_color="transparent",
        border_width=1,
        command=on_validate_app_data_bundle,
    ).pack(pady=(0, 5), anchor="w", padx=10)

    cache_status_label = ctk.CTkLabel(
        parent,
        text="",
        font=ctk.CTkFont(size=12),
        text_color="gray",
    )
    cache_status_label.pack(pady=(0, 10), anchor="w", padx=10)

    ctk.CTkLabel(
        parent,
        text="Feedback Diagnostics",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(pady=(10, 8), anchor="w", padx=10)

    feedback_box = ctk.CTkTextbox(
        parent,
        width=620,
        height=150,
        state="normal",
    )
    feedback_box.insert("end", feedback_diagnostics_text)
    feedback_box.configure(state="disabled")
    feedback_box.pack(pady=(0, 10), anchor="w", padx=10)

    ctk.CTkButton(
        parent,
        text="Copy Feedback Diagnostics",
        width=230,
        fg_color="transparent",
        border_width=1,
        command=on_copy_feedback_diagnostics,
    ).pack(pady=(0, 10), anchor="w", padx=10)

    ctk.CTkLabel(
        parent,
        text="Performance Diagnostics",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(pady=(10, 8), anchor="w", padx=10)

    source_diagnostics_textbox = ctk.CTkTextbox(
        parent,
        width=620,
        height=130,
        state="normal",
    )
    source_diagnostics_textbox.insert("end", source_diagnostics_text)
    source_diagnostics_textbox.configure(state="disabled")
    source_diagnostics_textbox.pack(pady=(0, 8), anchor="w", padx=10)

    ctk.CTkButton(
        parent,
        text="Refresh Diagnostics",
        width=180,
        fg_color="transparent",
        border_width=1,
        command=on_refresh_source_diagnostics,
    ).pack(pady=(0, 10), anchor="w", padx=10)

    return MaintenancePanelWidgets(
        cache_status_label=cache_status_label,
        source_diagnostics_textbox=source_diagnostics_textbox,
    )


def add_jobicy_api_status(parent):
    """Add the Jobicy public API status section and return its quota label."""
    jobicy_frame = ctk.CTkFrame(parent, fg_color="transparent")
    jobicy_frame.pack(fill="x", pady=(10, 20), padx=10)

    ctk.CTkLabel(
        jobicy_frame,
        text="Jobicy (Remote Jobs)",
        font=ctk.CTkFont(size=14, weight="bold"),
    ).pack(anchor="w", pady=(0, 5))

    ctk.CTkLabel(
        jobicy_frame,
        text="Public API - no key required (rate limited to 1 request/hour)",
        font=ctk.CTkFont(size=10),
        text_color="gray",
    ).pack(anchor="w", pady=(0, 5))

    ctk.CTkLabel(
        jobicy_frame,
        text="✓ Always available",
        text_color="green",
    ).pack(anchor="w")

    quota_label = ctk.CTkLabel(
        jobicy_frame,
        text="",
        font=ctk.CTkFont(size=10),
        text_color="gray",
    )
    quota_label.pack(anchor="w", pady=(5, 0))
    return quota_label


def add_jsearch_setup_tip(parent) -> None:
    """Add the JSearch setup tip shown when no API key is configured."""
    tip_frame = ctk.CTkFrame(
        parent,
        fg_color="transparent",
        border_width=2,
        border_color="#5DADE2",
    )
    tip_frame.pack(fill="x", pady=(20, 10), padx=10)

    ctk.CTkLabel(
        tip_frame,
        text="💡 Tip: Set up JSearch API key to search LinkedIn, Indeed, and Glassdoor",
        font=ctk.CTkFont(size=12),
        text_color="#5DADE2",
        wraplength=600,
    ).pack(pady=10, padx=10)


def add_danger_zone(parent, *, on_uninstall: Callable[[], None]) -> None:
    """Add destructive settings actions."""
    danger_section = ctk.CTkFrame(parent, fg_color="transparent")
    danger_section.pack(fill="x", pady=(10, 20), padx=10)

    ctk.CTkLabel(
        danger_section,
        text="Danger Zone",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="red",
    ).pack(anchor="w", pady=(0, 5))

    ctk.CTkLabel(
        danger_section,
        text="Remove Job Radar and all associated data from your system",
        font=ctk.CTkFont(size=12),
        text_color="gray",
    ).pack(anchor="w", pady=(0, 10))

    ctk.CTkButton(
        danger_section,
        text="Uninstall Job Radar",
        height=40,
        width=200,
        fg_color="red",
        hover_color="darkred",
        command=on_uninstall,
    ).pack(anchor="w", pady=(10, 0))


def add_scoring_config_panel(
    parent,
    *,
    profile: dict[str, Any] | None,
    on_save: Callable[[], None],
) -> ScoringConfigWidget:
    """Add the scoring configuration widget and return it."""
    scoring_config = ScoringConfigWidget(
        parent,
        profile=profile,
        on_save_callback=on_save,
    )
    scoring_config.pack(fill="x", padx=10, pady=(10, 20))
    return scoring_config
