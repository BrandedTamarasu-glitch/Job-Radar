"""Tests for app-data portability exports."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone

from job_radar.data_portability import (
    MAX_PORTABLE_FILE_BYTES,
    export_app_data_bundle,
    list_portable_data_files,
    restore_app_data_bundle,
    validate_app_data_bundle,
)


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


def test_validate_app_data_bundle_accepts_exported_bundle(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "profile.json").write_text('{"name": "Cory"}', encoding="utf-8")
    bundle_path = tmp_path / "job-radar-data.zip"
    export_app_data_bundle(bundle_path, data_dir=data_dir)

    result = validate_app_data_bundle(bundle_path)

    assert result.is_valid is True
    assert result.files == ["profile.json"]
    assert result.errors == []


def test_validate_app_data_bundle_rejects_missing_manifest(tmp_path):
    bundle_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(bundle_path, "w") as archive:
        archive.writestr("profile.json", "{}")

    result = validate_app_data_bundle(bundle_path)

    assert result.is_valid is False
    assert result.errors == ["Bundle is missing manifest.json"]


def test_validate_app_data_bundle_rejects_unsupported_and_missing_files(tmp_path):
    bundle_path = tmp_path / "bad.zip"
    manifest = {
        "version": 1,
        "files": [
            {"path": "profile.json", "description": "Profile"},
            {"path": "../escape.json", "description": "Bad"},
            {"path": "config.json", "description": "Missing"},
        ],
    }
    with zipfile.ZipFile(bundle_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("profile.json", "{}")
        archive.writestr("extra.json", "{}")

    result = validate_app_data_bundle(bundle_path)

    assert result.is_valid is False
    assert result.files == ["profile.json"]
    assert result.errors == [
        "Unsupported bundle file path: ../escape.json",
        "Manifest file missing from bundle: config.json",
        "Unexpected bundle file: extra.json",
    ]


def test_validate_app_data_bundle_rejects_invalid_json_payload(tmp_path):
    bundle_path = tmp_path / "bad-json.zip"
    manifest = {
        "version": 1,
        "files": [{"path": "profile.json", "description": "Profile"}],
    }
    with zipfile.ZipFile(bundle_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("profile.json", "{bad json")

    result = validate_app_data_bundle(bundle_path)

    assert result.is_valid is False
    assert result.files == []
    assert result.errors == ["Bundle file is not valid JSON: profile.json"]


def test_validate_app_data_bundle_rejects_non_object_json_payload(tmp_path):
    bundle_path = tmp_path / "bad-shape.zip"
    manifest = {
        "version": 1,
        "files": [{"path": "saved_searches.json", "description": "Saved searches"}],
    }
    with zipfile.ZipFile(bundle_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("saved_searches.json", "[]")

    result = validate_app_data_bundle(bundle_path)

    assert result.is_valid is False
    assert result.files == []
    assert result.errors == ["Bundle file must contain a JSON object: saved_searches.json"]


def test_validate_app_data_bundle_rejects_oversized_file(tmp_path):
    bundle_path = tmp_path / "large.zip"
    manifest = {
        "version": 1,
        "files": [{"path": "config.json", "description": "Config"}],
    }
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("config.json", " " * (MAX_PORTABLE_FILE_BYTES + 1))

    result = validate_app_data_bundle(bundle_path)

    assert result.is_valid is False
    assert result.files == []
    assert result.errors == ["Bundle file is too large: config.json"]


def test_restore_app_data_bundle_restores_validated_files(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "profile.json").write_text('{"name": "New"}', encoding="utf-8")
    (source_dir / "results").mkdir()
    (source_dir / "results" / "tracker.json").write_text('{"applications": {}}', encoding="utf-8")
    bundle_path = tmp_path / "bundle.zip"
    export_app_data_bundle(bundle_path, data_dir=source_dir)
    target_dir = tmp_path / "target"

    result = restore_app_data_bundle(bundle_path, data_dir=target_dir)

    assert result.restored_files == ["profile.json", "results/tracker.json"]
    assert result.backup_files == []
    assert (target_dir / "profile.json").read_text(encoding="utf-8") == '{"name": "New"}'
    assert (target_dir / "results" / "tracker.json").read_text(encoding="utf-8") == '{"applications": {}}'


def test_restore_app_data_bundle_backs_up_existing_files(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "profile.json").write_text('{"name": "Restored"}', encoding="utf-8")
    bundle_path = tmp_path / "bundle.zip"
    export_app_data_bundle(bundle_path, data_dir=source_dir)
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / "profile.json").write_text('{"name": "Existing"}', encoding="utf-8")
    now = datetime(2026, 5, 14, 20, 30, tzinfo=timezone.utc)

    result = restore_app_data_bundle(bundle_path, data_dir=target_dir, now=now)

    assert result.restored_files == ["profile.json"]
    assert result.backup_files == ["profile.json.20260514T203000Z.bak"]
    assert (target_dir / "profile.json").read_text(encoding="utf-8") == '{"name": "Restored"}'
    assert (
        target_dir / "profile.json.20260514T203000Z.bak"
    ).read_text(encoding="utf-8") == '{"name": "Existing"}'


def test_restore_app_data_bundle_rejects_invalid_bundle(tmp_path):
    bundle_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(bundle_path, "w") as archive:
        archive.writestr("profile.json", "{}")

    try:
        restore_app_data_bundle(bundle_path, data_dir=tmp_path / "target")
    except ValueError as exc:
        assert "manifest.json" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
