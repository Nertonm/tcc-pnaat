#!/usr/bin/env python3
"""REFERENCE ONLY: schematic envelopes, never fabrication or equipment geometry."""
import hashlib
import json
import math
import os
import re
import OCP
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
OUT = ROOT / "exports/reference-envelope/r03"


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
        "revision": "r03", "reference_id": None, "status": "reference_only",
        "reference_only": True,
        "fabrication_allowed": False, "measured": False, "units": "mm",
        "tools": {"cadquery": cq.__version__, "OCP": OCP.__version__,
                  "trimesh": trimesh.__version__, "numpy": np.__version__, "PyYAML": yaml.__version__},
        "validation_scope": "Digital reference envelopes only; not mechanical validation",
        "yaml_sha256": sha(SOURCE), "script_sha256": sha(Path(__file__)),
        "provenance": {
            "source": str(SOURCE.relative_to(ROOT)),
            "script": str(Path(__file__).relative_to(ROOT)),
            "geometry_inputs": ["reference_scenario.selected_nominal",
                                "reference_scenario.envelopes_mm"],
            "kind": "reference_envelope", "evidence": "SPECULATIVE",
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
    audit_checks = []
    preservation = {}

    def command(argv):
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        audit_checks.append({"argv": argv, "exit_code": result.returncode,
                             "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError(f"Audit command failed: {argv}")
        return result.stdout

    def historical_hashes():
        return {str(p.relative_to(ROOT)): sha(p)
                for directory in (ROOT/"exports/reference-envelope/r01", ROOT/"exports/reference-envelope/r02")
                if directory.exists() for p in sorted(directory.rglob("*")) if p.is_file()}

    def statuses():
        return {name: command(["git", "--no-optional-locks", "-C", str(ROOT.parent/name),
                              "status", "--porcelain=v1", "--untracked-files=all", "--", ".", ":!latex-workspace"])
                for name in ("ctgit", "github")}

    try:
        # Optional environment metadata; no host/container gate.
        before_history, before_external = historical_hashes(), statuses()
        data = yaml.safe_load(SOURCE.read_text())
        manifest["reference_id"] = data["reference_id"]
        scenario = data["reference_scenario"]
        if (data["status"] != "reference_only" or data["units"] != "mm" or scenario["status"] != "reference_only"
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
                            "placement_formula": formula, "evidence": "SPECULATIVE",
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
        step, stl = OUT/"envelope_b_r03_REFERENCE_ONLY.step", OUT/"envelope_b_r03_REFERENCE_ONLY.stl"
        assembly.export(str(step))
        step_text, replacements = re.subn(
            r"(FILE_NAME\s*\(\s*'[^']*'\s*,\s*)'[^']*'",
            r"\1'1970-01-01T00:00:00'", step.read_text(), count=1)
        if replacements != 1:
            raise ValueError("STEP FILE_NAME timestamp not found")
        step.write_text(step_text)
        manifest["step_header_timestamp"] = "1970-01-01T00:00:00 (canonical, not execution time)"
        union = components[0].fuse(*components[1:]).clean()
        if not union.isValid():
            raise ValueError("Invalid visual union")
        cq.exporters.export(union, str(stl), tolerance=0.1, angularTolerance=0.1)
        manifest["components"] = records
        manifest["bounding_box_mm"] = bbox(union)
        command = [sys.executable, str(ROOT/"scripts/validate_mesh.py"), str(stl)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        (OUT/"mesh_validation.log").write_text(result.stdout+result.stderr)
        manifest["commands"].append({"argv": command, "exit_code": result.returncode})
        if result.returncode:
            raise RuntimeError("Existing mesh validator failed; see mesh_validation.log")
        # Explicit vertex welding only: no repair, hole filling or face removal.
        raw = trimesh.load_mesh(stl, process=False)
        welded = raw.copy()
        welded.merge_vertices()
        readback = cq.importers.importStep(str(step)).val()
        solids = readback.Solids()
        mesh_parts = welded.split(only_watertight=False)
        # One-to-one serialized solid match, including every keepout, by OCC difference.
        unmatched = list(solids)
        coverage = {}
        volume_epsilon = 1e-5  # mm^3, numerical serialization only
        for record, original in zip(records, components):
            match = next((solid for solid in unmatched
                          if np.allclose(bbox(solid), bbox(original), rtol=0, atol=1e-5)
                          and original.cut(solid).Volume() <= volume_epsilon
                          and solid.cut(original).Volume() <= volume_epsilon), None)
            coverage[record["name"]] = match is not None
            if match is not None:
                unmatched.remove(match)
        required_keepouts = {"belt_volume_AND_keepout", "roller_keepout_left",
                             "roller_keepout_right", "motor_keepout"}
        # Probe tessellated boundary vertices of each forbidden volume against STL.
        # Interior overlap remains occupied by the visual boolean union.
        stl_keepouts = {}
        for record, original in zip(records, components):
            if record["name"] not in required_keepouts:
                continue
            vertices, _ = original.tessellate(0.1, 0.1)
            points = np.array([v.toTuple() for v in vertices])
            distances = trimesh.proximity.signed_distance(welded, points)
            stl_keepouts[record["name"]] = bool(np.isfinite(distances).all()
                                                       and (distances >= -0.1).all())
        manifest["bounding_boxes_mm"] = {"step": bbox(readback), "stl": raw.bounds.tolist()}
        checks = {
            "all_components_preserved_in_step": all(coverage.values()) and not unmatched,
            "all_required_keepouts_present": required_keepouts <= coverage.keys()
                and all(coverage[k] for k in required_keepouts)
                and set(stl_keepouts) == required_keepouts and all(stl_keepouts.values()),
            "step_each_solid_valid_positive_finite": all(s.isValid() and np.isfinite(s.Volume())
                and s.Volume() > 0 and np.isfinite(bbox(s)).all() for s in solids),
            "mesh_component_count": len(mesh_parts) == len(union.Solids()),
            "positive_finite_mesh_volume": bool(np.isfinite(welded.volume) and welded.volume > 0),
            "step_vs_stl_bounds": bool(np.allclose(bbox(readback), raw.bounds, rtol=0, atol=0.1)),
            "raw_mesh_finite": bool(np.isfinite(raw.vertices).all() and np.isfinite(raw.faces).all() and len(raw.faces) > 0),
            "welded_without_repair_watertight": bool(welded.is_watertight),
            "winding_consistent": bool(welded.is_winding_consistent),
            "all_mesh_components_positive": bool(mesh_parts) and all(m.is_volume and np.isfinite(m.volume) and m.volume > 0 for m in mesh_parts),
            "step_valid": readback.isValid(),
            "step_solid_count": len(readback.Solids()) == len(components),
            "step_bounds_match": bool(np.allclose(bbox(readback), bbox(union), rtol=0, atol=1e-5)),
            "stl_bounds_match": bool(np.allclose(raw.bounds, bbox(union), rtol=0, atol=0.1)),
        }
        write_json(OUT/"readback_validation.json", {
            "provenance": manifest["provenance"], "checks": checks,
            "step_component_coverage": coverage, "stl_keepout_boundary_coverage": stl_keepouts,
            "keepout_scope": "STEP OCC differences; STL sampled tessellated boundaries within 0.1 mm; no physical clearance validation",
            "processing": "load_mesh(process=False), copy, merge_vertices(); no mesh repair",
            "mesh_components": len(mesh_parts), "expected_union_components": len(union.Solids()),
            "bounding_boxes_mm": manifest["bounding_boxes_mm"],
            "max_step_stl_bounds_delta_mm": float(np.max(np.abs(np.array(bbox(readback))-raw.bounds))),
            "step_readback_epsilon_mm": 1e-5,
            "stl_tessellation_deflection_mm": 0.1,
            "stl_angular_tolerance_rad": 0.1,
            "stl_bounds_epsilon_mm": 0.1,
            "epsilon_note": "serialization check only; not an equipment tolerance",
            "step_solids": len(readback.Solids()), "mesh_faces": len(raw.faces),
            "scope": "digital geometry only; no engineering validation"})
        if not all(checks.values()):
            raise RuntimeError(f"Readback validation failed: {checks}")
        preservation = {"history_sha256": before_history,
                        "history_unchanged": before_history == historical_hashes(),
                        "external_status_unchanged": before_external == statuses(),
                        "external_scope": "read-only git status excluding latex-workspace; no external writes"}
        command(["git", "--no-optional-locks", "status", "--short", "--untracked-files=all",
                 "--", ".", ":!latex-workspace"])
        if not preservation["history_unchanged"] or not preservation["external_status_unchanged"]:
            raise RuntimeError("Preservation gate failed")
        manifest["validation_gate"] = "PASS"
        exit_code = 0
    except Exception:
        manifest["validation_gate"] = "FAIL"
        (OUT/"failure.log").write_text(traceback.format_exc())
        traceback.print_exc()
    finally:
        if not (OUT/"readback_validation.json").exists():
            write_json(OUT/"readback_validation.json", {
                "gate": "FAIL", "reason": "generation or prerequisite failed; see failure.log",
                "reference_only": True, "fabrication_allowed": False})
        manifest["status"] = "PASS_REFERENCE_ONLY" if exit_code == 0 else "FAIL_REFERENCE_ONLY"
        manifest["artifacts"] = {p.name: {"sha256": sha(p), "provenance": "this manifest"}
                                 for p in sorted(OUT.iterdir()) if p.is_file()}
        manifest["source"] = {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)}
        manifest["script"] = {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))}
        write_json(OUT/"manifest.json", manifest)
        # Directed hashes: audit -> manifest; SHA256SUMS -> audit and payloads.
        # Manifest excludes itself, audit and SHA256SUMS; no circular hashes.
        write_json(OUT/"execution_audit.json", {
            "reference_only": True, "measured": False, "fabrication_allowed": False,
            "provenance": {"manifest_sha256": sha(OUT/"manifest.json")},
            "commands": manifest["commands"] + [
                {"argv": [sys.executable, str(Path(__file__))], "exit_code": exit_code}],
            "environment": manifest["environment"],
            "preservation": preservation,
            "checks": audit_checks,
            "write_scope": [str(OUT.relative_to(ROOT))],
        })
        paths = [SOURCE, Path(__file__), ROOT/"scripts/validate_mesh.py"] + [
            p for p in sorted(OUT.iterdir()) if p.name not in {"manifest.json", "SHA256SUMS"}]
        with (OUT/"SHA256SUMS").open("x") as stream:
            for p in paths:
                stream.write(f"{sha(p)}  {p.relative_to(ROOT)}\n")
    print(f"{manifest['status']}; fabrication_allowed=false; exit_code={exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
