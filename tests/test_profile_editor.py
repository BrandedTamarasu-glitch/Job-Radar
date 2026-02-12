"""Tests for profile_editor module and CLI integration.

Covers:
- Menu building (field choices, current values, done option, category separators)
- Value formatting for diff display
- Diff preview and confirmation flow
- Field editing (text, number, boolean, list)
- Validator reuse verification
- CLI flag recognition (--edit-profile in parse_args)
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from questionary import Choice, Separator

from job_radar.profile_editor import (
    CONFIG_FIELDS,
    FIELD_VALIDATORS,
    PROFILE_FIELDS,
    _build_field_choices,
    _format_value_for_diff,
    _show_diff_and_confirm,
)
from job_radar.search import parse_args


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
        "profile_path": str(profile_path),
    }

    profile_path.write_text(json.dumps(profile_data, indent=2))
    config_path.write_text(json.dumps(config_data, indent=2))

    return profile_path, config_path, backup_dir


@pytest.fixture
def sample_profile():
    """Return a sample profile dict without writing to disk."""
    return {
        "name": "Test User",
        "years_experience": 5,
        "level": "mid",
        "target_titles": ["Software Engineer", "Backend Developer"],
        "core_skills": ["Python", "JavaScript", "React"],
        "location": "Remote",
        "dealbreakers": ["on-site only"],
        "schema_version": 1,
    }


@pytest.fixture
def sample_config():
    """Return a sample config dict."""
    return {
        "min_score": 2.8,
        "new_only": True,
    }


# ---------------------------------------------------------------------------
# Menu Building Tests
# ---------------------------------------------------------------------------


class TestBuildFieldChoices:
    """Test _build_field_choices menu construction."""

    def test_build_field_choices_includes_all_fields(self, sample_profile, sample_config):
        """All 8 editable fields appear as Choice objects."""
        choices = _build_field_choices(sample_profile, sample_config)
        choice_values = [c.value for c in choices if isinstance(c, Choice)]

        # All profile fields
        for key in PROFILE_FIELDS:
            assert key in choice_values, f"Missing profile field: {key}"

        # All config fields
        for key in CONFIG_FIELDS:
            assert key in choice_values, f"Missing config field: {key}"

        # Plus the "done" option
        assert "done" in choice_values

    def test_build_field_choices_shows_current_values(self, sample_profile, sample_config):
        """Menu choices contain current values in their title text."""
        choices = _build_field_choices(sample_profile, sample_config)
        choice_titles = {
            c.value: c.title for c in choices if isinstance(c, Choice) and c.value != "done"
        }

        assert "Test User" in choice_titles["name"]
        assert "5 years" in choice_titles["years_experience"]
        assert "Remote" in choice_titles["location"]
        assert "3 items" in choice_titles["core_skills"]
        assert "2 items" in choice_titles["target_titles"]
        assert "2.8" in choice_titles["min_score"]
        assert "Yes" in choice_titles["new_only"]

    def test_build_field_choices_includes_done_option(self, sample_profile, sample_config):
        """Last non-separator choice has value 'done'."""
        choices = _build_field_choices(sample_profile, sample_config)
        # Get the last Choice object (not Separator)
        real_choices = [c for c in choices if isinstance(c, Choice)]
        assert real_choices[-1].value == "done"
        assert "Done" in real_choices[-1].title

    def test_build_field_choices_has_category_separators(self, sample_profile, sample_config):
        """Separator objects exist for IDENTITY, SKILLS, FILTERS, PREFERENCES."""
        choices = _build_field_choices(sample_profile, sample_config)
        separator_texts = [
            c.line for c in choices if isinstance(c, Separator)
        ]
        separator_str = " ".join(separator_texts)

        assert "IDENTITY" in separator_str
        assert "SKILLS" in separator_str
        assert "FILTERS" in separator_str
        assert "PREFERENCES" in separator_str


# ---------------------------------------------------------------------------
# Value Formatting Tests
# ---------------------------------------------------------------------------


class TestFormatValueForDiff:
    """Test _format_value_for_diff for various types."""

    def test_format_value_for_diff_list(self):
        """List ['a', 'b'] formats as 'a, b'."""
        assert _format_value_for_diff(["a", "b"]) == "a, b"

    def test_format_value_for_diff_empty_list(self):
        """Empty list formats as '(empty)'."""
        assert _format_value_for_diff([]) == "(empty)"

    def test_format_value_for_diff_none(self):
        """None formats as '(not set)'."""
        assert _format_value_for_diff(None) == "(not set)"

    def test_format_value_for_diff_empty_string(self):
        """Empty string formats as '(not set)'."""
        assert _format_value_for_diff("") == "(not set)"

    def test_format_value_for_diff_number(self):
        """2.8 formats as '2.8'."""
        assert _format_value_for_diff(2.8) == "2.8"
        assert _format_value_for_diff(5) == "5"

    def test_format_value_for_diff_bool(self):
        """True formats as 'Yes', False formats as 'No'."""
        assert _format_value_for_diff(True) == "Yes"
        assert _format_value_for_diff(False) == "No"


# ---------------------------------------------------------------------------
# Diff and Confirmation Tests
# ---------------------------------------------------------------------------


class TestShowDiffAndConfirm:
    """Test _show_diff_and_confirm diff display and confirmation."""

    @patch("job_radar.profile_editor.questionary")
    def test_show_diff_and_confirm_approved(self, mock_questionary, capsys):
        """When user confirms, returns True."""
        mock_confirm = Mock()
        mock_confirm.ask.return_value = True
        mock_questionary.confirm.return_value = mock_confirm

        result = _show_diff_and_confirm("name", "Old Name", "New Name")
        assert result is True

    @patch("job_radar.profile_editor.questionary")
    def test_show_diff_and_confirm_declined(self, mock_questionary, capsys):
        """When user declines, returns False and prints 'Change discarded'."""
        mock_confirm = Mock()
        mock_confirm.ask.return_value = False
        mock_questionary.confirm.return_value = mock_confirm

        result = _show_diff_and_confirm("name", "Old Name", "New Name")
        assert result is False

        output = capsys.readouterr().out
        assert "Change discarded" in output

    @patch("job_radar.profile_editor.questionary")
    def test_show_diff_and_confirm_displays_old_new(self, mock_questionary, capsys):
        """Diff output contains 'Old:' and 'New:' labels."""
        mock_confirm = Mock()
        mock_confirm.ask.return_value = True
        mock_questionary.confirm.return_value = mock_confirm

        _show_diff_and_confirm("name", "Alice", "Bob")
        output = capsys.readouterr().out

        assert "Old:" in output
        assert "New:" in output
        assert "Alice" in output
        assert "Bob" in output


# ---------------------------------------------------------------------------
# Editor Integration Tests (mock questionary)
# ---------------------------------------------------------------------------


class TestEditTextField:
    """Test text field editing with mocked prompts."""

    @patch("job_radar.profile_editor.questionary")
    def test_edit_text_field_saves_on_confirm(
        self, mock_questionary, profile_and_config
    ):
        """Text field edit saves when user confirms."""
        from job_radar.profile_editor import _edit_text_field

        profile_path, config_path, _ = profile_and_config

        # Mock text input
        mock_text = Mock()
        mock_text.ask.return_value = "Updated Name"
        mock_questionary.text.return_value = mock_text

        # Mock confirmation
        mock_confirm = Mock()
        mock_confirm.ask.return_value = True
        mock_questionary.confirm.return_value = mock_confirm

        profile_data = json.loads(profile_path.read_text())
        result = _edit_text_field("name", profile_data, profile_path)

        assert result is True
        saved = json.loads(profile_path.read_text())
        assert saved["name"] == "Updated Name"

    @patch("job_radar.profile_editor.questionary")
    def test_edit_text_field_discards_on_decline(
        self, mock_questionary, profile_and_config
    ):
        """Text field edit discards when user declines confirmation."""
        from job_radar.profile_editor import _edit_text_field

        profile_path, config_path, _ = profile_and_config

        mock_text = Mock()
        mock_text.ask.return_value = "Should Not Save"
        mock_questionary.text.return_value = mock_text

        mock_confirm = Mock()
        mock_confirm.ask.return_value = False
        mock_questionary.confirm.return_value = mock_confirm

        profile_data = json.loads(profile_path.read_text())
        result = _edit_text_field("name", profile_data, profile_path)

        assert result is False
        saved = json.loads(profile_path.read_text())
        assert saved["name"] == "Test User"  # unchanged


class TestEditListField:
    """Test list field editing with add items submenu."""

    @patch("job_radar.profile_editor.questionary")
    def test_edit_list_field_add_items(
        self, mock_questionary, profile_and_config
    ):
        """Adding items to a list field saves correctly."""
        from job_radar.profile_editor import _edit_list_field

        profile_path, config_path, _ = profile_and_config

        # Mock select -> "Add items"
        mock_select = Mock()
        mock_select.ask.return_value = "Add items"
        mock_questionary.select.return_value = mock_select

        # Mock text input for new items
        mock_text = Mock()
        mock_text.ask.return_value = "TypeScript, Go"
        mock_questionary.text.return_value = mock_text

        # Mock confirmation
        mock_confirm = Mock()
        mock_confirm.ask.return_value = True
        mock_questionary.confirm.return_value = mock_confirm

        profile_data = json.loads(profile_path.read_text())
        result = _edit_list_field("core_skills", profile_data, profile_path)

        assert result is True
        saved = json.loads(profile_path.read_text())
        assert "TypeScript" in saved["core_skills"]
        assert "Go" in saved["core_skills"]
        # Original items still present
        assert "Python" in saved["core_skills"]


class TestEditBooleanField:
    """Test boolean field editing."""

    @patch("job_radar.profile_editor.questionary")
    def test_edit_boolean_field_saves_config(
        self, mock_questionary, profile_and_config
    ):
        """Boolean field toggle saves to config.json."""
        from job_radar.profile_editor import _edit_boolean_field

        profile_path, config_path, _ = profile_and_config

        # Mock confirm for new value
        mock_confirm_new = Mock()
        mock_confirm_new.ask.return_value = False  # Toggle from True to False

        # Mock confirm for diff approval
        mock_confirm_approve = Mock()
        mock_confirm_approve.ask.return_value = True

        mock_questionary.confirm.side_effect = [
            mock_confirm_new,      # new_only value
            mock_confirm_approve,  # apply this change?
        ]

        config_data = json.loads(config_path.read_text())
        result = _edit_boolean_field("new_only", config_data, config_path)

        assert result is True
        saved = json.loads(config_path.read_text())
        assert saved["new_only"] is False


# ---------------------------------------------------------------------------
# Validator Reuse Test
# ---------------------------------------------------------------------------


class TestValidatorReuse:
    """Test that validators are imported from wizard, not duplicated."""

    def test_validators_imported_not_duplicated(self):
        """profile_editor has no Validator class definitions -- only imports from wizard."""
        import inspect
        import job_radar.profile_editor as pe_module

        source = inspect.getsource(pe_module)

        # Should NOT define validator classes
        assert "class NonEmptyValidator" not in source
        assert "class CommaSeparatedValidator" not in source
        assert "class ScoreValidator" not in source
        assert "class YearsExperienceValidator" not in source
        assert "class CompensationValidator" not in source

        # Should import them from wizard
        assert "from .wizard import" in source

    def test_field_validators_reference_wizard_classes(self):
        """FIELD_VALIDATORS dict values are instances of wizard validators."""
        from job_radar.wizard import (
            NonEmptyValidator,
            CommaSeparatedValidator,
            ScoreValidator,
            YearsExperienceValidator,
        )

        assert isinstance(FIELD_VALIDATORS["name"], NonEmptyValidator)
        assert isinstance(FIELD_VALIDATORS["years_experience"], YearsExperienceValidator)
        assert isinstance(FIELD_VALIDATORS["core_skills"], CommaSeparatedValidator)
        assert isinstance(FIELD_VALIDATORS["target_titles"], CommaSeparatedValidator)
        assert isinstance(FIELD_VALIDATORS["min_score"], ScoreValidator)


# ---------------------------------------------------------------------------
# CLI Integration Tests
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    """Test CLI flag recognition and help text."""

    def test_edit_profile_flag_exists(self, monkeypatch):
        """parse_args() recognizes --edit-profile as boolean flag."""
        monkeypatch.setattr(sys, "argv", ["prog", "--edit-profile"])
        args = parse_args()
        assert args.edit_profile is True

    def test_edit_profile_default_false(self, monkeypatch):
        """--edit-profile defaults to False when not specified."""
        monkeypatch.setattr(sys, "argv", ["prog"])
        args = parse_args()
        assert args.edit_profile is False

    def test_help_text_includes_edit_profile(self, monkeypatch, capsys):
        """--help output contains --edit-profile."""
        monkeypatch.setattr(sys, "argv", ["prog", "--help"])
        with pytest.raises(SystemExit) as exc_info:
            parse_args()
        assert exc_info.value.code == 0

        output = capsys.readouterr().out
        assert "--edit-profile" in output
        assert "Edit profile fields interactively" in output

    def test_help_documents_profile_management_edit(self, monkeypatch, capsys):
        """Help epilog Profile Management section includes --edit-profile."""
        monkeypatch.setattr(sys, "argv", ["prog", "--help"])
        with pytest.raises(SystemExit):
            parse_args()

        output = capsys.readouterr().out
        assert "Profile Management:" in output
        assert "--edit-profile" in output
        # Verify placeholder is gone from output
        assert "coming in a future update" not in output
