"""Integration tests for Phase 8 entry point wiring.

Tests the full pipeline from wizard to search:
- Config profile_path recognition
- load_profile_with_recovery flows
- Profile path precedence
- Developer flags (--validate-profile, --no-wizard)
- Backward compatibility with legacy v1.0 configs
"""

import json
import sys
from pathlib import Path

import pytest

from job_radar.config import KNOWN_KEYS, load_config
from job_radar.search import load_profile_with_recovery, parse_args


# ---------------------------------------------------------------------------
# Test Group 1: Config profile_path recognition (3 tests)
# ---------------------------------------------------------------------------


def test_config_known_keys_includes_profile_path():
    """Assert 'profile_path' is in KNOWN_KEYS from config.py."""
    assert "profile_path" in KNOWN_KEYS


def test_config_loads_profile_path_from_json(tmp_path):
    """Write a config.json with profile_path, verify it loads correctly."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"profile_path": "/some/path.json", "min_score": 3.0}),
        encoding="utf-8",
    )

    result = load_config(str(config_file))

    assert "profile_path" in result
    assert result["profile_path"] == "/some/path.json"
    assert result["min_score"] == 3.0


def test_config_legacy_without_profile_path(tmp_path):
    """Write a v1.0 config (no profile_path), verify it still loads other keys."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"min_score": 2.5, "new_only": True}),
        encoding="utf-8",
    )

    result = load_config(str(config_file))

    assert result["min_score"] == 2.5
    assert result["new_only"] is True
    assert "profile_path" not in result


# ---------------------------------------------------------------------------
# Test Group 2: load_profile_with_recovery (6 tests)
# ---------------------------------------------------------------------------


def test_recovery_valid_profile_returns_dict(tmp_path):
    """Write a valid profile.json, call load_profile_with_recovery, verify it returns dict."""
    profile_path = tmp_path / "profile.json"
    profile_data = {
        "name": "Test User",
        "target_titles": ["Software Engineer"],
        "core_skills": ["Python", "Django"],
    }
    profile_path.write_text(json.dumps(profile_data), encoding="utf-8")

    result = load_profile_with_recovery(str(profile_path))

    assert isinstance(result, dict)
    assert result["name"] == "Test User"
    assert result["target_titles"] == ["Software Engineer"]
    assert result["core_skills"] == ["Python", "Django"]


def test_recovery_missing_profile_triggers_wizard(tmp_path, mocker):
    """Provide nonexistent path, verify wizard is called."""
    mocker.patch("job_radar.paths.get_data_dir", return_value=tmp_path)

    nonexistent_path = tmp_path / "missing_profile.json"

    # Mock wizard to create valid profile and return True
    def wizard_side_effect():
        profile_data = {
            "name": "Wizard Created",
            "target_titles": ["Engineer"],
            "core_skills": ["Python"],
        }
        nonexistent_path.write_text(json.dumps(profile_data), encoding="utf-8")
        return True

    mock_wizard = mocker.patch(
        "job_radar.wizard.run_setup_wizard", side_effect=wizard_side_effect
    )

    result = load_profile_with_recovery(str(nonexistent_path))

    # Verify wizard was called
    mock_wizard.assert_called_once()
    # Verify result is the wizard-created profile
    assert result["name"] == "Wizard Created"


def test_recovery_corrupt_json_backs_up_and_triggers_wizard(tmp_path, mocker):
    """Write invalid JSON, verify .bak file exists and wizard is called."""
    mocker.patch("job_radar.paths.get_data_dir", return_value=tmp_path)

    corrupt_path = tmp_path / "corrupt_profile.json"
    corrupt_path.write_text("{corrupt json", encoding="utf-8")

    # Mock wizard to create valid profile
    def wizard_side_effect():
        valid_data = {
            "name": "Fixed Profile",
            "target_titles": ["Engineer"],
            "core_skills": ["Python"],
        }
        corrupt_path.write_text(json.dumps(valid_data), encoding="utf-8")
        return True

    mock_wizard = mocker.patch(
        "job_radar.wizard.run_setup_wizard", side_effect=wizard_side_effect
    )

    result = load_profile_with_recovery(str(corrupt_path))

    # Verify backup was created
    backup_path = Path(f"{corrupt_path}.bak")
    assert backup_path.exists()
    assert backup_path.read_text() == "{corrupt json"

    # Verify wizard was called
    mock_wizard.assert_called_once()

    # Verify result is the fixed profile
    assert result["name"] == "Fixed Profile"


