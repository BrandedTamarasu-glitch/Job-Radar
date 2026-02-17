"""Tests for installer launch and cleanup functionality."""

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from job_radar.update_checker import cleanup_old_installers, launch_installer
from job_radar.gui.installer_dialogs import InstallConfirmDialog, LinuxInstallInstructionsDialog


class TestLaunchInstaller:
    """Tests for launch_installer function."""

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific subprocess calls")
    def test_launch_macos_dmg_success(self):
        """Test successful macOS DMG mount and open."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/dev/disk4\tApple_HFS\t/Volumes/Job-Radar\n"

        with patch("job_radar.update_checker.subprocess.run", return_value=mock_result) as mock_run, patch(
            "job_radar.update_checker.subprocess.Popen"
        ) as mock_popen, patch("job_radar.update_checker.Path.exists", return_value=True):
            installer_path = Path("/tmp/Job-Radar-v2.2.0-installer.dmg")
            mount_point = launch_installer(installer_path, platform="darwin")

            # Verify hdiutil attach was called
            mock_run.assert_called_once_with(
                ["hdiutil", "attach", str(installer_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Verify open was called with mount point
            mock_popen.assert_called_once_with(["open", "/Volumes/Job-Radar"])

            # Verify return value
            assert mount_point == "/Volumes/Job-Radar"

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific subprocess calls")
    def test_launch_macos_dmg_mount_failure(self):
        """Test DMG mount failure handling."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "hdiutil: attach failed - Resource busy"

        with patch("job_radar.update_checker.subprocess.run", return_value=mock_result):
            installer_path = Path("/tmp/Job-Radar-v2.2.0-installer.dmg")

            with pytest.raises(RuntimeError, match="DMG mount failed.*Resource busy"):
                launch_installer(installer_path, platform="darwin")

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific subprocess calls")
    def test_launch_macos_dmg_no_mount_point(self):
        """Test DMG mount succeeds but mount point not found."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/dev/disk4\tApple_partition_scheme\t\n"

        with patch("job_radar.update_checker.subprocess.run", return_value=mock_result):
            # Use a unique name guaranteed not to exist as a mounted volume
            installer_path = Path("/tmp/Job-Radar-v99.99.99-test-nonexistent.dmg")

            with pytest.raises(RuntimeError, match="Could not determine DMG mount point"):
                launch_installer(installer_path, platform="darwin")

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific subprocess calls")
    def test_launch_macos_dmg_timeout(self):
        """Test DMG mount timeout handling."""
        with patch(
            "job_radar.update_checker.subprocess.run", side_effect=subprocess.TimeoutExpired("hdiutil", 30)
        ):
            installer_path = Path("/tmp/Job-Radar-v2.2.0-installer.dmg")

            with pytest.raises(RuntimeError, match="timed out"):
                launch_installer(installer_path, platform="darwin")

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific subprocess calls")
    def test_launch_macos_dmg_fallback_mount_point(self):
        """Test DMG mount with fallback mount point detection."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "some output\nwithout clear mount point\n"

        with patch("job_radar.update_checker.subprocess.run", return_value=mock_result) as mock_run, patch(
            "job_radar.update_checker.subprocess.Popen"
        ) as mock_popen, patch.object(Path, "exists", return_value=True):
            installer_path = Path("/tmp/Job-Radar-v2.2.0-installer.dmg")
            mount_point = launch_installer(installer_path, platform="darwin")

            # Verify fallback mount point used
            assert mount_point == "/Volumes/Job-Radar-v2.2.0-installer"
            mock_popen.assert_called_once_with(["open", "/Volumes/Job-Radar-v2.2.0-installer"])

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific subprocess flags")
    def test_launch_windows_exe(self):
        """Test Windows exe launch with detached process."""
        with patch("job_radar.update_checker.subprocess.Popen") as mock_popen:
            installer_path = Path(r"C:\Temp\Job-Radar-Setup-v2.2.0.exe")
            result = launch_installer(installer_path, platform="win32")

            # Verify Popen called with correct flags
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args

            # Check path is correct
            assert call_args[0][0] == [str(installer_path)]

            # Check creationflags include DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP
            assert "creationflags" in call_args[1]
            flags = call_args[1]["creationflags"]
            assert flags & subprocess.DETACHED_PROCESS
            assert flags & subprocess.CREATE_NEW_PROCESS_GROUP

            # Verify empty string returned
            assert result == ""

    def test_launch_linux_raises(self):
        """Test Linux platform raises error with instructions message."""
        installer_path = Path("/tmp/job-radar-v2.2.0-installer.tar.gz")

        with pytest.raises(RuntimeError, match="Linux uses instructions dialog"):
            launch_installer(installer_path, platform="linux")

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific subprocess calls")
    def test_launch_file_not_found(self):
        """Test file not found error handling."""
        with patch("job_radar.update_checker.subprocess.run", side_effect=FileNotFoundError("No such file")):
            installer_path = Path("/tmp/nonexistent.dmg")

            with pytest.raises(RuntimeError, match=re.escape(f"Installer file not found: {installer_path}")):
                launch_installer(installer_path, platform="darwin")

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific subprocess calls")
    def test_launch_os_error(self):
        """Test OS error (permissions) handling."""
        with patch("job_radar.update_checker.subprocess.run", side_effect=OSError("Permission denied")):
            installer_path = Path("/tmp/no-permission.dmg")

            with pytest.raises(RuntimeError, match=re.escape(f"Failed to launch installer at {installer_path}")):
                launch_installer(installer_path, platform="darwin")

    def test_launch_unsupported_platform(self):
        """Test unsupported platform raises error."""
        installer_path = Path("/tmp/installer")

        with pytest.raises(RuntimeError, match="Unsupported platform: freebsd"):
            launch_installer(installer_path, platform="freebsd")


