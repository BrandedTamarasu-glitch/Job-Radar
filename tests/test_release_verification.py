"""Tests for release artifact verification diagnostics."""

import os

import pytest

from job_radar.release_verification import (
    ReleaseArtifactError,
    expected_release_artifacts,
    verify_release_artifacts,
    write_checksum_manifest,
)


def test_expected_release_artifacts_cover_platform_bundles():
    assert [check.path.as_posix() for check in expected_release_artifacts("linux", "v2.6.0")] == [
        "dist/job-radar/job-radar",
        "job-radar-v2.6.0-linux.tar.gz",
    ]
    assert [check.path.as_posix() for check in expected_release_artifacts("windows", "v2.6.0")] == [
        "dist/job-radar/job-radar.exe",
        "job-radar-v2.6.0-windows.zip",
    ]
    assert [check.path.as_posix() for check in expected_release_artifacts("macos", "v2.6.0")] == [
        "dist/JobRadar.app/Contents/MacOS/job-radar-cli",
        "job-radar-v2.6.0-macos.zip",
    ]


def test_expected_release_artifacts_cover_installers():
    assert [check.path.as_posix() for check in expected_release_artifacts("macos", "v2.6.0", kind="installer")] == [
        "Job-Radar-v2.6.0-macos.dmg",
    ]
    assert [check.path.as_posix() for check in expected_release_artifacts("windows", "v2.6.0", kind="installer")] == [
        "installers/windows/Job-Radar-Setup-v2.6.0.exe",
    ]


def test_verify_release_artifacts_accepts_nonempty_bundle_files(tmp_path):
    executable = tmp_path / "dist" / "job-radar" / "job-radar"
    executable.parent.mkdir(parents=True)
    executable.write_text("binary", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | 0o755)
    archive = tmp_path / "job-radar-v2.6.0-linux.tar.gz"
    archive.write_text("archive", encoding="utf-8")

    verified = verify_release_artifacts(tmp_path, "linux", "v2.6.0")

    assert verified == [executable, archive]


def test_verify_release_artifacts_reports_missing_and_empty_files(tmp_path):
    archive = tmp_path / "job-radar-v2.6.0-linux.tar.gz"
    archive.touch()

    with pytest.raises(ReleaseArtifactError) as exc:
        verify_release_artifacts(tmp_path, "linux", "v2.6.0")

    message = str(exc.value)
    assert "missing Linux executable" in message
    assert "empty Linux archive" in message
    assert os.fspath(tmp_path) in message


def test_verify_release_artifacts_reports_similar_files_for_name_drift(tmp_path):
    executable = tmp_path / "dist" / "job-radar" / "job-radar"
    executable.parent.mkdir(parents=True)
    executable.write_text("binary", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | 0o755)
    drifted_archive = tmp_path / "job-radar-v2.6.1-linux.tar.gz"
    drifted_archive.write_text("archive", encoding="utf-8")

    with pytest.raises(ReleaseArtifactError) as exc:
        verify_release_artifacts(tmp_path, "linux", "v2.6.0")

    message = str(exc.value)
    assert "missing Linux archive" in message
    assert "found similar: job-radar-v2.6.1-linux.tar.gz" in message


def test_verify_release_artifacts_reports_installer_directory_drift(tmp_path):
    drifted_installer = tmp_path / "Job-Radar-Setup-v2.6.0.exe"
    drifted_installer.write_text("installer", encoding="utf-8")

    with pytest.raises(ReleaseArtifactError) as exc:
        verify_release_artifacts(tmp_path, "windows", "v2.6.0", kind="installer")

    message = str(exc.value)
    assert "missing Windows NSIS installer" in message
    assert "found similar: Job-Radar-Setup-v2.6.0.exe" in message


def test_verify_release_artifacts_reports_missing_execute_permission(tmp_path):
    executable = tmp_path / "dist" / "job-radar" / "job-radar"
    executable.parent.mkdir(parents=True)
    executable.write_text("binary", encoding="utf-8")
    executable.chmod(0o644)
    archive = tmp_path / "job-radar-v2.6.0-linux.tar.gz"
    archive.write_text("archive", encoding="utf-8")

    with pytest.raises(ReleaseArtifactError) as exc:
        verify_release_artifacts(tmp_path, "linux", "v2.6.0")

    assert "not executable Linux executable" in str(exc.value)


def test_write_checksum_manifest_records_verified_artifact_hashes(tmp_path):
    artifact = tmp_path / "job-radar-v2.6.0-linux.tar.gz"
    artifact.write_text("archive", encoding="utf-8")
    manifest = tmp_path / "job-radar-v2.6.0-linux.sha256"

    result = write_checksum_manifest([artifact], manifest, root=tmp_path)

    assert result == manifest
    assert manifest.read_text(encoding="utf-8") == (
        "0eb3e36bfb24dcd9bb1d1bece1531216b59539a8fde17ee80224af0653c92aa3  "
        "job-radar-v2.6.0-linux.tar.gz\n"
    )
