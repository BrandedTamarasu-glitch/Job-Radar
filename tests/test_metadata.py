"""Project metadata consistency tests."""

from pathlib import Path

from job_radar import __version__

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def test_package_version_matches_pyproject():
    """Runtime version and package metadata stay in sync."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert __version__ == pyproject["project"]["version"]


def test_release_build_files_do_not_hardcode_old_versions():
    """Build scripts should derive release versions from package metadata."""
    build_script = Path("scripts/build.sh").read_text(encoding="utf-8")
    windows_build_script = Path("scripts/build.bat").read_text(encoding="utf-8")
    spec_file = Path("job-radar.spec").read_text(encoding="utf-8")
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "VERSION=\"1.1.0\"" not in build_script
    assert "from job_radar import __version__" in build_script
    assert "RELEASE_VERSION=\"v${VERSION#v}\"" in build_script
    assert "job-radar-${RELEASE_VERSION}-${PLATFORM}.sha256" in build_script
    assert "job_radar.release_verification" in build_script
    assert "set VERSION=1.1.0" not in windows_build_script
    assert "from job_radar import __version__" in windows_build_script
    assert "set RELEASE_VERSION=v%VERSION:v=%" in windows_build_script
    assert "job-radar-%RELEASE_VERSION%-windows.zip" in windows_build_script
    assert "job-radar-%RELEASE_VERSION%-windows.sha256" in windows_build_script
    assert "job_radar.release_verification" in windows_build_script
    assert "CFBundleShortVersionString': '2.1.7'" not in spec_file
    assert "CFBundleVersion': '2.1.7'" not in spec_file
    assert "app_version = version_scope['__version__']" in spec_file
    assert "job-radar-v*-linux.tar.gz" in gitignore
    assert "job-radar-v*.sha256" in gitignore


def test_shipped_metadata_uses_current_repository_owner():
    """Installer metadata should not point users to the previous repository owner."""
    installer = Path("installers/windows/installer.nsi").read_text(encoding="utf-8")

    assert "https://github.com/BrandedTamarasu-glitch/Job-Radar" in installer
    assert "https://github.com/coryebert/Job-Radar" not in installer


def test_release_workflow_uses_job_scoped_write_permission():
    """Release workflow should keep write-scoped tokens limited to publishing."""
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in workflow
    assert "release:\n    name: Create Release" in workflow
    assert "    permissions:\n      contents: write" in workflow
