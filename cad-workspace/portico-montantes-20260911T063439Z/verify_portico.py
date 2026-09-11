"""Independent re-open: fresh process, import the STEP and reopen the FCStd.

Compares solid counts, per-object volumes and the global bounding box against
the values the build process recorded.  "Export returned" is not success;
"reopens with the expected geometry" is.
"""

import json
import sys
from pathlib import Path

import FreeCAD as A
import Part

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import lib_geo as G  # noqa: E402

BUILD = json.loads((ROOT / "build-measurements.json").read_text())
OUT = ROOT / "exports"
STEP = OUT / "portico-montantes.step"
FCSTD = OUT / "portico-montantes.FCStd"
TOL_VOL = 1e-3
TOL_BBOX = 1e-6

out = {"stage": "verify", "gates": {}}
out["files"] = {"step_bytes": STEP.stat().st_size, "step_sha256": G.sha256(STEP),
                "fcstd_bytes": FCSTD.stat().st_size, "fcstd_sha256": G.sha256(FCSTD)}

build_vols = {n: v["volume"] for n, v in BUILD["parts"].items()}
build_solids = sum(v["solids"] for v in BUILD["parts"].values())
build_vol = round(sum(build_vols.values()), 6)
build_bbox = [round(min(v["bbox"][i] for v in BUILD["parts"].values()), 6) if i < 3
              else round(max(v["bbox"][i] for v in BUILD["parts"].values()), 6)
              for i in range(6)]
out["build_expected"] = {"objects": len(build_vols), "solids": build_solids,
                         "total_volume": build_vol, "bbox": build_bbox}

# ---------------------------------------------------------------- STEP ------
comp = Part.read(str(STEP))
bb = comp.BoundBox
step_bbox = [round(v, 6) for v in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)]
step_vol = round(comp.Volume, 6)
step_solids = len(comp.Solids)
out["step"] = {"shape_type": comp.ShapeType, "solids": step_solids,
               "total_volume": step_vol, "bbox": step_bbox, "valid": bool(comp.isValid()),
               "sub_shapes": len(comp.SubShapes),
               "sorted_solid_volumes": sorted(round(s.Volume, 4) for s in comp.Solids)}
out["gates"]["step_solid_count"] = step_solids == build_solids
out["gates"]["step_total_volume"] = abs(step_vol - build_vol) < TOL_VOL
out["gates"]["step_bbox"] = all(abs(a - b) < TOL_BBOX for a, b in zip(step_bbox, build_bbox))
out["gates"]["step_valid"] = bool(comp.isValid())
# per-body identity without relying on STEP names: the multiset of volumes
out["gates"]["step_per_body_volumes"] = all(
    abs(a - b) < TOL_VOL
    for a, b in zip(out["step"]["sorted_solid_volumes"], sorted(round(v, 4) for v in build_vols.values())))

# --------------------------------------------------------------- FCStd ------
for d in list(A.listDocuments()):
    A.closeDocument(d)
A.openDocument(str(FCSTD))
fdoc = list(A.listDocuments().values())[0]
fobjs = {o.Name: o for o in fdoc.Objects if hasattr(o, "Shape") and o.Shape is not None}
fvol = {n: round(o.Shape.Volume, 6) for n, o in fobjs.items()}
fsol = {n: len(o.Shape.Solids) for n, o in fobjs.items()}
fvalid = {n: bool(o.Shape.isValid()) for n, o in fobjs.items()}
fbb = [min(o.Shape.BoundBox.XMin for o in fobjs.values()),
       min(o.Shape.BoundBox.YMin for o in fobjs.values()),
       min(o.Shape.BoundBox.ZMin for o in fobjs.values()),
       max(o.Shape.BoundBox.XMax for o in fobjs.values()),
       max(o.Shape.BoundBox.YMax for o in fobjs.values()),
       max(o.Shape.BoundBox.ZMax for o in fobjs.values())]
out["fcstd"] = {"object_count": len(fobjs), "objects": sorted(fobjs),
                "volumes": fvol, "solids": fsol, "valid": fvalid,
                "bbox": [round(v, 6) for v in fbb]}
out["gates"]["fcstd_object_set"] = set(fobjs) == set(build_vols)
out["gates"]["fcstd_per_object_volume"] = all(
    abs(fvol.get(n, -1) - build_vols[n]) < TOL_VOL for n in build_vols)
out["gates"]["fcstd_single_solid_each"] = all(v == 1 for v in fsol.values())
out["gates"]["fcstd_all_valid"] = all(fvalid.values())
out["gates"]["fcstd_bbox"] = all(abs(a - b) < TOL_BBOX for a, b in zip(out["fcstd"]["bbox"],
                                                                      build_bbox))

# ------------------------------- producer -> consumer interference re-check --
if set(fobjs) >= {"JuncaoA", "MontanteA", "Travessa"}:
    out["reopen_interference"] = {
        "juncao_upright": round(fobjs["JuncaoA"].Shape.common(fobjs["MontanteA"].Shape).Volume, 6),
        "juncao_crossbar": round(fobjs["JuncaoA"].Shape.common(fobjs["Travessa"].Shape).Volume, 6)}
    out["gates"]["reopen_zero_interference"] = all(
        v <= 1e-3 for v in out["reopen_interference"].values())

out["gates"]["roundtrip_pass"] = all(out["gates"].values())
(ROOT / "verify-results.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out["gates"], indent=2))
print("roundtrip_pass:", out["gates"]["roundtrip_pass"])
