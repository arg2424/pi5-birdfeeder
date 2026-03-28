# Release Checklist

Use this checklist before creating a git tag.

## v0.1.0 Baseline Release

1. Scope frozen: done - 2026-03-28
   Included scope is camera capture, motion events, YOLO detection, baseline recognition, dashboard, API, and deployment assets.

2. README aligned with actual behavior: done - 2026-03-28
   README documents the current endpoints and deployment artifacts without marking user validation as complete.

3. Repository tests passing: done - 2026-03-28
   `pytest -q` -> 5 passed.

4. Packaging/import sanity for Python modules: done - 2026-03-28
   New helper modules work both in script execution and test imports.

5. Manual Pi validation of end-to-end pipeline: in work - 2026-03-28
   Validate camera -> motion -> detection -> DB -> dashboard on target hardware.

6. Manual validation of live mode and service switching: in work - 2026-03-28
   Confirm live stream and detection mode switching on the Pi.

7. Validation of deployment assets on target machine: in work - 2026-03-28
   Confirm `systemd` units, watchdog timer, and log rotation behave correctly once installed.

8. Release notes reviewed by maintainer: validated - 2026-03-28
   Review `docs/releases/v0.1.0.md` and `CHANGELOG.md`.

9. Final release decision by maintainer: validated - 2026-03-28
   Baseline release approved with known limits explicitly accepted.
