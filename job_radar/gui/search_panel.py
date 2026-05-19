"""Search tab panel construction helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import customtkinter as ctk

from job_radar.gui.search_controls import SearchControls
from job_radar.profile_readiness import ProfileReadiness
from job_radar.saved_searches import SearchPanelRow
from job_radar.gui.search_summary import (
    cancellation_message,
    completion_color,
    completion_message,
    error_message,
    source_fetching_message,
    source_progress_count_text,
)
from job_radar.gui.worker_thread import normalize_source_progress


@dataclass(frozen=True)
class SearchProgressWidgets:
    """Widgets MainWindow updates while a search is running."""

    progress_label: ctk.CTkLabel
    progress_bar: ctk.CTkProgressBar
    progress_count: ctk.CTkLabel
    job_count_display: ctk.CTkTextbox


@dataclass(frozen=True)
class SearchIdleWidgets:
    """Widgets MainWindow wires while search is idle."""

    content_frame: ctk.CTkFrame
    search_controls: SearchControls
    search_button: ctk.CTkButton
    preview_button: ctk.CTkButton
    warning_label: ctk.CTkLabel | None


def replace_success_message(parent, existing_label, message: str):
    """Replace the temporary success message label on the search tab."""
    if existing_label:
        existing_label.destroy()

    success_label = ctk.CTkLabel(
        parent,
        text=message,
        text_color="green",
        font=ctk.CTkFont(size=13),
    )
    success_label.grid(row=1, column=0, pady=(0, 10))
    return success_label


def show_temporary_success_message(
    parent,
    existing_label,
    message: str,
    *,
    schedule_hide: Callable[[int], None],
):
    """Display a replacement success label and schedule its dismissal."""
    success_label = replace_success_message(parent, existing_label, message)
    schedule_hide(3000)
    return success_label


def clear_search_content(parent) -> None:
    """Remove all widgets from the Search content frame before rendering a new state."""
    for widget in parent.winfo_children():
        widget.destroy()


def build_search_idle_shell(
    parent,
    *,
    source_strategy_lines: Sequence[str],
    profile_exists: bool,
    on_run_search: Callable[[], None],
    on_preview_demo: Callable[[], None],
) -> SearchIdleWidgets:
    """Build the search idle shell around dynamic guidance/history panels."""
    content_frame = ctk.CTkFrame(parent, fg_color="transparent")
    content_frame.grid(row=0, column=0)

    search_controls = SearchControls(
        content_frame,
        source_strategy_lines=source_strategy_lines,
    )
    search_controls.pack(pady=(0, 20))

    search_button = ctk.CTkButton(
        content_frame,
        text="Run Search",
        height=40,
        width=200,
        state="normal" if profile_exists else "disabled",
        command=on_run_search,
    )

    preview_button = ctk.CTkButton(
        content_frame,
        text="Preview Demo Report",
        height=36,
        width=200,
        command=on_preview_demo,
        fg_color="transparent",
        border_width=2,
    )

    warning_label = None
    if not profile_exists:
        warning_label = ctk.CTkLabel(
            content_frame,
            text="Profile required to run search",
            text_color="red",
        )

    return SearchIdleWidgets(
        content_frame=content_frame,
        search_controls=search_controls,
        search_button=search_button,
        preview_button=preview_button,
        warning_label=warning_label,
    )


def update_source_progress_widgets(
    progress_label,
    progress_bar,
    progress_count,
    source: str,
    current: int,
    total: int,
    *,
    update_label: bool = True,
) -> None:
    """Update Search progress widgets with normalized source progress."""
    current, total = normalize_source_progress(current, total)
    if update_label:
        progress_label.configure(text=source_fetching_message(source))
    progress_bar.set(current / total)
    progress_count.configure(text=source_progress_count_text(current, total))


def pack_search_idle_actions(widgets: SearchIdleWidgets) -> None:
    """Pack idle search actions after optional panels have been inserted."""
    widgets.search_button.pack(pady=(0, 10))
    widgets.preview_button.pack(pady=(0, 10))
    if widgets.warning_label is not None:
        widgets.warning_label.pack()


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


def build_search_progress_panel(parent, *, on_cancel: Callable[[], None]) -> SearchProgressWidgets:
    """Display progress state with progress bar, per-source job counts, and cancel button."""
    content_frame = ctk.CTkFrame(parent, fg_color="transparent")
    content_frame.grid(row=0, column=0)

    progress_label = ctk.CTkLabel(
        content_frame,
        text="Starting search...",
        font=ctk.CTkFont(size=14),
    )
    progress_label.pack(pady=(0, 15))

    progress_bar = ctk.CTkProgressBar(
        content_frame,
        width=400,
    )
    progress_bar.set(0)
    progress_bar.pack(pady=(0, 10))

    progress_count = ctk.CTkLabel(
        content_frame,
        text="Source 0 of 0",
        font=ctk.CTkFont(size=12),
        text_color="gray",
    )
    progress_count.pack(pady=(0, 15))

    job_count_display = ctk.CTkTextbox(
        content_frame,
        width=400,
        height=100,
        state="disabled",
    )
    job_count_display.pack(pady=(0, 20))

    ctk.CTkButton(
        content_frame,
        text="Cancel",
        height=35,
        width=150,
        command=on_cancel,
        fg_color="red",
        hover_color="darkred",
    ).pack()

    return SearchProgressWidgets(
        progress_label=progress_label,
        progress_bar=progress_bar,
        progress_count=progress_count,
        job_count_display=job_count_display,
    )


def build_search_completion_panel(
    parent,
    *,
    job_count: int,
    warning_message: str | None,
    next_action_text: str | None,
    summary_lines: Sequence[str],
    context_text: str | None,
    review_text: str | None,
    on_open_report: Callable[[], None],
    on_new_search: Callable[[], None],
) -> None:
    """Display completion state with report actions and run context."""
    content_frame = ctk.CTkFrame(parent, fg_color="transparent")
    content_frame.grid(row=0, column=0)

    ctk.CTkLabel(
        content_frame,
        text=completion_message(job_count),
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=completion_color(job_count),
    ).pack(pady=(0, 15))

    if warning_message:
        ctk.CTkLabel(
            content_frame,
            text=warning_message,
            font=ctk.CTkFont(size=12),
            text_color="orange",
            wraplength=420,
            justify="center",
        ).pack(pady=(0, 12))

    if next_action_text:
        ctk.CTkLabel(
            content_frame,
            text=next_action_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=420,
            justify="left",
        ).pack(pady=(0, 16))

    if summary_lines:
        summary_box = ctk.CTkTextbox(
            content_frame,
            width=420,
            height=min(180, max(80, len(summary_lines) * 24)),
            state="normal",
        )
        summary_box.insert("end", "\n".join(summary_lines))
        summary_box.configure(state="disabled")
        summary_box.pack(pady=(0, 20))

    if context_text:
        ctk.CTkLabel(
            content_frame,
            text=context_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=420,
            justify="left",
        ).pack(pady=(0, 16))

    if review_text:
        ctk.CTkLabel(
            content_frame,
            text=review_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=420,
            justify="center",
        ).pack(pady=(0, 16))

    ctk.CTkButton(
        content_frame,
        text="Open Report",
        height=40,
        width=200,
        command=on_open_report,
    ).pack(pady=(0, 15))

    ctk.CTkButton(
        content_frame,
        text="New Search",
        height=40,
        width=200,
        command=on_new_search,
        fg_color="transparent",
        border_width=2,
    ).pack()


def build_search_error_panel(
    parent,
    *,
    message: str,
    on_retry: Callable[[], None],
    on_back_to_search: Callable[[], None],
) -> None:
    """Display search failure state with retry and reset actions."""
    content_frame = ctk.CTkFrame(parent, fg_color="transparent")
    content_frame.grid(row=0, column=0)

    ctk.CTkLabel(
        content_frame,
        text="Search failed",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="red",
    ).pack(pady=(0, 12))

    ctk.CTkLabel(
        content_frame,
        text=error_message(message),
        font=ctk.CTkFont(size=12),
        text_color="gray",
        wraplength=420,
        justify="center",
    ).pack(pady=(0, 20))

    ctk.CTkButton(
        content_frame,
        text="Try Again",
        height=40,
        width=200,
        command=on_retry,
    ).pack(pady=(0, 15))

    ctk.CTkButton(
        content_frame,
        text="Back to Search",
        height=40,
        width=200,
        command=on_back_to_search,
        fg_color="transparent",
        border_width=2,
    ).pack()


def build_search_cancelled_panel(parent, *, on_new_search: Callable[[], None]) -> None:
    """Display search cancellation state with a reset action."""
    content_frame = ctk.CTkFrame(parent, fg_color="transparent")
    content_frame.grid(row=0, column=0)

    ctk.CTkLabel(
        content_frame,
        text="Search cancelled",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="orange",
    ).pack(pady=(0, 12))

    ctk.CTkLabel(
        content_frame,
        text=cancellation_message(),
        font=ctk.CTkFont(size=12),
        text_color="gray",
        wraplength=420,
        justify="center",
    ).pack(pady=(0, 20))

    ctk.CTkButton(
        content_frame,
        text="New Search",
        height=40,
        width=200,
        command=on_new_search,
        fg_color="transparent",
        border_width=2,
    ).pack()
