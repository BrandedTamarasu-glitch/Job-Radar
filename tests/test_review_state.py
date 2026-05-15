"""Tests for persisted search-result review state."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from job_radar.review_state import (
    clear_job_review_state,
    clear_review_state_by_state,
    get_job_review_state,
    load_review_state,
    review_state_counts,
    set_job_review_state,
)


def test_load_review_state_returns_empty_state_for_missing_or_invalid_file(tmp_path):
    path = tmp_path / "review_state.json"

    assert load_review_state(path) == {"version": 1, "jobs": {}}

    path.write_text("{bad json", encoding="utf-8")

    assert load_review_state(path) == {"version": 1, "jobs": {}}


def test_set_job_review_state_persists_normalized_job_entry(tmp_path):
    path = tmp_path / "review_state.json"
    now = datetime(2026, 5, 14, 12, 30, tzinfo=timezone.utc)

    state = set_job_review_state(
        "Senior Python Dev",
        "Acme",
        "shortlisted",
        path=path,
        now=now,
    )

    entry = state["jobs"]["senior python dev||acme"]
    assert entry == {
        "state": "shortlisted",
        "title": "Senior Python Dev",
        "company": "Acme",
        "updated_at": "2026-05-14T12:30:00+00:00",
    }
    assert json.loads(path.read_text(encoding="utf-8")) == state


def test_set_job_review_state_rejects_unknown_state(tmp_path):
    with pytest.raises(ValueError, match="Unknown job review state"):
        set_job_review_state("Engineer", "Acme", "later-ish", path=tmp_path / "state.json")


def test_get_and_clear_job_review_state(tmp_path):
    path = tmp_path / "review_state.json"
    set_job_review_state("Engineer", "Acme", "maybe_later", path=path)

    assert get_job_review_state("Engineer", "Acme", path=path) == "maybe_later"

    clear_job_review_state("Engineer", "Acme", path=path)

    assert get_job_review_state("Engineer", "Acme", path=path) is None


def test_review_state_counts_include_all_supported_states(tmp_path):
    path = tmp_path / "review_state.json"
    set_job_review_state("Engineer", "Acme", "shortlisted", path=path)
    set_job_review_state("Designer", "Acme", "dismissed", path=path)
    set_job_review_state("Manager", "Acme", "maybe_later", path=path)
    set_job_review_state("Analyst", "Acme", "maybe_later", path=path)

    assert review_state_counts(path) == {
        "dismissed": 1,
        "maybe_later": 2,
        "shortlisted": 1,
    }


def test_clear_review_state_by_state_is_bounded(tmp_path):
    path = tmp_path / "review_state.json"
    set_job_review_state("Dismissed 1", "Acme", "dismissed", path=path)
    set_job_review_state("Dismissed 2", "Acme", "dismissed", path=path)
    set_job_review_state("Maybe", "Acme", "maybe_later", path=path)

    state = clear_review_state_by_state("dismissed", path=path, limit=1)

    assert review_state_counts(path) == {
        "dismissed": 1,
        "maybe_later": 1,
        "shortlisted": 0,
    }
    assert len(state["jobs"]) == 2

    with pytest.raises(ValueError, match="Unknown job review state"):
        clear_review_state_by_state("later-ish", path=path)
