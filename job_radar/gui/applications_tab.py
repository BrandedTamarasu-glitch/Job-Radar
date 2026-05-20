"""Applications tab construction helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import customtkinter as ctk

from job_radar.application_templates import get_application_note_templates
from job_radar.gui.applications_view_model import (
    application_followup_filter_options,
    application_next_action_row,
    application_pipeline_display_row,
    application_status_menu_labels,
    build_applications_view_model,
    filter_application_next_actions,
)
from job_radar.tracker import get_all_application_statuses, get_application_next_actions


@dataclass(frozen=True)
class ApplicationsTabCallbacks:
    """Callbacks owned by MainWindow behavior methods."""

    export_csv: Callable[[], None]
    import_status_updates: Callable[[], None]
    export_calendar: Callable[[], None]
    refresh: Callable[[], None]
    set_followup_filter: Callable[[str], None]
    update_status: Callable[[Any, str], None]
    prompt_next_action: Callable[[Any], None]
    prompt_due_date: Callable[[Any], None]
    prompt_notes: Callable[[Any], None]
    insert_note_template: Callable[[Any, str], None]
    complete_next_action: Callable[[dict[str, Any]], None]
    snooze_next_action: Callable[[dict[str, Any]], None]


def set_applications_status(status_label, message: str, color: str) -> None:
    """Update Applications-tab feedback when the status label exists."""
    if status_label is not None:
        status_label.configure(text=message, text_color=color)


def build_applications_tab_content(
    parent,
    *,
    followup_filter: str,
    callbacks: ApplicationsTabCallbacks,
):
    """Build Applications tab widgets and return its status label."""
    for widget in parent.winfo_children():
        widget.destroy()

    scroll_frame = ctk.CTkScrollableFrame(parent)
    scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
    scroll_frame.grid_columnconfigure(0, weight=1)

    header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    header_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        header_frame,
        text="Applications",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).grid(row=0, column=0, columnspan=2, sticky="w")

    actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    actions_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    for column in range(4):
        actions_frame.grid_columnconfigure(column, weight=1, uniform="application_actions")

    ctk.CTkButton(
        actions_frame,
        text="Export CSV",
        height=30,
        command=callbacks.export_csv,
    ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

    ctk.CTkButton(
        actions_frame,
        text="Import Status JSON",
        height=30,
        command=callbacks.import_status_updates,
    ).grid(row=0, column=1, sticky="ew", padx=(0, 6))

    ctk.CTkButton(
        actions_frame,
        text="Export Calendar",
        height=30,
        command=callbacks.export_calendar,
    ).grid(row=0, column=2, sticky="ew", padx=(0, 6))

    ctk.CTkButton(
        actions_frame,
        text="Refresh",
        height=30,
        command=callbacks.refresh,
    ).grid(row=0, column=3, sticky="ew")

    filter_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    filter_frame.grid(row=1, column=0, sticky="w", pady=(0, 8))

    ctk.CTkLabel(
        filter_frame,
        text="Follow-ups:",
        font=ctk.CTkFont(size=12, weight="bold"),
    ).pack(side="left", padx=(0, 8))

    for filter_key, label in application_followup_filter_options():
        ctk.CTkButton(
            filter_frame,
            text=label,
            width=84,
            height=28,
            fg_color=None if followup_filter == filter_key else "transparent",
            border_width=0 if followup_filter == filter_key else 2,
            command=lambda key=filter_key: callbacks.set_followup_filter(key),
        ).pack(side="left", padx=(0, 6))

    status_label = ctk.CTkLabel(
        scroll_frame,
        text="",
        font=ctk.CTkFont(size=12),
        text_color="gray",
    )
    status_label.grid(row=2, column=0, sticky="w", pady=(0, 8))

    applications = get_all_application_statuses()
    next_actions = get_application_next_actions(
        applications=applications,
        limit=5,
    )
    filtered_next_actions = filter_application_next_actions(
        next_actions,
        followup_filter,
    )
    groups = build_applications_view_model(applications)
    total_rows = sum(group.count for group in groups)

    if total_rows == 0:
        ctk.CTkLabel(
            scroll_frame,
            text="No application pipeline entries yet.",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).grid(row=3, column=0, sticky="w", pady=20)
        return status_label

    row_index = 3
    if filtered_next_actions:
        _add_application_next_action_queue(scroll_frame, row_index, filtered_next_actions, callbacks)
        row_index += 1

    templates = get_application_note_templates()
    for group in groups:
        group_frame = ctk.CTkFrame(scroll_frame)
        group_frame.grid(row=row_index, column=0, sticky="ew", pady=(0, 10))
        group_frame.grid_columnconfigure(0, weight=1)
        row_index += 1

        ctk.CTkLabel(
            group_frame,
            text=f"{group.label} ({group.count})",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        if group.count == 0:
            ctk.CTkLabel(
                group_frame,
                text="No jobs in this status.",
                text_color="gray",
            ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
            continue

        for item_index, item in enumerate(group.rows, start=1):
            display_row = application_pipeline_display_row(item)

            ctk.CTkLabel(
                group_frame,
                text=display_row.heading,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
            ).grid(row=item_index * 3 - 2, column=0, sticky="ew", padx=16, pady=(4, 0))

            ctk.CTkLabel(
                group_frame,
                text=display_row.detail_text,
                text_color="gray",
                wraplength=760,
                anchor="w",
                justify="left",
            ).grid(row=item_index * 3 - 1, column=0, sticky="ew", padx=16, pady=(0, 4))

            _add_application_row_actions(
                group_frame,
                row_index=item_index * 3,
                item=item,
                templates=templates,
                callbacks=callbacks,
            )

    return status_label


def _add_application_row_actions(
    parent,
    *,
    row_index: int,
    item,
    templates,
    callbacks: ApplicationsTabCallbacks,
) -> None:
    """Add wrapped application status/edit/template controls for one row."""
    edit_frame = ctk.CTkFrame(parent, fg_color="transparent")
    edit_frame.grid(row=row_index, column=0, sticky="ew", padx=16, pady=(0, 8))
    edit_frame.grid_columnconfigure(0, weight=1)

    status_menu = ctk.CTkOptionMenu(
        edit_frame,
        values=application_status_menu_labels(item.status),
        width=180,
        command=lambda selected, row=item: callbacks.update_status(row, selected),
    )
    status_menu.set(item.status_label)
    status_menu.grid(row=0, column=0, sticky="w", pady=(0, 6))

    edit_actions = ctk.CTkFrame(edit_frame, fg_color="transparent")
    edit_actions.grid(row=1, column=0, sticky="ew", pady=(0, 6))
    for column in range(3):
        edit_actions.grid_columnconfigure(column, weight=1, uniform="application_edit")

    ctk.CTkButton(
        edit_actions,
        text="Set Next",
        height=28,
        command=lambda row=item: callbacks.prompt_next_action(row),
    ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
    ctk.CTkButton(
        edit_actions,
        text="Set Due",
        height=28,
        command=lambda row=item: callbacks.prompt_due_date(row),
    ).grid(row=0, column=1, sticky="ew", padx=(0, 6))
    ctk.CTkButton(
        edit_actions,
        text="Edit Notes",
        height=28,
        command=lambda row=item: callbacks.prompt_notes(row),
    ).grid(row=0, column=2, sticky="ew")

    template_actions = ctk.CTkFrame(edit_frame, fg_color="transparent")
    template_actions.grid(row=2, column=0, sticky="ew")
    for column in range(max(1, len(templates))):
        template_actions.grid_columnconfigure(column, weight=1, uniform="application_templates")

    for column, template in enumerate(templates):
        ctk.CTkButton(
            template_actions,
            text=f"Add {template.label}",
            height=28,
            command=lambda row=item, key=template.key: callbacks.insert_note_template(row, key),
        ).grid(row=0, column=column, sticky="ew", padx=(0, 6 if column < len(templates) - 1 else 0))


def _add_application_next_action_queue(
    parent,
    row_index: int,
    next_actions: list[dict[str, Any]],
    callbacks: ApplicationsTabCallbacks,
) -> None:
    """Add a compact follow-up queue to the Applications tab."""
    queue_frame = ctk.CTkFrame(parent)
    queue_frame.grid(row=row_index, column=0, sticky="ew", pady=(0, 12))
    queue_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        queue_frame,
        text="Next Actions",
        font=ctk.CTkFont(size=14, weight="bold"),
    ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

    for index, action in enumerate(next_actions, start=1):
        row = application_next_action_row(action)

        action_frame = ctk.CTkFrame(queue_frame, fg_color="transparent")
        action_frame.grid(row=index * 3 - 2, column=0, sticky="ew", padx=16, pady=(4, 0))
        action_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            action_frame,
            text=f"{index}. {action['next_action']} — {row.title} at {row.company}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            wraplength=640,
            justify="left",
        ).grid(row=0, column=0, sticky="ew")

        queue_actions = ctk.CTkFrame(queue_frame, fg_color="transparent")
        queue_actions.grid(row=index * 3 - 1, column=0, sticky="ew", padx=16, pady=(4, 4))
        for column in range(2):
            queue_actions.grid_columnconfigure(column, weight=1, uniform="followup_actions")

        ctk.CTkButton(
            queue_actions,
            text="Complete",
            height=28,
            command=lambda queued=action: callbacks.complete_next_action(queued),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            queue_actions,
            text="Snooze 3d",
            height=28,
            command=lambda queued=action: callbacks.snooze_next_action(queued),
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            queue_frame,
            text=f"{row.due_text} | {row.status_label}",
            text_color="gray",
            wraplength=760,
            anchor="w",
            justify="left",
        ).grid(row=index * 3, column=0, sticky="ew", padx=16, pady=(0, 6))
