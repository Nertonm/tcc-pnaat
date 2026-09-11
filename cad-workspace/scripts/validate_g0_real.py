#!/usr/bin/env python3
"""Read-only validation of the Esteira B field collection schema (not CAD approval)."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import yaml


# Explicit dependencies: a P1-only gap must not block P0 or M0.
# P0 is a proposed collection-readiness label, not a mechanical release.
FIELDS = {
    "machine_id": ("text", None, "P0"),
    "manufacturer": ("text", None, "P0"),
    "model": ("text", None, "P0"),
    "xyz_directions": ("text", None, "P0"),
    "physical_origin": ("text", None, "P0"),
    "chassis_length": ("number", "length", "P0"),
    "chassis_width": ("number", "length", "P0"),
    "chassis_height": ("number", "length", "P0"),
    "fixed_interfaces": ("text", None, "P0"),
    "interface_bounds_xyz": ("bounds", "length", "M0"),
    "interface_material_evidence": ("text", None, "M0"),
    "fastener_access": ("text", None, "M0"),
    "belt_width": ("number", "length", "P0"),
    "belt_bounds_xyz": ("bounds", "length", "P0"),
    "moving_parts_and_forbidden_zones": ("text", None, "P0"),
    "forbidden_bounds_xyz": ("bounds", "length", "M0"),
    "datum_A_candidate": ("text", None, "M0"),
    "datum_B_candidate": ("text", None, "M0"),
    "datum_C_candidate": ("text", None, "M0"),
    "hole_inventory": ("text", None, "P0"),
    "hole_centres_xyz": ("vectors", "length", "M0"),
    "hole_diameters": ("numbers", "length", "M0"),
    "interface_thicknesses": ("numbers", "length", "M0"),
    "acrylic_thicknesses": ("numbers", "length", "M0"),
    "camera_top_bounds_xyz": ("bounds", "length", "M0"),
    "camera_left_bounds_xyz": ("bounds", "length", "M0"),
    "camera_right_bounds_xyz": ("bounds", "length", "M0"),
    "lighting_bounds_xyz": ("bounds", "length", "M0"),
    "cable_bounds_xyz": ("bounds", "length", "M0"),
    "retention_candidate": ("text", None, "M0"),
    "trigger_identification": ("text", None, "M0"),
    "trigger_bounds_xyz": ("bounds", "length", "M0"),
    "trigger_to_capture_distance": ("number", "length", "M0"),
    "encoder_identification_and_mount": ("text", None, "M0"),
    "encoder_bounds_xyz": ("bounds", "length", "M0"),
    "encoder_distance_per_count": ("number", "distance_per_count", "P1"),
    "encoder_slip": ("number", "ratio", "P1"),
    "belt_speed": ("number", "speed", "P1"),
    "startup_acceleration": ("number", "acceleration", "P1"),
    "braking_acceleration": ("number", "acceleration", "P1"),
    "tracking_lateral_displacement": ("number", "length", "P1"),
    "vibration_amplitude": ("number", "length", "P1"),
    "vibration_frequency": ("number", "frequency", "P1"),
    "load_configuration": ("text", None, "P1"),
    "dummy_mass": ("number", "mass", "P1"),
    "dummy_cg_xyz": ("vector", "length", "P1"),
    "hardware_masses": ("numbers", "mass", "P1"),
    "hardware_cg_xyz": ("vectors", "length", "P1"),
    "temperature": ("number", "temperature", "P1"),
    "instrument_inventory_and_calibration": ("text", None, "P0"),
    "observations_and_anomalies": ("text", None, "P0"),
}
UNITS = {
    "length": {"mm", "cm", "m"}, "mass": {"g", "kg"},
    "time": {"s", "ms"}, "speed": {"mm/s", "m/s"},
    "acceleration": {"mm/s^2", "m/s^2"}, "frequency": {"Hz"},
    "temperature": {"degC", "K"}, "ratio": {"1", "%"},
    "distance_per_count": {"mm/count", "m/count"},
}
STATES = {"REFERENCE", "MEASURED", "DERIVED", "BLOCKED"}
GATES = ("P0", "M0", "P1")


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently replacing evidence."""


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str) or key in result:
            raise ValueError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def value_type(value, kind):
    if kind == "text":
        return nonempty(value)
    if kind == "number":
        return number(value)
    if not isinstance(value, list) or not value:
        return False
    if kind in {"vector", "numbers"}:
        return all(number(v) for v in value) and (kind != "vector" or len(value) == 3)
    if kind in {"vectors", "bounds"}:
        if not all(value_type(v, "vector") for v in value):
            return False
        return kind != "bounds" or (len(value) % 2 == 0 and all(
            all(a <= b for a, b in zip(value[i], value[i + 1]))
            for i in range(0, len(value), 2)))
    return False


