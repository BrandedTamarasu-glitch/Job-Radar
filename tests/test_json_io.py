"""Tests for shared JSON file I/O helpers."""

from __future__ import annotations

import json

import pytest

from job_radar import json_io


def test_write_json_atomic_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "state.json"

    json_io.write_json_atomic(path, {"status": "ok"})

    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "ok"}


def test_write_json_atomic_preserves_existing_file_on_failure(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"status": "old"}), encoding="utf-8")
    monkeypatch.setattr(
        "job_radar.json_io.os.fsync",
        lambda _fd: (_ for _ in ()).throw(OSError("disk full")),
    )

    with pytest.raises(OSError, match="disk full"):
        json_io.write_json_atomic(path, {"status": "new"})

    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "old"}
    assert not list(path.parent.glob("*.tmp"))
