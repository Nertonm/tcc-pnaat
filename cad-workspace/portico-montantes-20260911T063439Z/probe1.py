import FreeCAD as A, Part, json, math
from pathlib import Path
from FreeCAD import Vector as V

P = Path(__file__).resolve().parent
IN = P / "inputs"


def bb(s):
    b = s.BoundBox
    return [round(b.XMin, 4), round(b.YMin, 4), round(b.ZMin, 4),
            round(b.XMax, 4), round(b.YMax, 4), round(b.ZMax, 4)]


def face_info(f):
    t = type(f.Surface).__name__
    d = {
        "type": t,
        "area": round(f.Area, 4),
        "normal": [round(x, 4) for x in (f.normalAt(0, 0).x, f.normalAt(0, 0).y, f.normalAt(0, 0).z)],
        "center": [round(x, 4) for x in f.CenterOfMass],
        "bbox": bb(f),
        "edges": len(f.Edges),
        "outerwire_edges": len(f.OuterWire.Edges),
    }
    if t == "Cylinder":
        ax = f.Surface.Axis
        d["axis"] = [round(ax.x, 4), round(ax.y, 4), round(ax.z, 4)]
        d["radius"] = round(f.Surface.Radius, 4)
    return d


out = {}

# ---------- rail ----------
r = Part.read(str(IN / "dinr135-007.5.step"))
rs = r.Solids[0]
out["rail"] = {"valid": r.isValid(), "solids": len(r.Solids), "closed": rs.isClosed(),
               "volume": round(r.Volume, 4), "bbox": bb(r), "faces": len(r.Faces),
               "shells": len(r.Shells)}
# section extraction: end faces normal to X
endf = [f for f in r.Faces if abs(f.BoundBox.XMax - f.BoundBox.XMin) < 1e-6]
out["rail_section_faces"] = [face_info(f) for f in endf]
if endf:
    a = endf[0].Area
    out["rail_section_area"] = round(a, 4)
    out["rail_volume_if_prismatic"] = round(a * 75.0, 4)
    out["rail_volume_delta"] = round(r.Volume - a * 75.0, 4)
    out["rail_length"] = 75.0
# any non-prismatic feature? list cylinder faces (holes/slots)
out["rail_cylinders"] = [face_info(f) for f in r.Faces if type(f.Surface).__name__ == "Cylinder"]
out["rail_all_faces"] = [face_info(f) for f in r.Faces]

# ---------- peca oficial ----------
pc = Part.read(str(IN / "peca-dupla-plataformas.step"))
out["peca"] = {"valid": pc.isValid(), "solids": len(pc.Solids), "volume": round(pc.Volume, 4),
               "bbox": bb(pc), "faces": len(pc.Faces), "shells": len(pc.Shells)}
cyls = [f for f in pc.Faces if type(f.Surface).__name__ == "Cylinder"]
out["peca_cylinders"] = [face_info(f) for f in cyls]
planes = [f for f in pc.Faces if type(f.Surface).__name__ == "Plane"]
planes.sort(key=lambda f: -f.Area)
out["peca_planes_top25"] = [face_info(f) for f in planes[:25]]
out["peca_plane_count"] = len(planes)
out["peca_surface_types"] = {}
for f in pc.Faces:
    k = type(f.Surface).__name__
    out["peca_surface_types"][k] = out["peca_surface_types"].get(k, 0) + 1

# ---------- M6 bracket ----------
mb = Part.read(str(IN / "DIN-Rail-Bracket-4mm-component0.stl.brep"))
out["m6"] = {"valid": mb.isValid(), "solids": len(mb.Solids), "volume": round(mb.Volume, 4),
             "bbox": bb(mb), "faces": len(mb.Faces)}
mplanes = [f for f in mb.Faces if type(f.Surface).__name__ == "Plane"]
mplanes.sort(key=lambda f: -f.Area)
out["m6_planes_top12"] = [face_info(f) for f in mplanes[:12]]
out["m6_cylinders"] = [face_info(f) for f in mb.Faces if type(f.Surface).__name__ == "Cylinder"]

# ---------- G-clamp ----------
gc = Part.read(str(IN / "G-clamp_Tripod-component0.stl.brep"))
out["clamp"] = {"valid": gc.isValid(), "solids": len(gc.Solids), "volume": round(gc.Volume, 4),
                "bbox": bb(gc), "faces": len(gc.Faces)}
gcyls = [f for f in gc.Faces if type(f.Surface).__name__ == "Cylinder"]
gcyls.sort(key=lambda f: -f.Area)
out["clamp_cylinders_top10"] = [face_info(f) for f in gcyls[:10]]

# ---------- angle adapter 100mm ----------
try:
    aa = Part.read(str(IN / "din-rail_right_angle_adapter-100mm.step"))
    out["angle"] = {"valid": aa.isValid(), "solids": len(aa.Solids), "volume": round(aa.Volume, 4),
                    "bbox": bb(aa), "faces": len(aa.Faces)}
    out["angle_solids"] = [{"volume": round(s.Volume, 3), "bbox": bb(s), "faces": len(s.Faces)}
                           for s in aa.Solids]
except Exception as e:
    out["angle_error"] = repr(e)

(P / "probe.json").write_text(json.dumps(out, indent=2))
print("probe written", len(json.dumps(out)))