def test_recovery_missing_fields_backs_up_and_triggers_wizard(tmp_path, mocker):
    """Write valid JSON but missing required fields, verify backup and wizard call."""
    mocker.patch("job_radar.paths.get_data_dir", return_value=tmp_path)

    incomplete_path = tmp_path / "incomplete_profile.json"
    incomplete_data = {"name": "Test"}  # Missing target_titles and core_skills
    incomplete_path.write_text(json.dumps(incomplete_data), encoding="utf-8")

    # Mock wizard to create complete profile
    def wizard_side_effect():
        complete_data = {
            "name": "Complete Profile",
            "target_titles": ["Engineer"],
            "core_skills": ["Python"],
        }
        incomplete_path.write_text(json.dumps(complete_data), encoding="utf-8")
        return True

    mock_wizard = mocker.patch(
        "job_radar.wizard.run_setup_wizard", side_effect=wizard_side_effect
    )

    result = load_profile_with_recovery(str(incomplete_path))

    # Verify backup was created
    backup_path = Path(f"{incomplete_path}.bak")
    assert backup_path.exists()

    # Verify wizard was called
    mock_wizard.assert_called_once()

    # Verify result is complete
    assert "target_titles" in result
    assert "core_skills" in result


def test_recovery_max_retry_exits(tmp_path, mocker):
    """Mock wizard to always return True but write invalid profile, verify sys.exit after 2 retries."""
    mocker.patch("job_radar.paths.get_data_dir", return_value=tmp_path)

    missing_path = tmp_path / "retry_test.json"

    # Mock wizard to write invalid profile every time
    def wizard_side_effect():
        # Write incomplete profile (missing core_skills)
        missing_path.write_text(
            json.dumps({"name": "Bad", "target_titles": ["Engineer"]}), encoding="utf-8"
        )
        return True

    mocker.patch("job_radar.wizard.run_setup_wizard", side_effect=wizard_side_effect)

    # Should exit after max retries
    with pytest.raises(SystemExit) as exc_info:
        load_profile_with_recovery(str(missing_path))

    assert exc_info.value.code == 1


def test_recovery_wizard_cancelled_exits(tmp_path, mocker):
    """Missing profile, mock wizard to return False (user cancelled), verify sys.exit."""
    mocker.patch("job_radar.paths.get_data_dir", return_value=tmp_path)

    missing_path = tmp_path / "cancelled.json"

    # Mock wizard to return False (cancelled)
    mock_wizard = mocker.patch("job_radar.wizard.run_setup_wizard", return_value=False)

    with pytest.raises(SystemExit) as exc_info:
        load_profile_with_recovery(str(missing_path))

    mock_wizard.assert_called_once()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Test Group 3: Profile path precedence in parse_args (3 tests)
# ---------------------------------------------------------------------------


def test_parse_args_cli_profile_overrides_config(monkeypatch):
    """CLI --profile flag overrides config.json profile_path."""
    config = {"profile_path": "/config/path.json"}

    # Set sys.argv to include --profile flag
    monkeypatch.setattr(sys, "argv", ["prog", "--profile", "/cli/path.json"])

    args = parse_args(config)

    # CLI flag should override config
    assert args.profile == "/cli/path.json"


def test_parse_args_config_profile_path_used_as_default(monkeypatch):
    """When no CLI --profile flag, config.json profile_path is available but not set as argparse default."""
    config = {"profile_path": "/config/path.json"}

    # Set sys.argv with no --profile flag
    monkeypatch.setattr(sys, "argv", ["prog"])

    args = parse_args(config)

    # args.profile should be None (argparse dest is 'profile', not 'profile_path')
    # The main() function handles resolution: CLI > config > default
    assert args.profile is None


def test_parse_args_no_wizard_flag(monkeypatch):
    """--no-wizard flag sets args.no_wizard to True."""
    monkeypatch.setattr(sys, "argv", ["prog", "--no-wizard"])

    args = parse_args()

    assert args.no_wizard is True


# ---------------------------------------------------------------------------
# Test Group 4: Developer flags (2 tests)
# ---------------------------------------------------------------------------


def test_validate_profile_valid_exits_zero(tmp_path, mocker, capsys):
    """Valid profile with --validate-profile exits 0 with success message."""
    profile_path = tmp_path / "valid.json"
    profile_data = {
        "name": "Valid User",
        "target_titles": ["Engineer"],
        "core_skills": ["Python"],
    }
    profile_path.write_text(json.dumps(profile_data), encoding="utf-8")

    # Mock sys.argv to include --validate-profile
    mocker.patch("sys.argv", ["prog", "--validate-profile", str(profile_path)])

    # Import and call main - it should exit 0
    from job_radar.search import main

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    # Verify success message in stdout
    captured = capsys.readouterr()
    assert "Profile valid" in captured.out
    assert str(profile_path) in captured.out


def test_validate_profile_invalid_exits_one(tmp_path, mocker, capsys):
    """Invalid profile with --validate-profile exits 1 with error message."""
    profile_path = tmp_path / "invalid.json"
    profile_path.write_text("{}", encoding="utf-8")  # Empty object - missing required fields

    # Mock sys.argv to include --validate-profile
    mocker.patch("sys.argv", ["prog", "--validate-profile", str(profile_path)])

    # Import and call main - it should exit 1
    from job_radar.search import main

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1

    # Verify error message in stdout/stderr
    captured = capsys.readouterr()
    # Check both stdout and stderr for error message
    output = captured.out + captured.err
    assert "missing required field" in output.lower() or "Profile invalid" in output
