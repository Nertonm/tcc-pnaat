#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml

REQUIRED = ("schema_version", "g0_id", "equipment", "units", "coordinate_system", "interfaces", "datums", "parameters", "provenance")

def fail(message):
    print(f"FAIL: {message}")
    raise SystemExit(1)

def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/g0/canary.yaml")
    if not path.is_file(): fail(f"missing file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict): fail("root is not mapping")
    missing = [key for key in REQUIRED if key not in data]
    if missing: fail(f"missing keys: {missing}")
    if data["units"] != "mm": fail("units must be mm")
    for key in ("equipment", "coordinate_system", "datums", "parameters", "provenance"):
        if data[key] is None: fail(f"null required block: {key}")
    if not isinstance(data["interfaces"], list) or not data["interfaces"]:
        fail("interfaces must be non-empty list")
    for interface in data["interfaces"]:
        if interface.get("thickness_mm", {}).get("value") is None:
            fail(f"interface thickness is null: {interface.get('id')}")
        for hole in interface.get("holes", []):
            for field in ("x_mm", "y_mm", "diameter_mm"):
                if hole.get(field) is None: fail(f"null hole field {field}: {hole.get('id')}")
    print(f"PASS: G0 schema {path} ({data['g0_id']})")

if __name__ == "__main__": main()
