"""Tests for CLI update flags (--update-skills, --set-min-score, --set-titles).

Covers:
- Validator functions (comma_separated_skills, comma_separated_titles, valid_score_range)
- Handler functions (handle_update_skills, handle_set_min_score, handle_set_titles)
- Flag parsing and mutual exclusion
- Early exit behavior in main()
"""

import argparse
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from job_radar.search import (
    comma_separated_skills,
    comma_separated_titles,
    handle_set_min_score,
    handle_set_titles,
    handle_update_skills,
    parse_args,
    valid_score_range,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def profile_and_config(tmp_path):
    """Create valid profile.json and config.json in tmp_path."""
    profile_path = tmp_path / "profile.json"
    config_path = tmp_path / "config.json"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    profile_data = {
        "name": "Test User",
        "years_experience": 5,
        "level": "mid",
        "target_titles": ["Software Engineer", "Backend Developer"],
        "core_skills": ["Python", "JavaScript", "React"],
        "location": "Remote",
        "dealbreakers": ["on-site only"],
        "schema_version": 1,
    }
    config_data = {
        "min_score": 2.8,
        "new_only": True,
    }

    profile_path.write_text(json.dumps(profile_data, indent=2))
    config_path.write_text(json.dumps(config_data, indent=2))

    return profile_path, config_path, backup_dir


# ---------------------------------------------------------------------------
# 1. Validator tests
# ---------------------------------------------------------------------------


class TestCommaSeparatedSkills:
    """Tests for comma_separated_skills validator."""

    def test_valid_skills(self):
        """Standard comma-separated list parses correctly."""
        assert comma_separated_skills("python,react,typescript") == [
            "python",
            "react",
            "typescript",
        ]

    def test_with_spaces(self):
        """Whitespace around items is trimmed."""
        assert comma_separated_skills("python, react , typescript") == [
            "python",
            "react",
            "typescript",
        ]

    def test_empty_clears(self):
        """Empty string returns empty list (clearing operation)."""
        assert comma_separated_skills("") == []

    def test_commas_only_raises(self):
        """String of only commas raises ArgumentTypeError."""
        with pytest.raises(argparse.ArgumentTypeError, match="cannot be empty"):
            comma_separated_skills(",,,")

    def test_single_item(self):
        """Single item without commas works."""
        assert comma_separated_skills("python") == ["python"]

    def test_trailing_comma(self):
        """Trailing comma does not create empty items."""
        assert comma_separated_skills("python,react,") == ["python", "react"]


class TestCommaSeparatedTitles:
    """Tests for comma_separated_titles validator."""

    def test_valid_titles(self):
        """Standard comma-separated titles parse correctly."""
        assert comma_separated_titles("Backend Developer,SRE") == [
            "Backend Developer",
            "SRE",
        ]

    def test_empty_raises(self):
        """Empty string raises ArgumentTypeError (titles cannot be cleared)."""
        with pytest.raises(argparse.ArgumentTypeError, match="cannot be empty"):
            comma_separated_titles("")

    def test_commas_only_raises(self):
        """String of only commas raises ArgumentTypeError."""
        with pytest.raises(argparse.ArgumentTypeError, match="cannot be empty"):
            comma_separated_titles(",,,")

    def test_single_title(self):
        """Single title without commas works."""
        assert comma_separated_titles("SRE") == ["SRE"]

    def test_with_spaces(self):
        """Whitespace around titles is trimmed."""
        assert comma_separated_titles(" Backend Developer , SRE ") == [
            "Backend Developer",
            "SRE",
        ]


class TestValidScoreRange:
    """Tests for valid_score_range validator."""

    @pytest.mark.parametrize(
        "value,expected",
        [("3.5", 3.5), ("0.0", 0.0), ("5.0", 5.0), ("0", 0.0), ("2.8", 2.8)],
    )
    def test_valid_scores(self, value, expected):
        """Valid score values within range are accepted."""
        assert valid_score_range(value) == expected

    def test_non_numeric_raises(self):
        """Non-numeric input raises ArgumentTypeError with 'must be a number' message."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be a number"):
            valid_score_range("abc")

    def test_out_of_range_high(self):
        """Score above 5.0 raises ArgumentTypeError."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be 0.0-5.0"):
            valid_score_range("7.0")

    def test_out_of_range_negative(self):
        """Negative score raises ArgumentTypeError."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be 0.0-5.0"):
            valid_score_range("-1.0")


# ---------------------------------------------------------------------------
# 2. Handler tests
# ---------------------------------------------------------------------------


class TestHandleUpdateSkills:
    """Tests for handle_update_skills handler."""

    def test_replaces_list(self, profile_and_config, capsys):
        """Skills list is replaced in profile.json on success."""
        profile_path, _, backup_dir = profile_and_config

        with patch(
            "job_radar.profile_manager.get_backup_dir", return_value=backup_dir
        ):
            handle_update_skills(["python", "react"], str(profile_path))

        # Verify profile was updated
        updated = json.loads(profile_path.read_text())
        assert updated["core_skills"] == ["python", "react"]

        output = capsys.readouterr().out
        assert "Skills updated" in output
        assert "python, react" in output

    def test_clears_list_validation_error(self, profile_and_config, capsys):
        """Clearing skills with empty list fails validation (core_skills must be non-empty)."""
        profile_path, _, backup_dir = profile_and_config

        with patch(
            "job_radar.profile_manager.get_backup_dir", return_value=backup_dir
        ):
            with pytest.raises(SystemExit) as exc_info:
                handle_update_skills([], str(profile_path))

        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "Error" in output

    def test_no_profile(self, tmp_path, capsys):
        """Missing profile exits with error and guidance message."""
        fake_path = str(tmp_path / "nonexistent.json")

        with pytest.raises(SystemExit) as exc_info:
            handle_update_skills(["python"], fake_path)

        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "No profile found" in output
        assert "Run 'job-radar' first" in output

    def test_shows_old_and_new(self, profile_and_config, capsys):
        """Output shows both old and new values for diff."""
        profile_path, _, backup_dir = profile_and_config

        with patch(
            "job_radar.profile_manager.get_backup_dir", return_value=backup_dir
        ):
            handle_update_skills(["go", "rust"], str(profile_path))

        output = capsys.readouterr().out
        # Old skills were Python, JavaScript, React
        assert "Python, JavaScript, React" in output
        assert "go, rust" in output


class TestHandleSetMinScore:
    """Tests for handle_set_min_score handler."""

    def test_updates_config(self, profile_and_config, capsys):
        """min_score is updated in config.json."""
        _, config_path, _ = profile_and_config

        handle_set_min_score(3.5, str(config_path))

        updated = json.loads(config_path.read_text())
        assert updated["min_score"] == 3.5

        output = capsys.readouterr().out
        assert "Min score updated to 3.5" in output
        assert "Jobs scoring below 3.5 will be hidden" in output

    def test_no_config_creates_new(self, tmp_path, capsys):
        """Creates new config.json when file doesn't exist."""
        config_path = tmp_path / "config.json"

        handle_set_min_score(4.0, str(config_path))

        assert config_path.exists()

        updated = json.loads(config_path.read_text())
        assert updated["min_score"] == 4.0

        output = capsys.readouterr().out
        assert "Min score updated to 4.0" in output

    def test_shows_old_and_new(self, profile_and_config, capsys):
        """Output shows old and new score values."""
        _, config_path, _ = profile_and_config

        handle_set_min_score(3.5, str(config_path))

        output = capsys.readouterr().out
        assert "2.8" in output  # old value
        assert "3.5" in output  # new value

    def test_default_old_score(self, tmp_path, capsys):
        """When no config exists, old score defaults to 2.8."""
        config_path = tmp_path / "config.json"

        handle_set_min_score(3.5, str(config_path))

        output = capsys.readouterr().out
        assert "2.8" in output  # default old value


