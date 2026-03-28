# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and follows semantic versioning.

## [Unreleased]

### In Work
- Long-duration field validation on Raspberry Pi 5.
- Matching threshold calibration on real bird series.
- Final user validation for the first tagged release.

## [0.1.0] - 2026-03-28

### Added
- Camera capture loop with staging cleanup and persisted motion captures.
- Motion detection pipeline with SQLite event recording.
- Bird detection integration with YOLO ONNX model.
- Baseline individual recognition with feature extraction and cosine matching.
- Web dashboard with latest capture, sightings, event gallery, live mode, and camera status.
- Monitoring endpoints, hourly timeline, highlights, daily CSV export, and webhook test endpoint.
- Production deployment assets for systemd, watchdog timer, and logrotate.
- Workspace collaboration instructions in `.github/copilot-instructions.md`.
- Integration tests covering API filters, highlights, timeline, and export.

### Changed
- README updated to reflect current endpoints, deployment assets, and project phases.
- Motion detection made more robust with smoothing and consecutive trigger logic.
- Main loop extended with retention cleanup and optional alert sending.

### Known Limits
- `v0.1.0` is a working baseline, not a production-stable release.
- Long-run endurance on target hardware is not yet validated.
- Individual recognition remains a baseline heuristic pending calibration.