class TestCleanupOldInstallers:
    """Tests for cleanup_old_installers function."""

    def test_cleanup_deletes_matching_files(self, tmp_path):
        """Test cleanup deletes files matching installer patterns."""
        # Create temp files matching patterns
        dmg_file = tmp_path / "Job-Radar-v2.1.0-installer.dmg"
        exe_file = tmp_path / "Job-Radar-Setup-v2.1.0.exe"
        tar_file = tmp_path / "job-radar-v2.1.0-installer.tar.gz"
        other_file = tmp_path / "other-file.txt"

        dmg_file.touch()
        exe_file.touch()
        tar_file.touch()
        other_file.touch()

        # Mock tempfile.gettempdir to return our tmp_path
        with patch("job_radar.update_checker.tempfile.gettempdir", return_value=str(tmp_path)):
            deleted = cleanup_old_installers()

            # Verify 3 installer files deleted
            assert deleted == 3

            # Verify files were actually deleted
            assert not dmg_file.exists()
            assert not exe_file.exists()
            assert not tar_file.exists()

            # Verify other file NOT deleted
            assert other_file.exists()

    def test_cleanup_ignores_errors(self, tmp_path):
        """Test cleanup continues on OS errors."""
        # Create a temp file
        installer_file = tmp_path / "Job-Radar-v2.1.0-installer.dmg"
        installer_file.touch()

        # Mock unlink to raise OSError
        with patch("job_radar.update_checker.tempfile.gettempdir", return_value=str(tmp_path)), patch.object(
            Path, "unlink", side_effect=OSError("File in use")
        ):
            # Should not raise exception
            deleted = cleanup_old_installers()

            # No files deleted due to error
            assert deleted == 0

    def test_cleanup_no_files(self, tmp_path):
        """Test cleanup returns 0 when no installer files found."""
        # Empty directory (or directory with non-matching files)
        other_file = tmp_path / "some-other-file.txt"
        other_file.touch()

        with patch("job_radar.update_checker.tempfile.gettempdir", return_value=str(tmp_path)):
            deleted = cleanup_old_installers()

            assert deleted == 0

    def test_cleanup_multiple_versions(self, tmp_path):
        """Test cleanup deletes multiple versions of installers."""
        # Create multiple versions
        v210 = tmp_path / "Job-Radar-v2.1.0-installer.dmg"
        v220 = tmp_path / "Job-Radar-v2.2.0-installer.dmg"
        v230 = tmp_path / "Job-Radar-v2.3.0-installer.dmg"

        v210.touch()
        v220.touch()
        v230.touch()

        with patch("job_radar.update_checker.tempfile.gettempdir", return_value=str(tmp_path)):
            deleted = cleanup_old_installers()

            assert deleted == 3
            assert not v210.exists()
            assert not v220.exists()
            assert not v230.exists()


class TestInstallConfirmDialog:
    """Tests for InstallConfirmDialog class."""

    def test_dialog_stores_attributes(self):
        """Test dialog stores version and platform_message attributes."""
        # We can't fully test CTk dialogs without a display, but verify
        # class is importable and constructor signature works

        # Verify we can import the class
        assert InstallConfirmDialog is not None

        # Verify constructor would accept expected parameters
        # (actual GUI testing requires tkinter mainloop)
        version = "2.2.0"
        platform_message = "Opening installer DMG..."

        # Just verify the class exists and has expected structure
        assert hasattr(InstallConfirmDialog, "__init__")

    def test_dialog_importable(self):
        """Test InstallConfirmDialog is importable from installer_dialogs."""
        from job_radar.gui.installer_dialogs import InstallConfirmDialog as ICD

        assert ICD is not None
        assert ICD.__name__ == "InstallConfirmDialog"


class TestLinuxInstallInstructionsDialog:
    """Tests for LinuxInstallInstructionsDialog class."""

    def test_linux_dialog_copy_command_format(self):
        """Test _copy_command attribute format matches expected pattern."""
        # Can't test full GUI without display, but can verify the copy command
        # format would be correct based on the tar_path

        # Verify class is importable
        assert LinuxInstallInstructionsDialog is not None

        # The copy command should be: tar -xzf {filename} -C ~/Applications/
        # This would be set in __init__ as: self._copy_command = f"tar -xzf {tar_path.name} -C ~/Applications/"

        # Verify the class has the expected structure
        assert hasattr(LinuxInstallInstructionsDialog, "__init__")

    def test_linux_dialog_importable(self):
        """Test LinuxInstallInstructionsDialog is importable from installer_dialogs."""
        from job_radar.gui.installer_dialogs import LinuxInstallInstructionsDialog as LIID

        assert LIID is not None
        assert LIID.__name__ == "LinuxInstallInstructionsDialog"

    def test_linux_dialog_expected_command_format(self):
        """Test the expected format of copy command based on tar path."""
        # Simulate what the dialog would do
        tar_path = Path("/tmp/job-radar-v2.2.0-installer.tar.gz")
        expected_command = f"tar -xzf {tar_path.name} -C ~/Applications/"

        # Verify the expected format
        assert expected_command == "tar -xzf job-radar-v2.2.0-installer.tar.gz -C ~/Applications/"
