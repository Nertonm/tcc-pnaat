import FreeCAD as A, Part, json
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


def mat(cols):
    """cols = (image of e1, image of e2, image of e3)"""
    M = A.Matrix()
    M.A11, M.A21, M.A31 = cols[0]
    M.A12, M.A22, M.A32 = cols[1]
    M.A13, M.A23, M.A33 = cols[2]
    return M


def det(cols):
    c1, c2, c3 = cols
    return round(c1[0] * (c2[1] * c3[2] - c2[2] * c3[1])
                 - c1[1] * (c2[0] * c3[2] - c2[2] * c3[0])
                 + c1[2] * (c2[0] * c3[1] - c2[1] * c3[0]), 6)


r = peca.common(plane_face((-30.5, 95.0, 10.0), (0, 1, 0), (1, 0, 0)))
hole = None
for f in r.Faces:
    for w in f.Wires:
        b = w.BoundBox
        if abs(b.XMin + 48.18) < 0.2 and abs(b.ZMin - 9.9) < 0.2:
            hole = w
out["hole_bbox"] = [round(v, 4) for v in (hole.BoundBox.XMin, hole.BoundBox.ZMin,
                                          hole.BoundBox.XMax, hole.BoundBox.ZMax)]
out["hole_n_edges"] = len(hole.Edges)
pts = []
for e in hole.Edges:
    for p in (e.valueAt(e.FirstParameter), e.valueAt(e.LastParameter)):
        pts.append([round(p.x, 4), round(p.z, 4)])
seen = []
for p in pts:
    if p not in seen:
        seen.append(p)
out["hole_vertices_XZ"] = seen

endface = [f for f in rail.Faces if abs(f.BoundBox.XMax - f.BoundBox.XMin) < 1e-6][0]
rp = []
for e in endface.OuterWire.Edges:
    for p in (e.valueAt(e.FirstParameter), e.valueAt(e.LastParameter)):
        rp.append([round(p.y, 4), round(p.z, 4)])
seenr = []
for p in rp:
    if p not in seenr:
        seenr.append(p)
out["rail_section_vertices_YZ"] = seenr
out["rail_section_area"] = round(endface.Area, 4)

XC, ZBASE, Y0 = -30.5, 10.05, 92.902
out["datum_alignment"] = {
    "xc": XC, "zbase": ZBASE, "y0": Y0,
    "note": ("xc = centre of hole bbox in X; zbase = centre of hole bbox in Z minus centre of rail "
             "section bbox in its height axis; y0 = measured inner end plane of the hole (Y=92.902)")}

Y = (0, 1, 0)
FOLDS = {
    "len_up_f0":    (Y, (0, 0, 1), (1, 0, 0)),
    "len_up_f90":   (Y, (1, 0, 0), (0, 0, -1)),
    "len_up_f180":  (Y, (0, 0, -1), (-1, 0, 0)),
    "len_up_f270":  (Y, (-1, 0, 0), (0, 0, 1)),
    "len_down_f0":  ((0, -1, 0), (0, 0, 1), (1, 0, 0)),
    "len_down_f180": ((0, -1, 0), (0, 0, -1), (-1, 0, 0)),
}
res = {}
for name, cols in FOLDS.items():
    s = rail.copy()
    s.transformShape(mat(cols))
    s.translate(V(XC, Y0, ZBASE))
    d = s.distToShape(peca)
    res[name] = {"det": det(cols), "overlap": round(s.common(peca).Volume, 4), "gap": round(d[0], 4),
                 "bbox": [round(v, 3) for v in (s.BoundBox.XMin, s.BoundBox.YMin, s.BoundBox.ZMin,
                                                s.BoundBox.XMax, s.BoundBox.YMax, s.BoundBox.ZMax)]}
out["folds"] = res

(P / "probe4.json").write_text(json.dumps(out, indent=2))
print("hole_bbox", out["hole_bbox"], "edges", out["hole_n_edges"])
print("rail_section_area", out["rail_section_area"], "verts", len(seenr))
for k, v in res.items():
    print(k, "det", v["det"], "overlap", v["overlap"], "gap", v["gap"], flush=True)
print("probe4 written")
