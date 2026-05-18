"""View-model helpers for API credential test status labels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiStatusDisplay:
    """Display text and color for an API test status label."""

    text: str
    color: str


def api_testing_status() -> ApiStatusDisplay:
    return ApiStatusDisplay("Testing...", "gray")


def api_missing_key_status() -> ApiStatusDisplay:
    return ApiStatusDisplay("⚠ No API key provided", "orange")


def api_missing_credentials_status(label: str) -> ApiStatusDisplay:
    return ApiStatusDisplay(f"⚠ Both {label} required", "orange")


def api_valid_status() -> ApiStatusDisplay:
    return ApiStatusDisplay("✓ Valid", "green")


def api_invalid_key_status() -> ApiStatusDisplay:
    return ApiStatusDisplay("✗ Invalid key", "red")


def api_invalid_credentials_status() -> ApiStatusDisplay:
    return ApiStatusDisplay("✗ Invalid credentials", "red")


def api_unexpected_status(http_status: int) -> ApiStatusDisplay:
    return ApiStatusDisplay(f"⚠ Unexpected status {http_status}", "orange")


def api_http_status(http_status: int) -> ApiStatusDisplay:
    return ApiStatusDisplay(f"⚠ HTTP {http_status}", "orange")


def api_network_error_status() -> ApiStatusDisplay:
    return ApiStatusDisplay("⚠ Network error", "orange")


def api_timeout_status() -> ApiStatusDisplay:
    return ApiStatusDisplay("⚠ Timeout", "orange")


def api_error_status(error: object) -> ApiStatusDisplay:
    return ApiStatusDisplay(f"⚠ Error: {error}", "orange")
