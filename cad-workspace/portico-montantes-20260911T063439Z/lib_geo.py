"""Shared geometry helpers for the PNAAT portico candidate (freecadcmd).

Conventions
-----------
* Rail local frame (as delivered by the Winford STEP): X = length, Y = height
  0..7.5 (base plate at Y=0, open hat mouth at Y=7.5), Z = width +-17.5.
* The rail cross-section is an open "top hat" band: it is NOT a solid block.
  The female channel of a mating part must therefore be the prism of that same
  band, so the hollow of the hat stays filled by the mating part's core.
* All placements in this pipeline are derived from measured datums (face
  planes, hole/slot axes, bbox centres), never from a translation sweep.
"""

import hashlib
import json
import time

import FreeCAD as A
import Part
from FreeCAD import Vector as V

TOL = 1e-7


# --------------------------------------------------------------------------- #
# measurement primitives
# --------------------------------------------------------------------------- #
def stats(shape):
    b = shape.BoundBox
    return {
        "valid": bool(shape.isValid()),
        "solids": len(shape.Solids),
        "closed": bool(shape.isClosed()),
        "volume": round(shape.Volume, 6),
        "area": round(shape.Area, 6),
        "faces": len(shape.Faces),
        "bbox": [round(x, 6) for x in (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)],
    }


def overlap_volume(a, b):
    """Exact boolean intersection volume between two shapes."""
    return round(a.common(b).Volume, 6)


def min_gap(a, b):
    """Exact closest distance between two shapes (0.0 == in contact)."""
    return round(a.distToShape(b)[0], 6)


def contact_area(a, b, tol=1e-7, max_pairs=40000, budget_s=900.0):
    """Summed area of coincident/touching face patches between two shapes.

    Returns (total_mm2, by_axis, pairs_tested, seconds, status) where by_axis
    splits the area by the dominant world normal of each patch ("X"/"Y"/"Z").

    `common(solid, solid).Area` is not trustworthy for a dimension-reduced
    (face) intersection, so the contact is measured face-pair by face-pair with
    an AABB broad phase.  Calibrate with `self_test_contact_area()`.
    """
    fb = [(f, f.BoundBox) for f in b.Faces]
    total = 0.0
    by_axis = {"X": 0.0, "Y": 0.0, "Z": 0.0}
    pairs = 0
    t0 = time.time()
    status = "ok"
    for fa in a.Faces:
        ba = fa.BoundBox
        for f2, b2 in fb:
            if (ba.XMax < b2.XMin - tol or ba.XMin > b2.XMax + tol
                    or ba.YMax < b2.YMin - tol or ba.YMin > b2.YMax + tol
                    or ba.ZMax < b2.ZMin - tol or ba.ZMin > b2.ZMax + tol):
                continue
            if pairs >= max_pairs or (time.time() - t0) > budget_s:
                status = "truncated"
                return (round(total, 6), {k: round(v, 6) for k, v in by_axis.items()},
                        pairs, round(time.time() - t0, 3), status)
            try:
                c = fa.common(f2)
            except Exception:
                pairs += 1
                continue
            for pf in c.Faces:
                ar = pf.Area
                total += ar
                n = pf.normalAt(0, 0)
                ax = max(("X", abs(n.x)), ("Y", abs(n.y)), ("Z", abs(n.z)), key=lambda t: t[1])[0]
                by_axis[ax] += ar
            pairs += 1
    return (round(total, 6), {k: round(v, 6) for k, v in by_axis.items()},
            pairs, round(time.time() - t0, 3), status)


