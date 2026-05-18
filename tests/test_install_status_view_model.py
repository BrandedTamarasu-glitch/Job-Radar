from pathlib import Path

from job_radar.gui.install_status_view_model import (
    install_launch_error_message,
    install_launch_status_message,
    install_prompt_message,
    installer_not_found_message,
)


def test_install_prompt_message_is_platform_specific():
    assert install_prompt_message("darwin") == "Opening installer DMG..."
    assert install_prompt_message("win32") == (
        "Launching installer... Windows may show a security prompt."
    )
    assert install_prompt_message("linux") == "Launching installer..."


def test_install_launch_status_message_is_platform_specific():
    assert install_launch_status_message("darwin") == "Opening installer DMG..."
    assert install_launch_status_message("win32") == "Launching installer..."
    assert install_launch_status_message("linux") == "Launching installer..."


def test_install_error_messages_include_recovery_context():
    path = Path("/tmp/Job-Radar.dmg")

    assert install_launch_error_message(path, RuntimeError("blocked")) == (
        f"Couldn't launch installer. File saved at: {path}\n\nblocked"
    )
    assert installer_not_found_message("/tmp/missing.dmg") == (
        "Installer file not found. Download again?\n\n/tmp/missing.dmg"
    )
