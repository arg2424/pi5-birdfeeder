"""Serveur web simple pour visualiser les captures et détections."""
from __future__ import annotations

import io
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

from flask import Flask, Response, jsonify, request, send_file
from PIL import Image

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config import BASE_DIR, DB_PATH, FLASK_DEBUG, FLASK_HOST, FLASK_PORT

WEB_DIR = BASE_DIR / "web"
MESANGE_DIR = BASE_DIR / "data" / "mesange"
MESANGE_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="/web")
MAIN_SERVICE_NAME = "pi5-birdfeeder-main.service"

_camera_lock = threading.Lock()
_camera_instance = None
_camera_last_error = None


def _open_live_camera():
    """Initialise une caméra dédiée au flux live (si disponible)."""
    global _camera_instance
    global _camera_last_error
    with _camera_lock:
        if _camera_instance is not None:
            return _camera_instance

        try:
            from picamera2 import Picamera2
        except Exception as exc:
            _camera_last_error = f"picamera2 import failed: {exc}"
            return None

        try:
            cam = Picamera2()
            config = cam.create_video_configuration(main={"size": (1280, 720)})
            cam.configure(config)
            cam.start()
            _camera_instance = cam
            _camera_last_error = None
            return _camera_instance
        except Exception as exc:
            _camera_last_error = str(exc)
            return None


def _close_live_camera() -> None:
    """Ferme la caméra live si ouverte par le serveur API."""
    global _camera_instance
    with _camera_lock:
        if _camera_instance is None:
            return
        try:
            _camera_instance.stop()
        except Exception:
            pass
        try:
            _camera_instance.close()
        except Exception:
            pass
        _camera_instance = None


def _run_systemctl(action: str, service_name: str) -> tuple[bool, str]:
    """Exécute systemctl via sudo -n pour piloter les services depuis l'API."""
    try:
        result = subprocess.run(
            ["sudo", "-n", "systemctl", action, service_name],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)

    ok = result.returncode == 0
    message = (result.stdout or result.stderr or "").strip()
    return ok, message


def _service_is_active(service_name: str) -> bool:
    result = subprocess.run(
        ["systemctl", "is-active", service_name],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "active"


def _get_camera_status() -> dict:
    """Retourne un diagnostic exploitable dans l'interface web."""
    status = {
        "detected": False,
        "available": False,
        "stream_active": _camera_instance is not None,
        "camera_count": 0,
        "message": "unknown",
    }

    try:
        from picamera2 import Picamera2
    except Exception as exc:
        status["message"] = f"picamera2 import failed: {exc}"
        return status

    try:
        infos = Picamera2.global_camera_info()
    except Exception as exc:
        status["message"] = f"camera query failed: {exc}"
        return status

    status["camera_count"] = len(infos)
    if not infos:
        status["message"] = "no camera detected"
        return status

    status["detected"] = True
    if _camera_instance is not None:
        status["available"] = True
        status["message"] = "camera in use by live stream"
        return status

    try:
        probe = Picamera2()
        probe.close()
        status["available"] = True
        status["message"] = "camera available"
    except Exception as exc:
        status["message"] = f"camera busy or unavailable: {exc}"

    return status


def _mjpeg_generator():
    """Produit un flux MJPEG pour affichage navigateur."""
    cam = _open_live_camera()
    if cam is None:
        return

    while True:
        frame = cam.capture_array()
        image = Image.fromarray(frame).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=82)
        payload = buffer.getvalue()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Cache-Control: no-cache\r\n\r\n" + payload + b"\r\n"
        )
        time.sleep(0.06)


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


@app.get("/camera/live")
def live_camera_page():
    return send_file(WEB_DIR / "live.html")


@app.get("/mesange")
def mesange_page():
    return send_file(WEB_DIR / "mesange.html")
    
@app.get("/events")
def events_page():
    return send_file(WEB_DIR / "events.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/camera/status")
def camera_status():
    return jsonify(_get_camera_status())


@app.get("/api/mode")
def mode_status():
    """Expose l'état du mode cadrage (détection stoppée)."""
    detection_active = _service_is_active(MAIN_SERVICE_NAME)
    return jsonify(
        {
            "focus_mode": not detection_active,
            "detection_service_active": detection_active,
            "service": MAIN_SERVICE_NAME,
        }
    )


