"""Tests for UX polish features (Phase 10).

Covers: progress indicators (UX-01), friendly errors (UX-02),
welcome banner (UX-03), help text (UX-04), Ctrl+C handling (UX-05).
"""
import pytest
import sys
from unittest.mock import patch, MagicMock


class TestBanner:
    """Test welcome banner display (UX-03)."""

    def test_banner_shows_version(self, capsys):
        """Banner displays version string."""
        from job_radar.banner import display_banner
        display_banner(version="1.1")
        output = capsys.readouterr().out
        assert "1.1" in output

    def test_banner_shows_profile_name(self, capsys):
        """Banner displays profile name when provided."""
        from job_radar.banner import display_banner
        display_banner(version="1.1", profile_name="Jane Doe")
        output = capsys.readouterr().out
        assert "Jane Doe" in output

    def test_banner_shows_help_hint(self, capsys):
        """Banner includes --help hint."""
        from job_radar.banner import display_banner
        display_banner(version="1.1")
        output = capsys.readouterr().out
        assert "--help" in output

    def test_banner_without_profile_name(self, capsys):
        """Banner works without profile name (first run)."""
        from job_radar.banner import display_banner
        display_banner(version="1.1")
        output = capsys.readouterr().out
        assert "1.1" in output
        # Should NOT contain "Searching for" when no name
        assert "Searching for" not in output

    def test_banner_fallback_without_pyfiglet(self, capsys):
        """Banner falls back to boxed text when pyfiglet unavailable."""
        from job_radar.banner import display_banner

        # Mock pyfiglet import to raise ImportError
        with patch.dict('sys.modules', {'pyfiglet': None}):
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs:
                       (_ for _ in ()).throw(ImportError()) if name == 'pyfiglet'
                       else __import__(name, *args, **kwargs)):
                display_banner(version="1.1", profile_name="Test User")

        output = capsys.readouterr().out
        assert "1.1" in output
        assert "Test User" in output
        assert "=" in output  # Box border character


class TestHelpText:
    """Test help text organization and content (UX-04)."""

    def test_help_has_wizard_explanation(self, capsys):
        """--help explains the interactive wizard."""
        from job_radar.search import parse_args
        with patch.object(sys, 'argv', ['job-radar', '--help']):
            with pytest.raises(SystemExit):
                parse_args()
        output = capsys.readouterr().out
        assert "wizard" in output.lower()

    def test_help_has_argument_groups(self, capsys):
        """--help shows grouped flags."""
        from job_radar.search import parse_args
        with patch.object(sys, 'argv', ['job-radar', '--help']):
            with pytest.raises(SystemExit):
                parse_args()
        output = capsys.readouterr().out
        assert "Search Options" in output
        assert "Output Options" in output
        assert "Profile Options" in output

    def test_help_has_examples(self, capsys):
        """--help includes usage examples."""
        from job_radar.search import parse_args
        with patch.object(sys, 'argv', ['job-radar', '--help']):
            with pytest.raises(SystemExit):
                parse_args()
        output = capsys.readouterr().out
        assert "Examples" in output or "examples" in output
        assert "--min-score" in output

    def test_help_one_line_descriptions(self, capsys):
        """Flag descriptions are brief (one line each)."""
        from job_radar.search import parse_args
        with patch.object(sys, 'argv', ['job-radar', '--help']):
            with pytest.raises(SystemExit):
                parse_args()
        output = capsys.readouterr().out
        # Check a few specific flags have brief help
        assert "Minimum match score" in output
        assert "Output directory" in output


class TestCtrlCHandling:
    """Test Ctrl+C graceful exit (UX-05)."""

    def test_keyboard_interrupt_exits_cleanly(self, capsys):
        """KeyboardInterrupt results in friendly message, not traceback."""
        from job_radar.__main__ import main
        # Mock search_main to raise KeyboardInterrupt
        with patch('job_radar.__main__._fix_ssl_for_frozen'):
            with patch('job_radar.search.main', side_effect=KeyboardInterrupt):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
        output = capsys.readouterr().out
        # Should have friendly message
        assert "interrupt" in output.lower() or "goodbye" in output.lower()

    def test_keyboard_interrupt_no_traceback(self, capsys):
        """Ctrl+C should never show a Python traceback."""
        from job_radar.__main__ import main
        with patch('job_radar.__main__._fix_ssl_for_frozen'):
            with patch('job_radar.search.main', side_effect=KeyboardInterrupt):
                with pytest.raises(SystemExit):
                    main()
        output = capsys.readouterr().out + capsys.readouterr().err
        assert "Traceback" not in output


class TestErrorLogging:
    """Test error logging functions (UX-02)."""

    def test_log_error_to_file_does_not_exit(self, tmp_path):
        """log_error_to_file logs but does not call sys.exit."""
        from job_radar.banner import log_error_to_file
        log_file = tmp_path / "test-error.log"
        with patch('job_radar.banner.get_log_file', return_value=log_file):
            # Should NOT raise SystemExit
            log_error_to_file("test error message", ValueError("test"))
        assert log_file.exists()
        content = log_file.read_text()
        assert "test error message" in content

    def test_log_error_and_exit_exits_with_code_1(self, tmp_path):
        """log_error_and_exit exits with code 1."""
        from job_radar.banner import log_error_and_exit
        log_file = tmp_path / "test-error.log"
        with patch('job_radar.banner.get_log_file', return_value=log_file):
            with pytest.raises(SystemExit) as exc_info:
                log_error_and_exit("fatal error")
        assert exc_info.value.code == 1

    def test_log_error_writes_traceback(self, tmp_path):
        """Error log includes traceback when exception is provided."""
        from job_radar.banner import log_error_to_file
        log_file = tmp_path / "test-error.log"
        try:
            raise ValueError("test exception for traceback")
        except ValueError as e:
            with patch('job_radar.banner.get_log_file', return_value=log_file):
                log_error_to_file("error occurred", exception=e)
        content = log_file.read_text()
        assert "ValueError" in content


