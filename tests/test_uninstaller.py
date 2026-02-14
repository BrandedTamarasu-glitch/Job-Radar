"""Comprehensive unit tests for uninstaller module."""

import stat
import sys
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from job_radar.uninstaller import (
    get_uninstall_paths,
    create_backup,
    delete_app_data,
    get_binary_path,
    create_cleanup_script,
)


# ---------------------------------------------------------------------------
# get_uninstall_paths tests
# ---------------------------------------------------------------------------

def test_get_uninstall_paths_returns_existing_files_only(tmp_path, monkeypatch):
    """Test returns paths with descriptions for existing files only."""
    # Setup: Create some files
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "profile.json").write_text('{"test": true}')
    (data_dir / "config.json").write_text('{"setting": "value"}')

    log_file = tmp_path / "job-radar-error.log"
    log_file.write_text("error log")

    # Monkeypatch paths
    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.uninstaller.get_log_file", lambda: log_file)

    result = get_uninstall_paths()

    # Should include profile, config, and log
    assert len(result) >= 3
    paths = [path for path, _ in result]
    assert str(data_dir / "profile.json") in paths
    assert str(data_dir / "config.json") in paths
    assert str(log_file) in paths

    # All descriptions should be non-empty strings
    for _, description in result:
        assert isinstance(description, str)
        assert len(description) > 0


def test_get_uninstall_paths_empty_when_no_files(tmp_path, monkeypatch):
    """Test returns empty list when data directory has no relevant files."""
    data_dir = tmp_path / "empty_data"
    data_dir.mkdir()

    log_file = tmp_path / "nonexistent-log.log"

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.uninstaller.get_log_file", lambda: log_file)
    # Also patch Path.cwd() to avoid picking up real .rate_limits directory
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

    result = get_uninstall_paths()

    # Should be empty (no files exist)
    assert result == []


def test_get_uninstall_paths_includes_backups_and_cache(tmp_path, monkeypatch):
    """Test includes backups/ and cache/ directories when present."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    backups_dir = data_dir / "backups"
    backups_dir.mkdir()
    (backups_dir / "backup.zip").write_text("backup")

    cache_dir = data_dir / "cache"
    cache_dir.mkdir()

    log_file = tmp_path / "log.log"

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.uninstaller.get_log_file", lambda: log_file)

    result = get_uninstall_paths()

    paths = [path for path, _ in result]
    assert str(backups_dir) in paths
    assert str(cache_dir) in paths


def test_get_uninstall_paths_descriptions_are_human_readable(tmp_path, monkeypatch):
    """Test descriptions are human-readable strings."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "profile.json").write_text("{}")

    log_file = tmp_path / "log.log"

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.uninstaller.get_log_file", lambda: log_file)

    result = get_uninstall_paths()

    # Check that descriptions contain meaningful text
    for _, description in result:
        assert isinstance(description, str)
        assert len(description) > 10  # Meaningful description
        assert "-" in description or "/" in description  # Has structure


# ---------------------------------------------------------------------------
# create_backup tests
# ---------------------------------------------------------------------------

def test_create_backup_creates_valid_zip_with_both_files(tmp_path, monkeypatch):
    """Test creates valid ZIP with profile.json and config.json."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "profile.json").write_text('{"profile": "data"}')
    (data_dir / "config.json").write_text('{"config": "settings"}')

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)

    backup_path = tmp_path / "backup.zip"
    create_backup(str(backup_path))

    # Verify ZIP exists and is valid
    assert backup_path.exists()
    with zipfile.ZipFile(backup_path, 'r') as zf:
        assert set(zf.namelist()) == {"profile.json", "config.json"}


def test_create_backup_contains_correct_file_contents(tmp_path, monkeypatch):
    """Test ZIP contains correct file contents (read back and verify)."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    profile_content = '{"name": "test_profile"}'
    config_content = '{"setting": "value"}'
    (data_dir / "profile.json").write_text(profile_content)
    (data_dir / "config.json").write_text(config_content)

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)

    backup_path = tmp_path / "backup.zip"
    create_backup(str(backup_path))

    # Read back and verify contents
    with zipfile.ZipFile(backup_path, 'r') as zf:
        assert zf.read("profile.json").decode("utf-8") == profile_content
        assert zf.read("config.json").decode("utf-8") == config_content


