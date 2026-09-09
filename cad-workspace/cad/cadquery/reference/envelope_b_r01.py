#!/usr/bin/env python3
"""REFERENCE ONLY: schematic envelopes, never fabrication or equipment geometry."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback

import cadquery as cq
import numpy as np
import trimesh
import yaml

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "data/g0/esteira-b-reference-r01.yaml"
OUT = ROOT / "exports/reference-envelope/r01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def bbox(shape):
    b = shape.BoundingBox()
    return [[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]]


def main():
    # Never overwrite a previous review, including an unsuccessful run.
    OUT.mkdir(parents=True, exist_ok=False)
    manifest = {
        "reference_id": None, "status": "reference_only",
        "fabrication_allowed": False, "measured": False, "units": "mm",
        "cadquery_version": cq.__version__,
        "yaml_sha256": sha(SOURCE), "script_sha256": sha(Path(__file__)),
        "provenance": {
            "source": str(SOURCE.relative_to(ROOT)),
            "script": str(Path(__file__).relative_to(ROOT)),
            "geometry_inputs": ["reference_scenario.selected_nominal",
                                "reference_scenario.envelopes_mm"],
            "kind": "reference_envelope", "evidence": "REFERENCE",
            "measured": False, "fabrication_allowed": False,
            "coordinate_frame": "synthetic display frame; not a real datum",
            "position_rule": "centered belt, bottle above belt; all placement derived from authorized sizes",
            "belt_thickness_rule": "reuse side_plate_thickness_mm for display only",
            "side_plate_height_rule": "reuse roller_diameter_mm for display only",
            "bottle_rule": "rectangular bounding envelope, not bottle shape",
            "keepout_rule": "nominal display volumes only; no safety clearances inferred",
            "stl_rule": "boolean union of display volumes; STEP preserves named components",
        },
        "blocked": ["real holes", "chassis interface", "real datums", "mounting",
                    "loads", "fabrication", "rigidity", "torque", "tolerances",
                    "safety", "calibration", "actual cable routing"],
        "commands": [], "validation_gate": "INCOMPLETE",
        "environment": {"container": os.environ.get("CAD_ENVIRONMENT", "unspecified")},
    }
    exit_code = 1
    try:
        data = yaml.safe_load(SOURCE.read_text())
        manifest["reference_id"] = data["reference_id"]
        scenario = data["reference_scenario"]
        if (data["units"] != "mm" or scenario["status"] != "reference_only"
                or scenario["fabrication_allowed"] is not False
                or data["provenance"]["measured"] is not False
                or data["provenance"]["fabrication_allowed"] is not False):
            raise ValueError("Input must remain reference_only, mm, unmeasured and non-fabricable")
        n, e = scenario["selected_nominal"], scenario["envelopes_mm"]
        for key in ("belt_width_mm", "conveyor_length_mm", "side_plate_thickness_mm",
                    "roller_diameter_mm", "belt_top_z_mm"):
            v = n[key]
            if type(v) not in (int, float) or not math.isfinite(v) or (key != "belt_top_z_mm" and v <= 0):
                raise ValueError(f"Invalid nominal: {key}")
        for key in ("bottle", "camera_top", "camera_side", "trigger", "lighting_top",
                    "lighting_side", "cable_bundle", "motor_keepout"):
            for axis in ("width", "depth", "height"):
                v = e[key][axis]
                if type(v) not in (int, float) or not math.isfinite(v) or v <= 0:
                    raise ValueError(f"Invalid envelope: {key}.{axis}")
        length, width, thickness, diameter, z = (n[k] for k in (
            "conveyor_length_mm", "belt_width_mm", "side_plate_thickness_mm",
            "roller_diameter_mm", "belt_top_z_mm"))
        bottle, top, side, cable = (e[k] for k in ("bottle", "camera_top", "camera_side", "cable_bundle"))
        components, records = [], []
        assembly = cq.Assembly(name="REFERENCE_ONLY_NON_FABRICABLE")

        def add(name, shape, center, dimensions, role, formula):
            if not shape.isValid() or shape.Volume() <= 0:
                raise ValueError(f"Invalid CAD solid: {name}")
            color = cq.Color(1, 0.2, 0.1, 0.35) if "keepout" in role else cq.Color(0.2, 0.6, 0.9, 0.65)
            assembly.add(shape, name=name, color=color)
            components.append(shape)
            records.append({"name": name, "role": role, "center_xyz_mm": center,
                            "dimensions_xyz_mm": dimensions, "bounding_box_mm": bbox(shape),
                            "placement_formula": formula, "evidence": "REFERENCE",
                            "measured": False, "fabrication_allowed": False})

        def box(name, dims, center, role, formula):
            shape = cq.Workplane("XY").box(*dims).translate(center).val()
            add(name, shape, center, dims, role, formula)

        def envelope(name, key, center, formula, role="envelope"):
            dims = [e[key][k] for k in ("width", "depth", "height")]
            box(name, dims, center, role, formula)

        box("belt_volume_AND_keepout", [length, width, thickness], [0, 0, z-thickness/2],
            "belt volume and belt keepout", "[0,0,belt_top-thickness/2]")
        for sign, label in ((-1, "left"), (1, "right")):
            box(f"generic_side_plate_{label}", [length, thickness, diameter],
                [0, sign*(width+thickness)/2, z-diameter/2], "generic visual plate",
                "[0,+/-(belt_width+plate_thickness)/2,belt_top-roller_diameter/2]")
            roller = cq.Solid.makeCylinder(diameter/2, width,
                cq.Vector(sign*length/2, -width/2, z-diameter/2), cq.Vector(0, 1, 0))
            add(f"roller_keepout_{label}", roller, [sign*length/2, 0, z-diameter/2],
                [diameter, width, diameter], "roller keepout",
                "[+/-conveyor_length/2,0,belt_top-roller_diameter/2]")
        envelope("bottle", "bottle", [0, 0, z+bottle["height"]/2], "[0,0,belt_top+bottle_height/2]")
        centers = {"top": [0, 0, z+bottle["height"]+top["height"]],
                   "left": [0, -(width/2+side["depth"]), z+bottle["height"]/2],
                   "right": [0, width/2+side["depth"], z+bottle["height"]/2]}
        for name, center in centers.items():
            key = "camera_top" if name == "top" else "camera_side"
            envelope(f"camera_{name}", key, center,
                     "top: [0,0,belt_top+bottle_height+camera_height]; sides: [0,+/-(belt_width/2+camera_depth),belt_top+bottle_height/2]")
            envelope(f"cable_{name}", "cable_bundle",
                     [center[0], center[1], center[2]+e[key]["height"]/2+cable["height"]],
                     "camera center + [0,0,camera_height/2+cable_height]; local occupancy only")
        envelope("trigger", "trigger", [-length/4, 0, z+bottle["height"]/2],
                 "[-conveyor_length/4,0,belt_top+bottle_height/2]")
        envelope("lighting_top", "lighting_top",
                 [0, top["depth"]/2+e["lighting_top"]["depth"], centers["top"][2]],
                 "[0,camera_top_depth/2+lighting_top_depth,camera_top_z]")
        for sign, label in ((-1, "left"), (1, "right")):
            envelope(f"lighting_side_{label}", "lighting_side",
                     [side["width"]/2+e["lighting_side"]["width"],
                      sign*(width/2+side["depth"]), z+bottle["height"]/2],
                     "[camera_side_width/2+lighting_side_width,+/-(belt_width/2+camera_side_depth),belt_top+bottle_height/2]")
        motor = e["motor_keepout"]
        envelope("motor_keepout", "motor_keepout",
                 [-length/2, width/2+thickness+motor["depth"]/2, z-motor["height"]/2],
                 "[-conveyor_length/2,belt_width/2+plate_thickness+motor_depth/2,belt_top-motor_height/2]",
                 "motor keepout")
        step, stl = OUT/"envelope_b_r01_REFERENCE_ONLY.step", OUT/"envelope_b_r01_REFERENCE_ONLY.stl"
        assembly.export(str(step))
        union = components[0].fuse(*components[1:]).clean()
        if not union.isValid():
            raise ValueError("Invalid visual union")
        cq.exporters.export(union, str(stl))
        manifest["components"] = records
        manifest["bounding_box_mm"] = bbox(union)
        command = [sys.executable, str(ROOT/"scripts/validate_mesh.py"), str(stl)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        (OUT/"mesh_validation.log").write_text(result.stdout+result.stderr)
        manifest["commands"].append({"argv": command, "exit_code": result.returncode})
        if result.returncode:
            raise RuntimeError("Existing mesh validator failed; see mesh_validation.log")
        # Independent readback, including raw STL checks before validator repair.
        raw = trimesh.load_mesh(stl, process=False)
        welded = raw.copy()
        welded.merge_vertices()
        readback = cq.importers.importStep(str(step)).val()
        checks = {
            "raw_mesh_finite": bool(np.isfinite(raw.vertices).all()),
            "welded_without_repair_watertight": bool(welded.is_watertight),
            "winding_consistent": bool(welded.is_winding_consistent),
            "all_mesh_components_positive": all(m.is_volume for m in welded.split(only_watertight=False)),
            "step_valid": readback.isValid(),
            "step_solid_count": len(readback.Solids()) == len(components),
            "step_bounds_match": bool(np.allclose(bbox(readback), bbox(union), rtol=0, atol=1e-5)),
            "stl_bounds_match": bool(np.allclose(raw.bounds, bbox(union), rtol=0, atol=1e-5)),
        }
        write_json(OUT/"readback_validation.json", {
            "provenance": manifest["provenance"], "checks": checks,
            "numerical_readback_epsilon_mm": 1e-5,
            "epsilon_note": "serialization check only; not an equipment tolerance",
            "step_solids": len(readback.Solids()), "mesh_faces": len(raw.faces),
            "scope": "digital geometry only; no engineering validation"})
        if not all(checks.values()):
            raise RuntimeError(f"Readback validation failed: {checks}")
        manifest["validation_gate"] = "PASS"
        exit_code = 0
    except Exception:
        manifest["validation_gate"] = "FAIL"
        (OUT/"failure.log").write_text(traceback.format_exc())
        traceback.print_exc()
    finally:
        manifest["commands"].append({"argv": [sys.executable, str(Path(__file__))], "exit_code": exit_code})
        manifest["artifacts"] = {p.name: {"sha256": sha(p), "provenance": "this manifest"}
                                 for p in sorted(OUT.iterdir()) if p.is_file()}
        write_json(OUT/"manifest.json", manifest)
        paths = [SOURCE, Path(__file__), ROOT/"scripts/validate_mesh.py"] + sorted(OUT.iterdir())
        with (OUT/"SHA256SUMS").open("x") as stream:
            for p in paths:
                stream.write(f"{sha(p)}  {p.relative_to(ROOT)}\n")
    print(f"{manifest['validation_gate']}: reference_only; fabrication_allowed=false; exit_code={exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
