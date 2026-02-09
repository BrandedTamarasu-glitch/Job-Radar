"""Allow running as ``python -m job_radar`` and as PyInstaller entry point."""

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


def main():
    _fix_ssl_for_frozen()

    try:
        from job_radar.banner import display_banner
        from job_radar import __version__
        display_banner(version=__version__)
    except Exception:
        # Banner is non-critical, continue even if it fails
        pass

    # First-run setup wizard (skip if --no-wizard flag present)
    import argparse as _argparse
    _pre = _argparse.ArgumentParser(add_help=False)
    _pre.add_argument("--no-wizard", action="store_true")
    _pre_args, _ = _pre.parse_known_args()

    if not _pre_args.no_wizard:
        try:
            from job_radar.wizard import is_first_run, run_setup_wizard
            if is_first_run():
                print("\nWelcome to Job Radar!")
                print("Let's set up your profile before your first search.\n")
                if not run_setup_wizard():
                    print("\nSetup cancelled. Run again when you're ready!")
                    sys.exit(0)
                print()  # Blank line before search starts
        except ImportError:
            pass  # questionary not installed -- skip wizard (dev mode without extras)
        except Exception:
            pass  # Wizard failure is non-critical -- user can still use --profile flag

    try:
        from job_radar.search import main as search_main
        search_main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        try:
            from job_radar.banner import log_error_and_exit
            log_error_and_exit(f"Fatal error: {e}", exception=e)
        except Exception:
            # Last resort if even error logging fails
            print(f"\nFatal error: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
