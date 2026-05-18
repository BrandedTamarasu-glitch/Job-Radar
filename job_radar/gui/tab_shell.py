"""Helpers for the main window tab shell."""

import customtkinter as ctk


MAIN_TAB_NAMES = ("Profile", "Search", "Applications", "Settings")


def build_main_tabview(parent, on_tab_change):
    """Create the primary tabview and register the main application tabs."""
    tabview = ctk.CTkTabview(parent, command=on_tab_change)
    tabview.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

    for tab_name in MAIN_TAB_NAMES:
        tabview.add(tab_name)

    return tabview
