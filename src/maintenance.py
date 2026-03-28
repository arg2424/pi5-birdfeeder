"""Maintenance helpers for retention and daily summaries."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def prune_old_files(base_dir: Path, pattern: str, older_than_days: int) -> int:
    """Delete files older than N days and return the number of removed files."""
    if older_than_days <= 0:
        return 0

    cutoff = datetime.now() - timedelta(days=older_than_days)
    removed = 0
    for file_path in base_dir.glob(pattern):
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                file_path.unlink(missing_ok=True)
                removed += 1
        except Exception as exc:
            logger.warning("Retention cleanup failed for %s: %s", file_path, exc)
    return removed
