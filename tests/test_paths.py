"""Tests for job_radar.paths module."""
import sys
from pathlib import Path
from unittest.mock import patch

from job_radar.paths import get_resource_path, get_data_dir, get_log_file, is_frozen


def test_is_frozen_returns_false_in_dev():
    assert is_frozen() is False


def test_is_frozen_returns_true_when_frozen():
    with patch.object(sys, 'frozen', True, create=True):
        with patch.object(sys, '_MEIPASS', '/tmp/fake_meipass', create=True):
            assert is_frozen() is True


def test_get_resource_path_dev_mode():
    result = get_resource_path('resources/test.txt')
    # In dev mode, should be relative to paths.py's parent (job_radar/)
    expected_parent = Path(__file__).parent.parent / 'job_radar'
    assert result.parent.parent == expected_parent.parent or 'job_radar' in str(result)


def test_get_resource_path_frozen_mode():
    with patch.object(sys, 'frozen', True, create=True):
        with patch.object(sys, '_MEIPASS', '/tmp/fake_bundle', create=True):
            result = get_resource_path('resources/test.txt')
            assert str(result) == str(Path('/tmp/fake_bundle/resources/test.txt'))


def test_get_data_dir_returns_path():
    result = get_data_dir()
    assert isinstance(result, Path)
    assert result.exists()
    assert 'JobRadar' in str(result) or 'jobradar' in str(result).lower()


def test_get_log_file_in_home():
    result = get_log_file()
    assert result == Path.home() / 'job-radar-error.log'
