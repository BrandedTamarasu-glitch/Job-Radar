"""Release artifact verification helpers for build diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactCheck:
    """Expected release artifact metadata."""

    path: Path
    description: str
    executable: bool = False


class ReleaseArtifactError(RuntimeError):
    """Raised when release artifact verification fails."""


def expected_release_artifacts(
    platform: str,
    version: str,
    *,
    kind: str = "bundle",
) -> list[ArtifactCheck]:
    """Return expected release artifacts for a platform and build kind."""
    normalized_platform = platform.casefold()
    normalized_kind = kind.casefold()

    if normalized_kind == "installer":
        if normalized_platform == "macos":
            return [ArtifactCheck(Path(f"Job-Radar-{version}-macos.dmg"), "macOS DMG installer")]
        if normalized_platform == "windows":
            return [
                ArtifactCheck(
                    Path("installers") / "windows" / f"Job-Radar-Setup-{version}.exe",
                    "Windows NSIS installer",
                )
            ]
        return []

    if normalized_platform == "linux":
        return [
            ArtifactCheck(Path("dist") / "job-radar" / "job-radar", "Linux executable", executable=True),
            ArtifactCheck(Path(f"job-radar-{version}-linux.tar.gz"), "Linux archive"),
        ]
    if normalized_platform == "windows":
        return [
            ArtifactCheck(Path("dist") / "job-radar" / "job-radar.exe", "Windows executable"),
            ArtifactCheck(Path(f"job-radar-{version}-windows.zip"), "Windows archive"),
        ]
    if normalized_platform == "macos":
        return [
            ArtifactCheck(
                Path("dist") / "JobRadar.app" / "Contents" / "MacOS" / "job-radar-cli",
                "macOS CLI executable inside app bundle",
                executable=True,
            ),
            ArtifactCheck(Path(f"job-radar-{version}-macos.zip"), "macOS app archive"),
        ]

    raise ValueError(f"Unsupported release artifact platform: {platform}")


def verify_release_artifacts(
    root: str | Path,
    platform: str,
    version: str,
    *,
    kind: str = "bundle",
) -> list[Path]:
    """Verify expected release artifacts exist and are non-empty."""
    root_path = Path(root)
    checks = expected_release_artifacts(platform, version, kind=kind)
    failures: list[str] = []
    verified: list[Path] = []

    for check in checks:
        artifact_path = root_path / check.path
        if not artifact_path.exists():
            similar = _similar_artifacts(root_path, check.path)
            detail = f"missing {check.description}: {artifact_path}"
            if similar:
                detail += f" (found similar: {', '.join(str(path) for path in similar)})"
            failures.append(detail)
            continue
        if artifact_path.is_file() and artifact_path.stat().st_size <= 0:
            failures.append(f"empty {check.description}: {artifact_path}")
            continue
        if check.executable and artifact_path.is_file() and not _has_execute_bit(artifact_path):
            failures.append(f"not executable {check.description}: {artifact_path}")
            continue
        verified.append(artifact_path)

    if failures:
        details = "\n".join(f"- {failure}" for failure in failures)
        raise ReleaseArtifactError(
            f"Release artifact verification failed for {platform} {kind} build {version}:\n{details}"
        )
    return verified


def write_checksum_manifest(paths: list[Path], output_path: str | Path, *, root: str | Path = ".") -> Path:
    """Write SHA256 checksums for release artifacts."""
    root_path = Path(root)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for path in paths:
        digest = _sha256(path)
        try:
            display_path = path.relative_to(root_path)
        except ValueError:
            display_path = path
        lines.append(f"{digest}  {display_path.as_posix()}")
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return destination


def _has_execute_bit(path: Path) -> bool:
    return bool(path.stat().st_mode & 0o111)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _similar_artifacts(root: Path, expected_path: Path) -> list[Path]:
    """Return nearby artifact paths that can explain filename drift."""
    parent = root / expected_path.parent

    expected_name = expected_path.name
    tokens = [
        token
        for token in expected_name.replace(".", "-").replace("_", "-").split("-")
        if token and not token.startswith("v")
    ]
    if not tokens:
        return []

    matches = []
    candidates = parent.iterdir() if parent.is_dir() else root.rglob("*")
    for candidate in candidates:
        if (
            candidate.is_dir()
            or candidate == root / expected_path
            or not _is_plausible_artifact_candidate(candidate, root, expected_path)
        ):
            continue
        candidate_lower = candidate.name.casefold()
        if all(token.casefold() in candidate_lower for token in tokens[:2]):
            matches.append(candidate.relative_to(root))

    return sorted(matches, key=lambda path: path.as_posix())[:5]


def _is_plausible_artifact_candidate(candidate: Path, root: Path, expected_path: Path) -> bool:
    relative_parts = candidate.relative_to(root).parts
    if any(part.startswith(".") or part == "__pycache__" for part in relative_parts):
        return False

    expected_name = expected_path.name
    if expected_path.suffix:
        return candidate.suffix.casefold() == expected_path.suffix.casefold()
    return candidate.name == expected_name


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for release artifact verification."""
    parser = argparse.ArgumentParser(description="Verify Job Radar release artifacts.")
    parser.add_argument("--root", default=".", help="Repository/build root to inspect")
    parser.add_argument("--platform", required=True, choices=["linux", "windows", "macos"])
    parser.add_argument("--version", required=True, help="Release version/tag, for example v2.6.0")
    parser.add_argument("--kind", default="bundle", choices=["bundle", "installer"])
    parser.add_argument("--checksum-manifest", help="Optional path to write SHA256 checksums")
    args = parser.parse_args(argv)

    try:
        verified = verify_release_artifacts(args.root, args.platform, args.version, kind=args.kind)
    except ReleaseArtifactError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for path in verified:
        print(f"OK: {path}")
    if args.checksum_manifest:
        manifest_path = write_checksum_manifest(verified, args.checksum_manifest, root=args.root)
        print(f"OK: wrote checksums to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
