from job_radar.match_calibration import (
    CUSTOM_MATCH_CALIBRATION,
    apply_match_calibration,
    get_match_calibration,
    infer_match_calibration,
    match_calibration_choices,
    match_calibration_label,
)


def test_match_calibration_choices_include_expected_presets():
    assert match_calibration_choices() == ["Broader", "Balanced", "Strict", "Custom"]


def test_apply_match_calibration_sets_score_and_location_controls():
    config = {"new_only": True, "min_score": 2.8}

    calibrated = apply_match_calibration(config, "Strict")

    assert calibrated["new_only"] is True
    assert calibrated["match_calibration"] == "strict"
    assert calibrated["min_score"] == 3.4
    assert calibrated["location_strictness"] == "exclude_onsite"


def test_apply_match_calibration_marks_unknown_values_custom():
    calibrated = apply_match_calibration({"min_score": 3.0}, "Not a preset")

    assert calibrated["match_calibration"] == CUSTOM_MATCH_CALIBRATION
    assert calibrated["min_score"] == 3.0


def test_infer_match_calibration_from_explicit_controls():
    assert infer_match_calibration({
        "min_score": 2.4,
        "location_strictness": "profile",
    }) == "broader"
    assert infer_match_calibration({
        "min_score": 3.1,
        "location_strictness": "profile",
    }) == CUSTOM_MATCH_CALIBRATION


def test_match_calibration_lookup_accepts_labels_and_keys():
    assert get_match_calibration("balanced")["label"] == "Balanced"
    assert get_match_calibration("Broader")["min_score"] == 2.4
    assert match_calibration_label("strict") == "Strict"
    assert match_calibration_label("missing") == "Custom"
