"""Settings tab panel construction helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import customtkinter as ctk


@dataclass(frozen=True)
class MaintenancePanelWidgets:
    """Widgets MainWindow updates after maintenance actions."""

    cache_status_label: ctk.CTkLabel
    source_diagnostics_textbox: ctk.CTkTextbox


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
