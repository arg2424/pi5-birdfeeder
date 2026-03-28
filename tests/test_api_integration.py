from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path


def _seed_db(db_path: Path) -> None:
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    older = now - timedelta(hours=1)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO motion_events (created_at, image_path, clip_path, motion_score, threshold, bird_detections)
            VALUES (?, ?, NULL, ?, ?, ?)
            """,
            (older.isoformat(timespec="seconds"), "x1.jpg", 0.08, 0.02, 1),
        )
        conn.execute(
            """
            INSERT INTO motion_events (created_at, image_path, clip_path, motion_score, threshold, bird_detections)
            VALUES (?, ?, NULL, ?, ?, ?)
            """,
            (now.isoformat(timespec="seconds"), "x2.jpg", 0.01, 0.02, 0),
        )

        conn.execute(
            """
            INSERT INTO individuals (created_at, last_seen_at, sightings_count, prototype_embedding)
            VALUES (?, ?, ?, ?)
            """,
            (now.isoformat(timespec="seconds"), now.isoformat(timespec="seconds"), 3, "0.1,0.2"),
        )
        conn.execute(
            """
            INSERT INTO individuals (created_at, last_seen_at, sightings_count, prototype_embedding)
            VALUES (?, ?, ?, ?)
            """,
            (now.isoformat(timespec="seconds"), now.isoformat(timespec="seconds"), 1, "0.3,0.4"),
        )

        conn.execute(
            """
            INSERT INTO sightings (
                created_at, image_path, crop_path, individual_id, confidence, motion_event_id,
                bbox_x1, bbox_y1, bbox_x2, bbox_y2
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now.isoformat(timespec="seconds"), "x2.jpg", "c1.jpg", 1, 0.91, 2, 1, 1, 10, 10),
        )
        conn.execute(
            """
            INSERT INTO sightings (
                created_at, image_path, crop_path, individual_id, confidence, motion_event_id,
                bbox_x1, bbox_y1, bbox_x2, bbox_y2
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now.isoformat(timespec="seconds"), "x2.jpg", "c2.jpg", 2, 0.67, 2, 2, 2, 12, 12),
        )
        conn.commit()


def test_api_filters_timeline_highlights_and_export(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "birdfeeder.db"
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir(exist_ok=True)

    import src.database as database_mod

    monkeypatch.setattr(database_mod, "DB_PATH", str(db_path))
    db = database_mod.DatabaseHandler()
    db.init_schema()

    _seed_db(db_path)

    import src.api as api_mod

    monkeypatch.setattr(api_mod, "DB_PATH", str(db_path))
    monkeypatch.setattr(api_mod, "BASE_DIR", tmp_path)
    monkeypatch.setattr(api_mod, "EXPORTS_DIR", exports_dir)
    monkeypatch.setattr(api_mod, "DAILY_EXPORT_ENABLED", True)

    client = api_mod.app.test_client()

    res_stats = client.get("/api/stats")
    assert res_stats.status_code == 200
    stats = res_stats.get_json()
    assert stats["motion_events"] == 2
    assert stats["sightings"] == 2

    res_sightings = client.get("/api/sightings?individual_id=1&min_confidence=0.8&limit=20")
    assert res_sightings.status_code == 200
    items = res_sightings.get_json()["items"]
    assert len(items) == 1
    assert items[0]["individual_id"] == 1

    res_timeline = client.get("/api/stats/timeline?hours=48")
    assert res_timeline.status_code == 200
    timeline = res_timeline.get_json()["items"]
    assert len(timeline) >= 1

    res_highlights = client.get("/api/highlights?limit=2")
    assert res_highlights.status_code == 200
    highlights = res_highlights.get_json()["items"]
    assert len(highlights) == 2
    assert float(highlights[0]["confidence"]) >= float(highlights[1]["confidence"])

    res_export = client.post("/api/export/daily?days=7")
    assert res_export.status_code == 200
    payload = res_export.get_json()
    assert payload["ok"] is True
    assert (exports_dir / Path(payload["file"]).name).exists()


def test_alert_test_requires_webhook(monkeypatch):
    import src.api as api_mod

    class _DummySender:
        enabled = False

    monkeypatch.setattr(api_mod, "_alert_sender", _DummySender())
    client = api_mod.app.test_client()

    res = client.post("/api/alerts/test")
    assert res.status_code == 400