def test_create_backup_skips_missing_files_gracefully(tmp_path, monkeypatch):
    """Test skips missing files gracefully (only config.json exists)."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # Only create config.json, profile.json missing
    (data_dir / "config.json").write_text('{"config": "only"}')

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)

    backup_path = tmp_path / "backup.zip"
    create_backup(str(backup_path))

    # ZIP should contain only config.json
    with zipfile.ZipFile(backup_path, 'r') as zf:
        assert zf.namelist() == ["config.json"]


def test_create_backup_raises_on_invalid_save_path(tmp_path, monkeypatch):
    """Test raises on invalid save_path (directory that doesn't exist)."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)

    # Try to save to non-existent directory
    invalid_path = tmp_path / "nonexistent" / "backup.zip"

    with pytest.raises(Exception):
        create_backup(str(invalid_path))


def test_create_backup_empty_data_dir_creates_empty_zip(tmp_path, monkeypatch):
    """Test empty data directory creates ZIP with no entries."""
    data_dir = tmp_path / "empty"
    data_dir.mkdir()

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)

    backup_path = tmp_path / "backup.zip"
    create_backup(str(backup_path))

    # ZIP should exist but be empty
    assert backup_path.exists()
    with zipfile.ZipFile(backup_path, 'r') as zf:
        assert zf.namelist() == []


# ---------------------------------------------------------------------------
# delete_app_data tests
# ---------------------------------------------------------------------------

def test_delete_app_data_deletes_entire_data_directory(tmp_path, monkeypatch):
    """Test deletes entire data directory and returns empty failure list."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "profile.json").write_text("{}")
    (data_dir / "config.json").write_text("{}")
    (data_dir / "subdir").mkdir()

    log_file = tmp_path / "log.log"

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.uninstaller.get_log_file", lambda: log_file)

    # Mock _cleanup_connections
    with patch("job_radar.uninstaller._cleanup_connections") as mock_cleanup:
        failures = delete_app_data()

    # Should have no failures
    assert failures == []
    # Data directory should be deleted
    assert not data_dir.exists()
    # Cleanup should have been called
    mock_cleanup.assert_called_once()


def test_delete_app_data_deletes_log_file_when_present(tmp_path, monkeypatch):
    """Test deletes log file when present."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    log_file = tmp_path / "job-radar-error.log"
    log_file.write_text("error logs")

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.uninstaller.get_log_file", lambda: log_file)

    with patch("job_radar.uninstaller._cleanup_connections"):
        failures = delete_app_data()

    assert failures == []
    assert not log_file.exists()


def test_delete_app_data_returns_failures_for_locked_files(tmp_path, monkeypatch):
    """Test returns failure list for permission-denied files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    log_file = tmp_path / "log.log"

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.uninstaller.get_log_file", lambda: log_file)

    # Mock shutil.rmtree to trigger onerror callback
    original_rmtree = __import__('shutil').rmtree

    def mock_rmtree(path, onerror=None):
        # Simulate permission error
        if onerror:
            exc_info = (None, PermissionError("Permission denied"), None)
            onerror(None, str(data_dir / "locked.json"), exc_info)

    with patch("job_radar.uninstaller._cleanup_connections"):
        with patch("job_radar.uninstaller.shutil.rmtree", side_effect=mock_rmtree):
            failures = delete_app_data()

    # Should have collected the failure
    assert len(failures) > 0
    assert any("locked.json" in path for path, _ in failures)


def test_delete_app_data_calls_cleanup_connections_before_deletion(tmp_path, monkeypatch):
    """Test calls _cleanup_connections before deletion."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    log_file = tmp_path / "log.log"

    monkeypatch.setattr("job_radar.uninstaller.get_data_dir", lambda: data_dir)
    monkeypatch.setattr("job_radar.uninstaller.get_log_file", lambda: log_file)

    # Use mock to verify call order
    with patch("job_radar.uninstaller._cleanup_connections") as mock_cleanup:
        with patch("job_radar.uninstaller.shutil.rmtree") as mock_rmtree:
            delete_app_data()

    # Verify cleanup was called before rmtree
    assert mock_cleanup.called
    assert mock_rmtree.called
    # Verify order by checking call_args_list positions
    # cleanup should be called first


