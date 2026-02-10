"""Tests for browser utilities and headless environment detection."""

import pytest
from pathlib import Path
from job_radar.browser import is_headless_environment, open_report_in_browser
from job_radar.config import KNOWN_KEYS


# ---------------------------------------------------------------------------
# Headless environment detection tests
# ---------------------------------------------------------------------------

def test_headless_ci_env(monkeypatch):
    """Test that CI=true is detected as headless environment."""
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("BUILD_ID", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")  # Set display to ensure CI flag is reason

    assert is_headless_environment() is True


def test_headless_github_actions(monkeypatch):
    """Test that GITHUB_ACTIONS=true is detected as headless environment."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("BUILD_ID", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")

    assert is_headless_environment() is True


def test_headless_jenkins(monkeypatch):
    """Test that BUILD_ID present is detected as Jenkins headless environment."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("BUILD_ID", "123")
    monkeypatch.setenv("DISPLAY", ":0")

    assert is_headless_environment() is True


def test_headless_no_display_linux(monkeypatch):
    """Test that Linux without DISPLAY is detected as headless."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("BUILD_ID", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr("os.name", "posix")
    monkeypatch.setattr("sys.platform", "linux")

    assert is_headless_environment() is True


def test_not_headless_macos_no_display(monkeypatch):
    """Test that macOS without DISPLAY is NOT headless (macOS doesn't use X11)."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("BUILD_ID", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr("os.name", "posix")
    monkeypatch.setattr("sys.platform", "darwin")

    assert is_headless_environment() is False


def test_not_headless_normal_desktop(monkeypatch):
    """Test that normal desktop environment with DISPLAY is not headless."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("BUILD_ID", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")

    assert is_headless_environment() is False


# ---------------------------------------------------------------------------
# Browser opening tests
# ---------------------------------------------------------------------------

def test_open_disabled_by_user():
    """Test that auto_open=False disables browser opening."""
    result = open_report_in_browser("/tmp/test.html", auto_open=False)

    assert result["opened"] is False
    assert "disabled" in result["reason"].lower()


def test_open_in_headless_skips(monkeypatch):
    """Test that headless environment skips browser opening."""
    monkeypatch.setenv("CI", "true")

    result = open_report_in_browser("/tmp/test.html", auto_open=True)

    assert result["opened"] is False
    assert "headless" in result["reason"].lower()


def test_open_success(monkeypatch, tmp_path):
    """Test successful browser opening."""
    # Create a real HTML file
    html_file = tmp_path / "test_report.html"
    html_file.write_text("<html><body>Test</body></html>")

    # Clear headless environment variables
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("BUILD_ID", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")

    # Mock webbrowser.open to return True
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: True)

    result = open_report_in_browser(str(html_file), auto_open=True)

    assert result["opened"] is True
    assert result["reason"] == ""


def test_open_browser_failure(monkeypatch, tmp_path):
    """Test that webbrowser.open returning False is handled gracefully."""
    # Create a real HTML file
    html_file = tmp_path / "test_report.html"
    html_file.write_text("<html><body>Test</body></html>")

    # Clear headless environment variables
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("BUILD_ID", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")

    # Mock webbrowser.open to return False
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: False)

    result = open_report_in_browser(str(html_file), auto_open=True)

    assert result["opened"] is False
    assert "not available" in result["reason"].lower()


def test_open_browser_exception(monkeypatch, tmp_path):
    """Test that exceptions during browser opening are handled gracefully."""
    # Create a real HTML file
    html_file = tmp_path / "test_report.html"
    html_file.write_text("<html><body>Test</body></html>")

    # Clear headless environment variables
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("BUILD_ID", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")

    # Mock webbrowser.open to raise OSError
    import webbrowser
    def mock_open(url):
        raise OSError("Browser not found")
    monkeypatch.setattr(webbrowser, "open", mock_open)

    result = open_report_in_browser(str(html_file), auto_open=True)

    assert result["opened"] is False
    assert "error" in result["reason"].lower()


# ---------------------------------------------------------------------------
# Config integration tests
# ---------------------------------------------------------------------------

def test_config_recognizes_auto_open_browser():
    """Test that auto_open_browser is a recognized config key."""
    assert "auto_open_browser" in KNOWN_KEYS


def test_config_known_keys_count():
    """Test that KNOWN_KEYS has exactly 5 keys as expected."""
    # min_score, new_only, output, profile_path, auto_open_browser
    assert len(KNOWN_KEYS) == 5
