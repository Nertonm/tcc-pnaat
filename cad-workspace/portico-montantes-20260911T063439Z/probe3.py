import FreeCAD as A, Part, json, time
from pathlib import Path
from FreeCAD import Vector as V

P = Path(__file__).resolve().parent
IN = P / "inputs"
out = {}

peca = Part.read(str(IN / "peca-dupla-plataformas.step"))
rail = Part.read(str(IN / "dinr135-007.5.step"))


def plane_face(center, normal, n1, half=200.0):
    n = V(*normal).normalize(); u = V(*n1).normalize(); w = n.cross(u); c = V(*center)
    pts = [c - u * half - w * half, c + u * half - w * half,
           c + u * half + w * half, c - u * half + w * half, c - u * half - w * half]
    return Part.Face(Part.makePolygon(pts))


def sec(shape, center, normal, n1):
    r = shape.common(plane_face(center, normal, n1))
    res = []
    for f in r.Faces:
        b = f.BoundBox
        res.append({"area": round(f.Area, 4),
                    "bbox": [round(b.XMin, 3), round(b.YMin, 3), round(b.ZMin, 3),
                             round(b.XMax, 3), round(b.YMax, 3), round(b.ZMax, 3)],
                    "wires": [{"bbox": [round(w.BoundBox.XMin, 3), round(w.BoundBox.YMin, 3),
                                        round(w.BoundBox.ZMin, 3), round(w.BoundBox.XMax, 3),
                                        round(w.BoundBox.YMax, 3), round(w.BoundBox.ZMax, 3)],
                               "edges": len(w.Edges)} for w in f.Wires]})
    res.sort(key=lambda d: -d["area"])
    return res


out["secY"] = {}
for y in [74, 76, 78, 80, 82, 85, 88, 90, 91, 92.0, 92.5, 92.902, 93.5, 95, 97.0]:
    out["secY"][str(y)] = sec(peca, (-30.5, y, 10.0), (0, 1, 0), (1, 0, 0))
    print("secY", y, flush=True)

out["secZ"] = {}
for z in [6.0, 8.0, 9.5, 9.9, 10.5, 12.0, 15.0, 17.0, 17.5, 18.5]:
    out["secZ"][str(z)] = sec(peca, (-30.5, 85.0, z), (0, 0, 1), (1, 0, 0))
    print("secZ", z, flush=True)

M = A.Matrix()
M.A11, M.A12, M.A13 = 0, 0, 1
M.A21, M.A22, M.A23 = 1, 0, 0
M.A31, M.A32, M.A33 = 0, 1, 0   # localX->+Y, localY->+Z, localZ->+X


def placed(y0, z0, xc, sign=1):
    r = rail.copy()
    if sign < 0:
        Mm = A.Matrix()
        Mm.A11, Mm.A12, Mm.A13 = 0, 0, -1
        Mm.A21, Mm.A22, Mm.A23 = -1, 0, 0
        Mm.A31, Mm.A32, Mm.A33 = 0, 1, 0
        r.transformShape(Mm)
    else:
        r.transformShape(M)
    r.translate(V(xc, y0, z0))
    return r


def overlap(shape):
    return round(shape.common(peca).Volume, 4)


out["hypA_base_z9.9_cx-30.5"] = {}
for y0 in [-20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90]:
    out["hypA_base_z9.9_cx-30.5"][str(y0)] = overlap(placed(y0, 9.9, -30.5))
    print("hypA", y0, flush=True)

out["hypB_base_z10.0"] = {}
for y0 in [20, 40, 60, 80]:
    out["hypB_base_z10.0"][str(y0)] = overlap(placed(y0, 10.0, -30.5))

out["hypC_flip_base_z17.4"] = {}
for y0 in [20, 40, 60, 80]:
    out["hypC_flip_base_z17.4"][str(y0)] = overlap(placed(y0, 17.4, -30.5, sign=-1))

(P / "probe3.json").write_text(json.dumps(out, indent=2))
print("probe3 written")
