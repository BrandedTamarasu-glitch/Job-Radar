"""Parametrized tests for config module covering all load_config edge cases."""

import pytest
from pathlib import Path
from job_radar.config import load_config, LEGACY_CONFIG_PATH, KNOWN_KEYS


# ---------------------------------------------------------------------------
# load_config() missing file (Success Criteria 1)
# ---------------------------------------------------------------------------

def test_load_config_missing_file(tmp_path):
    """Test load_config returns empty dict when file doesn't exist."""
    nonexistent_path = tmp_path / "missing_config.json"
    result = load_config(str(nonexistent_path))
    assert result == {}


# ---------------------------------------------------------------------------
# load_config() invalid JSON (Success Criteria 2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("content,expected_warning", [
    ('{"invalid": json', "Warning: Could not parse config file"),  # malformed_json
    ('', "Warning: Could not parse config file"),  # empty_file
], ids=[
    "malformed_json",
    "empty_file",
])
def test_load_config_invalid_json(tmp_path, capsys, content, expected_warning):
    """Test load_config returns empty dict and warns on invalid JSON."""
    config_file = tmp_path / "invalid.json"
    config_file.write_text(content, encoding="utf-8")

    result = load_config(str(config_file))

    assert result == {}

    # Verify stderr contains warning and file path
    captured = capsys.readouterr()
    assert expected_warning in captured.err
    assert str(config_file) in captured.err


# ---------------------------------------------------------------------------
# load_config() non-dict JSON (Success Criteria 2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("content", [
    '[1, 2, 3]',  # json_array
    '"hello"',    # json_string
    '42',         # json_number
    'null',       # json_null
], ids=[
    "json_array",
    "json_string",
    "json_number",
    "json_null",
])
def test_load_config_non_dict_json(tmp_path, capsys, content):
    """Test load_config returns empty dict and warns when JSON is not an object."""
    config_file = tmp_path / "non_dict.json"
    config_file.write_text(content, encoding="utf-8")

    result = load_config(str(config_file))

    assert result == {}

    # Verify stderr contains warning about non-dict type
    captured = capsys.readouterr()
    assert "must be a JSON object" in captured.err


# ---------------------------------------------------------------------------
# load_config() unknown keys (Success Criteria 3)
# ---------------------------------------------------------------------------

def test_load_config_single_unknown_key(tmp_path, capsys):
    """Test load_config warns and filters out single unknown key."""
    config_file = tmp_path / "unknown_key.json"
    config_file.write_text('{"unknown_key": "value"}', encoding="utf-8")

    result = load_config(str(config_file))

    assert result == {}

    # Verify stderr contains warning with key name
    captured = capsys.readouterr()
    assert "Unrecognized config key: 'unknown_key'" in captured.err


def test_load_config_multiple_unknown_keys(tmp_path, capsys):
    """Test load_config warns for each unknown key when multiple present."""
    config_file = tmp_path / "multiple_unknown.json"
    config_file.write_text('{"bad1": 1, "bad2": 2}', encoding="utf-8")

    result = load_config(str(config_file))

    assert result == {}

    # Verify stderr contains warnings for both keys
    captured = capsys.readouterr()
    assert "bad1" in captured.err
    assert "bad2" in captured.err


def test_load_config_mixed_valid_invalid_keys(tmp_path, capsys):
    """Test load_config returns valid keys and warns about invalid keys."""
    config_file = tmp_path / "mixed_keys.json"
    config_file.write_text('{"min_score": 3.0, "bad_key": "x"}', encoding="utf-8")

    result = load_config(str(config_file))

    assert result == {"min_score": 3.0}

    # Verify stderr contains warning for bad_key only
    captured = capsys.readouterr()
    assert "bad_key" in captured.err


# ---------------------------------------------------------------------------
# load_config() valid configs (Success Criteria 3)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("content,expected", [
    ('{"min_score": 3.5}', {"min_score": 3.5}),  # single_key
    ('{"min_score": 3.0, "new_only": true, "output": "/tmp/out"}',
     {"min_score": 3.0, "new_only": True, "output": "/tmp/out"}),  # all_keys
    ('{}', {}),  # empty_object
], ids=[
    "single_key",
    "all_keys",
    "empty_object",
])
def test_load_config_valid_configs(tmp_path, content, expected):
    """Test load_config correctly parses valid configuration files."""
    config_file = tmp_path / "valid_config.json"
    config_file.write_text(content, encoding="utf-8")

    result = load_config(str(config_file))

    assert result == expected


# ---------------------------------------------------------------------------
# LEGACY_CONFIG_PATH tilde expansion (Success Criteria 4)
# ---------------------------------------------------------------------------

def test_default_config_path_has_tilde():
    """Test LEGACY_CONFIG_PATH contains tilde before expansion."""
    assert str(LEGACY_CONFIG_PATH).startswith("~")


def test_default_config_path_expands_to_home():
    """Test LEGACY_CONFIG_PATH.expanduser() starts with user home directory."""
    expanded = LEGACY_CONFIG_PATH.expanduser()
    assert str(expanded).startswith(str(Path.home()))


def test_default_config_path_no_tilde_after_expansion():
    """Test tilde is gone after expanduser()."""
    expanded = LEGACY_CONFIG_PATH.expanduser()
    assert "~" not in str(expanded)


def test_default_config_path_ends_with_config_json():
    """Test expanded LEGACY_CONFIG_PATH ends with .job-radar/config.json."""
    expanded = LEGACY_CONFIG_PATH.expanduser()
    assert str(expanded).endswith(".job-radar/config.json")


# ---------------------------------------------------------------------------
# KNOWN_KEYS validation (Success Criteria 5)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key,should_exist", [
    ("min_score", True),   # min_score_valid
    ("new_only", True),    # new_only_valid
    ("output", True),      # output_valid
    ("profile_path", True),  # profile_path_valid
    ("auto_open_browser", True),  # auto_open_browser_valid
    ("profile", False),    # profile_rejected
    ("config", False),     # config_rejected
    ("unknown", False),    # unknown_rejected
], ids=[
    "min_score_valid",
    "new_only_valid",
    "output_valid",
    "profile_path_valid",
    "auto_open_browser_valid",
    "profile_rejected",
    "config_rejected",
    "unknown_rejected",
])
def test_known_keys_membership(key, should_exist):
    """Test KNOWN_KEYS contains exactly min_score, new_only, output, profile_path, auto_open_browser."""
    assert (key in KNOWN_KEYS) == should_exist


def test_known_keys_exact_size():
    """Test KNOWN_KEYS contains exactly 5 members."""
    assert len(KNOWN_KEYS) == 5
