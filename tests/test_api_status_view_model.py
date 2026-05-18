from job_radar.gui.api_status_view_model import (
    api_error_status,
    api_http_status,
    api_invalid_credentials_status,
    api_invalid_key_status,
    api_missing_credentials_status,
    api_missing_key_status,
    api_network_error_status,
    api_testing_status,
    api_timeout_status,
    api_unexpected_status,
    api_valid_status,
)


def test_api_status_view_model_formats_common_states():
    assert api_testing_status().text == "Testing..."
    assert api_testing_status().color == "gray"
    assert api_valid_status().text == "✓ Valid"
    assert api_valid_status().color == "green"
    assert api_missing_key_status().text == "⚠ No API key provided"
    assert api_missing_key_status().color == "orange"
    assert api_invalid_key_status().text == "✗ Invalid key"
    assert api_invalid_key_status().color == "red"
    assert api_invalid_credentials_status().text == "✗ Invalid credentials"
    assert api_invalid_credentials_status().color == "red"
    assert api_network_error_status().text == "⚠ Network error"
    assert api_timeout_status().text == "⚠ Timeout"


def test_api_status_view_model_formats_dynamic_states():
    assert api_missing_credentials_status("email and API key").text == (
        "⚠ Both email and API key required"
    )
    assert api_unexpected_status(500).text == "⚠ Unexpected status 500"
    assert api_http_status(429).text == "⚠ HTTP 429"
    assert api_error_status(ValueError("bad key")).text == "⚠ Error: bad key"
