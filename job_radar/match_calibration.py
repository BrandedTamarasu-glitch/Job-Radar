"""Match calibration presets for search ranking strictness."""

from copy import deepcopy
from typing import Any


CUSTOM_MATCH_CALIBRATION = "custom"

MATCH_CALIBRATION_PRESETS = {
    "broader": {
        "label": "Broader",
        "min_score": 2.4,
        "location_strictness": "profile",
        "description": "Show more possible matches and let profile scoring sort the fit.",
    },
    "balanced": {
        "label": "Balanced",
        "min_score": 2.8,
        "location_strictness": "profile",
        "description": "Use the default threshold for a practical mix of reach and quality.",
    },
    "strict": {
        "label": "Strict",
        "min_score": 3.4,
        "location_strictness": "exclude_onsite",
        "description": "Prioritize stronger matches and filter out on-site roles.",
    },
}


def match_calibration_choices() -> list[str]:
    """Return GUI labels for available calibration options."""
    return [
        preset["label"]
        for preset in MATCH_CALIBRATION_PRESETS.values()
    ] + ["Custom"]


def match_calibration_label(key: str | None) -> str:
    """Return the display label for a calibration key."""
    preset = MATCH_CALIBRATION_PRESETS.get(str(key or "").casefold())
    if not preset:
        return "Custom"
    return str(preset["label"])


def get_match_calibration(label_or_key: str | None) -> dict[str, Any] | None:
    """Return a calibration preset by key or display label."""
    value = str(label_or_key or "").strip()
    if not value:
        return None

    key = value.casefold().replace(" ", "_")
    if key in MATCH_CALIBRATION_PRESETS:
        return deepcopy(MATCH_CALIBRATION_PRESETS[key])

    for preset in MATCH_CALIBRATION_PRESETS.values():
        if str(preset["label"]).casefold() == value.casefold():
            return deepcopy(preset)
    return None


def apply_match_calibration(config: dict[str, Any], label_or_key: str | None) -> dict[str, Any]:
    """Return config with preset search controls applied."""
    updated = dict(config)
    preset = get_match_calibration(label_or_key)
    if not preset:
        updated["match_calibration"] = CUSTOM_MATCH_CALIBRATION
        return updated

    key = _key_for_label(str(preset["label"]))
    updated["match_calibration"] = key
    updated["min_score"] = preset["min_score"]
    updated["location_strictness"] = preset["location_strictness"]
    return updated


def infer_match_calibration(config: dict[str, Any]) -> str:
    """Infer a calibration key from explicit search settings."""
    min_score = _float_or_none(config.get("min_score"))
    location_strictness = config.get("location_strictness") or "profile"

    for key, preset in MATCH_CALIBRATION_PRESETS.items():
        if (
            min_score is not None
            and abs(min_score - float(preset["min_score"])) < 0.001
            and location_strictness == preset["location_strictness"]
        ):
            return key
    return CUSTOM_MATCH_CALIBRATION


def _key_for_label(label: str) -> str:
    for key, preset in MATCH_CALIBRATION_PRESETS.items():
        if str(preset["label"]).casefold() == label.casefold():
            return key
    return CUSTOM_MATCH_CALIBRATION


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
