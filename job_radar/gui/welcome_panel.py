"""Welcome screen construction helpers."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk


def build_welcome_screen(
    parent,
    *,
    on_get_started: Callable[[], None],
    on_preview_demo: Callable[[], None],
) -> ctk.CTkLabel:
    """Build the first-run welcome screen and return its status label."""
    content_frame = ctk.CTkFrame(parent, fg_color="transparent")
    content_frame.place(in_=parent, relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(
        content_frame,
        text="Welcome to Job Radar",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(pady=(0, 20))

    ctk.CTkLabel(
        content_frame,
        text=(
            "Job Radar searches multiple job boards, scores each listing against your profile, "
            "and generates a ranked report — so you focus on the best matches."
        ),
        wraplength=500,
        justify="left",
    ).pack(pady=(0, 15))

    ctk.CTkLabel(
        content_frame,
        text="Set up your profile to get started. You'll enter your skills, target titles, and preferences.",
        wraplength=500,
        justify="left",
    ).pack(pady=(0, 30))

    ctk.CTkButton(
        content_frame,
        text="Get Started",
        height=40,
        width=200,
        command=on_get_started,
    ).pack()

    ctk.CTkButton(
        content_frame,
        text="Preview Demo Report",
        height=36,
        width=200,
        command=on_preview_demo,
        fg_color="transparent",
        border_width=2,
    ).pack(pady=(12, 0))

    status_label = ctk.CTkLabel(
        content_frame,
        text="",
        font=ctk.CTkFont(size=12),
        text_color="gray",
        wraplength=500,
        justify="center",
    )
    status_label.pack(pady=(14, 0))
    return status_label
