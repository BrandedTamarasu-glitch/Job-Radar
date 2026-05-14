"""Tests for release artifact verification diagnostics."""

import os

import pytest

from job_radar.release_verification import (
    ReleaseArtifactError,
    expected_release_artifacts,
    verify_release_artifacts,
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
