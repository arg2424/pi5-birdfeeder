"""Serveur web simple pour visualiser les captures et détections."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

from flask import Flask, jsonify, request, send_file

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config import BASE_DIR, DB_PATH, FLASK_DEBUG, FLASK_HOST, FLASK_PORT

WEB_DIR = BASE_DIR / "web"

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="/web")


def _to_web_path(image_path: str) -> str | None:
    p = Path(image_path)
    try:
        rel = p.resolve().relative_to(BASE_DIR.resolve())
    except ValueError:
        return None
    rel_str = str(rel).replace("\\", "/")
    return f"/media/{quote(rel_str)}"


def _fetch_rows(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
    return rows


@app.get("/")
def index():
    return send_file(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/latest")
def latest_capture():
    rows = _fetch_rows(
        """
        SELECT image_path, created_at, motion_score, bird_detections
        FROM motion_events
        ORDER BY id DESC
        LIMIT 1
        """
    )
    if not rows:
        return jsonify({"latest": None})

    row = dict(rows[0])
    row["image_url"] = _to_web_path(row["image_path"])
    return jsonify({"latest": row})


@app.get("/api/sightings")
def sightings():
    limit = int(request.args.get("limit", "30"))
    limit = max(1, min(limit, 200))

    rows = _fetch_rows(
        """
        SELECT
            s.id,
            s.created_at,
            s.image_path,
            s.individual_id,
            s.confidence,
            s.bbox_x1,
            s.bbox_y1,
            s.bbox_x2,
            s.bbox_y2,
            i.sightings_count
        FROM sightings s
        JOIN individuals i ON i.id = s.individual_id
        ORDER BY s.id DESC
        LIMIT ?
        """,
        (limit,),
    )

    data = []
    for r in rows:
        item = dict(r)
        item["image_url"] = _to_web_path(item["image_path"])
        item["bbox"] = [item["bbox_x1"], item["bbox_y1"], item["bbox_x2"], item["bbox_y2"]]
        data.append(item)
    return jsonify({"items": data})


@app.get("/api/stats")
def stats():
    rows = _fetch_rows(
        """
        SELECT
            (SELECT COUNT(*) FROM motion_events) AS motion_events,
            (SELECT COUNT(*) FROM sightings) AS sightings,
            (SELECT COUNT(*) FROM individuals) AS individuals
        """
    )
    return jsonify(dict(rows[0]))


@app.get("/media/<path:relpath>")
def media(relpath: str):
    file_path = (BASE_DIR / relpath).resolve()
    if not str(file_path).startswith(str(BASE_DIR.resolve())):
        return jsonify({"error": "forbidden"}), 403
    if not file_path.exists():
        return jsonify({"error": "not found"}), 404
    return send_file(file_path)


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