def validate(data):
    blockers = []

    def block(path, reason, gate="P0"):
        blockers.append({"field": path, "reason": reason,
                         "gates": list(GATES[GATES.index(gate):])})

    if not isinstance(data, dict):
        block("$", "YAML root must be a mapping")
        return finish(blockers)
    if data.get("schema_version") != "g0-real-collection-v1":
        block("schema_version", "unsupported or missing schema")
    for key in ("g0_id", "revision"):
        if not nonempty(data.get(key)):
            block(key, "missing identifier")
    for key in ("measured", "reference_only"):
        if type(data.get(key)) is not bool:
            block(key, "explicit boolean required")
    if data.get("fabrication_allowed") is not False:
        block("fabrication_allowed", "must be false; collection cannot authorize fabrication")
    if data.get("measured") is not True:
        block("measured", "physical collection has not been declared measured")
    if data.get("reference_only") is not False:
        block("reference_only", "REFERENCE is not physical measurement")
    if not isinstance(data.get("evidence_state"), str) or data["evidence_state"] not in STATES:
        block("evidence_state", "expected REFERENCE, MEASURED, DERIVED or BLOCKED")
    elif data["evidence_state"] != "MEASURED":
        block("evidence_state", "real collection must be MEASURED to complete")
    units = data.get("units")
    if not isinstance(units, dict):
        units = {}
    for dimension, allowed in UNITS.items():
        gate = "P0" if dimension == "length" else "P1"
        if not isinstance(units.get(dimension), str) or units[dimension] not in allowed:
            block("units." + dimension, "missing/unsupported unit; allowed: " + ", ".join(sorted(allowed)), gate)
    if not isinstance(units.get("state"), str) or units["state"] not in STATES:
        block("units.state", "invalid state")
    elif units["state"] != "MEASURED":
        block("units.state", "unit declaration remains unresolved")

    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    for key in ("collector", "collected_at", "session_id", "location"):
        if not nonempty(provenance.get(key)):
            block("provenance." + key, "required collection provenance is null/absent")
    if provenance.get("state") != "MEASURED":
        block("provenance.state", "collection provenance must be MEASURED")

    # Hash syntax and ID links are checked here; file bytes are checked independently in field review.
    file_ids = set()
    photos = data.get("files")
    if not isinstance(photos, list) or not photos:
        block("files", "photo/file catalogue is absent")
        photos = []
    for i, item in enumerate(photos):
        path = f"files[{i}]"
        if not isinstance(item, dict):
            block(path, "file entry must be a mapping")
            continue
        for key in ("id", "path", "captured_at", "author", "description"):
            if not nonempty(item.get(key)):
                block(path + "." + key, "required file provenance is null/absent")
        sha = item.get("sha256")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
            block(path + ".sha256", "required SHA-256 is absent or malformed")
        if item.get("state") != "MEASURED":
            block(path + ".state", "file must document actual collection, not reference")
        file_id = item.get("id")
        if nonempty(file_id):
            if file_id in file_ids:
                block(path + ".id", "duplicate file ID")
            file_ids.add(file_id)

    records = data.get("measurements")
    if not isinstance(records, dict):
        records = {}
    for extra in sorted(set(records) - set(FIELDS)):
        block("measurements." + extra, "unknown field; extend schema explicitly before acceptance")
    for name, (kind, dimension, gate) in FIELDS.items():
        path = "measurements." + name
        entry = records.get(name)
        if not isinstance(entry, dict):
            block(path, "essential record absent/null", gate)
            continue
        state = entry.get("state")
        if not isinstance(state, str):
            state = None
        if state not in STATES:
            block(path + ".state", "expected REFERENCE, MEASURED, DERIVED or BLOCKED", gate)
        elif state in {"BLOCKED", "REFERENCE"}:
            block(path + ".state", state + " cannot satisfy a real measurement gate", gate)
        if type(entry.get("measured")) is not bool or entry["measured"] != (state == "MEASURED"):
            block(path + ".measured", "must be true exactly for MEASURED evidence", gate)
        if entry.get("conflict") is not False:
            block(path + ".conflict", "conflict absent, unresolved or declared; preserve raw evidence", gate)
        if not value_type(entry.get("value"), kind):
            block(path + ".value", "essential value null/invalid; expected " + kind, gate)
        if dimension:
            unit = entry.get("unit")
            if not isinstance(unit, str) or unit not in UNITS[dimension]:
                block(path + ".unit", "numeric quantity requires explicit " + dimension + " unit", gate)
        elif entry.get("unit") != "not_applicable":
            block(path + ".unit", "text observation requires explicit not_applicable", gate)
        if state in {"MEASURED", "DERIVED"} or entry.get("measured") is True:
            for key in ("method", "limitations"):
                if not nonempty(entry.get(key)):
                    block(path + "." + key, "evidence metadata required", gate)
            ids = entry.get("provenance_ids")
            if not isinstance(ids, list) or not ids or any(
                not isinstance(v, str) or v not in file_ids for v in ids
            ):
                block(path + ".provenance_ids", "must reference existing photo/raw-file IDs", gate)
            uncertainty = entry.get("uncertainty")
            if not isinstance(uncertainty, dict):
                uncertainty = {}
            if dimension:
                if not number(uncertainty.get("value")) or uncertainty["value"] < 0:
                    block(path + ".uncertainty", "nonnegative finite uncertainty required", gate)
                if uncertainty.get("unit") != entry.get("unit"):
                    block(path + ".uncertainty.unit", "must match measurement unit", gate)
            elif uncertainty.get("value") != "not_applicable":
                block(path + ".uncertainty", "qualitative observation needs explicit not_applicable", gate)
            if not nonempty(uncertainty.get("basis")):
                block(path + ".uncertainty.basis", "uncertainty basis/qualitative justification required", gate)
        if state == "MEASURED" or entry.get("measured") is True:
            if not nonempty(entry.get("instrument")):
                block(path + ".instrument", "MEASURED requires instrument/observation means", gate)
            repetitions = entry.get("repetitions")
            if type(repetitions) is not int or repetitions < 1:
                block(path + ".repetitions", "MEASURED requires positive integer count", gate)
            raw = entry.get("raw_readings")
            if not isinstance(raw, list) or not raw or len(raw) != repetitions or any(
                not value_type(v, kind) for v in raw
            ):
                block(path + ".raw_readings", "raw repetitions must match value shape and repetition count; same unit", gate)
        if state == "DERIVED":
            if not nonempty(entry.get("equation")):
                block(path + ".equation", "DERIVED requires explicit equation", gate)
            sources = entry.get("source_ids")
            if not isinstance(sources, list) or not sources or any(
                not isinstance(v, str) or v == name or v not in FIELDS or
                not isinstance(records.get(v), dict) or records[v].get("state") != "MEASURED"
                for v in sources
            ):
                block(path + ".source_ids", "DERIVED requires direct MEASURED source IDs (no cycles/reference)", gate)
            else:
                for source in sources:
                    if any(b["field"].startswith("measurements." + source + ".") for b in blockers):
                        block(path + ".source_ids", "invalid source: " + source, gate)
    # Propagate even when a derived record appears before its measured source.
    for name, (_, _, gate) in FIELDS.items():
        entry = records.get(name)
        if isinstance(entry, dict) and entry.get("state") == "DERIVED" and isinstance(entry.get("source_ids"), list):
            for source in entry["source_ids"]:
                if isinstance(source, str) and any(b["field"].startswith("measurements." + source + ".") for b in blockers):
                    block("measurements." + name + ".source_ids", "invalid measured source: " + source, gate)
    return finish(blockers)


def finish(blockers):
    return {
        "status": "BLOCKED_G0_INCOMPLETE" if blockers else "PASS_G0_COLLECTION_SCHEMA",
        "gates": {gate: "INCOMPLETE" if any(gate in b["gates"] for b in blockers) else "READY" for gate in GATES},
        "fabrication_allowed": False,
        "scope": "collection schema only; READY is not mechanical approval; file hashes need independent byte verification",
        "blockers": blockers,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yaml_path", type=Path)
    args = parser.parse_args()
    sha = None
    try:
        content = args.yaml_path.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        result = validate(yaml.load(content.decode("utf-8"), Loader=UniqueLoader))
    except (OSError, UnicodeError, yaml.YAMLError, ValueError, RecursionError, OverflowError) as exc:
        result = finish([{"field": "$", "reason": str(exc), "gates": list(GATES)}])
    result["input"] = {"path": str(args.yaml_path), "sha256": sha}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["blockers"] else 0


if __name__ == "__main__":
    sys.exit(main())
