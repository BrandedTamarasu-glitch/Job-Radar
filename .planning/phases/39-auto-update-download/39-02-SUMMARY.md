# Plan 39-02 Summary: UpdateBanner Multi-State & Download Lifecycle

**Status:** Complete
**Duration:** ~600s (estimated, includes checkpoint)
**Commits:** 3

## What Was Built

### UpdateBanner Multi-State Widget (`update_banner.py`)
- Transformed single-state notification banner into multi-state widget
- States: notification → progress → complete → failure
- Progress state shows: progress bar + percentage + downloaded/total size
- Cancel button alongside progress bar
- Complete state shows "Install Now" button (stub for Phase 40)
- Failure state shows Retry and Dismiss buttons
- DownloadConfirmDialog: confirmation before download starts with version and size

### MainWindow Download Lifecycle (`main_window.py`)
- Wired download initiation from banner's on_download callback
- Queue message routing for download_progress, download_complete, download_failed
- DownloadWorker creation via create_download_worker factory
- Session dismiss on cancel (suppresses banner until next app launch)
- Asset fetching via UpdateChecker.fetch_release_assets + select_platform_asset

### Config Fix (`config.py`)
- Added "update_state" to KNOWN_KEYS to prevent unrecognized key warning

## Commits

1. `cbd0597` feat(39-02): transform UpdateBanner into multi-state widget with confirmation dialog
2. `eb70f33` feat(39-02): wire download lifecycle into MainWindow
3. `5c53def` fix(39-02): add update_state to known config keys

## Files Modified

| File | Action | Lines Changed |
|------|--------|---------------|
| job_radar/gui/update_banner.py | Modified | +200 |
| job_radar/gui/main_window.py | Modified | +80 |
| job_radar/config.py | Modified | +1 |

## Key Decisions

- Banner transforms in-place between states (no separate widgets)
- Session-only dismiss on cancel (softer than 24h suppress)
- "Install Now" button is a stub — Phase 40 will implement installer launch
- Confirmation dialog shows version number and estimated download size
