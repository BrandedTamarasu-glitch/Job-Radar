"""Tests for api_config module covering credential loading and key retrieval."""

import os
import pytest
from pathlib import Path
from job_radar.api_config import (
    get_api_credentials_path,
    load_api_credentials,
    get_api_key,
    ensure_env_example,
    save_api_credentials,
    read_api_credentials_file,
)


def test_load_api_credentials_no_env_file(tmp_path, monkeypatch, caplog):
    """Test load_api_credentials doesn't crash when .env file doesn't exist."""
    import logging
    caplog.set_level(logging.INFO)

    data_dir = tmp_path / "data"
    monkeypatch.setattr("job_radar.api_config.get_data_dir", lambda: data_dir)

    # Should not raise exception
    load_api_credentials()

    # Should log info message about no .env found
    assert "No API credential file found" in caplog.text


def test_load_api_credentials_loads_env_file(tmp_path, monkeypatch):
    """Test load_api_credentials loads environment variables from .env file."""
    # Create .env file with test credentials
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr("job_radar.api_config.get_data_dir", lambda: data_dir)
    env_file = data_dir / ".env"
    env_file.write_text("ADZUNA_APP_ID=test123\nADZUNA_APP_KEY=testkey456\n")

    # Clean environment first
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)

    # Load credentials
    load_api_credentials()

    # Verify credentials loaded
    assert os.getenv("ADZUNA_APP_ID") == "test123"
    assert os.getenv("ADZUNA_APP_KEY") == "testkey456"


def test_load_api_credentials_migrates_legacy_cwd_env(tmp_path, monkeypatch):
    """Legacy cwd .env is copied once into app data before loading."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr("job_radar.api_config.get_data_dir", lambda: data_dir)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("SERPAPI_API_KEY=legacy-key\n", encoding="utf-8")
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    load_api_credentials()

    assert (data_dir / ".env").exists()
    assert os.getenv("SERPAPI_API_KEY") == "legacy-key"


def test_save_api_credentials_uses_app_data_path(tmp_path, monkeypatch):
    """save_api_credentials writes under app data rather than cwd."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr("job_radar.api_config.get_data_dir", lambda: data_dir)
    monkeypatch.chdir(tmp_path)

    path = save_api_credentials({"ADZUNA_APP_ID": "app-id", "ADZUNA_APP_KEY": "app-key"})

    assert path == data_dir / ".env"
    assert not (tmp_path / ".env").exists()
    assert read_api_credentials_file()["ADZUNA_APP_ID"] == "app-id"
    assert get_api_credentials_path() == data_dir / ".env"


def test_get_api_key_returns_value_when_set(monkeypatch):
    """Test get_api_key returns value when environment variable is set."""
    monkeypatch.setenv("ADZUNA_APP_ID", "my_id")

    result = get_api_key("ADZUNA_APP_ID", "Adzuna")

    assert result == "my_id"


def test_get_api_key_returns_none_when_missing(monkeypatch):
    """Test get_api_key returns None when environment variable is missing."""
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)

    result = get_api_key("ADZUNA_APP_ID", "Adzuna")

    assert result is None


def test_get_api_key_logs_warning_when_missing(monkeypatch, caplog):
    """Test get_api_key logs warning message when key is missing."""
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)

    get_api_key("ADZUNA_APP_ID", "Adzuna")

    assert "Skipping Adzuna" in caplog.text
    assert "ADZUNA_APP_ID" in caplog.text


def test_ensure_env_example_creates_file(tmp_path, monkeypatch):
    """Test ensure_env_example creates .env.example template."""
    monkeypatch.chdir(tmp_path)

    ensure_env_example()

    example_path = tmp_path / ".env.example"
    assert example_path.exists()

    content = example_path.read_text()
    assert "ADZUNA_APP_ID" in content
    assert "ADZUNA_APP_KEY" in content
    assert "AUTHENTIC_JOBS_API_KEY" in content
    assert "https://developer.adzuna.com/" in content
    assert "https://authenticjobs.com/api/" in content


def test_ensure_env_example_does_not_overwrite(tmp_path, monkeypatch):
    """Test ensure_env_example doesn't overwrite existing .env.example."""
    monkeypatch.chdir(tmp_path)

    # Create existing .env.example with custom content
    example_path = tmp_path / ".env.example"
    custom_content = "# Custom content that should not be overwritten\n"
    example_path.write_text(custom_content)

    ensure_env_example()

    # Verify content unchanged
    assert example_path.read_text() == custom_content
