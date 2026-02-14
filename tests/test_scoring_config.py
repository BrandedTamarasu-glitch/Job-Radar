"""Unit tests for scoring configuration logic.

Tests normalization, validation, sample scores, and staffing mappings
without requiring GUI rendering.
"""

import pytest

from job_radar.gui.scoring_config import (
    normalize_weights,
    validate_weights,
    SAMPLE_SCORES,
    STAFFING_DISPLAY_MAP,
    STAFFING_INTERNAL_MAP,
)
from job_radar.profile_manager import DEFAULT_SCORING_WEIGHTS


class TestSampleScores:
    """Test SAMPLE_SCORES constant."""

    def test_sample_scores_has_all_components(self):
        """Verify SAMPLE_SCORES contains all 6 scoring component keys."""
        expected_keys = set(DEFAULT_SCORING_WEIGHTS.keys())
        actual_keys = set(SAMPLE_SCORES.keys())

        assert actual_keys == expected_keys, (
            f"SAMPLE_SCORES keys {actual_keys} don't match "
            f"DEFAULT_SCORING_WEIGHTS keys {expected_keys}"
        )


class TestDefaultWeights:
    """Test DEFAULT_SCORING_WEIGHTS sanity checks."""

    def test_default_weights_sum_to_one(self):
        """Verify DEFAULT_SCORING_WEIGHTS values sum to 1.0."""
        total = sum(DEFAULT_SCORING_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01, f"Default weights sum to {total}, expected 1.0"


class TestNormalizeWeights:
    """Test normalize_weights function."""

    def test_normalize_weights_proportional(self):
        """Test normalization preserves relative ratios."""
        weights = {
            "skill_match": 0.5,
            "title_relevance": 0.3,
            "seniority": 0.3,
            "location": 0.3,
            "domain": 0.2,
            "response_likelihood": 0.4,
        }
        # Sum = 2.0, so each should be halved

        normalized = normalize_weights(weights)

        # Check sum to 1.0 (allowing rounding artifacts)
        total = sum(normalized.values())
        assert abs(total - 1.0) < 0.01, f"Normalized sum is {total}, expected ~1.0"

        # Check ratios preserved (within rounding tolerance)
        # skill_match/title_relevance should be 0.5/0.3 = 1.67
        ratio_before = weights["skill_match"] / weights["title_relevance"]
        ratio_after = normalized["skill_match"] / normalized["title_relevance"]
        assert abs(ratio_before - ratio_after) < 0.1, (
            f"Ratio changed from {ratio_before} to {ratio_after}"
        )

    def test_normalize_weights_all_zeros(self):
        """Test normalization with all-zero weights produces equal distribution."""
        weights = {
            "skill_match": 0.0,
            "title_relevance": 0.0,
            "seniority": 0.0,
            "location": 0.0,
            "domain": 0.0,
            "response_likelihood": 0.0,
        }

        normalized = normalize_weights(weights)

        # All should be 1/6 = 0.17 (rounded to 0.17)
        expected = round(1.0 / 6, 2)
        for key, value in normalized.items():
            assert abs(value - expected) < 0.01, (
                f"{key} is {value}, expected {expected}"
            )


class TestPreviewCalculation:
    """Test score preview calculation logic."""

    def test_preview_calculation(self):
        """Test preview score with DEFAULT_SCORING_WEIGHTS."""
        # Manual calculation:
        # skill_match:          4.5 * 0.25 = 1.125
        # title_relevance:      4.0 * 0.15 = 0.600
        # seniority:            3.8 * 0.15 = 0.570
        # location:             5.0 * 0.15 = 0.750
        # domain:               3.5 * 0.10 = 0.350
        # response_likelihood:  3.2 * 0.20 = 0.640
        # Total:                          = 4.035

        score = sum(
            SAMPLE_SCORES[key] * DEFAULT_SCORING_WEIGHTS[key]
            for key in SAMPLE_SCORES
        )

        expected = 4.035
        assert abs(score - expected) < 0.01, f"Score is {score}, expected {expected}"

    def test_preview_with_staffing_boost(self):
        """Test staffing boost adds 0.5 to score (capped at 5.0)."""
        base_score = sum(
            SAMPLE_SCORES[key] * DEFAULT_SCORING_WEIGHTS[key]
            for key in SAMPLE_SCORES
        )

        boosted = min(5.0, base_score + 0.5)

        # base_score is ~4.035, so boosted should be ~4.535
        expected = min(5.0, 4.035 + 0.5)
        assert abs(boosted - expected) < 0.01, (
            f"Boosted score is {boosted}, expected {expected}"
        )

    def test_preview_with_staffing_penalize(self):
        """Test staffing penalize subtracts 1.0 from score (floored at 1.0)."""
        base_score = sum(
            SAMPLE_SCORES[key] * DEFAULT_SCORING_WEIGHTS[key]
            for key in SAMPLE_SCORES
        )

        penalized = max(1.0, base_score - 1.0)

        # base_score is ~4.035, so penalized should be ~3.035
        expected = max(1.0, 4.035 - 1.0)
        assert abs(penalized - expected) < 0.01, (
            f"Penalized score is {penalized}, expected {expected}"
        )


class TestStaffingMappings:
    """Test staffing preference display mappings."""

    def test_staffing_display_mapping(self):
        """Test display-to-internal mapping covers all 3 values."""
        expected_internal = {"boost", "neutral", "penalize"}
        actual_internal = set(STAFFING_DISPLAY_MAP.values())

        assert actual_internal == expected_internal, (
            f"Internal values {actual_internal} don't match expected {expected_internal}"
        )

        # Verify bidirectional consistency
        for display, internal in STAFFING_DISPLAY_MAP.items():
            assert STAFFING_INTERNAL_MAP[internal] == display, (
                f"Bidirectional mapping broken for {internal}"
            )


class TestWeightValidation:
    """Test validate_weights function."""

    def test_weight_validation_valid(self):
        """Test weights summing to 1.0 pass validation."""
        weights = {
            "skill_match": 0.25,
            "title_relevance": 0.15,
            "seniority": 0.15,
            "location": 0.15,
            "domain": 0.10,
            "response_likelihood": 0.20,
        }

        is_valid, error_msg = validate_weights(weights)

        assert is_valid, f"Validation failed: {error_msg}"
        assert error_msg is None

    def test_weight_validation_invalid_sum(self):
        """Test weights summing to 0.8 fail validation."""
        weights = {
            "skill_match": 0.20,
            "title_relevance": 0.15,
            "seniority": 0.10,
            "location": 0.15,
            "domain": 0.10,
            "response_likelihood": 0.10,
        }
        # Sum = 0.80

        is_valid, error_msg = validate_weights(weights)

        assert not is_valid, "Validation should fail for sum != 1.0"
        assert "sum to 1.0" in error_msg.lower()
        assert "0.8" in error_msg

    def test_weight_validation_below_minimum(self):
        """Test any weight below 0.05 fails validation."""
        weights = {
            "skill_match": 0.30,
            "title_relevance": 0.20,
            "seniority": 0.20,
            "location": 0.15,
            "domain": 0.02,  # Below minimum
            "response_likelihood": 0.13,
        }
        # Sum = 1.00 but domain < 0.05

        is_valid, error_msg = validate_weights(weights)

        assert not is_valid, "Validation should fail for weight below minimum"
        assert "domain" in error_msg.lower()
        assert "0.05" in error_msg
