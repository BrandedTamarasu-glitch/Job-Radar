"""Search tab panel construction helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import customtkinter as ctk

from job_radar.profile_readiness import ProfileReadiness


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
