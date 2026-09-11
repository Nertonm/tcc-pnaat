import FreeCAD as A, Part, json
from pathlib import Path
from FreeCAD import Vector as V

P = Path(__file__).resolve().parent
IN = P / "inputs"
out = {}

peca = Part.read(str(IN / "peca-dupla-plataformas.step"))
rail = Part.read(str(IN / "dinr135-007.5.step"))


def _plane_face(center, normal, n1, half=200.0):
    """Explicit large square face in world coords, normal `normal`, spanned by n1 and n1 x normal."""
    n = V(*normal).normalize()
    u = V(*n1).normalize()
    w = n.cross(u)
    c = V(*center)
    pts = [c - u * half - w * half, c + u * half - w * half,
           c + u * half + w * half, c - u * half + w * half, c - u * half - w * half]
    return Part.Face(Part.makePolygon(pts))


def sec_at_y(shape, y, half=200.0):
    pl = _plane_face((-30.5, y, 10.0), (0, 1, 0), (1, 0, 0), half)
    r = shape.common(pl)
    res = []
    for f in r.Faces:
        b = f.BoundBox
        res.append({"area": round(f.Area, 4),
                    "XZ": [round(b.XMin, 3), round(b.ZMin, 3), round(b.XMax, 3), round(b.ZMax, 3)],
                    "wires": len(f.Wires),
                    "outer_edges": len(f.OuterWire.Edges)})
    res.sort(key=lambda d: -d["area"])
    return res


out["sections_Y"] = {}
for y in [73.5, 75, 80, 85, 90, 92.0, 92.5, 93.5, 95, 97.0, 98, 100, 105, 107.0]:
    out["sections_Y"][str(y)] = sec_at_y(peca, y)


def sec_at_x(shape, x, half=200.0):
    pl = _plane_face((x, 70.0, 10.0), (1, 0, 0), (0, 1, 0), half)
    r = shape.common(pl)
    res = []
    for f in r.Faces:
        b = f.BoundBox
        res.append({"area": round(f.Area, 4),
                    "Y_Z": [round(b.YMin, 3), round(b.ZMin, 3), round(b.YMax, 3), round(b.ZMax, 3)]})
    res.sort(key=lambda d: -d["area"])
    return res


out["sections_X"] = {}
for x in [-48.5, -48.18, -47, -46.13, -40, -30.5, -20, -14.87, -12.82, -12.0]:
    out["sections_X"][str(x)] = sec_at_x(peca, x)

# Also: full face dump of peca in the socket region (Y 73..108)
reg = []
for i, f in enumerate(peca.Faces):
    b = f.BoundBox
    if b.YMin > 72.0:
        reg.append({"i": i, "type": type(f.Surface).__name__, "area": round(f.Area, 4),
                    "normal": [round(v, 4) for v in (f.normalAt(0, 0).x, f.normalAt(0, 0).y, f.normalAt(0, 0).z)],
                    "bbox": [round(b.XMin, 3), round(b.YMin, 3), round(b.ZMin, 3),
                             round(b.XMax, 3), round(b.YMax, 3), round(b.ZMax, 3)],
                    "edges": len(f.Edges)})
reg.sort(key=lambda d: -d["area"])
out["peca_faces_Y_gt_72"] = reg

# rail end face geometry (for comparison to the socket mouth)
endf = [f for f in rail.Faces if abs(f.BoundBox.XMax - f.BoundBox.XMin) < 1e-6]
out["rail_end_face"] = {"area": round(endf[0].Area, 5), "edges": len(endf[0].Edges),
                        "outer_edges": len(endf[0].OuterWire.Edges),
                        "bbox": [round(v, 4) for v in (endf[0].BoundBox.XMin, endf[0].BoundBox.YMin,
                                                       endf[0].BoundBox.ZMin, endf[0].BoundBox.XMax,
                                                       endf[0].BoundBox.YMax, endf[0].BoundBox.ZMax)]}

(P / "probe2.json").write_text(json.dumps(out, indent=2))
print("probe2 written")