class TestHandleSetTitles:
    """Tests for handle_set_titles handler."""

    def test_replaces_list(self, profile_and_config, capsys):
        """Titles list is replaced in profile.json on success."""
        profile_path, _, backup_dir = profile_and_config

        with patch(
            "job_radar.profile_manager.get_backup_dir", return_value=backup_dir
        ):
            handle_set_titles(["SRE", "DevOps"], str(profile_path))

        updated = json.loads(profile_path.read_text())
        assert updated["target_titles"] == ["SRE", "DevOps"]

        output = capsys.readouterr().out
        assert "Titles updated" in output

    def test_no_profile(self, tmp_path, capsys):
        """Missing profile exits with error and guidance message."""
        fake_path = str(tmp_path / "nonexistent.json")

        with pytest.raises(SystemExit) as exc_info:
            handle_set_titles(["SRE"], fake_path)

        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "No profile found" in output
        assert "Run 'job-radar' first" in output

    def test_shows_old_and_new(self, profile_and_config, capsys):
        """Output shows both old and new title values."""
        profile_path, _, backup_dir = profile_and_config

        with patch(
            "job_radar.profile_manager.get_backup_dir", return_value=backup_dir
        ):
            handle_set_titles(["SRE", "Platform Engineer"], str(profile_path))

        output = capsys.readouterr().out
        # Old titles were Software Engineer, Backend Developer
        assert "Software Engineer, Backend Developer" in output
        assert "SRE, Platform Engineer" in output


