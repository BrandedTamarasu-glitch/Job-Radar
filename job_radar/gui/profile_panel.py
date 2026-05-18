"""Profile tab panel construction helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import customtkinter as ctk

from job_radar.gui.profile_view_model import ProfileReadinessDisplay, ProfileSummaryRow


def add_profile_field(parent, row: int, label_text: str, value_text: str) -> None:
    """Add a label-value pair to the profile grid."""
    label = ctk.CTkLabel(
        parent,
        text=label_text,
        font=ctk.CTkFont(weight="bold"),
        anchor="w",
    )
    label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)

    value = ctk.CTkLabel(
        parent,
        text=value_text,
        anchor="w",
    )
    value.grid(row=row, column=1, sticky="w", pady=5)


def add_profile_summary_panel(
    parent,
    row: int,
    *,
    profile: dict[str, Any],
    readiness_display: ProfileReadinessDisplay,
    summary_rows: Sequence[ProfileSummaryRow],
    on_edit: Callable[[dict[str, Any]], None],
) -> int:
    """Render profile readiness, summary rows, and edit action."""
    add_profile_field(parent, row, "Profile Readiness:", readiness_display.summary)
    row += 1

    if readiness_display.guidance_text:
        ctk.CTkLabel(
            parent,
            text=readiness_display.guidance_text,
            text_color="gray",
            wraplength=680,
            justify="left",
            anchor="w",
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        row += 1

    if readiness_display.scoring_signals_text:
        add_profile_field(
            parent,
            row,
            "Scoring Signals:",
            readiness_display.scoring_signals_text,
        )
        row += 1

    for summary_row in summary_rows:
        add_profile_field(parent, row, summary_row.label, summary_row.value)
        row += 1

    ctk.CTkButton(
        parent,
        text="Edit Profile",
        height=40,
        width=150,
        command=lambda: on_edit(profile),
    ).grid(row=row, column=0, columnspan=2, pady=(20, 0))

    return row + 1
