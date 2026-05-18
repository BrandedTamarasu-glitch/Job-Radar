"""Search tab panel construction helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import customtkinter as ctk

from job_radar.profile_readiness import ProfileReadiness
from job_radar.saved_searches import SearchPanelRow


def add_search_readiness_guidance(
    parent,
    readiness: ProfileReadiness,
    guidance_lines: Sequence[str],
    *,
    on_review_profile: Callable[[], None],
) -> None:
    """Add profile quality guidance above the search action."""
    guidance_frame = ctk.CTkFrame(parent)
    guidance_frame.pack(fill="x", pady=(0, 16))
    guidance_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        guidance_frame,
        text=f"Profile readiness: {readiness.status} ({readiness.score}/{readiness.max_score})",
        font=ctk.CTkFont(size=13, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

    ctk.CTkLabel(
        guidance_frame,
        text="\n".join(f"- {line}" for line in guidance_lines),
        font=ctk.CTkFont(size=12),
        text_color="gray",
        wraplength=520,
        justify="left",
        anchor="w",
    ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

    ctk.CTkButton(
        guidance_frame,
        text="Review Profile",
        width=130,
        command=on_review_profile,
        fg_color="transparent",
        border_width=2,
    ).grid(row=0, column=1, rowspan=2, sticky="e", padx=12, pady=10)


def add_recent_searches_panel(
    parent,
    rows: Sequence[SearchPanelRow],
    *,
    on_apply: Callable[[dict[str, Any]], None],
) -> None:
    """Show recent searches with one-click apply controls."""
    if not rows:
        return

    panel = ctk.CTkFrame(parent)
    panel.pack(fill="x", pady=(0, 16))
    panel.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        panel,
        text="Recent Searches",
        font=ctk.CTkFont(size=13, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

    for index, row in enumerate(rows, start=1):
        ctk.CTkButton(
            panel,
            text=row.label,
            height=30,
            command=lambda cfg=row.config: on_apply(cfg),
        ).grid(row=index, column=0, sticky="ew", padx=12, pady=(0, 6))
        ctk.CTkLabel(
            panel,
            text=row.detail,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            justify="left",
        ).grid(row=index, column=1, sticky="w", padx=(8, 12), pady=(0, 6))


def add_saved_searches_panel(
    parent,
    rows: Sequence[SearchPanelRow],
    *,
    on_apply: Callable[[dict[str, Any]], None],
    on_save_current: Callable[[], None],
):
    """Show named saved searches and a save-current control."""
    panel = ctk.CTkFrame(parent)
    panel.pack(fill="x", pady=(0, 16))
    panel.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        panel,
        text="Saved Searches",
        font=ctk.CTkFont(size=13, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

    ctk.CTkButton(
        panel,
        text="Save Current",
        width=130,
        command=on_save_current,
        fg_color="transparent",
        border_width=2,
    ).grid(row=0, column=1, sticky="e", padx=12, pady=(10, 4))

    if not rows:
        ctk.CTkLabel(
            panel,
            text="No saved searches yet.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))
    else:
        for index, row in enumerate(rows, start=1):
            ctk.CTkButton(
                panel,
                text=row.label,
                height=30,
                command=lambda cfg=row.config: on_apply(cfg),
            ).grid(row=index, column=0, sticky="ew", padx=12, pady=(0, 6))
            ctk.CTkLabel(
                panel,
                text=row.detail,
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w",
                justify="left",
            ).grid(row=index, column=1, sticky="w", padx=(8, 12), pady=(0, 6))

    status_label = ctk.CTkLabel(
        panel,
        text="",
        font=ctk.CTkFont(size=12),
        text_color="gray",
    )
    status_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 8))
    return status_label