@app.post("/api/mode")
def mode_set():
    """Active/désactive le mode cadrage en stoppant/redémarrant la détection."""
    payload = request.get_json(silent=True) or {}
    focus_mode = bool(payload.get("focus_mode", False))

    if focus_mode:
        ok, msg = _run_systemctl("stop", MAIN_SERVICE_NAME)
        if not ok:
            return jsonify({"error": "failed to stop detection service", "details": msg}), 500
        return jsonify({"focus_mode": True, "detection_service_active": False, "message": msg})

    # Reprise détection: libérer d'abord la caméra potentiellement tenue par le live stream.
    _close_live_camera()
    ok, msg = _run_systemctl("start", MAIN_SERVICE_NAME)
    if not ok:
        return jsonify({"error": "failed to start detection service", "details": msg}), 500
    return jsonify({"focus_mode": False, "detection_service_active": True, "message": msg})


@app.get("/api/mesange")
def mesange_list():
    """Liste des photos de mésanges sauvegardées dans data/mesange/."""
    files = sorted(MESANGE_DIR.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for f in files:
        stat = f.stat()
        # Récupère les métadonnées depuis la DB si disponible
        rows = _fetch_rows(
            "SELECT individual_id, confidence, created_at FROM sightings WHERE crop_path = ? LIMIT 1",
            (str(f),),
        )
        meta = dict(rows[0]) if rows else {}
        items.append({
            "filename": f.name,
            "url": f"/media/data/mesange/{quote(f.name)}",
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            **meta,
        })
    return jsonify({"items": items, "total": len(items)})


@app.delete("/api/mesange/<filename>")
def mesange_delete(filename: str):
    """Supprime une photo mésange par son nom de fichier."""
    # n'autoriser que les noms sans séparateurs de chemin
    if "/" in filename or "\\" in filename or ".." in filename:
        return jsonify({"error": "invalid filename"}), 400
    file_path = (MESANGE_DIR / filename).resolve()
    if not str(file_path).startswith(str(MESANGE_DIR.resolve())):
        return jsonify({"error": "forbidden"}), 403
    if not file_path.exists():
        return jsonify({"error": "not found"}), 404
    file_path.unlink()
    return jsonify({"deleted": filename})


@app.get("/api/events")
def events_list():
    """Liste paginée des motion events avec image et nb détections."""
    limit = int(request.args.get("limit", "50"))
    limit = max(1, min(limit, 500))
    offset = int(request.args.get("offset", "0"))
    offset = max(0, offset)

    rows = _fetch_rows(
        """
        SELECT id, created_at, image_path, motion_score, bird_detections
        FROM motion_events
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    total_rows = _fetch_rows("SELECT COUNT(*) AS n FROM motion_events")
    total = dict(total_rows[0])["n"] if total_rows else 0

    items = []
    for r in rows:
        item = dict(r)
        item["image_url"] = _to_web_path(item["image_path"])
        items.append(item)
    return jsonify({"items": items, "total": total, "limit": limit, "offset": offset})

@app.delete("/api/events/<int:event_id>")
def event_delete(event_id: int):
    """Supprime un motion event (DB + fichier image)."""
    rows = _fetch_rows(
        "SELECT image_path FROM motion_events WHERE id = ? LIMIT 1",
        (event_id,),
    )
    if not rows:
        return jsonify({"error": "not found"}), 404

    image_path = dict(rows[0])["image_path"]

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM sightings WHERE motion_event_id = ?", (event_id,))
        conn.execute("DELETE FROM motion_events WHERE id = ?", (event_id,))
        conn.commit()

    try:
        p = Path(image_path).resolve()
        if str(p).startswith(str(BASE_DIR.resolve())) and p.exists():
            p.unlink()
    except Exception:
        pass

    return jsonify({"deleted": event_id})


@app.post("/api/admin/reset")
def admin_reset():
    """Remet la DB à zéro et vide captures/ et mesange/."""
    import shutil
    # Reset DB
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM sightings")
        conn.execute("DELETE FROM individuals")
        conn.execute("DELETE FROM motion_events")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('sightings','individuals','motion_events')")
        conn.commit()
    # Vider captures
    captures_dir = BASE_DIR / "data" / "captures"
    for f in captures_dir.glob("*.jpg"):
        f.unlink(missing_ok=True)
    # Vider mesange
    for f in MESANGE_DIR.glob("*.jpg"):
        f.unlink(missing_ok=True)
    return jsonify({"reset": True})


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


@app.get("/api/camera/stream")
def camera_stream():
    cam = _open_live_camera()
    if cam is None:
        status = _get_camera_status()
        if _camera_last_error:
            status["message"] = _camera_last_error
        status["error"] = "camera unavailable"
        return jsonify(status), 503

    return Response(
        _mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