# ---------------------------------------------------------------------------
# 3. Flag parsing tests
# ---------------------------------------------------------------------------


class TestFlagParsing:
    """Tests for update flags in parse_args."""

    def test_parse_update_skills(self):
        """--update-skills flag parses comma-separated skills list."""
        with patch("sys.argv", ["job-radar", "--update-skills", "python,react"]):
            args = parse_args()
        assert args.update_skills == ["python", "react"]

    def test_parse_set_min_score(self):
        """--set-min-score flag parses float value."""
        with patch("sys.argv", ["job-radar", "--set-min-score", "3.5"]):
            args = parse_args()
        assert args.set_min_score == 3.5

    def test_parse_set_titles(self):
        """--set-titles flag parses comma-separated titles list."""
        with patch("sys.argv", ["job-radar", "--set-titles", "Backend,SRE"]):
            args = parse_args()
        assert args.set_titles == ["Backend", "SRE"]

    def test_no_update_flags_defaults_none(self):
        """Without update flags, all update args are None."""
        with patch("sys.argv", ["job-radar"]):
            args = parse_args()
        assert args.update_skills is None
        assert args.set_min_score is None
        assert args.set_titles is None


# ---------------------------------------------------------------------------
# 4. Mutual exclusion tests
# ---------------------------------------------------------------------------


class TestMutualExclusion:
    """Tests for mutual exclusion of update flags."""

    def test_update_flags_mutually_exclusive(self):
        """Using two update flags together causes argparse error."""
        with patch(
            "sys.argv",
            ["job-radar", "--update-skills", "python", "--set-min-score", "3.5"],
        ):
            with pytest.raises(SystemExit) as exc_info:
                parse_args()
            assert exc_info.value.code == 2  # argparse error exit code

    def test_update_skills_with_set_titles_exclusive(self):
        """Using --update-skills and --set-titles together causes argparse error."""
        with patch(
            "sys.argv",
            [
                "job-radar",
                "--update-skills",
                "python",
                "--set-titles",
                "SRE",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                parse_args()
            assert exc_info.value.code == 2

    def test_update_flag_with_view_profile_rejected(self, capsys):
        """--update-skills with --view-profile is rejected in main()."""
        with patch(
            "sys.argv",
            ["job-radar", "--update-skills", "python", "--view-profile"],
        ):
            with patch("job_radar.search.load_config", return_value={}):
                with pytest.raises(SystemExit) as exc_info:
                    from job_radar.search import main

                    main()
                assert exc_info.value.code == 1

        output = capsys.readouterr().out
        assert "Update flags cannot be used with --view-profile" in output

    def test_set_min_score_with_edit_profile_rejected(self, capsys):
        """--set-min-score with --edit-profile is rejected in main()."""
        with patch(
            "sys.argv",
            ["job-radar", "--set-min-score", "3.5", "--edit-profile"],
        ):
            with patch("job_radar.search.load_config", return_value={}):
                with pytest.raises(SystemExit) as exc_info:
                    from job_radar.search import main

                    main()
                assert exc_info.value.code == 1

        output = capsys.readouterr().out
        assert "Update flags cannot be used with" in output


# ---------------------------------------------------------------------------
# 5. Integration-style tests
# ---------------------------------------------------------------------------


class TestUpdateExitsWithoutSearch:
    """Verify update flags exit before any search flow."""

    def test_update_skills_exits_without_search(self, profile_and_config):
        """When --update-skills is set, main() never reaches fetch_all."""
        profile_path, _, backup_dir = profile_and_config

        with patch(
            "sys.argv",
            [
                "job-radar",
                "--update-skills",
                "python,go",
                "--profile",
                str(profile_path),
            ],
        ):
            with patch("job_radar.search.load_config", return_value={}):
                with patch(
                    "job_radar.profile_manager.get_backup_dir",
                    return_value=backup_dir,
                ):
                    with patch("job_radar.search.fetch_all") as mock_fetch:
                        with pytest.raises(SystemExit) as exc_info:
                            from job_radar.search import main

                            main()

        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        # fetch_all should never be called
        mock_fetch.assert_not_called()

    def test_set_min_score_exits_without_search(self, profile_and_config):
        """When --set-min-score is set, main() never reaches fetch_all."""
        _, config_path, _ = profile_and_config

        with patch(
            "sys.argv",
            [
                "job-radar",
                "--set-min-score",
                "4.0",
                "--config",
                str(config_path),
            ],
        ):
            with patch("job_radar.search.load_config", return_value={}):
                with patch("job_radar.search.fetch_all") as mock_fetch:
                    with pytest.raises(SystemExit) as exc_info:
                        from job_radar.search import main

                        main()

        assert exc_info.value.code == 0
        mock_fetch.assert_not_called()
