"""Profile dashboard panel construction helpers."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from job_radar.gui.dashboard_view_model import DashboardAction


def add_dashboard_next_steps(
    parent,
    row: int,
    actions: list[DashboardAction],
    *,
    on_select: Callable[[str], None],
) -> int:
    """Render the profile dashboard next-step queue and return the next row."""
    if not actions:
        return row

    dashboard_frame = ctk.CTkFrame(parent)
    dashboard_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    dashboard_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        dashboard_frame,
        text="Next Steps",
        font=ctk.CTkFont(size=16, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

    for index, action in enumerate(actions, start=1):
        action_frame = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        action_frame.grid(row=index, column=0, sticky="ew", padx=12, pady=(0, 10))
        action_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            action_frame,
            text=action.title,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            action_frame,
            text=action.detail,
            text_color="gray",
            wraplength=560,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(2, 0))

        ctk.CTkButton(
            action_frame,
            text=action.target,
            width=120,
            command=lambda target=action.target: on_select(target),
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

    return row + 1
