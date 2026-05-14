"""Tests for app-data portability exports."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone

from job_radar.data_portability import export_app_data_bundle, list_portable_data_files


def test_list_portable_data_files_includes_existing_app_data(tmp_path):
    (tmp_path / "profile.json").write_text("{}", encoding="utf-8")
    (tmp_path / "saved_searches.json").write_text("{}", encoding="utf-8")
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "tracker.json").write_text("{}", encoding="utf-8")

    files = list_portable_data_files(tmp_path)

    assert [file.archive_name for file in files] == [
        "profile.json",
        "saved_searches.json",
        "results/tracker.json",
    ]


def test_export_app_data_bundle_writes_manifest_and_existing_files(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "profile.json").write_text('{"name": "Cory"}', encoding="utf-8")
    (data_dir / "config.json").write_text('{"api": true}', encoding="utf-8")
    (data_dir / "review_state.json").write_text('{"jobs": {}}', encoding="utf-8")
    (data_dir / "results").mkdir()
    (data_dir / "results" / "tracker.json").write_text('{"applications": {}}', encoding="utf-8")
    output_path = tmp_path / "job-radar-data.zip"
    now = datetime(2026, 5, 14, 18, 0, tzinfo=timezone.utc)

    result = export_app_data_bundle(output_path, data_dir=data_dir, now=now)

    assert result == output_path
    with zipfile.ZipFile(output_path) as archive:
        assert set(archive.namelist()) == {
            "manifest.json",
            "profile.json",
            "config.json",
            "review_state.json",
            "results/tracker.json",
        }
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["created_at"] == "2026-05-14T18:00:00+00:00"
        assert [file["path"] for file in manifest["files"]] == [
            "profile.json",
            "config.json",
            "review_state.json",
            "results/tracker.json",
        ]
        assert archive.read("profile.json").decode("utf-8") == '{"name": "Cory"}'


def test_export_app_data_bundle_allows_empty_bundle_with_manifest(tmp_path):
    output_path = tmp_path / "empty.zip"

    export_app_data_bundle(output_path, data_dir=tmp_path)

    with zipfile.ZipFile(output_path) as archive:
        assert archive.namelist() == ["manifest.json"]
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["files"] == []
