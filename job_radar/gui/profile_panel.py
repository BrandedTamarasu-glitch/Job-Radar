"""Profile tab panel construction helpers."""

from __future__ import annotations

import customtkinter as ctk


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
