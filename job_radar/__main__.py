"""Allow running as ``python -m job_radar`` and as PyInstaller entry point."""

import json
import os
import sys


def _fix_ssl_for_frozen():
    """Set REQUESTS_CA_BUNDLE for frozen builds so HTTPS works."""
    if getattr(sys, 'frozen', False):
        try:
            import certifi
            os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        except ImportError:
            pass  # certifi missing - requests will use system certs


def _get_profile_name() -> str | None:
    """Extract profile name for banner display. Returns None on any failure.

    Resolution order:
    1. CLI --profile flag
    2. Default location (platformdirs user data dir)

    Returns
    -------
    str | None
        Profile name from profile.json, or None if not available
    """
    try:
        import argparse as _argparse
        _pre = _argparse.ArgumentParser(add_help=False)
        _pre.add_argument("--profile", default=None)
        _pre.add_argument("--no-wizard", action="store_true")
        _pre_args, _ = _pre.parse_known_args()

        # Determine profile path
        if _pre_args.profile:
            from pathlib import Path
            profile_path = Path(_pre_args.profile).expanduser()
        else:
            # Use default location
            from job_radar.paths import get_data_dir
            profile_path = get_data_dir() / "profile.json"

        # Load and extract name
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                return profile.get("name")
    except Exception:
        pass  # Any error - return None (banner will show without name)

    return None


def _run_cli():
    """Run the CLI mode with banner, wizard prompts, and search."""
    try:
        # Extract profile name for banner
        profile_name = _get_profile_name()

        # Display banner
        from job_radar.banner import display_banner
        from job_radar import __version__
        display_banner(version=__version__, profile_name=profile_name)

        # Profile management (skip if --no-wizard flag present)
        import argparse as _argparse
        _pre = _argparse.ArgumentParser(add_help=False)
        _pre.add_argument("--no-wizard", action="store_true")
        _pre_args, _ = _pre.parse_known_args()

        if not _pre_args.no_wizard:
            try:
                from job_radar.wizard import is_first_run, run_setup_wizard

                if is_first_run():
                    # First run: Run wizard
                    print("\nWelcome to Job Radar!")
                    print("Let's set up your profile before your first search.\n")
                    if not run_setup_wizard():
                        print("\nSetup cancelled. Run again when you're ready!")
                        sys.exit(0)
                    print()  # Blank line before search starts
                else:
                    # Profile exists: Ask what to do
                    try:
                        import questionary
                        print()  # Blank line after banner
                        choice = questionary.select(
                            "What would you like to do?",
                            choices=[
                                "Run search with current profile",
                                "Update existing profile",
                                "Create new profile"
                            ]
                        ).ask()

                        if choice == "Update existing profile":
                            print("\nUpdating your profile...\n")
                            if not run_setup_wizard():
                                print("\nUpdate cancelled. Exiting.")
                                sys.exit(0)
                            print()
                        elif choice == "Create new profile":
                            print("\nCreating a new profile...\n")
                            if not run_setup_wizard():
                                print("\nProfile creation cancelled. Exiting.")
                                sys.exit(0)
                            print()
                        elif choice is None:
                            # User cancelled (Ctrl+C)
                            print("\nCancelled. Goodbye!")
                            sys.exit(0)
                        # else: "Run search" - continue to search
                    except ImportError:
                        pass  # questionary not installed - skip prompt

            except ImportError:
                pass  # questionary not installed -- skip wizard (dev mode without extras)
            except Exception:
                pass  # Wizard failure is non-critical -- user can still use --profile flag

        # Run search
        from job_radar.search import main as search_main
        search_main()

    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        try:
            from job_radar.banner import log_error_and_exit
            log_error_and_exit(f"Fatal error: {e}", exception=e)
        except Exception:
            # Last resort if even error logging fails
            print(f"\nFatal error: {e}")
            sys.exit(1)


def _run_gui():
    """Launch the desktop GUI window."""
    try:
        from job_radar.gui.main_window import launch_gui
        launch_gui()
    except ImportError as e:
        print(f"GUI dependencies not available: {e}")
        print("Install with: pip install customtkinter")
        print("Falling back to CLI mode...")
        _run_cli()
    except Exception as e:
        try:
            from job_radar.banner import log_error_and_exit
            log_error_and_exit(f"GUI error: {e}", exception=e)
        except Exception:
            print(f"\nGUI error: {e}")
            sys.exit(1)


def main():
    _fix_ssl_for_frozen()

    # CLI mode: any arguments present (--help, --profile, etc.)
    if len(sys.argv) > 1:
        _run_cli()
    else:
        # GUI mode: no arguments (double-click or bare invocation)
        _run_gui()


if __name__ == '__main__':
    main()
