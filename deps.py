"""OS-aware dependency checker and installer.

Called at startup to ensure all required packages are available.
Handles PEP 668 externally-managed environments by auto-creating
a virtual environment and re-executing the script within it.
"""

import importlib
import os
import platform
import subprocess
import sys

# Minimum Python version required
MIN_PYTHON = (3, 10)

# Required pip packages: (import_name, pip_name)
REQUIRED_PACKAGES = [
    ("requests", "requests"),
    ("bs4", "beautifulsoup4"),
]

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_VENV_DIR = os.path.join(_SCRIPT_DIR, ".venv")


def get_os_info() -> dict:
    """Detect OS and return platform details."""
    system = platform.system().lower()
    info = {
        "system": system,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "arch": platform.machine(),
    }

    if system == "darwin":
        info["os_name"] = "macOS"
        info["pkg_manager"] = "brew" if _command_exists("brew") else None
    elif system == "linux":
        info["os_name"] = "Linux"
        if _command_exists("apt-get"):
            info["pkg_manager"] = "apt-get"
        elif _command_exists("dnf"):
            info["pkg_manager"] = "dnf"
        elif _command_exists("yum"):
            info["pkg_manager"] = "yum"
        elif _command_exists("pacman"):
            info["pkg_manager"] = "pacman"
        else:
            info["pkg_manager"] = None
    elif system == "windows":
        info["os_name"] = "Windows"
        info["pkg_manager"] = "choco" if _command_exists("choco") else None
    else:
        info["os_name"] = system
        info["pkg_manager"] = None

    return info


def _command_exists(cmd: str) -> bool:
    """Check if a command exists on the system."""
    try:
        result = subprocess.run(
            ["which", cmd] if os.name != "nt" else ["where", cmd],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _in_venv() -> bool:
    """Check if we're already running inside a virtual environment."""
    return (
        hasattr(sys, "real_prefix")  # virtualenv
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)  # venv
    )


def check_python_version() -> bool:
    """Check that Python meets the minimum version requirement."""
    current = sys.version_info[:2]
    if current < MIN_PYTHON:
        print(
            f"Error: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, "
            f"but found {current[0]}.{current[1]}"
        )
        return False
    return True


def _get_missing_packages() -> list[tuple[str, str]]:
    """Return list of (import_name, pip_name) for packages that can't be imported."""
    missing = []
    for import_name, pip_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append((import_name, pip_name))
    return missing


def _create_venv_and_reexec():
    """Create a virtual environment, install deps, and re-execute the current script in it."""
    print(f"Creating virtual environment at {_VENV_DIR}...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "venv", _VENV_DIR],
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

    # Determine the venv Python path
    if os.name == "nt":
        venv_python = os.path.join(_VENV_DIR, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(_VENV_DIR, "bin", "python3")
        if not os.path.exists(venv_python):
            venv_python = os.path.join(_VENV_DIR, "bin", "python")

    # Install packages in the venv
    pip_names = [pip_name for _, pip_name in REQUIRED_PACKAGES]
    print(f"Installing packages: {', '.join(pip_names)}...")
    try:
        subprocess.check_call(
            [venv_python, "-m", "pip", "install", "--quiet"] + pip_names,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages in venv: {e}")
        sys.exit(1)

    print("Virtual environment ready. Re-launching...\n")
    # Re-execute the original command with the venv Python.
    # Use subprocess + sys.exit instead of os.execv because os.execv
    # does not replace the process on Windows (it spawns a second one).
    ret = subprocess.call([venv_python] + sys.argv)
    sys.exit(ret)


def _install_packages(missing: list[tuple[str, str]]) -> bool:
    """Try to install missing packages. Handle externally-managed environments."""
    pip_names = [pip_name for _, pip_name in missing]
    print(f"Missing packages: {', '.join(pip_names)}")

    # Try standard pip install first
    print(f"Installing: {', '.join(pip_names)}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet"] + pip_names,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # Verify
        still_missing = _get_missing_packages()
        if not still_missing:
            print("All packages installed successfully.")
            return True
    else:
        stderr_text = result.stderr or ""
        if "externally-managed-environment" in stderr_text:
            print("System Python is externally managed (PEP 668).")
            _create_venv_and_reexec()
            # _create_venv_and_reexec calls os.execv — does not return
        else:
            print(f"pip install failed (exit {result.returncode}): {stderr_text[:200]}")

    return False


def ensure_dependencies() -> dict:
    """Run all dependency checks. Exit if critical ones fail.

    Returns:
        OS info dict for use by the rest of the application.
    """
    os_info = get_os_info()

    if not check_python_version():
        sys.exit(1)

    missing = _get_missing_packages()
    if missing:
        if _in_venv():
            # Already in a venv but packages missing — just pip install
            pip_names = [pip_name for _, pip_name in missing]
            print(f"Installing missing packages in venv: {', '.join(pip_names)}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--quiet"] + pip_names,
                )
            except subprocess.CalledProcessError as e:
                print(f"Error installing packages: {e}")
                sys.exit(1)
        else:
            # Not in a venv — try installing, handle PEP 668
            if not _install_packages(missing):
                sys.exit(1)

    return os_info
