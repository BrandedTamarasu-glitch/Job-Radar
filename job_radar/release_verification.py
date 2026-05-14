"""Release artifact verification helpers for build diagnostics."""

from __future__ import annotations

import argparse
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
            failures.append(f"missing {check.description}: {artifact_path}")
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


def _has_execute_bit(path: Path) -> bool:
    return bool(path.stat().st_mode & 0o111)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for release artifact verification."""
    parser = argparse.ArgumentParser(description="Verify Job Radar release artifacts.")
    parser.add_argument("--root", default=".", help="Repository/build root to inspect")
    parser.add_argument("--platform", required=True, choices=["linux", "windows", "macos"])
    parser.add_argument("--version", required=True, help="Release version/tag, for example v2.6.0")
    parser.add_argument("--kind", default="bundle", choices=["bundle", "installer"])
    args = parser.parse_args(argv)

    verified = verify_release_artifacts(args.root, args.platform, args.version, kind=args.kind)
    for path in verified:
        print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
