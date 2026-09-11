#!/usr/bin/env python3
"""Validate the repository-level R05 three-camera contract without FreeCAD."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main(path: Path) -> None:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract["release_class"] != "OPTICAL_RIG_R05_v7_3CAM":
        fail("release_class must identify the R05 three-camera revision")
    views = contract["camera_views"]
    if views["count"] != 3 or set(views) != {"count", "C_TOP", "C_LEFT", "C_RIGHT"}:
        fail("contract must define exactly C_TOP, C_LEFT and C_RIGHT")
    if views["C_TOP"]["connection"] != "Raspberry Pi CSI":
        fail("C_TOP must be a Raspberry Pi CSI camera")
    if views["C_LEFT"]["connection"] != "Raspberry Pi CSI":
        fail("C_LEFT must be a Raspberry Pi CSI camera")
    if views["C_RIGHT"]["connection"] != "USB-C/UVC":
        fail("C_RIGHT must be the USB-C/UVC camera")
    if views["C_LEFT"]["axis"] != [0, 1, 0] or views["C_RIGHT"]["axis"] != [0, -1, 0]:
        fail("side cameras must point at the product from opposite sides")
    conveyor = contract["conveyor_reference"]
    if conveyor["belt_width_mm"] != 190 or conveyor["length_mm"] != 1500:
        fail("IN 150 compact nominal dimensions must remain 190 x 1500 mm")
    if contract.get("fabrication_allowed") is not False:
        fail("reference dimensions must not authorize fabrication")
    print("PASS: R05 three-camera contract")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fail("usage: validate_r05_contract.py CONTRACT.json")
    main(Path(sys.argv[1]))