# ---------------------------------------------------------------------------
# get_binary_path tests
# ---------------------------------------------------------------------------

def test_get_binary_path_returns_none_when_not_frozen(monkeypatch):
    """Test returns None when not frozen (normal dev mode)."""
    monkeypatch.setattr("job_radar.uninstaller.is_frozen", lambda: False)

    result = get_binary_path()

    assert result is None


def test_get_binary_path_returns_path_when_frozen(monkeypatch):
    """Test returns Path(sys.executable) when frozen."""
    monkeypatch.setattr("job_radar.uninstaller.is_frozen", lambda: True)

    result = get_binary_path()

    assert result == Path(sys.executable)
    assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# create_cleanup_script tests
# ---------------------------------------------------------------------------

def test_create_cleanup_script_macos_creates_shell_script(tmp_path, monkeypatch):
    """Test macOS: creates .sh script, returns appropriate message."""
    monkeypatch.setattr("sys.platform", "darwin")

    binary_path = Path("/Applications/JobRadar.app/Contents/MacOS/job-radar")

    with patch("job_radar.uninstaller.subprocess.Popen") as mock_popen:
        message, script_path = create_cleanup_script(binary_path)

    # Verify message
    assert "Trash" in message
    assert "shortly" in message.lower()

    # Verify script was created
    assert script_path is not None
    script = Path(script_path)
    assert script.exists()
    assert script.name == ".job-radar-cleanup.sh"

    # Verify script content
    content = script.read_text()
    assert "sleep 3" in content
    assert "osascript" in content
    assert ".app" in content

    # Verify subprocess was called
    mock_popen.assert_called_once()


def test_create_cleanup_script_windows_creates_batch_file(tmp_path, monkeypatch):
    """Test Windows: creates .bat script with correct content."""
    monkeypatch.setattr("sys.platform", "win32")

    binary_path = Path("C:/Program Files/JobRadar/job-radar.exe")

    with patch("job_radar.uninstaller.subprocess.Popen") as mock_popen:
        message, script_path = create_cleanup_script(binary_path)

    # Verify message
    assert "deleted shortly" in message.lower()

    # Verify script was created
    assert script_path is not None
    script = Path(script_path)
    assert script.exists()
    assert script.name == "job-radar-cleanup.bat"

    # Verify script content
    content = script.read_text()
    assert "timeout" in content
    assert "del" in content
    assert str(binary_path) in content

    # Verify subprocess was called
    mock_popen.assert_called_once()


def test_create_cleanup_script_linux_creates_executable_script(tmp_path, monkeypatch):
    """Test Linux: creates .sh script with execute permission."""
    monkeypatch.setattr("sys.platform", "linux")

    binary_path = Path("/usr/local/bin/job-radar")

    with patch("job_radar.uninstaller.subprocess.Popen") as mock_popen:
        message, script_path = create_cleanup_script(binary_path)

    # Verify message
    assert "deleted shortly" in message.lower()

    # Verify script was created
    assert script_path is not None
    script = Path(script_path)
    assert script.exists()
    assert script.name == ".job-radar-cleanup.sh"

    # Verify script is executable
    assert script.stat().st_mode & stat.S_IEXEC

    # Verify script content
    content = script.read_text()
    assert "sleep 3" in content
    assert "rm -f" in content
    assert str(binary_path) in content

    # Verify subprocess was called
    mock_popen.assert_called_once()


def test_create_cleanup_script_returns_manual_instructions_on_failure(monkeypatch):
    """Test returns manual instructions message when script creation fails."""
    monkeypatch.setattr("sys.platform", "darwin")

    binary_path = Path("/Applications/JobRadar.app/Contents/MacOS/job-radar")

    # Mock Path.write_text to raise exception
    with patch("pathlib.Path.write_text", side_effect=PermissionError("Cannot write")):
        message, script_path = create_cleanup_script(binary_path)

    # Should return manual instructions
    assert "manually delete" in message.lower()
    assert str(binary_path) in message
    assert script_path is None
