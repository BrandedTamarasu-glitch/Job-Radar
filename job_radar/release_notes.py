"""Release note extraction helpers for tagged GitHub releases."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


class ReleaseNotesError(RuntimeError):
    """Raised when release notes cannot be extracted."""


def extract_changelog_section(changelog_text: str, tag: str) -> str:
    """Extract the changelog section matching a release tag."""
    normalized_tag = tag if tag.startswith("v") else f"v{tag}"
    heading_prefix = f"## {normalized_tag}"
    lines = changelog_text.splitlines()
    start_index: int | None = None

    for index, line in enumerate(lines):
        if line.startswith(heading_prefix):
            start_index = index
            break

    if start_index is None:
        raise ReleaseNotesError(f"No CHANGELOG.md section found for {normalized_tag}")

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        if lines[index].startswith("## "):
            end_index = index
            break

    section = "\n".join(lines[start_index:end_index]).strip()
    if not section:
        raise ReleaseNotesError(f"CHANGELOG.md section for {normalized_tag} is empty")
    return section + "\n"


def write_release_notes(
    tag: str,
    output_path: str | Path,
    *,
    changelog_path: str | Path = "CHANGELOG.md",
) -> Path:
    """Write release notes for a tag from CHANGELOG.md."""
    changelog = Path(changelog_path)
    output = Path(output_path)
    notes = extract_changelog_section(changelog.read_text(encoding="utf-8"), tag)
    output.write_text(notes, encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for release note extraction."""
    parser = argparse.ArgumentParser(description="Extract Job Radar release notes from CHANGELOG.md.")
    parser.add_argument("--tag", required=True, help="Release tag, for example v2.6.0")
    parser.add_argument("--output", required=True, help="Path to write extracted release notes")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Path to CHANGELOG.md")
    args = parser.parse_args(argv)

    try:
        output = write_release_notes(args.tag, args.output, changelog_path=args.changelog)
    except (OSError, ReleaseNotesError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"OK: wrote release notes to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
