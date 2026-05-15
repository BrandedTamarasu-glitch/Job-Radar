"""Tests for release note extraction."""

from job_radar.release_notes import (
    ReleaseNotesError,
    extract_changelog_section,
    main,
    write_release_notes,
)


CHANGELOG = """# Changelog

## v2.6.0 -- 2026-05-15

### New Features
- Current release.

## v2.5.0 -- 2026-05-13

### New Features
- Previous release.
"""


def test_extract_changelog_section_for_tag():
    notes = extract_changelog_section(CHANGELOG, "v2.6.0")

    assert notes.startswith("## v2.6.0")
    assert "Current release." in notes
    assert "Previous release." not in notes


def test_extract_changelog_section_accepts_tag_without_v_prefix():
    notes = extract_changelog_section(CHANGELOG, "2.6.0")

    assert "## v2.6.0" in notes


def test_extract_changelog_section_raises_for_missing_tag():
    try:
        extract_changelog_section(CHANGELOG, "v9.9.9")
    except ReleaseNotesError as exc:
        assert "v9.9.9" in str(exc)
    else:
        raise AssertionError("expected ReleaseNotesError")


def test_write_release_notes_writes_matching_section(tmp_path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(CHANGELOG, encoding="utf-8")
    output = tmp_path / "release.md"

    result = write_release_notes("v2.6.0", output, changelog_path=changelog)

    assert result == output
    assert output.read_text(encoding="utf-8") == (
        "## v2.6.0 -- 2026-05-15\n\n"
        "### New Features\n"
        "- Current release.\n"
    )


def test_main_writes_release_notes(tmp_path, capsys):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(CHANGELOG, encoding="utf-8")
    output = tmp_path / "release.md"

    exit_code = main([
        "--tag", "v2.6.0",
        "--output", str(output),
        "--changelog", str(changelog),
    ])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"OK: wrote release notes to {output}" in captured.out
    assert output.exists()


def test_main_returns_clean_error_for_missing_tag(tmp_path, capsys):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(CHANGELOG, encoding="utf-8")

    exit_code = main([
        "--tag", "v9.9.9",
        "--output", str(tmp_path / "release.md"),
        "--changelog", str(changelog),
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "No CHANGELOG.md section found for v9.9.9" in captured.err
