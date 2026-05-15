# Release Notes Draft: Product Iteration U-Y

Created: 2026-05-15

## Highlights

- Added adaptive dashboard guidance that surfaces profile, maintenance, review queue, saved-search, and source-quality next steps from local app state.
- Added bounded workflow shortcuts for review cleanup so dismissed review items can be cleared without touching shortlist or maybe-later entries.
- Added source strategy intelligence in Settings and Search controls, including preset-yield diagnostics, source-selection recommendations, pre-run guidance, and readable source-name normalization.
- Hardened release readiness with focused release support validation, a full regression sweep, and Windows build script artifact-name verification.

## User-Facing Improvements

- Search controls can now show source reliability and preset-yield guidance before reruns.
- Settings diagnostics now recommend sources to temporarily uncheck, pair with broader coverage, or keep enabled based on recent outcomes.
- Profile dashboard recommendations now surface maintenance and source-quality issues earlier.
- Settings includes a bounded dismissed-review cleanup action.

## Validation

- Focused source strategy and release support checkpoint: 100 passed.
- Full automated regression: 950 passed, 8 skipped.
- Build-script metadata verification: release artifact naming and checksum checks passed.

## Privacy Notes

The release notes should describe features and validation only. Do not include local profile data, saved searches, tracker records, source history contents, API keys, or app-data paths from a user's machine.
