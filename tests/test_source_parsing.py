"""Tests for source parsing helpers."""

from job_radar.source_parsing import (
    _MAX_TITLE,
    _clean_field,
    _parse_arrangement,
    _strip_html,
    parse_location_to_city_state,
    strip_html_and_normalize,
)


def test_clean_field_truncates_at_word_boundary_with_ellipsis():
    text = "Senior Software Engineer with Platform Experience"

    assert _clean_field(text, 30) == "Senior Software Engineer..."


def test_clean_field_strips_short_values():
    assert _clean_field("  Software Engineer  ", _MAX_TITLE) == "Software Engineer"


def test_strip_html_and_normalize_decodes_entities():
    assert strip_html_and_normalize("<p>Python &amp; <b>React</b></p>") == "Python & React"


def test_parse_location_to_city_state_abbreviates_state_name():
    assert parse_location_to_city_state("San Francisco, California, United States") == "San Francisco, CA"


def test_parse_arrangement_prefers_remote():
    assert _parse_arrangement("Remote or hybrid") == "remote"


def test_strip_html_removes_tags_without_entity_decoding():
    assert _strip_html("<p>Python &amp; React</p>") == "Python &amp; React"