def self_test_contact_area(verbose=True):
    """Calibrate the contact-area measurer on a case with an exact answer.

    Two 20x20x20 boxes sharing one 20x20 face must report 400.000 mm^2 of
    contact (all of it on X-normal patches) and 0.0 mm^3 of intersection.
    """
    a = Part.makeBox(20, 20, 20, V(0, 0, 0))
    b = Part.makeBox(20, 20, 20, V(20, 0, 0))
    area, axes, pairs, secs, status = contact_area(a, b)
    vol = overlap_volume(a, b)
    ok = (abs(area - 400.0) < 1e-6 and abs(axes["X"] - 400.0) < 1e-6
          and abs(vol) < 1e-9 and status == "ok")
    res = {"expected_area": 400.0, "measured_area": area, "measured_by_axis": axes,
           "measured_overlap": vol, "pairs_tested": pairs, "seconds": secs,
           "status": status, "pass": ok}
    # a second calibration: 22 mm apart => no contact at all
    c = Part.makeBox(20, 20, 20, V(22, 0, 0))
    area2, axes2, _, _, st2 = contact_area(a, c)
    res["separated_measured_area"] = area2
    res["separated_pass"] = abs(area2) < 1e-9 and st2 == "ok"
    if verbose:
        print("self_test_contact_area:", json.dumps(res), flush=True)
    return res


# --------------------------------------------------------------------------- #
# transforms
# --------------------------------------------------------------------------- #
def mat_from_columns(c1, c2, c3):
    """Rotation matrix whose columns are the images of the local e1,e2,e3."""
    M = A.Matrix()
    M.A11, M.A21, M.A31 = c1
    M.A12, M.A22, M.A32 = c2
    M.A13, M.A23, M.A33 = c3
    return M


def det3(c1, c2, c3):
    return round(c1[0] * (c2[1] * c3[2] - c2[2] * c3[1])
                 - c1[1] * (c2[0] * c3[2] - c2[2] * c3[0])
                 + c1[2] * (c2[0] * c3[1] - c2[1] * c3[0]), 6)


def rot_about_axis(shape, point, direction, deg):
    out = shape.copy()
    out.rotate(V(*point), V(*direction), deg)
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# rail building
# --------------------------------------------------------------------------- #
def rail_section_face(rail_shape):
    """End face of the vendor rail (plane normal to its local X)."""
    faces = [f for f in rail_shape.Faces if abs(f.BoundBox.XMax - f.BoundBox.XMin) < 1e-6]
    faces.sort(key=lambda f: f.BoundBox.XMin)
    return faces[0]


def slot_tool(xc, ymin=-0.6, ymax=1.6):
    """Obround slot tool 8.8+2*3.1 = 15.0 long in X, 6.2 wide in Z, centred at Z=0.

    Geometry measured on the vendor sample: semicircular ends r=3.1 whose axes
    sit 8.8 mm apart, pitch 25 mm, only through the 1.0 mm base plate.
    """
    t = Part.makeBox(8.8, ymax - ymin, 6.2, V(xc - 4.4, ymin, -3.1))
    for dx in (-4.4, 4.4):
        t = t.fuse(Part.makeCylinder(3.1, ymax - ymin, V(xc + dx, ymin, 0.0), V(0, 1, 0)))
    return t


def build_rail(section_face, length, pitch=25.0, slot_len=15.0, first_centre=12.5):
    """Prismatic rail of `length` from the measured section + the measured slots."""
    solid = section_face.extrude(V(length, 0, 0))
    n = 0
    xc = first_centre
    while xc + slot_len / 2.0 <= length + 1e-9:
        solid = solid.cut(slot_tool(xc))
        n += 1
        xc += pitch
    solid = solid.removeSplitter()
    return solid, n


def place(shape, c1, c2, c3, translation):
    out = shape.copy()
    out.transformShape(mat_from_columns(c1, c2, c3))
    out.translate(V(*translation))
    return out


# orientation of a rail mounted as an UPRIGHT (length along +Y, base plate
# facing -Z, width along X) -- datum aligned with the validated peca socket
ROT_UPRIGHT = ((0, 1, 0), (0, 0, 1), (1, 0, 0))
# orientation of a rail mounted as the CROSSBAR (length along +X, base plate
# facing -Z, width along Y)
ROT_CROSSBAR = ((1, 0, 0), (0, 0, 1), (0, -1, 0))