class TestSourceProgress:
    """Test source-level progress tracking (UX-01)."""

    def test_source_progress_callback_fires_per_source(self):
        """Progress callback is called with correct source counts."""
        from job_radar.sources import fetch_all

        profile = {
            "target_titles": ["Python Developer"],
            "core_skills": ["Python"],
            "location": "Remote",
        }

        progress_calls = []

        def track_progress(source_name, count, total, status):
            progress_calls.append({
                "source": source_name,
                "count": count,
                "total": total,
                "status": status,
            })

        # Mock all fetchers to return empty lists quickly
        with patch('job_radar.sources.fetch_dice', return_value=[]):
            with patch('job_radar.sources.fetch_hn_hiring', return_value=[]):
                with patch('job_radar.sources.fetch_remoteok', return_value=[]):
                    with patch('job_radar.sources.fetch_weworkremotely', return_value=[]):
                        fetch_all(profile, on_source_progress=track_progress)

        # Should have called progress callback multiple times
        assert len(progress_calls) > 0

        # Check that both 'started' and 'complete' status appear
        statuses = [call["status"] for call in progress_calls]
        assert "started" in statuses
        assert "complete" in statuses

        # Check that counts are sequential (1, 2, 3, ...)
        started_calls = [c for c in progress_calls if c["status"] == "started"]
        if len(started_calls) > 1:
            for i, call in enumerate(started_calls, start=1):
                assert call["count"] == i

    def test_source_progress_started_before_complete(self):
        """'started' status fires before 'complete' for each source."""
        from job_radar.sources import fetch_all

        profile = {
            "target_titles": ["Python Developer"],
            "core_skills": ["Python"],
            "location": "Remote",
        }

        progress_events = []

        def track_progress(source_name, count, total, status):
            progress_events.append((source_name, status))

        # Mock all fetchers
        with patch('job_radar.sources.fetch_dice', return_value=[]):
            with patch('job_radar.sources.fetch_hn_hiring', return_value=[]):
                with patch('job_radar.sources.fetch_remoteok', return_value=[]):
                    with patch('job_radar.sources.fetch_weworkremotely', return_value=[]):
                        fetch_all(profile, on_source_progress=track_progress)

        # For each unique source, verify 'started' comes before 'complete'
        sources_seen = {}
        for source_name, status in progress_events:
            if source_name not in sources_seen:
                sources_seen[source_name] = []
            sources_seen[source_name].append(status)

        # Each source should have ['started', ...] pattern (started first)
        for source, statuses in sources_seen.items():
            if len(statuses) >= 2:
                assert statuses[0] == "started", f"{source} should start with 'started'"


class TestFriendlyErrors:
    """Test friendly error messages in search.py (UX-02)."""

    def test_network_error_shows_friendly_message(self, capsys, tmp_path):
        """Network errors show user-friendly message without traceback."""
        from job_radar.search import main

        # Mock profile loading to succeed
        mock_profile = {
            "name": "Test User",
            "target_titles": ["Developer"],
            "core_skills": ["Python"],
        }

        # Mock fetch_all to raise network error
        with patch.object(sys, 'argv', ['job-radar']):
            with patch('job_radar.search.load_config', return_value={}):
                with patch('job_radar.search.load_profile_with_recovery', return_value=mock_profile):
                    with patch('job_radar.search.fetch_all', side_effect=ConnectionError("Network timeout")):
                        with patch('job_radar.search.get_os_info', return_value={"os_name": "Test", "arch": "x64"}):
                            with patch('job_radar.banner.get_log_file', return_value=tmp_path / "error.log"):
                                with pytest.raises(SystemExit) as exc_info:
                                    main()
                                assert exc_info.value.code == 1

        output = capsys.readouterr().out
        # Should have friendly message about internet connection
        assert "internet" in output.lower() or "fetch" in output.lower()
        # Should NOT have Python traceback
        assert "Traceback" not in output

    def test_zero_results_shows_encouraging_message(self, capsys, tmp_path):
        """Zero results after scoring show encouraging message."""
        from job_radar.search import main

        mock_profile = {
            "name": "Test User",
            "target_titles": ["Developer"],
            "core_skills": ["Python"],
        }

        # Mock to return empty results after filtering
        with patch.object(sys, 'argv', ['job-radar']):
            with patch('job_radar.search.load_config', return_value={}):
                with patch('job_radar.search.load_profile_with_recovery', return_value=mock_profile):
                    with patch('job_radar.search.fetch_all', return_value=[]):
                        with patch('job_radar.search.get_os_info', return_value={"os_name": "Test", "arch": "x64"}):
                            with patch('job_radar.search.generate_report', return_value={
                                "html": str(tmp_path / "report.html"),
                                "markdown": str(tmp_path / "report.md"),
                                "stats": {"total": 0, "new": 0}
                            }):
                                with patch('job_radar.search.mark_seen', return_value=[]):
                                    with patch('job_radar.search.get_stats', return_value={
                                        "total_runs": 1,
                                        "total_unique_jobs_seen": 0,
                                        "avg_new_per_run_last_7": 0
                                    }):
                                        with patch('job_radar.search.open_report_in_browser', return_value={"opened": False, "reason": "no results"}):
                                            main()

        output = capsys.readouterr().out
        # Should have encouraging message about broadening search
        assert "no match" in output.lower() or "try" in output.lower() or "broaden" in output.lower()
