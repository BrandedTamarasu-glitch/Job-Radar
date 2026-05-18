"""Shared GUI dialog construction helpers."""

from __future__ import annotations

import customtkinter as ctk


def show_message_dialog(
    parent,
    *,
    title: str,
    message: str,
    geometry: str = "400x200",
    text_color: str | None = None,
) -> None:
    """Show a centered modal message dialog."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry(geometry)

    dialog.transient(parent)
    dialog.grab_set()

    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
    y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")

    label_kwargs = {
        "text": message,
        "wraplength": 350,
        "font": ctk.CTkFont(size=13),
    }
    if text_color is not None:
        label_kwargs["text_color"] = text_color

    ctk.CTkLabel(dialog, **label_kwargs).pack(pady=30, padx=20)

    ctk.CTkButton(
        dialog,
        text="OK",
        width=100,
        command=dialog.destroy,
    ).pack(pady=(0, 20))
