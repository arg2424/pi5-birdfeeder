#!/usr/bin/env python3
"""Diagnostic simple de disponibilité caméra sur Raspberry Pi."""

from __future__ import annotations

import subprocess
import sys


def print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def run_command(command: list[str]) -> int:
    try:
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
    except FileNotFoundError:
        print(f"Commande introuvable: {' '.join(command)}")
        return 127

    if completed.stdout:
        print(completed.stdout.strip())
    if completed.stderr:
        print(completed.stderr.strip())
    return completed.returncode


def check_picamera2() -> int:
    print_header("Picamera2")
    try:
        from picamera2 import Picamera2
    except ImportError as exc:
        print(f"Import impossible: {exc}")
        print("Installer les paquets système: sudo apt install -y python3-picamera2 python3-libcamera")
        return 1

    camera_info = Picamera2.global_camera_info()
    if not camera_info:
        print("Aucune caméra détectée par Picamera2")
        return 2

    print(f"Caméra(s) détectée(s): {len(camera_info)}")
    for index, camera in enumerate(camera_info):
        print(f"- Caméra {index}: {camera}")
    return 0


def main() -> int:
    print_header("rpicam-still --list-cameras")
    rpicam_code = run_command(["rpicam-still", "--list-cameras"])

    print_header("v4l2-ctl --list-devices")
    v4l2_code = run_command(["v4l2-ctl", "--list-devices"])

    picamera_code = check_picamera2()

    if rpicam_code == 0 and picamera_code == 0:
        print("\nDiagnostic caméra: OK")
        return 0

    print("\nDiagnostic caméra: NOK")
    return max(rpicam_code, v4l2_code, picamera_code)


if __name__ == "__main__":
    sys.exit(main())
